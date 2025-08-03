from typing import Dict, List, Optional
import time
class OWASPMapper:
    def __init__(self):
        # Define keywords that map to each OWASP category
        self.owasp_mappings = {
            "A01:2021 - Broken Access Control": {
                "keywords": [
                    "admin", "dashboard", "panel", "management", "config", "directory traversal",
                    "path traversal", "unauthorized access", "access control", "privilege escalation"
                ]
            },
            "A02:2021 - Cryptographic Failures": {
                "keywords": [
                    "https", "ssl", "tls", "encryption", "crypto", "md5", "sha1", "weak cipher",
                    "strict-transport-security", "hsts", "dnssec", "certificate"
                ]
            },
            "A03:2021 - Injection": {
                "keywords": [
                    "sql injection", "xss", "cross-site scripting", "command injection", 
                    "ldap injection", "nosql injection", "content-security-policy", "csp",
                    "script injection", "code injection", "waf"
                ]
            },
            "A04:2021 - Insecure Design": {
                "keywords": [
                    "rate limiting", "authentication pattern", "authorization pattern",
                    "security design", "threat modeling", "secure architecture"
                ]
            },
            "A05:2021 - Security Misconfiguration": {
                "keywords": [
                    "security header", "x-frame-options", "x-content-type-options", 
                    "referrer-policy", "information disclosure", ".git", ".env", "phpinfo",
                    "default configuration", "misconfiguration", "exposed files", "missing"
                ]
            },
            "A06:2021 - Vulnerable and Outdated Components": {
                "keywords": [
                    "vulnerable dependencies", "outdated packages", "vulnerable packages",
                    "cve", "security update", "patch", "version disclosure", "server header"
                ]
            },
            "A07:2021 - Identification and Authentication Failures": {
                "keywords": [
                    "authentication", "login", "signin", "password", "session", "auth",
                    "brute force", "weak password", "authentication bypass", "credential"
                ]
            },
            "A08:2021 - Software and Data Integrity Failures": {
                "keywords": [
                    "integrity", "checksum", "signature", "tampering", "unsafe-inline",
                    "unsafe-eval", "code integrity", "data integrity"
                ]
            },
            "A09:2021 - Security Logging and Monitoring Failures": {
                "keywords": [
                    "logging", "monitoring", "audit", "security log", "error handling",
                    "incident detection", "forensics", "alerting"
                ]
            },
            "A10:2021 - Server-Side Request Forgery (SSRF)": {
                "keywords": [
                    "ssrf", "server-side request", "url fetch", "remote file inclusion",
                    "internal service access", "localhost access"
                ]
            }
        }

    def map_issues_to_owasp(self, scan_results: Dict, repo_results: Optional[Dict] = None) -> Dict:
        """
        Map detected security issues to OWASP Top 10 categories
        """
        owasp_categories = {}
        
        # Initialize all categories
        for category in self.owasp_mappings.keys():
            owasp_categories[category] = {
                "issues": [],
                "count": 0,
                "sources": []
            }
        
        # Process scan results
        if scan_results:
            self._process_scan_results(scan_results, owasp_categories)
        
        # Process repository results
        if repo_results:
            self._process_repo_results(repo_results, owasp_categories)
        
        # Calculate summary
        summary = self._calculate_summary(owasp_categories)
        
        return {
            "owasp_mapping": owasp_categories,
            "summary": summary
        }

    def _process_scan_results(self, scan_results: Dict, owasp_categories: Dict):
        """Process security issues from /scan endpoint - FIXED to match your data structure"""
        
        # Process scan_result data (the actual scan data)
        scan_result = scan_results.get('scan_result', {})
        
        # Check HTTPS
        if not scan_result.get('https', True):
            self._add_issue(owasp_categories, "HTTPS not enabled", "scan", "A02:2021 - Cryptographic Failures")
        
        # Process security headers
        headers = scan_result.get('headers', {})
        
        header_mappings = {
            'content-security-policy': "A03:2021 - Injection",
            'x-frame-options': "A05:2021 - Security Misconfiguration",
            'x-content-type-options': "A05:2021 - Security Misconfiguration",
            'strict-transport-security': "A02:2021 - Cryptographic Failures",
            'referrer-policy': "A05:2021 - Security Misconfiguration"
        }
        
        for header, category in header_mappings.items():
            if header not in headers:
                self._add_issue(owasp_categories, f"Missing {header} header", "scan", category)

        # Process security flags/vulnerabilities
        flags = scan_result.get('flags', [])
        for flag in flags:
            self._categorize_vulnerability(owasp_categories, flag, "scan")

        # Process exposed paths (accessible paths from scan)
        exposed_paths = scan_results.get('exposed_paths', [])
        
        for path_info in exposed_paths:
            path = path_info.get('path', '').lower()
            
            # Check for admin paths
            if any(admin_term in path for admin_term in ['admin', 'dashboard', 'panel', 'management']):
                self._add_issue(owasp_categories, f"Administrative path accessible: {path}", "scan", "A01:2021 - Broken Access Control")
            
            # Check for sensitive files
            if any(sensitive in path for sensitive in ['.git', '.env', 'config', 'backup']):
                self._add_issue(owasp_categories, f"Sensitive file accessible: {path}", "scan", "A05:2021 - Security Misconfiguration")
            
            # Check for auth paths
            if any(auth_term in path for auth_term in ['login', 'signin', 'auth']):
                self._add_issue(owasp_categories, f"Authentication endpoint exposed: {path}", "scan", "A07:2021 - Identification and Authentication Failures")

        # Process WAF analysis
        waf_analysis = scan_results.get('waf_analysis', {})
        if not waf_analysis.get('waf_detected', False):
            self._add_issue(owasp_categories, "No Web Application Firewall detected", "scan", "A03:2021 - Injection")

        # Process DNS security
        dns_security = scan_results.get('dns_security', {})
        
        # Check DNSSEC
        dnssec = dns_security.get('dnssec', {})
        if not dnssec.get('enabled', False):
            self._add_issue(owasp_categories, "DNSSEC not enabled", "scan", "A02:2021 - Cryptographic Failures")
        
        # Check DMARC
        dmarc = dns_security.get('dmarc', {})
        if not dmarc.get('enabled', False):
            self._add_issue(owasp_categories, "DMARC not configured", "scan", "A02:2021 - Cryptographic Failures")

    def _process_repo_results(self, repo_results: Dict, owasp_categories: Dict):
        """Process security issues from /analyze-repo endpoint - FIXED to match your data structure"""
        
        # Process dependency scan results
        dependency_scan = repo_results.get('dependency_scan_results', {})
        vulnerable_packages = dependency_scan.get('vulnerable_packages', [])
        
        for package in vulnerable_packages:
            package_name = package.get('package', package.get('name', 'Unknown package'))
            self._add_issue(owasp_categories, f"Vulnerable dependency: {package_name}", "repo", "A06:2021 - Vulnerable and Outdated Components")

        # Process secret scan results
        secret_scan_results = repo_results.get('secret_scan_results', [])
        for secret in secret_scan_results:
            secret_type = secret.get('secret_type', 'Unknown secret')
            file_name = secret.get('file', 'Unknown file')
            self._add_issue(owasp_categories, f"Hardcoded secret found: {secret_type} in {file_name}", "repo", "A02:2021 - Cryptographic Failures")

        # Process static analysis results
        static_analysis = repo_results.get('static_analysis_results', [])
        for issue in static_analysis:
            issue_text = str(issue)
            self._categorize_vulnerability(owasp_categories, issue_text, "repo")

        # Process code quality results
        code_quality = repo_results.get('code_quality_results', [])
        for issue in code_quality:
            issue_desc = issue.get('description', issue.get('pattern', 'Code quality issue'))
            file_name = issue.get('file', 'Unknown file')
            issue_text = f"{issue_desc} in {file_name}"
            self._categorize_vulnerability(owasp_categories, issue_text, "repo")

        # Process file security scan
        file_security = repo_results.get('file_security_scan', {})
        
        # Sensitive files
        sensitive_files = file_security.get('sensitive_files', [])
        for file_info in sensitive_files:
            file_name = file_info.get('file', 'Unknown file')
            risk = file_info.get('risk', 'Unknown')
            self._add_issue(owasp_categories, f"Sensitive file detected: {file_name} ({risk} risk)", "repo", "A05:2021 - Security Misconfiguration")

        # Missing security files
        missing_files = file_security.get('missing_security_files', [])
        for missing_file in missing_files:
            self._add_issue(owasp_categories, f"Missing security file: {missing_file}", "repo", "A05:2021 - Security Misconfiguration")

    def _categorize_vulnerability(self, owasp_categories: Dict, vuln_text: str, source: str):
        """Categorize a vulnerability based on keywords"""
        vuln_lower = vuln_text.lower()
        
        # Check each OWASP category for keyword matches
        for category, mapping in self.owasp_mappings.items():
            for keyword in mapping['keywords']:
                if keyword.lower() in vuln_lower:
                    self._add_issue(owasp_categories, vuln_text, source, category)
                    return  # Stop at first match
        
        # If no specific category found, add to misconfiguration as default
        self._add_issue(owasp_categories, vuln_text, source, "A05:2021 - Security Misconfiguration")

    def _add_issue(self, owasp_categories: Dict, issue: str, source: str, category: str):
        """Add an issue to the appropriate OWASP category"""
        if category in owasp_categories:
            owasp_categories[category]['issues'].append({
                "description": issue,
                "source": source
            })
            owasp_categories[category]['count'] += 1
            if source not in owasp_categories[category]['sources']:
                owasp_categories[category]['sources'].append(source)

    def _calculate_summary(self, owasp_categories: Dict) -> Dict:
        """Calculate summary statistics"""
        total_issues = sum(cat['count'] for cat in owasp_categories.values())
        categories_with_issues = len([cat for cat in owasp_categories.values() if cat['count'] > 0])
        
        top_categories = sorted(
            [(name, data['count']) for name, data in owasp_categories.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total_issues": total_issues,
            "categories_affected": categories_with_issues,
            "total_categories": len(owasp_categories),
            "top_categories": [{"category": name, "issue_count": count} for name, count in top_categories if count > 0]
        }

def map_to_owasp_top10(scan_results: Dict, repo_results: Optional[Dict] = None) -> Dict:
    """
    Main function to map security issues to OWASP Top 10
    """
    mapper = OWASPMapper()
    return mapper.map_issues_to_owasp(scan_results, repo_results)