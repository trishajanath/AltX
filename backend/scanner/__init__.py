# scanner/__init__.py
from .secrets_detector import scan_secrets
from .static_python import run_bandit
import requests
from urllib.parse import urlparse
import urllib3
from .file_security_scanner import scan_for_sensitive_files, scan_file_contents_for_secrets
from .file_scanner import scan_url  # Use the existing one from file_scanner.py
def scan_url(url):
    """Enhanced URL security scanner with comprehensive checks"""
    
    # Disable SSL warnings for testing
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        parsed_url = urlparse(url)
        https_enabled = parsed_url.scheme == 'https'
        
        headers_request = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, timeout=10, headers=headers_request, verify=True)
        except requests.exceptions.SSLError:
            response = requests.get(url, timeout=10, headers=headers_request, verify=False)
        
        headers = dict(response.headers)
        flags = []
        
        # HTTPS/SSL Checks
        if not https_enabled:
            flags.append("❌ HTTPS not enabled - Insecure HTTP connection")
        
        # Comprehensive Security Headers Check
        security_headers = {
            'content-security-policy': 'Vulnerable to XSS attacks',
            'x-frame-options': 'Vulnerable to clickjacking attacks',
            'x-content-type-options': 'Vulnerable to MIME sniffing attacks',
            'strict-transport-security': 'Vulnerable to protocol downgrade attacks',
            'x-xss-protection': 'Missing XSS protection header',
            'referrer-policy': 'Referrer information may be exposed',
            'permissions-policy': 'Missing permissions policy controls',
            'cross-origin-embedder-policy': 'Missing cross-origin isolation',
            'cross-origin-opener-policy': 'Missing cross-origin opener policy',
            'cross-origin-resource-policy': 'Missing cross-origin resource policy'
        }
        
        header_keys_lower = [h.lower() for h in headers.keys()]
        for header, issue in security_headers.items():
            if header not in header_keys_lower:
                flags.append(f"⚠️ Missing {header} header - {issue}")
        
        # Server Information Exposure
        if 'server' in header_keys_lower:
            server_header = headers.get('Server', '').lower()
            if any(tech in server_header for tech in ['apache', 'nginx', 'iis', 'tomcat', 'express']):
                flags.append("🚨 Server version information exposed")
        
        # X-Powered-By Header Check
        if 'x-powered-by' in header_keys_lower:
            flags.append("🚨 X-Powered-By header exposes technology stack")
        
        # Cookie Security Analysis
        cookie_headers = [h for h in headers.keys() if h.lower() == 'set-cookie']
        if cookie_headers:
            for cookie_header in cookie_headers:
                cookie_value = headers[cookie_header].lower()
                if 'secure' not in cookie_value:
                    flags.append("🍪 Cookies not marked as Secure")
                if 'httponly' not in cookie_value:
                    flags.append("🍪 Cookies not marked as HttpOnly")
                if 'samesite' not in cookie_value:
                    flags.append("🍪 Cookies missing SameSite attribute")
        
        # Content Type Security
        content_type = headers.get('Content-Type', '').lower()
        if 'text/html' in content_type and 'charset' not in content_type:
            flags.append("📄 Missing charset declaration")
        
        # Cache Control Analysis
        cache_control = headers.get('Cache-Control', '').lower()
        if 'no-cache' not in cache_control and 'no-store' not in cache_control:
            if any(sensitive in url.lower() for sensitive in ['login', 'admin', 'auth', 'password']):
                flags.append("💾 Sensitive pages may be cached")
        
        # CORS Analysis
        cors_headers = ['access-control-allow-origin', 'access-control-allow-credentials']
        cors_present = any(h in header_keys_lower for h in cors_headers)
        if cors_present:
            origin_header = headers.get('Access-Control-Allow-Origin', '')
            if origin_header == '*':
                flags.append("🌐 CORS allows all origins - potential security risk")
        
        # Calculate comprehensive security score
        base_score = 20
        https_score = 30 if https_enabled else 0
        
        # Security headers scoring (max 35 points)
        critical_headers = ['content-security-policy', 'x-frame-options', 'x-content-type-options', 'strict-transport-security']
        critical_present = len([h for h in critical_headers if h in header_keys_lower])
        headers_score = critical_present * 8
        
        additional_headers = ['x-xss-protection', 'referrer-policy']
        additional_present = len([h for h in additional_headers if h in header_keys_lower])
        headers_score += additional_present * 2
        
        # Security implementation bonus (max 15 points)
        bonus_score = 0
        if 'secure' in str(headers).lower():
            bonus_score += 5
        if response.status_code == 200:
            bonus_score += 3
        if 'httponly' in str(headers).lower():
            bonus_score += 4
        if len(flags) == 0:
            bonus_score += 3
        
        total_score = min(100, base_score + https_score + headers_score + bonus_score)
        
        # Enhanced response with detailed analysis
        return {
            "url": url,
            "https": https_enabled,
            "flags": flags,
            "headers": headers,
            "security_score": total_score,
            "security_level": "High" if total_score >= 80 else "Medium" if total_score >= 60 else "Low",
            "response_code": response.status_code,
            "total_headers": len(headers),
            "security_headers_present": critical_present + additional_present,
            "total_security_headers_checked": len(security_headers),
            "analysis_details": {
                "https_score": https_score,
                "headers_score": headers_score,
                "bonus_score": bonus_score,
                "critical_headers_present": critical_present,
                "additional_headers_present": additional_present,
                "total_issues_found": len(flags)
            }
        }
        
    except requests.exceptions.Timeout:
        return {
            "url": url,
            "https": False,
            "flags": ["🔌 Request timeout - server not responding"],
            "headers": {},
            "security_score": 0,
            "security_level": "Unknown",
            "response_code": None
        }
    except requests.exceptions.ConnectionError:
        return {
            "url": url,
            "https": False,
            "flags": ["🔌 Connection error - cannot reach server"],
            "headers": {},
            "security_score": 0,
            "security_level": "Unknown",
            "response_code": None
        }
    except Exception as e:
        return {
            "url": url,
            "https": False,
            "flags": [f"❌ Error scanning URL: {str(e)}"],
            "headers": {},
            "security_score": 0,
            "security_level": "Unknown",
            "response_code": None
        }

__all__ = ['scan_secrets', 'run_bandit', 'scan_url', 'scan_for_sensitive_files', 'scan_file_contents_for_secrets']