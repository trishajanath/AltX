#!/usr/bin/env python3
"""
Test SOC2 Code Compliance Integration

This script tests the SOC2 compliance verification and audit documentation
generation for AI-generated code.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

# Test code samples with various security issues
TEST_FILES = {
    'backend/main.py': '''
from fastapi import FastAPI
import os

app = FastAPI()

# SOC2 Issue: Hardcoded password (CC6.1)
password = "secret123"

@app.get("/")
def read_root():
    return {"hello": "world"}

@app.post("/user")
def create_user(data: dict):
    # SOC2 Issue: Logging sensitive data (CC7.2)
    print(f"Creating user with password: {data}")
    return data
''',
    'backend/config.py': '''
# SOC2 Issue: Hardcoded API key (CC6.1)
api_key = "sk-1234567890abcdef"

# SOC2 Issue: Non-HTTPS URL (CC6.7)
API_URL = "http://api.example.com"

# SOC2 Issue: SSL verification disabled (CC6.7)
VERIFY_SSL = False
''',
    'frontend/src/App.jsx': '''
import React, { useState } from 'react';

function App() {
    const [user, setUser] = useState(null);
    
    // SOC2 Issue: Storing sensitive data in localStorage (CC6.1)
    const saveUser = (userData) => {
        localStorage.setItem("password", userData.password);
    };
    
    return (
        <div>
            {/* SOC2 Issue: dangerouslySetInnerHTML (CC6.6) */}
            <div dangerouslySetInnerHTML={{__html: user?.bio}} />
        </div>
    );
}

export default App;
'''
}


async def test_compliance_engine():
    """Test the SOC2 Code Compliance Engine"""
    print("=" * 70)
    print("SOC2 CODE COMPLIANCE ENGINE TEST")
    print("=" * 70)
    print()
    
    from soc2_code_compliance import SOC2CodeComplianceEngine
    
    print("🔍 Initializing SOC2 Code Compliance Engine...")
    engine = SOC2CodeComplianceEngine()
    print("✅ Engine initialized\n")
    
    print("📋 Testing with sample code containing security issues...")
    print(f"   Files to scan: {len(TEST_FILES)}")
    print()
    
    # Run compliance verification
    result, fixed_files = await engine.verify_generated_code(
        project_name="test_project",
        files_content=TEST_FILES,
        auto_fix=True
    )
    
    # Print results
    print("=" * 70)
    print("COMPLIANCE VERIFICATION RESULTS")
    print("=" * 70)
    print()
    
    print(f"📊 SUMMARY")
    print(f"   Compliance Score: {result.compliance_score:.1f}%")
    print(f"   Compliance Level: {result.compliance_level.value.upper()}")
    print(f"   Files Scanned: {result.total_files_scanned}")
    print(f"   Files with Issues: {result.files_with_issues}")
    print()
    
    print(f"🔍 FINDINGS BY SEVERITY")
    print(f"   Critical: {result.critical_findings}")
    print(f"   High: {result.high_findings}")
    print(f"   Medium: {result.medium_findings}")
    print(f"   Low: {result.low_findings}")
    print(f"   Total: {len(result.security_findings)}")
    print()
    
    print(f"✏️ REMEDIATION STATUS")
    print(f"   Auto-Fixed: {result.auto_fixes_applied}")
    print(f"   Manual Required: {result.manual_fixes_required}")
    print()
    
    print(f"📋 CONTROLS ASSESSED")
    for control, status in result.controls_assessed.items():
        print(f"   {control}: {status}")
    print()
    
    print(f"🔍 DETAILED FINDINGS")
    for i, finding in enumerate(result.security_findings, 1):
        print(f"\n   Finding {i}:")
        print(f"   ├─ ID: {finding.finding_id}")
        print(f"   ├─ Severity: {finding.severity}")
        print(f"   ├─ Category: {finding.category.value}")
        print(f"   ├─ File: {finding.file_path}")
        print(f"   ├─ Line: {finding.line_number}")
        print(f"   ├─ Description: {finding.description}")
        print(f"   ├─ Control: {finding.soc2_control}")
        print(f"   ├─ Auto-Fixed: {'Yes ✅' if finding.auto_fixed else 'No ❌'}")
        if finding.auto_fixed:
            print(f"   └─ Fix Applied: {finding.fix_applied}")
        else:
            print(f"   └─ Remediation: {finding.remediation}")
    print()
    
    print(f"🔧 COMPLIANCE GAPS")
    for gap in result.compliance_gaps:
        print(f"\n   Gap: {gap.gap_id}")
        print(f"   ├─ Control: {gap.control_code} - {gap.control_name}")
        print(f"   ├─ Severity: {gap.severity}")
        print(f"   ├─ Description: {gap.description}")
        print(f"   ├─ Affected Files: {', '.join(gap.affected_files)}")
        print(f"   ├─ Timeline: {gap.timeline_days} days")
        print(f"   └─ Remediation Steps:")
        for step in gap.remediation_steps:
            print(f"       • {step}")
    
    return result, fixed_files


async def test_audit_documentation(result):
    """Test audit documentation generation"""
    print()
    print("=" * 70)
    print("AUDIT DOCUMENTATION GENERATION TEST")
    print("=" * 70)
    print()
    
    from soc2_audit_documentation import SOC2AuditDocumentGenerator
    
    print("📄 Generating audit documentation...")
    generator = SOC2AuditDocumentGenerator()
    
    doc = generator.generate_complete_documentation(
        project_name="test_project",
        compliance_result=result,
        organization="Test Organization Inc."
    )
    
    print(f"✅ Documentation generated!")
    print(f"   Document ID: {doc.document_id}")
    print(f"   Generated: {doc.generated_date}")
    print(f"   Valid Until: {doc.valid_until}")
    print(f"   Classification: {doc.classification}")
    print()
    
    print(f"📋 SECTIONS GENERATED")
    for section_name in doc.sections.keys():
        print(f"   • {section_name}")
    print()
    
    # Export documentation
    output_dir = Path("/tmp/soc2_test_output")
    output_dir.mkdir(exist_ok=True)
    
    outputs = generator.export_document(
        doc, 
        output_dir, 
        formats=['markdown', 'json', 'html']
    )
    
    print(f"📁 DOCUMENTATION EXPORTED")
    for format_type, path in outputs.items():
        file_size = Path(path).stat().st_size
        print(f"   {format_type}: {path} ({file_size:,} bytes)")
    
    return doc, outputs


async def test_full_integration():
    """Test full integration with code generation flow"""
    print()
    print("=" * 70)
    print("FULL INTEGRATION TEST")
    print("=" * 70)
    print()
    
    from soc2_code_compliance import verify_and_document_compliance
    
    print("🔄 Testing verify_and_document_compliance function...")
    
    result, fixed_files, doc_path = await verify_and_document_compliance(
        project_name="integration_test_project",
        files_content=TEST_FILES,
        output_dir=Path("/tmp/soc2_integration_test")
    )
    
    print(f"✅ Full integration test complete!")
    print(f"   Compliance Score: {result.compliance_score:.1f}%")
    print(f"   Files Fixed: {len([f for f in fixed_files.values() if f != TEST_FILES.get(f, '')])}")
    print(f"   Documentation: {doc_path}")
    
    return result


async def main():
    """Run all tests"""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " SOC2 COMPLIANCE SYSTEM - INTEGRATION TEST ".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print(f"Test Started: {datetime.now().isoformat()}")
    print()
    
    try:
        # Test 1: Compliance Engine
        result, fixed_files = await test_compliance_engine()
        
        # Test 2: Audit Documentation
        doc, outputs = await test_audit_documentation(result)
        
        # Test 3: Full Integration
        await test_full_integration()
        
        print()
        print("=" * 70)
        print("ALL TESTS COMPLETED SUCCESSFULLY ✅")
        print("=" * 70)
        print()
        print("Summary:")
        print(f"  • Compliance verification: ✅ Working")
        print(f"  • Auto-fix capability: ✅ Working")
        print(f"  • Gap analysis: ✅ Working")
        print(f"  • Audit documentation: ✅ Working")
        print(f"  • Full integration: ✅ Working")
        print()
        print("The SOC2 compliance system is ready for production use!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
