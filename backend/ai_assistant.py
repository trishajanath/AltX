import google.generativeai as genai
import os
from typing import List, Dict, Optional, ClassVar
from dotenv import load_dotenv
from github import Github
from github.GithubException import GithubException
from dataclasses import dataclass

# Define RepoAnalysis class to store scan results
@dataclass
class RepoAnalysis:
    """Store repository analysis results"""
    repo_name: str
    description: str
    language: str
    files_scanned: List[str]
    security_findings: List[str]
    open_issues: int
    
    # Class variable to store latest analysis
    latest_analysis: ClassVar[Optional['RepoAnalysis']] = None

# Load environment variables
load_dotenv()

# Available models configuration
AVAILABLE_MODELS = {
    'fast': 'models/gemini-2.5-flash',
    'smart': 'models/gemini-2.5-pro'
}

# Initialize models dictionary
models = {}
GITHUB_TOKEN = os.getenv("GITHUB_PAT")
github_client = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None

# Initialize Gemini API
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("No API key found. Set GOOGLE_API_KEY environment variable.")
    
    genai.configure(api_key=api_key)
    
    # Initialize both models
    for model_type, model_name in AVAILABLE_MODELS.items():
        try:
            models[model_type] = genai.GenerativeModel(model_name)
            print(f"✅ Initialized {model_type} model ({model_name})")
        except Exception as e:
            print(f"❌ Failed to initialize {model_type} model: {e}")
            
except Exception as e:
    print(f"❌ Error initializing Gemini API: {e}")

def get_model(model_type: str = 'fast') -> Optional[genai.GenerativeModel]:
    """Get the specified model instance."""
    return models.get(model_type)

def get_chat_response(history: List[Dict], model_type: str = 'fast') -> str:
    model = get_model(model_type)
    if model is None:
        return f"AI model ({model_type}) is not available"

    try:
        # Add repository context if available
        context = """You are a security expert assistant analyzing a GitHub repository."""
        
        if RepoAnalysis.latest_analysis:
            context += f"""
            
            Current Repository Analysis:
            Repository: {RepoAnalysis.latest_analysis.repo_name}
            Language: {RepoAnalysis.latest_analysis.language}
            
            Files Scanned:
            {chr(10).join(RepoAnalysis.latest_analysis.files_scanned)}
            
            Security Findings:
            {chr(10).join(RepoAnalysis.latest_analysis.security_findings)}
            
            Base your answers on these actual scan results and findings.
            Provide specific, actionable recommendations when asked.
            """
        
        # Convert history to Gemini format
        formatted_history = [{
            'parts': [{'text': context}],
            'role': 'model'
        }]
        
        for msg in history:
            if isinstance(msg.get('parts'), list):
                content = msg['parts'][0]
            else:
                content = msg.get('user') or msg.get('ai') or msg.get('content', '')
            
            formatted_history.append({
                'parts': [{'text': content}],
                'role': 'user' if msg.get('type') == 'user' else 'model'
            })

        # Create chat session with formatted history
        chat = model.start_chat(history=formatted_history)
        
        # Get the last user message
        last_message = history[-1]['parts'][0] if isinstance(history[-1].get('parts'), list) else history[-1].get('content', '')
        
        # Send message and get response
        response = chat.send_message(last_message)
        return response.text.strip()
    except Exception as e:
        return f"Chat Error: {str(e)}"

def analyze_github_repo(repo_url: str, model_type: str = 'smart') -> str:
    """Analyze a GitHub repository for security issues."""
    if not github_client:
        return "GitHub token not configured. Please set GITHUB_PAT in .env file."
    
    try:
        # Clean up the repo URL and extract owner/repo
        repo_url = repo_url.rstrip('/').replace('.git', '')
        parts = repo_url.split('/')
        if len(parts) < 5:
            return "Invalid repository URL format. Expected: https://github.com/owner/repo"
            
        owner = parts[-2]
        repo_name = parts[-1]
        
        # Get repository
        repo = github_client.get_repo(f"{owner}/{repo_name}")
        print(f"📂 Accessing repository: {owner}/{repo_name}")
        
        # Initialize findings and file lists
        security_findings = []
        all_files_visited = []
        
        def scan_directory(path=""):
            """Recursively scan directory and collect file information"""
            try:
                contents = repo.get_contents(path)
                for content in contents:
                    if content.type == "dir":
                        scan_directory(content.path)
                    else:
                        all_files_visited.append(f"- {content.path}")
                        # Check for sensitive patterns in file names
                        if any(pattern in content.path.lower() for pattern in ['secret', 'password', 'key', '.env']):
                            security_findings.append(f"⚠️ Potentially sensitive file found: {content.path}")
            except Exception as e:
                security_findings.append(f"⚠️ Error accessing {path}: {str(e)}")

        # Scan repository contents
        print(f"🔍 Scanning repository contents...")
        scan_directory()

        # Check common security-related files
        security_files = {
            'package.json': 'Dependencies',
            'requirements.txt': 'Python dependencies',
            '.env.example': 'Environment configuration',
            'Dockerfile': 'Container configuration',
            '.github/workflows': 'CI/CD configuration',
            'security.md': 'Security documentation'
        }

        for file_path, description in security_files.items():
            try:
                content = repo.get_contents(file_path)
                if isinstance(content, list):
                    security_findings.append(f"Found {description} directory: {[f.path for f in content]}")
                else:
                    decoded = content.decoded_content.decode()
                    security_findings.append(f"Found {description}:\n{decoded[:500]}...")
            except: pass

        # Store analysis results
        RepoAnalysis.latest_analysis = RepoAnalysis(
            repo_name=repo.full_name,
            description=repo.description or 'No description',
            language=repo.language or 'Unknown',
            files_scanned=all_files_visited,
            security_findings=security_findings,
            open_issues=repo.open_issues_count
        )

        # Prepare security analysis prompt
        security_prompt = f"""
        Perform a detailed security analysis of this GitHub repository:
        
        Repository Info:
        - Name: {repo.full_name}
        - Description: {repo.description or 'No description'}
        - Language: {repo.language or 'Unknown'}
        - Open Issues: {repo.open_issues_count}
        
        Files Scanned ({len(all_files_visited)} total):
        {chr(10).join(all_files_visited)}
        
        Security Findings:
        {chr(10).join(security_findings) if security_findings else "No security-related files found"}
        
        Please provide:
        1. Overall security assessment
        2. Specific vulnerabilities found
        3. Sensitive information exposure risks
        4. Missing security best practices
        5. Concrete recommendations with examples
        6. Repository structure security analysis
        """
        
        # Get AI analysis using chat functionality
        history = [{
            "type": "user",
            "parts": [security_prompt]
        }]
        
        return get_chat_response(history, 'smart')

    except GithubException as e:
        if e.status == 404:
            return "Repository not found. Please check:\n1. The repository URL is correct\n2. The repository is public\n3. Your GitHub token has access to it"
        elif e.status == 401:
            return "GitHub authentication failed. Please check your GitHub token."
        else:
            return f"GitHub API error: {e.status} - {e.data.get('message', 'Unknown error')}"
    except Exception as e:
        return f"Error analyzing repository: {str(e)}"