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
                raise FileNotFoundError(f"Vector database not found at {self.vector_db_path}")
            
            # Initialize embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            
            # Load the vector store
            self.vectorstore = Chroma(
                persist_directory=self.vector_db_path,
                embedding_function=self.embeddings
            )
            
            print("✅ RAG system initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize RAG system: {e}")
            self.vectorstore = None
    
    def query_secure_patterns(self, vulnerability_description: str, k: int = 3) -> str:
        """
        Query the RAG database for secure coding patterns
        """
        if not self.vectorstore:
            return self._fallback_patterns(vulnerability_description)
        
        try:
            # Create search query
            search_query = f"How to fix {vulnerability_description} secure coding pattern prevention"
            
            # Search for relevant documents
            results = self.vectorstore.similarity_search(search_query, k=k)
            
            if not results:
                return self._fallback_patterns(vulnerability_description)
            
            # Combine results into a comprehensive response
            combined_context = ""
            for i, doc in enumerate(results, 1):
                combined_context += f"\n--- Security Pattern {i} ---\n"
                combined_context += doc.page_content
                combined_context += "\n"
            
            return combined_context.strip()
            
        except Exception as e:
            print(f"⚠️ RAG query failed: {e}")
            return self._fallback_patterns(vulnerability_description)
    
    def _fallback_patterns(self, vulnerability_description: str) -> str:
        """Fallback secure coding patterns when RAG is unavailable"""
        
        vuln_lower = vulnerability_description.lower()
        
        patterns = {
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
        
        # Find matching pattern
        for pattern_key, pattern_content in patterns.items():
            if pattern_key in vuln_lower:
                return pattern_content
        
        # Default secure coding advice
        return """
GENERAL SECURE CODING PATTERN:
- Apply input validation and sanitization
- Use principle of least privilege
- Implement proper error handling
- Follow security best practices for your framework
- Regular security testing and code reviews
- Keep dependencies updated
        """

# Global RAG instance
rag_engine = RAGQueryEngine()

def get_secure_coding_patterns(vulnerability_description: str) -> str:
    """
    Main function to get secure coding patterns for a vulnerability
    """
    return rag_engine.query_secure_patterns(vulnerability_description)