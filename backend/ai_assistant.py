import google.generativeai as genai
import os
from typing import List, Dict, Optional, ClassVar, Union, Any
from dotenv import load_dotenv
from github import Github
from github.GithubException import GithubException
from dataclasses import dataclass
from rag_query import get_secure_coding_patterns
import json
import jwt
import time
from github import Auth

# --- PHASE 1 IMPORTS ---
import git
import shutil
from pathlib import Path
from scanner.secrets_detector import scan_secrets
from scanner.static_python import run_bandit # --- PHASE 1B ---

# Updated RepoAnalysis class to handle both formats
@dataclass
class RepoAnalysis:
    """Store repository analysis results."""
    repo_name: str
    description: str
    language: str
    files_scanned: List[str]
    security_findings: List[str]
    open_issues: int
    # Updated to handle both dict (new comprehensive format) and RepoAnalysis (legacy format)
    latest_analysis: ClassVar[Optional[Union[Dict, 'RepoAnalysis']]] = None

@dataclass
class WebsiteScan:
    """Store website scan results for AI context"""
    url: str
    timestamp: str
    scan_result: Dict[str, Any]
    security_score: Optional[int] = None
    # Class variable to store latest scan
    latest_scan: ClassVar[Optional[Dict[str, Any]]] = None

@dataclass
class FixRequest:
    """Request model for automated fix generation"""
    repo_url: str
    issue: Dict[str, Any]
    branch_name: Optional[str] = None

# Load environment variables from a .env file
load_dotenv()

# Available models configuration
AVAILABLE_MODELS = {
    'fast': 'models/gemini-2.5-flash',
    'smart': 'models/gemini-2.5-pro'
}

# --- Enhanced GitHub Authentication Setup ---
models = {}
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Updated from GITHUB_PAT

# Read the private key from file
GITHUB_PRIVATE_KEY = None
try:
    if GITHUB_PRIVATE_KEY_PATH and os.path.exists(GITHUB_PRIVATE_KEY_PATH):
        with open(GITHUB_PRIVATE_KEY_PATH, 'r') as key_file:
            GITHUB_PRIVATE_KEY = key_file.read()
        print(f"✅ GitHub private key loaded from: {GITHUB_PRIVATE_KEY_PATH}")
    else:
        print(f"⚠️ Private key file not found at: {GITHUB_PRIVATE_KEY_PATH}")
        print("🔄 Falling back to personal access token authentication")
except FileNotFoundError:
    print(f"❌ ERROR: Private key file not found at path: {GITHUB_PRIVATE_KEY_PATH}")
    print("💡 Make sure the .pem file exists and the path in .env is correct")
    GITHUB_PRIVATE_KEY = None
except Exception as e:
    print(f"❌ ERROR reading private key file: {e}")
    GITHUB_PRIVATE_KEY = None

def generate_github_app_jwt():
    """Generate JWT for GitHub App authentication"""
    if not GITHUB_APP_ID or not GITHUB_PRIVATE_KEY:
        print("⚠️ GitHub App ID or Private Key not available")
        return None
    
    try:
        # Create JWT payload
        now = int(time.time())
        payload = {
            'iat': now - 60,  # Issued at time (1 minute ago to account for clock skew)
            'exp': now + (10 * 60),  # Expiration time (10 minutes from now)
            'iss': GITHUB_APP_ID  # Issuer (GitHub App ID)
        }
        
        # Generate JWT
        token = jwt.encode(payload, GITHUB_PRIVATE_KEY, algorithm='RS256')
        print("✅ GitHub App JWT generated successfully")
        return token
        
    except Exception as e:
        print(f"❌ Error generating GitHub App JWT: {e}")
        return None

def get_github_app_installation_token(owner, repo):
    """Get installation access token for a specific repository"""
    jwt_token = generate_github_app_jwt()
    if not jwt_token:
        return None
    
    try:
        # Create GitHub instance with JWT
        github_jwt = Github(auth=Auth.Token(jwt_token))
        
        # Get the app
        app = github_jwt.get_app()
        
        # Find installation for the repository owner
        installations = app.get_installations()
        target_installation = None
        
        for installation in installations:
            if installation.account.login.lower() == owner.lower():
                target_installation = installation
                break
        
        if not target_installation:
            print(f"⚠️ GitHub App not installed for {owner}")
            return None
        
        # Get installation access token
        access_token = target_installation.get_access_token()
        print(f"✅ GitHub App installation token obtained for {owner}/{repo}")
        return access_token.token
        
    except Exception as e:
        print(f"❌ Error getting installation token: {e}")
        return None

# Initialize GitHub client with enhanced authentication
def initialize_github_client():
    """Initialize GitHub client with best available authentication method"""
    
    # Try GitHub App authentication first (most powerful)
    if GITHUB_APP_ID and GITHUB_PRIVATE_KEY:
        try:
            jwt_token = generate_github_app_jwt()
            if jwt_token:
                github_client = Github(auth=Auth.Token(jwt_token))
                print("✅ GitHub client initialized with App authentication")
                return github_client
        except Exception as e:
            print(f"⚠️ GitHub App auth failed: {e}")
    
    # Fallback to personal access token
    if GITHUB_TOKEN:
        try:
            github_client = Github(GITHUB_TOKEN)
            test_user = github_client.get_user()
            print(f"✅ GitHub client initialized with personal access token for user: {test_user.login}")
            return github_client
        except Exception as e:
            print(f"⚠️ Personal token auth failed: {e}")
    
    # Final fallback to anonymous access
    print("❌ No GitHub authentication available - using anonymous access")
    return Github()

# Initialize the enhanced client
github_client = initialize_github_client()

def get_authenticated_repo(repo_url):
    """Get authenticated repository instance for pull request creation"""
    try:
        # Extract owner and repo name
        repo_url_clean = repo_url.rstrip('/').replace('.git', '')
        parts = repo_url_clean.split('/')
        if len(parts) < 2:
            raise ValueError("Invalid repository URL format")
        
        owner, repo_name = parts[-2], parts[-1]
        
        # Try GitHub App authentication for this specific repo
        if GITHUB_APP_ID and GITHUB_PRIVATE_KEY:
            installation_token = get_github_app_installation_token(owner, repo_name)
            if installation_token:
                app_github = Github(auth=Auth.Token(installation_token))
                repo = app_github.get_repo(f"{owner}/{repo_name}")
                print(f"✅ Repository access via GitHub App: {owner}/{repo_name}")
                return repo, app_github
        
        # Fallback to personal token
        if github_client:
            repo = github_client.get_repo(f"{owner}/{repo_name}")
            print(f"✅ Repository access via personal token: {owner}/{repo_name}")
            return repo, github_client
        
        raise Exception("No authentication method available")
        
    except Exception as e:
        print(f"❌ Failed to get authenticated repository access: {e}")
        return None, None

# --- Initialize Gemini AI ---
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("No API key found. Set the GOOGLE_API_KEY environment variable.")
    
    genai.configure(api_key=api_key)
    
    for model_type, model_name in AVAILABLE_MODELS.items():
        try:
            models[model_type] = genai.GenerativeModel(model_name)
            print(f"✅ Initialized {model_type} model ({model_name})")
        except Exception as e:
            print(f"❌ Failed to initialize {model_type} model: {e}")
            
except Exception as e:
    print(f"❌ Error initializing Gemini API: {e}")

# --- Helper functions ---
def get_model(model_type: str = 'fast') -> Optional[genai.GenerativeModel]:
    """Get the specified model (fast or smart)"""
    return models.get(model_type)

def format_chat_response(text: str) -> str:
    """Format AI response for better readability"""
    import re
    formatted = text.strip()
    formatted = re.sub(r'<[^>]+>', '', formatted)
    formatted = formatted.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    formatted = re.sub(r'---+', '', formatted)
    formatted = re.sub(r'═══+', '', formatted)
    formatted = re.sub(r'\n\s*\n\s*\n', '\n\n', formatted)
    emojis = ['✅', '❌', '⚠️', '🚨', '📊', '🔒', '🛡️', '🔐', '🌐', '🎯', '⚡', '📂', '🔍']
    for emoji in emojis:
        formatted = formatted.replace(emoji, f'\n{emoji}')
    formatted = re.sub(r'(##?\s*[🛡️🚨⚠️✅❌📊🎯⚡📂🔍].*)', r'\n\n\1', formatted)
    while '\n\n\n' in formatted:
        formatted = formatted.replace('\n\n\n', '\n\n')
    formatted = formatted.lstrip('\n')
    return formatted

def get_chat_response(history: List[Dict], model_type: str = 'fast') -> str:
    """
    Generates a chat response using the specified model, including context from the latest repository analysis.

    Args:
        history: A list of previous chat messages.
        model_type: The type of model to use ('fast' or 'smart').

    Returns:
        A formatted string containing the AI's response.
    """
    model = get_model(model_type)
    if model is None:
        return f"❌ **AI model ({model_type}) is not available**"

    try:
        # Define base context based on the selected model type
        if model_type == 'smart':
            context = """You are GitHub Copilot, an expert cybersecurity consultant and code analysis specialist. You provide comprehensive, detailed security analysis with:

🛡️ **Advanced Security Analysis:**
• Deep threat assessment and risk evaluation
• Comprehensive vulnerability analysis with CVSS scoring context
• Advanced remediation strategies with implementation details
• Compliance and regulatory guidance (OWASP, NIST, SOC2)
• Architecture-level security recommendations

🔬 **Expert Code Review:**
• Detailed static analysis interpretation with business impact
• Complex dependency vulnerability assessment
• Advanced secure coding pattern recommendations
• Performance vs security trade-off analysis
• Enterprise-grade security implementation guidance

💡 **Communication Style:**
• Provide comprehensive, detailed explanations
• Include technical depth with practical examples
• Reference industry standards and best practices
• Give step-by-step implementation guides
• Explain the 'why' behind each recommendation
• Use technical terminology appropriately"""
        else:  # 'fast' model
            context = """You are GitHub Copilot, a friendly cybersecurity assistant focused on quick, actionable security guidance:

🔒 **Quick Security Analysis:**
• Fast vulnerability identification and prioritization
• Clear, concise remediation steps
• Immediate action items and quick wins
• Essential security best practices
• Rapid threat assessment

⚡ **Efficient Communication:**
• Provide clear, concise recommendations
• Focus on high-impact, easy-to-implement fixes
• Use simple, actionable language
• Prioritize critical issues first
• Give practical examples and code snippets
• Be encouraging and supportive"""

        # Append the latest repository analysis to the context, if it exists
        if RepoAnalysis.latest_analysis:
            if isinstance(RepoAnalysis.latest_analysis, dict):
                # Handle new comprehensive analysis format from /analyze-repo
                analysis_context = format_analysis_for_context(RepoAnalysis.latest_analysis)
                context += "\n\n📂 **CURRENT REPOSITORY ANALYSIS:**\n" + analysis_context
            else:
                # Handle legacy RepoAnalysis format
                context += f"""

📂 **REPOSITORY CONTEXT:**
**Repository:** {RepoAnalysis.latest_analysis.repo_name}
**Language:** {RepoAnalysis.latest_analysis.language}
**Security Findings:** {len(RepoAnalysis.latest_analysis.security_findings)} issues found
**Recent Findings:** {', '.join(RepoAnalysis.latest_analysis.security_findings[:3])}"""
        
        # Also add website scan context if available
        if WebsiteScan.latest_scan:
            website_data = WebsiteScan.latest_scan
            if isinstance(website_data, dict):
                scan_data = website_data.get('scan_result', {})
                context += f"""

🌐 **WEBSITE SECURITY SCAN:**
• Target: {scan_data.get('url', 'N/A')}
• Security Score: {scan_data.get('security_score', 'N/A')}/100
• HTTPS: {'✅ Enabled' if scan_data.get('https', False) else '❌ Disabled'}
• Vulnerabilities: {len(scan_data.get('flags', []))} issues found"""

        # Prepare the chat history in the format required by the Generative AI model.
        # The history always starts with the model's context.
        new_history = [{"role": "model", "parts": [context]}]
        
        for message in history:
            try:
                # Extract content ensuring it's always a string
                content = ""
                
                if isinstance(message, dict):
                    # Method 1: Check for 'parts' field
                    if 'parts' in message and isinstance(message['parts'], list) and len(message['parts']) > 0:
                        first_part = message['parts'][0]
                        if isinstance(first_part, str):
                            content = first_part
                        elif isinstance(first_part, dict) and 'text' in first_part:
                            content = first_part['text']
                        else:
                            content = str(first_part)
                    
                    # Method 2: Check for direct message content
                    elif 'message' in message:
                        content = str(message['message'])
                    elif 'content' in message:
                        content = str(message['content'])
                    elif 'text' in message:
                        content = str(message['text'])
                    
                    # Method 3: Fallback - convert entire message to string
                    else:
                        content = str(message)
                else:
                    # If message is not a dict, convert to string
                    content = str(message)
                
                # Ensure content is not empty and is a string
                if not content or not isinstance(content, str):
                    content = "No message content"
                
                # Determine role
                role = 'user'
                if isinstance(message, dict):
                    if message.get('type') == 'assistant' or message.get('type') == 'model':
                        role = 'model'
                    elif message.get('role') == 'model' or message.get('role') == 'assistant':
                        role = 'model'
                
                new_history.append({
                    "role": role,
                    "parts": [content]  # Always a single string in a list
                })
                
            except Exception as e:
                print(f"Warning: Error processing message in history: {e}")
                continue

        # The last message is what the model needs to respond to.
        if len(new_history) > 1:
            chat_history_for_model = new_history[:-1]
            last_user_message = new_history[-1]['parts'][0]
        else:
            chat_history_for_model = [{"role": "model", "parts": [context]}]
            last_user_message = "Please help with security analysis."

        # Initiate the chat and get the response
        chat = model.start_chat(history=chat_history_for_model)
        response = chat.send_message(last_user_message)

        # Format and return the final response
        formatted_response = format_chat_response(response.text.strip())
        
        if model_type == 'smart':
            return f"🧠 **Comprehensive Analysis** (Smart Model)\n\n{formatted_response}"
        else:
            return f"⚡ **Quick Analysis** (Fast Model)\n\n{formatted_response}"

    except Exception as e:
        # Provide a clear error message if something goes wrong during the process
        print(f"An unexpected error occurred in get_chat_response: {e}") # For server-side logging
        return f"❌ **Chat Error ({model_type} model):** {str(e)}"

# --- Main Analysis Function ---
def analyze_github_repo(repo_url: str, model_type: str = 'smart', existing_clone_path: str = None) -> str:
    """Analyze GitHub repository with model selection"""
    if not github_client:
        return "❌ **GitHub client not available.** Please check your setup."
    
    repo_name_from_url = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
    
    # Use existing clone if provided, otherwise create new temp directory
    if existing_clone_path and os.path.exists(existing_clone_path):
        local_repo_path = existing_clone_path
        temp_dir = None  # Don't create new temp dir
        print(f"📁 Using existing clone at {existing_clone_path}")
    else:
        # Use proper cross-platform temporary directory
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix=f"altx_ai_{repo_name_from_url}_")
        local_repo_path = temp_dir

    try:
        repo_url = repo_url.rstrip('/').replace('.git', '')
        parts = repo_url.split('/')
        if len(parts) < 5 or parts[2].lower() != 'github.com':
            return "❌ **Invalid repository URL format.**"
        
        owner, repo_name = parts[-2], parts[-1]
        repo = github_client.get_repo(f"{owner}/{repo_name}")
        
        # Only clone if we don't have an existing clone
        if not existing_clone_path:
            print(f"Cloning {repo_url} to {local_repo_path}...")
            git.Repo.clone_from(repo_url, local_repo_path)
        
        security_findings = []
        all_files_visited = [str(p.relative_to(local_repo_path)) for p in Path(local_repo_path).rglob("*") if p.is_file()]
        
        # --- Run Secret Scanner (Phase 1A) ---
        print("🔍 Scanning for hardcoded secrets...")
        hardcoded_secrets = scan_secrets(local_repo_path)
        if hardcoded_secrets:
            security_findings.append(f"🚨 CRITICAL: Found {len(hardcoded_secrets)} hardcoded secrets!")
            for secret in hardcoded_secrets:
                security_findings.append(f"   - Type: {secret['type']} in file: `{secret['file']}`")
        
        # --- PHASE 1B: Run Bandit Static Analysis ---
        print("🐍 Scanning Python code with Bandit...")
        static_issues = run_bandit(local_repo_path)
        if static_issues:
            security_findings.append(f"🛡️ Found {len(static_issues)} potential issues in Python code via Bandit.")
            for issue in static_issues:
                # To avoid clutter, let's focus on medium/high severity issues
                if issue['severity'] in ['MEDIUM', 'HIGH']:
                    security_findings.append(f"   - {issue['severity']}: {issue['issue']} in `{issue['filename']}` (Line: {issue['line_number']})")
        print(f"✅ Scans complete. Found {len(hardcoded_secrets)} secrets and {len(static_issues)} static issues.")

        # --- Store Analysis Results (Legacy format for backward compatibility) ---
        RepoAnalysis.latest_analysis = RepoAnalysis(
            repo_name=repo.full_name,
            description=repo.description or 'No description',
            language=repo.language or 'Unknown',
            files_scanned=all_files_visited,
            security_findings=security_findings,
            open_issues=repo.open_issues_count
        )
        
        # --- Build AI Analysis Prompt with Model-Specific Detail Level ---
        secret_findings_summary = "\n".join([f"• {s}" for s in security_findings if "secret" in s.lower()])
        static_findings_summary = "\n".join([f"• {s}" for s in security_findings if "Bandit" in s or "Python code" in s])

        if model_type == 'smart':
            security_prompt = f"""
**COMPREHENSIVE REPOSITORY SECURITY ANALYSIS REQUEST**
Perform a detailed security analysis of the GitHub repository below based on comprehensive scan results.

**📊 Repository Information:**
• **Name:** {repo.full_name}
• **Description:** {repo.description or 'No description provided'}
• **Primary Language:** {repo.language or 'Unknown'}
• **Open Issues:** {repo.open_issues_count}
• **Files Scanned:** {len(all_files_visited)}

**🔑 Hardcoded Secrets Analysis:**
{secret_findings_summary if secret_findings_summary else "• ✅ No hardcoded secrets were detected in the repository."}

**🐍 Python Static Code Analysis (Bandit):**
{static_findings_summary if static_findings_summary else "• ✅ No medium or high-severity static analysis issues found in Python code."}

Please provide a comprehensive, detailed analysis with these sections:

## 🛡️ Executive Security Summary
Provide a detailed security posture assessment with risk rating and strategic recommendations.

## 🚨 Critical Vulnerabilities Assessment
Detailed analysis of each critical issue with:
- CVSS risk scoring context
- Potential attack vectors
- Business impact assessment
- Exploitation scenarios

## 🔬 Technical Risk Analysis
In-depth technical evaluation including:
- Code quality implications
- Architecture security considerations
- Dependency management risks
- Configuration security gaps

## 🎯 Prioritized Remediation Roadmap
Detailed action plan with:
- Immediate critical fixes (0-24 hours)
- Short-term improvements (1-4 weeks)  
- Long-term security strategy (1-6 months)
- Implementation complexity assessment

## 💡 Advanced Security Recommendations
Enterprise-grade recommendations including:
- Security architecture improvements
- DevSecOps integration strategies
- Compliance considerations (OWASP, NIST)
- Monitoring and alerting strategies

**ANALYSIS REQUIREMENTS:**
• Provide comprehensive technical depth with practical examples
• Include specific code examples and implementation guides
• Reference industry standards and best practices
• Explain the business rationale behind each recommendation
• Use professional security consultant terminology
"""
        else:  # fast model
            security_prompt = f"""
**QUICK REPOSITORY SECURITY SCAN ANALYSIS**
Analyze this GitHub repository and provide fast, actionable security guidance.

**📊 Repository:** {repo.full_name} ({repo.language or 'Unknown'})

**🔑 Secrets Scan:**
{secret_findings_summary if secret_findings_summary else "• ✅ No secrets found"}

**🐍 Code Analysis:**
{static_findings_summary if static_findings_summary else "• ✅ No major issues found"}

Please provide a quick analysis with these sections:

## 🛡️ Security Summary
Quick security rating and main concerns.

## 🚨 Critical Issues
List the most important problems to fix immediately.

## ⚡ Quick Fixes
Specific, actionable steps you can implement today.

## 🎯 Next Steps
Simple recommendations for improving security.

**REQUIREMENTS:**
• Keep responses concise and actionable
• Focus on high-impact, easy-to-implement fixes
• Provide specific examples and commands
• Use simple, clear language
"""
        
        history = [{"type": "user", "parts": [security_prompt]}]
        return get_chat_response(history, model_type)

    except Exception as e:
        print(f"Error analyzing repository: {str(e)}")
        return f"❌ **An unexpected error occurred:** {str(e)}"
    finally:
        # Enhanced Windows-compatible cleanup - only if we created a temp directory
        if temp_dir and os.path.exists(local_repo_path):
            try:
                import stat
                import time
                
                def force_remove_readonly_ai(func, path, exc_info):
                    """Enhanced readonly handler for Git objects"""
                    try:
                        if os.path.exists(path):
                            # Make file writable and remove all permissions restrictions
                            os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                            # Try the original function again
                            func(path)
                    except Exception as e:
                        print(f"⚠️ AI cleanup: Could not remove {path}: {e}")
                
                def cleanup_git_directory_ai(directory):
                    """Special cleanup for Git directories in AI analysis"""
                    try:
                        git_dir = os.path.join(directory, '.git')
                        if os.path.exists(git_dir):
                            for root, dirs, files in os.walk(git_dir):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    try:
                                        os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                                    except Exception:
                                        pass
                    except Exception:
                        pass
                
                # Apply enhanced cleanup
                cleanup_git_directory_ai(local_repo_path)
                
                if os.name == 'nt':  # Windows
                    time.sleep(0.3)  # Wait for file handles
                
                shutil.rmtree(local_repo_path, onerror=force_remove_readonly_ai)
                print(f"✅ AI analysis temp directory cleaned up: {local_repo_path}")
                
            except Exception as cleanup_error:
                print(f"⚠️ AI cleanup warning: {cleanup_error}")
                # Try Windows-specific cleanup if standard method fails
                if os.name == 'nt':
                    try:
                        import subprocess
                        subprocess.run(['rmdir', '/s', '/q', local_repo_path], 
                                     shell=True, check=False)
                    except:
                        pass

def analyze_scan_with_llm(https: bool, flags: List[str], headers: Dict[str, str], model_type: str = 'fast') -> str:
    """Analyze website scan results using LLM with model selection"""
    model = get_model(model_type)
    if model is None:
        return f"❌ **AI model ({model_type}) is not available**"
    
    try:
        # Model-specific analysis depth
        if model_type == 'smart':
            security_prompt = f"""
**COMPREHENSIVE WEBSITE SECURITY ANALYSIS REQUEST**

Perform a detailed security assessment of the following website scan results.

**🔒 Security Configuration Status:**
• **HTTPS Protection:** {'✅ Properly Configured' if https else '❌ Not Implemented - CRITICAL VULNERABILITY'}
• **Security Issues Detected:** {len(flags)} vulnerabilities identified
• **HTTP Security Headers:** {len(headers)} headers analyzed

**🚨 Detailed Vulnerability Assessment:**
{chr(10).join([f'• **{flag}** - Requires immediate attention' for flag in flags]) if flags else '• ✅ No critical security vulnerabilities detected'}

**📋 HTTP Security Headers Analysis:**
{chr(10).join([f'• **{key}:** `{value}`' for key, value in headers.items()]) if headers else '• ⚠️ No security headers detected'}

Please provide a comprehensive security analysis with these sections:

## 🛡️ Executive Security Assessment
• Overall security posture rating
• Risk level classification (Critical/High/Medium/Low)
• Executive summary for stakeholders

## 🚨 Critical Vulnerability Analysis
• Detailed assessment of each security issue
• Potential attack vectors and exploitation scenarios
• Business impact assessment
• OWASP Top 10 correlation

## 🔐 Security Headers Deep Dive
• Analysis of implemented security headers
• Missing critical headers identification
• Configuration optimization recommendations
• Browser compatibility considerations

## 🎯 Comprehensive Remediation Strategy
• Immediate fixes (0-24 hours)
• Short-term improvements (1-4 weeks)
• Long-term security architecture (1-6 months)
• Implementation complexity assessment

## 💡 Advanced Security Recommendations
• Content Security Policy (CSP) implementation
• Security monitoring and alerting setup
• Penetration testing recommendations
• Compliance considerations (PCI DSS, GDPR, etc.)

**ANALYSIS REQUIREMENTS:**
• Provide technical depth with specific implementation examples
• Include nginx/Apache configuration snippets
• Reference security standards and best practices
• Explain business rationale for each recommendation
"""
        else:  # fast model
            security_prompt = f"""
**QUICK WEBSITE SECURITY SCAN ANALYSIS**

Analyze this website security scan and provide fast, actionable recommendations.

**🔒 Security Status:**
• **HTTPS:** {'✅ Enabled' if https else '❌ Missing - FIX IMMEDIATELY'}
• **Issues Found:** {len(flags)} problems
• **Headers Present:** {len(headers)} security headers

**🚨 Problems Found:**
{chr(10).join([f'• {flag}' for flag in flags]) if flags else '• ✅ No major issues detected'}

**📋 Security Headers:**
{chr(10).join([f'• {key}: {value}' for key, value in headers.items()]) if headers else '• No headers found'}

Please provide a quick analysis with these sections:

## 🛡️ Security Rating
Quick assessment of website security.

## 🚨 Critical Issues
Most important problems to fix first.

## ⚡ Quick Fixes
Specific steps to improve security today.

## 🎯 Implementation Guide
Simple examples and code snippets.

**REQUIREMENTS:**
• Keep responses practical and actionable
• Provide specific configuration examples
• Focus on high-impact, easy wins
• Use clear, simple language
"""
        
        history = [{"type": "user", "parts": [security_prompt]}]
        return get_chat_response(history, model_type)
        
    except Exception as e:
        return f"❌ **Website Analysis Error ({model_type} model):** {str(e)}"
    
def format_analysis_for_context(analysis_data: Dict[str, Any]) -> str:
    """Format comprehensive analysis data for AI context"""
    try:
        if not analysis_data:
            return "No analysis data available"
        
        repo_info = analysis_data.get('repository_info', {})
        security_summary = analysis_data.get('security_summary', {})
        
        context = f"""
**REPOSITORY ANALYSIS CONTEXT:**
• Repository: {repo_info.get('name', 'Unknown')}
• Language: {repo_info.get('language', 'Unknown')}
• Security Score: {analysis_data.get('overall_security_score', 'N/A')}/100
• Security Level: {analysis_data.get('security_level', 'Unknown')}

**SECURITY METRICS:**
• Files Scanned: {security_summary.get('total_files_scanned', 0)}
• Secrets Found: {security_summary.get('secrets_found', 0)}
• Static Issues: {security_summary.get('static_issues_found', 0)}
• Code Quality Issues: {security_summary.get('code_quality_issues', 0)}
• Vulnerable Dependencies: {security_summary.get('vulnerable_dependencies', 0)}

**KEY FINDINGS:**
"""
        
        # Add secret scan results
        secrets = analysis_data.get('secret_scan_results', [])
        if secrets:
            context += f"\n🔑 SECRETS ({len(secrets)} found):\n"
            for secret in secrets[:5]:  # Limit to first 5
                context += f"• {secret.get('file', 'unknown')}: {secret.get('secret_type', 'unknown')} (Line {secret.get('line', 'N/A')})\n"
        
        # Add code quality issues
        code_issues = analysis_data.get('code_quality_results', [])
        if code_issues:
            context += f"\n📝 CODE QUALITY ({len(code_issues)} issues):\n"
            for issue in code_issues[:5]:  # Limit to first 5
                context += f"• {issue.get('file', 'unknown')}: {issue.get('pattern', 'unknown')} - {issue.get('severity', 'Unknown')}\n"
        
        # Add recommendations
        recommendations = analysis_data.get('recommendations', [])
        if recommendations:
            context += f"\n💡 TOP RECOMMENDATIONS:\n"
            for rec in recommendations[:5]:  # Limit to first 5
                context += f"• {rec}\n"
        
        return context.strip()
        
    except Exception as e:
        return f"Error formatting analysis context: {str(e)}"

def test_github_authentication():
    """Test function to verify GitHub authentication setup"""
    print("🔍 Testing GitHub authentication setup...")
    
    print(f"📁 Private key path: {GITHUB_PRIVATE_KEY_PATH}")
    print(f"📁 File exists: {os.path.exists(GITHUB_PRIVATE_KEY_PATH) if GITHUB_PRIVATE_KEY_PATH else False}")
    print(f"🔑 Private key loaded: {'✅ Yes' if GITHUB_PRIVATE_KEY else '❌ No'}")
    print(f"🆔 App ID configured: {'✅ Yes' if GITHUB_APP_ID else '❌ No'}")
    
    if GITHUB_PRIVATE_KEY:
        print(f"🔐 Key length: {len(GITHUB_PRIVATE_KEY)} characters")
        print(f"🔐 Key preview: {GITHUB_PRIVATE_KEY[:50]}...")
    
    # Test JWT generation
    jwt_token = generate_github_app_jwt()
    if jwt_token:
        print("✅ JWT generation successful")
    else:
        print("❌ JWT generation failed")

# Call this when the module loads for testing
if __name__ == "__main__":
    test_github_authentication()