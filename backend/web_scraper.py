import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from typing import List, Dict
import time

def fetch_sonar_rules(output_file: str = "knowledge_base/sonar_rules_data.txt"):
    """
    Fetch SonarSource security rules data and save to knowledge base
    """
    print("🌐 Fetching SonarSource security rules...")
    
    try:
        # Base URL for SonarSource rules
        base_url = "https://rules.sonarsource.com"
        
        # Languages available on SonarSource (from their website)
        languages = [
            "java", "javascript", "typescript", "python", "csharp", 
            "php", "go", "kotlin", "swift", "ruby", "scala", "cpp",
            "c", "css", "html", "docker", "terraform", "kubernetes",
            "dart", "rust"
        ]
        
        all_rules_content = []
        successful_fetches = 0
        
        for lang in languages:
            try:
                print(f"📥 Fetching {lang.upper()} rules...")
                
                # Construct URL for language-specific rules page
                url = f"{base_url}/{lang}/"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    # Parse HTML content
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract rule information from the page
                    lang_content = f"\n\n{lang.upper()} SECURITY RULES:\n"
                    lang_content += "=" * 50 + "\n"
                    
                    rules_found = 0
                    
                    # Look for individual rule links (RSPEC format)
                    rule_links = soup.find_all('a', href=lambda x: x and '/RSPEC-' in str(x))
                    
                    if rule_links:
                        lang_content += f"Found {len(rule_links)} individual rules for {lang.upper()}:\n\n"
                        
                        # Process up to 5 individual rules to get detailed info
                        for i, rule_link in enumerate(rule_links[:5]):
                            try:
                                rule_href = rule_link.get('href')
                                if not rule_href.startswith('http'):
                                    rule_url = base_url + rule_href
                                else:
                                    rule_url = rule_href
                                
                                # Fetch individual rule page
                                rule_response = requests.get(rule_url, headers=headers, timeout=10)
                                if rule_response.status_code == 200:
                                    rule_soup = BeautifulSoup(rule_response.content, 'html.parser')
                                    
                                    # Extract rule details
                                    rule_title = rule_soup.find('h1')
                                    rule_title_text = rule_title.get_text(strip=True) if rule_title else "Unknown Rule"
                                    
                                    # Look for rule type/severity indicators
                                    severity_elem = rule_soup.find(string=lambda x: x and ('vulnerability' in str(x).lower() or 'security' in str(x).lower() or 'bug' in str(x).lower()))
                                    
                                    # Get rule description
                                    description_elem = rule_soup.find(['p', 'div'], class_=lambda x: x and 'description' in str(x).lower())
                                    if not description_elem:
                                        # Look for the first substantial paragraph
                                        description_elem = rule_soup.find('p')
                                    
                                    description = description_elem.get_text(strip=True)[:200] + "..." if description_elem else "No description available"
                                    
                                    lang_content += f"Rule {i+1}: {rule_title_text}\n"
                                    lang_content += f"URL: {rule_url}\n"
                                    lang_content += f"Description: {description}\n"
                                    lang_content += f"Language: {lang.upper()}\n"
                                    lang_content += "-" * 30 + "\n\n"
                                    rules_found += 1
                                    
                                    # Rate limiting for individual rule requests
                                    time.sleep(1)
                                    
                            except Exception as e:
                                print(f"   ⚠️  Error fetching individual rule: {e}")
                                continue
                    
                    # Fallback: Extract general rule information from main page
                    if rules_found == 0:
                        # Look for rule categories or counts
                        rule_categories = soup.find_all(string=lambda x: x and ('vulnerability' in str(x).lower() or 'security' in str(x).lower() or 'code smell' in str(x).lower()))
                        
                        if rule_categories:
                            lang_content += f"Rule categories found for {lang.upper()}:\n"
                            for category in rule_categories[:10]:
                                clean_category = category.strip()
                                if len(clean_category) > 5 and len(clean_category) < 100:
                                    lang_content += f"- {clean_category}\n"
                        
                        # Get main content overview
                        main_content = soup.find('main') or soup.find('body')
                        if main_content:
                            text_content = main_content.get_text(separator=' ', strip=True)
                            
                            # Extract security-related content
                            sentences = text_content.split('.')
                            security_sentences = [s.strip() for s in sentences if any(keyword in s.lower() for keyword in ['security', 'vulnerability', 'attack', 'injection', 'xss', 'sql', 'csrf'])]
                            
                            if security_sentences:
                                lang_content += f"\nSecurity-related information for {lang.upper()}:\n"
                                for sentence in security_sentences[:5]:
                                    if len(sentence) > 20:
                                        lang_content += f"• {sentence}.\n"
                            
                        lang_content += f"\nFull rules available at: {url}\n"
                    
                    all_rules_content.append(lang_content)
                    successful_fetches += 1
                    print(f"✅ Successfully fetched {lang.upper()} rules ({rules_found} detailed rules)")
                    
                else:
                    print(f"⚠️  Failed to fetch {lang.upper()} rules: HTTP {response.status_code}")
                
                # Be respectful with rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error fetching {lang.upper()} rules: {e}")
                continue
        
        # Save to knowledge base
        if successful_fetches > 0:
            content = f"""SonarSource Security Rules Database - Live Data
==================================================
Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Languages Processed: {len(languages)}
Successful Fetches: {successful_fetches}
Source: {base_url}

OVERVIEW:
SonarSource provides comprehensive static analysis rules covering:
- Security vulnerabilities (OWASP Top 10, CWE, SANS Top 25)
- Code quality issues
- Bug detection
- Maintainability concerns

The rules are continuously updated and cover modern frameworks and technologies.

SECURITY FOCUS AREAS:
- Injection flaws (SQL, Command, LDAP, etc.)
- Cross-Site Scripting (XSS)
- Authentication and session management
- Access control issues
- Security misconfigurations
- Sensitive data exposure
- Cryptographic failures
- Input validation
- Error handling and logging
- Component vulnerabilities

LANGUAGE-SPECIFIC RULES:
"""
            
            # Add all collected content
            content += "".join(all_rules_content)
            
            # Add footer
            content += f"""

INTEGRATION NOTES:
================
- Use SonarQube/SonarCloud for automated analysis
- Rules are mapped to industry standards (CWE, OWASP, etc.)
- Regular updates ensure coverage of latest vulnerabilities
- IDE plugins available for real-time analysis
- CI/CD integration supported

For the most current rules, visit: {base_url}
Total rules database contains 6000+ rules across 30+ languages.
"""
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"💾 Saved rules data from {successful_fetches} languages to {output_file}")
            return True
        else:
            print("⚠️  No rules data successfully fetched")
            return False
            
    except Exception as e:
        print(f"❌ Error in fetch_sonar_rules: {e}")
        return False

def force_update_knowledge_base():
    """
    Force update knowledge base from web (ignoring cache)
    Use this to refresh the data manually
    """
    print("🔄 Force updating knowledge base from web...")
    print("⏱️ This may take up to 9 minutes...")
    
    success = fetch_sonar_rules()
    
    if success:
        print("✅ Knowledge base force updated with fresh web data")
        
        # Auto-generate PDF if conversion script exists
        import subprocess
        pdf_script = "convert_rules_to_pdf.py"
        if os.path.exists(pdf_script):
            try:
                print("📄 Auto-generating PDF from fresh data...")
                result = subprocess.run(
                    ["python", pdf_script],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                if result.returncode == 0:
                    print("✅ PDF regenerated successfully")
                else:
                    print(f"⚠️ PDF generation warning: {result.stderr}")
            except Exception as e:
                print(f"⚠️ Could not auto-generate PDF: {e}")
        
        return True
    else:
        print("❌ Failed to force update knowledge base")
        return False

def update_knowledge_base_with_web_data():
    """
    Update knowledge base with fresh web data
    Uses local PDF if available to avoid 9-minute web fetching
    """
    print("🔄 Updating knowledge base with web data...")
    
    # Check if local PDF exists and is recent (less than 7 days old)
    pdf_path = "knowledge_base/sonar_security_rules.pdf"
    txt_path = "knowledge_base/sonar_rules_data.txt"
    
    import os
    from datetime import datetime, timedelta
    
    if os.path.exists(pdf_path):
        # Check PDF age
        pdf_modified = datetime.fromtimestamp(os.path.getmtime(pdf_path))
        if datetime.now() - pdf_modified < timedelta(days=7):
            print(f"✅ Using local PDF (created {pdf_modified.strftime('%Y-%m-%d %H:%M')})")
            print("📄 Skipping web fetch - using cached SonarSource rules PDF")
            print("⚡ Saved 9 minutes of fetching time!")
            return True
        else:
            print(f"⚠️ Local PDF is older than 7 days (created {pdf_modified.strftime('%Y-%m-%d %H:%M')})")
    
    # Check if text file exists and is recent (less than 7 days old)
    if os.path.exists(txt_path):
        txt_modified = datetime.fromtimestamp(os.path.getmtime(txt_path))
        if datetime.now() - txt_modified < timedelta(days=7):
            print(f"✅ Using cached text data (updated {txt_modified.strftime('%Y-%m-%d %H:%M')})")
            print("📄 Skipping web fetch - using cached SonarSource rules")
            print("⚡ Saved 9 minutes of fetching time!")
            return True
        else:
            print(f"⚠️ Cached data is older than 7 days (updated {txt_modified.strftime('%Y-%m-%d %H:%M')})")
    
    # Fall back to web fetching if no recent local data
    print("🌐 No recent local data found, fetching from web...")
    print("⏱️ This may take up to 9 minutes...")
    success = fetch_sonar_rules()
    
    if success:
        print("✅ Knowledge base updated with web data")
        print("💡 Tip: The data will be cached for 7 days to speed up future requests")
        return True
    else:
        print("❌ Failed to update knowledge base with web data")
        return False

if __name__ == "__main__":
    update_knowledge_base_with_web_data()
