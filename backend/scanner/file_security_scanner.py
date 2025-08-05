# scanner/file_security_scanner.py
import os
import re
from typing import List, Dict

def scan_for_sensitive_files(directory_path: str) -> Dict:
    """Scan directory for sensitive files and security issues with proper filtering"""
    
    # Directories to skip completely
    skip_directories = {
        'venv', 'env', '.env', 'virtualenv', 'venv_*', 'env_*',  # Python virtual environments
        '__pycache__', '*.egg-info', '.tox', '.pytest_cache', '.coverage',  # Python build/test artifacts
        'node_modules', 'bower_components', '.npm', 'npm-debug.log*',  # Node.js dependencies
        '.git', '.svn', '.hg', '.bzr',  # Version control
        'build', 'dist', 'target', 'out', 'bin', 'obj',  # Build directories
        '.gradle', '.maven', '.ivy2',  # Java build tools
        'vendor', 'Godeps', '_workspace',  # Go dependencies
        '.next', '.nuxt', 'coverage', '.nyc_output',  # Frontend frameworks
        'logs', '*.log', 'tmp', 'temp', '.tmp', '.temp',  # Temporary files
        '.DS_Store', 'Thumbs.db', '*.swp', '*.swo',  # OS/Editor files
        '.vscode', '.idea', '*.sublime-*', '.atom',  # IDE files
        'docker-data', 'postgres-data', 'mysql-data'  # Docker volumes
    }
    
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
        'excluded_directories': [],
        'gitignore_recommendations': [],
        'total_files_scanned': 0,
        'directories_scanned': 0,
        'directories_skipped': 0
    }
    
    try:
        # Check if .gitignore exists and load it
        gitignore_path = os.path.join(directory_path, '.gitignore')
        gitignore_entries = set()
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
                gitignore_entries = {line.strip() for line in f if line.strip() and not line.startswith('#')}
        
        def should_skip_directory(dir_path, dir_name):
            """Check if directory should be skipped"""
            dir_lower = dir_name.lower()
            
            # Check against skip patterns
            for skip_pattern in skip_directories:
                if skip_pattern.startswith('*') and dir_lower.endswith(skip_pattern[1:]):
                    return True
                elif skip_pattern.endswith('*') and dir_lower.startswith(skip_pattern[:-1]):
                    return True
                elif skip_pattern == dir_lower:
                    return True
                elif skip_pattern in dir_lower:
                    return True
            
            return False
        
        for root, dirs, files in os.walk(directory_path):
            # Filter out directories that should be skipped
            dirs_to_remove = []
            for dir_name in dirs:
                if should_skip_directory(root, dir_name):
                    dirs_to_remove.append(dir_name)
                    findings['directories_skipped'] += 1
                    relative_path = os.path.relpath(os.path.join(root, dir_name), directory_path)
                    findings['excluded_directories'].append({
                        'directory': relative_path,
                        'reason': 'Build/dependency directory - excluded from scan'
                    })
            
            # Remove directories from the dirs list to prevent os.walk from entering them
            for dir_name in dirs_to_remove:
                dirs.remove(dir_name)
            
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
        
        # Generate .gitignore recommendations based on found directories
        gitignore_recommendations = []
        
        # Check for common patterns that should be in .gitignore
        common_gitignore_patterns = {
            '__pycache__/': 'Python bytecode cache',
            '*.pyc': 'Python compiled files',
            '*.pyo': 'Python optimized files',
            '*.pyd': 'Python extension modules',
            '.Python': 'Python environment marker',
            'venv/': 'Python virtual environment',
            'env/': 'Python virtual environment',
            '.env': 'Environment variables file',
            'node_modules/': 'Node.js dependencies',
            'npm-debug.log*': 'NPM debug logs',
            'yarn-debug.log*': 'Yarn debug logs',
            'yarn-error.log*': 'Yarn error logs',
            '.DS_Store': 'macOS system files',
            'Thumbs.db': 'Windows system files',
            '*.log': 'Log files',
            '.vscode/': 'VS Code settings',
            '.idea/': 'IntelliJ IDEA settings',
            'build/': 'Build output directory',
            'dist/': 'Distribution directory',
            '*.egg-info/': 'Python package metadata',
            '.coverage': 'Code coverage data',
            '.pytest_cache/': 'Pytest cache',
            '.tox/': 'Tox testing tool cache'
        }
        
        # Check which patterns are missing from .gitignore
        for pattern, description in common_gitignore_patterns.items():
            if pattern not in gitignore_entries and pattern.rstrip('/') not in gitignore_entries:
                # Check if this type of file/directory exists in the project
                pattern_found = False
                if '/' in pattern:  # Directory pattern
                    dir_name = pattern.rstrip('/')
                    for excluded in findings['excluded_directories']:
                        if dir_name.lower() in excluded['directory'].lower():
                            pattern_found = True
                            break
                
                if pattern_found or pattern in ['.env', '*.log', '.DS_Store', 'Thumbs.db']:
                    gitignore_recommendations.append({
                        'pattern': pattern,
                        'description': description,
                        'priority': 'High' if pattern in ['.env', '*.log', '__pycache__/', 'node_modules/'] else 'Medium'
                    })
        
        findings['gitignore_recommendations'] = gitignore_recommendations
        
        return findings
        
    except Exception as e:
        return {
            'error': f"Error scanning directory: {str(e)}",
            'sensitive_files': [],
            'risky_files': [],
            'security_files_found': [],
            'missing_security_files': [],
            'excluded_directories': [],
            'gitignore_recommendations': [],
            'total_files_scanned': 0,
            'directories_scanned': 0,
            'directories_skipped': 0
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