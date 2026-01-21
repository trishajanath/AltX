"""
OWASP ZAP Security Scanner Service
Performs passive and active security scans on dynamically generated application URLs.
"""

import time
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

try:
    from zapv2 import ZAPv2
    ZAP_AVAILABLE = True
except ImportError:
    ZAP_AVAILABLE = False
    print("⚠️ python-owasp-zap-v2.4 not installed. Run: pip install python-owasp-zap-v2.4")


class ScanType(Enum):
    PASSIVE = "passive"
    ACTIVE = "active"
    SPIDER = "spider"
    AJAX_SPIDER = "ajax_spider"  # Better for SPAs
    FULL = "full"
    API = "api"  # Direct API endpoint scanning


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
    scan_duration_seconds: float
    error: Optional[str] = None


class ZAPSecurityScanner:
    """
    OWASP ZAP Security Scanner for scanning dynamically generated application URLs.
    
    Usage:
        scanner = ZAPSecurityScanner()
        result = scanner.scan_url("http://localhost:8000/api/sandbox-preview/my-app")
    """
    
    def __init__(
        self,
        zap_host: str = "127.0.0.1",
        zap_port: int = 8080,
        api_key: str = None  # Default to None for disabled key
    ):
        """
        Initialize the ZAP scanner.
        
        Args:
            zap_host: Host where ZAP daemon is running
            zap_port: Port for ZAP API
            api_key: ZAP API key (None if api.disablekey=true)
        """
        self.zap_host = zap_host
        self.zap_port = zap_port
        self.api_key = api_key
        self.zap_url = f"http://{zap_host}:{zap_port}"
        self.zap: Optional[ZAPv2] = None
        
    def _connect(self) -> bool:
        """Connect to the ZAP daemon."""
        if not ZAP_AVAILABLE:
            raise RuntimeError("ZAP library not installed. Run: pip install python-owasp-zap-v2.4")
        
        try:
            # Test connection to ZAP
            response = requests.get(f"{self.zap_url}/JSON/core/view/version/", timeout=5)
            if response.status_code != 200:
                return False
            
            # Initialize ZAP client - handle both with and without API key
            proxies = {
                'http': self.zap_url,
                'https': self.zap_url
            }
            
            if self.api_key:
                self.zap = ZAPv2(apikey=self.api_key, proxies=proxies)
            else:
                self.zap = ZAPv2(proxies=proxies)
                
            print(f"✅ Connected to ZAP at {self.zap_url}")
            return True
            
        except requests.exceptions.ConnectionError:
            return False
        except Exception as e:
            print(f"❌ ZAP connection error: {e}")
            return False
    
    def is_zap_running(self) -> bool:
        """Check if ZAP daemon is reachable."""
        try:
            response = requests.get(
                f"{self.zap_url}/JSON/core/view/version/",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def scan_url(
        self,
        target_url: str,
        scan_type: ScanType = ScanType.PASSIVE,
        max_spider_time: int = 60,
        max_scan_time: int = 300
    ) -> ScanResult:
        """
        Perform a security scan on the target URL.
        
        Args:
            target_url: The URL to scan (e.g., sandbox preview URL)
            scan_type: Type of scan to perform
            max_spider_time: Maximum time for spider in seconds
            max_scan_time: Maximum time for active scan in seconds
            
        Returns:
            ScanResult with alerts and statistics
        """
        start_time = time.time()
        
        # Check ZAP connection
        if not self.is_zap_running():
            return ScanResult(
                success=False,
                target_url=target_url,
                scan_type=scan_type.value,
                alerts=[],
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                informational_count=0,
                scan_duration_seconds=0,
                error=f"ZAP daemon not reachable at {self.zap_url}. Please start ZAP first."
            )
        
        # Connect to ZAP
        if not self._connect():
            return ScanResult(
                success=False,
                target_url=target_url,
                scan_type=scan_type.value,
                alerts=[],
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                informational_count=0,
                scan_duration_seconds=0,
                error="Failed to connect to ZAP"
            )
        
        try:
            print(f"🔍 Starting {scan_type.value} scan on: {target_url}")
            
            # Step 1: Access the target URL to generate traffic
            print("📡 Accessing target URL...")
            self.zap.urlopen(target_url)
            time.sleep(2)
            
            # Step 2: Use AJAX Spider for SPAs (BEST for React apps)
            if scan_type in [ScanType.AJAX_SPIDER, ScanType.FULL]:
                print("🌐 Starting AJAX Spider (for React/SPA)...")
                try:
                    self.zap.ajaxSpider.scan(target_url)
                    
                    ajax_start = time.time()
                    while self.zap.ajaxSpider.status == 'running':
                        if time.time() - ajax_start > max_spider_time:
                            print(f"⚠️ AJAX Spider timeout after {max_spider_time}s")
                            self.zap.ajaxSpider.stop()
                            break
                        results = self.zap.ajaxSpider.number_of_results
                        print(f"🌐 AJAX Spider found {results} resources...")
                        time.sleep(3)
                    
                    print(f"✅ AJAX Spider completed - found {self.zap.ajaxSpider.number_of_results} resources")
                except Exception as e:
                    print(f"⚠️ AJAX Spider not available: {e}, falling back to traditional spider")
                    scan_type = ScanType.SPIDER
            
            # Step 2b: Traditional Spider (fallback or explicit)
            if scan_type in [ScanType.SPIDER, ScanType.PASSIVE]:
                print("🕷️ Starting spider scan...")
                spider_scan_id = self.zap.spider.scan(target_url)
                
                # Wait for spider to complete
                spider_start = time.time()
                while int(self.zap.spider.status(spider_scan_id)) < 100:
                    if time.time() - spider_start > max_spider_time:
                        print(f"⚠️ Spider timeout after {max_spider_time}s")
                        break
                    progress = self.zap.spider.status(spider_scan_id)
                    print(f"🕷️ Spider progress: {progress}%")
                    time.sleep(2)
                
                print("✅ Spider scan completed")
            
            # Step 3: Wait for passive scan to complete
            print("🔎 Waiting for passive scan to complete...")
            passive_start = time.time()
            while int(self.zap.pscan.records_to_scan) > 0:
                if time.time() - passive_start > 60:  # 1 minute timeout for passive scan
                    print("⚠️ Passive scan timeout")
                    break
                records = self.zap.pscan.records_to_scan
                print(f"📊 Records to passive scan: {records}")
                time.sleep(2)
            
            print("✅ Passive scan completed")
            
            # Step 4: Active scan (if requested)
            if scan_type in [ScanType.ACTIVE, ScanType.FULL]:
                print("⚔️ Starting active scan...")
                active_scan_id = self.zap.ascan.scan(target_url)
                
                active_start = time.time()
                while int(self.zap.ascan.status(active_scan_id)) < 100:
                    if time.time() - active_start > max_scan_time:
                        print(f"⚠️ Active scan timeout after {max_scan_time}s")
                        break
                    progress = self.zap.ascan.status(active_scan_id)
                    print(f"⚔️ Active scan progress: {progress}%")
                    time.sleep(5)
                
                print("✅ Active scan completed")
            
            # Step 5: Get all alerts
            alerts = self.zap.core.alerts(baseurl=target_url)
            
            # Categorize alerts by risk level
            high_risk = [a for a in alerts if a.get('risk') == 'High']
            medium_risk = [a for a in alerts if a.get('risk') == 'Medium']
            low_risk = [a for a in alerts if a.get('risk') == 'Low']
            informational = [a for a in alerts if a.get('risk') == 'Informational']
            
            duration = time.time() - start_time
            
            print(f"\n📋 Scan Results for {target_url}")
            print(f"   🔴 High Risk: {len(high_risk)}")
            print(f"   🟠 Medium Risk: {len(medium_risk)}")
            print(f"   🟡 Low Risk: {len(low_risk)}")
            print(f"   🔵 Informational: {len(informational)}")
            print(f"   ⏱️ Duration: {duration:.2f}s")
            
            return ScanResult(
                success=True,
                target_url=target_url,
                scan_type=scan_type.value,
                alerts=alerts,
                high_risk_count=len(high_risk),
                medium_risk_count=len(medium_risk),
                low_risk_count=len(low_risk),
                informational_count=len(informational),
                scan_duration_seconds=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return ScanResult(
                success=False,
                target_url=target_url,
                scan_type=scan_type.value,
                alerts=[],
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                informational_count=0,
                scan_duration_seconds=duration,
                error=str(e)
            )
    
    def scan_api_endpoints(
        self,
        base_url: str,
        endpoints: List[str] = None,
        scan_type: ScanType = ScanType.ACTIVE,
        max_scan_time: int = 300
    ) -> ScanResult:
        """
        Scan API endpoints directly - BEST PRACTICE for React SPAs.
        The real attack surface is the backend API, not the React frontend.
        
        Args:
            base_url: Base API URL (e.g., http://localhost:8000/api)
            endpoints: List of API endpoints to scan (e.g., ['/login', '/users', '/upload'])
            scan_type: Type of scan (ACTIVE recommended for APIs)
            max_scan_time: Maximum time for scanning
            
        Returns:
            ScanResult with all findings
        """
        start_time = time.time()
        
        # Default common API endpoints if none provided
        if not endpoints:
            endpoints = [
                '/login', '/register', '/auth', '/token',
                '/users', '/user', '/profile', '/account',
                '/upload', '/files', '/download',
                '/admin', '/api', '/graphql',
                '/search', '/query', '/data',
                '/payment', '/checkout', '/orders',
                '/settings', '/config', '/webhook'
            ]
        
        if not self._connect():
            return ScanResult(
                success=False,
                target_url=base_url,
                scan_type="api",
                alerts=[],
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                informational_count=0,
                scan_duration_seconds=0,
                error="Failed to connect to ZAP"
            )
        
        all_alerts = []
        scanned_endpoints = []
        
        print(f"🔌 Starting API endpoint scan on: {base_url}")
        print(f"   Testing {len(endpoints)} endpoints...")
        
        try:
            for endpoint in endpoints:
                full_url = f"{base_url.rstrip('/')}{endpoint}"
                
                try:
                    # Access the endpoint
                    self.zap.urlopen(full_url)
                    scanned_endpoints.append(endpoint)
                    print(f"   ✓ Accessed: {endpoint}")
                except:
                    print(f"   ✗ Failed: {endpoint}")
                    continue
            
            time.sleep(2)  # Wait for traffic to be processed
            
            # Run active scan on discovered endpoints
            if scan_type == ScanType.ACTIVE and scanned_endpoints:
                print("⚔️ Starting active scan on API endpoints...")
                active_scan_id = self.zap.ascan.scan(base_url)
                
                active_start = time.time()
                while int(self.zap.ascan.status(active_scan_id)) < 100:
                    if time.time() - active_start > max_scan_time:
                        print(f"⚠️ Active scan timeout after {max_scan_time}s")
                        break
                    progress = self.zap.ascan.status(active_scan_id)
                    print(f"⚔️ Active scan progress: {progress}%")
                    time.sleep(5)
            
            # Wait for passive scan
            print("🔎 Waiting for passive scan...")
            passive_start = time.time()
            while int(self.zap.pscan.records_to_scan) > 0:
                if time.time() - passive_start > 60:
                    break
                time.sleep(2)
            
            # Get alerts
            alerts = self.zap.core.alerts(baseurl=base_url)
            
            # Categorize
            high_risk = [a for a in alerts if a.get('risk') == 'High']
            medium_risk = [a for a in alerts if a.get('risk') == 'Medium']
            low_risk = [a for a in alerts if a.get('risk') == 'Low']
            informational = [a for a in alerts if a.get('risk') == 'Informational']
            
            duration = time.time() - start_time
            
            print(f"\n📋 API Scan Results for {base_url}")
            print(f"   📌 Endpoints scanned: {len(scanned_endpoints)}")
            print(f"   🔴 High Risk: {len(high_risk)}")
            print(f"   🟠 Medium Risk: {len(medium_risk)}")
            print(f"   🟡 Low Risk: {len(low_risk)}")
            print(f"   🔵 Informational: {len(informational)}")
            print(f"   ⏱️ Duration: {duration:.2f}s")
            
            return ScanResult(
                success=True,
                target_url=base_url,
                scan_type="api",
                alerts=alerts,
                high_risk_count=len(high_risk),
                medium_risk_count=len(medium_risk),
                low_risk_count=len(low_risk),
                informational_count=len(informational),
                scan_duration_seconds=duration
            )
            
        except Exception as e:
            return ScanResult(
                success=False,
                target_url=base_url,
                scan_type="api",
                alerts=[],
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                informational_count=0,
                scan_duration_seconds=time.time() - start_time,
                error=str(e)
            )
    
    def get_alert_summary(self, alerts: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group alerts by type for easier analysis.
        
        Args:
            alerts: List of alert dictionaries from ZAP
            
        Returns:
            Dictionary with alerts grouped by alert type
        """
        summary = {}
        for alert in alerts:
            alert_type = alert.get('alert', 'Unknown')
            if alert_type not in summary:
                summary[alert_type] = []
            summary[alert_type].append({
                'risk': alert.get('risk'),
                'confidence': alert.get('confidence'),
                'url': alert.get('url'),
                'description': alert.get('description'),
                'solution': alert.get('solution'),
                'reference': alert.get('reference')
            })
        return summary
    
    def generate_report(self, result: ScanResult) -> str:
        """
        Generate a human-readable security report.
        
        Args:
            result: ScanResult from a scan
            
        Returns:
            Formatted report string
        """
        report = []
        
        # Header
        report.append("=" * 76)
        report.append("OWASP ZAP SECURITY ASSESSMENT REPORT")
        report.append("=" * 76)
        report.append("")
        
        # Scan Metadata
        report.append("SCAN CONFIGURATION")
        report.append("-" * 76)
        report.append(f"  Target URL      : {result.target_url}")
        report.append(f"  Scan Type       : {result.scan_type.upper()}")
        report.append(f"  Scan Duration   : {result.scan_duration_seconds:.2f} seconds")
        report.append(f"  Scan Status     : {'COMPLETED' if result.success else 'FAILED'}")
        report.append(f"  Timestamp       : {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append("")
        
        if result.error:
            report.append("SCAN ERROR")
            report.append("-" * 76)
            report.append(f"  {result.error}")
            report.append("")
        
        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 76)
        total_findings = result.high_risk_count + result.medium_risk_count + result.low_risk_count + result.informational_count
        report.append(f"  Total Findings  : {total_findings}")
        report.append("")
        report.append("  Risk Distribution:")
        report.append(f"    CRITICAL/HIGH   : {result.high_risk_count:>4}  {'[REQUIRES IMMEDIATE ATTENTION]' if result.high_risk_count > 0 else ''}")
        report.append(f"    MEDIUM          : {result.medium_risk_count:>4}  {'[RECOMMENDED TO ADDRESS]' if result.medium_risk_count > 0 else ''}")
        report.append(f"    LOW             : {result.low_risk_count:>4}")
        report.append(f"    INFORMATIONAL   : {result.informational_count:>4}")
        report.append("")
        
        # Calculate risk score
        risk_score = 100 - (result.high_risk_count * 25 + result.medium_risk_count * 10 + result.low_risk_count * 3 + result.informational_count * 1)
        risk_score = max(0, min(100, risk_score))
        if result.high_risk_count > 0:
            risk_rating = "CRITICAL"
        elif result.medium_risk_count > 0:
            risk_rating = "MODERATE"
        elif result.low_risk_count > 0:
            risk_rating = "LOW"
        else:
            risk_rating = "MINIMAL"
        report.append(f"  Security Score  : {risk_score}/100")
        report.append(f"  Risk Rating     : {risk_rating}")
        report.append("")
        
        if result.alerts:
            report.append("DETAILED FINDINGS")
            report.append("=" * 76)
            
            # Group by risk level
            finding_num = 1
            for risk_level in ['High', 'Medium', 'Low', 'Informational']:
                risk_alerts = [a for a in result.alerts if a.get('risk') == risk_level]
                if risk_alerts:
                    report.append("")
                    report.append(f"[{risk_level.upper()} RISK FINDINGS]")
                    report.append("-" * 76)
                    
                    for alert in risk_alerts:
                        report.append("")
                        report.append(f"Finding #{finding_num}: {alert.get('alert', 'Unknown')}")
                        report.append(f"  Severity      : {risk_level.upper()}")
                        report.append(f"  Confidence    : {alert.get('confidence', 'N/A')}")
                        
                        if alert.get('cweid'):
                            report.append(f"  CWE ID        : CWE-{alert.get('cweid')}")
                        if alert.get('wascid'):
                            report.append(f"  WASC ID       : WASC-{alert.get('wascid')}")
                        
                        report.append(f"  Affected URL  : {alert.get('url', 'N/A')}")
                        
                        if alert.get('param'):
                            report.append(f"  Parameter     : {alert.get('param')}")
                        
                        if alert.get('evidence'):
                            evidence = alert.get('evidence', '')[:200]
                            report.append(f"  Evidence      : {evidence}")
                        
                        if alert.get('description'):
                            desc = alert.get('description', '').replace('\n', ' ').strip()
                            # Word wrap description at 70 chars
                            desc_lines = [desc[i:i+60] for i in range(0, len(desc), 60)]
                            report.append(f"  Description   : {desc_lines[0] if desc_lines else 'N/A'}")
                            for line in desc_lines[1:4]:  # Limit to 4 lines
                                report.append(f"                  {line}")
                        
                        if alert.get('solution'):
                            solution = alert.get('solution', '').replace('\n', ' ').strip()
                            sol_lines = [solution[i:i+60] for i in range(0, len(solution), 60)]
                            report.append(f"  Remediation   : {sol_lines[0] if sol_lines else 'N/A'}")
                            for line in sol_lines[1:3]:  # Limit to 3 lines
                                report.append(f"                  {line}")
                        
                        if alert.get('reference'):
                            refs = alert.get('reference', '').split('\n')[:2]  # First 2 references
                            report.append(f"  References    : {refs[0] if refs else 'N/A'}")
                            for ref in refs[1:]:
                                if ref.strip():
                                    report.append(f"                  {ref.strip()}")
                        
                        finding_num += 1
        
        # Recommendations section
        report.append("")
        report.append("RECOMMENDATIONS")
        report.append("=" * 76)
        if result.high_risk_count > 0:
            report.append("  [PRIORITY 1] Address all HIGH risk findings immediately.")
            report.append("               These vulnerabilities may lead to data breach or system compromise.")
        if result.medium_risk_count > 0:
            report.append("  [PRIORITY 2] Review and remediate MEDIUM risk findings within 30 days.")
            report.append("               These issues could be exploited under certain conditions.")
        if result.low_risk_count > 0:
            report.append("  [PRIORITY 3] Address LOW risk findings as part of regular maintenance.")
        if result.informational_count > 0:
            report.append("  [INFO] Review informational findings to improve security posture.")
        if total_findings == 0:
            report.append("  No vulnerabilities detected. Continue regular security assessments.")
        
        # Footer
        report.append("")
        report.append("=" * 76)
        report.append("END OF REPORT")
        report.append("Generated by OWASP ZAP Security Scanner")
        report.append("=" * 76)
        
        return "\n".join(report)


# FastAPI endpoint integration
def create_scanner_endpoint():
    """
    Create a FastAPI endpoint for security scanning.
    Add this to your main.py routes.
    """
    endpoint_code = '''
from scanner_service import ZAPSecurityScanner, ScanType, ScanResult

@app.post("/api/security-scan")
async def run_security_scan(request: dict = Body(...)):
    """
    Run a security scan on a generated application URL.
    
    Request body:
        - target_url: The sandbox preview URL to scan
        - scan_type: "passive", "active", "spider", or "full" (default: passive)
        - zap_api_key: Optional custom ZAP API key
    """
    target_url = request.get("target_url")
    scan_type_str = request.get("scan_type", "passive")
    api_key = request.get("zap_api_key", "changeme")
    
    if not target_url:
        raise HTTPException(status_code=400, detail="target_url is required")
    
    # Map string to enum
    scan_type_map = {
        "passive": ScanType.PASSIVE,
        "active": ScanType.ACTIVE,
        "spider": ScanType.SPIDER,
        "full": ScanType.FULL
    }
    scan_type = scan_type_map.get(scan_type_str, ScanType.PASSIVE)
    
    # Initialize scanner
    scanner = ZAPSecurityScanner(api_key=api_key)
    
    # Check if ZAP is running
    if not scanner.is_zap_running():
        return {
            "success": False,
            "error": "ZAP daemon not running. Please start OWASP ZAP and enable the API.",
            "instructions": [
                "1. Download OWASP ZAP from https://www.zaproxy.org/download/",
                "2. Start ZAP in daemon mode: zap.sh -daemon -port 8080",
                "3. Or start ZAP GUI and go to Tools > Options > API to enable API",
                "4. Set API key or use 'changeme' as default"
            ]
        }
    
    # Run scan
    result = scanner.scan_url(target_url, scan_type)
    
    return {
        "success": result.success,
        "target_url": result.target_url,
        "scan_type": result.scan_type,
        "duration_seconds": result.scan_duration_seconds,
        "summary": {
            "high_risk": result.high_risk_count,
            "medium_risk": result.medium_risk_count,
            "low_risk": result.low_risk_count,
            "informational": result.informational_count,
            "total_alerts": len(result.alerts)
        },
        "alerts": result.alerts[:50],  # Limit response size
        "error": result.error,
        "report": scanner.generate_report(result) if result.success else None
    }
'''
    return endpoint_code


# Example usage and testing
if __name__ == "__main__":
    # Example: Scan a sandbox preview URL
    test_url = "http://localhost:8000/api/sandbox-preview/e-commerce-sell-dairy-733439?v=1767546626238&user_email=trishajanath%40gmail.com&user_id_alt=69185f9403d5c9719c80c17a"
    
    print("OWASP ZAP Security Scanner")
    print("=" * 50)
    
    # Initialize scanner
    scanner = ZAPSecurityScanner(api_key="changeme")
    
    # Check if ZAP is running
    if not scanner.is_zap_running():
        print("\n[ERROR] ZAP daemon is not running")
        print("\nSetup Instructions:")
        print("  1. Download from: https://www.zaproxy.org/download/")
        print("  2. Run in daemon mode: zap.sh -daemon -port 8080")
        print("  3. Or start ZAP GUI and enable API in Tools > Options > API")
        print("\nDocker Alternative:")
        print("  docker run -u zap -p 8080:8080 -d owasp/zap2docker-stable zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true -config api.key=changeme")
    else:
        print(f"\n[OK] ZAP is running at {scanner.zap_url}")
        print(f"\nTarget: {test_url[:80]}...")
        
        # Run passive scan
        result = scanner.scan_url(test_url, ScanType.PASSIVE)
        
        # Print report
        print(scanner.generate_report(result))
