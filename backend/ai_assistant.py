import google.generativeai as genai
import os
from typing import List, Dict, Optional, ClassVar
from dotenv import load_dotenv
from github import Github
from github.GithubException import GithubException
from dataclasses import dataclass

# --- PHASE 1 IMPORTS ---
import git
import shutil
from pathlib import Path
from scanner.secrets_detector import scan_secrets
from scanner.static_python import run_bandit # --- PHASE 1B ---

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
    latest_analysis: ClassVar[Optional['RepoAnalysis']] = None

# Load environment variables from a .env file
load_dotenv()

# Available models configuration
AVAILABLE_MODELS = {
    'fast': 'models/gemini-2.5-flash',
    'smart': 'models/gemini-2.5-pro'
}

# --- Initialize API Clients (no changes in this section) ---
models = {}
GITHUB_TOKEN = os.getenv("GITHUB_PAT")

if GITHUB_TOKEN:
    try:
        github_client = Github(GITHUB_TOKEN)
        test_user = github_client.get_user()
        print(f"✅ GitHub client initialized for user: {test_user.login}")
    except Exception as e:
        print(f"❌ GitHub client initialization failed: {e}")
        github_client = Github()
        print("⚠️ Falling back to anonymous GitHub access")
else:
    github_client = Github()
    print("⚠️ GitHub client initialized without token (public repos only)")

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

# --- Helper functions (no changes in this section) ---
def get_model(model_type: str = 'fast') -> Optional[genai.GenerativeModel]:
    return models.get(model_type)

def format_chat_response(text: str) -> str:
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
    model = get_model(model_type)
    if model is None:
        return f"❌ **AI model ({model_type}) is not available**"

    try:
        context = "You are a friendly cybersecurity expert assistant..." # (rest of context is unchanged)
        
        if RepoAnalysis.latest_analysis:
            context += f"""

📂 **CURRENT REPOSITORY CONTEXT:**
**Repository:** {RepoAnalysis.latest_analysis.repo_name}
**Language:** {RepoAnalysis.latest_analysis.language}
**Security Findings:**
{chr(10).join([f'• {finding}' for finding in RepoAnalysis.latest_analysis.security_findings[:15]])}
"""
        
        formatted_history = [{'parts': [{'text': context}], 'role': 'model'}]
        for msg in history:
            content = msg.get('parts', [{}])[0].get('text', '') if isinstance(msg.get('parts'), list) else msg.get('parts', {}).get('text', '')
            role = 'user' if msg.get('type') == 'user' or msg.get('role') == 'user' else 'model'
            formatted_history.append({'parts': [{'text': str(content)}], 'role': role})

        chat = model.start_chat(history=formatted_history[:-1])
        last_message = formatted_history[-1]['parts'][0]['text']
        response = chat.send_message(last_message)
        return format_chat_response(response.text.strip())
        
    except Exception as e:
        return f"❌ **Chat Error:** {str(e)}"

# --- Main Analysis Function ---
def analyze_github_repo(repo_url: str, model_type: str = 'smart') -> str:
    if not github_client:
        return "❌ **GitHub client not available.** Please check your setup."
    
    repo_name_from_url = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
    local_repo_path = f"/tmp/{repo_name_from_url}"

    try:
        repo_url = repo_url.rstrip('/').replace('.git', '')
        parts = repo_url.split('/')
        if len(parts) < 5 or parts[2].lower() != 'github.com':
            return "❌ **Invalid repository URL format.**"
        
        owner, repo_name = parts[-2], parts[-1]
        repo = github_client.get_repo(f"{owner}/{repo_name}")
        
        print(f"Cloning {repo_url} to {local_repo_path}...")
        if Path(local_repo_path).exists():
            shutil.rmtree(local_repo_path)
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

        # --- Store Analysis Results ---
        RepoAnalysis.latest_analysis = RepoAnalysis(
            repo_name=repo.full_name,
            description=repo.description or 'No description',
            language=repo.language or 'Unknown',
            files_scanned=all_files_visited,
            security_findings=security_findings,
            open_issues=repo.open_issues_count
        )
        
        # --- PHASE 1B: Update AI prompt with both scan results ---
        secret_findings_summary = "\n".join([f"• {s}" for s in security_findings if "secret" in s.lower()])
        static_findings_summary = "\n".join([f"• {s}" for s in security_findings if "Bandit" in s or "Python code" in s])

        security_prompt = f"""
**REPOSITORY SECURITY ANALYSIS REQUEST**
Analyze the GitHub repository below based on my scan results.

**📊 Repository Information:**
• **Name:** {repo.full_name}
• **Primary Language:** {repo.language or 'Unknown'}

**🔑 Hardcoded Secrets Scan Results:**
{secret_findings_summary if secret_findings_summary else "• ✅ No hardcoded secrets were found."}

**🐍 Python Static Analysis Results (Bandit):**
{static_findings_summary if static_findings_summary else "• ✅ No medium or high-severity static analysis issues found in Python code."}

Please provide a structured analysis with these sections:
## 🛡️ Overall Security Assessment
## 🚨 Critical Security Issues (Prioritize secrets, then high-severity Bandit findings)
## ⚠️ Potential Security Risks
## 🎯 Immediate Action Items (Provide a checklist)
## 💡 Long-term Security Improvements

**FORMAT REQUIREMENTS:**
• Use clean text formatting only with markdown-style headers. NO HTML.
"""
        
        history = [{"type": "user", "parts": [security_prompt]}]
        return get_chat_response(history, model_type)

    except Exception as e:
        print(f"Error analyzing repository: {str(e)}")
        return f"❌ **An unexpected error occurred:** {str(e)}"
    finally:
        if Path(local_repo_path).exists():
            shutil.rmtree(local_repo_path)

# --- The analyze_scan_with_llm function remains unchanged ---
# Replace the incomplete analyze_scan_with_llm function in ai_assistant.py with this:

def analyze_scan_with_llm(https: bool, flags: List[str], headers: Dict[str, str], model_type: str = 'fast') -> str:
    """Analyze scan results using LLM"""
    model = get_model(model_type)
    if model is None:
        return f"❌ **AI model ({model_type}) is not available**"
    
    try:
        # Create analysis prompt
        security_prompt = f"""
**WEBSITE SECURITY ANALYSIS REQUEST**

Analyze the following website security scan results and provide actionable recommendations.

**🔒 Security Status:**
• **HTTPS Enabled:** {'✅ Yes' if https else '❌ No'}
• **Security Issues Found:** {len(flags)} issues detected
• **HTTP Headers Analyzed:** {len(headers)} headers present

**🚨 Security Issues Detected:**
{chr(10).join([f'• {flag}' for flag in flags]) if flags else '• ✅ No critical security issues detected'}

**📋 HTTP Headers Present:**
{chr(10).join([f'• {key}: {value}' for key, value in headers.items()]) if headers else '• No headers detected'}

Please provide a structured analysis with these sections:

## 🛡️ Overall Security Assessment
Provide a security rating and summary of the website's security posture.

## 🚨 Critical Issues
List the most important security vulnerabilities that need immediate attention.

## ⚠️ Recommendations
Provide specific, actionable steps to improve security.

## 💡 Implementation Guide
Give practical examples of how to implement the security improvements.

**FORMAT REQUIREMENTS:**
• Use clean text formatting with markdown-style headers
• Provide specific, actionable recommendations
• Include code examples where helpful
• NO HTML tags or styling
"""
        
        history = [{"type": "user", "parts": [security_prompt]}]
        return get_chat_response(history, model_type)
        
    except Exception as e:
        return f"❌ **Website Analysis Error:** {str(e)}"