#!/usr/bin/env python3
"""
Convert SonarSource rules data to PDF format
This script creates a professional PDF from the rules data to avoid 9-minute web fetching
"""

import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import black, blue, red, green

def create_sonar_rules_pdf():
    """Convert sonar_rules_data.txt to a professional PDF"""
    
    # File paths
    input_file = os.path.join('knowledge_base', 'sonar_rules_data.txt')
    output_file = os.path.join('knowledge_base', 'sonar_security_rules.pdf')
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return False
    
    print(f"📄 Converting {input_file} to PDF...")
    
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
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        textColor=blue,
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=12,
        textColor=red
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=6,
        spaceBefore=6,
        textColor=green
    )
    
    rule_style = ParagraphStyle(
        'RuleStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        leftIndent=20
    )
    
    normal_style = styles['Normal']
    
    # Story (content) list
    story = []
    
    # Read and parse the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    # Parse content
    lines = content.split('\n')
    
    # Add title page
    story.append(Paragraph("SonarSource Security Rules Database", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Comprehensive Static Analysis Rules for Security & Code Quality", normal_style))
    story.append(PageBreak())
    
    current_language = None
    rule_count = 0
    
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
            
        # Title and headers
        if line.startswith("SonarSource Security Rules Database"):
            continue  # Already added
        elif line.startswith("=================================================="):
            continue
        elif line.startswith("Last Updated:"):
            story.append(Paragraph(f"<b>{line}</b>", normal_style))
        elif line.startswith("Languages Processed:") or line.startswith("Successful Fetches:") or line.startswith("Source:"):
            story.append(Paragraph(line, normal_style))
        elif line.startswith("OVERVIEW:"):
            story.append(Paragraph("Overview", heading_style))
        elif line.startswith("SECURITY FOCUS AREAS:"):
            story.append(Paragraph("Security Focus Areas", heading_style))
        elif line.startswith("LANGUAGE-SPECIFIC RULES:"):
            story.append(PageBreak())
            story.append(Paragraph("Language-Specific Security Rules", heading_style))
            
        # Language sections
        elif line.endswith("SECURITY RULES:") and "LANGUAGE-SPECIFIC" not in line:
            language = line.replace(" SECURITY RULES:", "")
            current_language = language
            story.append(PageBreak())
            story.append(Paragraph(f"{language} Security Rules", heading_style))
            rule_count = 0
            
        elif line.startswith("Found ") and "individual rules" in line:
            story.append(Paragraph(line, subheading_style))
            
        # Individual rules
        elif line.startswith("Rule "):
            rule_count += 1
            # Extract rule title (everything after "Rule X: ")
            if ":" in line:
                rule_title = line.split(":", 1)[1].strip()
                story.append(Paragraph(f"<b>Rule {rule_count}: {rule_title}</b>", rule_style))
            
        elif line.startswith("URL: "):
            url = line.replace("URL: ", "")
            story.append(Paragraph(f"URL: <link href='{url}'>{url}</link>", rule_style))
            
        elif line.startswith("Description: "):
            desc = line.replace("Description: ", "")
            story.append(Paragraph(f"Description: {desc}", rule_style))
            
        elif line.startswith("Language: "):
            lang = line.replace("Language: ", "")
            story.append(Paragraph(f"Language: <b>{lang}</b>", rule_style))
            story.append(Spacer(1, 6))
            
        elif line.startswith("------------------------------"):
            story.append(Spacer(1, 6))
            
        # Regular content lines
        elif line.startswith("- "):
            story.append(Paragraph(line, normal_style))
        elif len(line) > 0 and not line.startswith("Rule ") and not line.startswith("URL:") and not line.startswith("Description:") and not line.startswith("Language:"):
            story.append(Paragraph(line, normal_style))
    
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

def install_requirements():
    """Install required packages if not present"""
    try:
        import reportlab
        return True
    except ImportError:
        print("📦 Installing reportlab...")
        os.system("pip install reportlab")
        try:
            import reportlab
            return True
        except ImportError:
            print("❌ Failed to install reportlab")
            return False

if __name__ == "__main__":
    print("🔄 SonarSource Rules to PDF Converter")
    print("=====================================")
    
    # Check/install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Convert to PDF
    success = create_sonar_rules_pdf()
    
    if success:
        print("\n✅ Conversion completed successfully!")
        print("📝 The PDF will now be used instead of web fetching")
        print("⚡ This will reduce loading time from 9 minutes to seconds")
    else:
        print("\n❌ Conversion failed")
        sys.exit(1)
