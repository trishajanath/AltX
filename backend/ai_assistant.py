import google.generativeai as genai
import os
from typing import List, Dict, Optional, ClassVar, Union, Any
from dotenv import load_dotenv
from github import Github
from github.GithubException import GithubException
from dataclasses import dataclass
from rag_query import get_secure_coding_patterns
import json

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

# --- Initialize API Clients ---
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
    """Enhanced chat response with model selection and comprehensive context"""
    model = get_model(model_type)
    if model is None:
        return f"❌ **AI model ({model_type}) is not available**"

    try:
        # Enhanced context based on model type
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
        else:  # fast model
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
        
        # Add current analysis context if available
        if RepoAnalysis.latest_analysis:
            if isinstance(RepoAnalysis.latest_analysis, dict):
                # Handle new comprehensive analysis format from /analyze-repo
                repo_info = RepoAnalysis.latest_analysis.get('repository_info', {})
                security_summary = RepoAnalysis.latest_analysis.get('security_summary', {})
                
                if model_type == 'smart':
                    context += f"""

📂 **COMPREHENSIVE REPOSITORY CONTEXT:**
**Repository:** {repo_info.get('name', 'Unknown')} ({repo_info.get('language', 'Unknown')})
**Description:** {repo_info.get('description', 'No description')}
**Security Score:** {RepoAnalysis.latest_analysis.get('overall_security_score', 'N/A')}/100 ({RepoAnalysis.latest_analysis.get('security_level', 'Unknown')})

**DETAILED SECURITY METRICS:**
• Files Scanned: {security_summary.get('total_files_scanned', 0)}
• Sensitive Files: {security_summary.get('sensitive_files_found', 0)}
• Hardcoded Secrets: {security_summary.get('secrets_found', 0)}
• Static Analysis Issues: {security_summary.get('static_issues_found', 0)}
• Vulnerable Dependencies: {security_summary.get('vulnerable_dependencies', 0)}
• Code Quality Issues: {security_summary.get('code_quality_issues', 0)}
• Security Files Present: {security_summary.get('security_files_present', 0)}

**CRITICAL FINDINGS SUMMARY:**
• Secret Scan: {len(RepoAnalysis.latest_analysis.get('secret_scan_results', []))} secrets detected
• Code Quality: {len(RepoAnalysis.latest_analysis.get('code_quality_results', []))} patterns found
• Dependencies: {len(RepoAnalysis.latest_analysis.get('dependency_scan_results', {}).get('vulnerable_packages', []))} vulnerable packages
• Static Analysis: {len(RepoAnalysis.latest_analysis.get('static_analysis_results', []))} issues found

**TOP RECOMMENDATIONS:**
{chr(10).join([f'• {rec}' for rec in RepoAnalysis.latest_analysis.get('recommendations', [])[:5]])}

**RECENT FINDINGS DETAILS:**
{chr(10).join([f'• {finding.get("file", "unknown")}: {finding.get("description", "Security issue")}' for finding in RepoAnalysis.latest_analysis.get('secret_scan_results', [])[:3]])}
{chr(10).join([f'• {finding.get("file", "unknown")}: {finding.get("pattern", "unknown")} ({finding.get("severity", "unknown")} severity)' for finding in RepoAnalysis.latest_analysis.get('code_quality_results', [])[:3]])}"""
                else:  # fast model
                    context += f"""

📂 **REPOSITORY CONTEXT:**
**Repository:** {repo_info.get('name', 'Unknown')} - Security Score: {RepoAnalysis.latest_analysis.get('overall_security_score', 'N/A')}/100
**Key Issues:** {security_summary.get('secrets_found', 0)} secrets, {security_summary.get('code_quality_issues', 0)} code issues, {security_summary.get('vulnerable_dependencies', 0)} vulnerable deps
**Priority Actions:** {', '.join(RepoAnalysis.latest_analysis.get('recommendations', [])[:2])}"""
            else:
                # Handle legacy RepoAnalysis format
                context += f"""

📂 **REPOSITORY CONTEXT:**
**Repository:** {RepoAnalysis.latest_analysis.repo_name}
**Language:** {RepoAnalysis.latest_analysis.language}
**Security Findings:** {len(RepoAnalysis.latest_analysis.security_findings)} issues found
**Recent Findings:** {', '.join(RepoAnalysis.latest_analysis.security_findings[:3])}"""
        
        # Build conversation history with proper error handling
        formatted_history = [{'parts': [{'text': context}], 'role': 'model'}]
        for msg in history:
            try:
                # Handle different message formats
                if isinstance(msg.get('parts'), list):
                    # Handle parts as list of dicts: [{"text": "content"}]
                    if len(msg['parts']) > 0 and isinstance(msg['parts'][0], dict):
                        content = msg['parts'][0].get('text', '')
                    # Handle parts as list with string: ["content"]
                    elif len(msg['parts']) > 0 and isinstance(msg['parts'][0], str):
                        content = msg['parts'][0]
                    else:
                        content = str(msg.get('parts', ''))
                elif isinstance(msg.get('parts'), dict):
                    # Handle parts as single dict: {"text": "content"}
                    content = msg['parts'].get('text', '')
                elif isinstance(msg.get('parts'), str):
                    # Handle parts as string: "content"
                    content = msg['parts']
                else:
                    # Fallback: try to get message content from other fields
                    content = msg.get('message', msg.get('content', str(msg.get('parts', ''))))
                
                role = 'user' if msg.get('type') == 'user' or msg.get('role') == 'user' else 'model'
                formatted_history.append({'parts': [{'text': str(content)}], 'role': role})
            except Exception as e:
                print(f"Warning: Error processing message in history: {e}")
                # Skip malformed messages
                continue

        # Use selected model for response
        chat = model.start_chat(history=formatted_history[:-1])
        last_message = formatted_history[-1]['parts'][0]['text']
        response = chat.send_message(last_message)
        
        # Enhanced response formatting based on model type
        formatted_response = format_chat_response(response.text.strip())
        
        if model_type == 'smart':
            # Add model indicator for comprehensive responses
            return f"🧠 **Comprehensive Analysis** (Smart Model)\n\n{formatted_response}"
        else:
            # Add model indicator for quick responses
            return f"⚡ **Quick Analysis** (Fast Model)\n\n{formatted_response}"
        
    except Exception as e:
        return f"❌ **Chat Error ({model_type} model):** {str(e)}"
# --- Main Analysis Function ---
def analyze_github_repo(repo_url: str, model_type: str = 'smart') -> str:
    """Analyze GitHub repository with model selection"""
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
        
        history = [{"type": "user", "parts": [{"text": security_prompt}]}]
        return get_chat_response(history, model_type)

    except Exception as e:
        print(f"Error analyzing repository: {str(e)}")
        return f"❌ **An unexpected error occurred:** {str(e)}"
    finally:
        if Path(local_repo_path).exists():
            shutil.rmtree(local_repo_path)

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
    
# Add this function after the existing functions

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