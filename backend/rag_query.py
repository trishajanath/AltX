import os
from typing import List, Dict

# Fix deprecation warning
try:
    from langchain_chroma import Chroma  # New import
except ImportError:
    from langchain_community.vectorstores import Chroma  # Fallback
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

class RAGQueryEngine:
    def __init__(self, vector_db_path: str = "vector_db"):
        self.vector_db_path = vector_db_path
        self.vectorstore = None
        self.embeddings = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the RAG system"""
        try:
            if not os.path.exists(self.vector_db_path):
                print(f"🚨 Vector database not found at {self.vector_db_path}")
                raise FileNotFoundError(f"Vector database not found at {self.vector_db_path}")
            
            print(f"📂 Loading vector database from: {self.vector_db_path}")
            
            # Initialize embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            print("🧠 Embeddings model loaded: sentence-transformers/all-MiniLM-L6-v2")
            
            # Load the vector store
            self.vectorstore = Chroma(
                persist_directory=self.vector_db_path,
                embedding_function=self.embeddings
            )
            
            # Get database statistics
            try:
                collection = self.vectorstore._collection
                count = collection.count()
                print(f"📊 Vector database loaded successfully with {count} documents")
            except:
                print("✅ Vector database loaded successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize RAG system: {e}")
            self.vectorstore = None
    
    def query_secure_patterns(self, vulnerability_description: str, k: int = 3) -> str:
        """
        Query the RAG database for secure coding patterns
        """
        print(f"\n🔍 RAG QUERY PROCESS:")
        print(f"📝 Input: '{vulnerability_description}'")
        print(f"🎯 Requested results: {k}")
        
        if not self.vectorstore:
            print("🚨 VECTOR DATABASE NOT AVAILABLE - Using fallback patterns")
            fallback_result = self._fallback_patterns(vulnerability_description)
            print(f"📋 FALLBACK SOURCE: Hardcoded patterns")
            print(f"📄 Fallback pattern length: {len(fallback_result)} characters")
            return fallback_result
        
        try:
            # Create search query
            search_query = f"How to fix {vulnerability_description} secure coding pattern prevention"
            print(f"🔎 Search query: '{search_query}'")
            
            # Search for relevant documents
            print(f"🔍 Searching vector database...")
            results = self.vectorstore.similarity_search(search_query, k=k)
            
            print(f"📊 SEARCH RESULTS: Found {len(results)} documents")
            
            if not results:
                print("❌ NO SIMILAR DOCUMENTS FOUND - Using fallback patterns")
                fallback_result = self._fallback_patterns(vulnerability_description)
                print(f"📋 FALLBACK SOURCE: Hardcoded patterns")
                print(f"📄 Fallback pattern length: {len(fallback_result)} characters")
                return fallback_result
            
            # Log details about each result
            print(f"✅ USING VECTOR DATABASE RESULTS:")
            combined_context = ""
            total_chars = 0
            
            for i, doc in enumerate(results, 1):
                doc_content = doc.page_content
                doc_length = len(doc_content)
                total_chars += doc_length
                
                # Show document metadata if available
                metadata = getattr(doc, 'metadata', {})
                source = metadata.get('source', 'Unknown source')
                
                print(f"  📄 Document {i}:")
                print(f"     📍 Source: {source}")
                print(f"     📏 Length: {doc_length} characters")
                print(f"     📝 Preview: {doc_content[:100]}...")
                
                combined_context += f"\n--- Security Pattern {i} (Source: {source}) ---\n"
                combined_context += doc_content
                combined_context += "\n"
            
            print(f"🎯 FINAL RESULT:")
            print(f"   📊 Total documents used: {len(results)}")
            print(f"   📏 Total content length: {total_chars} characters")
            print(f"   📂 Source: Vector database ({self.vector_db_path})")
            
            return combined_context.strip()
            
        except Exception as e:
            print(f"⚠️ RAG QUERY FAILED: {e}")
            print(f"🔄 Falling back to hardcoded patterns")
            fallback_result = self._fallback_patterns(vulnerability_description)
            print(f"📋 FALLBACK SOURCE: Hardcoded patterns due to error")
            print(f"📄 Fallback pattern length: {len(fallback_result)} characters")
            return fallback_result
    
    def _fallback_patterns(self, vulnerability_description: str) -> str:
        """Fallback secure coding patterns when RAG is unavailable"""
        
        vuln_lower = vulnerability_description.lower()
        print(f"🔍 FALLBACK PATTERN MATCHING:")
        print(f"   📝 Searching for keywords in: '{vuln_lower}'")
        
        patterns = {
            "env": """
SECURE PATTERN: Environment File Security (.env files)
CRITICAL: .env files should NEVER be committed to repositories

Step-by-Step Fix:
1. ADD TO .GITIGNORE (Most Important):
   .env
   .env.local
   .env.production
   .env.staging
   .env.development

2. Remove from git if already committed:
   git rm --cached .env
   git commit -m "Remove .env from repository"

3. Create .env.example with dummy values:
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   API_KEY=your_api_key_here
   SECRET_KEY=your_secret_key_here

4. Update code to use environment variables:
   import os
   DATABASE_URL = os.getenv('DATABASE_URL')
   API_KEY = os.getenv('API_KEY')

SECURITY IMPACT: Environment files often contain:
- Database credentials
- API keys and tokens  
- Encryption secrets
- OAuth client secrets
            """,
            
            "gitignore": """
SECURE PATTERN: .gitignore Security Configuration
Essential patterns to prevent accidental commits:

# Environment variables (CRITICAL)
.env
.env.local
.env.production
.env.staging

# Python artifacts
__pycache__/
*.pyc
*.pyo
*.egg-info/
venv/
env/

# Logs and temporary files
*.log
tmp/
temp/

# OS files
.DS_Store
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp

# Dependencies
node_modules/
            """,
            
            "eval": """
SECURE PATTERN: Replace eval() with ast.literal_eval()
- Use ast.literal_eval() for safe evaluation of literals only
- Implement strict input validation and sanitization  
- Use allowlists for permitted operations
- Consider safer alternatives like json.loads() for data parsing
- Never use eval() with user-controlled input

Example Fix:
# Bad
result = eval(user_input)

# Good  
import ast
try:
    result = ast.literal_eval(user_input)  # Only evaluates literals
except (ValueError, SyntaxError):
    raise ValueError("Invalid input")
            """,
            
            "sql injection": """
SECURE PATTERN: Use parameterized queries/prepared statements
- Always use parameter binding, never string concatenation
- Use ORM frameworks that handle SQL injection prevention
- Implement input validation and sanitization
- Apply principle of least privilege for database users
- Use stored procedures with proper parameter handling

Example Fix:
# Bad
query = f"SELECT * FROM users WHERE id = {user_id}"

# Good
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
            """,
            
            "xss": """
SECURE PATTERN: Input validation and output encoding
- Validate all user input against strict allowlists
- Use context-appropriate output encoding (HTML, JavaScript, CSS, URL)
- Implement Content Security Policy (CSP) headers
- Use templating engines with automatic escaping
- Sanitize user input before storing or displaying

Example Fix:
# Bad
html = f"<p>Hello {user_name}</p>"

# Good
import html
safe_name = html.escape(user_name)
html = f"<p>Hello {safe_name}</p>"
            """,
            
            "path traversal": """
SECURE PATTERN: Validate and restrict file paths
- Use os.path.normpath() and os.path.abspath() to normalize paths
- Validate paths against allowlists of permitted directories
- Use os.path.commonpath() to ensure files are within allowed directories
- Implement proper access controls and file permissions
- Never directly concatenate user input to file paths

Example Fix:
# Bad
file_path = "/uploads/" + user_filename

# Good
import os
UPLOAD_DIR = "/uploads/"
safe_path = os.path.normpath(os.path.join(UPLOAD_DIR, user_filename))
if not safe_path.startswith(UPLOAD_DIR):
    raise ValueError("Invalid file path")
            """,
            
            "hardcoded": """
SECURE PATTERN: Use environment variables and secrets management
- Store sensitive data in environment variables
- Use dedicated secrets management systems (AWS Secrets Manager, Azure Key Vault)
- Implement proper key rotation policies
- Never commit secrets to version control
- Use configuration files that are not tracked by git

Example Fix:
# Bad
API_KEY = "sk-1234567890abcdef"

# Good
import os
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")
            """
        }
        
        # Enhanced pattern matching with logging
        matched_patterns = []
        for pattern_key, pattern_content in patterns.items():
            if pattern_key in vuln_lower:
                matched_patterns.append(pattern_key)
                print(f"   ✅ Matched pattern: '{pattern_key}'")
                print(f"   📏 Pattern length: {len(pattern_content)} characters")
                return pattern_content
        
        # Check for .env specific keywords
        env_keywords = ['.env', 'environment']
        gitignore_keywords = ['gitignore']
        
        for keyword in env_keywords:
            if keyword in vuln_lower:
                print(f"   ✅ Matched .env keyword: '{keyword}' -> using 'env' pattern")
                print(f"   📏 Pattern length: {len(patterns['env'])} characters")
                return patterns['env']
                
        for keyword in gitignore_keywords:
            if keyword in vuln_lower:
                print(f"   ✅ Matched gitignore keyword: '{keyword}' -> using 'gitignore' pattern")
                print(f"   📏 Pattern length: {len(patterns['gitignore'])} characters")
                return patterns['gitignore']
        
        # Default pattern
        default_pattern = """
GENERAL SECURE CODING PATTERN:
- Apply input validation and sanitization
- Use principle of least privilege
- Implement proper error handling
- Follow security best practices for your framework
- Regular security testing and code reviews
- Keep dependencies updated
        """
        
        print(f"   ⚠️ No specific pattern matched - using default")
        print(f"   📏 Default pattern length: {len(default_pattern)} characters")
        return default_pattern

    def debug_database_contents(self):
        """Debug function to show what's in the vector database"""
        if not self.vectorstore:
            print("❌ Vector database not available")
            return
            
        try:
            # Get all documents for debugging
            collection = self.vectorstore._collection
            all_docs = collection.get()
            
            print(f"\n📊 VECTOR DATABASE CONTENTS:")
            print(f"📂 Database path: {self.vector_db_path}")
            print(f"📄 Total documents: {len(all_docs['documents'])}")
            
            for i, doc in enumerate(all_docs['documents'][:5]):  # Show first 5
                metadata = all_docs['metadatas'][i] if all_docs['metadatas'] else {}
                doc_id = all_docs['ids'][i] if all_docs['ids'] else f"doc_{i}"
                
                print(f"\n📄 Document {i+1}:")
                print(f"   🆔 ID: {doc_id}")
                print(f"   📍 Metadata: {metadata}")
                print(f"   📏 Length: {len(doc)} characters")
                print(f"   📝 Preview: {doc[:150]}...")
                
        except Exception as e:
            print(f"❌ Error inspecting database: {e}")

# Global RAG instance
rag_engine = RAGQueryEngine()

def get_secure_coding_patterns(vulnerability_description: str) -> str:
    """
    Main function to get secure coding patterns for a vulnerability
    """
    return rag_engine.query_secure_patterns(vulnerability_description)

def debug_rag_database():
    """Debug function to inspect RAG database contents"""
    return rag_engine.debug_database_contents()