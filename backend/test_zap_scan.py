"""Test ZAP Security Scanner on a sandbox preview URL"""
import sys
sys.path.insert(0, '.')

from scanner_service import ZAPSecurityScanner, ScanType

# Initialize scanner without API key (we disabled it in Docker)
scanner = ZAPSecurityScanner(api_key=None)

# Check if ZAP is running
print("🔍 Checking ZAP connection...")
if not scanner.is_zap_running():
    print("❌ ZAP is not running!")
    print("\nMake sure ZAP Docker container is running:")
    print("  docker ps | grep zap")
    sys.exit(1)

print("✅ ZAP is running!")

# Test scan on a sample URL - update this to your actual preview URL
target_url = "http://host.docker.internal:8000/api/sandbox-preview/e-commerce-sell-dairy-733439"

print(f"\n🎯 Target URL: {target_url}")
print("🔍 Starting passive security scan...")
print("   (This may take 1-2 minutes)\n")

# Run the scan
result = scanner.scan_url(target_url, scan_type=ScanType.PASSIVE)

# Print results
if result.success:
    print("\n" + "=" * 60)
    print("📊 SCAN RESULTS")
    print("=" * 60)
    print(f"🔴 High Risk:      {result.high_risk_count}")
    print(f"🟠 Medium Risk:    {result.medium_risk_count}")
    print(f"🟡 Low Risk:       {result.low_risk_count}")
    print(f"🔵 Informational:  {result.informational_count}")
    print(f"⏱️  Duration:       {result.scan_duration_seconds:.2f}s")
    
    if result.alerts:
        print("\n" + "-" * 60)
        print("⚠️  TOP ALERTS:")
        print("-" * 60)
        
        # Group by risk level
        for risk in ['High', 'Medium', 'Low']:
            risk_alerts = [a for a in result.alerts if a.get('risk') == risk]
            if risk_alerts:
                emoji = '🔴' if risk == 'High' else '🟠' if risk == 'Medium' else '🟡'
                print(f"\n{emoji} {risk} Risk:")
                for alert in risk_alerts[:3]:  # Show top 3 per category
                    print(f"   • {alert.get('alert', 'Unknown')}")
                    print(f"     URL: {alert.get('url', 'N/A')[:60]}...")
    
    # Generate full report
    print("\n" + "=" * 60)
    print("📋 FULL REPORT")
    print("=" * 60)
    print(scanner.generate_report(result))
else:
    print(f"\n❌ Scan failed: {result.error}")
