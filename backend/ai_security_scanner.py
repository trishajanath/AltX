"""
AI-Powered Security Scanner Service
Performs security analysis on generated applications WITHOUT requiring OWASP ZAP.
Uses Gemini AI to analyze code for security vulnerabilities.

Enhanced Features:
- Comprehensive OWASP Top 10 coverage
- CWE (Common Weakness Enumeration) mapping
- Detailed remediation guidance
- Performance optimized with async operations
"""

import os
import time
import json
import re
import asyncio
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import requests
from urllib.parse import urlparse

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai not installed. Run: pip install google-generativeai")

# Thread pool for parallel operations
_executor = ThreadPoolExecutor(max_workers=4)


class ScanType(Enum):
    QUICK = "quick"          # Fast scan - basic checks
    STANDARD = "standard"    # Standard scan - comprehensive
    DEEP = "deep"            # Deep scan - thorough analysis
    OWASP = "owasp"          # OWASP Top 10 focused


class RiskLevel(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"


@dataclass
class SecurityAlert:
    """A security vulnerability finding"""
    alert_id: str
    alert_type: str
    risk: str
    confidence: str
    name: str
    description: str
    solution: str
    affected_code: str = ""
    cwe_id: str = ""
    owasp_category: str = ""
    references: List[str] = field(default_factory=list)


@dataclass
class ScanResult:
    """Result of a security scan"""
    success: bool
    target_url: str
    scan_type: str
    alerts: List[Dict[str, Any]]
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    informational_count: int
    critical_count: int
    scan_duration_seconds: float
    error: Optional[str] = None
    owasp_mapping: Optional[Dict[str, List[Dict]]] = None


class AISecurityScanner:
    """
    AI-Powered Security Scanner for analyzing generated applications.
    Uses Gemini AI to detect security vulnerabilities without requiring OWASP ZAP.
    
    Usage:
        scanner = AISecurityScanner()
        result = await scanner.scan_code(code_content, "javascript")
        # or
        result = await scanner.scan_url("http://localhost:8000/api/sandbox-preview/my-app")
    """
    
    # Comprehensive security vulnerability patterns (OWASP Top 10 + CWE coverage)
    VULNERABILITY_PATTERNS = {
        # === A03:2021 - INJECTION ===
        "xss_dom": {
            "patterns": [
                r'innerHTML\s*=',
                r'outerHTML\s*=',
                r'document\.write\s*\(',
                r'document\.writeln\s*\(',
                r'eval\s*\(',
                r'new\s+Function\s*\(',
                r'setTimeout\s*\(\s*[\'"`]',
                r'setInterval\s*\(\s*[\'"`]',
                r'dangerouslySetInnerHTML',
                r'v-html\s*=',
                r'\$\{.*\}\s*(?:innerHTML|outerHTML)',
                r'insertAdjacentHTML\s*\(',
                r'\.html\s*\(\s*[^)]*\$\{',
                r'createContextualFragment',
            ],
            "name": "DOM-based Cross-Site Scripting (XSS)",
            "risk": "High",
            "cwe": "CWE-79",
            "owasp": "A03:2021 - Injection",
            "description": "DOM XSS occurs when user input is directly used in JavaScript to modify the DOM without proper sanitization.",
            "solution": "Use textContent instead of innerHTML, sanitize user inputs with DOMPurify, implement Content Security Policy (CSP)."
        },
        "xss_reflected": {
            "patterns": [
                r'req\.query\s*\[.*\]\s*(?:.*innerHTML|.*document\.write)',
                r'req\.params\s*\[.*\]\s*(?:.*innerHTML|.*document\.write)',
                r'location\.search.*innerHTML',
                r'URL\s*\(.*\)\.searchParams.*innerHTML',
            ],
            "name": "Reflected Cross-Site Scripting (XSS)",
            "risk": "High",
            "cwe": "CWE-79",
            "owasp": "A03:2021 - Injection",
            "description": "User-controlled input from URL parameters is reflected back in the response without sanitization.",
            "solution": "Encode all user inputs before rendering, use framework auto-escaping, implement CSP headers."
        },
        "sql_injection": {
            "patterns": [
                r'SELECT\s+.*\+\s*(?:req|request|input|params)',
                r'INSERT\s+INTO\s+.*\+\s*(?:req|request|input)',
                r'DELETE\s+FROM\s+.*\+\s*(?:req|request|input)',
                r'UPDATE\s+.*SET.*\+\s*(?:req|request|input)',
                r'query\s*\(\s*[\'"`].*\$\{',
                r'execute\s*\(\s*[\'"`].*\$\{',
                r'raw\s*\(\s*[\'"`].*\$\{',
                r'f[\'"]SELECT.*{',
                r'f[\'"]INSERT.*{',
                r'f[\'"]UPDATE.*{',
                r'f[\'"]DELETE.*{',
                r'%s.*%.*(?:SELECT|INSERT|UPDATE|DELETE)',
            ],
            "name": "SQL Injection",
            "risk": "Critical",
            "cwe": "CWE-89",
            "owasp": "A03:2021 - Injection",
            "description": "SQL queries constructed with unsanitized user input can be manipulated to access or modify data.",
            "solution": "Use parameterized queries (prepared statements), ORMs with query builders, input validation with allowlists."
        },
        "nosql_injection": {
            "patterns": [
                r'\.find\s*\(\s*\{.*\$where',
                r'\.find\s*\(\s*\{.*\$regex.*req\.',
                r'collection\.find\s*\(\s*req\.',
                r'Model\.find\s*\(\s*req\.body\)',
                r'mongoose.*\{\s*\$.*:\s*req\.',
            ],
            "name": "NoSQL Injection",
            "risk": "High",
            "cwe": "CWE-943",
            "owasp": "A03:2021 - Injection",
            "description": "NoSQL databases can be exploited using operators like $where, $regex when user input is not validated.",
            "solution": "Validate and sanitize all user inputs, avoid $where operator, use schema validation."
        },
        "command_injection": {
            "patterns": [
                r'exec\s*\(\s*.*(?:req|request|params|query|input)',
                r'spawn\s*\(\s*.*(?:req|request|params)',
                r'execSync\s*\(\s*.*(?:req|request|params)',
                r'child_process.*(?:req|request|params)',
                r'os\.system\s*\(\s*.*(?:request|params|input)',
                r'os\.popen\s*\(\s*.*(?:request|params|input)',
                r'subprocess\.(?:call|run|Popen)\s*\([^)]*(?:request|input|params)',
                r'shell\s*=\s*True.*(?:request|input)',
            ],
            "name": "OS Command Injection",
            "risk": "Critical",
            "cwe": "CWE-78",
            "owasp": "A03:2021 - Injection",
            "description": "User input passed to system shell commands can lead to arbitrary command execution.",
            "solution": "Avoid shell commands with user input, use spawn with array args, validate inputs against allowlist."
        },
        "ldap_injection": {
            "patterns": [
                r'ldap\.search\s*\(.*\+.*(?:req|request|input)',
                r'ldap_search\s*\(.*\+.*(?:\$_GET|\$_POST)',
                r'\(uid=.*\+.*(?:req|request)',
            ],
            "name": "LDAP Injection",
            "risk": "High",
            "cwe": "CWE-90",
            "owasp": "A03:2021 - Injection",
            "description": "User input in LDAP queries can manipulate directory lookups.",
            "solution": "Use LDAP encoding functions, validate inputs, use parameterized LDAP queries."
        },
        "xpath_injection": {
            "patterns": [
                r'xpath\s*\(.*\+.*(?:req|request|input)',
                r'selectNodes\s*\(.*\+.*(?:req|request)',
            ],
            "name": "XPath Injection",
            "risk": "High",
            "cwe": "CWE-643",
            "owasp": "A03:2021 - Injection",
            "description": "User input in XPath queries can manipulate XML data retrieval.",
            "solution": "Use parameterized XPath queries, validate and sanitize inputs."
        },
        "template_injection": {
            "patterns": [
                r'render_template_string\s*\(\s*.*(?:request|input)',
                r'Template\s*\(\s*.*(?:request|input)',
                r'\.render\s*\(\s*.*\{\{.*(?:req|request)',
                r'Jinja2.*render.*(?:request|input)',
                r'nunjucks\.renderString\s*\(.*(?:req|request)',
            ],
            "name": "Server-Side Template Injection (SSTI)",
            "risk": "Critical",
            "cwe": "CWE-94",
            "owasp": "A03:2021 - Injection",
            "description": "User input in template engines can lead to remote code execution.",
            "solution": "Never pass user input to template rendering, use sandboxed templates, implement strict input validation."
        },
        
        # === A02:2021 - CRYPTOGRAPHIC FAILURES ===
        "hardcoded_secrets": {
            "patterns": [
                r'api[_-]?key\s*[=:]\s*[\'"`][A-Za-z0-9]{16,}[\'"`]',
                r'password\s*[=:]\s*[\'"`][^\'"]{4,}[\'"`]',
                r'secret\s*[=:]\s*[\'"`][^\'"]{8,}[\'"`]',
                r'token\s*[=:]\s*[\'"`][A-Za-z0-9_-]{20,}[\'"`]',
                r'AWS_SECRET_ACCESS_KEY\s*=\s*[\'"`]',
                r'PRIVATE_KEY\s*=\s*[\'"`]',
                r'DATABASE_URL\s*=\s*[\'"`].*:.*@',
                r'MONGO_URI\s*=\s*[\'"`]',
                r'REDIS_URL\s*=\s*[\'"`]',
                r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
                r'ghp_[A-Za-z0-9]{36}',  # GitHub token
                r'sk-[A-Za-z0-9]{32,}',  # OpenAI key
                r'AIza[A-Za-z0-9_-]{35}',  # Google API key
            ],
            "name": "Hardcoded Secrets/Credentials",
            "risk": "Critical",
            "cwe": "CWE-798",
            "owasp": "A02:2021 - Cryptographic Failures",
            "description": "Sensitive credentials embedded in source code can be extracted and misused.",
            "solution": "Use environment variables, secret managers (AWS Secrets Manager, HashiCorp Vault), .env files with .gitignore."
        },
        "weak_crypto": {
            "patterns": [
                r'md5\s*\(',
                r'MD5\s*\.',
                r'sha1\s*\(',
                r'SHA1\s*\.',
                r'createHash\s*\(\s*[\'"]md5[\'"]',
                r'createHash\s*\(\s*[\'"]sha1[\'"]',
                r'DES\s*\.',
                r'RC4\s*\.',
                r'ECB\s*mode',
                r'crypto\.createCipher\(',  # Deprecated
                r'Math\.random\s*\(\s*\)',
                r'random\.random\s*\(',
            ],
            "name": "Weak Cryptographic Algorithm",
            "risk": "Medium",
            "cwe": "CWE-327",
            "owasp": "A02:2021 - Cryptographic Failures",
            "description": "Using weak or deprecated cryptographic algorithms compromises data security.",
            "solution": "Use SHA-256/SHA-3 for hashing, AES-256-GCM for encryption, crypto.randomBytes() for random generation."
        },
        "sensitive_data_exposure": {
            "patterns": [
                r'console\.log\s*\([^)]*(?:password|token|secret|key|credit|ssn)',
                r'print\s*\([^)]*(?:password|token|secret|key|credit)',
                r'logging\.(?:info|debug|error)\s*\([^)]*(?:password|secret|token)',
                r'logger\.(?:info|debug|error)\s*\([^)]*(?:password|secret)',
                r'response\.(?:send|json)\s*\([^)]*password',
            ],
            "name": "Sensitive Data Exposure in Logs/Response",
            "risk": "Medium",
            "cwe": "CWE-200",
            "owasp": "A02:2021 - Cryptographic Failures",
            "description": "Sensitive data logged or exposed in responses can be accessed by attackers.",
            "solution": "Mask sensitive data before logging, never return passwords in API responses, use structured logging."
        },
        "http_not_https": {
            "patterns": [
                r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)',
                r'fetch\s*\(\s*[\'"]http://',
                r'axios\s*\.\s*(?:get|post)\s*\(\s*[\'"]http://',
            ],
            "name": "Insecure HTTP Usage",
            "risk": "Medium",
            "cwe": "CWE-319",
            "owasp": "A02:2021 - Cryptographic Failures",
            "description": "Data transmitted over HTTP is not encrypted and can be intercepted.",
            "solution": "Always use HTTPS for external communications, implement HSTS headers."
        },
        
        # === A01:2021 - BROKEN ACCESS CONTROL ===
        "insecure_redirect": {
            "patterns": [
                r'window\.location\s*=\s*.*(?:req|request|params|query|searchParams)',
                r'redirect\s*\(\s*.*(?:req|request|params|query)',
                r'location\.href\s*=\s*.*(?:req|request|params|query)',
                r'res\.redirect\s*\(\s*req\.',
                r'return\s+redirect\s*\(\s*request\.',
            ],
            "name": "Open Redirect Vulnerability",
            "risk": "Medium",
            "cwe": "CWE-601",
            "owasp": "A01:2021 - Broken Access Control",
            "description": "Unvalidated redirects can be exploited for phishing attacks.",
            "solution": "Validate redirect URLs against allowlist, use relative URLs, check URL domain."
        },
        "path_traversal": {
            "patterns": [
                r'\.\./',
                r'\.\.\\\\',
                r'req\.params.*(?:readFile|writeFile|unlink|readdir)',
                r'req\.query.*(?:readFile|writeFile|unlink)',
                r'path\.join\s*\([^)]*req\.',
                r'fs\.(?:read|write|access).*(?:req\.|input|params)',
                r'open\s*\(\s*.*(?:request|params|input)',
            ],
            "name": "Path Traversal",
            "risk": "High",
            "cwe": "CWE-22",
            "owasp": "A01:2021 - Broken Access Control",
            "description": "Path traversal allows attackers to access files outside the intended directory.",
            "solution": "Use path.basename(), validate against allowlist, use chroot/sandboxing."
        },
        "idor": {
            "patterns": [
                r'\.findById\s*\(\s*req\.params',
                r'\.findByPk\s*\(\s*req\.params',
                r'WHERE\s+id\s*=\s*(?:req|params)',
                r'/users/:\w+(?!.*(?:auth|verify|owner))',
                r'/api/.*/:id(?!.*(?:auth|permission))',
            ],
            "name": "Insecure Direct Object Reference (IDOR)",
            "risk": "High",
            "cwe": "CWE-639",
            "owasp": "A01:2021 - Broken Access Control",
            "description": "Direct access to objects via user-provided ID without authorization check.",
            "solution": "Implement authorization checks, verify object ownership, use indirect references."
        },
        "missing_auth": {
            "patterns": [
                r'app\.(get|post|put|delete|patch)\s*\([\'"][^\'"]+[\'"],\s*(?:async\s*)?\([^)]*\)\s*=>',
                r'router\.(get|post|put|delete|patch)\s*\([\'"][^\'"]+[\'"],\s*(?:async\s*)?\([^)]*\)\s*=>',
                r'@app\.route\s*\([\'"][^\'"]+[\'"](?:,.*?)?\)\s*\n\s*(?:async\s+)?def\s+\w+\s*\([^)]*\):(?!.*(?:login_required|jwt_required|auth))',
            ],
            "name": "Missing Authentication Check",
            "risk": "High",
            "cwe": "CWE-306",
            "owasp": "A07:2021 - Identification and Authentication Failures",
            "description": "Endpoints without authentication middleware can be accessed by anyone.",
            "solution": "Add authentication middleware, implement JWT/session validation, use role-based access control."
        },
        
        # === A05:2021 - SECURITY MISCONFIGURATION ===
        "insecure_cookies": {
            "patterns": [
                r'document\.cookie\s*=(?!.*(?:Secure|HttpOnly|SameSite))',
                r'setCookie\s*\((?!.*(?:secure|httpOnly))',
                r'httpOnly\s*:\s*false',
                r'secure\s*:\s*false',
                r'sameSite\s*:\s*[\'"]?none[\'"]?(?!.*secure)',
                r'cookie.*secure.*false',
            ],
            "name": "Insecure Cookie Configuration",
            "risk": "Medium",
            "cwe": "CWE-614",
            "owasp": "A05:2021 - Security Misconfiguration",
            "description": "Cookies without security flags are vulnerable to interception and CSRF.",
            "solution": "Set Secure, HttpOnly, and SameSite=Strict flags on all sensitive cookies."
        },
        "cors_misconfiguration": {
            "patterns": [
                r'Access-Control-Allow-Origin[\'"]?\s*:\s*[\'"]?\*',
                r'cors\s*\(\s*\{\s*origin\s*:\s*[\'"]?\*',
                r'cors\s*\(\s*\)',
                r'allowOrigin\s*:\s*[\'"]?\*',
                r'Access-Control-Allow-Credentials.*true.*Access-Control-Allow-Origin.*\*',
            ],
            "name": "CORS Misconfiguration",
            "risk": "Medium",
            "cwe": "CWE-942",
            "owasp": "A05:2021 - Security Misconfiguration",
            "description": "Overly permissive CORS allows any website to make requests to your API.",
            "solution": "Specify exact allowed origins, don't use '*' with credentials, validate Origin header."
        },
        "debug_enabled": {
            "patterns": [
                r'DEBUG\s*=\s*True',
                r'debug\s*:\s*true',
                r'app\.run\s*\([^)]*debug\s*=\s*True',
                r'NODE_ENV\s*=\s*[\'"]development[\'"]',
                r'\.debug\s*\(\s*\)',
            ],
            "name": "Debug Mode Enabled",
            "risk": "Low",
            "cwe": "CWE-489",
            "owasp": "A05:2021 - Security Misconfiguration",
            "description": "Debug mode in production exposes stack traces and internal information.",
            "solution": "Disable debug mode in production, use environment-specific configurations."
        },
        "verbose_errors": {
            "patterns": [
                r'catch\s*\([^)]*\)\s*\{[^}]*(?:res\.send|response\.write)\s*\([^)]*(?:err|error|exception)',
                r'except.*:\s*\n\s*return.*(?:str\(e\)|exception|traceback)',
                r'\.catch\s*\([^)]*\)\s*\.then\s*\([^)]*res\.json\s*\(\s*\{[^}]*error',
            ],
            "name": "Verbose Error Messages",
            "risk": "Low",
            "cwe": "CWE-209",
            "owasp": "A05:2021 - Security Misconfiguration",
            "description": "Detailed error messages can reveal system internals to attackers.",
            "solution": "Log full errors server-side, return generic error messages to clients."
        },
        
        # === A08:2021 - SOFTWARE AND DATA INTEGRITY FAILURES ===
        "prototype_pollution": {
            "patterns": [
                r'__proto__',
                r'constructor\.prototype',
                r'Object\.assign\s*\(\s*\{\}\s*,\s*(?:req|request|input)',
                r'lodash\.merge\s*\([^)]*(?:req|request|input)',
                r'deepmerge\s*\([^)]*(?:req|request|input)',
                r'\[.*\]\s*=\s*(?:req|request|input)',
            ],
            "name": "Prototype Pollution",
            "risk": "High",
            "cwe": "CWE-1321",
            "owasp": "A08:2021 - Software and Data Integrity Failures",
            "description": "Modifying object prototypes can lead to DoS or code execution.",
            "solution": "Use Object.create(null), validate keys, use Map instead of objects for user data."
        },
        "insecure_deserialization": {
            "patterns": [
                r'pickle\.loads?\s*\(',
                r'yaml\.load\s*\(\s*[^)]*(?:Loader=yaml\.Loader|Loader=None)?[^)]*\)',
                r'JSON\.parse\s*\(\s*(?:req|request|body)',
                r'unserialize\s*\(',
                r'eval\s*\(\s*JSON',
                r'marshal\.loads?\s*\(',
            ],
            "name": "Insecure Deserialization",
            "risk": "High",
            "cwe": "CWE-502",
            "owasp": "A08:2021 - Software and Data Integrity Failures",
            "description": "Deserializing untrusted data can lead to remote code execution.",
            "solution": "Use safe YAML loader (SafeLoader), validate JSON schema, avoid pickle with untrusted data."
        },
        "unsafe_regex": {
            "patterns": [
                r'new\s+RegExp\s*\(\s*(?:req|request|input|params)',
                r're\.compile\s*\(\s*(?:request|input|params)',
                r'\(\.\*\)\+',
                r'\(\.\+\)\*',
                r'\(\[.*\]\+\)\+',
            ],
            "name": "Regular Expression Denial of Service (ReDoS)",
            "risk": "Medium",
            "cwe": "CWE-1333",
            "owasp": "A08:2021 - Software and Data Integrity Failures",
            "description": "Regex with catastrophic backtracking can cause DoS.",
            "solution": "Avoid nested quantifiers, use atomic groups, limit input length, use re2 library."
        },
        
        # === A10:2021 - SSRF ===
        "ssrf": {
            "patterns": [
                r'fetch\s*\(\s*(?:req|request|params|query)',
                r'axios\s*\.\s*(?:get|post)\s*\(\s*(?:req|request|params)',
                r'requests\.(?:get|post)\s*\(\s*(?:request|params|input)',
                r'urllib\.request\.urlopen\s*\(\s*(?:request|input)',
                r'http\.get\s*\(\s*(?:req|request|params)',
                r'curl_exec\s*\(.*(?:req|request|\$_GET|\$_POST)',
            ],
            "name": "Server-Side Request Forgery (SSRF)",
            "risk": "High",
            "cwe": "CWE-918",
            "owasp": "A10:2021 - Server-Side Request Forgery",
            "description": "User-controlled URLs in server-side requests can access internal resources.",
            "solution": "Validate URLs against allowlist, block private IP ranges, use DNS rebinding protection."
        },
        
        # === ADDITIONAL SECURITY CONCERNS ===
        "jwt_issues": {
            "patterns": [
                r'algorithm\s*[=:]\s*[\'"]none[\'"]',
                r'algorithms\s*[=:]\s*\[[^\]]*[\'"]none[\'"]',
                r'verify\s*[=:]\s*false',
                r'ignoreExpiration\s*[=:]\s*true',
            ],
            "name": "Insecure JWT Configuration",
            "risk": "High",
            "cwe": "CWE-347",
            "owasp": "A07:2021 - Identification and Authentication Failures",
            "description": "JWT with 'none' algorithm or disabled verification can be forged.",
            "solution": "Always verify JWT signatures, specify allowed algorithms, check expiration."
        },
        "mass_assignment": {
            "patterns": [
                r'\.create\s*\(\s*req\.body\s*\)',
                r'\.update\s*\(\s*req\.body\s*\)',
                r'\.findOneAndUpdate\s*\([^)]*,\s*req\.body',
                r'Model\s*\(\s*\*\*request\.',
                r'Object\.assign\s*\(\s*\w+\s*,\s*req\.body',
            ],
            "name": "Mass Assignment Vulnerability",
            "risk": "High",
            "cwe": "CWE-915",
            "owasp": "A04:2021 - Insecure Design",
            "description": "Directly assigning request body to database models can modify unintended fields.",
            "solution": "Use allowlists for accepted fields, use DTOs, implement field-level access control."
        },
        "file_upload": {
            "patterns": [
                r'multer\s*\(\s*\)',
                r'upload\.(?:single|array)\s*\(',
                r'\.filename\s*=\s*(?:req|file)\.',
                r'move_uploaded_file\s*\(',
                r'FileField\s*\(\s*\)',
            ],
            "name": "Unrestricted File Upload",
            "risk": "High",
            "cwe": "CWE-434",
            "owasp": "A04:2021 - Insecure Design",
            "description": "File uploads without validation can lead to code execution or storage attacks.",
            "solution": "Validate file types (magic bytes, not extension), limit size, rename files, use separate storage."
        },
        "xml_xxe": {
            "patterns": [
                r'\.parseString\s*\(\s*(?:req|request|input)',
                r'etree\.fromstring\s*\(\s*(?:request|input)',
                r'XMLReader\s*\(\s*\)',
                r'lxml\.etree\.parse\s*\(',
                r'LIBXML_NOENT',
            ],
            "name": "XML External Entity (XXE) Injection",
            "risk": "High",
            "cwe": "CWE-611",
            "owasp": "A05:2021 - Security Misconfiguration",
            "description": "XML parsers with external entity processing can leak files or perform SSRF.",
            "solution": "Disable external entities, use defusedxml library, use JSON instead of XML."
        },
        "race_condition": {
            "patterns": [
                r'if\s*\([^)]*(?:balance|count|quantity)[^)]*\)\s*\{[^}]*(?:balance|count|quantity)\s*[-+]=',
                r'check.*then.*(?:update|modify|delete)',
                r'\.findOne\s*\([^)]*\)[^;]*\.save\s*\(',
            ],
            "name": "Race Condition (TOCTOU)",
            "risk": "Medium",
            "cwe": "CWE-367",
            "owasp": "A04:2021 - Insecure Design",
            "description": "Time-of-check to time-of-use vulnerabilities in concurrent operations.",
            "solution": "Use database transactions, atomic operations, optimistic locking."
        },
        "information_disclosure": {
            "patterns": [
                r'x-powered-by',
                r'server\s*:\s*[\'"][^\'"]+[\'"]',
                r'<!--.*(?:TODO|FIXME|password|secret|key).*-->',
                r'/\*.*(?:password|secret|key|token).*\*/',
                r'\.version\s*=',
            ],
            "name": "Information Disclosure",
            "risk": "Low",
            "cwe": "CWE-200",
            "owasp": "A05:2021 - Security Misconfiguration",
            "description": "Headers, comments, or version info can help attackers identify vulnerabilities.",
            "solution": "Remove server headers, strip comments in production, don't expose versions."
        },
        "clickjacking": {
            "patterns": [
                r'X-Frame-Options',  # Check if missing
                r'frame-ancestors',  # Check CSP
            ],
            "name": "Clickjacking Protection Check",
            "risk": "Informational",
            "cwe": "CWE-1021",
            "owasp": "A05:2021 - Security Misconfiguration",
            "description": "Without X-Frame-Options or CSP frame-ancestors, the site may be vulnerable to clickjacking.",
            "solution": "Set X-Frame-Options: DENY or use CSP frame-ancestors directive."
        }
    }
    
    # OWASP Top 10 2021 Categories
    OWASP_TOP_10 = {
        "A01:2021": "Broken Access Control",
        "A02:2021": "Cryptographic Failures",
        "A03:2021": "Injection",
        "A04:2021": "Insecure Design",
        "A05:2021": "Security Misconfiguration",
        "A06:2021": "Vulnerable and Outdated Components",
        "A07:2021": "Identification and Authentication Failures",
        "A08:2021": "Software and Data Integrity Failures",
        "A09:2021": "Security Logging and Monitoring Failures",
        "A10:2021": "Server-Side Request Forgery (SSRF)"
    }
    
    def __init__(self, gemini_api_key: str = None):
        """
        Initialize the AI Security Scanner.
        
        Args:
            gemini_api_key: Google Gemini API key (uses env var if not provided)
        """
        self.api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.model = None
        
        if GEMINI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash")
            print("✅ AI Security Scanner initialized with Gemini")
        else:
            print("⚠️ Gemini not available - using pattern-based scanning only")
    
    def _pattern_scan(self, code: str, language: str = "javascript") -> List[Dict]:
        """
        Perform pattern-based vulnerability scanning.
        
        Args:
            code: Source code to scan
            language: Programming language
            
        Returns:
            List of vulnerability findings
        """
        alerts = []
        alert_id = 0
        
        for vuln_type, vuln_info in self.VULNERABILITY_PATTERNS.items():
            for pattern in vuln_info["patterns"]:
                try:
                    matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        # Get surrounding context (more context for better understanding)
                        start = max(0, match.start() - 100)
                        end = min(len(code), match.end() + 100)
                        context = code[start:end]
                        
                        # Get line number
                        line_num = code[:match.start()].count('\n') + 1
                        
                        # Get the actual line of code
                        lines = code.split('\n')
                        actual_line = lines[line_num - 1] if line_num <= len(lines) else ""
                        
                        alert_id += 1
                        
                        # Use enriched description and solution from pattern info
                        description = vuln_info.get("description", f"Potential {vuln_info['name']} vulnerability detected.")
                        description = f"{description} Found at line {line_num}."
                        
                        solution = vuln_info.get("solution", f"Review and fix the code pattern that may cause {vuln_info['name']}")
                        
                        alerts.append({
                            "alert_id": f"PATTERN-{vuln_type.upper()[:8]}-{alert_id:04d}",
                            "alert": vuln_info["name"],
                            "risk": vuln_info["risk"],
                            "confidence": "Medium",
                            "description": description,
                            "solution": solution,
                            "evidence": match.group()[:150],
                            "url": f"line:{line_num}",
                            "cwe_id": vuln_info.get("cwe", ""),
                            "owasp": vuln_info.get("owasp", ""),
                            "context": context.strip(),
                            "line_content": actual_line.strip()[:200],
                            "source": "Pattern Analysis"
                        })
                except Exception as e:
                    continue
        
        return alerts
    
    async def _ai_scan(self, code: str, language: str = "javascript", scan_type: ScanType = ScanType.STANDARD) -> List[Dict]:
        """
        Perform AI-powered security analysis using Gemini.
        
        Args:
            code: Source code to scan
            language: Programming language
            scan_type: Type of scan to perform
            
        Returns:
            List of vulnerability findings from AI analysis
        """
        if not self.model:
            return []
        
        # Build prompt based on scan type
        depth_instructions = {
            ScanType.QUICK: "Focus on the most critical and obvious vulnerabilities only.",
            ScanType.STANDARD: "Perform a comprehensive security review covering common vulnerabilities.",
            ScanType.DEEP: "Perform an extremely thorough security audit, including subtle vulnerabilities, logic flaws, and edge cases.",
            ScanType.OWASP: "Focus specifically on OWASP Top 10 2021 vulnerabilities."
        }
        
        prompt = f"""You are a senior application security expert. Analyze the following {language} code for security vulnerabilities.

{depth_instructions.get(scan_type, depth_instructions[ScanType.STANDARD])}

**IMPORTANT**: Return ONLY a valid JSON array. No markdown, no code blocks, no explanations outside the JSON.

Each vulnerability should be an object with these fields:
- "alert_id": unique identifier (e.g., "AI-0001")
- "alert": short name of the vulnerability
- "risk": severity level ("Critical", "High", "Medium", "Low", or "Informational")
- "confidence": confidence level ("High", "Medium", "Low")
- "description": detailed description of the vulnerability and why it's dangerous
- "solution": specific remediation steps with code examples if applicable
- "evidence": the vulnerable code snippet
- "cwe_id": CWE identifier if applicable
- "owasp": OWASP Top 10 2021 category (e.g., "A03:2021 - Injection")
- "line_hint": approximate line number or location description

Look for these types of vulnerabilities:
1. Injection (SQL, NoSQL, Command, XSS)
2. Broken Authentication
3. Sensitive Data Exposure
4. Security Misconfigurations
5. Insecure Direct Object References
6. Cross-Site Request Forgery (CSRF)
7. Missing Function Level Access Control
8. Hardcoded Credentials/Secrets
9. Insecure Dependencies
10. Improper Error Handling
11. Insufficient Logging
12. Race Conditions
13. Business Logic Flaws

CODE TO ANALYZE:
```{language}
{code[:15000]}
```

Return ONLY a JSON array of findings. If no vulnerabilities found, return: []
"""
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4000
                )
            )
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])
            
            # Try to find JSON array
            if "[" in response_text:
                start = response_text.index("[")
                # Find matching bracket
                bracket_count = 0
                end = start
                for i, char in enumerate(response_text[start:], start):
                    if char == "[":
                        bracket_count += 1
                    elif char == "]":
                        bracket_count -= 1
                        if bracket_count == 0:
                            end = i + 1
                            break
                json_str = response_text[start:end]
                alerts = json.loads(json_str)
                
                # Normalize alerts
                normalized_alerts = []
                for alert in alerts:
                    normalized_alerts.append({
                        "alert_id": alert.get("alert_id", f"AI-{len(normalized_alerts)+1:04d}"),
                        "alert": alert.get("alert", "Unknown Vulnerability"),
                        "risk": alert.get("risk", "Medium"),
                        "confidence": alert.get("confidence", "Medium"),
                        "description": alert.get("description", ""),
                        "solution": alert.get("solution", ""),
                        "evidence": alert.get("evidence", "")[:200],
                        "url": f"line:{alert.get('line_hint', 'unknown')}",
                        "cwe_id": alert.get("cwe_id", ""),
                        "owasp": alert.get("owasp", ""),
                        "source": "AI Analysis"
                    })
                
                return normalized_alerts
            
            return []
            
        except Exception as e:
            print(f"❌ AI scan error: {e}")
            return []
    
    async def scan_code(
        self,
        code: str,
        language: str = "javascript",
        scan_type: ScanType = ScanType.STANDARD
    ) -> ScanResult:
        """
        Scan source code for security vulnerabilities.
        
        Args:
            code: Source code to analyze
            language: Programming language (javascript, python, etc.)
            scan_type: Type of scan to perform
            
        Returns:
            ScanResult with all findings
        """
        start_time = time.time()
        all_alerts = []
        
        print(f"🔍 Starting {scan_type.value} security scan...")
        
        # Step 1: Pattern-based scanning (fast)
        print("📊 Running pattern-based analysis...")
        pattern_alerts = self._pattern_scan(code, language)
        all_alerts.extend(pattern_alerts)
        print(f"   Found {len(pattern_alerts)} potential issues from patterns")
        
        # Step 2: AI-powered scanning (if available)
        if self.model:
            print("🤖 Running AI-powered analysis...")
            ai_alerts = await self._ai_scan(code, language, scan_type)
            
            # Deduplicate - avoid counting same issue twice
            existing_alerts = {(a.get("alert"), a.get("evidence", "")[:50]) for a in all_alerts}
            for alert in ai_alerts:
                key = (alert.get("alert"), alert.get("evidence", "")[:50])
                if key not in existing_alerts:
                    all_alerts.append(alert)
                    existing_alerts.add(key)
            
            print(f"   Found {len(ai_alerts)} issues from AI analysis")
        
        # Categorize by risk
        critical = [a for a in all_alerts if a.get('risk') == 'Critical']
        high = [a for a in all_alerts if a.get('risk') == 'High']
        medium = [a for a in all_alerts if a.get('risk') == 'Medium']
        low = [a for a in all_alerts if a.get('risk') == 'Low']
        info = [a for a in all_alerts if a.get('risk') == 'Informational']
        
        # Map to OWASP Top 10
        owasp_mapping = self._map_to_owasp(all_alerts)
        
        duration = time.time() - start_time
        
        print(f"\n📋 Scan Complete - {len(all_alerts)} total findings")
        print(f"   🔴 Critical: {len(critical)}")
        print(f"   🟠 High: {len(high)}")
        print(f"   🟡 Medium: {len(medium)}")
        print(f"   🟢 Low: {len(low)}")
        print(f"   🔵 Info: {len(info)}")
        
        return ScanResult(
            success=True,
            target_url="code_analysis",
            scan_type=scan_type.value,
            alerts=all_alerts,
            critical_count=len(critical),
            high_risk_count=len(high),
            medium_risk_count=len(medium),
            low_risk_count=len(low),
            informational_count=len(info),
            scan_duration_seconds=duration,
            owasp_mapping=owasp_mapping
        )
    
    async def scan_url(
        self,
        target_url: str,
        scan_type: ScanType = ScanType.STANDARD,
        timeout: int = 60,
        retries: int = 3
    ) -> ScanResult:
        """
        Scan a URL by fetching its content and analyzing it.
        
        Args:
            target_url: URL to scan (e.g., sandbox preview URL)
            scan_type: Type of scan to perform
            timeout: Request timeout in seconds (default: 60)
            retries: Number of retry attempts (default: 3)
            
        Returns:
            ScanResult with all findings
        """
        start_time = time.time()
        html_content = None
        last_error = None
        
        # Validate URL
        try:
            parsed = urlparse(target_url)
            if not parsed.scheme or not parsed.netloc:
                return ScanResult(
                    success=False,
                    target_url=target_url,
                    scan_type=scan_type.value,
                    alerts=[],
                    critical_count=0,
                    high_risk_count=0,
                    medium_risk_count=0,
                    low_risk_count=0,
                    informational_count=0,
                    scan_duration_seconds=time.time() - start_time,
                    error="Invalid URL format. Must include scheme (http/https) and domain."
                )
        except Exception as e:
            return ScanResult(
                success=False,
                target_url=target_url,
                scan_type=scan_type.value,
                alerts=[],
                critical_count=0,
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                informational_count=0,
                scan_duration_seconds=time.time() - start_time,
                error=f"URL parsing error: {str(e)}"
            )
        
        # Fetch with retries
        for attempt in range(retries):
            try:
                print(f"📡 Fetching content from: {target_url[:80]}... (attempt {attempt + 1}/{retries})")
                
                # Use session with better settings
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'AltX-Security-Scanner/1.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                })
                
                # Make request with progressive timeout
                current_timeout = timeout + (attempt * 15)  # Increase timeout on retries
                response = await asyncio.to_thread(
                    lambda: session.get(target_url, timeout=current_timeout, allow_redirects=True)
                )
                response.raise_for_status()
                html_content = response.text
                
                # Also capture response headers for security analysis
                response_headers = dict(response.headers)
                print(f"   ✅ Fetched {len(html_content)} bytes")
                break
                
            except requests.exceptions.Timeout as e:
                last_error = f"Request timed out after {current_timeout}s (attempt {attempt + 1})"
                print(f"   ⚠️ {last_error}")
                if attempt < retries - 1:
                    await asyncio.sleep(2)  # Wait before retry
                    
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {str(e)}"
                print(f"   ⚠️ {last_error}")
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    
            except requests.exceptions.RequestException as e:
                last_error = f"Request failed: {str(e)}"
                print(f"   ⚠️ {last_error}")
                break  # Don't retry for other errors
        
        # If we couldn't fetch the content, return error
        if html_content is None:
            return ScanResult(
                success=False,
                target_url=target_url,
                scan_type=scan_type.value,
                alerts=[],
                critical_count=0,
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                informational_count=0,
                scan_duration_seconds=time.time() - start_time,
                error=f"Failed to fetch URL after {retries} attempts: {last_error}"
            )
        
        try:
            all_alerts = []
            
            # === STEP 1: Analyze Response Headers ===
            print("🔒 Analyzing security headers...")
            header_alerts = self._scan_headers(response_headers, target_url)
            all_alerts.extend(header_alerts)
            
            # === STEP 2: Scan HTML Content ===
            print("📄 Analyzing HTML content...")
            html_alerts = self._scan_html(html_content)
            all_alerts.extend(html_alerts)
            
            # === STEP 3: Extract and Scan JavaScript ===
            js_pattern = r'<script[^>]*>(.*?)</script>'
            js_matches = re.findall(js_pattern, html_content, re.DOTALL | re.IGNORECASE)
            js_code = "\n\n".join([m for m in js_matches if m.strip() and 'src=' not in m[:50]])
            
            # Also get external script URLs
            external_scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
            
            if js_code.strip():
                print(f"📜 Analyzing {len(js_code)} chars of JavaScript...")
                js_result = await self.scan_code(js_code, "javascript", scan_type)
                all_alerts.extend(js_result.alerts)
            
            # === STEP 4: Check Inline Event Handlers ===
            event_pattern = r'on\w+=["\'][^"\']+["\']'
            inline_events = re.findall(event_pattern, html_content, re.IGNORECASE)
            
            if inline_events:
                all_alerts.append({
                    "alert_id": "HTML-EVENT-001",
                    "alert": "Inline Event Handlers Detected",
                    "risk": "Low",
                    "confidence": "High",
                    "description": f"Found {len(inline_events)} inline event handlers (onclick, onload, etc.). These can be vectors for XSS attacks if user input is interpolated and violate Content Security Policy best practices.",
                    "solution": "Move event handlers to separate JavaScript files and use addEventListener() method. This improves security, enables strict CSP, and separates concerns.",
                    "evidence": ", ".join(inline_events[:5]),
                    "url": target_url,
                    "cwe_id": "CWE-79",
                    "owasp": "A03:2021 - Injection"
                })
            
            # === STEP 5: Check External Script Sources ===
            unsafe_scripts = [s for s in external_scripts if not s.startswith(('https://', '/'))]
            if unsafe_scripts:
                all_alerts.append({
                    "alert_id": "HTML-SCRIPT-001",
                    "alert": "Insecure External Script Sources",
                    "risk": "High",
                    "confidence": "High",
                    "description": f"Found {len(unsafe_scripts)} scripts loaded over insecure connections (HTTP or protocol-relative).",
                    "solution": "Always load external scripts over HTTPS to prevent man-in-the-middle attacks.",
                    "evidence": ", ".join(unsafe_scripts[:3]),
                    "url": target_url,
                    "cwe_id": "CWE-319",
                    "owasp": "A02:2021 - Cryptographic Failures"
                })
            
            # === STEP 6: Check for Common Libraries with Known Vulnerabilities ===
            vulnerable_libs = self._check_vulnerable_libraries(html_content, external_scripts)
            all_alerts.extend(vulnerable_libs)
            
            # === STEP 7: Check Forms and Inputs ===
            form_alerts = self._scan_forms(html_content, target_url)
            all_alerts.extend(form_alerts)
            
            # Deduplicate alerts
            seen_alerts = set()
            unique_alerts = []
            for alert in all_alerts:
                key = (alert.get("alert"), alert.get("evidence", "")[:50])
                if key not in seen_alerts:
                    seen_alerts.add(key)
                    unique_alerts.append(alert)
            
            all_alerts = unique_alerts
            
            # Categorize by risk
            critical = [a for a in all_alerts if a.get('risk') == 'Critical']
            high = [a for a in all_alerts if a.get('risk') == 'High']
            medium = [a for a in all_alerts if a.get('risk') == 'Medium']
            low = [a for a in all_alerts if a.get('risk') == 'Low']
            info = [a for a in all_alerts if a.get('risk') == 'Informational']
            
            duration = time.time() - start_time
            
            print(f"\n📋 URL Scan Complete - {len(all_alerts)} findings")
            print(f"   🔴 Critical: {len(critical)}")
            print(f"   🟠 High: {len(high)}")
            print(f"   🟡 Medium: {len(medium)}")
            print(f"   🟢 Low: {len(low)}")
            print(f"   🔵 Info: {len(info)}")
            
            return ScanResult(
                success=True,
                target_url=target_url,
                scan_type=scan_type.value,
                alerts=all_alerts,
                critical_count=len(critical),
                high_risk_count=len(high),
                medium_risk_count=len(medium),
                low_risk_count=len(low),
                informational_count=len(info),
                scan_duration_seconds=duration,
                owasp_mapping=self._map_to_owasp(all_alerts)
            )
            
        except Exception as e:
            import traceback
            return ScanResult(
                success=False,
                target_url=target_url,
                scan_type=scan_type.value,
                alerts=[],
                critical_count=0,
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                informational_count=0,
                scan_duration_seconds=time.time() - start_time,
                error=f"Scan analysis error: {str(e)}\n{traceback.format_exc()}"
            )
    
    def _scan_headers(self, headers: Dict[str, str], url: str) -> List[Dict]:
        """Scan HTTP response headers for security issues."""
        alerts = []
        headers_lower = {k.lower(): v for k, v in headers.items()}
        
        # Check for missing security headers
        security_headers = {
            'x-content-type-options': {
                'expected': 'nosniff',
                'risk': 'Low',
                'description': 'Prevents browsers from MIME-sniffing responses, reducing drive-by download attacks.',
                'solution': 'Add header: X-Content-Type-Options: nosniff'
            },
            'x-frame-options': {
                'expected': ['DENY', 'SAMEORIGIN'],
                'risk': 'Medium',
                'description': 'Protects against clickjacking attacks by controlling iframe embedding.',
                'solution': 'Add header: X-Frame-Options: DENY or SAMEORIGIN'
            },
            'x-xss-protection': {
                'expected': '1; mode=block',
                'risk': 'Low',
                'description': 'Enables browser XSS filter (legacy protection for older browsers).',
                'solution': 'Add header: X-XSS-Protection: 1; mode=block'
            },
            'strict-transport-security': {
                'expected': 'max-age=',
                'risk': 'Medium',
                'description': 'HSTS forces browsers to use HTTPS, preventing protocol downgrade attacks.',
                'solution': 'Add header: Strict-Transport-Security: max-age=31536000; includeSubDomains'
            },
            'content-security-policy': {
                'expected': None,  # Just check existence
                'risk': 'Medium',
                'description': 'CSP prevents XSS by controlling which scripts can execute.',
                'solution': "Add CSP header with script-src 'self' at minimum."
            },
            'referrer-policy': {
                'expected': None,
                'risk': 'Low',
                'description': 'Controls how much referrer information is sent with requests.',
                'solution': 'Add header: Referrer-Policy: strict-origin-when-cross-origin'
            },
            'permissions-policy': {
                'expected': None,
                'risk': 'Low', 
                'description': 'Controls access to browser features like camera, microphone, geolocation.',
                'solution': 'Add Permissions-Policy header to restrict browser feature access.'
            }
        }
        
        for header, config in security_headers.items():
            header_value = headers_lower.get(header)
            
            if not header_value:
                alerts.append({
                    "alert_id": f"HDR-{header.upper().replace('-', '')[:8]}-001",
                    "alert": f"Missing Security Header: {header.title()}",
                    "risk": config['risk'],
                    "confidence": "High",
                    "description": config['description'],
                    "solution": config['solution'],
                    "evidence": f"Header '{header}' not present in response",
                    "url": url,
                    "cwe_id": "CWE-693",
                    "owasp": "A05:2021 - Security Misconfiguration"
                })
        
        # Check for insecure headers
        if 'server' in headers_lower:
            server_val = headers_lower['server']
            if any(v in server_val.lower() for v in ['apache', 'nginx', 'iis', 'php']):
                alerts.append({
                    "alert_id": "HDR-SERVER-001",
                    "alert": "Server Version Information Disclosure",
                    "risk": "Low",
                    "confidence": "High",
                    "description": f"Server header reveals technology: {server_val}. This helps attackers identify potential vulnerabilities.",
                    "solution": "Remove or obfuscate the Server header in production.",
                    "evidence": f"Server: {server_val}",
                    "url": url,
                    "cwe_id": "CWE-200",
                    "owasp": "A05:2021 - Security Misconfiguration"
                })
        
        if 'x-powered-by' in headers_lower:
            alerts.append({
                "alert_id": "HDR-XPOWERED-001",
                "alert": "Technology Stack Disclosure",
                "risk": "Low",
                "confidence": "High",
                "description": f"X-Powered-By header reveals: {headers_lower['x-powered-by']}",
                "solution": "Remove the X-Powered-By header in production.",
                "evidence": f"X-Powered-By: {headers_lower['x-powered-by']}",
                "url": url,
                "cwe_id": "CWE-200",
                "owasp": "A05:2021 - Security Misconfiguration"
            })
        
        # Check for insecure cookie settings
        if 'set-cookie' in headers_lower:
            cookies = headers_lower['set-cookie']
            if 'secure' not in cookies.lower():
                alerts.append({
                    "alert_id": "HDR-COOKIE-001",
                    "alert": "Cookie Without Secure Flag",
                    "risk": "Medium",
                    "confidence": "High",
                    "description": "Cookie set without 'Secure' flag can be transmitted over HTTP.",
                    "solution": "Add 'Secure' flag to all cookies.",
                    "evidence": f"Set-Cookie: {cookies[:100]}...",
                    "url": url,
                    "cwe_id": "CWE-614",
                    "owasp": "A05:2021 - Security Misconfiguration"
                })
            if 'httponly' not in cookies.lower():
                alerts.append({
                    "alert_id": "HDR-COOKIE-002",
                    "alert": "Cookie Without HttpOnly Flag",
                    "risk": "Medium",
                    "confidence": "High",
                    "description": "Cookie without 'HttpOnly' flag is accessible via JavaScript, enabling XSS cookie theft.",
                    "solution": "Add 'HttpOnly' flag to sensitive cookies.",
                    "evidence": f"Set-Cookie: {cookies[:100]}...",
                    "url": url,
                    "cwe_id": "CWE-1004",
                    "owasp": "A05:2021 - Security Misconfiguration"
                })
        
        return alerts
    
    def _check_vulnerable_libraries(self, html: str, scripts: List[str]) -> List[Dict]:
        """Check for known vulnerable JavaScript libraries."""
        alerts = []
        
        # Known vulnerable library patterns (version detection)
        vulnerable_libs = {
            'jquery': {
                'pattern': r'jquery[.-]?([\d.]+)',
                'vulnerable_versions': ['1.', '2.', '3.0', '3.1', '3.2', '3.3', '3.4.0'],
                'cve': 'CVE-2020-11022',
                'description': 'jQuery versions < 3.5.0 are vulnerable to XSS via html() function.'
            },
            'angular': {
                'pattern': r'angular(?:\.min)?\.js[^"\']*[\'"](1\.[0-5])',
                'vulnerable_versions': ['1.0', '1.1', '1.2', '1.3', '1.4', '1.5'],
                'cve': 'Multiple CVEs',
                'description': 'AngularJS 1.x has multiple known XSS vulnerabilities.'
            },
            'lodash': {
                'pattern': r'lodash[.-]?([\d.]+)',
                'vulnerable_versions': ['4.17.0', '4.17.1', '4.17.2', '4.17.3', '4.17.4', '4.17.10', '4.17.11'],
                'cve': 'CVE-2019-10744',
                'description': 'Lodash < 4.17.12 is vulnerable to prototype pollution.'
            },
            'bootstrap': {
                'pattern': r'bootstrap[.-]?([\d.]+)',
                'vulnerable_versions': ['3.', '4.0', '4.1', '4.2', '4.3.0'],
                'cve': 'CVE-2019-8331',
                'description': 'Bootstrap < 4.3.1 has XSS vulnerabilities in data attributes.'
            },
            'moment': {
                'pattern': r'moment(?:\.min)?\.js',
                'vulnerable_versions': ['all'],
                'cve': 'CVE-2017-18214',
                'description': 'Moment.js is deprecated and has ReDoS vulnerabilities. Use date-fns or dayjs instead.'
            }
        }
        
        combined_content = html + ' ' + ' '.join(scripts)
        
        for lib_name, lib_info in vulnerable_libs.items():
            match = re.search(lib_info['pattern'], combined_content, re.IGNORECASE)
            if match:
                version = match.group(1) if match.lastindex else 'unknown'
                is_vulnerable = any(version.startswith(v) for v in lib_info['vulnerable_versions']) or lib_info['vulnerable_versions'] == ['all']
                
                if is_vulnerable:
                    alerts.append({
                        "alert_id": f"LIB-{lib_name.upper()}-001",
                        "alert": f"Vulnerable Library: {lib_name.title()}",
                        "risk": "Medium",
                        "confidence": "Medium",
                        "description": f"{lib_info['description']} Detected version: {version}",
                        "solution": f"Update {lib_name} to the latest patched version.",
                        "evidence": f"{lib_name} version {version}",
                        "cwe_id": "CWE-1035",
                        "owasp": "A06:2021 - Vulnerable and Outdated Components",
                        "references": [lib_info['cve']]
                    })
        
        return alerts
    
    def _scan_forms(self, html: str, url: str) -> List[Dict]:
        """Scan HTML forms for security issues."""
        alerts = []
        
        forms = re.findall(r'<form[^>]*>.*?</form>', html, re.DOTALL | re.IGNORECASE)
        
        for i, form in enumerate(forms):
            form_lower = form.lower()
            
            # Check for POST forms without CSRF tokens
            if ('method="post"' in form_lower or "method='post'" in form_lower):
                has_csrf = any(token in form_lower for token in ['csrf', '_token', 'authenticity_token', 'xsrf'])
                if not has_csrf:
                    alerts.append({
                        "alert_id": f"FORM-CSRF-{i+1:03d}",
                        "alert": "POST Form Missing CSRF Protection",
                        "risk": "Medium",
                        "confidence": "Medium",
                        "description": "POST form without CSRF token is vulnerable to Cross-Site Request Forgery attacks.",
                        "solution": "Add a CSRF token hidden field to all POST forms and validate on the server.",
                        "evidence": form[:200] + "...",
                        "url": url,
                        "cwe_id": "CWE-352",
                        "owasp": "A01:2021 - Broken Access Control"
                    })
            
            # Check for forms submitting to HTTP
            action_match = re.search(r'action=["\']?(http://[^"\'\s>]+)', form, re.IGNORECASE)
            if action_match:
                alerts.append({
                    "alert_id": f"FORM-HTTP-{i+1:03d}",
                    "alert": "Form Submits to HTTP Endpoint",
                    "risk": "High",
                    "confidence": "High",
                    "description": f"Form submits data to insecure HTTP URL: {action_match.group(1)}",
                    "solution": "Change form action to use HTTPS.",
                    "evidence": action_match.group(0),
                    "url": url,
                    "cwe_id": "CWE-319",
                    "owasp": "A02:2021 - Cryptographic Failures"
                })
            
            # Check for password fields with autocomplete
            if 'type="password"' in form_lower or "type='password'" in form_lower:
                if 'autocomplete="new-password"' not in form_lower and 'autocomplete="off"' not in form_lower:
                    alerts.append({
                        "alert_id": f"FORM-PWD-{i+1:03d}",
                        "alert": "Password Field Without Autocomplete Control",
                        "risk": "Low",
                        "confidence": "High",
                        "description": "Password field may be saved by browser autocomplete.",
                        "solution": "Add autocomplete='new-password' or autocomplete='off' to password fields.",
                        "evidence": "Password input without autocomplete attribute",
                        "url": url,
                        "cwe_id": "CWE-522",
                        "owasp": "A07:2021 - Identification and Authentication Failures"
                    })
        
        return alerts
    
    def _scan_html(self, html: str) -> List[Dict]:
        """Scan HTML for common security issues."""
        alerts = []
        
        # Check for missing security headers indicators
        if '<meta http-equiv="Content-Security-Policy"' not in html:
            alerts.append({
                "alert_id": "HTML-CSP-001",
                "alert": "Missing Content Security Policy",
                "risk": "Medium",
                "confidence": "High",
                "description": "No Content Security Policy meta tag found. CSP helps prevent XSS and data injection attacks.",
                "solution": "Add a CSP meta tag or configure CSP headers on the server.",
                "evidence": "No CSP meta tag in HTML",
                "owasp": "A05:2021 - Security Misconfiguration"
            })
        
        # Check for autocomplete on sensitive fields
        sensitive_autocomplete = re.findall(r'<input[^>]*type=["\']?password[^>]*(?!autocomplete=["\']?off)', html, re.IGNORECASE)
        if sensitive_autocomplete:
            alerts.append({
                "alert_id": "HTML-AUTO-001",
                "alert": "Password Autocomplete Enabled",
                "risk": "Low",
                "confidence": "High",
                "description": "Password fields without autocomplete='off' may allow browsers to store sensitive credentials.",
                "solution": "Add autocomplete='off' to password input fields.",
                "evidence": str(sensitive_autocomplete[:1]),
                "owasp": "A02:2021 - Cryptographic Failures"
            })
        
        # Check for forms without CSRF tokens
        forms = re.findall(r'<form[^>]*>.*?</form>', html, re.DOTALL | re.IGNORECASE)
        for form in forms:
            if 'csrf' not in form.lower() and '_token' not in form.lower():
                if 'method="post"' in form.lower() or "method='post'" in form.lower():
                    alerts.append({
                        "alert_id": "HTML-CSRF-001",
                        "alert": "Missing CSRF Token",
                        "risk": "Medium",
                        "confidence": "Medium",
                        "description": "POST form without apparent CSRF protection token.",
                        "solution": "Include a CSRF token in all state-changing forms.",
                        "evidence": form[:200],
                        "owasp": "A01:2021 - Broken Access Control"
                    })
                    break  # Only report once
        
        # Check for target="_blank" without rel="noopener"
        unsafe_links = re.findall(r'<a[^>]*target=["\']?_blank[^>]*(?!rel=["\']?noopener)', html, re.IGNORECASE)
        if unsafe_links:
            alerts.append({
                "alert_id": "HTML-LINK-001",
                "alert": "Unsafe External Links",
                "risk": "Low",
                "confidence": "High",
                "description": f"Found {len(unsafe_links)} links with target='_blank' without rel='noopener'. This can allow tab-nabbing attacks.",
                "solution": "Add rel='noopener noreferrer' to all links with target='_blank'.",
                "evidence": str(unsafe_links[:2]),
                "owasp": "A05:2021 - Security Misconfiguration"
            })
        
        return alerts
    
    def _map_to_owasp(self, alerts: List[Dict]) -> Dict[str, List[Dict]]:
        """Map alerts to OWASP Top 10 2021 categories."""
        mapping = {cat: [] for cat in self.OWASP_TOP_10.keys()}
        
        for alert in alerts:
            owasp = alert.get("owasp", "")
            for cat_id in self.OWASP_TOP_10.keys():
                if cat_id in owasp:
                    mapping[cat_id].append(alert)
                    break
        
        # Remove empty categories
        return {k: v for k, v in mapping.items() if v}
    
    def generate_report(self, result: ScanResult) -> str:
        """Generate a human-readable security report."""
        report = []
        report.append("=" * 70)
        report.append("🛡️  AI-POWERED SECURITY SCAN REPORT")
        report.append("=" * 70)
        report.append(f"\n📍 Target: {result.target_url}")
        report.append(f"📋 Scan Type: {result.scan_type}")
        report.append(f"⏱️  Duration: {result.scan_duration_seconds:.2f} seconds")
        report.append(f"✅ Status: {'Success' if result.success else 'Failed'}")
        
        if result.error:
            report.append(f"\n❌ Error: {result.error}")
        
        report.append("\n" + "-" * 50)
        report.append("📊 RISK SUMMARY")
        report.append("-" * 50)
        report.append(f"⚫ Critical:      {result.critical_count}")
        report.append(f"🔴 High:          {result.high_risk_count}")
        report.append(f"🟠 Medium:        {result.medium_risk_count}")
        report.append(f"🟡 Low:           {result.low_risk_count}")
        report.append(f"🔵 Informational: {result.informational_count}")
        report.append(f"📈 Total Findings: {len(result.alerts)}")
        
        # OWASP Top 10 Mapping
        if result.owasp_mapping:
            report.append("\n" + "-" * 50)
            report.append("🎯 OWASP TOP 10 2021 MAPPING")
            report.append("-" * 50)
            for cat_id, alerts in result.owasp_mapping.items():
                cat_name = self.OWASP_TOP_10.get(cat_id, "Unknown")
                report.append(f"\n{cat_id}: {cat_name}")
                report.append(f"   Issues found: {len(alerts)}")
        
        # Detailed Alerts
        if result.alerts:
            report.append("\n" + "-" * 50)
            report.append("🚨 DETAILED FINDINGS")
            report.append("-" * 50)
            
            for risk_level in ['Critical', 'High', 'Medium', 'Low', 'Informational']:
                risk_emoji = {'Critical': '⚫', 'High': '🔴', 'Medium': '🟠', 'Low': '🟡', 'Informational': '🔵'}
                risk_alerts = [a for a in result.alerts if a.get('risk') == risk_level]
                
                if risk_alerts:
                    report.append(f"\n{risk_emoji.get(risk_level, '•')} {risk_level.upper()} RISK ({len(risk_alerts)} issues):")
                    report.append("=" * 40)
                    
                    for i, alert in enumerate(risk_alerts[:10], 1):  # Limit to 10 per category
                        report.append(f"\n  [{i}] {alert.get('alert', 'Unknown')}")
                        report.append(f"      Confidence: {alert.get('confidence', 'N/A')}")
                        if alert.get('cwe_id'):
                            report.append(f"      CWE: {alert.get('cwe_id')}")
                        if alert.get('owasp'):
                            report.append(f"      OWASP: {alert.get('owasp')}")
                        if alert.get('description'):
                            desc = alert.get('description', '')[:200]
                            report.append(f"      Description: {desc}...")
                        if alert.get('solution'):
                            sol = alert.get('solution', '')[:150]
                            report.append(f"      Solution: {sol}...")
        
        report.append("\n" + "=" * 70)
        report.append("Report generated by AI Security Scanner (No ZAP Required)")
        report.append("=" * 70)
        
        return "\n".join(report)


# Synchronous wrapper for non-async contexts
def scan_code_sync(code: str, language: str = "javascript", scan_type: str = "standard") -> Dict:
    """Synchronous wrapper for code scanning."""
    scanner = AISecurityScanner()
    scan_type_enum = ScanType(scan_type) if scan_type in [e.value for e in ScanType] else ScanType.STANDARD
    
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(scanner.scan_code(code, language, scan_type_enum))
        return {
            "success": result.success,
            "scan_type": result.scan_type,
            "duration_seconds": result.scan_duration_seconds,
            "summary": {
                "critical": result.critical_count,
                "high_risk": result.high_risk_count,
                "medium_risk": result.medium_risk_count,
                "low_risk": result.low_risk_count,
                "informational": result.informational_count,
                "total_alerts": len(result.alerts)
            },
            "alerts": result.alerts,
            "owasp_mapping": result.owasp_mapping,
            "report": scanner.generate_report(result)
        }
    finally:
        loop.close()


# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Test code with various vulnerabilities
    test_code = '''
    // Example vulnerable code
    const userInput = req.query.search;
    
    // XSS vulnerability
    document.getElementById("result").innerHTML = userInput;
    
    // SQL Injection
    const query = "SELECT * FROM users WHERE name = '" + userInput + "'";
    
    // Hardcoded secret
    const API_KEY = "sk-1234567890abcdefghijklmnop";
    
    // Weak crypto
    const hash = md5(password);
    
    // Command injection
    exec("ls " + req.params.dir);
    
    // Open redirect
    window.location = req.query.redirect;
    
    // Sensitive data logging
    console.log("User password: " + password);
    '''
    
    async def main():
        scanner = AISecurityScanner()
        result = await scanner.scan_code(test_code, "javascript", ScanType.STANDARD)
        print(scanner.generate_report(result))
    
    asyncio.run(main())
