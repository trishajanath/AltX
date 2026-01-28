# SOC2 Scanner Rewrite: From Misleading "Compliance" to Honest "Readiness"

## Summary of Changes

This document describes the complete rewrite of the SOC2 scanner to address fundamental flaws that were producing misleading results.

## Problems Identified

### 1. False Positives
**Old behavior:** `os.getenv("SECRET_KEY", "default_secret")` was marked as ✅ "Secrets managed via environment variables"

**Reality:** The hardcoded fallback `"default_secret"` IS in the code - this is a **CRITICAL SOC2 violation**

### 2. String Matching vs. Actual Enforcement
**Old behavior:** Finding `https://` URLs was marked as TLS compliance

**Reality:** SOC2 CC6.7 requires:
- TLS 1.2+ enforced server-side
- HSTS headers
- Certificate management
- No mixed content

Code scanning **cannot verify** any of this.

### 3. Confusing Code Hints with Operational Controls
**Old behavior:** `console.error` override was marked as "monitoring"

**Reality:** SOC2 CC7.2 requires:
- SIEM integration
- Alert routing
- Log retention policies
- 24/7 monitoring SLAs

### 4. Unrealistic Scoring
**Old behavior:** Could achieve 100% "FULLY_COMPLIANT" from code alone

**Reality:** A project with:
- 21 files
- No infrastructure configs
- No IAM policies
- No monitoring setup

...should never be "100% compliant"

---

## New Design: Readiness Assessment

### Key Principles

1. **Renamed from "Compliance" to "Readiness"** - This is an assessment tool, not a certification
2. **Maximum 50% from code alone** - Operational evidence is the other 50%
3. **Strict pattern detection** - Catches `os.getenv(key, default)` as CRITICAL
4. **Operational controls always marked MISSING** - Until evidence artifacts are provided

### New Severity Scoring

```
CRITICAL violations: -15 points each (e.g., hardcoded secrets, eval())
HIGH violations:      -8 points each (e.g., XSS, localStorage tokens)
MEDIUM violations:    -4 points each (e.g., empty catch blocks)
LOW violations:       -1 point each  (e.g., debug code)
```

### New Readiness Levels

| Level | Score Range | Meaning |
|-------|-------------|---------|
| `NOT_READY` | 0-24% | Significant security work needed |
| `EARLY_STAGE` | 25-39% | Basic patterns in place, many gaps |
| `PARTIAL_READINESS` | 40-50% | Good code hygiene, needs operational evidence |

**Note:** Maximum possible score from code alone is 50%. To reach higher scores, operational evidence artifacts must be provided (IAM policies, monitoring configs, IR plans, etc.)

### Security Patterns Detected

| Pattern | Severity | What It Catches |
|---------|----------|-----------------|
| `secret_with_fallback` | CRITICAL | `os.getenv("KEY", "default_value")` - the fallback IS in code! |
| `hardcoded_secret` | CRITICAL | `password = "hunter2"` |
| `eval_exec` | CRITICAL | `eval()` or `exec()` calls |
| `xss` | HIGH | `dangerouslySetInnerHTML`, `innerHTML =` |
| `ssl_disabled` | CRITICAL | `verify=False`, `rejectUnauthorized: false` |
| `http_plaintext` | HIGH | Non-localhost HTTP URLs |
| `localstorage_auth` | HIGH | Auth tokens in localStorage |
| `empty_catch` | MEDIUM | Swallowed errors |
| `debug_code` | LOW | `debugger;`, `console.debug` |

### Operational Controls (Always Missing Without Evidence)

| Control | Name | Required Evidence |
|---------|------|-------------------|
| CC6.1 | Access Control | IAM policies, access reviews, MFA config |
| CC6.6 | System Protection | WAF config, firewall rules |
| CC6.7 | Transmission Security | TLS 1.2+ config, HSTS, cert management |
| CC7.1 | Vulnerability Management | Scan reports, pen test results |
| CC7.2 | Security Monitoring | SIEM config, alerts, log retention policy |
| CC7.3 | Incident Response | IR plan, postmortems, communication procedures |
| CC8.1 | Change Management | Change policy, code review requirements |
| CC9.1 | Vendor Risk | Vendor inventory, security assessments |

---

## New API Response Format

```json
{
  "success": true,
  "project_name": "my-project",
  "assessment_type": "SOC2_READINESS_SCAN",
  
  "disclaimer": {
    "title": "⚠️ READINESS Assessment - NOT Compliance Certification",
    "text": "SOC2 is an operational trust framework requiring evidence artifacts...",
    "checks": ["Code vulnerabilities", "Hardcoded secrets", "Dangerous patterns"],
    "cannot_verify": ["IAM policies", "TLS enforcement", "Monitoring/alerting", "Incident response"]
  },
  
  "readiness_score": 35,
  "readiness_level": "EARLY_STAGE",
  "max_possible_score": 50,
  "audit_ready": false,
  
  "score_breakdown": {
    "code_security": { "score": 35, "max": 50, "deductions": "Critical:-15 High:-0 Med:-0 Low:-0" },
    "operational_evidence": { "score": 0, "max": 50, "reason": "No evidence artifacts provided" }
  },
  
  "controls_assessment": {
    "CC6.1": {
      "name": "Access Control",
      "code_status": "HAS_ISSUES",
      "ops_status": "MISSING",
      "overall": "FAILING",
      "findings": 2,
      "required_evidence": ["IAM policies", "Access reviews", "MFA config"]
    }
  },
  
  "code_vulnerabilities": [
    {
      "id": "VULN-0001",
      "type": "secret_with_fallback",
      "file": "backend/auth.py",
      "line": 12,
      "severity": "CRITICAL",
      "description": "Secret with hardcoded fallback - SOC2 violation",
      "why_critical": "Default values mean secrets ARE in code. SOC2 requires no production secrets in code.",
      "remediation": "Use os.environ[\"KEY\"] to crash if missing, or use secrets manager"
    }
  ],
  
  "critical_gaps": [
    { "priority": 1, "gap": "Secrets Management", "count": 3, "fix": "Use os.environ[] or secrets manager" },
    { "priority": 2, "gap": "Operational Evidence", "issue": "8 controls missing evidence", "fix": "Prepare IAM, monitoring, IR docs" }
  ],
  
  "limitations": [
    "Cannot verify runtime behavior",
    "Cannot verify production configs",
    "Cannot verify operational procedures",
    "Pattern matching may have false positives"
  ]
}
```

---

## Files Changed

### Backend
- [main.py](backend/main.py#L1688-L1940) - Complete rewrite of `/api/projects/{project_name}/compliance` endpoint

### Frontend
- [MonacoProjectEditor.jsx](frontend/src/components/MonacoProjectEditor.jsx) - Updated modal to display new response format:
  - Added disclaimer banner
  - Changed "Compliance Score" → "Readiness Score" 
  - Changed "Compliance Level" → "Readiness Level"
  - Added Score Breakdown section (code vs operational)
  - Added controls with Code Status / Ops Status / Required Evidence
  - Added Critical Gaps section
  - Added Limitations warning
  - Updated footer text

---

## Expected Output for This Project

For the AltX codebase itself, the scanner should now produce:

```
Readiness Score: 30-45%
Readiness Level: EARLY_STAGE or PARTIAL_READINESS
Audit Ready: ❌ No

Critical Gaps:
1. Secrets Management (if os.getenv with defaults found)
2. Operational Evidence (all 8 controls MISSING)
3. TLS Enforcement (no evidence)
4. Monitoring (no SIEM/alerting)

Controls Status:
- CC6.1 Access Control: Ops: ✗ MISSING
- CC6.7 Transmission Security: Ops: ✗ MISSING
- CC7.2 Security Monitoring: Ops: ✗ MISSING
...all marked as NOT_VERIFIED or FAILING
```

This is **honest** - it tells you what you actually need to do, rather than falsely claiming compliance.
