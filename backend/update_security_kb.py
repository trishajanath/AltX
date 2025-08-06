#!/usr/bin/env python3
"""
AltX Security Scanner - Manual Knowledge Base Update Script
Run this script to manually update the security knowledge base with latest rules
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_scraper import update_knowledge_base_with_web_data
from build_rag_db import build_database

async def update_security_knowledge():
    """Update security knowledge base with latest rules"""
    print("🚀 Starting manual security knowledge base update...")
    
    try:
        # Update with web data
        print("📥 Fetching latest security rules...")
        success = update_knowledge_base_with_web_data()
        
        if success:
            print("✅ Security rules updated successfully")
            
            # Rebuild RAG database
            print("🔄 Updating RAG database...")
            build_database(rebuild_from_scratch=False, fetch_web_data=False)
            print("✅ RAG database updated")
            
            print("""
🎉 Security knowledge base update completed!

Your AltX scanner now has access to:
• Latest SonarSource security rules (6000+ patterns)
• Updated vulnerability detection patterns
• Current secure coding best practices
• Enhanced RAG-powered analysis

Next steps:
• Run repository analysis: /analyze-repo
• Generate security fixes: /propose-fix (in chat)
• The knowledge base will auto-update during analysis
""")
            
        else:
            print("❌ Failed to update security rules")
            return False
            
    except Exception as e:
        print(f"❌ Update failed: {e}")
        return False
    
    return True

def main():
    """Main entry point"""
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
AltX Security Knowledge Base Updater

Usage:
  python update_security_kb.py          # Update knowledge base
  python update_security_kb.py --help   # Show this help

This script:
1. Fetches latest security rules from SonarSource
2. Updates the local knowledge base
3. Rebuilds the RAG database for enhanced AI analysis

The updated knowledge base will be used automatically by:
• /analyze-repo endpoint (auto-updates before analysis)
• /propose-fix AI chat command (uses enhanced patterns)
• General security consultations (RAG-enhanced responses)
""")
        return
    
    # Run the update
    asyncio.run(update_security_knowledge())

if __name__ == "__main__":
    main()
