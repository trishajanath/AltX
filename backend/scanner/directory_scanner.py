import httpx
import dns.resolver
import dns.exception
import re
import time
import asyncio
import socket
from typing import List, Dict, Optional
from urllib.parse import urlparse

# Extended list of common paths to check
COMMON_PATHS = [
    "/admin", "/login", "/dashboard", "/admin/login", "/wp-admin",
    "/administrator", "/panel", "/user/login", "/auth", "/api",
    "/.git/config", "/.env", "/backup", "/config", "/robots.txt",
    "/sitemap.xml", "/phpinfo.php", "/info.php", "/test.php",
    "/wp-config.php", "/web.config", "/.htaccess", "/database.sql",
    "/debug", "/console", "/status", "/health", "/metrics"
]

# Enhanced WAF detection patterns with cookie-based and advanced detection
WAF_SIGNATURES = {
    'cloudflare': {
        'headers': ['cf-ray', 'cf-cache-status', '__cfduid', 'cf-request-id', 'server'],
        'header_values': {'server': ['cloudflare', 'cloudflare-nginx']},
        'cookies': ['__cfduid', '__cfuid', '__cf_bm', 'cf_clearance'],
        'error_codes': [403, 503, 520, 521, 522, 523, 524],
        'content_patterns': ['cloudflare', 'ray id', 'cf-error', 'attention required'],
        'error_pages': ['cloudflare error', 'checking your browser'],
        'custom_error_messages': ['please enable cookies', 'checking your browser']
    },
    'aws_waf': {
        'headers': ['x-amzn-requestid', 'x-amz-cf-id', 'x-amzn-trace-id', 'x-amzn-errortype'],
        'header_values': {'server': ['awselb/2.0', 'amazon', 'awselb', 'amazonS3']},
        'cookies': ['AWSALB', 'AWSALBCORS', 'aws-waf-token'],
        'error_codes': [403, 503],
        'content_patterns': ['blocked by aws waf', 'amazon cloudfront error', 'aws waf blocked', 'accessdeniedexception'],
        'error_pages': ['request blocked by aws waf', 'cloudfront error'],
        'custom_error_messages': ['forbidden', 'access denied by aws waf']
    },
    'mod_security': {
        'headers': ['mod_security', 'x-mod-security', 'server'],
        'header_values': {'server': ['apache', 'nginx']},
        'cookies': ['mod_security_session'],
        'error_codes': [403, 406, 501],
        'content_patterns': ['mod_security', 'modsecurity', 'not acceptable', 'security violation'],
        'error_pages': ['mod_security action'],
        'custom_error_messages': ['not acceptable', 'security violation detected']
    },
    'incapsula': {
        'headers': ['x-iinfo', 'incap_ses', 'x-cdn', 'x-cache'],
        'header_values': {'x-cdn': ['incapsula'], 'x-iinfo': ['incapsula']},
        'cookies': ['incap_ses', 'nlbi', 'visid_incap'],
        'error_codes': [403],
        'content_patterns': ['incapsula', 'incap_ses', 'imperva', 'access denied'],
        'error_pages': ['incapsula incident id'],
        'custom_error_messages': ['access denied', 'incapsula incident']
    },
    'sucuri': {
        'headers': ['x-sucuri-id', 'x-sucuri-cache', 'server'],
        'header_values': {'server': ['sucuri']},
        'cookies': ['sucuri_cloudproxy_uuid'],
        'error_codes': [403],
        'content_patterns': ['sucuri', 'access denied', 'website firewall', 'blocked by sucuri'],
        'error_pages': ['sucuri website firewall'],
        'custom_error_messages': ['blocked by sucuri', 'website firewall blocked']
    },
    'akamai': {
        'headers': ['akamai-ghost-ip', 'akamai-edgescape', 'x-akamai', 'server'],
        'header_values': {'server': ['akamaighost']},
        'cookies': ['ak_bmsc', 'bm_sz', 'abck'],
        'error_codes': [403],
        'content_patterns': ['akamai', 'reference #', 'edge server'],
        'error_pages': ['akamai error'],
        'custom_error_messages': ['reference #', 'akamai error']
    },
    'citrix_netscaler': {
        'headers': ['citrix-aag', 'ns-cache', 'server'],
        'header_values': {'server': ['netscaler', 'citrix-aag']},
        'cookies': ['ns_af', 'citrix_ns_id', 'nsid', 'aaatokenid'],  # ns_af is the key Citrix cookie!
        'error_codes': [403, 302],
        'content_patterns': ['citrix', 'netscaler', 'access gateway', 'you shouldn\'t be here'],
        'error_pages': ['citrix access denied', 'netscaler error'],
        'custom_error_messages': ['you shouldn\'t be here', 'citrix access gateway']
    },
    'f5_bigip': {
        'headers': ['f5-cache-status', 'server'],
        'header_values': {'server': ['bigip', 'f5', 'f5-ltm']},
        'cookies': ['bigipserver', 'f5avraaaaaaaaaaaaaaaa', 'bigip'],
        'error_codes': [403],
        'content_patterns': ['f5', 'bigip', 'application security policy'],
        'error_pages': ['f5 error', 'bigip blocked'],
        'custom_error_messages': ['application security policy', 'f5 application firewall']
    },
    'barracuda': {
        'headers': ['x-barracuda-url', 'server'],
        'header_values': {'server': ['barracuda']},
        'cookies': ['barra_counter', 'barracuda_', 'barra'],
        'error_codes': [403],
        'content_patterns': ['barracuda', 'web application firewall'],
        'error_pages': ['barracuda blocked'],
        'custom_error_messages': ['barracuda web application firewall']
    },
    'fortinet': {
        'headers': ['fortigate-authcookie', 'x-fortinet-guard'],
        'header_values': {'server': ['fortinet', 'fortigate']},
        'cookies': ['fortiwafsid', 'fortinet_session'],
        'error_codes': [403],
        'content_patterns': ['fortinet', 'fortigate', 'fortiweb'],
        'error_pages': ['fortinet blocked'],
        'custom_error_messages': ['fortinet security', 'blocked by fortigate']
    },
    'varnish': {
        'headers': ['x-varnish', 'via', 'server'],
        'header_values': {'server': ['varnish'], 'via': ['varnish']},
        'cookies': ['varnish_sess'],
        'error_codes': [403, 503],
        'content_patterns': ['varnish', 'you shouldn\'t be here'],
        'error_pages': ['varnish error'],
        'custom_error_messages': ['you shouldn\'t be here']  # Classic Varnish message!
    }
}

class SecurityAnalyzer:
    def __init__(self, domain: str):
        self.domain = domain
        self.detected_wafs = []
        self.blocked_requests = 0
        self.rate_limited = False
        self.waf_probe_tested = False

    def analyze_waf_response(self, response: httpx.Response) -> Dict:
        """Enhanced WAF detection with cookie analysis, header fingerprinting, and error message detection"""
        waf_info = {
            'waf_detected': False,
            'waf_type': None,
            'blocked': False,
            'evidence': [],
            'confidence': 0,
            'detection_methods': []
        }
        
        headers_lower = {k.lower(): v.lower() for k, v in response.headers.items()}
        
        # Extract cookies from Set-Cookie headers for analysis
        cookies = {}
        set_cookie_headers = response.headers.get_list('set-cookie') if hasattr(response.headers, 'get_list') else []
        if not set_cookie_headers and 'set-cookie' in response.headers:
            set_cookie_headers = [response.headers['set-cookie']]
        
        for cookie_header in set_cookie_headers:
            if '=' in cookie_header:
                cookie_name = cookie_header.split('=')[0].strip()
                cookies[cookie_name.lower()] = cookie_header
        
        for waf_name, signatures in WAF_SIGNATURES.items():
            evidence = []
            confidence = 0
            detected_methods = []
            
            # Method 1: Cookie-based detection (HIGH CONFIDENCE - as per your example)
            for cookie_name in signatures.get('cookies', []):
                if cookie_name.lower() in cookies:
                    evidence.append(f"WAF Cookie: {cookie_name}")
                    confidence += 60  # High confidence for cookie detection
                    detected_methods.append('cookie_detection')
                    # Special case for Citrix NetScaler ns_af cookie
                    if cookie_name.lower() == 'ns_af':
                        evidence.append("Citrix NetScaler App Firewall cookie detected")
                        confidence += 40  # Extra points for specific WAF cookie
            
            # Method 2: Header-based detection
            for header in signatures['headers']:
                if header.lower() in headers_lower:
                    evidence.append(f"WAF Header: {header}")
                    confidence += 30
                    detected_methods.append('header_detection')
            
            # Method 3: Header value analysis
            for header, values in signatures.get('header_values', {}).items():
                if header.lower() in headers_lower:
                    for value in values:
                        if value.lower() in headers_lower[header.lower()]:
                            evidence.append(f"Header Value: {header}={value}")
                            confidence += 40
                            detected_methods.append('header_value_detection')
            
            # Method 4: Status code analysis
            if response.status_code in signatures['error_codes']:
                evidence.append(f"WAF Status Code: {response.status_code}")
                confidence += 20
                detected_methods.append('status_code_detection')
            
            # Method 5: Content pattern matching
            try:
                content = response.text.lower()
                
                # Check for content patterns
                for pattern in signatures['content_patterns']:
                    if pattern.lower() in content:
                        evidence.append(f"Content Pattern: {pattern}")
                        confidence += 25
                        detected_methods.append('content_pattern_detection')
                
                # Check for specific error pages
                for error_page in signatures.get('error_pages', []):
                    if error_page.lower() in content:
                        evidence.append(f"Error Page: {error_page}")
                        confidence += 50
                        detected_methods.append('error_page_detection')
                
                # Method 6: Custom error message detection (NEW - as per your examples)
                for custom_msg in signatures.get('custom_error_messages', []):
                    if custom_msg.lower() in content:
                        evidence.append(f"Custom Error Message: '{custom_msg}'")
                        confidence += 45  # High confidence for custom messages
                        detected_methods.append('custom_error_detection')
                        
            except:
                pass
            
            # Method 7: Session timeout detection (rapid session expiry)
            cache_control = headers_lower.get('cache-control', '')
            expires = headers_lower.get('expires', '')
            if ('no-cache' in cache_control and 'no-store' in cache_control) or 'max-age=0' in cache_control:
                evidence.append("Rapid session expiry detected")
                confidence += 15
                detected_methods.append('session_timeout_detection')
            
            # If confidence is high enough, mark as detected
            if confidence >= 60 and evidence:  # Keep threshold at 60 for accuracy
                waf_info.update({
                    'waf_detected': True,
                    'waf_type': waf_name,
                    'evidence': evidence,
                    'confidence': confidence,
                    'blocked': response.status_code in [403, 406, 429],
                    'detection_methods': detected_methods
                })
                if waf_info['blocked']:
                    self.blocked_requests += 1
                break
        
        return waf_info

    async def waf_active_probe(self, client: httpx.AsyncClient, base_url: str) -> Dict:
        """
        ENHANCED: Active WAF probe test with content analysis for silent WAFs
        This detects WAFs that don't block but serve different content
        """
        probe_info = {
            'probe_tested': False,
            'waf_confirmed': False,
            'evidence': [],
            'confidence_boost': 0,
            'debug_info': [],
            'detection_method': 'content_analysis'  # NEW: Track detection method
        }
        
        if self.waf_probe_tested:
            return probe_info
            
        try:
            self.waf_probe_tested = True
            probe_info['probe_tested'] = True
            
            # First, get a baseline response to compare against
            try:
                baseline_response = await client.get(base_url)
                baseline_status = baseline_response.status_code
                baseline_content = baseline_response.text
                baseline_length = len(baseline_content)
                baseline_headers = dict(baseline_response.headers)
                
                probe_info['debug_info'].append(f"Baseline: {base_url} -> {baseline_status} ({baseline_length} bytes)")
            except Exception as e:
                probe_info['debug_info'].append(f"Baseline request failed: {str(e)}")
                return probe_info
            
            # Test probes - more aggressive and varied
            test_queries = [
                "/?test=<script>alert('waf-test')</script>",
                "/?id=1' OR '1'='1",
                "/?search=../../../etc/passwd",
                "/?input=<img src=x onerror=alert(1)>",
                "/?file=/etc/passwd"
            ]
            
            content_diffs = []  # Track content size differences
            
            for test_query in test_queries:
                try:
                    probe_url = base_url + test_query
                    probe_response = await client.get(probe_url)
                    probe_status = probe_response.status_code
                    probe_content = probe_response.text
                    probe_length = len(probe_content)
                    probe_headers = dict(probe_response.headers)
                    
                    probe_info['debug_info'].append(f"Probe: {test_query} -> {probe_status} ({probe_length} bytes)")
                    
                    # Track content size difference
                    length_diff = abs(probe_length - baseline_length)
                    content_diffs.append(length_diff)
                    
                    # Method 1: Status code differences (blocking WAFs)
                    if probe_status != baseline_status and probe_status in [403, 406, 429, 451]:
                        probe_info['waf_confirmed'] = True
                        probe_info['evidence'].append(f"Status difference: {test_query} -> {probe_status} (baseline: {baseline_status})")
                        probe_info['confidence_boost'] += 60
                        probe_info['detection_method'] = 'status_blocking'
                        break
                    
                    # Method 2: Major content differences (content substitution WAFs)
                    length_ratio = length_diff / baseline_length if baseline_length > 0 else 0
                    if length_ratio > 0.1 and length_diff > 1000:  # More than 10% difference AND at least 1KB
                        probe_info['waf_confirmed'] = True
                        probe_info['evidence'].append(f"Major content size difference: {test_query} -> {probe_length} bytes vs baseline {baseline_length} bytes ({length_ratio:.1%} difference)")
                        probe_info['confidence_boost'] += 40
                        probe_info['detection_method'] = 'content_substitution'
                    
                    # Method 3: Significant content modifications (not micro-changes)
                    elif length_diff > 500:  # More than 500 bytes difference (not tiny changes)
                        probe_info['waf_confirmed'] = True
                        probe_info['evidence'].append(f"Significant content modification detected: {test_query} -> {length_diff} bytes difference ({length_ratio:.3%})")
                        probe_info['confidence_boost'] += 35
                        probe_info['detection_method'] = 'content_modification'
                        
                    # Method 4: Content word analysis (sophisticated content filtering)
                    if baseline_length > 1000 and probe_length > 100:  # Only if we have substantial content
                        # Check for completely different content
                        baseline_words = set(baseline_content.lower().split()[:50])  # First 50 words
                        probe_words = set(probe_content.lower().split()[:50])
                        
                        common_words = baseline_words.intersection(probe_words)
                        similarity = len(common_words) / len(baseline_words) if baseline_words else 0
                        
                        if similarity < 0.3:  # Less than 30% word overlap
                            probe_info['waf_confirmed'] = True
                            probe_info['evidence'].append(f"Content substitution detected: {test_query} -> {similarity:.1%} content similarity")
                            probe_info['confidence_boost'] += 50
                            probe_info['detection_method'] = 'content_substitution'
                    
                    # Method 5: Header analysis (server header changes)
                    baseline_server = baseline_headers.get('server', '').lower()
                    probe_server = probe_headers.get('server', '').lower()
                    
                    if baseline_server and probe_server and baseline_server != probe_server:
                        probe_info['evidence'].append(f"Server header changed: {baseline_server} -> {probe_server}")
                        probe_info['confidence_boost'] += 30
                    
                    # Method 6: Look for WAF-specific content patterns
                    waf_content_indicators = [
                        'blocked', 'security', 'firewall', 'violation', 'forbidden',
                        'access denied', 'not allowed', 'suspicious', 'filtered',
                        'error', 'warning', 'incident', 'reference', 'protection'
                    ]
                    
                    probe_content_lower = probe_content.lower()
                    found_indicators = [term for term in waf_content_indicators if term in probe_content_lower and term not in baseline_content.lower()]
                    
                    if found_indicators:
                        probe_info['evidence'].append(f"WAF content indicators found: {', '.join(found_indicators)}")
                        probe_info['confidence_boost'] += 25
                    
                    # Method 7: Session timeout detection (rapid session expiry as WAF indicator)
                    probe_cache_control = probe_headers.get('cache-control', '').lower()
                    baseline_cache_control = baseline_headers.get('cache-control', '').lower()
                    
                    # Check for aggressive cache control changes
                    if ('no-cache' in probe_cache_control and 'no-cache' not in baseline_cache_control) or \
                       ('max-age=0' in probe_cache_control and 'max-age=0' not in baseline_cache_control):
                        probe_info['evidence'].append(f"Session timeout behavior detected: cache-control changed to {probe_cache_control}")
                        probe_info['confidence_boost'] += 20
                        probe_info['detection_method'] = 'session_timeout_detection'
                    
                    # Method 8: Response time analysis (WAFs may add latency)
                    # Note: This would require timing measurements, which we can add if needed
                    
                    # If we found evidence, break early
                    if probe_info['waf_confirmed']:
                        break
                        
                    await asyncio.sleep(0.5)  # Small delay between probes
                    
                except Exception as e:
                    probe_info['debug_info'].append(f"Probe error for {test_query}: {str(e)}")
                    continue
            
            # FIXED: Final analysis for actual WAF detection (not micro-changes)
            if not probe_info['waf_confirmed']:
                # Check for consistent significant modifications across multiple probes
                if len(content_diffs) >= 3:
                    # Method 1: Any probe with significant differences (500+ bytes)
                    significant_diffs = [diff for diff in content_diffs if diff > 500]
                    if significant_diffs:
                        probe_info['waf_confirmed'] = True
                        probe_info['evidence'].append(f"Content modification pattern detected: {len(significant_diffs)} probes with significant differences {significant_diffs}")
                        probe_info['confidence_boost'] += 50
                        probe_info['detection_method'] = 'content_modification'
                        probe_info['debug_info'].append(f"✅ WAF DETECTED: Significant content differences indicate request processing")
                    
                    # Method 2: Multiple large changes (200+ bytes)
                    elif len([d for d in content_diffs if d > 200]) >= 3:  # 3+ probes with 200+ byte differences
                        probe_info['waf_confirmed'] = True
                        probe_info['evidence'].append(f"Multiple content variations detected: {[d for d in content_diffs if d > 200]} - indicates request processing")
                        probe_info['confidence_boost'] += 40
                        probe_info['detection_method'] = 'request_processing_detected'
                        probe_info['debug_info'].append(f"✅ WAF DETECTED: Multiple variations suggest active filtering")
                
                if not probe_info['waf_confirmed']:
                    probe_info['debug_info'].append("No WAF confirmed - all probes returned similar responses")
                    
                    # ENHANCEMENT: Even if no WAF confirmed, check for silent protection indicators
                    if baseline_length > 5000:  # Large page suggests dynamic content
                        probe_info['evidence'].append("Large dynamic page suggests potential silent WAF protection")
                        probe_info['confidence_boost'] += 10
                
        except Exception as e:
            probe_info['evidence'].append(f"Probe test error: {str(e)}")
            probe_info['debug_info'].append(f"General error: {str(e)}")
        
        return probe_info

    def check_dnssec(self) -> Dict:
        """
        ENHANCED: Proper DNSSEC validation with resolver validation awareness
        """
        dnssec_info = {
            'enabled': False,
            'status': 'Unknown',
            'details': [],
            'error': None,
            'validation_chain': [],
            'resolver_validation': 'unknown'
        }
        
        try:
            # ENHANCEMENT: Test if our resolver supports DNSSEC validation
            resolver = dns.resolver.Resolver()
            
            # Check resolver's DNSSEC capability
            try:
                # Query a known DNSSEC-signed domain to test resolver
                test_response = resolver.resolve('dnssec-name-and-shame.com', 'A')
                if hasattr(test_response.response, 'flags') and test_response.response.flags & dns.flags.AD:
                    dnssec_info['resolver_validation'] = 'capable'
                    dnssec_info['details'].append("DNS resolver supports DNSSEC validation")
                else:
                    dnssec_info['resolver_validation'] = 'limited'
                    dnssec_info['details'].append("DNS resolver has limited DNSSEC support")
            except:
                dnssec_info['resolver_validation'] = 'unknown'
                dnssec_info['details'].append("Could not verify resolver DNSSEC capability")
            
            # Enable DNSSEC validation
            resolver.use_edns(0, dns.flags.DO)
            
            # Check for DNSKEY records
            try:
                dnskey_response = resolver.resolve(self.domain, 'DNSKEY')
                if dnskey_response:
                    dnssec_info['validation_chain'].append("DNSKEY records found")
                    
                    # ENHANCEMENT: Check for valid DNSSEC signatures with resolver awareness
                    if dnskey_response.response.flags & dns.flags.AD:
                        dnssec_info['enabled'] = True
                        dnssec_info['status'] = 'Fully Validated'
                        dnssec_info['details'].append(f"Found {len(dnskey_response)} DNSKEY records with valid signatures")
                        
                        if dnssec_info['resolver_validation'] == 'capable':
                            dnssec_info['details'].append("DNSSEC validation confirmed by capable resolver")
                        else:
                            dnssec_info['details'].append("DNSSEC records present (resolver validation uncertain)")
                    else:
                        dnssec_info['status'] = 'DNSKEY present but not validated'
                        dnssec_info['details'].append("DNSKEY records found but signatures not validated")
                        
                        if dnssec_info['resolver_validation'] == 'limited':
                            dnssec_info['details'].append("May be due to resolver limitations")
                        
            except dns.resolver.NXDOMAIN:
                dnssec_info['status'] = 'Domain not found'
            except dns.resolver.NoAnswer:
                dnssec_info['status'] = 'No DNSKEY records'
                dnssec_info['details'].append("No DNSKEY records found")
            
            # Check for DS records in parent zone
            try:
                parent_domain = '.'.join(self.domain.split('.')[1:])
                if parent_domain:
                    ds_response = resolver.resolve(self.domain, 'DS')
                    if ds_response:
                        dnssec_info['validation_chain'].append("DS records found in parent zone")
                        dnssec_info['details'].append(f"Found {len(ds_response)} DS records")
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                dnssec_info['details'].append("No DS records in parent zone")
                
        except Exception as e:
            dnssec_info['error'] = str(e)
            dnssec_info['status'] = 'Error checking DNSSEC'
        
        return dnssec_info

    def check_dmarc(self) -> Dict:
        """Enhanced DMARC policy validation"""
        dmarc_info = {
            'enabled': False,
            'policy': None,
            'subdomain_policy': None,
            'percentage': None,
            'alignment': {'spf': None, 'dkim': None},
            'reporting': {'rua': [], 'ruf': []},
            'details': [],
            'record': None,
            'error': None,
            'validation': 'unknown'
        }
        
        try:
            dmarc_domain = f"_dmarc.{self.domain}"
            txt_records = dns.resolver.resolve(dmarc_domain, 'TXT')
            
            for record in txt_records:
                record_str = str(record).strip('"')
                if record_str.startswith('v=DMARC1'):
                    dmarc_info['enabled'] = True
                    dmarc_info['record'] = record_str
                    dmarc_info['validation'] = 'valid'
                    
                    # Parse DMARC components
                    components = dict(item.split('=', 1) for item in record_str.split(';') if '=' in item)
                    
                    # Policy
                    policy = components.get('p', '').strip()
                    if policy == 'none':
                        dmarc_info['policy'] = 'none (monitoring only)'
                    elif policy == 'quarantine':
                        dmarc_info['policy'] = 'quarantine (suspicious emails to spam)'
                    elif policy == 'reject':
                        dmarc_info['policy'] = 'reject (strict enforcement)'
                    
                    # Subdomain policy
                    sp = components.get('sp', '').strip()
                    if sp:
                        dmarc_info['subdomain_policy'] = sp
                    
                    # Percentage
                    pct = components.get('pct', '100').strip()
                    dmarc_info['percentage'] = f"{pct}%"
                    
                    # Alignment modes
                    dmarc_info['alignment']['spf'] = components.get('aspf', 'relaxed').strip()
                    dmarc_info['alignment']['dkim'] = components.get('adkim', 'relaxed').strip()
                    
                    # Reporting
                    if 'rua' in components:
                        dmarc_info['reporting']['rua'] = [email.strip() for email in components['rua'].split(',')]
                        dmarc_info['details'].append("Aggregate reports configured")
                    
                    if 'ruf' in components:
                        dmarc_info['reporting']['ruf'] = [email.strip() for email in components['ruf'].split(',')]
                        dmarc_info['details'].append("Forensic reports configured")
                    
                    # Additional details
                    if policy == 'reject' and pct == '100':
                        dmarc_info['details'].append("Strong policy: Full rejection enforcement")
                    elif policy == 'quarantine':
                        dmarc_info['details'].append("Moderate policy: Quarantine suspicious emails")
                    elif policy == 'none':
                        dmarc_info['details'].append("Monitoring mode: No enforcement action")
                    
                    break
            
            if not dmarc_info['enabled']:
                dmarc_info['details'].append("No DMARC record found")
                dmarc_info['validation'] = 'missing'
                
        except dns.resolver.NXDOMAIN:
            dmarc_info['details'].append("DMARC record not found")
            dmarc_info['validation'] = 'missing'
        except Exception as e:
            dmarc_info['error'] = str(e)
            dmarc_info['validation'] = 'error'
        
        return dmarc_info

    def check_dkim(self) -> Dict:
        """Smart DKIM detection using multiple methods"""
        dkim_info = {
            'selectors_found': [],
            'total_checked': 0,
            'details': [],
            'error': None,
            'discovery_method': [],
            'limitation_note': 'DKIM check is best-effort - custom selectors may not be detected'
        }
        
        # Method 1: Common selectors
        common_selectors = [
            'default', 'google', 'k1', 'k2', 'mail', 'email', 'dkim',
            'selector1', 'selector2', 's1', 's2', 'mailchimp', 'mandrill',
            'mxvault', 'everlytickey1', 'everlytickey2', 'key1', 'key2'
        ]
        
        # Method 2: Try to discover from email headers (if available)
        try:
            # Check MX records to identify email providers
            mx_records = dns.resolver.resolve(self.domain, 'MX')
            mx_hosts = [str(mx.exchange).lower() for mx in mx_records]
            
            # Add provider-specific selectors
            for mx_host in mx_hosts:
                if 'google' in mx_host or 'gmail' in mx_host:
                    common_selectors.extend(['google', '20210112', '20161025'])
                    dkim_info['discovery_method'].append('Google Workspace detected')
                elif 'outlook' in mx_host or 'office365' in mx_host:
                    common_selectors.extend(['selector1', 'selector2'])
                    dkim_info['discovery_method'].append('Office 365 detected')
                elif 'mailchimp' in mx_host:
                    common_selectors.extend(['k1', 'k2', 'k3'])
                    dkim_info['discovery_method'].append('Mailchimp detected')
                    
        except:
            pass
        
        # Remove duplicates and check selectors
        unique_selectors = list(set(common_selectors))
        
        try:
            for selector in unique_selectors:
                dkim_info['total_checked'] += 1
                try:
                    dkim_domain = f"{selector}._domainkey.{self.domain}"
                    txt_records = dns.resolver.resolve(dkim_domain, 'TXT')
                    
                    for record in txt_records:
                        record_str = str(record).strip('"')
                        if 'v=DKIM1' in record_str or ('k=' in record_str and 'p=' in record_str):
                            # Parse DKIM record
                            dkim_record = {
                                'selector': selector,
                                'record': record_str,
                                'key_type': 'unknown',
                                'hash_algorithms': [],
                                'public_key_present': 'p=' in record_str
                            }
                            
                            # Extract key type
                            if 'k=rsa' in record_str:
                                dkim_record['key_type'] = 'RSA'
                            elif 'k=ed25519' in record_str:
                                dkim_record['key_type'] = 'Ed25519'
                            
                            # Extract hash algorithms
                            if 'h=' in record_str:
                                h_match = re.search(r'h=([^;]+)', record_str)
                                if h_match:
                                    dkim_record['hash_algorithms'] = h_match.group(1).split(':')
                            
                            dkim_info['selectors_found'].append(dkim_record)
                            break
                            
                except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                    continue
                except Exception:
                    continue
            
            if dkim_info['selectors_found']:
                dkim_info['details'].append(f"Found {len(dkim_info['selectors_found'])} DKIM selectors")
                
                # Analyze quality
                rsa_keys = [s for s in dkim_info['selectors_found'] if s['key_type'] == 'RSA']
                if rsa_keys:
                    dkim_info['details'].append(f"RSA encryption: {len(rsa_keys)} keys")
                
                ed25519_keys = [s for s in dkim_info['selectors_found'] if s['key_type'] == 'Ed25519']
                if ed25519_keys:
                    dkim_info['details'].append(f"Ed25519 encryption: {len(ed25519_keys)} keys (modern)")
                    
            else:
                dkim_info['details'].append(f"No DKIM records found (checked {dkim_info['total_checked']} selectors)")
                
        except Exception as e:
            dkim_info['error'] = str(e)
        
        return dkim_info

async def scan_common_paths(url: str) -> Dict:
    """
    Enhanced scanner with improved WAF detection and proper DNS security checks
    """
    # Extract domain from URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    
    # Remove port if present
    if ':' in domain:
        domain = domain.split(':')[0]
    
    # Remove www prefix for DNS checks
    dns_domain = domain
    if domain.startswith('www.'):
        dns_domain = domain[4:]
    
    analyzer = SecurityAnalyzer(dns_domain)
    
    scan_results = {
        'accessible_paths': [],
        'waf_analysis': {
            'waf_detected': False,
            'waf_type': None,
            'protection_level': 'Unknown',
            'blocked_requests': 0,
            'total_requests': 0,
            'evidence': [],
            'confidence': 0,
            'active_probe': {}  # NEW: Active probe results
        },
        'dns_security': {
            'dnssec': {},
            'dmarc': {},
            'dkim': {}
        },
        'scan_summary': {
            'domain': domain,
            'dns_domain': dns_domain,
            'total_paths_checked': len(COMMON_PATHS),
            'accessible_paths_found': 0,
            'blocked_paths': 0,
            'scan_duration': 0
        }
    }
    
    base_url = url.rstrip('/')
    start_time = time.time()
    
    # Custom headers to avoid basic bot detection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    print(f"🔍 Starting comprehensive security scan for: {domain}")
    print(f"🔐 DNS security checks for: {dns_domain}")
    
    # 1. DNS Security Checks (run in parallel)
    print("🔐 Checking DNS security features...")
    scan_results['dns_security']['dnssec'] = analyzer.check_dnssec()
    scan_results['dns_security']['dmarc'] = analyzer.check_dmarc()
    scan_results['dns_security']['dkim'] = analyzer.check_dkim()
    
    # 2. Path scanning with enhanced WAF detection
    print("🛡️ Scanning paths and detecting WAF...")
    async with httpx.AsyncClient(
        timeout=15.0, 
        follow_redirects=True,
        headers=headers
    ) as client:
        
        for i, path in enumerate(COMMON_PATHS):
            try:
                target_url = base_url + path
                
                # Add small delay to avoid triggering aggressive rate limiting
                if i > 0:
                    await asyncio.sleep(0.3)
                
                response = await client.get(target_url)
                scan_results['waf_analysis']['total_requests'] += 1
                
                # Enhanced WAF analysis
                waf_analysis = analyzer.analyze_waf_response(response)
                
                # Update WAF detection results with highest confidence match
                if waf_analysis['waf_detected'] and waf_analysis['confidence'] > scan_results['waf_analysis']['confidence']:
                    scan_results['waf_analysis'].update({
                        'waf_detected': True,
                        'waf_type': waf_analysis['waf_type'],
                        'evidence': waf_analysis['evidence'],
                        'confidence': waf_analysis['confidence'],
                        'detection_methods': waf_analysis.get('detection_methods', [])
                    })
                
                # Check if path is accessible
                if response.status_code == 200 and len(response.content) > 200:
                    if not _is_homepage_redirect(response, base_url):
                        print(f"✅ Found accessible path: {target_url}")
                        scan_results['accessible_paths'].append({
                            "path": path,
                            "status_code": response.status_code,
                            "url": target_url,
                            "content_length": len(response.content),
                            "waf_analysis": waf_analysis
                        })
                        scan_results['scan_summary']['accessible_paths_found'] += 1
                
                # Track blocked requests
                elif response.status_code in [403, 406, 429]:
                    scan_results['scan_summary']['blocked_paths'] += 1
                    print(f"🚫 Path blocked: {target_url} (Status: {response.status_code})")
                
                # Rate limiting detection
                if response.status_code == 429:
                    print(f"⏰ Rate limiting detected, adding delays...")
                    await asyncio.sleep(2)
                
            except httpx.RequestError as e:
                print(f"⚠️ Could not connect to {target_url}: {e}")
                continue
            except Exception as e:
                print(f"⚠️ Error scanning {target_url}: {e}")
                continue
        
                # ENHANCEMENT: Active WAF probe test (run after path scanning)
        print("🧪 Performing active WAF probe test...")
        probe_results = await analyzer.waf_active_probe(client, base_url)
        scan_results['waf_analysis']['active_probe'] = probe_results
        
        # Debug output
        print(f"🔍 Probe results: {probe_results}")
        for debug_msg in probe_results.get('debug_info', []):
            print(f"   Debug: {debug_msg}")
        
        # Boost confidence if probe confirms WAF
        if probe_results['waf_confirmed']:
            print(f"✅ WAF confirmed via active probe!")
            scan_results['waf_analysis']['confidence'] += probe_results['confidence_boost']
            scan_results['waf_analysis']['evidence'].extend(probe_results['evidence'])
            if not scan_results['waf_analysis']['waf_detected']:
                scan_results['waf_analysis']['waf_detected'] = True
                scan_results['waf_analysis']['waf_type'] = 'Generic WAF (probe confirmed)'
        else:
            print(f"❌ No WAF detected via active probe")
    
    # Finalize WAF analysis with comprehensive detection summary
    scan_results['waf_analysis']['blocked_requests'] = analyzer.blocked_requests
    
    # Enhanced WAF Detection Summary (based on your manual/automated detection techniques)
    if scan_results['waf_analysis']['waf_detected']:
        confidence = scan_results['waf_analysis']['confidence']
        waf_type = scan_results['waf_analysis'].get('waf_type', 'Unknown')
        evidence = scan_results['waf_analysis'].get('evidence', [])
        detection_methods = scan_results['waf_analysis'].get('detection_methods', [])
        
        # Determine protection level based on confidence and evidence
        if confidence >= 80:
            scan_results['waf_analysis']['protection_level'] = 'High'
        elif confidence >= 50:
            scan_results['waf_analysis']['protection_level'] = 'Medium'
        else:
            scan_results['waf_analysis']['protection_level'] = 'Low'
        
        # Add detection method summary
        scan_results['waf_analysis']['detection_summary'] = {
            'primary_detection_method': detection_methods[0] if detection_methods else 'unknown',
            'all_detection_methods': detection_methods,
            'evidence_count': len(evidence),
            'manual_verification_possible': True,  # Always possible to manually verify
            'automated_tools_compatible': True,     # Our detection is compatible with automated tools
        }
        
        # Special handling for high-confidence detections (like cookie-based)
        if 'cookie_detection' in detection_methods:
            scan_results['waf_analysis']['detection_summary']['manual_verification_method'] = 'Check browser cookies for WAF-specific cookies'
            if 'ns_af' in str(evidence).lower():
                scan_results['waf_analysis']['detection_summary']['manual_verification_method'] = 'Check for ns_af cookie indicating Citrix NetScaler App Firewall'
        
        if 'custom_error_detection' in detection_methods:
            scan_results['waf_analysis']['detection_summary']['manual_verification_method'] = 'Send malicious requests and observe custom error messages'
        
        if 'header_detection' in detection_methods:
            scan_results['waf_analysis']['detection_summary']['manual_verification_method'] = 'Inspect HTTP response headers for WAF-specific headers'
        
        # Add automation tool recommendations
        scan_results['waf_analysis']['detection_summary']['recommended_tools'] = []
        if confidence >= 70:
            scan_results['waf_analysis']['detection_summary']['recommended_tools'].extend([
                'wafw00f - WAF fingerprinting tool',
                'Nmap http-waf-detect script',
                'Manual cookie inspection'
            ])
        
        print(f"✅ WAF DETECTED: {waf_type} (Confidence: {confidence}%, Protection: {scan_results['waf_analysis']['protection_level']})")
        print(f"   Detection Methods: {', '.join(detection_methods)}")
        print(f"   Evidence: {len(evidence)} indicators found")
        
        # Manual verification guidance
        if 'cookie_detection' in detection_methods:
            print(f"   💡 Manual Verification: Check browser cookies for WAF-specific cookies")
        if 'custom_error_detection' in detection_methods:
            print(f"   💡 Manual Verification: Send test payloads and observe custom error messages")
    else:
        scan_results['waf_analysis']['protection_level'] = 'None'
        scan_results['waf_analysis']['detection_summary'] = {
            'primary_detection_method': 'none',
            'all_detection_methods': [],
            'evidence_count': 0,
            'manual_verification_possible': True,
            'automated_tools_compatible': True,
            'manual_verification_method': 'Send malicious payloads and check for blocking or error responses',
            'recommended_tools': [
                'wafw00f - Comprehensive WAF detection',
                'Nmap http-waf-detect script',
                'Manual payload testing'
            ]
        }
        print(f"❌ NO WAF DETECTED - Consider implementing WAF protection")
    
    scan_results['scan_summary']['scan_duration'] = round(time.time() - start_time, 2)
    
    return scan_results

def _is_homepage_redirect(response: httpx.Response, base_url: str) -> bool:
    """Check if the response is just a redirect to the homepage"""
    try:
        if len(response.content) < 500:
            return True
        
        content_lower = response.text.lower()
        redirect_indicators = ['window.location', 'meta http-equiv="refresh"', 'redirect']
        
        return any(indicator in content_lower for indicator in redirect_indicators)
    except:
        return False