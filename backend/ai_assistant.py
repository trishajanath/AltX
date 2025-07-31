import google.generativeai as genai
import os
from typing import List, Dict, Optional, ClassVar
from dotenv import load_dotenv
from github import Github
from github.GithubException import GithubException
from dataclasses import dataclass

# Define RepoAnalysis class to store scan results
@dataclass
class RepoAnalysis:
    """Store repository analysis results."""
    repo_name: str
    description: str
    language: str
    files_scanned: List[str]
    security_findings: List[str]
    open_issues: int
    
    # Class variable to store the latest analysis for context
    latest_analysis: ClassVar[Optional['RepoAnalysis']] = None

# Load environment variables from a .env file
load_dotenv()

# Available models configuration
AVAILABLE_MODELS = {
    'fast': 'models/gemini-2.5-flash',
    'smart': 'models/gemini-2.5-pro'
}

# --- Initialize API Clients ---
models = {}
GITHUB_TOKEN = os.getenv("GITHUB_PAT")
# Initialize GitHub client - use token if available, otherwise use anonymous access for public repos
if GITHUB_TOKEN:
    github_client = Github(GITHUB_TOKEN)
    print("✅ GitHub client initialized with authentication token")
else:
    github_client = Github()  # Anonymous access for public repositories
    print("⚠️ GitHub client initialized without token (public repos only)")

# Initialize Gemini API
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("No API key found. Set the GOOGLE_API_KEY environment variable.")
    
    genai.configure(api_key=api_key)
    
    # Initialize all available models
    for model_type, model_name in AVAILABLE_MODELS.items():
        try:
            models[model_type] = genai.GenerativeModel(model_name)
            print(f"✅ Initialized {model_type} model ({model_name})")
        except Exception as e:
            print(f"❌ Failed to initialize {model_type} model: {e}")
            
except Exception as e:
    print(f"❌ Error initializing Gemini API: {e}")

def get_model(model_type: str = 'fast') -> Optional[genai.GenerativeModel]:
    """Retrieves the specified generative model instance."""
    return models.get(model_type)

def analyze_scan_with_llm(https: bool, flags: List[str], headers: Dict[str, str], model_type: str = 'fast') -> str:
    """Generates a detailed security report with structured containers."""
    model = get_model(model_type)
    if not model:
        return f"AI model ({model_type}) is not available."

    # Calculate security metrics
    total_headers = 6  # Essential security headers
    present_headers = len(headers) if headers else 0
    critical_issues = len(flags)
    
    # Determine security level
    if https and present_headers >= 4 and critical_issues == 0:
        security_level = "High"
        security_score = 85 + (present_headers * 2)
    elif https and present_headers >= 2:
        security_level = "Medium" 
        security_score = 60 + (present_headers * 3)
    else:
        security_level = "Low"
        security_score = max(20, 40 + (present_headers * 5))
    
    # Create structured analysis
    implemented_features = []
    missing_features = []
    
    # Check HTTPS
    if https:
        implemented_features.append("✅ **HTTPS/SSL:** Secure connection established")
    else:
        missing_features.append("❌ **HTTPS/SSL:** CRITICAL - No secure connection")
    
    # Check headers
    if headers:
        for header in headers.keys():
            implemented_features.append(f"✅ **{header}:** Security header configured")
    
    # Check for missing critical headers
    critical_headers = ['content-security-policy', 'x-frame-options', 'x-content-type-options', 'strict-transport-security']
    header_keys_lower = [h.lower() for h in headers.keys()] if headers else []
    
    for critical_header in critical_headers:
        if critical_header not in header_keys_lower:
            descriptions = {
                'content-security-policy': 'Vulnerable to XSS attacks',
                'x-frame-options': 'Vulnerable to clickjacking', 
                'x-content-type-options': 'Vulnerable to MIME sniffing',
                'strict-transport-security': 'Vulnerable to downgrade attacks'
            }
            missing_features.append(f"❌ **{critical_header.title()}:** {descriptions[critical_header]}")
    
    # Always add accessibility as working
    implemented_features.append("✅ **Website Accessibility:** Site is reachable and responsive")
    
    # Calculate detailed scores
    https_score = 25 if https else 0
    headers_score = min(30, present_headers * 5)
    content_score = 20 if present_headers >= 2 else 10
    network_score = 15 if https else 5
    
    # System prompt for generating container-friendly output
    system_prompt = """You are a senior cybersecurity expert. Create a well-structured security analysis that can be displayed in organized UI containers/boxes.

    FORMATTING REQUIREMENTS:
    - Use clear section headers for different containers
    - Include visual indicators (✅❌⚠️🚨) for easy scanning
    - Make each section self-contained and visually distinct
    - Focus on actionable recommendations
    - Structure output for easy container-based UI display
    """
    
    user_prompt = f"""
SECURITY SCAN RESULTS:
- HTTPS Status: {'✅ Enabled' if https else '❌ Not Enabled'}
- Vulnerabilities Found: {len(flags)} issues
- Headers Analyzed: {len(headers)} headers
- Security Level: {security_level}
- Security Score: {min(100, security_score)}/100

Create a comprehensive security report with these container sections:

## 🛡️ SECURITY OVERVIEW CONTAINER
- **Security Level:** {security_level}
- **Overall Score:** {min(100, security_score)}/100
- **Critical Issues:** {critical_issues}
- **Action Required:** {"Yes" if not https or critical_issues > 0 else "No"}

## ✅ WORKING FEATURES CONTAINER
{chr(10).join(implemented_features)}

## ❌ MISSING FEATURES CONTAINER  
{chr(10).join(missing_features)}

## 🚨 VULNERABILITIES CONTAINER
{chr(10).join([f"🚨 **CRITICAL:** {flag}" for flag in flags]) if flags else '✅ **No critical vulnerabilities detected**'}

## 📊 SECURITY METRICS CONTAINER
- **🔒 HTTPS/SSL:** {https_score}/25 - {"✅ Enabled" if https else "❌ Disabled"}
- **🛡️ Security Headers:** {headers_score}/30 - {present_headers}/{total_headers} headers present
- **🔐 Content Protection:** {content_score}/25 - {"Good" if present_headers >= 2 else "Poor"}
- **🌐 Network Security:** {network_score}/20 - {"Secure" if https else "Insecure"}

## 🎯 ACTION PLAN CONTAINER
{"1. 🚨 **CRITICAL:** Enable HTTPS/SSL certificate (immediate)" if not https else ""}
2. ⚠️ **HIGH:** Implement missing security headers (CSP, X-Frame-Options, etc.)
3. 🔧 **MEDIUM:** Configure proper HTTP to HTTPS redirects  
4. 📝 **LOW:** Schedule regular security monitoring

## ⚡ IMPLEMENTATION CHECKLIST CONTAINER
- [{"x" if https else " "}] Enable HTTPS/SSL certificate (Critical Priority)
- [{"x" if 'content-security-policy' in header_keys_lower else " "}] Add Content-Security-Policy header (High Priority)
- [{"x" if 'x-frame-options' in header_keys_lower else " "}] Implement X-Frame-Options header (High Priority)
- [{"x" if 'x-content-type-options' in header_keys_lower else " "}] Configure X-Content-Type-Options header (Medium Priority)
- [{"x" if 'strict-transport-security' in header_keys_lower else " "}] Set up Strict-Transport-Security header (High Priority)
- [ ] Test all security implementations (Medium Priority)

Format each section clearly so it can be displayed in separate UI containers with appropriate styling and colors.
"""

    try:
        response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
        
        # Post-process for better container formatting
        formatted_response = response.text.strip()
        
        # Ensure proper spacing for containers
        formatted_response = formatted_response.replace('##', '\n\n##')
        formatted_response = formatted_response.replace('- [', '\n- [')
        formatted_response = formatted_response.replace('- **', '\n- **')
        formatted_response = formatted_response.replace('✅', '\n✅')
        formatted_response = formatted_response.replace('❌', '\n❌')
        formatted_response = formatted_response.replace('🚨', '\n🚨')
        formatted_response = formatted_response.replace('⚠️', '\n⚠️')
        
        # Clean up excessive line breaks
        while '\n\n\n' in formatted_response:
            formatted_response = formatted_response.replace('\n\n\n', '\n\n')
        
        return formatted_response.strip()
    except Exception as e:
        # Fallback structured format
        return f"""
## 🛡️ SECURITY OVERVIEW CONTAINER
**Security Level:** {security_level}
**Overall Score:** {min(100, security_score)}/100
**Critical Issues:** {critical_issues}
**Action Required:** {"Yes" if not https or critical_issues > 0 else "No"}

## ✅ WORKING FEATURES CONTAINER
{chr(10).join(implemented_features)}

## ❌ MISSING FEATURES CONTAINER
{chr(10).join(missing_features)}

## 🚨 VULNERABILITIES CONTAINER
{chr(10).join([f"🚨 **CRITICAL:** {flag}" for flag in flags]) if flags else '✅ **No critical vulnerabilities detected**'}

## 📊 SECURITY METRICS CONTAINER
**🔒 HTTPS/SSL:** {https_score}/25 - {"✅ Enabled" if https else "❌ Disabled"}
**🛡️ Security Headers:** {headers_score}/30 - {present_headers}/{total_headers} headers present
**🔐 Content Protection:** {content_score}/25 - {"Good" if present_headers >= 2 else "Poor"}
**🌐 Network Security:** {network_score}/20 - {"Secure" if https else "Insecure"}

## 🎯 ACTION PLAN CONTAINER
{"1. 🚨 **CRITICAL:** Enable HTTPS/SSL certificate" if not https else ""}
2. ⚠️ **HIGH:** Implement missing security headers
3. 🔧 **MEDIUM:** Configure proper redirects
4. 📝 **LOW:** Schedule regular monitoring

## ⚡ IMPLEMENTATION CHECKLIST CONTAINER
- [{"x" if https else " "}] Enable HTTPS/SSL certificate
- [{"x" if 'content-security-policy' in header_keys_lower else " "}] Add Content-Security-Policy header
- [{"x" if 'x-frame-options' in header_keys_lower else " "}] Implement X-Frame-Options header
- [{"x" if 'x-content-type-options' in header_keys_lower else " "}] Configure X-Content-Type-Options header
- [{"x" if 'strict-transport-security' in header_keys_lower else " "}] Set up Strict-Transport-Security header
- [ ] Test all security implementations

API Error: {str(e)}
"""
    """Generates a detailed security report based on scan results using an LLM."""
    model = get_model(model_type)
    if not model:
        return f"AI model ({model_type}) is not available."

    # System prompt defines the AI's persona and expertise
    system_prompt = """You are a senior cybersecurity expert. Provide clear, point-wise security analysis with proper formatting.
    
    CRITICAL FORMATTING REQUIREMENTS:
    - Use proper markdown formatting with line breaks between sections
    - Each bullet point should be on a separate line
    - Use bold text for important items
    - Include proper spacing between headers and content
    - Make the output easy to read and well-structured
    - Each section should be clearly separated
    """
    
    # User prompt provides the scan data and requests a specific report format
    user_prompt = f"""
    SECURITY SCAN RESULTS:
    - HTTPS Status: {'✅ Enabled' if https else '❌ Not Enabled'}
    - Vulnerabilities Found: {len(flags)} issues
    - Security Issues: {flags if flags else 'None detected'}
    - Headers Analyzed: {len(headers.keys()) if headers else 0}
    - Present Headers: {list(headers.keys()) if headers else 'None'}
    
    Please provide a CLEAR, POINT-WISE security analysis:

    ## � Security Analysis Summary

    ### ✅ Security Status
    • Overall Security Level: [High/Medium/Low]
    • Critical Issues: [Number] found
    • Immediate Action Required: [Yes/No]

    ### � Critical Vulnerabilities
    {f'• {chr(10).join([f"- {flag}" for flag in flags])}' if flags else '• No critical vulnerabilities detected'}

    ### 🛡️ Security Headers Analysis
    #### Present Headers:
    {f'• {chr(10).join([f"- {header}: {value[:50]}..." for header, value in headers.items()])}' if headers else '• No security headers detected'}
    
    #### Missing Critical Headers:
    • Content-Security-Policy: [Status and recommendation]
    • X-Frame-Options: [Status and recommendation] 
    • X-Content-Type-Options: [Status and recommendation]
    • Strict-Transport-Security: [Status and recommendation]

    ### 🎯 Immediate Action Items
    1. **CRITICAL**: [Most urgent security fix needed]
    2. **HIGH**: [Important security improvements]
    3. **MEDIUM**: [General security enhancements]

    ### 📊 Security Score
    **Overall: [X]/100**
    • HTTPS: [X]/25
    • Headers: [X]/35  
    • Content Protection: [X]/40

    ### � Quick Fixes
    • [Specific 1-line fix recommendations]
    • [Code examples where applicable]

    Keep all points concise, actionable, and easy to implement.
    """

    try:
        response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
        
        # Post-process the response to ensure proper formatting
        formatted_response = response.text.strip()
        
        # Add proper line breaks after headers and sections
        formatted_response = formatted_response.replace('##', '\n\n##')
        formatted_response = formatted_response.replace('###', '\n\n###')
        formatted_response = formatted_response.replace('####', '\n\n####')
        formatted_response = formatted_response.replace('• ', '\n• ')
        formatted_response = formatted_response.replace('1. ', '\n1. ')
        formatted_response = formatted_response.replace('2. ', '\n2. ')
        formatted_response = formatted_response.replace('3. ', '\n3. ')
        formatted_response = formatted_response.replace('4. ', '\n4. ')
        formatted_response = formatted_response.replace('5. ', '\n5. ')
        
        # Clean up multiple consecutive line breaks
        while '\n\n\n' in formatted_response:
            formatted_response = formatted_response.replace('\n\n\n', '\n\n')
        
        return formatted_response.strip()
    except Exception as e:
        return f"API Error: {str(e)}"

def get_chat_response(history: List[Dict], model_type: str = 'fast') -> str:
    """Handles conversational chat with context from repository analysis."""
    model = get_model(model_type)
    if not model:
        return f"AI model ({model_type}) is not available."

    try:
        # Extract the user's current question
        current_question = ""
        if history and len(history) > 0:
            last_msg = history[-1]
            if 'parts' in last_msg and isinstance(last_msg['parts'], list) and len(last_msg['parts']) > 0:
                if isinstance(last_msg['parts'][0], dict):
                    current_question = last_msg['parts'][0].get('text', '')
                else:
                    current_question = str(last_msg['parts'][0])

        # Check if question is within security scope
        security_keywords = [
            'security', 'vulnerability', 'scan', 'attack', 'threat', 'malware', 'encryption', 
            'authentication', 'authorization', 'firewall', 'penetration', 'exploit', 'breach',
            'https', 'ssl', 'tls', 'certificate', 'headers', 'cors', 'xss', 'sql injection',
            'csrf', 'owasp', 'password', 'token', 'api', 'endpoint', 'secure', 'protection',
            'analyze', 'repository', 'code', 'github', 'deployment', 'configuration', 'best practices'
        ]
        

        # Build context with repository analysis if available
        context_lines = [
            "You are a cybersecurity expert AI assistant. Provide clear, actionable security advice.",
            "Focus ONLY on cybersecurity, web security, application security, and security best practices.",
            "Always use bullet points and structured responses for clarity."
        ]
        
        if RepoAnalysis.latest_analysis:
            repo_info = RepoAnalysis.latest_analysis
            context_lines.extend([
                f"\n📂 **Current Analysis Context**:",
                f"• Repository: {repo_info.repo_name}",
                f"• Language: {repo_info.language}",
                f"• Files Analyzed: {len(repo_info.files_scanned)}",
                f"• Security Issues Found: {len(repo_info.security_findings)}",
                "\n🔍 **Key Security Findings**:",
                *[f"• {finding}" for finding in repo_info.security_findings[:5]],
                "\nUse this analysis to provide specific, actionable security recommendations."
            ])
        else:
            context_lines.append("\n💡 **No current repository analysis available.** Please run a security scan first for specific recommendations.")
        
        context_lines.extend([
            "\n📋 **Response Guidelines**:",
            "• Keep responses focused on security topics only",
            "• Use bullet points and numbered lists for clarity", 
            "• Provide specific, implementable solutions",
            "• Include code examples when relevant",
            "• Reference security standards (OWASP, NIST) when applicable"
        ])
        
        system_context = "\n".join(context_lines)

        # Create focused security prompt
        prompt = f"""
{system_context}

Security Question: {current_question}

Provide a comprehensive security-focused response with actionable recommendations.
Use clear structure with bullet points and specific steps.
"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"Chat error details: {str(e)}")
        return "I'm having trouble processing your security question. Please try asking about specific security topics like vulnerabilities, best practices, or security configurations."

def analyze_github_repo(repo_url: str, model_type: str = 'smart') -> str:
    """Analyzes a public GitHub repository for potential security issues."""
    if not github_client:
        return "GitHub client not available. Please check your setup."
    
    try:
        # Extract owner and repo name from the URL
        repo_url = repo_url.rstrip('/').replace('.git', '')
        parts = repo_url.split('/')
        if len(parts) < 5 or parts[2].lower() != 'github.com':
            return "Invalid repository URL format. Expected: https://github.com/owner/repo"
        
        owner, repo_name = parts[-2], parts[-1]
        
        # Try to access the repository
        repo = github_client.get_repo(f"{owner}/{repo_name}")
        print(f"📂 Accessing repository: {owner}/{repo_name}")
        
        # Check rate limit for anonymous users (with error handling)
        try:
            rate_limit = github_client.get_rate_limit()
            if hasattr(rate_limit, 'core'):
                remaining = rate_limit.core.remaining
            elif hasattr(rate_limit, 'search'):
                remaining = rate_limit.search.remaining  
            else:
                remaining = 1000  # Assume reasonable limit if can't determine
                
            if not GITHUB_TOKEN and remaining < 10:
                return f"GitHub API rate limit approaching ({remaining} requests remaining). Please add a GITHUB_PAT token to your .env file for higher limits."
        except Exception as e:
            print(f"⚠️ Could not check rate limit: {e}")
            # Continue without rate limit check
        
        # --- Scan Repository ---
        security_findings = []
        all_files_visited = []
        
        def scan_directory(path="", max_files=100):
            """Recursively scan directory, flagging sensitive file names."""
            try:
                contents = repo.get_contents(path)
                if not isinstance(contents, list):
                    contents = [contents]
                    
                for content in contents:
                    if len(all_files_visited) >= max_files:
                        security_findings.append(f"⚠️ File scan limit reached ({max_files} files). Use GitHub token for complete analysis.")
                        return
                        
                    if content.type == "dir":
                        scan_directory(content.path, max_files)
                    else:
                        all_files_visited.append(f"- {content.path}")
                        # Check for sensitive patterns
                        sensitive_patterns = ['secret', 'password', 'key', '.env', 'config', 'credential', 'token']
                        if any(p in content.path.lower() for p in sensitive_patterns):
                            security_findings.append(f"⚠️ Potentially sensitive file found: {content.path}")
                        
                        # Check for security-related files
                        if content.name.lower() in ['security.md', 'security.txt', 'dockerfile', 'docker-compose.yml']:
                            security_findings.append(f"✅ Security-related file found: {content.path}")
                            
            except Exception as e:
                security_findings.append(f"⚠️ Could not access {path}: {str(e)}")

        print("🔍 Scanning repository contents...")
        scan_directory()

        # Check for common security files
        security_files_to_check = [
            ('SECURITY.md', 'Security policy'),
            ('.github/SECURITY.md', 'GitHub security policy'), 
            ('requirements.txt', 'Python dependencies'),
            ('package.json', 'Node.js dependencies'),
            ('Dockerfile', 'Container configuration'),
            ('docker-compose.yml', 'Docker compose configuration')
        ]
        
        for file_path, description in security_files_to_check:
            try:
                content = repo.get_contents(file_path)
                security_findings.append(f"✅ Found {description}: {file_path}")
            except:
                pass  # File doesn't exist

        # --- Store Analysis and Generate Report ---
        RepoAnalysis.latest_analysis = RepoAnalysis(
            repo_name=repo.full_name,
            description=repo.description or 'No description',
            language=repo.language or 'Unknown',
            files_scanned=all_files_visited,
            security_findings=security_findings,
            open_issues=repo.open_issues_count
        )
        
        # Prepare the initial prompt for the security analysis
        security_prompt = f"""
        Perform a detailed security analysis of the following GitHub repository based on the initial scan data.

        **Repository Info:**
        - **Name**: {repo.full_name}
        - **Description**: {repo.description or 'No description'}
        - **Primary Language**: {repo.language or 'Unknown'}
        - **Open Issues**: {repo.open_issues_count}
        - **Stars**: {repo.stargazers_count}
        - **Forks**: {repo.forks_count}
        - **Files Scanned**: {len(all_files_visited)}
        
        **Security Findings:**
        {chr(10).join(security_findings) if security_findings else "No specific security findings detected."}
        
        **Please provide a comprehensive security analysis report covering:**
        1. **Overall Security Assessment** - Rate the repository's security posture
        2. **Vulnerabilities Found** - Detail any security issues discovered
        3. **Sensitive Information Risks** - Assess potential data exposure
        4. **Missing Security Best Practices** - Identify gaps in security implementation
        5. **Actionable Recommendations** - Provide specific, implementable security improvements
        6. **Repository Structure Analysis** - Evaluate the overall project security architecture
        
        Format your response with clear sections, use bullet points for lists, and provide specific examples where possible.
        """
        
        # Format the prompt as the first message in a new chat history
        history = [{"role": "user", "parts": [{"text": security_prompt}]}]
        
        return get_chat_response(history, model_type)

    except GithubException as e:
        if e.status == 404:
            return "Repository not found. Please check that the URL is correct and the repository is public."
        elif e.status == 401:
            return "GitHub authentication failed. For private repositories, please add a GITHUB_PAT token to your .env file."
        elif e.status == 403:
            return "GitHub API rate limit exceeded. Please add a GITHUB_PAT token to your .env file for higher rate limits."
        return f"GitHub API error: {e.status} - {e.data.get('message', 'Unknown error')}"
    except Exception as e:
        print(f"Error analyzing repository: {str(e)}")
        return f"An unexpected error occurred during the repository analysis: {str(e)}"