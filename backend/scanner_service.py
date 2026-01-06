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
    FULL = "full"


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
            
            # Step 2: Spider the application to discover all endpoints
            if scan_type in [ScanType.SPIDER, ScanType.PASSIVE, ScanType.FULL]:
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
        report.append("=" * 60)
        report.append("🔐 OWASP ZAP SECURITY SCAN REPORT")
        report.append("=" * 60)
        report.append(f"\n📍 Target URL: {result.target_url}")
        report.append(f"📋 Scan Type: {result.scan_type}")
        report.append(f"⏱️ Duration: {result.scan_duration_seconds:.2f} seconds")
        report.append(f"✅ Success: {result.success}")
        
        if result.error:
            report.append(f"\n❌ Error: {result.error}")
        
        report.append("\n" + "-" * 40)
        report.append("📊 RISK SUMMARY")
        report.append("-" * 40)
        report.append(f"🔴 High Risk:      {result.high_risk_count}")
        report.append(f"🟠 Medium Risk:    {result.medium_risk_count}")
        report.append(f"🟡 Low Risk:       {result.low_risk_count}")
        report.append(f"🔵 Informational:  {result.informational_count}")
        
        if result.alerts:
            report.append("\n" + "-" * 40)
            report.append("🚨 DETAILED ALERTS")
            report.append("-" * 40)
            
            # Group by risk level
            for risk_level in ['High', 'Medium', 'Low', 'Informational']:
                risk_alerts = [a for a in result.alerts if a.get('risk') == risk_level]
                if risk_alerts:
                    report.append(f"\n{'🔴' if risk_level == 'High' else '🟠' if risk_level == 'Medium' else '🟡' if risk_level == 'Low' else '🔵'} {risk_level} Risk Alerts:")
                    for alert in risk_alerts[:5]:  # Limit to 5 per category
                        report.append(f"\n  • {alert.get('alert', 'Unknown')}")
                        report.append(f"    URL: {alert.get('url', 'N/A')[:80]}...")
                        report.append(f"    Confidence: {alert.get('confidence', 'N/A')}")
                        if alert.get('solution'):
                            report.append(f"    Solution: {alert.get('solution', '')[:100]}...")
        
        report.append("\n" + "=" * 60)
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
    
    print("🔐 OWASP ZAP Security Scanner")
    print("=" * 50)
    
    # Initialize scanner
    scanner = ZAPSecurityScanner(api_key="changeme")
    
    # Check if ZAP is running
    if not scanner.is_zap_running():
        print("\n❌ ZAP daemon is not running!")
        print("\nTo start ZAP:")
        print("  1. Download from: https://www.zaproxy.org/download/")
        print("  2. Run in daemon mode: zap.sh -daemon -port 8080")
        print("  3. Or start ZAP GUI and enable API in Tools > Options > API")
        print("\nAlternatively, run ZAP with Docker:")
        print("  docker run -u zap -p 8080:8080 -d owasp/zap2docker-stable zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true -config api.key=changeme")
    else:
        print(f"\n✅ ZAP is running at {scanner.zap_url}")
        print(f"\n🎯 Scanning: {test_url[:80]}...")
        
        # Run passive scan
        result = scanner.scan_url(test_url, ScanType.PASSIVE)
        
        # Print report
        print(scanner.generate_report(result))
