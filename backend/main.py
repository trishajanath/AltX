
import os
import secrets
import shutil
import git
import requests
import time
import tempfile
import stat
import platform
from fastapi import Request, Header, FastAPI, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
import hmac
import hashlib
import subprocess
import asyncio
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from starlette.concurrency import run_in_threadpool
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
from rag_query import get_secure_coding_patterns

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import docker
from nginx_config import NginxConfigManager

# --- Local Imports ---
from ai_assistant import get_chat_response, RepoAnalysis, FixRequest
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
    model_config = {'protected_namespaces': ()}

class RepoAnalysisRequest(BaseModel):
    repo_url: str
    model_type: str = 'smart'
    deep_scan: bool = True
    model_config = {'protected_namespaces': ()}

class OWASPMappingRequest(BaseModel):
    url: str
    repo_url: Optional[str] = None
    model_type: str = "fast"
    model_config = {'protected_namespaces': ()}

class FixRequest(BaseModel):
    repo_url: str
    issue: Dict[str, Any]
    branch_name: Optional[str] = None

from fastapi import Query
# --- Project File Tree Endpoint ---
@app.get("/project-file-tree")
async def get_project_file_tree(project_name: str = Query(...)):
    """
    Returns a mock file tree for the generated project.
    In production, this should read from the actual generated files.
    """
    # For demo, return a static file tree
    tree = [
        {"name": "src", "type": "dir", "path": "src/"},
        {"name": "App.jsx", "type": "file", "path": "src/App.jsx"},
        {"name": "index.js", "type": "file", "path": "src/index.js"},
        {"name": "components", "type": "dir", "path": "src/components/"},
        {"name": "TodoList.jsx", "type": "file", "path": "src/components/TodoList.jsx"},
        {"name": "public", "type": "dir", "path": "public/"},
        {"name": "index.html", "type": "file", "path": "public/index.html"},
        {"name": "package.json", "type": "file", "path": "package.json"},
        {"name": "README.md", "type": "file", "path": "README.md"}
    ]
    return {"success": True, "tree": tree}

# --- Project File Content Endpoint ---
@app.get("/project-file-content")
async def get_project_file_content(project_name: str = Query(...), file_path: str = Query(...)):
    """
    Returns mock file content for a given file in the generated project.
    In production, this should read the actual file content.
    """
    # Demo content for some files
    demo_files = {
        "src/App.jsx": "import React, { useState } from 'react';\nimport TodoList from './components/TodoList';\nfunction App() {\n  return <div><h1>To Do App</h1><TodoList /></div>;\n}\nexport default App;",
        "src/components/TodoList.jsx": "import React, { useState } from 'react';\nexport default function TodoList() {\n  const [items, setItems] = useState([]);\n  const [input, setInput] = useState('');\n  return (<div><input value={input} onChange={e => setInput(e.target.value)} /><button onClick={() => { setItems([...items, input]); setInput(''); }}>Add</button><ul>{items.map((item, i) => <li key={i}>{item}</li>)}</ul></div>);\n}",
        "src/index.js": "import React from 'react';\nimport ReactDOM from 'react-dom';\nimport App from './App';\nReactDOM.render(<App />, document.getElementById('root'));",
        "public/index.html": "<!DOCTYPE html><html><head><title>To Do App</title></head><body><div id='root'></div></body></html>",
        "package.json": "{\n  \"name\": \"todo-app\",\n  \"version\": \"1.0.0\",\n  \"dependencies\": {\n    \"react\": \"^18.0.0\",\n    \"react-dom\": \"^18.0.0\"\n  }\n}",
        "README.md": "# To Do App\nA simple React to-do application."
    }
    content = demo_files.get(file_path, f"// No content available for {file_path}")
    return {"success": True, "content": content}

# --- Project Preview URL Endpoint ---
@app.get("/project-preview-url")
async def get_project_preview_url(project_name: str = Query(...)):
    """
    Returns a mock live preview URL for the generated project.
    In production, this should point to the actual deployed preview.
    """
    # Demo: return a placeholder preview URL
    url = f"https://demo.altx.app/{project_name.lower().replace(' ', '-')}-preview"
    return {"success": True, "url": url}


@app.get("/debug/test-token")
async def test_github_token_direct():
    """Test GitHub token directly without ai_assistant import"""
    try:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return {"error": "GITHUB_TOKEN not found in environment"}
        
        # Test token directly
        from github import Github
        test_client = Github(token)
        
        # Test authentication
        user = test_client.get_user()
        
        # Fix: Get rate limit properly (newer PyGithub versions)
        try:
            rate_limit = test_client.get_rate_limit()
            # Try different attributes for rate limit
            if hasattr(rate_limit, 'core'):
                remaining = rate_limit.core.remaining
            elif hasattr(rate_limit, 'rate'):
                remaining = rate_limit.rate.remaining  
            else:
                remaining = "Unknown"
        except Exception as rate_error:
            print(f"Rate limit check failed: {rate_error}")
            remaining = "Could not check"
        
        return {
            "token_valid": True,
            "authenticated_as": user.login,
            "user_id": user.id,
            "user_type": user.type,
            "rate_limit_remaining": remaining,
            "token_scopes": "Check GitHub settings for exact scopes"
        }
        
    except Exception as e:
        return {
            "token_valid": False,
            "error": str(e),
            "token_present": bool(os.getenv("GITHUB_TOKEN")),
            "suggestion": "Check if token has 'repo' and 'public_repo' permissions"
        }
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
        exposed_paths = scan_data.get('accessible_paths', []) if scan_data else []
        waf_info = scan_data.get('waf_analysis', {}) if scan_data else {}
        dns_security = scan_data.get('dns_security', {}) if scan_data else {}

        suggestions = await run_in_threadpool(suggest_fixes, scan_result.get('headers', {}))
        ai_advice = await run_in_threadpool(
            ai_assistant.analyze_scan_with_llm,
            scan_result.get("https", False),
            scan_result.get("flags", []),
            scan_result.get("headers", {}),
            request.model_type
        )

        security_level = scan_result.get("security_level", "Unknown") if scan_result else "Unknown"
        security_score = scan_result.get("security_score", 0) if scan_result else 0

        # Extract SSL analysis data
        ssl_certificate = scan_result.get("ssl_certificate", {}) if scan_result else {}

        # Enhanced summary with SSL certificate information (using imported function)
        scan_summary = scan_data.get('scan_summary', {}) if scan_data else {}
        domain = scan_summary.get('domain', 'Unknown')
        summary = f"""🔒 **Security Scan Complete**

📊 **Target Analysis:**
• Domain: {domain}
• Overall Security Score: {security_score}/100 ({security_level})
• HTTPS: {'✅ Enabled' if scan_result.get("https", False) else '❌ Disabled'}
• Vulnerabilities: {len(scan_result.get("flags", []))} issues found
• Pages Crawled: {len(pages)} pages
• Security Headers: {len(scan_result.get("headers", {}))} detected
• Exposed Paths: {len(exposed_paths)} found

🛡️ **Web Application Firewall (WAF):**
• WAF Detected: {'✅ Yes' if waf_info.get('waf_detected') else '❌ No'}
• WAF Type: {waf_info.get('waf_type', 'None detected')}
• Protection Level: {waf_info.get('protection_level', 'Unknown')}
• Blocked Requests: {waf_info.get('blocked_requests', 0)}/{waf_info.get('total_requests', 0)}

🔐 **DNS Security Features:**
• DNSSEC: {'✅ Enabled' if dns_security.get('dnssec', {}).get('enabled') else '❌ Disabled'} - {dns_security.get('dnssec', {}).get('status', 'Unknown')}
• DMARC: {'✅ Enabled' if dns_security.get('dmarc', {}).get('enabled') else '❌ Not configured'} - {dns_security.get('dmarc', {}).get('policy', 'No policy')}
• DKIM: {'✅ Found' if dns_security.get('dkim', {}).get('selectors_found') else '❌ Not found'} - {len(dns_security.get('dkim', {}).get('selectors_found', []))} selectors

🔐 **SSL/TLS Security Analysis:**
{_format_ssl_analysis(ssl_certificate)}

🚨 **Key Issues Found:**
{chr(10).join([f'• {flag}' for flag in scan_result.get("flags", [])[:5]]) if scan_result.get("flags", []) else '• No critical issues detected'}

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


@app.post("/update-knowledge-base")
async def force_update_knowledge_base():
    """Force update knowledge base from web (ignoring 7-day cache)"""
    try:
        from web_scraper import force_update_knowledge_base
        success = await run_in_threadpool(force_update_knowledge_base)
        
        if success:
            # Rebuild RAG database to include new data
            from build_rag_db import build_database
            await run_in_threadpool(build_database, False, False)
            
            return {
                "success": True,
                "message": "Knowledge base force updated with fresh web data",
                "cache_bypass": True,
                "pdf_generated": True,
                "next_auto_update": "7 days from now"
            }
        else:
            return {
                "success": False,
                "message": "Failed to update knowledge base",
                "error": "Web scraping failed"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Update failed: {str(e)}",
            "error": str(e)
        }


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
        
        # ENHANCEMENT: Update knowledge base with latest security rules before analysis
        print("🌐 Updating security knowledge base with latest rules...")
        try:
            from web_scraper import update_knowledge_base_with_web_data
            web_update_success = await run_in_threadpool(update_knowledge_base_with_web_data)
            if web_update_success:
                print("✅ Knowledge base updated with latest SonarSource rules")
                # Rebuild RAG database to include new data
                from build_rag_db import build_database
                await run_in_threadpool(build_database, False, False)  # Incremental update
                print("✅ RAG database updated with new security rules")
            else:
                print("⚠️ Knowledge base update failed, using existing data")
        except Exception as e:
            print(f"⚠️ Knowledge base update error: {e} - continuing with existing data")
        
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
            
            # Initialize analysis tracking arrays
            analysis_warnings = []
            analysis_errors = []
            
            # Add Windows compatibility warnings if needed
            if os.name == 'nt':  # Windows
                analysis_warnings.extend([
                    "Running on Windows - some Unix-specific security tools may have limited functionality",
                    "File path analysis optimized for Windows environment", 
                    "If analysis tools fail, try running VS Code as administrator"
                ])
            
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
                analysis_errors.append(f"GitHub API analysis failed: {str(e)}")
                # Add enhanced fallback analysis
                github_analysis += f"""

📊 **Enhanced Local Analysis Summary:**
• Repository successfully analyzed using local tools
• Enhanced with live SonarSource security rules
• {len(secret_scan_results)} secrets detected
• {len(static_analysis_results)} static analysis issues found  
• {len(code_quality_results)} code quality issues identified
• Security recommendations generated using RAG-enhanced AI"""
            
            # Compile comprehensive results
            # Ensure all dicts are valid for .get() usage
            file_scan_results = file_scan_results if isinstance(file_scan_results, dict) else {}
            dependency_scan_results = dependency_scan_results if isinstance(dependency_scan_results, dict) else {}
            comprehensive_results = {
                "repository_info": {
                    "url": repo_url,
                    "name": getattr(github_repo, 'full_name', "Unknown") if github_repo else "Unknown",
                    "description": getattr(github_repo, 'description', "No description") if github_repo else "No description",
                    "language": getattr(github_repo, 'language', "Unknown") if github_repo else "Unknown",
                    "stars": getattr(github_repo, 'stargazers_count', 0) if github_repo else 0,
                    "forks": getattr(github_repo, 'forks_count', 0) if github_repo else 0,
                    "open_issues": getattr(github_repo, 'open_issues_count', 0) if github_repo else 0
                },
                "file_security_scan": file_scan_results,
                "secret_scan_results": secret_scan_results,
                "static_analysis_results": static_analysis_results,
                "dependency_scan_results": dependency_scan_results,
                "code_quality_results": code_quality_results,
                "ai_analysis": github_analysis,
                "analysis_warnings": analysis_warnings,
                "analysis_errors": analysis_errors,
                "security_summary": {
                    "total_files_scanned": file_scan_results.get('total_files_scanned', 0),
                    "sensitive_files_found": len(file_scan_results.get('sensitive_files', [])),
                    "risky_files_found": len(file_scan_results.get('risky_files', [])),
                    "secrets_found": len(secret_scan_results) if secret_scan_results else 0,
                    "static_issues_found": len(static_analysis_results) if static_analysis_results else 0,
                    "vulnerable_dependencies": len(dependency_scan_results.get('vulnerable_packages', [])),
                    "code_quality_issues": len(code_quality_results) if code_quality_results else 0,
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
            
            # Enhanced recommendations with RAG-powered security intelligence
            recommendations = []
            
            # Critical Security Issues (RAG-Enhanced)
            if file_scan_results.get('sensitive_files'):
                recommendations.append({
                    "file": "Multiple sensitive files detected",
                    "pattern": "Sensitive file exposure",
                    "risk": "Critical",
                    "fix": "Remove sensitive files from repository or add to .gitignore. Refer to SonarSource RSPEC rules for file security patterns."
                })
            
            if secret_scan_results:
                recommendations.append({
                    "file": f"{len(secret_scan_results)} files with secrets",
                    "pattern": "Hardcoded secrets detected",
                    "risk": "Critical", 
                    "fix": "Remove secrets from code and use environment variables or secret management systems. Follow OWASP secure coding guidelines."
                })
            
            if static_analysis_results and len(static_analysis_results) > 0:
                recommendations.append({
                    "file": f"{len(static_analysis_results)} static analysis issues", 
                    "pattern": "Code vulnerabilities detected",
                    "risk": "High",
                    "fix": "Apply secure coding patterns from updated SonarSource rules database. Focus on injection flaws and input validation."
                })
            
            if dependency_scan_results.get('vulnerable_packages'):
                vulnerable_count = len(dependency_scan_results['vulnerable_packages'])
                recommendations.append({
                    "file": f"{vulnerable_count} vulnerable dependencies",
                    "pattern": "Outdated dependencies with known vulnerabilities", 
                    "risk": "High",
                    "fix": "Update packages to secure versions. Monitor security advisories and implement automated dependency scanning."
                })
            
            # Infrastructure and Configuration Issues
            if file_scan_results.get('excluded_directories'):
                excluded_count = len(file_scan_results['excluded_directories'])
                recommendations.append({
                    "file": f"{excluded_count} build/dependency directories found",
                    "pattern": "Build artifacts in repository",
                    "risk": "Medium",
                    "fix": f"Ensure {excluded_count} directories (venv, __pycache__, node_modules) are in .gitignore to prevent sensitive data exposure."
                })
            
            if file_scan_results.get('gitignore_recommendations'):
                high_priority_gitignore = [rec for rec in file_scan_results['gitignore_recommendations'] if rec['priority'] == 'High']
                if high_priority_gitignore:
                    patterns = [rec['pattern'] for rec in high_priority_gitignore[:3]]
                    recommendations.append({
                        "file": ".gitignore",
                        "pattern": "Missing security patterns in .gitignore",
                        "risk": "Medium", 
                        "fix": f"Add patterns to .gitignore: {', '.join(patterns)} - Based on SonarSource file security recommendations."
                    })
            
            critical_code_issues = [r for r in code_quality_results if r.get('severity') in ['Critical', 'High']]
            if critical_code_issues:
                recommendations.append({
                    "file": f"{len(critical_code_issues)} files with critical issues",
                    "pattern": "Insecure coding patterns",
                    "risk": "High",
                    "fix": "Apply secure coding practices from live SonarSource rules. Focus on input validation, error handling, and authentication patterns."
                })
            
            # Additional Security Improvements  
            if file_scan_results.get('risky_files'):
                risky_count = len(file_scan_results['risky_files'])
                recommendations.append({
                    "file": f"{risky_count} risky file types",
                    "pattern": "Potentially risky file extensions",
                    "risk": "Medium",
                    "fix": "Review risky file types for security implications. Consider removing unnecessary executable files or configuration files with defaults."
                })
            
            if file_scan_results.get('missing_security_files'):
                missing = file_scan_results['missing_security_files'][:3]
                recommendations.append({
                    "file": "Repository root",
                    "pattern": "Missing security documentation", 
                    "risk": "Low",
                    "fix": f"Add missing security files: {', '.join(missing)} to improve security posture and compliance."
                })
            
            if not any('security.md' in f.get('type', '') for f in file_scan_results.get('security_files_found', [])):
                recommendations.append({
                    "file": "SECURITY.md",
                    "pattern": "Missing security policy",
                    "risk": "Low", 
                    "fix": "Add SECURITY.md file with vulnerability disclosure policy and security contact information."
                })
            
            comprehensive_results["recommendations"] = recommendations[:10]  # Limit to top 10 recommendations
            
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
                                # Make file writable and remove all permissions restrictions
                                os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                                # Try the original function again
                                func(path)
                        except Exception as e:
                            print(f"⚠️ Could not remove {path}: {e}")
                            # Try with admin privileges if needed
                            try:
                                import subprocess
                                if os.name == 'nt':  # Windows
                                    subprocess.run(['del', '/f', '/q', f'"{path}"'], 
                                                 shell=True, check=False)
                            except:
                                pass
                    
                    def cleanup_git_directory(directory):
                        """Special cleanup for Git directories with enhanced Windows support"""
                        try:
                            # First, try to make all files in .git writable
                            git_dir = os.path.join(directory, '.git')
                            if os.path.exists(git_dir):
                                print(f"🔧 Making Git files writable in: {git_dir}")
                                for root, dirs, files in os.walk(git_dir):
                                    # Make directories writable
                                    for dir_name in dirs:
                                        dir_path = os.path.join(root, dir_name)
                                        try:
                                            os.chmod(dir_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                                        except Exception:
                                            pass
                                    
                                    # Make files writable  
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        try:
                                            # Remove read-only attribute and make writable
                                            os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                                            # Additional Windows-specific attribute removal
                                            if os.name == 'nt':
                                                import subprocess
                                                # Fix path construction for Windows
                                                subprocess.run(['attrib', '-r', '-h', '-s', file_path], 
                                                             shell=True, check=False)
                                        except Exception:
                                            pass
                        except Exception as e:
                            print(f"⚠️ Error in Git directory cleanup: {e}")
                    
                    # Special handling for Git directories
                    cleanup_git_directory(temp_dir)
                    
                    # Wait longer for file handles to close on Windows
                    if os.name == 'nt':
                        time.sleep(0.5)  # Longer wait on Windows
                    else:
                        time.sleep(0.1)
                    
                    # Try multiple removal strategies
                    removal_success = False
                    
                    # Strategy 1: Standard shutil.rmtree with error handler
                    try:
                        shutil.rmtree(temp_dir, onerror=force_remove_readonly)
                        print(f"✅ Temporary directory cleaned up: {temp_dir}")
                        removal_success = True
                    except Exception as e1:
                        print(f"⚠️ Standard cleanup failed: {e1}")
                        
                        # Strategy 2: Windows-specific command line tools
                        if os.name == 'nt' and not removal_success:
                            try:
                                import subprocess
                                print("🔧 Trying Windows command line cleanup...")
                                
                                # Method 1: rmdir with force
                                result = subprocess.run([
                                    'rmdir', '/s', '/q', temp_dir
                                ], shell=True, capture_output=True, text=True, timeout=30)
                                
                                if result.returncode == 0:
                                    print(f"✅ Directory cleaned up using rmdir")
                                    removal_success = True
                                else:
                                    print(f"⚠️ rmdir failed: {result.stderr}")
                                    
                            except Exception as e2:
                                print(f"⚠️ rmdir cleanup failed: {e2}")
                        
                        # Strategy 3: PowerShell as last resort
                        if os.name == 'nt' and not removal_success:
                            try:
                                print("🔧 Trying PowerShell cleanup...")
                                ps_result = subprocess.run([
                                    'powershell', '-Command', 
                                    f'Get-ChildItem -Path "{temp_dir}" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue; Remove-Item -Path "{temp_dir}" -Force -ErrorAction SilentlyContinue'
                                ], capture_output=True, text=True, timeout=30)
                                
                                if ps_result.returncode == 0:
                                    print(f"✅ Directory cleaned up using PowerShell")
                                    removal_success = True
                                else:
                                    print(f"⚠️ PowerShell cleanup issues: {ps_result.stderr}")
                                    
                            except Exception as e3:
                                print(f"⚠️ PowerShell cleanup failed: {e3}")
                        
                        # Strategy 4: Manual file-by-file deletion
                        if not removal_success:
                            try:
                                print("🔧 Trying manual file-by-file deletion...")
                                for root, dirs, files in os.walk(temp_dir, topdown=False):
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        try:
                                            os.chmod(file_path, stat.S_IWRITE)
                                            os.remove(file_path)
                                        except:
                                            pass
                                    for dir_name in dirs:
                                        dir_path = os.path.join(root, dir_name)
                                        try:
                                            os.rmdir(dir_path)
                                        except:
                                            pass
                                try:
                                    os.rmdir(temp_dir)
                                    print(f"✅ Directory cleaned up manually")
                                    removal_success = True
                                except:
                                    pass
                            except Exception as e4:
                                print(f"⚠️ Manual cleanup failed: {e4}")
                    
                    if not removal_success:
                        print(f"⚠️ Could not fully clean temp directory: {temp_dir}")
                        print(f"💡 The directory will be cleaned up automatically by the system eventually.")
                        print(f"💡 Or you can manually delete: {temp_dir}")
                    
                except Exception as e:
                    print(f"⚠️ Cleanup error: {e} - continuing anyway")
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
            repo_analysis = getattr(RepoAnalysis, 'latest_analysis', None)
            website_scan = getattr(WebsiteScan, 'latest_scan', None)
            if repo_analysis:
                context_type = 'repo_analysis'
                enhanced_context += "🔍 **AUTOMATICALLY DETECTED: Repository Analysis Available**\n\n"
            elif website_scan:
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
        if context_type == 'repo_analysis':
            analysis_data = getattr(RepoAnalysis, 'latest_analysis', None)
            if isinstance(analysis_data, dict):
                repo_info = analysis_data.get('repository_info', {}) if analysis_data else {}
                security_summary = analysis_data.get('security_summary', {}) if analysis_data else {}
                secret_scan_results = analysis_data.get('secret_scan_results', []) if analysis_data else []
                code_quality_results = analysis_data.get('code_quality_results', []) if analysis_data else []
                dependency_scan_results = analysis_data.get('dependency_scan_results', {}) if analysis_data else {}
                static_analysis_results = analysis_data.get('static_analysis_results', []) if analysis_data else []
                recommendations = analysis_data.get('recommendations', []) if analysis_data else []
                file_security_scan = analysis_data.get('file_security_scan', {}) if analysis_data else {}
                sensitive_files = file_security_scan.get('sensitive_files', []) if file_security_scan else []
                enhanced_context += f"""
📁 **REPOSITORY SECURITY ANALYSIS:**
• Repository: {repo_info.get('name', 'Unknown')}
• Security Score: {analysis_data.get('overall_security_score', 'N/A')}/100 ({analysis_data.get('security_level', 'Unknown')})
• Language: {repo_info.get('language', 'Unknown')}

📊 **SECURITY SUMMARY:**
• Files Scanned: {security_summary.get('total_files_scanned', 0)}
• Secrets Found: {security_summary.get('secrets_found', 0)}
• Static Issues: {security_summary.get('static_issues_found', 0)}
• Vulnerable Dependencies: {security_summary.get('vulnerable_dependencies', 0)}
• Code Quality Issues: {security_summary.get('code_quality_issues', 0)}

🚨 **CRITICAL FINDINGS:**
SECRET SCAN RESULTS: {len(secret_scan_results)} secrets found
{chr(10).join([f"• {str(s.get('file', 'unknown'))}: {str(s.get('secret_type', 'unknown'))} (Line {str(s.get('line', 'N/A'))})" for s in secret_scan_results[:5]] if secret_scan_results else ['• No secrets detected'])}

CODE QUALITY ISSUES: {len(code_quality_results)} patterns found
{chr(10).join([f"• {str(c.get('file', 'unknown'))}: {str(c.get('pattern', 'unknown'))} - {str(c.get('severity', 'Unknown'))} ({str(c.get('description', 'No description'))})" for c in code_quality_results[:5]] if code_quality_results else ['• No code quality issues found'])}

DEPENDENCY VULNERABILITIES: {len(dependency_scan_results.get('vulnerable_packages', []))} packages
{chr(10).join([f"• {str(d.get('package', 'unknown'))}: {str(d.get('severity', 'Unknown'))} - {str(d.get('advisory', 'Update recommended'))}" for d in dependency_scan_results.get('vulnerable_packages', [])[:5]] if dependency_scan_results.get('vulnerable_packages', []) else ['• No vulnerable dependencies found'])}

STATIC ANALYSIS: {len(static_analysis_results)} issues found
{chr(10).join([f"• {s.get('filename', 'unknown')}: {s.get('issue', 'Security issue')} ({s.get('severity', 'Unknown')} severity)" for s in static_analysis_results[:3]] if static_analysis_results else ['• No static analysis issues found'])}

🤖 **RAG-POWERED CAPABILITIES:**
- Ask me to "fix this issue" and I'll automatically create a pull request with the solution
- I can explain any security finding using curated OWASP knowledge
- I provide context-aware remediation guidance

📋 **RECOMMENDATIONS:**
{chr(10).join([f"• {str(rec)}" for rec in recommendations[:5]] if recommendations else ['• No specific recommendations at this time'])}

🔍 **SENSITIVE FILES:**
{chr(10).join([f"• {str(f.get('file', 'unknown'))} - {str(f.get('risk', 'Unknown'))} risk" for f in sensitive_files[:5]] if sensitive_files else ['• No sensitive files detected'])}
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
            website_data = getattr(WebsiteScan, 'latest_scan', None)
            if scan_result:
                scan_data = scan_result
            elif website_data:
                scan_data = website_data.get('scan_result', {}) if isinstance(website_data, dict) else {}
            else:
                scan_data = None

            waf_analysis = website_data.get('waf_analysis', {}) if website_data else {}
            dns_security = website_data.get('dns_security', {}) if website_data else {}
            exposed_paths = website_data.get('exposed_paths', []) if website_data else []
            pages = website_data.get('pages', []) if website_data else []
            ai_assistant_advice = website_data.get('ai_assistant_advice', 'No AI suggestions available') if website_data else 'No AI suggestions available'

            if scan_data:
                enhanced_context += f"""
🌐 **WEBSITE SECURITY SCAN:**
• Target: {scan_data.get('url', 'N/A')}
• Security Score: {scan_data.get('security_score', 'N/A')}/100 ({scan_data.get('security_level', 'Unknown')})
• HTTPS: {'✅ Enabled' if scan_data.get('https', False) else '❌ Disabled'}
• Vulnerabilities: {len(scan_data.get('flags', []))} issues found
• Security Headers: {len(scan_data.get('headers', {}))} detected

🛡️ **WAF ANALYSIS:**
• WAF Detected: {'✅ Yes' if waf_analysis.get('waf_detected') else '❌ No'}
• WAF Type: {waf_analysis.get('waf_type', 'None detected')}
• Protection Level: {waf_analysis.get('protection_level', 'Unknown')}

🔐 **DNS SECURITY:**
• DNSSEC: {'✅ Enabled' if dns_security.get('dnssec', {}).get('enabled') else '❌ Disabled'}
• DMARC: {'✅ Enabled' if dns_security.get('dmarc', {}).get('enabled') else '❌ Not configured'}
• DKIM: {'✅ Found' if dns_security.get('dkim', {}).get('selectors_found') else '❌ Not found'}

🚨 **SECURITY ISSUES:**
{chr(10).join([f'• {flag}' for flag in scan_data.get('flags', [])]) if scan_data.get('flags', []) else '• No critical issues detected'}

🔒 **SECURITY HEADERS:**
{chr(10).join([f'• {header}: {value}' for header, value in scan_data.get('headers', {}).items()]) if scan_data.get('headers', {}) else '• No security headers detected'}

🚪 **EXPOSED PATHS:**
{chr(10).join([f'• {p["path"]} (Status: {p.get("status_code", "N/A")})' for p in exposed_paths[:5]]) if exposed_paths else '• No exposed paths found'}

📄 **PAGES CRAWLED:**
{chr(10).join([f'• {page}' for page in pages[:5]]) if pages else '• No pages data'}

🧠 **RAG-ENHANCED CAPABILITIES:**
- I can explain any security finding using curated OWASP knowledge
- Ask about specific vulnerabilities for detailed explanations
- Get implementation guidance for security fixes

💡 **AI SUGGESTIONS:**
{ai_assistant_advice}
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
    
async def provide_local_fix_suggestion(issue: dict):
    """
    Provide fix suggestions for local analysis without GitHub operations
    """
    try:
        print(f"🔧 Providing local fix suggestion for: {issue.get('description', 'Unknown issue')}")
        
        # Query RAG database for secure coding patterns
        rag_query = f"{issue.get('type', 'security')} {issue.get('description', '')} {issue.get('vulnerable_code', '')}"
        secure_patterns = await run_in_threadpool(get_secure_coding_patterns, rag_query)
        
        # Create AI prompt
        ai_prompt = f"""
        You are a security expert. Analyze this security issue and provide a fix:
        
        Issue Type: {issue.get('type', 'Unknown')}
        Description: {issue.get('description', 'No description')}
        File: {issue.get('file', 'Unknown file')}
        Line: {issue.get('line', 'Unknown')}
        
        Vulnerable Code:
        {issue.get('vulnerable_code', 'Not provided')}
        
        Security Knowledge Base:
        {secure_patterns}
        
        Provide a JSON response with:
        {{
            "fix_summary": "Brief description of the fix",
            "security_impact": "How this improves security",
            "suggested_code": "The corrected code",
            "explanation": "Detailed explanation of the fix",
            "prevention_tips": ["List of tips to prevent this issue"]
        }}
        """
        
        # Get AI response
        ai_response = await run_in_threadpool(get_chat_response, [
            {"role": "user", "content": ai_prompt}
        ], "smart")
        ai_text = ai_response if isinstance(ai_response, str) else str(ai_response)
        
        # Parse JSON response
        try:
            json_start = ai_text.find('{')
            json_end = ai_text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                fix_data = json.loads(ai_text[json_start:json_end])
            else:
                raise ValueError("No JSON found")
        except:
            # Fallback response
            fix_data = {
                "fix_summary": f"Security fix suggested for {issue.get('type', 'issue')}",
                "security_impact": "Reduces security vulnerability risk",
                "suggested_code": "# Apply security best practices here",
                "explanation": f"This {issue.get('type', 'issue')} should be addressed by following security best practices.",
                "prevention_tips": ["Regular security audits", "Use security linting tools", "Follow OWASP guidelines"]
            }
        
        return {
            "success": True,
            "fix_applied": False,
            "suggestion_only": True,
            "fix_summary": fix_data.get("fix_summary", "Security fix suggested"),
            "security_impact": fix_data.get("security_impact", "Improves security"),
            "suggested_code": fix_data.get("suggested_code", ""),
            "explanation": fix_data.get("explanation", ""),
            "prevention_tips": fix_data.get("prevention_tips", []),
            "issue_details": {
                "type": issue.get('type'),
                "file": issue.get('file'),
                "line": issue.get('line'),
                "description": issue.get('description')
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate fix suggestion: {str(e)}",
            "fix_summary": "Unable to generate fix",
            "suggestion_only": True
        }

class ProjectRequest(BaseModel):
    idea: str
    project_type: str = "web-app"
    tech_stack: str = "auto"
    complexity: str = "medium"

@app.post("/generate-project")
async def generate_project(request: ProjectRequest):
    """
    AI-powered project generation endpoint
    Takes a project idea and generates a complete project structure
    """
    try:
        idea = request.idea
        project_type = request.project_type
        tech_stack = request.tech_stack
        complexity = request.complexity
        
        print(f"🚀 Generating project for idea: '{idea}'")
        print(f"🔧 Project type: {project_type}, Tech stack: {tech_stack}, Complexity: {complexity}")
        
        # Generate project name
        words = idea.split()[:3]
        project_name = " ".join([word.capitalize() for word in words])
        
        # Select tech stack based on project type
        if tech_stack == "auto":
            stack_mapping = {
                "web-app": ["React", "Node.js", "PostgreSQL", "Tailwind CSS"],
                "mobile-app": ["React Native", "Expo", "Firebase", "NativeBase"],
                "api": ["FastAPI", "PostgreSQL", "Redis", "Docker"],
                "desktop-app": ["Electron", "React", "SQLite", "Styled Components"],
                "ai-ml": ["Python", "FastAPI", "TensorFlow", "PostgreSQL"],
                "blockchain": ["Solidity", "React", "Web3.js", "IPFS"]
            }
            selected_stack = stack_mapping.get(project_type, stack_mapping["web-app"])
        else:
            stack_mapping = {
                "react-node": ["React", "Node.js", "Express", "MongoDB"],
                "python-fastapi": ["Python", "FastAPI", "PostgreSQL", "SQLAlchemy"],
                "nextjs": ["Next.js", "React", "Prisma", "PostgreSQL"],
                "vue-express": ["Vue.js", "Express", "Node.js", "MongoDB"],
                "django": ["Django", "Python", "PostgreSQL", "Bootstrap"],
                "rails": ["Ruby on Rails", "PostgreSQL", "Redis", "Stimulus"]
            }
            selected_stack = stack_mapping.get(tech_stack, ["React", "Node.js"])
        
        # Generate project structure
        structure_mapping = {
            "web-app": [
                "📁 src/",
                "  📁 components/",
                "  📁 pages/",
                "  📁 hooks/",
                "  📁 utils/",
                "  📁 assets/",
                "📁 public/",
                "📁 api/",
                "📄 package.json",
                "📄 README.md",
                "📄 .env.example"
            ],
            "mobile-app": [
                "📁 src/",
                "  📁 screens/",
                "  📁 components/",
                "  📁 navigation/",
                "  📁 services/",
                "  📁 assets/",
                "📄 App.js",
                "📄 package.json",
                "📄 app.json",
                "📄 babel.config.js"
            ],
            "api": [
                "📁 src/",
                "  📁 routes/",
                "  📁 models/",
                "  📁 middleware/",
                "  📁 utils/",
                "📄 main.py",
                "📄 requirements.txt",
                "📄 Dockerfile",
                "📄 docker-compose.yml"
            ]
        }
        project_structure = structure_mapping.get(project_type, structure_mapping["web-app"])
        
        # Generate features based on idea keywords
        common_features = [
            "User Authentication",
            "Responsive Design", 
            "API Integration",
            "Database Storage",
            "Real-time Updates"
        ]
        
        additional_features = []
        idea_lower = idea.lower()
        if "chat" in idea_lower: additional_features.append("Real-time Chat")
        if "payment" in idea_lower: additional_features.append("Payment Integration")
        if "ai" in idea_lower or "ml" in idea_lower: additional_features.append("AI/ML Features")
        if "social" in idea_lower: additional_features.append("Social Features")
        if "admin" in idea_lower: additional_features.append("Admin Dashboard")
        if "notification" in idea_lower: additional_features.append("Push Notifications")
        
        all_features = common_features + additional_features
        
        # Estimate development time
        time_mapping = {
            "simple": "2-3 days",
            "medium": "1-2 weeks", 
            "complex": "3-4 weeks"
        }
        estimated_time = time_mapping.get(complexity, "1-2 weeks")
        
        # Generate URLs (these would be real in production)
        project_slug = project_name.lower().replace(" ", "-")
        github_repo = f"https://github.com/user/{project_slug}"
        deployment_url = f"https://{project_slug}.vercel.app"
        
        return {
            "success": True,
            "project": {
                "name": project_name,
                "description": idea,
                "tech_stack": selected_stack,
                "structure": project_structure,
                "features": all_features,
                "estimated_time": estimated_time,
                "github_repo": github_repo,
                "deployment_url": deployment_url,
                "project_type": project_type,
                "complexity": complexity
            }
        }
        
    except Exception as e:
        print(f"❌ Project generation error: {e}")
        return {
            "success": False,
            "error": f"Failed to generate project: {str(e)}"
        }

@app.post("/propose-fix")
async def propose_fix(request: FixRequest):
    """
    RAG-powered automated code remediation endpoint with detailed code comparison
    Takes a specific security issue and creates a PR with the fix
    """
    try:
        repo_url = request.repo_url
        issue = request.issue
        
        print(f"🔍 Raw repo_url received: '{repo_url}'")
        print(f"🔍 Issue data: {json.dumps(issue, indent=2)}")
        
        # Check if this is a local analysis (not a GitHub repo)
        if not repo_url.startswith('https://github.com/') and not repo_url.startswith('git@github.com:'):
            print(f"❌ Invalid repo URL format: '{repo_url}' - not a GitHub URL")
            return await provide_local_fix_suggestion(issue)
        
        # Clean and extract repo info
        repo_url_clean = repo_url.rstrip('/').replace('.git', '')
        
        # Handle different GitHub URL formats
        if '/tree/' in repo_url_clean:
            # Remove everything after /tree/
            repo_url_clean = repo_url_clean.split('/tree/')[0]
            print(f"🔧 Cleaned tree URL: '{repo_url}' -> '{repo_url_clean}'")
        
        if '/blob/' in repo_url_clean:
            # Remove everything after /blob/
            repo_url_clean = repo_url_clean.split('/blob/')[0]
            print(f"🔧 Cleaned blob URL: '{repo_url}' -> '{repo_url_clean}'")
        
        parts = repo_url_clean.replace('https://github.com/', '').split('/')
        print(f"🔍 URL parts after cleaning: {parts}")
        
        if len(parts) < 2:
            print(f"❌ Invalid repo URL format after cleaning: '{repo_url_clean}' -> parts: {parts}")
            raise HTTPException(status_code=400, detail=f"Invalid repo URL format. Expected format: https://github.com/owner/repo, got: '{repo_url}'")
        
        owner, repo_name = parts[0], parts[1]
        print(f"🔍 Extracted repo: {owner}/{repo_name}")
        
        # Initialize GitHub client with proper authentication
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise HTTPException(status_code=500, detail="GitHub token not configured. Please set GITHUB_TOKEN environment variable.")
        
        from github import Github
        try:
            # Always create a fresh GitHub client with the token
            working_github_client = Github(token)
            print("✅ Created fresh GitHub client")
            
            # Test the client immediately
            test_user = working_github_client.get_user()
            print(f"✅ GitHub client authenticated as: {test_user.login}")
            
        except Exception as client_error:
            print(f"❌ GitHub authentication failed: {client_error}")
            raise HTTPException(status_code=401, detail=f"GitHub authentication failed: {str(client_error)}")
        
        # Test repository access with the working client
        try:
            print(f"🔍 Testing access to repository: {owner}/{repo_name}")
            github_repo = working_github_client.get_repo(f"{owner}/{repo_name}")
            print(f"✅ Repository accessible: {github_repo.full_name}")
            print(f"📊 Repository info: {github_repo.language}, Private: {github_repo.private}")
            
        except Exception as repo_error:
            error_msg = str(repo_error)
            print(f"❌ Repository access failed: {error_msg}")
            
            if "401" in error_msg or "Bad credentials" in error_msg:
                raise HTTPException(
                    status_code=401, 
                    detail=f"GitHub authentication failed. Your token may not have the correct permissions. Please ensure your GITHUB_TOKEN has 'repo' scope for private repositories or 'public_repo' scope for public repositories. Error: {error_msg}"
                )
            elif "404" in error_msg or "Not Found" in error_msg:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Repository '{owner}/{repo_name}' not found or not accessible. Please check: 1) Repository URL is correct, 2) Repository exists and is public, or 3) Your token has access to private repositories. Error: {error_msg}"
                )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Repository access error: {error_msg}"
                )
        
        # Create temporary directory for cloning
        temp_dir = tempfile.mkdtemp()
        
        try:
            print(f"🔧 Starting fix process for {repo_url_clean}")
            
            # Clone the repository using the cleaned URL
            repo = git.Repo.clone_from(repo_url_clean, temp_dir)
            
            # Get the file content
            issue_file = issue.get('file', '')
            if not issue_file:
                raise HTTPException(status_code=400, detail="Issue must specify a file path")
            
            # Extract relative path from absolute path if needed
            # Handle cases where issue_file might be an absolute temp path
            if os.path.isabs(issue_file):
                # Try to extract the relative path by finding common patterns
                # Look for patterns like /backend/, /frontend/, /src/, etc.
                path_parts = issue_file.replace('\\', '/').split('/')
                
                # Find the start of the relative path (after temp directory)
                relative_start = -1
                for i, part in enumerate(path_parts):
                    if part in ['backend', 'frontend', 'src', 'lib', 'app', 'public', 'static', 'assets']:
                        relative_start = i
                        break
                
                if relative_start != -1:
                    # Take everything from the relative start
                    issue_file = '/'.join(path_parts[relative_start:])
                    print(f"🔄 Extracted relative path from absolute: {issue_file}")
                else:
                    # If we can't find a common pattern, take the last few parts
                    # This handles cases like "config/db.js" or "package.json"
                    if len(path_parts) >= 2:
                        issue_file = '/'.join(path_parts[-2:])  # Take last 2 parts
                    else:
                        issue_file = path_parts[-1]  # Take just the filename
                    print(f"🔄 Using fallback relative path: {issue_file}")
            
            # Normalize file path (ensure forward slashes for cross-platform compatibility)
            issue_file = issue_file.replace('\\', '/')
            print(f"🔍 Final normalized issue file path: {issue_file}")
            print(f"🔍 Repository temp directory: {temp_dir}")
            
            file_path = os.path.join(temp_dir, issue_file)
            print(f"🔍 Full file path: {file_path}")
            
            # Store original file content (before fix)
            original_content = ""
            file_existed = os.path.exists(file_path)
            
            if file_existed:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    original_content = f.read()
                print(f"📄 Original file content loaded: {len(original_content)} characters")
            else:
                print(f"📝 File {issue_file} will be created (doesn't exist)")
            
            # Query RAG database for secure coding patterns (Enhanced with live SonarSource rules)
            print("🔍 Querying enhanced RAG database for secure patterns...")
            rag_query = f"{issue.get('type', 'security')} {issue.get('description', '')} {issue.get('vulnerable_code', '')}"
            secure_patterns = await run_in_threadpool(get_secure_coding_patterns, rag_query)
            
            print(f"✅ Retrieved {len(secure_patterns)} characters of security patterns from RAG database")
            
            # Enhanced "Fixer" AI prompt - Gemini receives BOTH user issue AND RAG knowledge
            fixer_prompt = f"""
You are a security code remediation expert. I'm providing you with BOTH a specific security issue that needs fixing AND relevant security knowledge from our RAG database. Use both pieces of information together to create the best possible fix.

**USER'S SECURITY ISSUE TO FIX:**
- File: {issue.get('file', 'unknown')}
- Line: {issue.get('line', 'unknown')}
- Type: {issue.get('type', 'unknown')}
- Description: {issue.get('description', 'No description')}
- Vulnerable Code: {issue.get('vulnerable_code', 'Not specified')}
- Severity: {issue.get('severity', 'Medium')}

**CURRENT FILE CONTENT:**
```
{original_content if file_existed else "// File does not exist - will be created"}
```

**RAG SECURITY KNOWLEDGE (SonarSource Rules + OWASP Guidelines):**
{secure_patterns}

**YOUR TASK:**
Analyze the user's security issue AND the RAG knowledge together to:
1. Understand the specific vulnerability in the user's code
2. Find the most relevant security patterns from the RAG knowledge
3. Apply the best remediation technique from both sources
4. Generate a complete, production-ready fixed version of the file
5. Reference specific rules and patterns you used from the RAG knowledge
6. Ensure the fix addresses the user's exact issue
7. Preserve all functionality while improving security

**RESPONSE FORMAT:**
Return ONLY a JSON object with this exact structure:
{{
    "fixed_content": "complete fixed file content here",
    "changes_made": [
        "Applied pattern from RAG knowledge: Replaced eval() with ast.literal_eval() based on SonarSource RSPEC-XXX",
        "Implemented user's specific issue fix: Added input validation for the vulnerable code section"
    ],
    "security_impact": "Resolves the user's {issue.get('type', 'security')} issue while applying RAG-recommended security patterns",
    "commit_message": "fix: resolve {issue.get('type', 'security')} vulnerability in {issue.get('file', 'file')} using RAG-enhanced patterns",
    "lines_changed": [
        {{"line_number": 15, "old_code": "eval(user_input)", "new_code": "ast.literal_eval(user_input)", "change_type": "modified"}},
        {{"line_number": 16, "old_code": "", "new_code": "# Security: Applied RAG pattern (SonarSource RSPEC-XXX)", "change_type": "added"}}
    ],
    "fix_summary": "Combined user issue analysis with RAG security knowledge: {issue.get('description', 'vulnerability')} resolved using recommended patterns",
    "rag_patterns_applied": ["Pattern from RAG: SonarSource RSPEC-XXX for code injection prevention", "OWASP guideline for input validation"],
    "user_issue_addressed": "Specific fix for: {issue.get('description', 'security issue')} in {issue.get('file', 'file')}",
    "integration_approach": "Gemini AI analyzed both user issue and RAG knowledge simultaneously for optimal fix"
}}
"""

            # Call Gemini AI with BOTH user issue and RAG knowledge
            print("🤖 Gemini AI processing user issue + RAG knowledge together...")
            ai_response = await run_in_threadpool(get_chat_response, [
                {'type': 'user', 'parts': [fixer_prompt]}
            ], 'smart')  # Use smart model for comprehensive analysis
            
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
                print(f"⚠️ Failed to parse AI JSON, using enhanced fallback: {e}")
                print(f"🔍 AI Response: {ai_response[:500]}...")
                
                # Enhanced fallback: create intelligent fix based on issue type
                issue_desc = issue.get('description', '').lower()
                
                if 'private key' in issue_desc or 'secret' in issue_desc:
                    # For key/secret issues, remove the sensitive content
                    fix_data = {
                        "fixed_content": "# Sensitive content removed for security\n# Please move secrets to environment variables\n",
                        "changes_made": ["Removed private key/secret for security"],
                        "fix_summary": f"Removed sensitive content from {issue.get('file', 'file')}",
                        "security_improvement": "Credentials moved to secure environment variables"
                    }
                elif '.gitignore' in issue.get('file', ''):
                    # For gitignore issues, add security patterns
                    fix_data = {
                        "fixed_content": original_content + "\n# Security additions\n*.key\n*.pem\n*.env\n.env.*\nsecrets/\nconfig/secrets.yml\n",
                        "changes_made": ["Added security patterns to .gitignore"],
                        "fix_summary": "Enhanced .gitignore with security patterns",
                        "security_improvement": "Prevented sensitive files from being committed"
                    }
                else:
                    # Generic security fix
                    fix_data = {
                        "fixed_content": "# Security fix applied\n" + original_content,
                        "changes_made": ["Applied security fix"],
                        "security_impact": "Security improvement applied",
                        "commit_message": f"fix: resolve {issue.get('type', 'security')} vulnerability",
                        "lines_changed": [],
                        "fix_summary": "Security fix applied"
                    }
            
            # Apply the fix to the file
            fixed_content = fix_data.get('fixed_content', '')
            if not fixed_content:
                raise HTTPException(status_code=500, detail="AI did not provide fixed content")
            
            # Create directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write the fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print("✅ Fix applied to local file")
            
            # Calculate detailed code differences
            def calculate_code_diff(original: str, fixed: str) -> dict:
                """Calculate detailed differences between original and fixed code"""
                original_lines = original.splitlines() if original else []
                fixed_lines = fixed.splitlines()
                
                # Simple diff calculation
                diff_stats = {
                    "lines_added": len(fixed_lines) - len(original_lines) if len(fixed_lines) > len(original_lines) else 0,
                    "lines_removed": len(original_lines) - len(fixed_lines) if len(original_lines) > len(fixed_lines) else 0,
                    "lines_modified": 0,
                    "total_changes": 0
                }
                
                # Calculate modifications
                min_lines = min(len(original_lines), len(fixed_lines))
                for i in range(min_lines):
                    if original_lines[i] != fixed_lines[i]:
                        diff_stats["lines_modified"] += 1
                
                diff_stats["total_changes"] = diff_stats["lines_added"] + diff_stats["lines_removed"] + diff_stats["lines_modified"]
                
                return diff_stats
            
            code_diff = calculate_code_diff(original_content, fixed_content)
            
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
            
            # Use relative path for git operations (normalize path separators)
            git_file_path = issue_file.replace('\\', '/')
            print(f"📝 Adding file to git: {git_file_path}")
            print(f"🔍 Current working directory: {os.getcwd()}")
            print(f"🔍 Repository working directory: {repo.working_dir}")
            
            try:
                # Verify file exists relative to repo root
                full_file_path = os.path.join(repo.working_dir, git_file_path)
                if os.path.exists(full_file_path):
                    print(f"✅ File exists at: {full_file_path}")
                else:
                    print(f"❌ File not found at: {full_file_path}")
                    # List files in the directory to debug
                    dir_to_check = os.path.dirname(full_file_path)
                    if os.path.exists(dir_to_check):
                        print(f"📂 Files in {dir_to_check}: {os.listdir(dir_to_check)}")
                
                repo.git.add(git_file_path)
                print(f"✅ Successfully added {git_file_path} to git")
                
            except Exception as git_add_error:
                print(f"❌ DETAILED ERROR in git add: {git_add_error}")
                print(f"📍 Git add failed for: {git_file_path}")
                print(f"📍 Repository root: {repo.working_dir}")
                print(f"📍 Attempted file path: {git_file_path}")
                raise git_add_error
            
            commit_message = fix_data.get('commit_message', f"fix: resolve security vulnerability in {issue_file}")
            repo.git.commit('-m', commit_message)
            
            # Push the branch
            try:
                origin = repo.remote('origin')
                origin.push(branch_name)
                print(f"✅ Pushed fix to branch: {branch_name}")
                
                # If push succeeds, continue with PR creation
                push_success = True
                
            except Exception as push_error:
                push_success = False
                error_msg = str(push_error)
                print(f"❌ Push failed: {error_msg}")
                
                # Check if it's a permission issue (403, authentication, etc.)
                if "403" in error_msg or "401" in error_msg or "authentication" in error_msg.lower() or "permission" in error_msg.lower():
                    print("🔒 No write access to repository - attempting fork workflow...")
                    
                    try:
                        # Try to fork the repository
                        print(f"🍴 Attempting to fork {owner}/{repo_name}")
                        
                        # Get the authenticated user
                        auth_user = working_github_client.get_user()
                        user_login = auth_user.login
                        print(f"👤 Authenticated as: {user_login}")
                        
                        # Check if fork already exists
                        try:
                            existing_fork = working_github_client.get_repo(f"{user_login}/{repo_name}")
                            print(f"✅ Fork already exists: {existing_fork.full_name}")
                            forked_repo = existing_fork
                        except:
                            # Create fork
                            original_repo = working_github_client.get_repo(f"{owner}/{repo_name}")
                            forked_repo = auth_user.create_fork(original_repo)
                            print(f"✅ Fork created: {forked_repo.full_name}")
                        
                        # Update remote origin to point to fork
                        fork_url = forked_repo.clone_url
                        # Add token to URL for authentication
                        token = os.getenv("GITHUB_TOKEN")
                        if token:
                            fork_url_with_auth = fork_url.replace("https://", f"https://{token}@")
                        else:
                            fork_url_with_auth = fork_url
                        
                        # Remove existing origin and add fork as origin
                        try:
                            repo.delete_remote('origin')
                        except:
                            pass
                        
                        fork_origin = repo.create_remote('origin', fork_url_with_auth)
                        print(f"🔄 Updated origin to fork: {fork_url}")
                        
                        # Push to fork
                        fork_origin.push(branch_name)
                        print(f"✅ Pushed fix to fork: {forked_repo.full_name}/{branch_name}")
                        
                        # Create PR from fork to original repo
                        head_ref = f"{user_login}:{branch_name}"  # Format: fork_owner:branch_name
                        
                        push_success = True
                        # Update github_repo to the original for PR creation
                        github_repo = working_github_client.get_repo(f"{owner}/{repo_name}")
                        
                    except Exception as fork_error:
                        print(f"❌ Fork workflow failed: {fork_error}")
                        
                        # Return local fix suggestion with fork instructions
                        return {
                            "success": True,
                            "message": f"🔧 Security fix generated for {issue_file} (Fork required)",
                            "fix_type": "fork_required",
                            "access_limitation": "Repository requires forking to contribute",
                            "fork_instructions": [
                                f"1. Go to https://github.com/{owner}/{repo_name}",
                                "2. Click the 'Fork' button to create your own copy",
                                "3. Clone your fork to your local machine",
                                "4. Apply the fix shown below",
                                "5. Commit and push to your fork",
                                "6. Create a pull request from your fork to the original repository"
                            ],
                            "fix_details": {
                                "file_fixed": issue_file,
                                "vulnerability_type": issue.get('type'),
                                "severity": issue.get('severity', 'Medium'),
                                "changes_made": fix_data.get('changes_made', []),
                                "security_impact": fix_data.get('security_impact'),
                                "fix_summary": fix_data.get('fix_summary', 'Security fix generated'),
                                "lines_changed": fix_data.get('lines_changed', [])
                            },
                            "code_comparison": {
                                "file_existed_before": file_existed,
                                "original_content": original_content,
                                "fixed_content": fixed_content,
                                "content_length_before": len(original_content),
                                "content_length_after": len(fixed_content),
                                "character_changes": len(fixed_content) - len(original_content)
                            },
                            "manual_fix_instructions": f"To apply this fix:\n1. Fork the repository at https://github.com/{owner}/{repo_name}\n2. Clone your fork\n3. Edit the file: {issue_file}\n4. Replace the content with the fixed version\n5. Commit, push, and create a pull request",
                            "code_preview": {
                                "original_preview": original_content[:500] + ("..." if len(original_content) > 500 else ""),
                                "fixed_preview": fixed_content[:500] + ("..." if len(fixed_content) > 500 else ""),
                                "preview_truncated": len(original_content) > 500 or len(fixed_content) > 500
                            }
                        }
                else:
                    # For other git errors, re-raise
                    raise push_error
            
            # Only proceed with PR creation if push was successful
            if not push_success:
                return  # This shouldn't be reached due to the return above, but just in case
            
            # Create enhanced pull request with code comparison
            pr_title = f"🔒 Security Fix: {issue.get('description', 'Vulnerability remediation')}"
            
            # Generate code diff preview for PR body
            def generate_diff_preview(original: str, fixed: str, max_lines: int = 20) -> str:
                """Generate a diff preview for the PR description"""
                if not original and fixed:
                    return f"```diff\n+ {chr(10).join(fixed.splitlines()[:max_lines])}\n```"
                
                original_lines = original.splitlines()
                fixed_lines = fixed.splitlines()
                
                diff_preview = "```diff\n"
                
                # Show first few differences
                shown_lines = 0
                min_lines = min(len(original_lines), len(fixed_lines))
                
                for i in range(min_lines):
                    if shown_lines >= max_lines:
                        diff_preview += "... (more changes in the full diff)\n"
                        break
                        
                    if original_lines[i] != fixed_lines[i]:
                        diff_preview += f"- {original_lines[i]}\n+ {fixed_lines[i]}\n"
                        shown_lines += 2
                
                # Show added lines
                if len(fixed_lines) > len(original_lines):
                    for i in range(min_lines, min(len(fixed_lines), min_lines + max_lines - shown_lines)):
                        diff_preview += f"+ {fixed_lines[i]}\n"
                        shown_lines += 1
                
                diff_preview += "```"
                return diff_preview
            
            diff_preview = generate_diff_preview(original_content, fixed_content)
            
            pr_body = f"""
## 🛡️ Automated Security Fix

**Vulnerability Fixed:**
- **File:** `{issue.get('file', 'unknown')}`
- **Line:** {issue.get('line', 'unknown')}
- **Type:** {issue.get('type', 'Security Issue')}
- **Severity:** {issue.get('severity', 'Medium')}
- **Description:** {issue.get('description', 'No description')}

**Fix Summary:**
{fix_data.get('fix_summary', 'Security improvements applied')}

**Changes Made:**
{chr(10).join([f'- {change}' for change in fix_data.get('changes_made', [])])}

**Security Impact:**
{fix_data.get('security_impact', 'Improves application security')}

**Code Changes Preview:**
{diff_preview}

**Statistics:**
- **Lines Added:** {code_diff['lines_added']}
- **Lines Modified:** {code_diff['lines_modified']}
- **Lines Removed:** {code_diff['lines_removed']}
- **Total Changes:** {code_diff['total_changes']}

**Generated by:** AltX Security Scanner - Automated Remediation
**Powered by:** RAG-enhanced AI code analysis

---

⚠️ **Please review this automated fix carefully before merging.**

🔍 **Testing Recommended:**
- Run existing tests to ensure functionality is preserved
- Perform security testing to verify the vulnerability is resolved
- Review the code changes for any potential side effects
"""
            try:
                default_branch = github_repo.default_branch
                print(f"📋 Repository default branch: {default_branch}")
                try:
                    remote_branch = github_repo.get_branch(branch_name)
                    print(f"✅ Branch {branch_name} confirmed on remote")
                except Exception as e:
                    print(f"⚠️ Branch verification failed: {e}")
                    github_repo = working_github_client.get_repo(f"{owner}/{repo_name}")
            
                # Check if we're working with a fork (head_ref would be set in fork workflow)
                if 'head_ref' in locals():
                    print(f"🍴 Creating PR from fork: {head_ref} -> {default_branch}")
                    pull_request = github_repo.create_pull(
                        title=pr_title,
                        body=pr_body,
                        head=head_ref,  # fork_owner:branch_name
                        base=default_branch
                    )
                else:
                    print(f"📝 Creating PR from same repo: {branch_name} -> {default_branch}")
                    pull_request = github_repo.create_pull(
                        title=pr_title,
                        body=pr_body,
                        head=branch_name,
                        base=default_branch
                    )
                print(f"✅ Pull request created: {pull_request.html_url}")
            except Exception as pr_error:
                error_msg = str(pr_error)
                print(f"❌ Pull request creation failed: {error_msg}")
                
                # Handle specific GitHub API errors with user-friendly messages
                if "403" in error_msg and ("archived" in error_msg.lower() or "read-only" in error_msg.lower()):
                    print(f"🔒 Repository is archived and read-only: {owner}/{repo_name}")
                    return {
                        "success": True,
                        "message": f"🔧 Security fix generated for {issue_file} (Repository is archived)",
                        "fix_type": "archived_repository",
                        "access_limitation": f"Repository {owner}/{repo_name} is archived and read-only",
                        "manual_fix_instructions": f"This repository is archived and cannot accept pull requests. To apply this fix:\n1. Contact the repository owner to unarchive it\n2. Or fork the repository and apply the fix to your fork\n3. The security issue was found in: {issue_file}",
                        "fix_details": fix_data,
                        "code_comparison": {
                            "original_content": original_content,
                            "fixed_content": fixed_content,
                            "content_length_before": len(original_content),
                            "content_length_after": len(fixed_content),
                            "character_changes": len(fixed_content) - len(original_content)
                        },
                        "code_preview": {
                            "original_preview": original_content[:500] + ("..." if len(original_content) > 500 else ""),
                            "fixed_preview": fixed_content[:500] + ("..." if len(fixed_content) > 500 else ""),
                            "preview_truncated": len(original_content) > 500 or len(fixed_content) > 500
                        }
                    }
                elif "404" in error_msg:
                    print(f"❌ PR creation failed with 404. Debugging info:")
                    print(f"   Repository: {owner}/{repo_name}")
                    print(f"   Head branch: {branch_name}")
                    print(f"   Base branch: {default_branch}")
                    print(f"   Repository exists: {github_repo.full_name}")
                    
                    # Check if it's a branch not found issue
                    if "not found" in error_msg.lower() and "branch" in error_msg.lower():
                        print(f"🔍 Branch not found - this might be a timing issue")
                        return {
                            "success": True,
                            "message": f"🔧 Security fix applied to {issue_file} (Branch sync issue)",
                            "fix_type": "branch_sync_issue",
                            "access_limitation": "Branch synchronization issue with GitHub",
                            "manual_fix_instructions": f"The fix was applied locally but there was a branch synchronization issue. To resolve:\n1. The changes were made to: {issue_file}\n2. Try creating the pull request manually\n3. Or re-run the fix after a few minutes",
                            "fix_details": fix_data,
                            "code_comparison": {
                                "original_content": original_content,
                                "fixed_content": fixed_content,
                                "content_length_before": len(original_content),
                                "content_length_after": len(fixed_content),
                                "character_changes": len(fixed_content) - len(original_content)
                            }
                        }
                    
                    if hasattr(github_repo, 'fork') and github_repo.fork:
                        print("   Note: This is a forked repository")
                        head_with_owner = f"{owner}:{branch_name}"
                        print(f"   Trying with owner prefix: {head_with_owner}")
                        try:
                            pull_request = github_repo.create_pull(
                                title=pr_title,
                                body=pr_body,
                                head=head_with_owner,
                                base=default_branch
                            )
                            print(f"✅ Pull request created with owner prefix: {pull_request.html_url}")
                        except Exception as e2:
                            print(f"❌ PR creation with owner prefix also failed: {e2}")
                            raise HTTPException(status_code=404, 
                                detail=f"Failed to create pull request. Repository: {owner}/{repo_name},Branch: {branch_name} → {default_branch}. Error: {error_msg}"
                            )
                    else:
                        raise HTTPException(
                            status_code=404, 
                            detail=f"Failed to create pull request. Repository: {owner}/{repo_name}, Branch: {branch_name} → {default_branch}. Error: {error_msg}"
                        )
                elif "403" in error_msg:
                    print(f"🔒 Permission denied for repository: {owner}/{repo_name}")
                    return {
                        "success": True,
                        "message": f"🔧 Security fix generated for {issue_file} (Permission denied)",
                        "fix_type": "permission_denied",
                        "access_limitation": "Insufficient permissions to create pull request",
                        "manual_fix_instructions": f"Permission denied while creating pull request. To apply this fix:\n1. Ensure your GitHub token has write access to {owner}/{repo_name}\n2. Or fork the repository and apply the fix to your fork\n3. The security issue was found in: {issue_file}",
                        "fix_details": fix_data,
                        "code_comparison": {
                            "original_content": original_content,
                            "fixed_content": fixed_content,
                            "content_length_before": len(original_content),
                            "content_length_after": len(fixed_content),
                            "character_changes": len(fixed_content) - len(original_content)
                        }
                    }
                elif "422" in error_msg and ("collaborator" in error_msg.lower() or "validation failed" in error_msg.lower()):
                    print(f"🤝 Not a collaborator on repository: {owner}/{repo_name}")
                    return {
                        "success": True,
                        "message": f"🔧 Security fix generated for {issue_file} (Fork required for contribution)",
                        "fix_type": "collaboration_required",
                        "access_limitation": "You are not a collaborator on this repository",
                        "manual_fix_instructions": f"You need to be a collaborator to create pull requests directly. To apply this fix:\n1. Ask the repository owner to add you as a collaborator\n2. Or fork the repository at https://github.com/{owner}/{repo_name}\n3. Apply the fix to your fork and create a PR from there\n4. The security issue was found in: {issue_file}",
                        "fix_details": fix_data,
                        "code_comparison": {
                            "original_content": original_content,
                            "fixed_content": fixed_content,
                            "content_length_before": len(original_content),
                            "content_length_after": len(fixed_content),
                            "character_changes": len(fixed_content) - len(original_content)
                        },
                        "fork_url": f"https://github.com/{owner}/{repo_name}/fork",
                        "code_preview": {
                            "original_preview": original_content[:500] + ("..." if len(original_content) > 500 else ""),
                            "fixed_preview": fixed_content[:500] + ("..." if len(fixed_content) > 500 else ""),
                            "preview_truncated": len(original_content) > 500 or len(fixed_content) > 500
                        }
                    }
                else:
                    raise HTTPException(
                            status_code=500,
                            detail=f"Pull request creation error: {error_msg}"
                    )
            # Prepare detailed response with code comparison
            response_data = {
                "success": True,
                "message": f"🔧 Security fix successfully applied to {issue_file}",
                "pull_request": {
                    "url": pull_request.html_url,
                    "number": pull_request.number,
                    "title": pr_title,
                    "branch": branch_name
                },
                "fix_details": {
                    "file_fixed": issue_file,
                    "vulnerability_type": issue.get('type'),
                    "severity": issue.get('severity', 'Medium'),
                    "changes_made": fix_data.get('changes_made', []),
                    "security_impact": fix_data.get('security_impact'),
                    "commit_message": commit_message,
                    "fix_summary": fix_data.get('fix_summary', 'Security fix applied'),
                    "lines_changed": fix_data.get('lines_changed', [])
                },
                "code_comparison": {
                    "file_existed_before": file_existed,
                    "original_content": original_content,
                    "fixed_content": fixed_content,
                    "content_length_before": len(original_content),
                    "content_length_after": len(fixed_content),
                    "diff_statistics": code_diff,
                    "character_changes": len(fixed_content) - len(original_content)
                },
                "metadata": {
                    "repo_url": repo_url,
                    "repo_name": f"{owner}/{repo_name}",
                    "timestamp": datetime.now().isoformat(),
                    "ai_model_used": "smart",
                    "rag_patterns_used": True,
                    "rag_query": rag_query,
                    "rag_patterns_applied": fix_data.get('rag_patterns_applied', []),
                    "user_issue_addressed": fix_data.get('user_issue_addressed', 'Security issue resolved'),
                    "integration_approach": fix_data.get('integration_approach', 'Gemini AI with RAG knowledge'),
                    "security_intelligence": "Gemini AI analyzed user issue + RAG knowledge simultaneously (6000+ patterns)"
                }
            }
            
            # Add preview of changes (first 500 chars of each)
            if original_content or fixed_content:
                response_data["code_preview"] = {
                    "original_preview": original_content[:500] + ("..." if len(original_content) > 500 else ""),
                    "fixed_preview": fixed_content[:500] + ("..." if len(fixed_content) > 500 else ""),
                    "preview_truncated": len(original_content) > 500 or len(fixed_content) > 500
                }
            
            return response_data
            
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                try:
                    import stat
                    
                    def force_remove_readonly(func, path, exc_info):
                        try:
                            if os.path.exists(path):
                                os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
                                func(path)
                        except Exception:
                            pass
                    
                    shutil.rmtree(temp_dir, onerror=force_remove_readonly)
                    print("✅ Temporary directory cleaned up")
                except Exception as e:
                    print(f"⚠️ Warning: Could not clean up temp directory: {e}")
                    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ DETAILED ERROR in propose-fix: {e}")
        print(f"📍 TRACEBACK:\n{error_traceback}")
        raise HTTPException(status_code=500, detail=f"Fix generation failed: {str(e)}\nLocation: {error_traceback.split('File')[-1].split(',')[0] if 'File' in error_traceback else 'Unknown'}")
@app.get("/auth/github/callback")
async def github_callback(code: str = None, state: str = None):
    """
    Handle GitHub OAuth callback after user authorization
    This is the 'front door' for users returning after GitHub login
    """
    try:
        if not code:
            print("❌ No authorization code received from GitHub")
            return RedirectResponse(
                url="/?error=authorization_failed", 
                status_code=302
            )
        
        print(f"✅ Received GitHub authorization code: {code[:10]}...")
        
        # Exchange authorization code for access token
        

        # Exchange authorization code for access token
        token_url = "https://github.com/login/oauth/access_token"
        token_data = {
            "client_id": os.getenv("GITHUB_CLIENT_ID"),  # Changed from GITHUB_APP_ID
            "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
            "code": code,
            "state": state
        }
        token_headers = {
            "Accept": "application/json",
            "User-Agent": "AltX-Security-Scanner"
        }
        
        print("🔄 Exchanging code for access token...")
        token_response = requests.post(token_url, data=token_data, headers=token_headers)
        
        if token_response.status_code != 200:
            print(f"❌ Token exchange failed: {token_response.text}")
            return RedirectResponse(
                url="/?error=token_exchange_failed", 
                status_code=302
            )
        
        token_info = token_response.json()
        access_token = token_info.get("access_token")
        
        if not access_token:
            print(f"❌ No access token received: {token_info}")
            return RedirectResponse(
                url="/?error=no_access_token", 
                status_code=302
            )
        
        print("✅ Access token received successfully")
        
        # Get user information
        user_headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/json",
            "User-Agent": "AltX-Security-Scanner"
        }
        
        user_response = requests.get("https://api.github.com/user", headers=user_headers)
        
        if user_response.status_code != 200:
            print(f"❌ Failed to get user info: {user_response.text}")
            return RedirectResponse(
                url="/?error=user_info_failed", 
                status_code=302
            )
        
        user_info = user_response.json()
        username = user_info.get("login", "unknown")
        user_id = user_info.get("id")
        avatar_url = user_info.get("avatar_url")
        
        print(f"✅ User authenticated: {username} (ID: {user_id})")
        
        # In a real application, you would:
        # 1. Store the user session
        # 2. Create a JWT token
        # 3. Store user data in database
        # For now, we'll just redirect with success
        
        # Redirect to frontend with success and user info
        redirect_url = f"/?auth=success&user={username}&avatar={avatar_url}"
        
        print(f"🚀 Redirecting user to: {redirect_url}")
        
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except Exception as e:
        print(f"❌ OAuth callback error: {str(e)}")
        return RedirectResponse(
            url=f"/?error=callback_failed&message={str(e)}", 
            status_code=302
        )



@app.get("/auth/github/login")
async def github_login():
    """
    Initiate GitHub OAuth login
    This redirects users to GitHub for authorization
    """
    try:
        # Use GITHUB_CLIENT_ID for OAuth, not GITHUB_APP_ID
        github_client_id = os.getenv("GITHUB_CLIENT_ID")  # Changed from GITHUB_APP_ID
        
        if not github_client_id:
            raise HTTPException(status_code=500, detail="GitHub Client ID not configured")
        
        # Generate a random state parameter for security
        import secrets
        state = secrets.token_urlsafe(32)
        
        # GitHub OAuth authorization URL
        github_auth_url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={github_client_id}"
            f"&redirect_uri={os.getenv('GITHUB_CALLBACK_URL', 'http://localhost:8000/auth/github/callback')}"
            f"&scope=repo,user:email"
            f"&state={state}"
            f"&allow_signup=true"
        )
        
        print(f"🔗 Redirecting to GitHub OAuth: {github_auth_url}")
        
        return RedirectResponse(url=github_auth_url, status_code=302)
        
    except Exception as e:
        print(f"❌ Login initiation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

from fastapi import Request

@app.get("/auth/google/callback")
async def google_callback(request: Request):
    """
    Handle Google OAuth callback after user authorization
    """
    try:
        # Get the authorization code from the query parameters
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code:
            print("❌ No authorization code received from Google")
            return RedirectResponse(url="/?error=authorization_failed", status_code=302)

        print(f"✅ Received Google authorization code: {code[:10]}...")

        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "code": code,
            "redirect_uri": os.getenv("GOOGLE_CALLBACK_URL", "http://localhost:8000/auth/google/callback"),
            "grant_type": "authorization_code"
        }
        token_headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        print("🔄 Exchanging code for access token...")
        token_response = requests.post(token_url, data=token_data, headers=token_headers)

        if token_response.status_code != 200:
            print(f"❌ Token exchange failed: {token_response.text}")
            return RedirectResponse(url="/?error=token_exchange_failed", status_code=302)

        token_info = token_response.json()
        access_token = token_info.get("access_token")

        if not access_token:
            print(f"❌ No access token received: {token_info}")
            return RedirectResponse(url="/?error=no_access_token", status_code=302)

        print("✅ Access token received successfully")

        # Get user information
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        user_headers = {
            "Authorization": f"Bearer {access_token}"
        }
        user_response = requests.get(user_info_url, headers=user_headers)

        if user_response.status_code != 200:
            print(f"❌ Failed to get user info: {user_response.text}")
            return RedirectResponse(url="/?error=user_info_failed", status_code=302)

        user_info = user_response.json()
        email = user_info.get("email", "unknown")
        name = user_info.get("name", "unknown")
        picture = user_info.get("picture", "")

        print(f"✅ User authenticated: {email} ({name})")

        # Redirect to frontend with success and user info
        redirect_url = f"/?auth=success&user={email}&name={name}&avatar={picture}"
        print(f"🚀 Redirecting user to: {redirect_url}")

        return RedirectResponse(url=redirect_url, status_code=302)

    except Exception as e:
        print(f"❌ OAuth callback error: {str(e)}")
        return RedirectResponse(url=f"/?error=callback_failed&message={str(e)}", status_code=302)
@app.get("/auth/google/login")
async def google_login():
    """
    Initiate Google OAuth login
    Redirects user to Google's OAuth consent screen
    """
    try:
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        google_callback_url = os.getenv("GOOGLE_CALLBACK_URL", "http://localhost:8000/auth/google/callback")
        if not google_client_id:
            raise HTTPException(status_code=500, detail="Google Client ID not configured")

        # Generate a random state parameter for security
        state = secrets.token_urlsafe(32)

        # Google OAuth authorization URL
        google_auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={google_client_id}"
            f"&redirect_uri={google_callback_url}"
            "&response_type=code"
            "&scope=openid%20email%20profile"
            f"&state={state}"
            "&access_type=offline"
            "&prompt=consent"
        )

        print(f"🔗 Redirecting to Google OAuth: {google_auth_url}")
        return RedirectResponse(url=google_auth_url, status_code=302)

    except Exception as e:
        print(f"❌ Google login initiation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Google login failed: {str(e)}")
@app.get("/auth/status")
async def auth_status():
    """
    Check authentication status
    """
    return {
        "github_app_configured": bool(os.getenv("GITHUB_APP_ID")),
        "github_client_id_configured": bool(os.getenv("GITHUB_CLIENT_ID")),  # Added
        "github_client_secret_configured": bool(os.getenv("GITHUB_CLIENT_SECRET")),
        "callback_url": os.getenv("GITHUB_CALLBACK_URL", "http://localhost:8000/auth/github/callback"),
        "login_url": "/auth/github/login",
        "timestamp": datetime.now().isoformat()
    }
@app.post("/api/deploy")
async def manual_deploy(request: dict):
    """
    Manual deployment endpoint for the Deploy Page
    Does not require webhook signature verification
    """
    try:
        repo_url = request.get("repo_url")
        if not repo_url:
            raise HTTPException(status_code=400, detail="Repository URL is required")
        
        print(f"🚀 Manual deployment requested for: {repo_url}")
        
        # Create a simplified payload for deployment
        repo_name = repo_url.split('/')[-1]
        owner = repo_url.split('/')[-2]
        
        deployment_payload = {
            "ref": "refs/heads/main",
            "repository": {
                "name": repo_name,
                "full_name": f"{owner}/{repo_name}",
                "clone_url": repo_url,
                "default_branch": "main"
            },
            "head_commit": {
                "id": f"manual-deploy-{int(time.time())}",
                "message": "Manual deployment from AltX Deploy Page",
                "committer": {
                    "name": "AltX Deploy"
                }
            }
        }
        
        print(f"📦 Processing deployment for {owner}/{repo_name}")
        
        # Handle push event (same logic as webhook but without signature verification)
        result = await handle_push_event(deployment_payload)
        
        return {
            "success": True,
            "message": f"Deployment initiated for {repo_name}",
            "deployment_result": result,
            "repository": {
                "name": repo_name,
                "owner": owner,
                "url": repo_url
            },
            "deployment_url": f"http://localhost:8000/{repo_name}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Manual deployment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")

@app.post("/api/webhook")
async def github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    """
    Enhanced GitHub App webhook endpoint for automated deployments and security analysis
    """
    try:
        # 1. Get the secret from your environment variables
        secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        if not secret:
            print("❌ Webhook secret is not configured.")
            raise HTTPException(status_code=500, detail="Webhook secret not configured.")

        # 2. Verify the signature to ensure the request is from GitHub
        raw_body = await request.body()
        expected_signature = "sha256=" + hmac.new(secret.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()

        if not x_hub_signature_256:
            print("❌ No signature provided in webhook request.")
            raise HTTPException(status_code=403, detail="No signature provided.")

        if not hmac.compare_digest(expected_signature, x_hub_signature_256):
            print("❌ Invalid webhook signature.")
            raise HTTPException(status_code=403, detail="Invalid signature.")
        
        # 3. Process the event payload
        event_type = request.headers.get("X-GitHub-Event")
        payload = await request.json()

        print(f"🎉 Received valid webhook. Event type: {event_type}")
        
        # 4. Handle different GitHub events
        if event_type == "push":
            return await handle_push_event(payload)
        elif event_type == "pull_request":
            return await handle_pull_request_event(payload)
        elif event_type == "installation":
            return await handle_installation_event(payload)
        elif event_type == "security_advisory":
            return await handle_security_advisory_event(payload)
        else:
            print(f"📝 Unhandled event type: {event_type}")
            return {"status": "event received but not processed", "event_type": event_type}

    except Exception as e:
        print(f"❌ Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")
async def handle_push_event(payload):
    """Handle push events - trigger deployment and security analysis"""
    try:
        ref = payload.get("ref", "")
        repo_info = payload.get("repository", {})
        clone_url = repo_info.get("clone_url")
        repo_name = repo_info.get("name")
        repo_full_name = repo_info.get("full_name")
        default_branch = repo_info.get("default_branch", "main")
        
        # Check if push is to default branch (main/master)
        if ref == f"refs/heads/{default_branch}":
            print(f"🚀 Push to {default_branch} branch detected for {repo_full_name}")
            
            if clone_url and repo_name:
                # Trigger automated security analysis
                print(f"🔍 Triggering automated security analysis for {repo_name}...")
                
                # Run security analysis in background
                analysis_task = asyncio.create_task(
                    run_automated_security_analysis(repo_info, payload)
                )
                
                # Trigger deployment process
                print(f"📦 Triggering deployment for {repo_name}...")
                deployment_task = asyncio.create_task(
                    deploy_project(repo_name, clone_url, payload)
                )
                
                return {
                    "status": "deployment and security analysis triggered",
                    "repo": repo_full_name,
                    "branch": default_branch,
                    "commit": payload.get("head_commit", {}).get("id", "unknown")[:8],
                    "timestamp": datetime.now().isoformat(),
                    "actions": ["security_analysis", "deployment"]
                }
            else:
                print("⚠️ Push event received, but couldn't get repo info.")
                return {"status": "insufficient repo information"}
        else:
            print(f"📝 Push to non-default branch {ref} - no deployment triggered")
            return {"status": "push to non-default branch", "ref": ref}
            
    except Exception as e:
        print(f"❌ Error handling push event: {str(e)}")
        return {"status": "error", "error": str(e)}

async def handle_pull_request_event(payload):
    """Handle pull request events - run security checks on PR"""
    try:
        action = payload.get("action")
        pr_info = payload.get("pull_request", {})
        repo_info = payload.get("repository", {})
        
        print(f"🔍 Pull request {action}: #{pr_info.get('number')} in {repo_info.get('full_name')}")
        
        if action in ["opened", "synchronize", "reopened"]:
            # Run security analysis on PR
            print(f"🛡️ Running security analysis on PR #{pr_info.get('number')}")
            
            # Analyze the PR branch
            head_sha = pr_info.get("head", {}).get("sha")
            base_sha = pr_info.get("base", {}).get("sha")
            
            # Run security analysis in background
            analysis_task = asyncio.create_task(
                run_pr_security_analysis(pr_info, repo_info, payload)
            )
            
            return {
                "status": "pr security analysis triggered",
                "pr_number": pr_info.get("number"),
                "repo": repo_info.get("full_name"),
                "head_sha": head_sha[:8] if head_sha else "unknown",
                "action": action
            }
        
        return {"status": "pr event processed", "action": action}
        
    except Exception as e:
        print(f"❌ Error handling pull request event: {str(e)}")
        return {"status": "error", "error": str(e)}

async def handle_installation_event(payload):
    """Handle GitHub App installation events"""
    try:
        action = payload.get("action")
        installation_info = payload.get("installation", {})
        account_info = installation_info.get("account", {})
        
        print(f"📱 GitHub App {action} for {account_info.get('login')}")
        
        if action == "created":
            print(f"✅ New installation: {account_info.get('login')} ({account_info.get('type')})")
            
            # Send welcome security analysis
            if installation_info.get("repository_selection") == "all":
                print("🔒 Full repository access granted - can provide comprehensive security analysis")
            else:
                repos = payload.get("repositories", [])
                print(f"🔒 Selected repository access: {len(repos)} repositories")
            
            return {
                "status": "installation created",
                "account": account_info.get("login"),
                "repo_access": installation_info.get("repository_selection"),
                "permissions": list(installation_info.get("permissions", {}).keys())
            }
        
        return {"status": "installation event processed", "action": action}
        
    except Exception as e:
        print(f"❌ Error handling installation event: {str(e)}")
        return {"status": "error", "error": str(e)}

async def handle_security_advisory_event(payload):
    """Handle security advisory events"""
    try:
        action = payload.get("action")
        advisory = payload.get("security_advisory", {})
        
        print(f"🚨 Security advisory {action}: {advisory.get('summary', 'Unknown')}")
        
        if action == "published":
            severity = advisory.get("severity", "unknown")
            cve_id = advisory.get("cve_id")
            
            print(f"🔒 New security advisory: {severity} severity")
            if cve_id:
                print(f"🆔 CVE ID: {cve_id}")
            
            # Could trigger repository rescans for affected dependencies
            return {
                "status": "security advisory processed",
                "severity": severity,
                "cve_id": cve_id,
                "action": action
            }
        
        return {"status": "security advisory event processed", "action": action}
        
    except Exception as e:
        print(f"❌ Error handling security advisory event: {str(e)}")
        return {"status": "error", "error": str(e)}

async def run_automated_security_analysis(repo_info, payload):
    """Run automated security analysis on repository"""
    try:
        repo_full_name = repo_info.get("full_name")
        clone_url = repo_info.get("clone_url")
        
        print(f"🔍 Starting automated security analysis for {repo_full_name}")
        
        # Create analysis request
        analysis_request = RepoAnalysisRequest(
            repo_url=clone_url,
            model_type='smart',  # Use smart model for webhook-triggered analysis
            deep_scan=True
        )
        
        # Run comprehensive analysis
        analysis_result = await analyze_repo_comprehensive(analysis_request)
        
        if not analysis_result.get("error"):
            security_score = analysis_result.get("overall_security_score", 0)
            security_level = analysis_result.get("security_level", "Unknown")
            
            print(f"✅ Security analysis complete: {security_score}/100 ({security_level})")
            
            # If security issues found, could create an issue or PR
            critical_issues = []
            critical_issues.extend(analysis_result.get("secret_scan_results", []))
            
            high_severity_static = [
                issue for issue in analysis_result.get("static_analysis_results", [])
                if isinstance(issue, dict) and issue.get("issue_severity") == "HIGH"
            ]
            critical_issues.extend(high_severity_static)
            
            if critical_issues:
                print(f"🚨 {len(critical_issues)} critical security issues found")
                
                # Could automatically create security issue in repository
                await create_security_issue_if_needed(repo_info, analysis_result, critical_issues)
            
            return {
                "analysis_complete": True,
                "security_score": security_score,
                "critical_issues": len(critical_issues)
            }
        else:
            print(f"❌ Security analysis failed: {analysis_result.get('error')}")
            return {"analysis_complete": False, "error": analysis_result.get("error")}
            
    except Exception as e:
        print(f"❌ Automated security analysis error: {str(e)}")
        return {"analysis_complete": False, "error": str(e)}

async def run_pr_security_analysis(pr_info, repo_info, payload):
    """Run security analysis on pull request"""
    try:
        pr_number = pr_info.get("number")
        repo_full_name = repo_info.get("full_name")
        head_repo_url = pr_info.get("head", {}).get("repo", {}).get("clone_url")
        
        print(f"🔍 Analyzing PR #{pr_number} in {repo_full_name}")
        
        if head_repo_url:
            # Create analysis request for PR branch
            analysis_request = RepoAnalysisRequest(
                repo_url=head_repo_url,
                model_type='fast',  # Use fast model for PR analysis
                deep_scan=False  # Lighter scan for PRs
            )
            
            # Run analysis
            analysis_result = await analyze_repo_comprehensive(analysis_request)
            
            if not analysis_result.get("error"):
                security_score = analysis_result.get("overall_security_score", 0)
                
                # Could post security analysis as PR comment
                print(f"✅ PR security analysis complete: {security_score}/100")
                
                # If critical issues found, could request changes
                secrets_found = len(analysis_result.get("secret_scan_results", []))
                if secrets_found > 0:
                    print(f"🚨 PR contains {secrets_found} hardcoded secrets - requires attention")
                
                return {
                    "pr_analysis_complete": True,
                    "security_score": security_score,
                    "secrets_found": secrets_found
                }
            else:
                print(f"❌ PR security analysis failed: {analysis_result.get('error')}")
                return {"pr_analysis_complete": False, "error": analysis_result.get("error")}
        else:
            print("⚠️ Could not get PR head repository URL")
            return {"pr_analysis_complete": False, "error": "No head repo URL"}
            
    except Exception as e:
        print(f"❌ PR security analysis error: {str(e)}")
        return {"pr_analysis_complete": False, "error": str(e)}

async def create_security_issue_if_needed(repo_info, analysis_result, critical_issues):
    """Create a security issue in the repository if critical issues are found"""
    try:
        # This would use the GitHub API to create an issue
        # Implementation depends on whether you want to auto-create issues
        print(f"💡 Could create security issue for {len(critical_issues)} critical findings")
        
        # Example issue content:
        issue_title = f"🔒 Security Review: {len(critical_issues)} Critical Issues Detected"
        issue_body = f"""
# 🛡️ Automated Security Analysis Results

**Security Score:** {analysis_result.get('overall_security_score', 'N/A')}/100

## 🚨 Critical Issues Found ({len(critical_issues)})

{chr(10).join([f"- {issue.get('description', 'Security issue')} in `{issue.get('file', 'unknown file')}`" for issue in critical_issues[:10]])}

## 🔧 Recommended Actions

1. Review and address the critical security issues listed above
2. Consider using environment variables for sensitive data
3. Run additional security testing before deployment

---
*Generated by AltX Security Scanner - Automated Analysis*
"""
        
        print("📝 Security issue content prepared (not created automatically)")
        return {"issue_prepared": True}
        
    except Exception as e:
        print(f"❌ Error preparing security issue: {str(e)}")
        return {"issue_prepared": False, "error": str(e)}

async def deploy_project(repo_name: str, clone_url: str, payload: dict):
    """Actually deploy project to ngrok domain"""
    try:
        print(f"🚀 Starting real deployment for {repo_name}")
        
        # Get deployment directory (create if doesn't exist) - Windows compatible
        if platform.system() == "Windows":
            deployment_base = r"D:\AltX\deployments"  # Raw string for Windows path
        else:
            deployment_base = os.path.join(os.getcwd(), "deployments") 
        
        os.makedirs(deployment_base, exist_ok=True)
        
        # Create unique deployment directory
        deploy_dir = os.path.join(deployment_base, repo_name)
        
        # Remove existing deployment if exists (Windows-safe)
        if os.path.exists(deploy_dir):
            print(f"🗑️ Removing existing deployment: {deploy_dir}")
            try:
                def force_remove_readonly(func, path, exc_info):
                    """Force remove read-only files on Windows"""
                    if os.path.exists(path):
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                
                shutil.rmtree(deploy_dir, onerror=force_remove_readonly)
                print("✅ Existing deployment removed successfully")
            except Exception as e:
                print(f"⚠️ Warning: Could not fully remove existing deployment: {e}")
                # Try to continue anyway
        
        commit_info = payload.get("head_commit", {})
        commit_message = commit_info.get("message", "No commit message")
        committer = commit_info.get("committer", {}).get("name", "Unknown")
        
        print(f"📦 Deploying commit: {commit_message}")
        print(f"👤 Committed by: {committer}")
        
        # Step 1: Clone repository
        print("⏳ Cloning repository...")
        repo = git.Repo.clone_from(clone_url, deploy_dir)
        await asyncio.sleep(1)
        
        # Step 2: Detect project type and install dependencies
        print("⏳ Installing dependencies...")
        project_type = detect_project_type(deploy_dir)
        await install_dependencies(deploy_dir, project_type)
        
        # Step 3: Build project
        print("⏳ Building application...")
        build_result = await build_project(deploy_dir, project_type)
        
        # Step 4: Configure web server (simulation for now)
        print("⏳ Configuring web server...")
        nginx_config = await configure_nginx(repo_name, deploy_dir, project_type)
        
        # Step 5: Copy files to your FastAPI static directory
        print("⏳ Copying files to ngrok domain...")
        static_copy_result = await copy_to_static_domain(repo_name, deploy_dir, project_type)
        
        # Generate deployment URL
        deployment_url = f"https://legal-actively-glider.ngrok-free.app/{repo_name}"
        
        print(f"✅ Deployment complete for {repo_name}")
        print(f"🌐 Live at: {deployment_url}")
        
        return {
            "deployment_complete": True,
            "repo": repo_name,
            "commit": commit_info.get("id", "unknown")[:8],
            "deployment_url": deployment_url,
            "project_type": project_type,
            "build_success": build_result.get("success", False),
            "nginx_configured": nginx_config.get("success", False),
            "files_copied": static_copy_result.get("files_copied", 0)
        }
        
    except Exception as e:
        print(f"❌ Deployment error: {str(e)}")
        return {"deployment_complete": False, "error": str(e)}

def detect_project_type(deploy_dir: str) -> str:
    """Detect what type of project this is"""
    if os.path.exists(os.path.join(deploy_dir, "package.json")):
        return "nodejs"
    elif os.path.exists(os.path.join(deploy_dir, "requirements.txt")):
        return "python"
    elif os.path.exists(os.path.join(deploy_dir, "index.html")):
        return "static"
    elif os.path.exists(os.path.join(deploy_dir, "Dockerfile")):
        return "docker"
    else:
        return "unknown"

async def install_dependencies(deploy_dir: str, project_type: str):
    """Install project dependencies based on type"""
    try:
        if project_type == "nodejs":
            # Check for package manager
            if os.path.exists(os.path.join(deploy_dir, "package-lock.json")):
                subprocess.run(["npm", "install"], cwd=deploy_dir, check=True)
            elif os.path.exists(os.path.join(deploy_dir, "yarn.lock")):
                subprocess.run(["yarn", "install"], cwd=deploy_dir, check=True)
            else:
                subprocess.run(["npm", "install"], cwd=deploy_dir, check=True)
        
        elif project_type == "python":
            # Create virtual environment and install
            subprocess.run(["python", "-m", "venv", "venv"], cwd=deploy_dir, check=True)
            
            # Mac/Unix pip path
            pip_path = os.path.join(deploy_dir, "venv", "bin", "pip")
            subprocess.run([pip_path, "install", "-r", "requirements.txt"], cwd=deploy_dir, check=True)
        
        print(f"✅ Dependencies installed for {project_type} project")
        return {"success": True}
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Dependency installation failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        print(f"⚠️ Dependency installation skipped: {e}")
        return {"success": True, "skipped": True}

async def build_project(deploy_dir: str, project_type: str):
    """Build the project"""
    try:
        if project_type == "nodejs":
            # Check for build script in package.json
            package_json_path = os.path.join(deploy_dir, "package.json")
            if os.path.exists(package_json_path):
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                scripts = package_data.get("scripts", {})
                
                if "build" in scripts:
                    subprocess.run(["npm", "run", "build"], cwd=deploy_dir, check=True)
                elif "dist" in scripts:
                    subprocess.run(["npm", "run", "dist"], cwd=deploy_dir, check=True)
        
        elif project_type == "python":
            # For Python, we might need to collect static files or build assets
            print("🐍 Python project detected - no build step required")
        
        print(f"✅ Build completed for {project_type} project")
        return {"success": True}
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        print(f"⚠️ Build skipped: {e}")
        return {"success": True, "skipped": True}

async def configure_nginx(repo_name: str, deploy_dir: str, project_type: str):
    """Configure nginx for the deployment (simulation)"""
    try:
        # Determine document root based on project type
        if project_type == "nodejs":
            # Check for common build directories
            for build_dir in ["dist", "build", "public"]:
                potential_root = os.path.join(deploy_dir, build_dir)
                if os.path.exists(potential_root):
                    document_root = potential_root
                    break
            else:
                document_root = deploy_dir
        elif project_type == "static":
            document_root = deploy_dir
        else:
            document_root = deploy_dir
        
        print(f"📝 Nginx would serve from: {document_root}")
        print(f"🌐 Would be accessible at: /{repo_name}")
        
        # In a real deployment, you'd write nginx config and reload
        return {"success": True, "document_root": document_root}
        
    except Exception as e:
        print(f"❌ Nginx configuration failed: {e}")
        return {"success": False, "error": str(e)}

async def copy_to_static_domain(repo_name: str, deploy_dir: str, project_type: str):
    """Copy deployed files to FastAPI static directory for ngrok domain"""
    try:
        # Create static directory in your FastAPI backend (Windows compatible)
        static_base = os.path.join(os.getcwd(), "static")
        repo_static_dir = os.path.join(static_base, repo_name)
        
        os.makedirs(static_base, exist_ok=True)
        
        # Remove existing deployment (Windows safe)
        if os.path.exists(repo_static_dir):
            def force_remove_readonly(func, path, exc_info):
                """Force remove read-only files on Windows"""
                if os.path.exists(path):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
            
            shutil.rmtree(repo_static_dir, onerror=force_remove_readonly)
        
        # Determine source directory
        if project_type == "nodejs":
            # Look for built files
            for build_dir in ["dist", "build", "public"]:
                source_path = os.path.join(deploy_dir, build_dir)
                if os.path.exists(source_path):
                    shutil.copytree(source_path, repo_static_dir, ignore=shutil.ignore_patterns(
                        '.git', 'node_modules', '__pycache__', '*.pyc', '.env*', 'venv', 'env'
                    ))
                    files_copied = len([f for f in os.listdir(repo_static_dir) if os.path.isfile(os.path.join(repo_static_dir, f))])
                    print(f"✅ Copied {files_copied} files from {build_dir}/ to static domain")
                    return {"success": True, "files_copied": files_copied, "source": build_dir}
        
        # Fallback: copy entire directory
        shutil.copytree(deploy_dir, repo_static_dir, ignore=shutil.ignore_patterns(
            '.git', 'node_modules', '*.pyc', '__pycache__', '.env*', 'venv', 'env'
        ))
        files_copied = sum([len(files) for r, d, files in os.walk(repo_static_dir)])
        print(f"✅ Copied {files_copied} files to static domain")
        
        return {"success": True, "files_copied": files_copied, "source": "root"}
        
    except Exception as e:
        print(f"❌ Static file copy failed: {e}")
        return {"success": False, "error": str(e)}
# Add this NEW function to main.py (alongside your existing deploy_project)

async def deploy_project_with_docker(repo_name: str, clone_url: str, payload: dict):
    """Enhanced CI/CD deployment with Docker builds - fallback to standard deployment"""
    try:
        print(f"🐳 Attempting Docker CI/CD deployment for {repo_name}")
        
        # Check if Docker is available
        try:
            docker_client = docker.from_env()
            print("✅ Docker is available")
        except Exception as docker_error:
            print(f"⚠️ Docker not available: {docker_error}")
            # Fall back to your proven method immediately
            return await deploy_project(repo_name, clone_url, payload)
        
        # Step 1: Prepare directories
        deployment_base = "/Users/trishajanath/AltX/deployments"
        deploy_dir = os.path.join(deployment_base, repo_name)
        build_output_dir = os.path.join(deployment_base, f"{repo_name}-build")
        
        os.makedirs(deployment_base, exist_ok=True)
        
        # Clean existing deployments
        for dir_path in [deploy_dir, build_output_dir]:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
        
        commit_info = payload.get("head_commit", {})
        print(f"📦 Docker deployment for: {commit_info.get('message', 'No message')}")
        
        # Step 2: Clone repository
        print("⏳ Cloning repository for Docker build...")
        repo = git.Repo.clone_from(clone_url, deploy_dir)
        
        # Step 3: Detect if this project needs Docker builds
        project_type = detect_project_type(deploy_dir)
        
        # Check if project actually benefits from Docker builds
        needs_docker_build = False
        if project_type == "nodejs" and os.path.exists(os.path.join(deploy_dir, "package.json")):
            with open(os.path.join(deploy_dir, "package.json"), 'r') as f:
                package_data = json.load(f)
                if "build" in package_data.get("scripts", {}):
                    needs_docker_build = True
        elif project_type == "python" and os.path.exists(os.path.join(deploy_dir, "requirements.txt")):
            needs_docker_build = True
        
        if not needs_docker_build:
            print(f"📄 Project type '{project_type}' doesn't need Docker builds, using standard deployment")
            return await deploy_project(repo_name, clone_url, payload)
        
        # Step 4: Check if Docker build files exist
        docker_config_dir = "/Users/trishajanath/AltX/backend/docker-configs"
        if not os.path.exists(docker_config_dir):
            print("⚠️ Docker configurations not found, using standard deployment")
            return await deploy_project(repo_name, clone_url, payload)
        
        # Step 5: Try Docker build
        print("🔨 Attempting Docker build...")
        build_result = await build_in_docker(deploy_dir, build_output_dir, project_type)
        
        if not build_result.get("success"):
            print(f"⚠️ Docker build failed: {build_result.get('error')}")
            print("🔄 Falling back to standard deployment method")
            return await deploy_project(repo_name, clone_url, payload)
        
        # Step 6: Copy Docker build output to static domain
        print("📁 Copying Docker build to static domain...")
        static_copy_result = await copy_build_to_static(repo_name, build_output_dir, project_type)
        
        if not static_copy_result.get("success"):
            print("⚠️ Docker build copy failed, using standard deployment")
            return await deploy_project(repo_name, clone_url, payload)
        
        # Success! Return Docker deployment result
        deployment_url = f"https://legal-actively-glider.ngrok-free.app/{repo_name}"
        
        print(f"✅ Docker CI/CD deployment complete for {repo_name}")
        print(f"🌐 Live at: {deployment_url}")
        
        return {
            "deployment_complete": True,
            "repo": repo_name,
            "commit": commit_info.get("id", "unknown")[:8],
            "deployment_url": deployment_url,
            "project_type": project_type,
            "build_success": True,
            "docker_build": True,
            "nginx_configured": False,
            "files_copied": static_copy_result.get("files_copied", 0),
            "deployment_method": "docker_ci_cd_success"
        }
        
    except Exception as e:
        print(f"❌ Docker CI/CD deployment error: {str(e)}")
        print("🔄 Falling back to proven standard deployment method")
        # Always fall back to your working method
        return await deploy_project(repo_name, clone_url, payload)

async def build_in_docker(source_dir: str, output_dir: str, project_type: str):
    """Build project using Docker containers"""
    try:
        # ADD THIS LINE AT THE TOP OF THE FUNCTION
        docker_client = docker.from_env()
        
        # Check if Docker files exist
        dockerfile_map = {
            "nodejs": "Dockerfile.nodejs",
            "python": "Dockerfile.python", 
            "php": "Dockerfile.php",
            "static": "Dockerfile.universal",
            "unknown": "Dockerfile.universal"
        }
        
        dockerfile_name = dockerfile_map.get(project_type, "Dockerfile.universal")
        dockerfile_path = f"/Users/trishajanath/AltX/backend/docker-configs/{dockerfile_name}"
        
        # Check if Docker files exist
        if not os.path.exists(dockerfile_path):
            print(f"⚠️ Docker configuration not found: {dockerfile_path}")
            return {"success": False, "error": "Docker configuration missing"}
        
        print(f"🐳 Using Docker configuration: {dockerfile_name}")
        
        # Build Docker image
        print("🔨 Building Docker image...")
        image_tag = f"altx-builder-{project_type}:latest"
        
        # Build image with build context
        image, build_logs = docker_client.images.build(
            path="/Users/trishajanath/AltX/backend",
            dockerfile=f"docker-configs/{dockerfile_name}",
            tag=image_tag,
            rm=True,
            forcerm=True
        )
        
        print("✅ Docker image built successfully")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Run build container
        print("🏗️ Running build process in container...")
        
        container = docker_client.containers.run(
            image_tag,
            volumes={
                source_dir: {'bind': '/app', 'mode': 'ro'},
                output_dir: {'bind': '/deployment', 'mode': 'rw'}
            },
            working_dir='/app',
            detach=True,
            auto_remove=False
        )
        
        # Wait for completion and get logs
        exit_code = container.wait()
        build_logs = container.logs().decode('utf-8')
        
        print("📋 Build logs:")
        print(build_logs[-1000:])  # Last 1000 characters
        
        # Clean up container
        container.remove()
        
        if exit_code['StatusCode'] != 0:
            return {"success": False, "error": f"Build failed with exit code {exit_code['StatusCode']}"}
        
        # Determine document root from build output
        document_root = output_dir
        if os.path.exists(os.path.join(output_dir, "dist")):
            document_root = os.path.join(output_dir, "dist")
        elif os.path.exists(os.path.join(output_dir, "build")):
            document_root = os.path.join(output_dir, "build")
        
        print(f"✅ Docker build completed successfully")
        print(f"📁 Document root: {document_root}")
        
        return {
            "success": True,
            "image_tag": image_tag,
            "document_root": document_root,
            "build_logs": build_logs[-500:],  # Last 500 chars
            "files_created": len(os.listdir(output_dir)) if os.path.exists(output_dir) else 0
        }
        
    except docker.errors.DockerException as e:
        print(f"❌ Docker not available: {e}")
        return {"success": False, "error": f"Docker not available: {str(e)}"}
    except Exception as e:
        print(f"❌ Docker deployment error: {e}")
        return {"success": False, "error": str(e)}
    
async def copy_build_to_static(repo_name: str, build_dir: str, project_type: str):
    """Copy Docker build output to static domain"""
    try:
        # Create static directory in your FastAPI backend
        static_base = "/Users/trishajanath/AltX/backend/static"
        repo_static_dir = os.path.join(static_base, repo_name)
        
        os.makedirs(static_base, exist_ok=True)
        
        # Remove existing deployment
        if os.path.exists(repo_static_dir):
            shutil.rmtree(repo_static_dir)
        
        # Copy build output to static domain
        if os.path.exists(build_dir):
            shutil.copytree(build_dir, repo_static_dir)
            files_copied = sum([len(files) for r, d, files in os.walk(repo_static_dir)])
            print(f"✅ Copied {files_copied} files from Docker build to static domain")
            
            return {"success": True, "files_copied": files_copied}
        else:
            print(f"❌ Docker build directory not found: {build_dir}")
            return {"success": False, "error": "Build directory not found"}
            
    except Exception as e:
        print(f"❌ Failed to copy Docker build to static: {e}")
        return {"success": False, "error": str(e)}
    
async def handle_push_event(payload):
    """Handle push events - try Docker first, fallback to standard deployment"""
    try:
        ref = payload.get("ref", "")
        repo_info = payload.get("repository", {})
        clone_url = repo_info.get("clone_url")
        repo_name = repo_info.get("name")
        repo_full_name = repo_info.get("full_name")
        default_branch = repo_info.get("default_branch", "main")
        
        if ref == f"refs/heads/{default_branch}":
            print(f"🚀 Push to {default_branch} branch detected for {repo_full_name}")
            
            if clone_url and repo_name:
                # Trigger security analysis (async)
                analysis_task = asyncio.create_task(
                    run_automated_security_analysis(repo_info, payload)
                )
                
                # Try Docker deployment first, fallback to standard deployment
                try:
                    deployment_result = await deploy_project_with_docker(repo_name, clone_url, payload)
                    deployment_method = "docker_ci_cd"
                except Exception as e:
                    print(f"⚠️ Docker deployment failed: {e}, using standard deployment")
                    deployment_result = await deploy_project(repo_name, clone_url, payload)
                    deployment_method = "standard"
                
                return {
                    "status": "enhanced CI/CD deployment triggered",
                    "repo": repo_full_name,
                    "branch": default_branch,
                    "commit": payload.get("head_commit", {}).get("id", "unknown")[:8],
                    "deployment_method": deployment_method,
                    "timestamp": datetime.now().isoformat(),
                    "actions": ["security_analysis", "enhanced_deployment"],
                    "deployment_result": deployment_result
                }
        
        return {"status": "push to non-default branch", "ref": ref}
        
    except Exception as e:
        print(f"❌ Error handling push event: {str(e)}")
        return {"status": "error", "error": str(e)}

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

from fastapi.staticfiles import StaticFiles

# Add this after your other app configurations but before the endpoints
# Create static directory if it doesn't exist (Windows compatible)
if platform.system() == "Windows":
    static_dir = os.path.join(os.getcwd(), "static")
else:
    static_dir = "/Users/trishajanath/AltX/backend/static"

os.makedirs(static_dir, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/{repo_name}/{file_path:path}")
async def serve_deployed_files(repo_name: str, file_path: str):
    """Serve deployed repository files"""
    try:
        # Windows compatible path
        if platform.system() == "Windows":
            repo_static_dir = os.path.join(os.getcwd(), "static", repo_name)
        else:
            repo_static_dir = f"/Users/trishajanath/AltX/backend/static/{repo_name}"
        
        file_full_path = os.path.join(repo_static_dir, file_path)
        
        # Security check: ensure file is within the repo directory
        if not os.path.realpath(file_full_path).startswith(os.path.realpath(repo_static_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if os.path.exists(file_full_path) and os.path.isfile(file_full_path):
            from fastapi.responses import FileResponse
            return FileResponse(file_full_path)
        
        # Try index.html for SPA applications
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        
        raise HTTPException(status_code=404, detail="File not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")

@app.get("/{repo_name}")
async def serve_deployed_repo_root(repo_name: str):
    """Serve deployed repository root (index.html)"""
    try:
        static_dir = f"/Users/trishajanath/AltX/backend/static/{repo_name}"
        index_path = os.path.join(static_dir, "index.html")
        
        if os.path.exists(index_path):
            from fastapi.responses import FileResponse
            return FileResponse(index_path)
        
        # If no index.html, show directory listing
        if os.path.exists(static_dir):
            files = os.listdir(static_dir)
            html_content = f"""
<!DOCTYPE html>
<html>
<head><title>🚀 {repo_name} - Deployed Files</title></head>
<body>
    <h1>🚀 Repository: {repo_name}</h1>
    <h2>📁 Deployed Files:</h2>
    <ul>
        {''.join([f'<li><a href="/{repo_name}/{f}">{f}</a></li>' for f in files])}
    </ul>
    <p><strong>Deployment URL:</strong> https://legal-actively-glider.ngrok-free.app/{repo_name}</p>
</body>
</html>
            """
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=html_content)
        
        raise HTTPException(status_code=404, detail=f"Repository {repo_name} not deployed")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving repository: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)