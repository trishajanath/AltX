"""
AI-Powered Security Scanner Service
Performs security analysis on generated applications WITHOUT requiring OWASP ZAP.
Uses Gemini AI to analyze code for security vulnerabilities.
"""

import os
import time
import json
import re
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import requests

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai not installed. Run: pip install google-generativeai")


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
    
    # Common security vulnerability patterns
    VULNERABILITY_PATTERNS = {
        "xss": {
            "patterns": [
                r'innerHTML\s*=',
                r'document\.write\(',
                r'eval\(',
                r'dangerouslySetInnerHTML',
                r'v-html\s*=',
                r'\$\{.*\}\s*(?:innerHTML|outerHTML)',
            ],
            "name": "Cross-Site Scripting (XSS)",
            "risk": "High",
            "cwe": "CWE-79",
            "owasp": "A03:2021 - Injection"
        },
        "sql_injection": {
            "patterns": [
                r'SELECT\s+.*\+.*\+',
                r'INSERT\s+INTO\s+.*\+',
                r'DELETE\s+FROM\s+.*\+',
                r'UPDATE\s+.*SET.*\+',
                r'query\s*\(\s*[\'"].*\+',
                r'execute\s*\(\s*[\'"].*\+',
            ],
            "name": "SQL Injection",
            "risk": "Critical",
            "cwe": "CWE-89",
            "owasp": "A03:2021 - Injection"
        },
        "hardcoded_secrets": {
            "patterns": [
                r'api[_-]?key\s*[=:]\s*[\'"][A-Za-z0-9]{20,}[\'"]',
                r'password\s*[=:]\s*[\'"][^\'\"]{4,}[\'"]',
                r'secret\s*[=:]\s*[\'"][^\'\"]{8,}[\'"]',
                r'token\s*[=:]\s*[\'"][A-Za-z0-9_-]{20,}[\'"]',
                r'AWS_SECRET_ACCESS_KEY\s*=',
                r'PRIVATE_KEY\s*=',
            ],
            "name": "Hardcoded Secrets",
            "risk": "Critical",
            "cwe": "CWE-798",
            "owasp": "A02:2021 - Cryptographic Failures"
        },
        "insecure_redirect": {
            "patterns": [
                r'window\.location\s*=\s*(?:req|request|params|query)',
                r'redirect\s*\(\s*(?:req|request|params|query)',
                r'location\.href\s*=\s*(?:req|request|params)',
            ],
            "name": "Open Redirect",
            "risk": "Medium",
            "cwe": "CWE-601",
            "owasp": "A01:2021 - Broken Access Control"
        },
        "insecure_cookies": {
            "patterns": [
                r'document\.cookie\s*=(?!.*(?:Secure|HttpOnly|SameSite))',
                r'setCookie\s*\((?!.*(?:secure|httpOnly))',
                r'httpOnly\s*:\s*false',
                r'secure\s*:\s*false',
            ],
            "name": "Insecure Cookie Configuration",
            "risk": "Medium",
            "cwe": "CWE-614",
            "owasp": "A05:2021 - Security Misconfiguration"
        },
        "cors_misconfiguration": {
            "patterns": [
                r'Access-Control-Allow-Origin[\'"]?\s*:\s*[\'"]?\*',
                r'cors\s*\(\s*\{\s*origin\s*:\s*[\'"]?\*',
                r'allowOrigin\s*:\s*[\'"]?\*',
            ],
            "name": "CORS Misconfiguration",
            "risk": "Medium",
            "cwe": "CWE-942",
            "owasp": "A05:2021 - Security Misconfiguration"
        },
        "prototype_pollution": {
            "patterns": [
                r'__proto__',
                r'constructor\.prototype',
                r'Object\.assign\s*\(\s*\{\}',
            ],
            "name": "Prototype Pollution",
            "risk": "High",
            "cwe": "CWE-1321",
            "owasp": "A03:2021 - Injection"
        },
        "path_traversal": {
            "patterns": [
                r'\.\./',
                r'req\.params.*(?:readFile|writeFile|unlink)',
                r'path\.join\s*\([^)]*req\.',
            ],
            "name": "Path Traversal",
            "risk": "High",
            "cwe": "CWE-22",
            "owasp": "A01:2021 - Broken Access Control"
        },
        "command_injection": {
            "patterns": [
                r'exec\s*\(\s*(?:req|request|params|query)',
                r'spawn\s*\(\s*(?:req|request|params)',
                r'os\.system\s*\(\s*(?:request|params)',
                r'subprocess\.(?:call|run|Popen)\s*\([^)]*(?:request|input)',
            ],
            "name": "Command Injection",
            "risk": "Critical",
            "cwe": "CWE-78",
            "owasp": "A03:2021 - Injection"
        },
        "insecure_deserialization": {
            "patterns": [
                r'pickle\.loads?\s*\(',
                r'yaml\.load\s*\([^)]*(?:Loader=yaml\.Loader)?[^)]*\)',
                r'JSON\.parse\s*\(\s*(?:req|request|body)',
                r'unserialize\s*\(',
            ],
            "name": "Insecure Deserialization",
            "risk": "High",
            "cwe": "CWE-502",
            "owasp": "A08:2021 - Software and Data Integrity Failures"
        },
        "missing_auth": {
            "patterns": [
                r'app\.(get|post|put|delete)\s*\([\'"][^\'"]+[\'"](?!.*(?:auth|verify|token|jwt))',
                r'router\.(get|post|put|delete)\s*\([\'"][^\'"]+[\'"](?!.*(?:auth|middleware))',
            ],
            "name": "Missing Authentication",
            "risk": "High",
            "cwe": "CWE-306",
            "owasp": "A07:2021 - Identification and Authentication Failures"
        },
        "weak_crypto": {
            "patterns": [
                r'md5\s*\(',
                r'sha1\s*\(',
                r'DES\s*\.',
                r'RC4\s*\.',
                r'Math\.random\s*\(\s*\)',
            ],
            "name": "Weak Cryptography",
            "risk": "Medium",
            "cwe": "CWE-327",
            "owasp": "A02:2021 - Cryptographic Failures"
        },
        "sensitive_data_exposure": {
            "patterns": [
                r'console\.log\s*\([^)]*(?:password|token|secret|key)',
                r'print\s*\([^)]*(?:password|token|secret|key)',
                r'logging\.(?:info|debug|error)\s*\([^)]*(?:password|secret)',
            ],
            "name": "Sensitive Data Exposure in Logs",
            "risk": "Medium",
            "cwe": "CWE-200",
            "owasp": "A02:2021 - Cryptographic Failures"
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
                        # Get surrounding context
                        start = max(0, match.start() - 50)
                        end = min(len(code), match.end() + 50)
                        context = code[start:end]
                        
                        # Get line number
                        line_num = code[:match.start()].count('\n') + 1
                        
                        alert_id += 1
                        alerts.append({
                            "alert_id": f"PATTERN-{alert_id:04d}",
                            "alert": vuln_info["name"],
                            "risk": vuln_info["risk"],
                            "confidence": "Medium",
                            "description": f"Potential {vuln_info['name']} vulnerability detected at line {line_num}",
                            "solution": f"Review and fix the code pattern that may cause {vuln_info['name']}",
                            "evidence": match.group()[:100],
                            "url": f"line:{line_num}",
                            "cwe_id": vuln_info.get("cwe", ""),
                            "owasp": vuln_info.get("owasp", ""),
                            "context": context.strip()
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
        scan_type: ScanType = ScanType.STANDARD
    ) -> ScanResult:
        """
        Scan a URL by fetching its content and analyzing it.
        
        Args:
            target_url: URL to scan (e.g., sandbox preview URL)
            scan_type: Type of scan to perform
            
        Returns:
            ScanResult with all findings
        """
        start_time = time.time()
        
        try:
            # Fetch the page content
            print(f"📡 Fetching content from: {target_url[:80]}...")
            response = requests.get(target_url, timeout=30)
            response.raise_for_status()
            
            html_content = response.text
            
            # Extract JavaScript from the HTML
            js_pattern = r'<script[^>]*>(.*?)</script>'
            js_matches = re.findall(js_pattern, html_content, re.DOTALL | re.IGNORECASE)
            js_code = "\n\n".join(js_matches)
            
            # Also check for inline event handlers
            event_pattern = r'on\w+=["\'][^"\']+["\']'
            inline_events = re.findall(event_pattern, html_content, re.IGNORECASE)
            
            all_alerts = []
            
            # Scan HTML for security issues
            print("📄 Analyzing HTML content...")
            html_alerts = self._scan_html(html_content)
            all_alerts.extend(html_alerts)
            
            # Scan JavaScript
            if js_code.strip():
                print("📜 Analyzing JavaScript content...")
                js_result = await self.scan_code(js_code, "javascript", scan_type)
                all_alerts.extend(js_result.alerts)
            
            # Check inline events
            if inline_events:
                all_alerts.append({
                    "alert_id": "HTML-001",
                    "alert": "Inline Event Handlers",
                    "risk": "Low",
                    "confidence": "High",
                    "description": f"Found {len(inline_events)} inline event handlers. These can be vectors for XSS if user input is interpolated.",
                    "solution": "Move event handlers to JavaScript files and use addEventListener() for better security and CSP compliance.",
                    "evidence": str(inline_events[:3]),
                    "url": target_url,
                    "owasp": "A03:2021 - Injection"
                })
            
            # Categorize by risk
            critical = [a for a in all_alerts if a.get('risk') == 'Critical']
            high = [a for a in all_alerts if a.get('risk') == 'High']
            medium = [a for a in all_alerts if a.get('risk') == 'Medium']
            low = [a for a in all_alerts if a.get('risk') == 'Low']
            info = [a for a in all_alerts if a.get('risk') == 'Informational']
            
            duration = time.time() - start_time
            
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
            
        except requests.exceptions.RequestException as e:
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
                error=f"Failed to fetch URL: {str(e)}"
            )
    
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
