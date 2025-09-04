#!/usr/bin/env python3
"""
Fetch OWASP Low-Code/No-Code Top 10 Security Risks and convert to PDF
This script collects comprehensive security guidance for low-code/no-code platforms
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import black, blue, red, green, darkblue

# OWASP Low-Code/No-Code Top 10 URLs
BASE_URL = "https://owasp.org/www-project-top-10-low-code-no-code-security-risks"
MAIN_URL = "https://owasp.org/www-project-top-10-low-code-no-code-security-risks/"

# Individual risk URLs
RISK_URLS = [
    "https://owasp.org/www-project-top-10-low-code-no-code-security-risks/content/2022/en/LCNC-SEC-01-Account-Impersonation",
    "https://owasp.org/www-project-top-10-low-code-no-code-security-risks/content/2022/en/LCNC-SEC-02-Authorization-Misuse",
    "https://owasp.org/www-project-top-10-low-code-no-code-security-risks/content/2022/en/LCNC-SEC-03-Data-Leakage-and-Unexpected-Consequences",
    "https://owasp.org/www-project-top-10-low-code-no-code-security-risks/content/2022/en/LCNC-SEC-04-Authentication-and-Secure-Communication-Failures",
    "https://owasp.org/www-project-top-10-low-code-no-code-security-risks/content/2022/en/LCNC-SEC-05-Security-Misconfiguration",
    "https://owasp.org/www-project-top-10-low-code-no-code-security-risks/content/2022/en/LCNC-SEC-06-Injection-Handling-Failures",
    "https://owasp.org/www-project-top-10-low-code-no-code-security-risks/content/2022/en/LCNC-SEC-07-Vulnerable-and-Untrusted-Components",
    "https://owasp.org/www-project-top-10-low-code-no-code-security-risks/content/2022/en/LCNC-SEC-08-Data-and-Secret-Handling-Failures",
    "https://owasp.org/www-project-top-10-low-code-no-code-security-risks/content/2022/en/LCNC-SEC-09-Asset-Management-Failures",
    "https://owasp.org/www-project-top-10-low-code-no-code-security-risks/content/2022/en/LCNC-SEC-10-Security-Logging-and-Monitoring-Failures"
]

def fetch_webpage_content(url, max_retries=3):
    """Fetch and parse webpage content"""
    for attempt in range(max_retries):
        try:
            print(f"📥 Fetching: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Extract main content
            content = soup.get_text()
            
            # Clean up the content
            lines = []
            for line in content.split('\n'):
                line = line.strip()
                if line and len(line) > 3:  # Filter out empty lines and very short ones
                    lines.append(line)
            
            return '\n'.join(lines)
            
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                print(f"❌ Failed to fetch {url} after {max_retries} attempts")
                return None

def create_owasp_lcnc_pdf():
    """Create comprehensive PDF from OWASP Low-Code/No-Code Top 10"""
    
    output_file = os.path.join('knowledge_base', 'owasp-low-code-no-code-top-10.pdf')
    
    print(f"📄 Creating OWASP Low-Code/No-Code Top 10 PDF...")
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Create styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=darkblue,
        alignment=1
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=12,
        textColor=red
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=8,
        textColor=green
    )
    
    risk_title_style = ParagraphStyle(
        'RiskTitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=16,
        spaceBefore=16,
        textColor=red
    )
    
    normal_style = styles['Normal']
    
    story = []
    
    # Title page
    story.append(Paragraph("OWASP Low-Code/No-Code Top 10", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Security Risks for Low-Code/No-Code Development Platforms", heading_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Source: https://owasp.org/www-project-top-10-low-code-no-code-security-risks/", normal_style))
    story.append(PageBreak())
    
    # Overview
    story.append(Paragraph("Overview", heading_style))
    overview_text = """
    Low-Code/No-Code development platforms provide a development environment used to create application software through a graphical user interface instead of traditional hand-coded computer programming. Such platforms reduce the amount of traditional hand-coding, enabling accelerated delivery of business applications.

    As Low-Code/No-Code platforms proliferate and become widely used by organizations, there is a clear and immediate need to create awareness around security and privacy risks related to applications developed on such platforms.

    The primary goal of the "OWASP Low-Code/No-Code Top 10" document is to provide assistance and education for organizations looking to adopt and develop Low-Code/No-Code applications. The guide provides information about what the most prominent security risks are for such applications, the challenges involved, and how to overcome them.
    """
    story.append(Paragraph(overview_text, normal_style))
    story.append(PageBreak())
    
    # Security Focus Areas
    story.append(Paragraph("Security Focus Areas", heading_style))
    focus_areas = [
        "Account impersonation and privilege escalation",
        "Authorization bypass and privilege misuse",
        "Data leakage and unintended consequences",
        "Authentication failures and communication security",
        "Security misconfigurations", 
        "Injection handling failures",
        "Vulnerable and untrusted components",
        "Data and secret handling failures",
        "Asset management failures",
        "Security logging and monitoring failures"
    ]
    
    for area in focus_areas:
        story.append(Paragraph(f"• {area}", normal_style))
    
    story.append(PageBreak())
    
    # The Top 10 List
    story.append(Paragraph("The OWASP Low-Code/No-Code Top 10", heading_style))
    
    top_10_list = [
        "LCNC-SEC-01: Account Impersonation",
        "LCNC-SEC-02: Authorization Misuse", 
        "LCNC-SEC-03: Data Leakage and Unexpected Consequences",
        "LCNC-SEC-04: Authentication and Secure Communication Failures",
        "LCNC-SEC-05: Security Misconfiguration",
        "LCNC-SEC-06: Injection Handling Failures",
        "LCNC-SEC-07: Vulnerable and Untrusted Components",
        "LCNC-SEC-08: Data and Secret Handling Failures",
        "LCNC-SEC-09: Asset Management Failures",
        "LCNC-SEC-10: Security Logging and Monitoring Failures"
    ]
    
    for i, risk in enumerate(top_10_list, 1):
        story.append(Paragraph(f"{i}. {risk}", normal_style))
    
    story.append(PageBreak())
    
    # Fetch detailed content for each risk
    for i, url in enumerate(RISK_URLS, 1):
        print(f"📥 Fetching detailed content for risk {i}/10...")
        
        content = fetch_webpage_content(url)
        if content:
            # Extract risk title
            risk_title = top_10_list[i-1]
            story.append(Paragraph(risk_title, risk_title_style))
            
            # Parse and format content
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if not line or len(line) < 3:
                    continue
                    
                # Skip navigation and footer content
                if any(skip in line.lower() for skip in ['edit on github', 'watch on github', 'star on github', 'corporate supporters', 'additional links', 'owasp foundation', 'creative commons']):
                    continue
                    
                # Detect sections
                if line.startswith('## '):
                    section_title = line.replace('## ', '')
                    if section_title not in ['Spotlight:', 'Corporate Supporters', 'Additional Links']:
                        story.append(Paragraph(section_title, subheading_style))
                        current_section = section_title
                elif line.startswith('### '):
                    subsection_title = line.replace('### ', '')
                    if 'Corporate' not in subsection_title and 'Spotlight' not in subsection_title:
                        story.append(Paragraph(subsection_title, subheading_style))
                elif line.startswith('# '):
                    continue  # Skip main titles as we already have them
                elif line.startswith('|'):
                    continue  # Skip table formatting
                elif line.startswith('http'):
                    continue  # Skip bare URLs
                elif len(line) > 20 and not line.startswith('[') and current_section not in ['Corporate Supporters', 'Additional Links']:
                    # Add regular content
                    story.append(Paragraph(line, normal_style))
                    story.append(Spacer(1, 6))
            
            story.append(PageBreak())
        
        # Add delay between requests
        time.sleep(1)
    
    # Build PDF
    try:
        doc.build(story)
        print(f"✅ Successfully created PDF: {output_file}")
        
        # Check file size
        pdf_size = os.path.getsize(output_file)
        print(f"📊 PDF size: {pdf_size / 1024:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        return False

def save_raw_content():
    """Save raw content to text file for RAG database"""
    
    output_file = os.path.join('knowledge_base', 'owasp-low-code-no-code-security.txt')
    
    print(f"📝 Saving raw content to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("OWASP Low-Code/No-Code Top 10 Security Risks\n")
        f.write("=" * 50 + "\n")
        f.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("Source: https://owasp.org/www-project-top-10-low-code-no-code-security-risks/\n\n")
        
        f.write("OVERVIEW:\n")
        f.write("Low-Code/No-Code development platforms provide development environments for creating applications through graphical interfaces instead of traditional programming. These platforms accelerate business application delivery but introduce unique security risks.\n\n")
        
        f.write("SECURITY FOCUS AREAS:\n")
        f.write("- Account impersonation and privilege escalation\n")
        f.write("- Authorization bypass and privilege misuse\n") 
        f.write("- Data leakage and unintended consequences\n")
        f.write("- Authentication failures and communication security\n")
        f.write("- Security misconfigurations\n")
        f.write("- Injection handling failures\n")
        f.write("- Vulnerable and untrusted components\n")
        f.write("- Data and secret handling failures\n")
        f.write("- Asset management failures\n")
        f.write("- Security logging and monitoring failures\n\n")
        
        # Fetch and save detailed content for each risk
        for i, url in enumerate(RISK_URLS, 1):
            print(f"📥 Fetching content for risk {i}/10...")
            
            content = fetch_webpage_content(url)
            if content:
                f.write(f"\n{'='*60}\n")
                f.write(f"LCNC-SEC-{i:02d}: Detailed Information\n")
                f.write(f"{'='*60}\n")
                f.write(f"Source: {url}\n\n")
                
                # Filter and clean content
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if (line and len(line) > 10 and 
                        not any(skip in line.lower() for skip in ['edit on github', 'corporate supporters', 'additional links', 'owasp foundation']) and
                        not line.startswith('http') and
                        not line.startswith('[')):
                        f.write(line + '\n')
                
                f.write('\n')
            
            time.sleep(1)  # Be respectful to the server
    
    print(f"✅ Raw content saved to: {output_file}")
    return True

def install_requirements():
    """Install required packages if not present"""
    try:
        import reportlab
        import requests
        from bs4 import BeautifulSoup
        return True
    except ImportError as e:
        print(f"📦 Installing missing packages: {e}")
        os.system("pip install reportlab requests beautifulsoup4")
        try:
            import reportlab
            import requests
            from bs4 import BeautifulSoup
            return True
        except ImportError:
            print("❌ Failed to install required packages")
            return False

if __name__ == "__main__":
    print("🔄 OWASP Low-Code/No-Code Top 10 to PDF Converter")
    print("=" * 55)
    
    # Check/install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Create knowledge_base directory if it doesn't exist
    os.makedirs('knowledge_base', exist_ok=True)
    
    # Save raw content for RAG
    print("\n📝 Step 1: Saving raw content for RAG database...")
    save_raw_content()
    
    # Create PDF
    print("\n📄 Step 2: Creating comprehensive PDF...")
    success = create_owasp_lcnc_pdf()
    
    if success:
        print("\n✅ OWASP Low-Code/No-Code Top 10 processing completed!")
        print("📝 Raw content saved for RAG database")
        print("📄 Professional PDF created")
        print("🚀 Ready for integration into your security knowledge base")
    else:
        print("\n❌ Processing failed")
        sys.exit(1)
