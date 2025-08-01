# scanner/secrets_detector.py

from pathlib import Path
import re

# Common secret patterns
SECRET_PATTERNS = {
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "AWS Secret Key": r"(?i)aws.*['\"][0-9a-zA-Z/+]{40}['\"]",
    "Google API Key": r"AIza[0-9A-Za-z\-]{35}",
    "Generic API Key": r"(?i)(api|apikey|token|secret)[\s:=]+['\"]?[0-9a-zA-Z-]{16,}['\"]?",
    "Private Key": r"-----BEGIN PRIVATE KEY-----",
    "JWT Token": r"eyJ[a-zA-Z0-9-]+.[a-zA-Z0-9-]+.[a-zA-Z0-9-_]+"
}

def scan_secrets(repo_path: str):
    """
    Scans a repository for hardcoded secrets based on regex patterns.
    """
    matches = []
    # A set of file extensions to check
    allowed_extensions = {".py", ".js", ".ts", ".env", ".json", ".yml", ".yaml", ".txt"}

    for filepath in Path(repo_path).rglob("*"):
        # Check if the file is not a directory and has an allowed extension
        if filepath.is_file() and filepath.suffix in allowed_extensions:
            try:
                content = filepath.read_text(errors="ignore")
                for label, pattern in SECRET_PATTERNS.items():
                    for match in re.findall(pattern, content):
                        matches.append({
                            "file": str(filepath.relative_to(repo_path)),
                            "match": match,
                            "type": label
                        })
            except Exception:
                # Ignore files that can't be read
                continue
    return matches