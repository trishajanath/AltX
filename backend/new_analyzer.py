import json

def analyze_scan_with_llm_new(https: bool, flags: List[str], headers: Dict[str, str], model_type: str = 'fast') -> str:
    """Generates a detailed security report with structured containers."""
    from backend.ai_assistant import get_model
    
    model = get_model(model_type)
    if not model:
        return f"AI model ({model_type}) is not available."

    # Calculate security metrics
    total_headers = 6  # Essential security headers
    present_headers = len(headers) if headers else 0
    critical_issues = len(flags)
    
    # Determine security level
    if https and present_headers >= 4 and critical_issues == 0:
        security_level = "High"
        security_score = 85 + (present_headers * 2)
    elif https and present_headers >= 2:
        security_level = "Medium" 
        security_score = 60 + (present_headers * 3)
    else:
        security_level = "Low"
        security_score = max(20, 40 + (present_headers * 5))
    
    # Create structured analysis data
    analysis_data = {
        "summary": {
            "security_level": security_level,
            "security_score": min(100, security_score),
            "critical_issues": critical_issues,
            "immediate_action_required": "Yes" if not https or critical_issues > 0 else "No"
        },
        "implemented_features": [
            {"name": "HTTPS/SSL", "status": "✅ Enabled", "description": "Secure connection established"} if https else None,
            *[{"name": header, "status": "✅ Present", "description": f"Security header configured"} for header in headers.keys()],
            {"name": "Website Accessibility", "status": "✅ Working", "description": "Site is reachable and responsive"}
        ],
        "missing_features": [
            {"name": "HTTPS/SSL", "status": "❌ Missing", "description": "CRITICAL: No secure connection", "severity": "critical"} if not https else None,
            {"name": "Content-Security-Policy", "status": "❌ Missing", "description": "Vulnerable to XSS attacks", "severity": "high"} if not headers or 'content-security-policy' not in [h.lower() for h in headers.keys()] else None,
            {"name": "X-Frame-Options", "status": "❌ Missing", "description": "Vulnerable to clickjacking", "severity": "high"} if not headers or 'x-frame-options' not in [h.lower() for h in headers.keys()] else None,
            {"name": "X-Content-Type-Options", "status": "❌ Missing", "description": "Vulnerable to MIME sniffing", "severity": "medium"} if not headers or 'x-content-type-options' not in [h.lower() for h in headers.keys()] else None,
            {"name": "Strict-Transport-Security", "status": "❌ Missing", "description": "Vulnerable to downgrade attacks", "severity": "high"} if not headers or 'strict-transport-security' not in [h.lower() for h in headers.keys()] else None
        ],
        "vulnerabilities": [
            {"name": flag, "severity": "🚨 Critical", "description": "Security vulnerability detected"} for flag in flags
        ] if flags else [{"name": "No vulnerabilities", "severity": "✅ Clean", "description": "No critical vulnerabilities detected"}],
        "security_breakdown": {
            "https_ssl": {"score": 25 if https else 0, "max": 25, "status": "✅ Enabled" if https else "❌ Disabled"},
            "security_headers": {"score": min(30, present_headers * 5), "max": 30, "status": f"{present_headers}/{total_headers} headers"},
            "content_protection": {"score": 20 if present_headers >= 2 else 10, "max": 25, "status": "Partial" if present_headers > 0 else "None"},
            "network_security": {"score": 15 if https else 5, "max": 20, "status": "Good" if https else "Poor"}
        },
        "action_items": [
            {"priority": "🚨 CRITICAL", "action": "Enable HTTPS/SSL certificate", "description": "Most urgent security fix"} if not https else None,
            {"priority": "⚠️ HIGH", "action": "Implement missing security headers", "description": "Add CSP, X-Frame-Options, etc."},
            {"priority": "🔧 MEDIUM", "action": "Configure proper redirects", "description": "Ensure HTTP to HTTPS redirects"},
            {"priority": "📝 LOW", "action": "Schedule regular security scans", "description": "Maintain security posture"}
        ],
        "implementation_checklist": [
            {"task": "Enable HTTPS/SSL certificate", "completed": https, "priority": "critical"},
            {"task": "Add Content-Security-Policy header", "completed": headers and 'content-security-policy' in [h.lower() for h in headers.keys()], "priority": "high"},
            {"task": "Implement X-Frame-Options header", "completed": headers and 'x-frame-options' in [h.lower() for h in headers.keys()], "priority": "high"},
            {"task": "Configure X-Content-Type-Options header", "completed": headers and 'x-content-type-options' in [h.lower() for h in headers.keys()], "priority": "medium"},
            {"task": "Set up Strict-Transport-Security header", "completed": headers and 'strict-transport-security' in [h.lower() for h in headers.keys()], "priority": "high"},
            {"task": "Test all security implementations", "completed": False, "priority": "medium"}
        ]
    }
    
    # Filter out None values
    analysis_data["implemented_features"] = [f for f in analysis_data["implemented_features"] if f is not None]
    analysis_data["missing_features"] = [f for f in analysis_data["missing_features"] if f is not None]
    analysis_data["action_items"] = [a for a in analysis_data["action_items"] if a is not None]
    
    # Convert to formatted JSON string for the AI to use as a template
    structured_template = json.dumps(analysis_data, indent=2)
    
    # System prompt for generating formatted output
    system_prompt = """You are a senior cybersecurity expert. Based on the structured data provided, create a comprehensive, well-formatted security analysis that can be displayed in organized containers/boxes.

    FORMATTING REQUIREMENTS:
    - Create clear sections that can be displayed in separate containers
    - Use proper markdown formatting with clear headers
    - Include visual indicators (✅❌⚠️🚨) for easy scanning
    - Make each section self-contained and visually distinct
    - Focus on actionable recommendations
    """
    
    user_prompt = f"""
Based on this structured security analysis data:

{structured_template}

Create a comprehensive security report with the following container sections:

## 🛡️ Security Overview
[Summary with security level, score, and immediate status]

## 🔍 Feature Analysis
### ✅ Working Security Features
[List implemented features in a green success container]

### ❌ Missing Critical Features  
[List missing features in a red warning container]

### ⚠️ Needs Improvement
[List items needing attention in an orange warning container]

## 🚨 Vulnerability Report
[Detailed vulnerability information in a critical alert container]

## 📊 Security Score Breakdown
[Visual score breakdown that can be displayed in metric containers]

## 🎯 Action Plan
[Priority-ordered action items in a task container]

## ⚡ Implementation Checklist
[Checkable items in a checklist container]

Format each section clearly so it can be displayed in separate UI containers with appropriate styling.
"""

    try:
        response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
        return response.text.strip()
    except Exception as e:
        # Fallback to structured text format
        return f"""
## 🛡️ Security Overview
**Security Level:** {analysis_data['summary']['security_level']}
**Security Score:** {analysis_data['summary']['security_score']}/100
**Critical Issues:** {analysis_data['summary']['critical_issues']}
**Action Required:** {analysis_data['summary']['immediate_action_required']}

## ✅ Working Security Features
{chr(10).join([f"• {f['name']}: {f['description']}" for f in analysis_data['implemented_features']])}

## ❌ Missing Critical Features
{chr(10).join([f"• {f['name']}: {f['description']}" for f in analysis_data['missing_features']])}

## 🚨 Vulnerability Report
{chr(10).join([f"• {v['severity']}: {v['name']} - {v['description']}" for v in analysis_data['vulnerabilities']])}

## 📊 Security Score Breakdown
• HTTPS/SSL: {analysis_data['security_breakdown']['https_ssl']['score']}/{analysis_data['security_breakdown']['https_ssl']['max']}
• Security Headers: {analysis_data['security_breakdown']['security_headers']['score']}/{analysis_data['security_breakdown']['security_headers']['max']}
• Content Protection: {analysis_data['security_breakdown']['content_protection']['score']}/{analysis_data['security_breakdown']['content_protection']['max']}
• Network Security: {analysis_data['security_breakdown']['network_security']['score']}/{analysis_data['security_breakdown']['network_security']['max']}

## 🎯 Action Plan
{chr(10).join([f"{i+1}. {a['priority']}: {a['action']} - {a['description']}" for i, a in enumerate(analysis_data['action_items'])])}

## ⚡ Implementation Checklist
{chr(10).join([f"- [{'x' if c['completed'] else ' '}] {c['task']} ({c['priority']} priority)" for c in analysis_data['implementation_checklist']])}
"""
