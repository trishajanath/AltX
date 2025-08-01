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
    try:
        github_client = Github(GITHUB_TOKEN)
        # Test the connection immediately
        test_user = github_client.get_user()
        print(f"✅ GitHub client initialized for user: {test_user.login}")
    except Exception as e:
        print(f"❌ GitHub client initialization failed: {e}")
        github_client = Github()  # Fallback to anonymous
        print("⚠️ Falling back to anonymous GitHub access")
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

def format_chat_response(text: str) -> str:
    """Format the AI response for better readability - strip HTML and format as clean text"""
    
    # Clean up the text
    formatted = text.strip()
    
    # Remove HTML tags and styling
    import re
    # Remove HTML tags
    formatted = re.sub(r'<[^>]+>', '', formatted)
    # Remove HTML entities
    formatted = formatted.replace('&nbsp;', ' ')
    formatted = formatted.replace('&lt;', '<')
    formatted = formatted.replace('&gt;', '>')
    formatted = formatted.replace('&amp;', '&')
    
    # Remove excessive dashes and separators
    formatted = re.sub(r'---+', '', formatted)
    formatted = re.sub(r'═══+', '', formatted)
    
    # Clean up spacing
    formatted = re.sub(r'\n\s*\n\s*\n', '\n\n', formatted)
    
    # Ensure proper spacing around emojis and headers
    emojis = ['✅', '❌', '⚠️', '🚨', '📊', '🔒', '🛡️', '🔐', '🌐', '🎯', '⚡', '📂', '🔍']
    for emoji in emojis:
        formatted = formatted.replace(emoji, f'\n{emoji}')
    
    # Fix headers
    formatted = re.sub(r'(##?\s*[🛡️🚨⚠️✅❌📊🎯⚡📂🔍].*)', r'\n\n\1', formatted)
    
    # Clean up excessive line breaks
    while '\n\n\n' in formatted:
        formatted = formatted.replace('\n\n\n', '\n\n')
    
    # Ensure response starts clean
    formatted = formatted.lstrip('\n')
    
    return formatted

def get_chat_response(history: List[Dict], model_type: str = 'fast') -> str:
    model = get_model(model_type)
    if model is None:
        return f"❌ **AI model ({model_type}) is not available**"

    try:
        # Enhanced context with strict formatting requirements
        context = """You are a friendly cybersecurity expert assistant. IMPORTANT: Always respond with clean, readable text only - NO HTML, NO styling tags, NO div elements.

**FORMATTING REQUIREMENTS:**
- Use **bold text** for headings (markdown style)
- Use bullet points (•) for lists
- Use emojis (✅ ❌ ⚠️ 🚨 🔒 🛡️ 🔐 🌐 🎯 ⚡ 📂 🔍 📊 💡 🔧 📝 ℹ️) for status indicators
- Add clear line breaks between sections
- Provide specific, actionable recommendations
- Keep responses well-organized and easy to scan
- DO NOT use HTML tags, div elements, or styling
- Use plain text formatting only
- Make responses conversational and user-friendly
- Explain technical concepts in simple terms
- Provide step-by-step guidance when possible

**RESPONSE STRUCTURE:**
1. Start with a friendly greeting and brief summary
2. Use clear section headers with ## 
3. Provide detailed analysis with examples
4. End with actionable recommendations
5. Use friendly, encouraging tone

**CONVERSATION STYLE:**
- Be helpful and encouraging - like a knowledgeable friend
- Explain security concepts in simple, everyday terms
- Provide practical, actionable advice
- Use examples and analogies when helpful
- Acknowledge user concerns and questions
- Be supportive of security improvement efforts
- Avoid overwhelming users with too much technical detail
- Focus on the most important actions first
- Keep implementation checklists simple and focused

**IMPLEMENTATION CHECKLIST STYLE:**
- Only show the most critical and high-priority items
- Use simple, clear language
- Focus on 3-5 most important actions
- Avoid listing every possible security measure
- Make it easy to understand and implement

CRITICAL: Return only clean text - no HTML formatting, no <div> tags, no styling attributes."""
        
        if RepoAnalysis.latest_analysis:
            context += f"""

📂 **CURRENT REPOSITORY CONTEXT:**
**Repository:** {RepoAnalysis.latest_analysis.repo_name}
**Language:** {RepoAnalysis.latest_analysis.language}
**Files Scanned:** {len(RepoAnalysis.latest_analysis.files_scanned)}
**Open Issues:** {RepoAnalysis.latest_analysis.open_issues}

**Security Findings:**
{chr(10).join([f'• {finding}' for finding in RepoAnalysis.latest_analysis.security_findings[:10]])}

**IMPORTANT:** Base your answers on these actual scan results. Reference specific findings when providing recommendations."""
        
        # Convert history to Gemini format
        formatted_history = [{
            'parts': [{'text': context}],
            'role': 'model'
        }]
        
        for msg in history:
            if isinstance(msg.get('parts'), list):
                content = msg['parts'][0]
            elif isinstance(msg.get('parts'), dict):
                content = msg['parts'].get('text', '')
            else:
                content = msg.get('user') or msg.get('ai') or msg.get('content', '')
            
            role = 'user' if msg.get('type') == 'user' or msg.get('role') == 'user' else 'model'
            formatted_history.append({
                'parts': [{'text': str(content)}],
                'role': role
            })

        # Create chat session
        chat = model.start_chat(history=formatted_history[:-1])
        
        # Get the last user message
        last_message = formatted_history[-1]['parts'][0]['text']
        
        # Send message and get response
        response = chat.send_message(last_message)
        
        # Format the response for better readability
        formatted_response = format_chat_response(response.text.strip())
        return formatted_response
        
    except Exception as e:
        return f"❌ **Chat Error:** {str(e)}"

def analyze_github_repo(repo_url: str, model_type: str = 'smart') -> str:
    """Analyzes a GitHub repository for potential security issues."""
    if not github_client:
        return "❌ **GitHub client not available.** Please check your setup."
    
    try:
        # Extract owner and repo name from the URL
        repo_url = repo_url.rstrip('/').replace('.git', '')
        parts = repo_url.split('/')
        if len(parts) < 5 or parts[2].lower() != 'github.com':
            return "❌ **Invalid repository URL format.** Expected: https://github.com/owner/repo"
        
        owner, repo_name = parts[-2], parts[-1]
        
        # Try to access the repository
        repo = github_client.get_repo(f"{owner}/{repo_name}")
        print(f"📂 Accessing repository: {owner}/{repo_name}")
        
        # Check rate limit for anonymous users
        try:
            rate_limit = github_client.get_rate_limit()
            remaining = getattr(rate_limit.core, 'remaining', 1000)
            if not GITHUB_TOKEN and remaining < 10:
                return f"⚠️ **GitHub API rate limit approaching** ({remaining} requests remaining). Please add a GITHUB_PAT token to your .env file for higher limits."
        except Exception as e:
            print(f"⚠️ Could not check rate limit: {e}")
        
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
                        all_files_visited.append(content.path)
                        # Check for sensitive patterns
                        sensitive_patterns = ['secret', 'password', 'key', '.env', 'config', 'credential', 'token']
                        if any(p in content.path.lower() for p in sensitive_patterns):
                            security_findings.append(f"🚨 Potentially sensitive file: {content.path}")
                        
                        # Check for security-related files
                        if content.name.lower() in ['security.md', 'security.txt', 'dockerfile', 'docker-compose.yml']:
                            security_findings.append(f"✅ Security-related file: {content.path}")
                            
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
            ('package-lock.json', 'Node.js dependency lock'),
            ('yarn.lock', 'Yarn dependency lock'),
            ('Pipfile', 'Python pipenv dependencies'),
            ('Dockerfile', 'Container configuration'),
            ('docker-compose.yml', 'Docker compose configuration'),
            ('.github/workflows', 'CI/CD workflows'),
            ('.gitignore', 'Git ignore patterns')
        ]
        
        for file_path, description in security_files_to_check:
            try:
                content = repo.get_contents(file_path)
                if isinstance(content, list):
                    security_findings.append(f"📁 Found {description} directory: {file_path}")
                else:
                    security_findings.append(f"📄 Found {description}: {file_path}")
            except:
                pass  # File doesn't exist

        # --- Store Analysis Results ---
        RepoAnalysis.latest_analysis = RepoAnalysis(
            repo_name=repo.full_name,
            description=repo.description or 'No description',
            language=repo.language or 'Unknown',
            files_scanned=all_files_visited,
            security_findings=security_findings,
            open_issues=repo.open_issues_count
        )
        
        # Enhanced security analysis prompt
        security_prompt = f"""
        **REPOSITORY SECURITY ANALYSIS REQUEST**

        Analyze the following GitHub repository for security vulnerabilities and provide a comprehensive security assessment.

        **📊 Repository Information:**
        • **Name:** {repo.full_name}
        • **Description:** {repo.description or 'No description provided'}
        • **Primary Language:** {repo.language or 'Unknown'}
        • **Open Issues:** {repo.open_issues_count}
        • **Stars:** {repo.stargazers_count}
        • **Forks:** {repo.forks_count}
        • **Files Analyzed:** {len(all_files_visited)}

        **🔍 Security Scan Results:**
        {chr(10).join(security_findings) if security_findings else "• No specific security findings detected during initial scan"}

        **📋 FILES SCANNED ({len(all_files_visited)} total):**
        {chr(10).join([f"• {file}" for file in all_files_visited[:20]])}
        {f"• ... and {len(all_files_visited) - 20} more files" if len(all_files_visited) > 20 else ""}

        **REQUIRED ANALYSIS SECTIONS:**

        ## 🛡️ **Overall Security Assessment**
        Provide a security rating (High/Medium/Low) and explain the reasoning.

        ## 🚨 **Critical Security Issues**
        List any high-priority security vulnerabilities found.

        ## ⚠️ **Potential Security Risks**
        Identify possible security concerns that need attention.

        ## ✅ **Security Best Practices Found**
        Highlight what the repository is doing well security-wise.

        ## 🎯 **Immediate Action Items**
        Provide 3-5 specific, actionable recommendations with examples.

        ## 📊 **Repository Structure Analysis**
        Evaluate the overall project security architecture and file organization.

        ## 💡 **Long-term Security Improvements**
        Suggest additional security measures for enhanced protection.

        **FORMAT REQUIREMENTS:**
        • Use clear section headers with emojis
        • Provide specific examples and code snippets where applicable
        • Make recommendations actionable and implementation-ready
        • Use bullet points for better readability
        • Include severity levels for issues (Critical/High/Medium/Low)
        """
        
        # Get AI analysis using the chat system
        history = [{"type": "user", "parts": [security_prompt]}]
        return get_chat_response(history, model_type)

    except GithubException as e:
        if e.status == 404:
            return "❌ **Repository not found.** Please check that the URL is correct and the repository is public."
        elif e.status == 401:
            return "❌ **GitHub authentication failed.** For private repositories, please add a GITHUB_PAT token to your .env file."
        elif e.status == 403:
            return "❌ **GitHub API rate limit exceeded.** Please add a GITHUB_PAT token to your .env file for higher rate limits."
        return f"❌ **GitHub API error:** {e.status} - {e.data.get('message', 'Unknown error')}"
    except Exception as e:
        print(f"Error analyzing repository: {str(e)}")
        return f"❌ **An unexpected error occurred during repository analysis:** {str(e)}"

def analyze_scan_with_llm(https: bool, flags: List[str], headers: Dict[str, str], model_type: str = 'fast') -> str:
    """Generates a detailed security report with structured containers."""
    model = get_model(model_type)
    if not model:
        return f"❌ **AI model ({model_type}) is not available.**"

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
    
    # System prompt for generating user-friendly output
    system_prompt = """You are a friendly cybersecurity expert. Create a conversational, easy-to-understand security analysis.

    FORMATTING REQUIREMENTS:
    - Use clear section headers with emojis
    - Include visual indicators (✅❌⚠️🚨) for easy scanning
    - Make responses conversational and encouraging
    - Focus on the most important actionable recommendations
    - Explain technical concepts in simple terms
    - Keep implementation checklists focused on 3-5 key items
    - Avoid overwhelming users with too much detail
    """
    
    user_prompt = f"""
SECURITY SCAN RESULTS:
- HTTPS Status: {'✅ Enabled' if https else '❌ Not Enabled'}
- Vulnerabilities Found: {len(flags)} issues
- Headers Analyzed: {len(headers)} headers
- Security Level: {security_level}
- Security Score: {min(100, security_score)}/100

Create a bullet-point only security analysis with these sections:

## 🤖 **Security Analysis Summary**
• Security Level: {security_level}
• Security Score: {min(100, security_score)}/100

## ✅ **What's Working Well**
{chr(10).join(implemented_features[:3]) if implemented_features else "• Website is accessible and responsive"}

## ⚠️ **Areas for Improvement**
{chr(10).join(missing_features[:3]) if missing_features else "• No major issues detected"}

## 🚨 **Key Issues Found**
{chr(10).join([f"• {flag}" for flag in flags[:3]]) if flags else "• No critical vulnerabilities detected"}

## 🎯 **Quick Recommendations**
• {"Enable HTTPS/SSL certificate immediately" if not https else "Implement missing security headers"}
• Add the most important security headers this week
• Test all implementations thoroughly

Use ONLY bullet points - no paragraphs or long explanations!
"""

    try:
        response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
        
        # Post-process for better container formatting
        formatted_response = format_chat_response(response.text.strip())
        return formatted_response
        
    except Exception as e:
        # Fallback bullet-point format
        return f"""
## 🤖 **Security Analysis Summary**
• Security Level: {security_level}
• Security Score: {min(100, security_score)}/100

## ✅ **What's Working Well**
{chr(10).join(implemented_features[:3]) if implemented_features else "• Website is accessible and responsive"}

## ⚠️ **Areas for Improvement**
{chr(10).join(missing_features[:3]) if missing_features else "• No major issues detected"}

## 🚨 **Key Issues Found**
{chr(10).join([f"• {flag}" for flag in flags[:3]]) if flags else "• No critical vulnerabilities detected"}

## 🎯 **Quick Recommendations**
• {"Enable HTTPS/SSL certificate immediately" if not https else "Implement missing security headers"}
• Add the most important security headers this week
• Test all implementations thoroughly

**Note:** There was a technical issue with the AI analysis, but I've provided you with the essential information above.
"""