
    
import requests

def scan_url(url):
    result = {
        "https": url.startswith("https"),
        "headers": {},
        "flags": [],
        "security_score": 0,
        "ssl_valid": False
    }
    
    try:
        res = requests.get(url, timeout=5)
        headers = res.headers
        result["headers"] = dict(headers)

        # Calculate security score
        score = 0
        
        # HTTPS check (25 points)
        if result["https"]:
            score += 25
            result["ssl_valid"] = True
        
        # Security headers check (up to 50 points)
        security_headers = {
            "Content-Security-Policy": {"points": 10, "description": "Missing Content-Security-Policy header - vulnerable to XSS attacks"},
            "Strict-Transport-Security": {"points": 10, "description": "Missing Strict-Transport-Security header - vulnerable to protocol downgrade attacks"},
            "X-Frame-Options": {"points": 8, "description": "Missing X-Frame-Options header - vulnerable to clickjacking attacks"},
            "X-XSS-Protection": {"points": 6, "description": "Missing X-XSS-Protection header - reduced XSS protection"},
            "X-Content-Type-Options": {"points": 6, "description": "Missing X-Content-Type-Options header - vulnerable to MIME sniffing attacks"},
            "Referrer-Policy": {"points": 5, "description": "Missing Referrer-Policy header - potential information leakage"},
            "Permissions-Policy": {"points": 5, "description": "Missing Permissions-Policy header - limited browser feature control"}
        }
        
        for header, config in security_headers.items():
            if header not in headers:
                result["flags"].append(config["description"])
            else:
                score += config["points"]
        
        # Additional security checks
        if not result["https"]:
            result["flags"].append("🚨 CRITICAL: Website does not use HTTPS - data transmitted in plain text")
            score = max(0, score - 25)  # Heavy penalty for no HTTPS
        
        # Check for server information disclosure
        if "Server" in headers:
            server_info = headers["Server"]
            if any(version in server_info.lower() for version in ["apache", "nginx", "iis"]):
                # This is normal, but we could add version checking in the future
                pass
        
        # Check for security-related headers that are good to have
        good_headers = ["X-Permitted-Cross-Domain-Policies", "Cross-Origin-Embedder-Policy", "Cross-Origin-Opener-Policy"]
        for header in good_headers:
            if header in headers:
                score += 2  # Bonus points for additional security headers
        
        # Set final security score
        result["security_score"] = min(100, max(0, score))
        
        # Add summary based on score
        if result["security_score"] >= 80:
            result["security_level"] = "Excellent"
        elif result["security_score"] >= 60:
            result["security_level"] = "Good"
        elif result["security_score"] >= 40:
            result["security_level"] = "Fair"
        else:
            result["security_level"] = "Poor"
            
    except Exception as e:
        result["flags"].append(f"❌ Request failed: {e}")
        result["security_score"] = 0
        result["security_level"] = "Error"

    return result
