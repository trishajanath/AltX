import os
from github import Github

def test_github_token():
    token = os.getenv("GITHUB_TOKEN", "your_github_token_here")
    
    try:
        g = Github(token)
        
        # Test basic authentication
        user = g.get_user()
        print(f"✅ Token authenticated as: {user.login}")
        
        # Test repository access
        repo = g.get_repo("DrNeel11/ezhealth_final")
        print(f"✅ Repository accessible: {repo.full_name}")
        print(f"✅ Repository language: {repo.language}")
        print(f"✅ Repository private: {repo.private}")
        
        return True
        
    except Exception as e:
        print(f"❌ Token test failed: {e}")
        return False

if __name__ == "__main__":
    test_github_token()
