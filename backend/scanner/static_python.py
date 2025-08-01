# scanner/static_python.py

import subprocess
import json
from pathlib import Path

def run_bandit(repo_path: str):
    """
    Runs bandit static analysis on a Python repository.
    """
    results = []
    repo_path_obj = Path(repo_path)

    # Ensure the path exists and is a directory
    if not repo_path_obj.is_dir():
        return results

    try:
        # Execute bandit and capture the JSON output
        # The '-f json' flag tells bandit to output in JSON format.
        # The '-r' flag makes it run recursively.
        command = ["bandit", "-r", str(repo_path_obj), "-f", "json"]
        
        # Using capture_output=True and text=True for cleaner handling
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False # Don't raise an exception on non-zero exit codes
        )

        # Bandit exits with a non-zero status code if it finds issues,
        # so we parse stdout regardless of the exit code.
        if process.stdout:
            report = json.loads(process.stdout)
            for issue in report.get("results", []):
                results.append({
                    "filename": issue["filename"],
                    "issue": issue["issue_text"],
                    "severity": issue["issue_severity"],
                    "confidence": issue["issue_confidence"],
                    "line_number": issue["line_number"]
                })
    except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
        # Handle cases where bandit is not installed or output is malformed
        print(f"Error running bandit: {e}")
        pass
        
    return results