def analyze_scan_with_llm(https: bool, flags: List[str], headers: Dict[str, str], model_type: str = 'fast') -> str:
    """Generates a detailed security report based on scan results using an LLM."""
    model = get_model(model_type)
    if not model:
        return f"AI model ({model_type}) is not available."

    # System prompt defines the AI's persona and expertise
    system_prompt = """You are a senior cybersecurity expert. Provide comprehensive security analysis with detailed checkmarks.
    
    FORMATTING REQUIREMENTS:
    - Use clear checkmarks: ✅ for implemented features, ❌ for missing features, ⚠️ for needs improvement, 🚨 for vulnerabilities
    - Format with proper markdown and line breaks
    - Make each section clearly separated and easy to scan
    - Provide actionable recommendations with implementation steps
    """
    
    # User prompt provides the scan data and requests a specific report format
    user_prompt = f"""
SECURITY SCAN RESULTS:
- HTTPS Status: {'✅ Enabled' if https else '❌ Not Enabled'}
- Vulnerabilities Found: {len(flags)} issues
- Security Issues: {flags if flags else 'None detected'}
- Headers Analyzed: {len(headers.keys()) if headers else 0}
- Present Headers: {list(headers.keys()) if headers else 'None'}

Please provide a COMPREHENSIVE security analysis with detailed checkmarks:

## 🛡️ Security Analysis Summary

### 📊 Overall Security Status
• **Security Level:** [High/Medium/Low]
• **Critical Issues:** {len(flags)} found  
• **Immediate Action Required:** [Yes/No]
• **Security Score:** [X]/100

### 🔍 Security Features Checklist

#### ✅ IMPLEMENTED FEATURES (Working Well)
{"✅ **HTTPS/SSL:** Properly configured and enabled" if https else ""}
{chr(10).join([f"✅ **{header}:** Present and configured" for header in headers.keys()]) if headers else ""}
• ✅ **Website Accessibility:** Site is reachable and responsive

#### ❌ MISSING CRITICAL FEATURES
{"❌ **HTTPS/SSL:** Not implemented - CRITICAL security vulnerability" if not https else ""}
{"❌ **Content-Security-Policy:** Missing - Vulnerable to XSS attacks" if not headers or 'content-security-policy' not in [h.lower() for h in headers.keys()] else ""}
{"❌ **X-Frame-Options:** Missing - Vulnerable to clickjacking" if not headers or 'x-frame-options' not in [h.lower() for h in headers.keys()] else ""}
{"❌ **X-Content-Type-Options:** Missing - Vulnerable to MIME sniffing" if not headers or 'x-content-type-options' not in [h.lower() for h in headers.keys()] else ""}
{"❌ **Strict-Transport-Security:** Missing - Vulnerable to downgrade attacks" if not headers or 'strict-transport-security' not in [h.lower() for h in headers.keys()] else ""}

#### ⚠️ NEEDS IMPROVEMENT
• ⚠️ **Security Headers Coverage:** {len(headers) if headers else 0}/6 essential headers implemented
• ⚠️ **Certificate Validation:** Requires verification if HTTPS is enabled
• ⚠️ **HTTP to HTTPS Redirects:** Need proper redirect configuration

### 🚨 VULNERABILITIES DETECTED
{chr(10).join([f"🚨 **CRITICAL VULNERABILITY:** {flag}" for flag in flags]) if flags else '✅ **No critical vulnerabilities detected in scan**'}

### 🛡️ Detailed Security Headers Analysis

#### ✅ Present Headers:
{chr(10).join([f"✅ **{header}:** {value[:50]}..." for header, value in headers.items()]) if headers else '❌ **No security headers detected**'}

#### ❌ Missing Essential Headers:
• ❌ **Content-Security-Policy (CSP):** Prevents XSS and code injection attacks
• ❌ **X-Frame-Options:** Prevents clickjacking and iframe embedding attacks  
• ❌ **X-Content-Type-Options:** Prevents MIME type sniffing vulnerabilities
• ❌ **Strict-Transport-Security (HSTS):** Enforces HTTPS and prevents downgrade attacks
• ❌ **Referrer-Policy:** Controls referrer information leakage
• ❌ **Permissions-Policy:** Controls browser feature access

### 🎯 Priority Action Items
1. **🚨 CRITICAL:** [Most urgent security fix - typically HTTPS implementation]
2. **⚠️ HIGH:** [Important security headers implementation]  
3. **🔧 MEDIUM:** [Security configuration improvements]
4. **📝 LOW:** [Optional security enhancements]

### 📊 Detailed Security Score Breakdown
**Overall Security Score: [X]/100**
• **🔒 HTTPS/SSL Security:** [X]/25 - {"✅ Enabled" if https else "❌ Not Enabled"}
• **🛡️ Security Headers:** [X]/30 - {len(headers) if headers else 0}/6 headers present
• **🔐 Content Protection:** [X]/25 - CSP and frame protection status
• **🌐 Network Security:** [X]/20 - Certificate and transport security

### ⚡ Quick Implementation Checklist
- [ ] **Enable HTTPS/SSL certificate** (Let's Encrypt recommended)
- [ ] **Add Content-Security-Policy header** 
- [ ] **Implement X-Frame-Options header**
- [ ] **Configure X-Content-Type-Options header**
- [ ] **Set up Strict-Transport-Security header**
- [ ] **Configure HTTP to HTTPS redirects**
- [ ] **Test all security implementations**
- [ ] **Schedule regular security scans**

### 🔧 Implementation Code Examples
[Provide specific code examples for missing headers and HTTPS setup]

IMPORTANT: Use clear checkmarks (✅❌⚠️🚨) and provide specific, actionable recommendations with implementation steps.
"""

    try:
        response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
        
        # Post-process the response to ensure proper formatting
        formatted_response = response.text.strip()
        
        # Add proper line breaks after headers and sections
        formatted_response = formatted_response.replace('##', '\n\n##')
        formatted_response = formatted_response.replace('###', '\n\n###')
        formatted_response = formatted_response.replace('####', '\n\n####')
        formatted_response = formatted_response.replace('• ', '\n• ')
        formatted_response = formatted_response.replace('- [ ]', '\n- [ ]')
        formatted_response = formatted_response.replace('1. ', '\n1. ')
        formatted_response = formatted_response.replace('2. ', '\n2. ')
        formatted_response = formatted_response.replace('3. ', '\n3. ')
        formatted_response = formatted_response.replace('4. ', '\n4. ')
        formatted_response = formatted_response.replace('5. ', '\n5. ')
        
        # Clean up multiple consecutive line breaks
        while '\n\n\n' in formatted_response:
            formatted_response = formatted_response.replace('\n\n\n', '\n\n')
        
        return formatted_response.strip()
    except Exception as e:
        return f"API Error: {str(e)}"
