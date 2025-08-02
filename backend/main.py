import os
import shutil
import git
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from starlette.concurrency import run_in_threadpool
import tempfile
import json
import re
from scanner.file_security_scanner import scan_for_sensitive_files, scan_file_contents_for_secrets
from scanner.directory_scanner import scan_common_paths

# --- Local Imports ---
from ai_assistant import get_chat_response, RepoAnalysis
from scanner import scan_url
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

# --- Request Models ---
class ScanRequest(BaseModel):
    url: str
    model_type: str = 'fast'

class RepoAnalysisRequest(BaseModel):
    repo_url: str
    model_type: str = 'smart'
    deep_scan: bool = True

# --- Enhanced Security Analysis Functions ---
def scan_dependencies(directory_path: str) -> Dict:
    """Scan for vulnerable dependencies in package files"""
    
    vulnerable_patterns = {
        'package.json': {
            'lodash': {'versions': ['<4.17.19'], 'severity': 'High'},
            'axios': {'versions': ['<0.21.1'], 'severity': 'Critical'},
            'jquery': {'versions': ['<3.5.0'], 'severity': 'Medium'},
            'express': {'versions': ['<4.17.1'], 'severity': 'High'},
            'react': {'versions': ['<16.13.0'], 'severity': 'Medium'},
            'angular': {'versions': ['<10.0.0'], 'severity': 'Medium'},
        },
        'requirements.txt': {
            'django': {'versions': ['<2.2.13'], 'severity': 'Critical'},
            'flask': {'versions': ['<1.1.0'], 'severity': 'High'},
            'requests': {'versions': ['<2.20.0'], 'severity': 'Medium'},
            'pillow': {'versions': ['<6.2.0'], 'severity': 'High'},
            'urllib3': {'versions': ['<1.24.2'], 'severity': 'High'},
            'pyyaml': {'versions': ['<5.1'], 'severity': 'Critical'},
        }
    }
    
    findings = {
        'dependency_files_found': [],
        'vulnerable_packages': [],
        'total_dependencies': 0,
        'security_advisory_count': 0
    }
    
    try:
        for root, dirs, files in os.walk(directory_path):
            if '.git' in root:
                continue
                
            for file in files:
                if file in vulnerable_patterns:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, directory_path)
                    
                    findings['dependency_files_found'].append({
                        'file': relative_path,
                        'type': file
                    })
                    
                    # Analyze dependencies
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            if file == 'package.json':
                                data = json.loads(content)
                                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                                findings['total_dependencies'] += len(deps)
                                
                                for pkg_name, version in deps.items():
                                    if pkg_name in vulnerable_patterns[file]:
                                        findings['vulnerable_packages'].append({
                                            'package': pkg_name,
                                            'current_version': version,
                                            'file': relative_path,
                                            'severity': vulnerable_patterns[file][pkg_name]['severity'],
                                            'advisory': f"Update {pkg_name} to latest version"
                                        })
                                        
                            elif file == 'requirements.txt':
                                lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
                                findings['total_dependencies'] += len(lines)
                                
                                for line in lines:
                                    pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].strip()
                                    if pkg_name in vulnerable_patterns[file]:
                                        findings['vulnerable_packages'].append({
                                            'package': pkg_name,
                                            'current_version': line,
                                            'file': relative_path,
                                            'severity': vulnerable_patterns[file][pkg_name]['severity'],
                                            'advisory': f"Update {pkg_name} to latest version"
                                        })
                    except Exception as e:
                        pass
        
        findings['security_advisory_count'] = len(findings['vulnerable_packages'])
        return findings
        
    except Exception as e:
        return {
            'error': f"Error scanning dependencies: {str(e)}",
            'dependency_files_found': [],
            'vulnerable_packages': [],
            'total_dependencies': 0,
            'security_advisory_count': 0
        }

def scan_code_quality_patterns(directory_path: str) -> List[Dict]:
    """Scan for insecure coding patterns across multiple languages"""
    
    patterns = {
        'python': {
            'eval_usage': {'pattern': r'eval\s*\(', 'severity': 'Critical', 'description': 'Use of eval() can lead to code injection'},
            'exec_usage': {'pattern': r'exec\s*\(', 'severity': 'Critical', 'description': 'Use of exec() can lead to code injection'},
            'shell_injection': {'pattern': r'os\.system\s*\(', 'severity': 'High', 'description': 'Potential shell injection vulnerability'},
            'sql_injection': {'pattern': r'cursor\.execute\s*\(\s*["\'].*%.*["\']', 'severity': 'Critical', 'description': 'Potential SQL injection vulnerability'},
            'pickle_usage': {'pattern': r'pickle\.loads?\s*\(', 'severity': 'High', 'description': 'Unsafe deserialization with pickle'},
            'subprocess_shell': {'pattern': r'subprocess\.\w+\(.*shell=True', 'severity': 'High', 'description': 'Subprocess with shell=True can be dangerous'},
            'input_function': {'pattern': r'\binput\s*\(', 'severity': 'Medium', 'description': 'input() function can be vulnerable in Python 2'},
        },
        'javascript': {
            'eval_usage': {'pattern': r'eval\s*\(', 'severity': 'Critical', 'description': 'Use of eval() can lead to code injection'},
            'document_write': {'pattern': r'document\.write\s*\(', 'severity': 'Medium', 'description': 'document.write can lead to XSS'},
            'inner_html': {'pattern': r'innerHTML\s*=', 'severity': 'Medium', 'description': 'innerHTML assignment can lead to XSS'},
            'local_storage': {'pattern': r'localStorage\.setItem', 'severity': 'Low', 'description': 'Sensitive data in localStorage'},
            'console_log': {'pattern': r'console\.log\s*\(', 'severity': 'Low', 'description': 'Remove console.log in production'},
            'function_constructor': {'pattern': r'new\s+Function\s*\(', 'severity': 'High', 'description': 'Function constructor can lead to code injection'},
            'settimeout_string': {'pattern': r'setTimeout\s*\(\s*["\']', 'severity': 'High', 'description': 'setTimeout with string argument can lead to code injection'},
        }
    }
    
    findings = []
    
    try:
        for root, dirs, files in os.walk(directory_path):
            if '.git' in root:
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory_path)
                
                # Determine file type
                lang = None
                if file.endswith('.py'):
                    lang = 'python'
                elif file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    lang = 'javascript'
                
                if lang and lang in patterns:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            for pattern_name, pattern_info in patterns[lang].items():
                                matches = list(re.finditer(pattern_info['pattern'], content, re.IGNORECASE))
                                
                                for match in matches:
                                    line_num = content[:match.start()].count('\n') + 1
                                    findings.append({
                                        'file': relative_path,
                                        'line': line_num,
                                        'pattern': pattern_name,
                                        'severity': pattern_info['severity'],
                                        'description': pattern_info['description'],
                                        'code_snippet': match.group()[:100],
                                        'language': lang
                                    })
                    except Exception:
                        pass
        
        return findings
        
    except Exception as e:
        return [{"error": f"Error scanning code quality: {str(e)}"}]

def is_likely_false_positive(file_path: str, secret_type: str, match: str) -> bool:
    """Enhanced general-purpose false positive filter"""
    
    # Package management files (contains hashes, not secrets)
    package_files = ['package-lock.json', 'yarn.lock', 'composer.lock', 'Pipfile.lock', 'poetry.lock']
    if any(pkg_file in file_path.lower() for pkg_file in package_files):
        if secret_type in ['aws_secret_key', 'aws_access_key']:
            return True
    
    # Build/dist/cache directories
    if any(dir_name in file_path.lower() for dir_name in ['node_modules', 'dist/', 'build/', '.cache/', 'vendor/']):
        return True
    
    # Data/configuration files (often contain encoded data)
    data_extensions = ['.json', '.xml', '.csv', '.log', '.dump', '.backup']
    data_keywords = ['data', 'config', 'settings', 'cache', 'temp', 'log', 'backup', 'dump']
    
    file_lower = file_path.lower()
    if (any(ext in file_lower for ext in data_extensions) and 
        any(keyword in file_lower for keyword in data_keywords)):
        if secret_type in ['aws_secret_key', 'aws_access_key']:
            return True
    
    # Base64 encoded data (universal pattern)
    if secret_type in ['aws_secret_key'] and len(match) >= 20:
        # Base64 characteristics: contains +, /, = and high alphanumeric ratio
        has_base64_chars = any(char in match for char in ['+', '/', '='])
        alphanumeric_ratio = sum(c.isalnum() for c in match) / len(match)
        
        if has_base64_chars or alphanumeric_ratio > 0.9:
            return True
    
    # Non-AWS patterns (anything that doesn't look like real AWS credentials)
    if secret_type in ['aws_secret_key']:
        # Real AWS access keys start with 'AKIA'
        # Real AWS secret keys are 40 chars, mixed case, no special pattern
        if not match.startswith('AKIA') and len(match) == 40:
            # If it has patterns typical of encoded data, it's likely a false positive
            return True
    
    # Test/demo/example patterns
    test_indicators = ['test', 'demo', 'example', 'sample', 'mock', 'fake', 'dummy', 'placeholder']
    if any(indicator in match.lower() or indicator in file_path.lower() for indicator in test_indicators):
        return True
    
    # Very short matches
    if len(match.strip()) < 20:
        return True
    
    return False

# --- ENDPOINTS ---


@app.post("/scan")
async def scan(request: ScanRequest):
    """Scan a website for security vulnerabilities and store results for AI chat"""
    url = request.url
    
    try:
        # --- HYBRID CRAWLER INTEGRATION ---
        # Replace the old crawler call with the new hybrid one.
        # Since crawl_hybrid is async, we can await it directly.
        pages = await crawl_hybrid(url)
        
        # The rest of the scanning proceeds as before
        scan_result = await run_in_threadpool(scan_url, url)
        
        # Correctly call the async directory scanner
        exposed_paths = await scan_common_paths(url)
        
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
        
        summary = f"""🔒 **Security Scan Complete**

📊 **Scan Results Summary:**
• Target: {url}
• Security Score: {security_score}/100 ({security_level})
• HTTPS: {'✅ Enabled' if scan_result["https"] else '❌ Disabled'}
• Vulnerabilities: {len(scan_result["flags"])} issues found
• Pages Crawled: {len(pages)} pages
• Security Headers: {len(scan_result["headers"])} detected
• Exposed Paths: {len(exposed_paths)} found

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
            "suggestions": suggestions,
            "ai_assistant_advice": ai_advice,
            "summary": summary
        }
        
        WebsiteScan.latest_scan = scan_response
        return scan_response
        
    except Exception as e:
        # Return a more structured error response
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
            
            # 2. Deep content scanning for secrets (with false positive filtering)
            secret_scan_results = []
            if deep_scan:
                print("🕵️ Performing deep content scanning for secrets...")
                scanned_files = 0
                for root, dirs, files in os.walk(temp_dir):
                    # Skip .git directory
                    if '.git' in root:
                        continue
                    
                    for file in files:
                        if scanned_files >= 50:  # Limit to prevent timeout
                            break
                        
                        if file.endswith(('.py', '.js', '.json', '.yml', '.yaml', '.env', '.config', '.txt', '.md')):
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
            
            # Enhanced recommendations
            recommendations = []
            
            if file_scan_results.get('sensitive_files'):
                recommendations.append("🚨 CRITICAL: Remove or secure sensitive files detected")
            
            if secret_scan_results:
                recommendations.append("🔑 CRITICAL: Remove hardcoded secrets from source code")
            
            if static_analysis_results and len(static_analysis_results) > 0:
                recommendations.append("🔬 HIGH: Fix static code analysis vulnerabilities")
            
            if dependency_scan_results.get('vulnerable_packages'):
                recommendations.append("📦 HIGH: Update vulnerable dependencies")
            
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
            
            comprehensive_results["recommendations"] = recommendations[:8]
            
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

@app.post("/ai-chat")
async def unified_ai_chat(request: dict):
    """Unified AI chat endpoint that automatically uses latest scan results as context"""
    try:
        question = request.get('question', '')
        context_type = request.get('context', 'auto')  # 'auto', 'general', 'website_scan', 'repo_analysis'
        model_type = request.get('model_type', 'fast')
        previous_history = request.get('history', [])
        
        # Validate model type
        if model_type not in ['fast', 'smart']:
            model_type = 'fast'
        
        # Build enhanced context with automatic scan result detection
        enhanced_context = f"MODEL TYPE: {model_type}\nUSER QUESTION: {question}\n\n"
        
        # Auto-detect and use available scan results
        if context_type == 'auto':
            # Check for repository analysis first (most comprehensive)
            if hasattr(RepoAnalysis, 'latest_analysis') and RepoAnalysis.latest_analysis:
                context_type = 'repo_analysis'
                enhanced_context += "🔍 **AUTOMATICALLY DETECTED: Repository Analysis Available**\n\n"
            # Check for website scan results
            elif hasattr(WebsiteScan, 'latest_scan') and WebsiteScan.latest_scan:
                context_type = 'website_scan'
                enhanced_context += "🌐 **AUTOMATICALLY DETECTED: Website Scan Available**\n\n"
            else:
                context_type = 'general'
                enhanced_context += "🤖 **GENERAL SECURITY CONSULTATION** - No recent scan data available.\n\n"
        
        # Repository Analysis Context (from /analyze-repo)
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
        
        # Website Scan Context (from /scan or manual)
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

🚨 **SECURITY ISSUES:**
{chr(10).join([f'• {flag}' for flag in scan_data.get('flags', [])]) if scan_data.get('flags') else '• No critical issues detected'}

🔒 **SECURITY HEADERS:**
{chr(10).join([f'• {header}: {value}' for header, value in scan_data.get('headers', {}).items()]) if scan_data.get('headers') else '• No security headers detected'}

📄 **PAGES CRAWLED:**
{chr(10).join([f'• {page}' for page in website_data.get('pages', [])[:5]]) if website_data else '• No pages data'}

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
• Common vulnerability explanations
• Security implementation guidance
• Code review suggestions
• Security tool recommendations

To get specific analysis, please run:
• `/analyze-repo` for repository security analysis
• `/scan` for website security scanning
"""
        
        # Build conversation history
        if previous_history:
            history = previous_history.copy()
            history.append({'type': 'user', 'parts': [enhanced_context + f"\n\nBased on the above security analysis, provide a helpful response to: {question}"]})
        else:
            history = [{'type': 'user', 'parts': [enhanced_context + f"\n\nBased on the above security analysis, provide a helpful response to: {question}"]}]
        
        response = await run_in_threadpool(get_chat_response, history, model_type)
        
        # Add response to history
        history.append({'type': 'assistant', 'parts': [response]})
        
        return {
            "response": response,
            "model_used": model_type,
            "context_detected": context_type,
            "scan_data_available": context_type in ['repo_analysis', 'website_scan'],
            "history": history
        }
        
    except Exception as e:
        return {
            "response": f"❌ Error: {str(e)}",
            "model_used": model_type if 'model_type' in locals() else 'unknown',
            "context_detected": 'error',
            "scan_data_available": False,
            "history": []
        }

@app.get("/health")
async def health_check():
    """Check if the API is running"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)