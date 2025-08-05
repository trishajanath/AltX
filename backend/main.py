import os
import shutil
import git
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from starlette.concurrency import run_in_threadpool
import tempfile
import json
import re
from scanner.file_security_scanner import scan_for_sensitive_files, scan_file_contents_for_secrets
from scanner.directory_scanner import scan_common_paths
from owasp_mapper import map_to_owasp_top10
from datetime import datetime 
import time
import base64
from github import Github
from rag_query import get_secure_coding_patterns
import tempfile
from rag_query import get_secure_coding_patterns  # Add this
from ai_assistant import FixRequest  # Add this import

# --- Local Imports ---
from ai_assistant import get_chat_response, RepoAnalysis
from scanner.file_scanner import (
    scan_url, 
    _format_ssl_analysis,
    scan_dependencies,
    scan_code_quality_patterns,
    is_likely_false_positive
)
from scanner.hybrid_crawler import crawl_hybrid 
from nlp_suggester import suggest_fixes
import ai_assistant
try:
    from ai_assistant import github_client
except ImportError:
    github_client = None
    print("Warning: GitHub client not available")

# --- Phase 1 Imports ---
from scanner.secrets_detector import scan_secrets
from scanner.static_python import run_bandit

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Storage Classes for Scan Results ---
class WebsiteScan:
    latest_scan = None

class ScanRequest(BaseModel):
    url: str
    model_type: str = 'fast'

class RepoAnalysisRequest(BaseModel):
    repo_url: str
    model_type: str = 'smart'
    deep_scan: bool = True

class OWASPMappingRequest(BaseModel):
    url: str
    repo_url: Optional[str] = None
    model_type: str = "fast"

class FixRequest(BaseModel):
    repo_url: str
    issue: Dict[str, Any]
    branch_name: Optional[str] = None


# --- Enhanced Security Analysis Functions ---
@app.post("/scan")
async def scan(request: ScanRequest):
    """Scan a website for security vulnerabilities and store results for AI chat"""
    url = request.url
    
    try:
        # --- HYBRID CRAWLER INTEGRATION ---
        pages = await crawl_hybrid(url)
        
        # Enhanced scanning with SSL certificate analysis
        scan_result = await run_in_threadpool(scan_url, url)
        
        # Correctly call the async directory scanner
        scan_data = await scan_common_paths(url)
        exposed_paths = scan_data['accessible_paths']
        waf_info = scan_data['waf_analysis']
        dns_security = scan_data['dns_security']        
        
        suggestions = await run_in_threadpool(suggest_fixes, scan_result['headers'])
        ai_advice = await run_in_threadpool(
            ai_assistant.analyze_scan_with_llm,
            scan_result["https"],
            scan_result["flags"],
            scan_result["headers"],
            request.model_type
        )
        
        security_level = scan_result.get("security_level", "Unknown")
        security_score = scan_result.get("security_score", 0)
        
        # Extract SSL analysis data
        ssl_certificate = scan_result.get("ssl_certificate", {})
        
        # Enhanced summary with SSL certificate information (using imported function)
        summary = f"""🔒 **Security Scan Complete**

📊 **Target Analysis:**
• Domain: {scan_data['scan_summary']['domain']}
• Overall Security Score: {security_score}/100 ({security_level})
• HTTPS: {'✅ Enabled' if scan_result["https"] else '❌ Disabled'}
• Vulnerabilities: {len(scan_result["flags"])} issues found
• Pages Crawled: {len(pages)} pages
• Security Headers: {len(scan_result["headers"])} detected
• Exposed Paths: {len(exposed_paths)} found

🛡️ **Web Application Firewall (WAF):**
• WAF Detected: {'✅ Yes' if waf_info['waf_detected'] else '❌ No'}
• WAF Type: {waf_info.get('waf_type', 'None detected')}
• Protection Level: {waf_info.get('protection_level', 'Unknown')}
• Blocked Requests: {waf_info.get('blocked_requests', 0)}/{waf_info.get('total_requests', 0)}

🔐 **DNS Security Features:**
• DNSSEC: {'✅ Enabled' if dns_security['dnssec'].get('enabled') else '❌ Disabled'} - {dns_security['dnssec'].get('status', 'Unknown')}
• DMARC: {'✅ Enabled' if dns_security['dmarc'].get('enabled') else '❌ Not configured'} - {dns_security['dmarc'].get('policy', 'No policy')}
• DKIM: {'✅ Found' if dns_security['dkim'].get('selectors_found') else '❌ Not found'} - {len(dns_security['dkim'].get('selectors_found', []))} selectors

🔐 **SSL/TLS Security Analysis:**
{_format_ssl_analysis(ssl_certificate)}

🚨 **Key Issues Found:**
{chr(10).join([f'• {flag}' for flag in scan_result["flags"][:5]]) if scan_result["flags"] else '• No critical issues detected'}

🚪 **Potentially Exposed Paths:**
{chr(10).join([f'• Found accessible path: {p["path"]}' for p in exposed_paths[:3]]) if exposed_paths else '• No common sensitive paths were found.'}

💡 **Ready to help with specific security questions about this scan!**"""
        
        scan_response = {
            "url": url,
            "pages": pages,
            "scan_result": scan_result,
            "exposed_paths": exposed_paths,
            "waf_analysis": waf_info,          # NEW: WAF detection results
            "dns_security": dns_security,      # NEW: DNSSEC, DMARC, DKIM results
            "suggestions": suggestions,
            "ai_assistant_advice": ai_advice,
            "summary": summary
        }
        
        # Debug logging to see what we're returning
        print(f"🔍 DEBUG - WAF Analysis Data: {waf_info}")
        print(f"🔍 DEBUG - DNS Security Data: {dns_security}")
        print(f"🔍 DEBUG - Scan Response Keys: {list(scan_response.keys())}")
        
        WebsiteScan.latest_scan = scan_response
        return scan_response
        
    except Exception as e:
        error_detail = f"Scan failed for {url}: {str(e)}"
        print(f"❌ {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)


@app.post("/analyze-repo")
async def analyze_repo_comprehensive(request: RepoAnalysisRequest):
    """Comprehensive repository security analysis with file scanning and store results for AI chat"""
    try:
        repo_url = request.repo_url
        model_type = request.model_type
        deep_scan = request.deep_scan
        
        if not repo_url:
            return {"error": "Repository URL is required"}
        
        # Validate model type
        if model_type not in ['fast', 'smart']:
            model_type = 'smart'  # Default fallback
        
        # Create temporary directory for cloning
        temp_dir = tempfile.mkdtemp()
        
        # Verify temp directory is writable
        try:
            test_file = os.path.join(temp_dir, 'test_write.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            return {"error": f"Temporary directory is not writable: {temp_dir}\nError: {e}\nTry running VS Code as administrator or check folder permissions."}
        
        print(f"📁 Created temporary directory: {temp_dir}")
        
        try:
            # Clone the repository for comprehensive analysis
            print(f"🔄 Cloning repository: {repo_url}")
            
            # Handle different URL formats
            clone_url = repo_url
            if not clone_url.endswith('.git'):
                clone_url += '.git'
            
            # Clone repository with proper error handling
            import git
            from git import Repo, GitCommandError
            
            try:
                # Simple clone first - ensure we use the temp_dir we created
                repo = git.Repo.clone_from(clone_url, temp_dir)
                print(f"✅ Repository cloned successfully to {temp_dir}")
                
                # Configure the cloned repo for Windows compatibility
                try:
                    with repo.config_writer() as config_writer:
                        config_writer.set_value("core", "filemode", "false")
                        config_writer.set_value("core", "autocrlf", "true")
                        config_writer.set_value("core", "safecrlf", "false")
                except Exception as config_error:
                    print(f"⚠️ Could not configure Git settings: {config_error}")
                
            except GitCommandError as git_error:
                # Try with different clone options
                print(f"⚠️ Initial clone failed, trying with depth limit: {git_error}")
                try:
                    # Try shallow clone to reduce potential file permission issues
                    repo = git.Repo.clone_from(clone_url, temp_dir, depth=1)
                    print(f"✅ Repository cloned using shallow clone to {temp_dir}")
                    
                    # Configure the cloned repo
                    try:
                        with repo.config_writer() as config_writer:
                            config_writer.set_value("core", "filemode", "false")
                            config_writer.set_value("core", "autocrlf", "true")
                    except Exception as config_error:
                        print(f"⚠️ Could not configure Git settings: {config_error}")
                        
                except GitCommandError as shallow_error:
                    print(f"⚠️ Shallow clone also failed: {shallow_error}")
                    raise Exception(f"All Git clone methods failed. Last error: {shallow_error}")
            
            # Get basic repo info from GitHub API
            repo_url_clean = repo_url.rstrip('/').replace('.git', '')
            parts = repo_url_clean.split('/')
            github_repo = None
            github_error = None
            
            if len(parts) >= 5 and github_client:
                owner, repo_name = parts[-2], parts[-1]
                try:
                    github_repo = github_client.get_repo(f"{owner}/{repo_name}")
                    print(f"✅ Successfully fetched GitHub repo info for {owner}/{repo_name}")
                except Exception as e:
                    github_error = str(e)
                    print(f"⚠️ Could not fetch GitHub repo info: {e}")
                    if "404" in str(e):
                        print(f"💡 Repository might be private or URL might be incorrect")
                    elif "403" in str(e):
                        print(f"💡 API rate limit reached or authentication required")
            
            # 1. Comprehensive file security scan
            print("🔍 Performing comprehensive file security scan...")
            file_scan_results = await run_in_threadpool(scan_for_sensitive_files, temp_dir)
            
            # 2. Deep content scanning for secrets (with proper directory filtering)
            secret_scan_results = []
            if deep_scan:
                print("🕵️ Performing deep content scanning for secrets...")
                scanned_files = 0
                skip_dirs = {
                    'venv', 'env', '.env', 'virtualenv', '__pycache__', 
                    'node_modules', '.git', '.svn', 'build', 'dist', 'target',
                    '.gradle', '.maven', 'vendor', '.next', '.nuxt', 'coverage',
                    'logs', 'tmp', 'temp', '.tmp', '.temp', '.DS_Store', 
                    '.vscode', '.idea', 'docker-data'
                }
                
                for root, dirs, files in os.walk(temp_dir):
                    # Filter out directories we should skip
                    dirs[:] = [d for d in dirs if not any(skip_pattern in d.lower() for skip_pattern in skip_dirs)]
                    
                    # Skip if current directory contains excluded patterns
                    if any(skip_pattern in root.lower() for skip_pattern in skip_dirs):
                        continue
                    
                    for file in files:
                        if scanned_files >= 100:  # Increased limit since we're filtering better
                            break
                        
                        if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.yml', '.yaml', '.env', '.config', '.txt', '.md', '.sh', '.bat')):
                            file_path = os.path.join(root, file)
                            secrets = await run_in_threadpool(scan_file_contents_for_secrets, file_path)
                            
                            # Filter false positives
                            filtered_secrets = []
                            for secret in secrets:
                                if not is_likely_false_positive(file_path, secret.get('secret_type', ''), secret.get('match', '')):
                                    filtered_secrets.append(secret)
                            
                            secret_scan_results.extend(filtered_secrets)
                            scanned_files += 1
            
            # 3. Static Code Analysis with Bandit
            print("🔬 Running static code analysis...")
            static_analysis_results = []
            if deep_scan:
                try:
                    bandit_results = await run_in_threadpool(run_bandit, temp_dir)
                    static_analysis_results = bandit_results if isinstance(bandit_results, list) else []
                except Exception as e:
                    print(f"Static analysis failed: {e}")
                    static_analysis_results = []
            
            # 4. Dependency Vulnerability Scanning
            print("📦 Scanning dependencies for vulnerabilities...")
            dependency_scan_results = await run_in_threadpool(scan_dependencies, temp_dir)
            
            # 5. Code Quality Pattern Detection
            print("🎯 Detecting insecure coding patterns...")
            code_quality_results = await run_in_threadpool(scan_code_quality_patterns, temp_dir)
            
            # Run traditional GitHub API analysis for AI insights
            print("📊 Running AI analysis...")
            try:
                if github_repo:
                    github_analysis = await run_in_threadpool(
                        ai_assistant.analyze_github_repo, 
                        repo_url, 
                        model_type
                    )
                else:
                    # Fallback when GitHub API fails
                    github_analysis = f"""
📊 **Repository Analysis** (Limited - GitHub API unavailable)

**Repository:** {repo_url}
**Status:** Successfully cloned and analyzed locally
**Note:** GitHub API returned error: {github_error or 'Unknown error'} - repository might be private or require authentication

✅ **Local Analysis Completed:**
• File security scanning: Complete
• Secret detection: Complete  
• Static code analysis: Complete
• Dependency scanning: Complete
• Code quality analysis: Complete

💡 **Recommendation:** For full GitHub integration, ensure repository is public or add GitHub token authentication.
"""
            except Exception as e:
                github_analysis = f"⚠️ AI analysis error: {str(e)}"
            
            # Compile comprehensive results
            comprehensive_results = {
                "repository_info": {
                    "url": repo_url,
                    "name": github_repo.full_name if github_repo else "Unknown",
                    "description": github_repo.description if github_repo else "No description",
                    "language": github_repo.language if github_repo else "Unknown",
                    "stars": github_repo.stargazers_count if github_repo else 0,
                    "forks": github_repo.forks_count if github_repo else 0,
                    "open_issues": github_repo.open_issues_count if github_repo else 0
                },
                "file_security_scan": file_scan_results,
                "secret_scan_results": secret_scan_results,
                "static_analysis_results": static_analysis_results,
                "dependency_scan_results": dependency_scan_results,
                "code_quality_results": code_quality_results,
                "ai_analysis": github_analysis,
                "security_summary": {
                    "total_files_scanned": file_scan_results.get('total_files_scanned', 0),
                    "sensitive_files_found": len(file_scan_results.get('sensitive_files', [])),
                    "risky_files_found": len(file_scan_results.get('risky_files', [])),
                    "secrets_found": len(secret_scan_results),
                    "static_issues_found": len(static_analysis_results),
                    "vulnerable_dependencies": len(dependency_scan_results.get('vulnerable_packages', [])),
                    "code_quality_issues": len(code_quality_results),
                    "security_files_present": len(file_scan_results.get('security_files_found', [])),
                    "missing_security_files": len(file_scan_results.get('missing_security_files', []))
                }
            }
            
            # Enhanced security score calculation
            base_score = 70
            
            # Deduct for security issues
            sensitive_files_penalty = min(30, len(file_scan_results.get('sensitive_files', [])) * 10)
            risky_files_penalty = min(20, len(file_scan_results.get('risky_files', [])) * 5)
            secrets_penalty = min(40, len(secret_scan_results) * 15)
            static_analysis_penalty = min(25, len(static_analysis_results) * 5)
            dependency_penalty = min(20, len(dependency_scan_results.get('vulnerable_packages', [])) * 10)
            code_quality_penalty = min(15, len([r for r in code_quality_results if r.get('severity') in ['Critical', 'High']]) * 3)
            
            # Add points for good practices
            security_files_bonus = min(15, len(file_scan_results.get('security_files_found', [])) * 2)
            
            overall_score = max(0, base_score - sensitive_files_penalty - risky_files_penalty - secrets_penalty - static_analysis_penalty - dependency_penalty - code_quality_penalty + security_files_bonus)
            
            comprehensive_results["overall_security_score"] = overall_score
            comprehensive_results["security_level"] = (
                "High" if overall_score >= 80 else 
                "Medium" if overall_score >= 60 else 
                "Low"
            )
            
            # Enhanced recommendations with gitignore guidance
            recommendations = []
            
            if file_scan_results.get('sensitive_files'):
                recommendations.append("🚨 CRITICAL: Remove or secure sensitive files detected")
            
            if secret_scan_results:
                recommendations.append("🔑 CRITICAL: Remove hardcoded secrets from source code")
            
            if static_analysis_results and len(static_analysis_results) > 0:
                recommendations.append("🔬 HIGH: Fix static code analysis vulnerabilities")
            
            if dependency_scan_results.get('vulnerable_packages'):
                recommendations.append("📦 HIGH: Update vulnerable dependencies")
            
            # Add gitignore recommendations for excluded directories
            if file_scan_results.get('excluded_directories'):
                excluded_count = len(file_scan_results['excluded_directories'])
                recommendations.append(f"📁 HIGH: Found {excluded_count} build/dependency directories (venv, __pycache__, node_modules) - Ensure these are in .gitignore")
            
            if file_scan_results.get('gitignore_recommendations'):
                high_priority_gitignore = [rec for rec in file_scan_results['gitignore_recommendations'] if rec['priority'] == 'High']
                if high_priority_gitignore:
                    patterns = [rec['pattern'] for rec in high_priority_gitignore[:3]]
                    recommendations.append(f"📋 HIGH: Add to .gitignore: {', '.join(patterns)}")
            
            critical_code_issues = [r for r in code_quality_results if r.get('severity') in ['Critical', 'High']]
            if critical_code_issues:
                recommendations.append("🎯 HIGH: Address critical insecure coding patterns")
            
            if file_scan_results.get('risky_files'):
                recommendations.append("⚠️ MEDIUM: Review risky file types for security implications")
            
            if file_scan_results.get('missing_security_files'):
                missing = file_scan_results['missing_security_files'][:3]
                recommendations.append(f"📄 MEDIUM: Add missing security files: {', '.join(missing)}")
            
            if not any('security.md' in f.get('type', '') for f in file_scan_results.get('security_files_found', [])):
                recommendations.append("📋 LOW: Add SECURITY.md file with security policy")
            
            comprehensive_results["recommendations"] = recommendations[:10]  # Increased to show more recommendations
            
            # Store results for AI chat context
            RepoAnalysis.latest_analysis = comprehensive_results
            
            return comprehensive_results
            
        except git.exc.GitCommandError as e:
            error_msg = str(e)
            if "Access is denied" in error_msg:
                return {"error": f"Access denied during Git clone. This might be due to:\n• Repository permissions\n• Windows file system restrictions\n• Antivirus software blocking Git operations\n\nTry running VS Code as administrator or temporarily disable antivirus scanning for the temp directory.\n\nOriginal error: {error_msg}"}
            elif "not found" in error_msg.lower():
                return {"error": f"Repository not found. Please verify:\n• Repository URL is correct\n• Repository is public (or you have access)\n• GitHub is accessible from your network\n\nOriginal error: {error_msg}"}
            elif "authentication" in error_msg.lower():
                return {"error": f"Authentication failed. For private repositories:\n• Ensure you have access rights\n• Consider using GitHub token authentication\n\nOriginal error: {error_msg}"}
            else:
                return {"error": f"Git clone failed: {error_msg}"}
        except Exception as e:
            error_msg = str(e)
            if "Access is denied" in error_msg:
                return {"error": f"Windows access denied error. Try:\n• Running VS Code as administrator\n• Checking antivirus settings\n• Ensuring temp directory is writable\n\nOriginal error: {error_msg}"}
            else:
                return {"error": f"Repository analysis failed: {error_msg}"}
        finally:
            # Enhanced cleanup for Git repositories on Windows
            if os.path.exists(temp_dir):
                try:
                    import stat
                    import time
                    
                    def force_remove_readonly(func, path, exc_info):
                        """Enhanced readonly handler for Git objects"""
                        try:
                            if os.path.exists(path):
                                # Make file writable
                                os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
                                # Try the original function again
                                func(path)
                        except Exception as e:
                            print(f"⚠️ Could not remove {path}: {e}")
                    
                    def cleanup_git_directory(directory):
                        """Special cleanup for Git directories"""
                        try:
                            # First, try to make all files in .git writable
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
                    
                    # Special handling for Git directories
                    cleanup_git_directory(temp_dir)
                    
                    # Wait a moment for file handles to close
                    time.sleep(0.1)
                    
                    # Remove the directory
                    shutil.rmtree(temp_dir, onerror=force_remove_readonly)
                    print(f"✅ Temporary directory cleaned up: {temp_dir}")
                    
                except Exception as e:
                    # Try alternative cleanup methods
                    try:
                        import subprocess
                        print(f"⚠️ Standard cleanup failed, trying alternative method: {e}")
                        
                        if os.name == 'nt':  # Windows
                            # Use rmdir with force options
                            result = subprocess.run([
                                'rmdir', '/s', '/q', temp_dir
                            ], shell=True, capture_output=True, text=True)
                            
                            if result.returncode == 0:
                                print(f"✅ Directory cleaned up using rmdir")
                            else:
                                # Try powershell as last resort
                                ps_result = subprocess.run([
                                    'powershell', '-Command', 
                                    f'Remove-Item -Recurse -Force "{temp_dir}" -ErrorAction SilentlyContinue'
                                ], capture_output=True, text=True)
                                
                                if ps_result.returncode == 0:
                                    print(f"✅ Directory cleaned up using PowerShell")
                                else:
                                    print(f"⚠️ Could not fully clean temp directory: {temp_dir}")
                        else:
                            subprocess.run(['rm', '-rf', temp_dir], check=False)
                            
                    except Exception as e2:
                        print(f"⚠️ Warning: Could not clean up temp directory {temp_dir}: {e2}")
                        print(f"💡 You may need to manually delete: {temp_dir}")
                
    except Exception as e:
        return {"error": f"Analysis setup failed: {str(e)}"}

# REPLACE your existing @app.post("/ai-chat") endpoint with this enhanced version

@app.post("/ai-chat")
async def unified_ai_chat(request: dict):
    """Enhanced AI chat endpoint - RAG-powered Explainer and Fixer Initiator"""
    try:
        question = request.get('question', '')
        context_type = request.get('context', 'auto')
        model_type = request.get('model_type', 'fast')
        previous_history = request.get('history', [])
        
        # Validate model type
        if model_type not in ['fast', 'smart']:
            model_type = 'fast'
        
        # Check if this is a fix request
        is_fix_request = any(phrase in question.lower() for phrase in [
            'fix this', 'fix the', 'propose fix', 'create fix', 'generate fix',
            'fix it', 'resolve this', 'solve this', 'patch this', 'auto fix'
        ])
        
        # Check if this is an explanation request
        is_explanation_request = any(phrase in question.lower() for phrase in [
            'what is', 'explain', 'what does', 'how does', 'tell me about',
            'describe', 'meaning of', 'definition'
        ])
        
        # Build enhanced context with automatic scan result detection
        enhanced_context = f"MODEL TYPE: {model_type}\nUSER QUESTION: {question}\n\n"
        
        # Auto-detect and use available scan results
        if context_type == 'auto':
            if hasattr(RepoAnalysis, 'latest_analysis') and RepoAnalysis.latest_analysis:
                context_type = 'repo_analysis'
                enhanced_context += "🔍 **AUTOMATICALLY DETECTED: Repository Analysis Available**\n\n"
            elif hasattr(WebsiteScan, 'latest_scan') and WebsiteScan.latest_scan:
                context_type = 'website_scan'
                enhanced_context += "🌐 **AUTOMATICALLY DETECTED: Website Scan Available**\n\n"
            else:
                context_type = 'general'
                enhanced_context += "🤖 **GENERAL SECURITY CONSULTATION** - No recent scan data available.\n\n"
        
        # Handle RAG-powered explanation requests
        if is_explanation_request:
            print("🔍 Processing explanation request with RAG...")
            
            # Query RAG for detailed explanation
            rag_context = await run_in_threadpool(get_secure_coding_patterns, question)
            
            enhanced_context += f"""
🧠 **RAG-ENHANCED EXPLANATION:**
{rag_context}

Please provide a comprehensive explanation using the above security knowledge.
"""

        # Handle fix requests for repository analysis
        if is_fix_request and context_type == 'repo_analysis':
            analysis_data = RepoAnalysis.latest_analysis
            
            if not analysis_data:
                return {
                    "response": "❌ No repository analysis available. Please run `/analyze-repo` first to scan for issues to fix.",
                    "model_used": model_type,
                    "context_detected": context_type,
                    "scan_data_available": False,
                    "history": previous_history,
                    "action_taken": None
                }
            
            # Try to identify which issue the user wants to fix
            repo_url = analysis_data.get('repository_info', {}).get('url', '')
            
            # Collect all fixable issues
            fixable_issues = []
            
            # Add secret scan results
            for secret in analysis_data.get('secret_scan_results', []):
                fixable_issues.append({
                    'file': secret.get('file', ''),
                    'line': secret.get('line', ''),
                    'type': 'Secret Detection',
                    'description': f"Hardcoded {secret.get('secret_type', 'secret')} found",
                    'vulnerable_code': secret.get('match', ''),
                    'severity': 'Critical'
                })
            
            # Add static analysis results
            for issue in analysis_data.get('static_analysis_results', []):
                if isinstance(issue, dict):
                    fixable_issues.append({
                        'file': issue.get('filename', ''),
                        'line': issue.get('line_number', ''),
                        'type': 'Static Analysis',
                        'description': issue.get('issue_text', str(issue)),
                        'vulnerable_code': '',
                        'severity': issue.get('issue_severity', 'Medium')
                    })
            
            # Add code quality issues
            for issue in analysis_data.get('code_quality_results', []):
                fixable_issues.append({
                    'file': issue.get('file', ''),
                    'line': issue.get('line', ''),
                    'type': 'Code Quality',
                    'description': issue.get('description', issue.get('pattern', '')),
                    'vulnerable_code': issue.get('code_snippet', ''),
                    'severity': issue.get('severity', 'Medium')
                })
            
            if not fixable_issues:
                return {
                    "response": "✅ Great news! No fixable security issues were found in the latest repository scan. Your code appears to be secure based on our analysis.",
                    "model_used": model_type,
                    "context_detected": context_type,
                    "scan_data_available": True,
                    "history": previous_history,
                    "action_taken": None
                }
            
            # If user specified a particular issue type or file, try to match it
            target_issue = None
            question_lower = question.lower()
            
            # Look for specific mentions
            for issue in fixable_issues:
                if (issue['file'].lower() in question_lower or 
                    issue['type'].lower() in question_lower or
                    any(word in issue['description'].lower() for word in question_lower.split())):
                    target_issue = issue
                    break
            
            # If no specific issue identified, pick the most critical one
            if not target_issue:
                # Sort by severity: Critical > High > Medium > Low
                severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
                fixable_issues.sort(key=lambda x: severity_order.get(x['severity'], 4))
                target_issue = fixable_issues[0]
            
            # Call the propose-fix endpoint
            try:
                fix_request = FixRequest(
                    repo_url=repo_url,
                    issue=target_issue
                )
                
                fix_response = await propose_fix(fix_request)
                
                if fix_response['success']:
                    pr_url = fix_response['pull_request']['url']
                    pr_number = fix_response['pull_request']['number']
                    changes_made = fix_response['fix_details']['changes_made']
                    
                    response = f"""🔧 **RAG-Powered Fix Generated Successfully!**

✅ I've created an automated security fix using advanced AI and secure coding patterns:

**Issue Fixed:**
• **File:** `{target_issue['file']}`
• **Type:** {target_issue['type']}
• **Description:** {target_issue['description']}

**AI-Generated Changes:**
{chr(10).join([f'• {change}' for change in changes_made])}

**🚀 Pull Request Created:**
**[#{pr_number} - Review Automated Fix]({pr_url})**

**✨ RAG-Enhanced Features:**
• 🧠 Applied secure coding patterns from OWASP guidelines
• 🛡️ Context-aware vulnerability remediation
• 📚 Knowledge base of 1000+ security best practices

**Next Steps:**
1. 📋 Review the automated changes in the pull request
2. 🧪 Test the fix to ensure functionality is preserved
3. ✅ Merge the PR once you're satisfied with the changes

This fix was generated using RAG (Retrieval-Augmented Generation) technology, combining AI reasoning with a curated database of security expertise.

Need me to explain any part of the fix or have questions about the security issue?"""
                    
                    return {
                        "response": response,
                        "model_used": model_type,
                        "context_detected": context_type,
                        "scan_data_available": True,
                        "history": previous_history + [
                            {'type': 'user', 'parts': [question]},
                            {'type': 'assistant', 'parts': [response]}
                        ],
                        "action_taken": {
                            "type": "fix_generated",
                            "pull_request_url": pr_url,
                            "issue_fixed": target_issue,
                            "rag_enhanced": True
                        }
                    }
                else:
                    return {
                        "response": f"❌ Failed to generate fix: {fix_response.get('error', 'Unknown error')}",
                        "model_used": model_type,
                        "context_detected": context_type,
                        "scan_data_available": True,
                        "history": previous_history,
                        "action_taken": None
                    }
                    
            except Exception as e:
                return {
                    "response": f"❌ Error generating fix: {str(e)}\n\nWould you like me to explain the security issue instead?",
                    "model_used": model_type,
                    "context_detected": context_type,
                    "scan_data_available": True,
                    "history": previous_history,
                    "action_taken": None
                }
        
        # Repository Analysis Context (Enhanced with RAG capabilities)
        if context_type == 'repo_analysis' and hasattr(RepoAnalysis, 'latest_analysis') and RepoAnalysis.latest_analysis:
            analysis_data = RepoAnalysis.latest_analysis
            
            if isinstance(analysis_data, dict):
                enhanced_context += f"""
📁 **REPOSITORY SECURITY ANALYSIS:**
• Repository: {analysis_data.get('repository_info', {}).get('name', 'Unknown')}
• Security Score: {analysis_data.get('overall_security_score', 'N/A')}/100 ({analysis_data.get('security_level', 'Unknown')})
• Language: {analysis_data.get('repository_info', {}).get('language', 'Unknown')}

📊 **SECURITY SUMMARY:**
• Files Scanned: {analysis_data.get('security_summary', {}).get('total_files_scanned', 0)}
• Secrets Found: {analysis_data.get('security_summary', {}).get('secrets_found', 0)}
• Static Issues: {analysis_data.get('security_summary', {}).get('static_issues_found', 0)}
• Vulnerable Dependencies: {analysis_data.get('security_summary', {}).get('vulnerable_dependencies', 0)}
• Code Quality Issues: {analysis_data.get('security_summary', {}).get('code_quality_issues', 0)}

🚨 **CRITICAL FINDINGS:**
SECRET SCAN RESULTS: {len(analysis_data.get('secret_scan_results', []))} secrets found
{chr(10).join([f"• {s.get('file', 'unknown')}: {s.get('secret_type', 'unknown')} (Line {s.get('line', 'N/A')})" for s in analysis_data.get('secret_scan_results', [])[:5]])}

CODE QUALITY ISSUES: {len(analysis_data.get('code_quality_results', []))} patterns found
{chr(10).join([f"• {c.get('file', 'unknown')}: {c.get('pattern', 'unknown')} - {c.get('severity', 'Unknown')} ({c.get('description', 'No description')})" for c in analysis_data.get('code_quality_results', [])[:5]])}

DEPENDENCY VULNERABILITIES: {len(analysis_data.get('dependency_scan_results', {}).get('vulnerable_packages', []))} packages
{chr(10).join([f"• {d.get('package', 'unknown')}: {d.get('severity', 'Unknown')} - {d.get('advisory', 'Update recommended')}" for d in analysis_data.get('dependency_scan_results', {}).get('vulnerable_packages', [])[:5]])}

STATIC ANALYSIS: {len(analysis_data.get('static_analysis_results', []))} issues found
{chr(10).join([f"• {str(s)[:100]}" for s in analysis_data.get('static_analysis_results', [])[:3]])}

🤖 **RAG-POWERED CAPABILITIES:**
- Ask me to "fix this issue" and I'll automatically create a pull request with the solution
- I can explain any security finding using curated OWASP knowledge
- I provide context-aware remediation guidance

📋 **RECOMMENDATIONS:**
{chr(10).join([f"• {rec}" for rec in analysis_data.get('recommendations', [])[:5]])}

🔍 **SENSITIVE FILES:**
{chr(10).join([f"• {f.get('file', 'unknown')} - {f.get('risk', 'Unknown')} risk" for f in analysis_data.get('file_security_scan', {}).get('sensitive_files', [])[:5]])}
"""
            else:
                enhanced_context += f"""
📁 **REPOSITORY ANALYSIS RESULTS:**
{str(analysis_data)[:2000]}...
"""
        
        # Website Scan Context (Enhanced with RAG capabilities)
        elif context_type == 'website_scan':
            scan_result = request.get('scan_result', None)
            
            # Use provided scan_result or stored scan data
            if scan_result:
                scan_data = scan_result
                website_data = None
            elif hasattr(WebsiteScan, 'latest_scan') and WebsiteScan.latest_scan:
                scan_data = WebsiteScan.latest_scan.get('scan_result', {})
                website_data = WebsiteScan.latest_scan
            else:
                scan_data = None
                website_data = None
            
            if scan_data:
                enhanced_context += f"""
🌐 **WEBSITE SECURITY SCAN:**
• Target: {scan_data.get('url', 'N/A')}
• Security Score: {scan_data.get('security_score', 'N/A')}/100 ({scan_data.get('security_level', 'Unknown')})
• HTTPS: {'✅ Enabled' if scan_data.get('https', False) else '❌ Disabled'}
• Vulnerabilities: {len(scan_data.get('flags', []))} issues found
• Security Headers: {len(scan_data.get('headers', {}))} detected

🛡️ **WAF ANALYSIS:**
• WAF Detected: {'✅ Yes' if website_data.get('waf_analysis', {}).get('waf_detected') else '❌ No'}
• WAF Type: {website_data.get('waf_analysis', {}).get('waf_type', 'None detected')}
• Protection Level: {website_data.get('waf_analysis', {}).get('protection_level', 'Unknown')}

🔐 **DNS SECURITY:**
• DNSSEC: {'✅ Enabled' if website_data.get('dns_security', {}).get('dnssec', {}).get('enabled') else '❌ Disabled'}
• DMARC: {'✅ Enabled' if website_data.get('dns_security', {}).get('dmarc', {}).get('enabled') else '❌ Not configured'}
• DKIM: {'✅ Found' if website_data.get('dns_security', {}).get('dkim', {}).get('selectors_found') else '❌ Not found'}

🚨 **SECURITY ISSUES:**
{chr(10).join([f'• {flag}' for flag in scan_data.get('flags', [])]) if scan_data.get('flags') else '• No critical issues detected'}

🔒 **SECURITY HEADERS:**
{chr(10).join([f'• {header}: {value}' for header, value in scan_data.get('headers', {}).items()]) if scan_data.get('headers') else '• No security headers detected'}

🚪 **EXPOSED PATHS:**
{chr(10).join([f'• {p["path"]} (Status: {p["status_code"]})' for p in website_data.get('exposed_paths', [])[:5]]) if website_data else '• No exposed paths found'}

📄 **PAGES CRAWLED:**
{chr(10).join([f'• {page}' for page in website_data.get('pages', [])[:5]]) if website_data else '• No pages data'}

🧠 **RAG-ENHANCED CAPABILITIES:**
- I can explain any security finding using curated OWASP knowledge
- Ask about specific vulnerabilities for detailed explanations
- Get implementation guidance for security fixes

💡 **AI SUGGESTIONS:**
{website_data.get('ai_assistant_advice', 'No AI suggestions available') if website_data else 'No AI suggestions available'}
"""
            else:
                enhanced_context += "🌐 **WEBSITE SCAN:** No scan result available.\n"
        
        # General Context
        elif context_type == 'general':
            enhanced_context += """
🔒 **GENERAL SECURITY CONSULTATION**
No specific scan data available. I can help with:
• General security best practices  
• Common vulnerability explanations (RAG-enhanced)
• Security implementation guidance
• Code review suggestions
• Security tool recommendations

🧠 **RAG-ENHANCED:** I have access to comprehensive security knowledge including OWASP guidelines, secure coding patterns, and vulnerability remediation techniques.

To get specific analysis, please run:
• `/analyze-repo` for repository security analysis (with automated fix generation)
• `/scan` for website security scanning
"""
        
        # Add RAG capability notice to responses
        enhanced_context += "\n\n🧠 **RAG-ENHANCED AI:** I now have access to a comprehensive security knowledge base for detailed explanations and automated fixes!"
        
        # Build conversation history and get response
        if previous_history:
            history = previous_history.copy()
            history.append({'type': 'user', 'parts': [enhanced_context + f"\n\nBased on the above security analysis and knowledge base, provide a helpful response to: {question}"]})
        else:
            history = [{'type': 'user', 'parts': [enhanced_context + f"\n\nBased on the above security analysis and knowledge base, provide a helpful response to: {question}"]}]
        
        response = await run_in_threadpool(get_chat_response, history, model_type)
        
        # Add response to history
        history.append({'type': 'assistant', 'parts': [response]})
        
        return {
            "response": response,
            "model_used": model_type,
            "context_detected": context_type,
            "scan_data_available": context_type in ['repo_analysis', 'website_scan'],
            "history": history,
            "action_taken": None,
            "rag_enhanced": True
        }
        
    except Exception as e:
        return {
            "response": f"❌ Error: {str(e)}",
            "model_used": model_type if 'model_type' in locals() else 'unknown',
            "context_detected": 'error',
            "scan_data_available": False,
            "history": [],
            "action_taken": None
        }
@app.post("/owasp-mapping")
async def owasp_mapping():
    """
    Map detected security issues to OWASP Top 10 categories
    Uses the latest scan and repo analysis results automatically
    """
    try:
        # Get the latest scan results from stored data
        scan_results = None
        if hasattr(WebsiteScan, 'latest_scan') and WebsiteScan.latest_scan:
            scan_results = WebsiteScan.latest_scan
        
        # Get the latest repository results from stored data
        repo_results = None
        if hasattr(RepoAnalysis, 'latest_analysis') and RepoAnalysis.latest_analysis:
            repo_results = RepoAnalysis.latest_analysis
        
        # Check if we have any data to analyze
        if not scan_results and not repo_results:
            return {
                "success": False,
                "error": "No scan results available. Please run /scan or /analyze-repo first.",
                "owasp_mapping": None,
                "metadata": {
                    "scan_available": False,
                    "repo_available": False,
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        # Map to OWASP Top 10
        owasp_mapping = map_to_owasp_top10(scan_results, repo_results)
        
        return {
            "success": True,
            "owasp_mapping": owasp_mapping,
            "metadata": {
                "scan_available": scan_results is not None,
                "repo_available": repo_results is not None,
                "scan_url": scan_results.get('url') if scan_results else None,
                "repo_name": repo_results.get('repository_info', {}).get('name') if repo_results else None,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OWASP mapping failed: {str(e)}")
    
@app.post("/propose-fix")
async def propose_fix(request: FixRequest):
    """
    RAG-powered automated code remediation endpoint
    Takes a specific security issue and creates a PR with the fix
    """
    try:
        repo_url = request.repo_url
        issue = request.issue
        
        # Extract repo info
        repo_url_clean = repo_url.rstrip('/').replace('.git', '')
        parts = repo_url_clean.split('/')
        
        if len(parts) < 5 or not github_client:
            raise HTTPException(status_code=400, detail="Invalid repo URL or GitHub client not available")
        
        owner, repo_name = parts[-2], parts[-1]
        
        # Get the repository
        try:
            github_repo = github_client.get_repo(f"{owner}/{repo_name}")
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Repository not found or not accessible: {str(e)}")
        
        # Create temporary directory for cloning
        temp_dir = tempfile.mkdtemp()
        
        try:
            print(f"🔧 Starting fix process for {repo_url}")
            
            # Clone the repository
            repo = git.Repo.clone_from(repo_url, temp_dir)
            
            # Get the file content
            issue_file = issue.get('file', '')
            if not issue_file:
                raise HTTPException(status_code=400, detail="Issue must specify a file path")
            
            file_path = os.path.join(temp_dir, issue_file)
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail=f"File {issue_file} not found in repository")
            
            # Read the vulnerable file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            # Query RAG database for secure coding patterns
            print("🔍 Querying RAG database for secure patterns...")
            rag_query = f"{issue.get('type', 'security')} {issue.get('description', '')}"
            secure_patterns = await run_in_threadpool(get_secure_coding_patterns, rag_query)
            
            # Construct the "Fixer" AI prompt
            fixer_prompt = f"""
You are a security code remediation expert. Your task is to fix a specific security vulnerability in code.

**VULNERABILITY DETAILS:**
- File: {issue.get('file', 'unknown')}
- Line: {issue.get('line', 'unknown')}
- Type: {issue.get('type', 'unknown')}
- Description: {issue.get('description', 'No description')}
- Vulnerable Code: {issue.get('vulnerable_code', 'Not specified')}

**CURRENT FILE CONTENT:**
```
{original_content}
```

**SECURE CODING PATTERNS (from RAG database):**
{secure_patterns}

**INSTRUCTIONS:**
1. Identify the exact vulnerability in the code
2. Apply the most appropriate secure coding pattern from the RAG database
3. Generate a complete, fixed version of the file
4. Ensure the fix doesn't break existing functionality
5. Add security comments where appropriate
6. Preserve all imports, functions, and logic that aren't security-related

**RESPONSE FORMAT:**
Return ONLY a JSON object with this exact structure:
{{
    "fixed_content": "complete fixed file content here",
    "changes_made": [
        "Replaced eval() with ast.literal_eval() for safe evaluation",
        "Added input validation before processing"
    ],
    "security_impact": "Prevents code injection attacks by removing unsafe eval() usage",
    "commit_message": "fix: resolve {issue.get('type', 'security')} vulnerability in {issue.get('file', 'file')}"
}}
"""

            # Call the AI to generate the fix
            print("🤖 Generating security fix with AI...")
            ai_response = await run_in_threadpool(get_chat_response, [
                {'type': 'user', 'parts': [fixer_prompt]}
            ], 'smart')  # Use smart model for fixing
            
            # Parse the AI response
            try:
                # Extract JSON from AI response
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    fix_data = json.loads(ai_response[json_start:json_end])
                else:
                    raise ValueError("No JSON found in AI response")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
            
            # Apply the fix to the file
            fixed_content = fix_data.get('fixed_content', '')
            if not fixed_content:
                raise HTTPException(status_code=500, detail="AI did not provide fixed content")
            
            # Write the fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print("✅ Fix applied to local file")
            
            # Create a new branch
            branch_name = request.branch_name or f"fix/{issue.get('type', 'security').lower().replace(' ', '-')}-{issue.get('file', 'file').replace('/', '-').replace('.', '-')}"
            
            # Check if branch already exists
            try:
                github_repo.get_branch(branch_name)
                # Branch exists, add timestamp to make it unique
                import time
                branch_name = f"{branch_name}-{int(time.time())}"
            except:
                pass  # Branch doesn't exist, which is what we want
            
            # Create branch and commit
            repo.git.checkout('-b', branch_name)
            repo.git.add(issue_file)
            
            commit_message = fix_data.get('commit_message', f"fix: resolve security vulnerability in {issue_file}")
            repo.git.commit('-m', commit_message)
            
            # Push the branch
            origin = repo.remote('origin')
            origin.push(branch_name)
            
            print(f"✅ Pushed fix to branch: {branch_name}")
            
            # Create pull request
            pr_title = f"🔒 Security Fix: {issue.get('description', 'Vulnerability remediation')}"
            pr_body = f"""
## 🛡️ Automated Security Fix

**Vulnerability Fixed:**
- **File:** `{issue.get('file', 'unknown')}`
- **Line:** {issue.get('line', 'unknown')}
- **Type:** {issue.get('type', 'Security Issue')}
- **Description:** {issue.get('description', 'No description')}

**Changes Made:**
{chr(10).join([f'- {change}' for change in fix_data.get('changes_made', [])])}

**Security Impact:**
{fix_data.get('security_impact', 'Improves application security')}

**Generated by:** AltX Security Scanner - Automated Remediation
**Powered by:** RAG-enhanced AI code analysis

---

⚠️ **Please review this automated fix carefully before merging.**

🔍 **Testing Recommended:**
- Run existing tests to ensure functionality is preserved
- Perform security testing to verify the vulnerability is resolved
- Review the code changes for any potential side effects
"""

            pull_request = github_repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base='main'  # Adjust if your default branch is different
            )
            
            print(f"✅ Pull request created: {pull_request.html_url}")
            
            return {
                "success": True,
                "pull_request": {
                    "url": pull_request.html_url,
                    "number": pull_request.number,
                    "title": pr_title,
                    "branch": branch_name
                },
                "fix_details": {
                    "file_fixed": issue_file,
                    "vulnerability_type": issue.get('type'),
                    "changes_made": fix_data.get('changes_made', []),
                    "security_impact": fix_data.get('security_impact'),
                    "commit_message": commit_message
                },
                "metadata": {
                    "repo_url": repo_url,
                    "timestamp": datetime.now().isoformat(),
                    "ai_model_used": "smart",
                    "rag_patterns_used": True
                }
            }
            
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
                    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fix generation failed: {str(e)}")
    
@app.get("/debug-scan")
async def debug_scan():
    """Debug endpoint to check stored scan data"""
    if hasattr(WebsiteScan, 'latest_scan') and WebsiteScan.latest_scan:
        scan_data = WebsiteScan.latest_scan
        return {
            "has_scan_data": True,
            "keys": list(scan_data.keys()),
            "waf_analysis_keys": list(scan_data.get('waf_analysis', {}).keys()) if scan_data.get('waf_analysis') else None,
            "dns_security_keys": list(scan_data.get('dns_security', {}).keys()) if scan_data.get('dns_security') else None,
            "waf_detected": scan_data.get('waf_analysis', {}).get('waf_detected'),
            "dns_has_data": bool(scan_data.get('dns_security')),
            "url": scan_data.get('url')
        }
    else:
        return {
            "has_scan_data": False,
            "message": "No scan data stored"
        }

@app.get("/health")
async def health_check():
    """Check if the API is running"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)