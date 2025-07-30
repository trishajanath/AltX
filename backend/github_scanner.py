# github_scanner.py
import os
from github import Github
from urllib.parse import urlparse

# A list of file names or extensions to look for.
# You can expand this list with Dockerfiles, .yml files, etc.
INTERESTING_FILES = [
    'package.json', 
    'requirements.txt', 
    'pom.xml',
    '.py',
    '.js',
    '.conf',
    '.sh'
]

def get_repo_file_contents(repo_url: str) -> dict:
    """
    Connects to a GitHub repository and fetches the content of interesting files.

    Args:
        repo_url: The full URL of the GitHub repository.

    Returns:
        A dictionary where keys are file paths and values are their content.
    """
    try:
        # Initialize the GitHub client using the Personal Access Token
        g = Github(os.getenv("GITHUB_PAT"))
        
        # Extract the 'owner/repo' part from the URL
        path = urlparse(repo_url).path.strip('/')
        
        # Get the repository object
        repo = g.get_repo(path)
        
        contents = repo.get_contents("")
        files_content = {}
        
        # Loop through the repository's contents
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                # If it's a directory, add its contents to the list to process
                contents.extend(repo.get_contents(file_content.path))
            else:
                # If it's a file, check if it's one we care about
                if any(file_content.path.endswith(ext) for ext in INTERESTING_FILES):
                    print(f"-> Found interesting file: {file_content.path}")
                    # Get the raw content of the file
                    content = file_content.decoded_content.decode('utf-8')
                    files_content[file_content.path] = content

        return {"files": files_content, "error": None}

    except Exception as e:
        print(f"Error connecting to GitHub repo: {e}")
        return {"files": {}, "error": f"Could not access repository. Details: {e}"}