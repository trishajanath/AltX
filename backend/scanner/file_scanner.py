# Keep only these imports (remove FastAPI imports)
import os
import shutil
import git
import tempfile
import json
import re
import ssl
import socket
import datetime
from urllib.parse import urlparse
import requests
from typing import List, Dict, Optional


# Keep local imports for functions only
from scanner.file_security_scanner import scan_for_sensitive_files, scan_file_contents_for_secrets
from scanner.directory_scanner import scan_common_paths
from scanner.hybrid_crawler import crawl_hybrid 
from nlp_suggester import suggest_fixes
import ai_assistant
from ai_assistant import get_chat_response, RepoAnalysis
from scanner.secrets_detector import scan_secrets
from scanner.static_python import run_bandit

try:
    from ai_assistant import github_client
except ImportError:
    github_client = None
    print("Warning: GitHub client not available")

# Add these functions after your existing imports and before the FastAPI app definition

def scan_url(url: str) -> Dict:
    """Enhanced URL security scanner with SSL certificate analysis"""
    
    result = {
        "https": False,
        "ssl_certificate": {},
        "ssl_security_score": 0,
        "headers": {},
        "flags": [],
        "security_score": 0,
        "security_level": "Unknown"
    }
    
    try:
        # Check if HTTPS is enabled
        result["https"] = url.startswith("https://")
        
        if result["https"]:
            # Perform detailed SSL certificate analysis
            ssl_analysis = analyze_ssl_certificate(url)
            result["ssl_certificate"] = ssl_analysis
            result["ssl_security_score"] = ssl_analysis.get("ssl_score", 0)
            
            # Add SSL-related flags
            if ssl_analysis.get("expired"):
                result["flags"].append("❌ SSL certificate has expired")
            if ssl_analysis.get("self_signed"):
                result["flags"].append("⚠️ Self-signed SSL certificate detected")
            if ssl_analysis.get("weak_cipher"):
                result["flags"].append("⚠️ Weak SSL cipher suite detected")
            if ssl_analysis.get("expires_soon"):
                result["flags"].append("⚠️ SSL certificate expires within 30 days")
        
        # Get website headers and content
        response = requests.get(url, timeout=10, verify=True)
        result["headers"] = dict(response.headers)
        
        # Check for security headers
        security_headers_analysis = analyze_security_headers(result["headers"])
        result["flags"].extend(security_headers_analysis["flags"])
        
        # Calculate security score including SSL
        score = calculate_security_score(result)
        result["security_score"] = score
        result["security_level"] = get_security_level(score)
        
        return result
        
    except Exception as e:
        result["flags"].append(f"❌ Scan failed: {str(e)}")
        return result

def analyze_security_headers(headers: Dict[str, str]) -> Dict:
    """Analyze security headers and return flags"""
    flags = []
    
    # Critical security headers
    critical_headers = {
        "Strict-Transport-Security": "Missing HSTS header - HTTPS security risk",
        "Content-Security-Policy": "Missing Content Security Policy - XSS risk",
        "X-Frame-Options": "Missing X-Frame-Options - Clickjacking risk",
        "X-Content-Type-Options": "Missing X-Content-Type-Options - MIME sniffing risk",
        "X-XSS-Protection": "Missing X-XSS-Protection header"
    }
    
    for header, message in critical_headers.items():
        if header not in headers:
            flags.append(f"⚠️ {message}")
    
    # Check for information disclosure
    disclosure_headers = ["Server", "X-Powered-By", "X-AspNet-Version"]
    for header in disclosure_headers:
        if header in headers:
            flags.append(f"ℹ️ Information disclosure: {header} header present")
    
    return {"flags": flags}

def analyze_ssl_certificate(url: str) -> Dict:
    """Comprehensive SSL certificate analysis"""
    
    ssl_analysis = {
        "valid": False,
        "expired": False,
        "self_signed": False,
        "expires_soon": False,
        "weak_cipher": False,
        "ssl_score": 0,
        "certificate_details": {},
        "cipher_info": {},
        "security_issues": []
    }
    
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        port = parsed_url.port or 443
        
        if parsed_url.scheme != "https":
            ssl_analysis["security_issues"].append("HTTPS not enabled")
            return ssl_analysis
        
        # Get SSL certificate
        context = ssl.create_default_context()
        
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert_info = ssock.getpeercert()
                cipher_info = ssock.cipher()
                
                if cert_info:
                    # Certificate validity
                    not_after = datetime.datetime.strptime(
                        cert_info['notAfter'], '%b %d %H:%M:%S %Y %Z'
                    )
                    not_before = datetime.datetime.strptime(
                        cert_info['notBefore'], '%b %d %H:%M:%S %Y %Z'
                    )
                    
                    now = datetime.datetime.utcnow()
                    
                    ssl_analysis["valid"] = not_before <= now <= not_after
                    ssl_analysis["expired"] = now > not_after
                    ssl_analysis["expires_soon"] = (not_after - now).days < 30
                    
                    # Check if self-signed (simplified check)
                    issuer = dict(x[0] for x in cert_info['issuer'])
                    subject = dict(x[0] for x in cert_info['subject'])
                    ssl_analysis["self_signed"] = (
                        issuer.get('commonName') == subject.get('commonName') and
                        issuer.get('organizationName') == subject.get('organizationName')
                    )
                    
                    # Certificate details
                    ssl_analysis["certificate_details"] = {
                        "subject": subject,
                        "issuer": issuer,
                        "valid_from": not_before.isoformat(),
                        "valid_until": not_after.isoformat(),
                        "days_until_expiry": (not_after - now).days,
                        "serial_number": cert_info.get('serialNumber', 'Unknown')
                    }
                
                # Cipher analysis
                if cipher_info:
                    cipher_name = cipher_info[0]
                    ssl_version = cipher_info[1]
                    cipher_bits = cipher_info[2]
                    
                    ssl_analysis["cipher_info"] = {
                        "name": cipher_name,
                        "version": ssl_version,
                        "bits": cipher_bits
                    }
                    
                    # Check for weak ciphers
                    weak_ciphers = ['RC4', 'DES', 'MD5', 'NULL']
                    ssl_analysis["weak_cipher"] = any(
                        weak in cipher_name.upper() for weak in weak_ciphers
                    )
                    
                    # Check for old SSL/TLS versions
                    if ssl_version in ['SSLv2', 'SSLv3', 'TLSv1']:
                        ssl_analysis["security_issues"].append(f"Outdated SSL/TLS version: {ssl_version}")
                
                # Calculate SSL security score
                ssl_score = 0
                
                if ssl_analysis["valid"]:
                    ssl_score += 30
                if not ssl_analysis["self_signed"]:
                    ssl_score += 20
                if cipher_info and cipher_info[2] >= 256:
                    ssl_score += 20
                elif cipher_info and cipher_info[2] >= 128:
                    ssl_score += 15
                if not ssl_analysis["expires_soon"]:
                    ssl_score += 15
                if cipher_info and cipher_info[1] in ['TLSv1.2', 'TLSv1.3']:
                    ssl_score += 15
                
                ssl_analysis["ssl_score"] = min(100, ssl_score)
                
    except ssl.SSLError as ssl_error:
        ssl_analysis["security_issues"].append(f"SSL Error: {ssl_error}")
    except socket.timeout:
        ssl_analysis["security_issues"].append("SSL connection timeout")
    except Exception as e:
        ssl_analysis["security_issues"].append(f"SSL analysis failed: {str(e)}")
    
    return ssl_analysis

# Add these functions after your existing imports and before the FastAPI app definition

def scan_url(url: str) -> Dict:
    """Enhanced URL security scanner with integrated SSL analysis"""
    
    result = {
        "https": False,
        "ssl_certificate": {},
        "headers": {},
        "flags": [],
        "security_score": 0,
        "security_level": "Unknown"
    }
    
    try:
        # Check if HTTPS is enabled
        result["https"] = url.startswith("https://")
        
        if result["https"]:
            # Perform detailed SSL certificate analysis
            ssl_analysis = analyze_ssl_certificate(url)
            result["ssl_certificate"] = ssl_analysis
            
            # Add SSL-related flags (these will affect the overall score)
            if ssl_analysis.get("expired"):
                result["flags"].append("❌ SSL certificate has expired")
            if ssl_analysis.get("self_signed"):
                result["flags"].append("⚠️ Self-signed SSL certificate detected")
            if ssl_analysis.get("weak_cipher"):
                result["flags"].append("⚠️ Weak SSL cipher suite detected")
            if ssl_analysis.get("expires_soon"):
                result["flags"].append("⚠️ SSL certificate expires within 30 days")
            
            # Add TLS version warnings
            cipher_info = ssl_analysis.get("cipher_info", {})
            if cipher_info and cipher_info.get("version") in ['SSLv2', 'SSLv3', 'TLSv1', 'TLSv1.1']:
                result["flags"].append(f"⚠️ Outdated TLS version: {cipher_info.get('version')}")
        else:
            result["flags"].append("❌ HTTPS not enabled - critical security risk")
        
        # Get website headers and content
        response = requests.get(url, timeout=10, verify=True)
        result["headers"] = dict(response.headers)
        
        # Check for security headers
        security_headers_analysis = analyze_security_headers(result["headers"])
        result["flags"].extend(security_headers_analysis["flags"])
        
        # Calculate integrated security score (includes SSL analysis)
        score = calculate_security_score(result)
        result["security_score"] = score
        result["security_level"] = get_security_level(score)
        
        return result
        
    except Exception as e:
        result["flags"].append(f"❌ Scan failed: {str(e)}")
        result["security_score"] = 0
        result["security_level"] = "Critical"
        return result
    
def analyze_security_headers(headers: Dict[str, str]) -> Dict:
    """Analyze security headers and return flags"""
    flags = []
    
    # Critical security headers
    critical_headers = {
        "Strict-Transport-Security": "Missing HSTS header - HTTPS security risk",
        "Content-Security-Policy": "Missing Content Security Policy - XSS risk",
        "X-Frame-Options": "Missing X-Frame-Options - Clickjacking risk",
        "X-Content-Type-Options": "Missing X-Content-Type-Options - MIME sniffing risk",
        "X-XSS-Protection": "Missing X-XSS-Protection header"
    }
    
    for header, message in critical_headers.items():
        if header not in headers:
            flags.append(f"⚠️ {message}")
    
    # Check for information disclosure
    disclosure_headers = ["Server", "X-Powered-By", "X-AspNet-Version"]
    for header in disclosure_headers:
        if header in headers:
            flags.append(f"ℹ️ Information disclosure: {header} header present")
    
    return {"flags": flags}

def analyze_ssl_certificate(url: str) -> Dict:
    """Comprehensive SSL certificate analysis"""
    
    ssl_analysis = {
        "valid": False,
        "expired": False,
        "self_signed": False,
        "expires_soon": False,
        "weak_cipher": False,
        "ssl_score": 0,
        "certificate_details": {},
        "cipher_info": {},
        "security_issues": []
    }
    
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        port = parsed_url.port or 443
        
        if parsed_url.scheme != "https":
            ssl_analysis["security_issues"].append("HTTPS not enabled")
            return ssl_analysis
        
        # Get SSL certificate
        context = ssl.create_default_context()
        
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert_info = ssock.getpeercert()
                cipher_info = ssock.cipher()
                
                if cert_info:
                    # Certificate validity
                    not_after = datetime.datetime.strptime(
                        cert_info['notAfter'], '%b %d %H:%M:%S %Y %Z'
                    )
                    not_before = datetime.datetime.strptime(
                        cert_info['notBefore'], '%b %d %H:%M:%S %Y %Z'
                    )
                    
                    now = datetime.datetime.utcnow()
                    
                    ssl_analysis["valid"] = not_before <= now <= not_after
                    ssl_analysis["expired"] = now > not_after
                    ssl_analysis["expires_soon"] = (not_after - now).days < 30
                    
                    # Check if self-signed (simplified check)
                    issuer = dict(x[0] for x in cert_info['issuer'])
                    subject = dict(x[0] for x in cert_info['subject'])
                    ssl_analysis["self_signed"] = (
                        issuer.get('commonName') == subject.get('commonName') and
                        issuer.get('organizationName') == subject.get('organizationName')
                    )
                    
                    # Certificate details
                    ssl_analysis["certificate_details"] = {
                        "subject": subject,
                        "issuer": issuer,
                        "valid_from": not_before.isoformat(),
                        "valid_until": not_after.isoformat(),
                        "days_until_expiry": (not_after - now).days,
                        "serial_number": cert_info.get('serialNumber', 'Unknown')
                    }
                
                # Cipher analysis
                if cipher_info:
                    cipher_name = cipher_info[0]
                    ssl_version = cipher_info[1]
                    cipher_bits = cipher_info[2]
                    
                    ssl_analysis["cipher_info"] = {
                        "name": cipher_name,
                        "version": ssl_version,
                        "bits": cipher_bits
                    }
                    
                    # Check for weak ciphers
                    weak_ciphers = ['RC4', 'DES', 'MD5', 'NULL']
                    ssl_analysis["weak_cipher"] = any(
                        weak in cipher_name.upper() for weak in weak_ciphers
                    )
                    
                    # Check for old SSL/TLS versions
                    if ssl_version in ['SSLv2', 'SSLv3', 'TLSv1']:
                        ssl_analysis["security_issues"].append(f"Outdated SSL/TLS version: {ssl_version}")
                
                # Calculate SSL security score
                ssl_score = 0
                
                if ssl_analysis["valid"]:
                    ssl_score += 30
                if not ssl_analysis["self_signed"]:
                    ssl_score += 20
                if cipher_info and cipher_info[2] >= 256:
                    ssl_score += 20
                elif cipher_info and cipher_info[2] >= 128:
                    ssl_score += 15
                if not ssl_analysis["expires_soon"]:
                    ssl_score += 15
                if cipher_info and cipher_info[1] in ['TLSv1.2', 'TLSv1.3']:
                    ssl_score += 15
                
                ssl_analysis["ssl_score"] = min(100, ssl_score)
                
    except ssl.SSLError as ssl_error:
        ssl_analysis["security_issues"].append(f"SSL Error: {ssl_error}")
    except socket.timeout:
        ssl_analysis["security_issues"].append("SSL connection timeout")
    except Exception as e:
        ssl_analysis["security_issues"].append(f"SSL analysis failed: {str(e)}")
    
    return ssl_analysis


def calculate_security_score(result: Dict) -> int:
    """Enhanced security score calculation with integrated SSL analysis"""
    
    score = 0
    
    # HTTPS and SSL Certificate Analysis (35 points total)
    if result["https"]:
        score += 10  # Base HTTPS points
        
        # SSL Certificate detailed analysis (25 additional points)
        ssl_cert = result.get("ssl_certificate", {})
        
        # Valid certificate (10 points)
        if ssl_cert.get("valid"):
            score += 10
        
        # Certificate authority trust (5 points)
        if not ssl_cert.get("self_signed"):
            score += 5
        
        # Strong cipher encryption (5 points)
        cipher_info = ssl_cert.get("cipher_info", {})
        if cipher_info:
            cipher_bits = cipher_info.get("bits", 0)
            if cipher_bits >= 256:
                score += 5
            elif cipher_bits >= 128:
                score += 3
        
        # Certificate not expiring soon (3 points)
        if not ssl_cert.get("expires_soon"):
            score += 3
        
        # Modern TLS version (2 points)
        if cipher_info and cipher_info.get("version") in ['TLSv1.2', 'TLSv1.3']:
            score += 2
    
    # Security Headers Analysis (40 points total)
    headers = result.get("headers", {})
    header_scores = {
        "Strict-Transport-Security": 12,     # HSTS is critical
        "Content-Security-Policy": 12,       # CSP prevents XSS
        "X-Frame-Options": 8,                # Prevents clickjacking
        "X-Content-Type-Options": 4,         # Prevents MIME sniffing
        "X-XSS-Protection": 4                # Basic XSS protection
    }
    
    for header, points in header_scores.items():
        if header in headers:
            score += points
    
    # Additional Security Features (15 points total)
    # Check for advanced security headers
    advanced_headers = {
        "Referrer-Policy": 3,
        "Permissions-Policy": 3,
        "Expect-CT": 2,
        "Feature-Policy": 2
    }
    
    for header, points in advanced_headers.items():
        if header in headers:
            score += points
    
    # Information Disclosure Penalties (10 points total deduction)
    disclosure_headers = ["Server", "X-Powered-By", "X-AspNet-Version", "X-Generator"]
    for header in disclosure_headers:
        if header in headers:
            score -= 2  # Deduct points for information disclosure
    
    # SSL/Security Issue Penalties
    flags = result.get("flags", [])
    for flag in flags:
        flag_lower = flag.lower()
        if "expired" in flag_lower or "invalid" in flag_lower:
            score -= 25  # Severe penalty for expired/invalid certificates
        elif "self-signed" in flag_lower:
            score -= 10  # Moderate penalty for self-signed certificates
        elif "weak" in flag_lower:
            score -= 15  # Penalty for weak encryption
        elif "missing" in flag_lower and any(critical in flag_lower for critical in ["hsts", "csp", "content-security-policy"]):
            score -= 5   # Penalty for missing critical headers
        elif "outdated" in flag_lower and "tls" in flag_lower:
            score -= 12  # Penalty for outdated TLS versions
    
    # Bonus points for excellent security implementation
    ssl_cert = result.get("ssl_certificate", {})
    if (result.get("https") and 
        ssl_cert.get("valid") and 
        not ssl_cert.get("self_signed") and
        "Strict-Transport-Security" in headers and
        "Content-Security-Policy" in headers):
        score += 5  # Bonus for comprehensive security setup
    
    # Ensure score is within valid range
    return min(100, max(0, score))

def get_security_level(score: int) -> str:
    """Convert score to security level"""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    elif score >= 40:
        return "Poor"
    else:
        return "Critical"

# Add this helper function for main.py
def _format_ssl_analysis(ssl_certificate: dict) -> str:
    """Format SSL certificate analysis for summary display"""
    if not ssl_certificate or ssl_certificate.get("error"):
        return "• ❌ SSL certificate analysis failed or HTTPS not enabled"
    
    ssl_info = []
    
    # Certificate validity
    if ssl_certificate.get("valid"):
        ssl_info.append("• ✅ SSL certificate is valid")
    else:
        ssl_info.append("• ❌ SSL certificate is invalid or expired")
    
    # Certificate details
    cert_details = ssl_certificate.get("certificate_details", {})
    if cert_details:
        days_until_expiry = cert_details.get("days_until_expiry", "Unknown")
        if isinstance(days_until_expiry, int):
            if days_until_expiry < 0:
                ssl_info.append(f"• ❌ Certificate expired {abs(days_until_expiry)} days ago")
            elif days_until_expiry < 30:
                ssl_info.append(f"• ⚠️ Certificate expires in {days_until_expiry} days")
            else:
                ssl_info.append(f"• ✅ Certificate valid for {days_until_expiry} more days")
        
        # Certificate authority
        issuer = cert_details.get("issuer", {})
        if issuer and issuer.get("commonName"):
            ssl_info.append(f"• 🏛️ Issued by: {issuer['commonName']}")
    
    # Self-signed certificate check
    if ssl_certificate.get("self_signed"):
        ssl_info.append("• ⚠️ Self-signed certificate detected")
    
    # Cipher strength
    cipher_info = ssl_certificate.get("cipher_info", {})
    if cipher_info:
        cipher_bits = cipher_info.get("bits", 0)
        if cipher_bits >= 256:
            ssl_info.append(f"• 🔒 Strong encryption: {cipher_bits}-bit")
        elif cipher_bits >= 128:
            ssl_info.append(f"• 🔐 Moderate encryption: {cipher_bits}-bit")
        else:
            ssl_info.append(f"• ⚠️ Weak encryption: {cipher_bits}-bit")
    
    # Security issues
    security_issues = ssl_certificate.get("security_issues", [])
    if security_issues:
        for issue in security_issues[:3]:  # Show top 3 issues
            ssl_info.append(f"• ⚠️ {issue}")
    
    return "\n".join(ssl_info) if ssl_info else "• ℹ️ SSL analysis completed - no major issues"



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

