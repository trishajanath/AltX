# scanner/file_security_scanner.py
import os
import re
from typing import List, Dict

def scan_for_sensitive_files(directory_path: str) -> Dict:
    """Scan directory for sensitive files and security issues"""
    
    sensitive_patterns = [
        'secret', 'password', 'key', '.env', 'config', 'credential', 
        'token', 'api_key', 'private', 'auth', 'jwt', 'oauth', 'ssl', 
        'cert', 'pem', 'rsa', 'dsa', 'ecdsa'
    ]
    
    risky_extensions = [
        '.sql', '.db', '.sqlite', '.sqlite3', '.key', '.pem', 
        '.p12', '.jks', '.pfx', '.crt', '.cer', '.der'
    ]
    
    important_security_files = [
        'security.md', 'security.txt', 'dockerfile', 'docker-compose.yml',
        'requirements.txt', 'package.json', 'package-lock.json', 'yarn.lock',
        'pipfile', 'pipfile.lock', '.gitignore', 'makefile', 'cmake'
    ]
    
    findings = {
        'sensitive_files': [],
        'risky_files': [],
        'security_files_found': [],
        'missing_security_files': [],
        'total_files_scanned': 0,
        'directories_scanned': 0
    }
    
    try:
        for root, dirs, files in os.walk(directory_path):
            # Skip .git directory
            if '.git' in root:
                continue
                
            findings['directories_scanned'] += 1
            
            for file in files:
                findings['total_files_scanned'] += 1
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory_path)
                file_lower = file.lower()
                
                # Check for sensitive patterns in filename
                for pattern in sensitive_patterns:
                    if pattern in file_lower:
                        findings['sensitive_files'].append({
                            'file': relative_path,
                            'pattern': pattern,
                            'risk': 'High' if pattern in ['password', 'secret', 'key'] else 'Medium'
                        })
                        break
                
                # Check for risky file extensions
                for ext in risky_extensions:
                    if file_lower.endswith(ext):
                        findings['risky_files'].append({
                            'file': relative_path,
                            'extension': ext,
                            'risk': 'Critical' if ext in ['.key', '.pem', '.p12'] else 'High'
                        })
                        break
                
                # Check for important security files
                if file_lower in important_security_files:
                    findings['security_files_found'].append({
                        'file': relative_path,
                        'type': file_lower
                    })
        
        # Check for missing important security files
        found_files = [f['type'] for f in findings['security_files_found']]
        for security_file in important_security_files:
            if security_file not in found_files:
                findings['missing_security_files'].append(security_file)
        
        return findings
        
    except Exception as e:
        return {
            'error': f"Error scanning directory: {str(e)}",
            'sensitive_files': [],
            'risky_files': [],
            'security_files_found': [],
            'missing_security_files': [],
            'total_files_scanned': 0,
            'directories_scanned': 0
        }

def scan_file_contents_for_secrets(file_path: str) -> List[Dict]:
    """Scan file contents for potential secrets"""
    
    secret_patterns = {
        'api_key': r'api[_-]?key[\'"\s]*[:=][\'"\s]*[a-zA-Z0-9]{20,}',
        'aws_access_key': r'AKIA[0-9A-Z]{16}',
        'aws_secret_key': r'[0-9a-zA-Z/+]{40}',
        'github_token': r'gh[pso]_[A-Za-z0-9_]{36}',
        'jwt_token': r'eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*',
        'password': r'password[\'"\s]*[:=][\'"\s]*[^\s\'";,]{8,}',
        'private_key': r'-----BEGIN [A-Z ]+PRIVATE KEY-----',
        'database_url': r'[a-zA-Z]+://[^\s\'";,]+:[^\s\'";,]+@[^\s\'";,]+',
        'google_api': r'AIza[0-9A-Za-z_-]{35}',
        'slack_token': r'xox[bpoa]-[0-9]{12}-[0-9]{12}-[0-9a-zA-Z]{24}',
    }
    
    findings = []
    
    try:
        # Only scan text files
        if not file_path.endswith(('.py', '.js', '.json', '.yml', '.yaml', '.env', '.config', '.txt', '.md', '.sh', '.bat')):
            return findings
            
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            for secret_type, pattern in secret_patterns.items():
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    findings.append({
                        'file': os.path.basename(file_path),
                        'secret_type': secret_type,
                        'line': content[:match.start()].count('\n') + 1,
                        'match': match.group()[:50] + '...' if len(match.group()) > 50 else match.group(),
                        'risk': 'Critical'
                    })
    
    except Exception:
        pass  # Skip files that can't be read
    
    return findings