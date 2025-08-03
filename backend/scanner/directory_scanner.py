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

# Enhanced WAF detection patterns
WAF_SIGNATURES = {
    'cloudflare': {
        'headers': ['cf-ray', 'cf-cache-status', '__cfduid', 'cf-request-id', 'server'],
        'header_values': {'server': ['cloudflare', 'cloudflare-nginx']},
        'error_codes': [403, 503, 520, 521, 522, 523, 524],
        'content_patterns': ['cloudflare', 'ray id', 'cf-error', 'attention required'],
        'error_pages': ['cloudflare error', 'checking your browser']
    },
    'aws_waf': {
        'headers': ['x-amzn-requestid', 'x-amz-cf-id', 'x-amzn-trace-id', 'server'],
        'header_values': {'server': ['awselb', 'amazon']},
        'error_codes': [403],
        'content_patterns': ['aws', 'blocked by aws waf', 'amazon cloudfront'],
        'error_pages': ['request blocked']
    },
    'mod_security': {
        'headers': ['mod_security', 'x-mod-security', 'server'],
        'header_values': {'server': ['apache', 'nginx']},
        'error_codes': [403, 406],
        'content_patterns': ['mod_security', 'modsecurity', 'not acceptable', 'security violation'],
        'error_pages': ['mod_security action']
    },
    'incapsula': {
        'headers': ['x-iinfo', 'incap_ses', 'x-cdn', 'x-cache'],
        'header_values': {'x-cdn': ['incapsula'], 'x-iinfo': ['incapsula']},
        'error_codes': [403],
        'content_patterns': ['incapsula', 'incap_ses', 'imperva', 'access denied'],
        'error_pages': ['incapsula incident id']
    },
    'sucuri': {
        'headers': ['x-sucuri-id', 'x-sucuri-cache', 'server'],
        'header_values': {'server': ['sucuri']},
        'error_codes': [403],
        'content_patterns': ['sucuri', 'access denied', 'website firewall', 'blocked by sucuri'],
        'error_pages': ['sucuri website firewall']
    },
    'akamai': {
        'headers': ['akamai-ghost-ip', 'akamai-edgescape', 'x-akamai', 'server'],
        'header_values': {'server': ['akamaighost']},
        'error_codes': [403],
        'content_patterns': ['akamai', 'reference #', 'edge server'],
        'error_pages': ['akamai error']
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
        """Enhanced WAF detection with multiple detection methods"""
        waf_info = {
            'waf_detected': False,
            'waf_type': None,
            'blocked': False,
            'evidence': [],
            'confidence': 0
        }
        
        headers_lower = {k.lower(): v.lower() for k, v in response.headers.items()}
        
        for waf_name, signatures in WAF_SIGNATURES.items():
            evidence = []
            confidence = 0
            
            # Check headers
            for header in signatures['headers']:
                if header.lower() in headers_lower:
                    evidence.append(f"Header: {header}")
                    confidence += 30
            
            # Check header values
            for header, values in signatures.get('header_values', {}).items():
                if header.lower() in headers_lower:
                    for value in values:
                        if value.lower() in headers_lower[header.lower()]:
                            evidence.append(f"Header Value: {header}={value}")
                            confidence += 40
            
            # Check status codes
            if response.status_code in signatures['error_codes']:
                evidence.append(f"Status Code: {response.status_code}")
                confidence += 20
            
            # Check content patterns
            try:
                content = response.text.lower()
                for pattern in signatures['content_patterns']:
                    if pattern.lower() in content:
                        evidence.append(f"Content Pattern: {pattern}")
                        confidence += 25
                
                # Check for specific error pages
                for error_page in signatures.get('error_pages', []):
                    if error_page.lower() in content:
                        evidence.append(f"Error Page: {error_page}")
                        confidence += 50
                        
            except:
                pass
            
            # If confidence is high enough, mark as detected
            if confidence >= 40 and evidence:
                waf_info.update({
                    'waf_detected': True,
                    'waf_type': waf_name,
                    'evidence': evidence,
                    'confidence': confidence,
                    'blocked': response.status_code in [403, 406, 429]
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
                    if length_ratio > 0.3:  # More than 30% difference in content size
                        probe_info['waf_confirmed'] = True
                        probe_info['evidence'].append(f"Major content size difference: {test_query} -> {probe_length} bytes vs baseline {baseline_length} bytes ({length_ratio:.1%} difference)")
                        probe_info['confidence_boost'] += 40
                        probe_info['detection_method'] = 'content_substitution'
                    
                    # Method 3: Subtle content modifications (silent WAFs like Netflix)
                    elif length_diff > 20:  # More than 20 bytes difference
                        probe_info['waf_confirmed'] = True
                        probe_info['evidence'].append(f"Subtle content modification detected: {test_query} -> {length_diff} bytes difference ({length_ratio:.3%})")
                        probe_info['confidence_boost'] += 35
                        probe_info['detection_method'] = 'subtle_content_modification'
                        
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
                    
                    # If we found evidence, break early
                    if probe_info['waf_confirmed']:
                        break
                        
                    await asyncio.sleep(0.5)  # Small delay between probes
                    
                except Exception as e:
                    probe_info['debug_info'].append(f"Probe error for {test_query}: {str(e)}")
                    continue
            
            # CRITICAL FIX: Final analysis for consistent small changes (Netflix pattern)
            if not probe_info['waf_confirmed']:
                # Check for consistent content modifications across multiple probes
                if len(content_diffs) >= 3:
                    # Method 1: Any probe with significant differences (20+ bytes)
                    significant_diffs = [diff for diff in content_diffs if diff > 20]
                    if significant_diffs:
                        probe_info['waf_confirmed'] = True
                        probe_info['evidence'].append(f"Content modification pattern detected: {len(content_diffs)} probes with differences {content_diffs}")
                        probe_info['confidence_boost'] += 50
                        probe_info['detection_method'] = 'subtle_content_modification'
                        probe_info['debug_info'].append(f"✅ WAF DETECTED: Content differences indicate request processing")
                    
                    # Method 2: Multiple small changes still indicate processing (10+ bytes)
                    elif len([d for d in content_diffs if d > 10]) >= 4:  # 4+ probes with 10+ byte differences
                        probe_info['waf_confirmed'] = True
                        probe_info['evidence'].append(f"Multiple content variations detected: {content_diffs} - indicates request processing")
                        probe_info['confidence_boost'] += 40
                        probe_info['detection_method'] = 'request_processing_detected'
                        probe_info['debug_info'].append(f"✅ WAF DETECTED: Multiple variations suggest active filtering")
                    
                    # Method 3: Even tiny consistent changes suggest processing (5+ bytes)
                    elif len([d for d in content_diffs if d > 5]) >= 3:  # 3+ probes with 5+ byte differences
                        probe_info['waf_confirmed'] = True
                        probe_info['evidence'].append(f"Consistent micro-variations detected: {content_diffs} - suggests request monitoring")
                        probe_info['confidence_boost'] += 30
                        probe_info['detection_method'] = 'micro_content_variation'
                        probe_info['debug_info'].append(f"✅ WAF DETECTED: Micro-variations indicate request monitoring")
                
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
                        'confidence': waf_analysis['confidence']
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
    
    # Finalize results
    scan_results['waf_analysis']['blocked_requests'] = analyzer.blocked_requests
    
    # Finalize results
    scan_results['waf_analysis']['blocked_requests'] = analyzer.blocked_requests
    
    if scan_results['waf_analysis']['waf_detected']:
        confidence = scan_results['waf_analysis']['confidence']
        if confidence >= 80:
            scan_results['waf_analysis']['protection_level'] = 'High'
        elif confidence >= 50:
            scan_results['waf_analysis']['protection_level'] = 'Medium'
        else:
            scan_results['waf_analysis']['protection_level'] = 'Low'
    
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