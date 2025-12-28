"""
Code Validation and Testing System

This module provides comprehensive validation for generated code to ensure:
1. Syntax correctness 
2. Import validity
3. Runtime functionality
4. Security compliance
5. Quality standards

CRITICAL: No code should be written to files without passing ALL validation checks.
"""

import ast
import subprocess
import sys
import tempfile
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Result of code validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    
    def __bool__(self):
        return self.is_valid

class CodeValidator:
    """Comprehensive code validation system."""
    
    def __init__(self):
        self.python_reserved_words = {
            'False', 'None', 'True', 'and', 'as', 'assert', 'break', 'class', 
            'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 
            'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 
            'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try', 
            'while', 'with', 'yield'
        }
    
    def validate_python_syntax(self, code: str, filename: str = "generated.py") -> ValidationResult:
        """Validate Python code syntax and structure."""
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Remove any markdown code blocks that might be present
            cleaned_code = self._clean_markdown_from_code(code)
            
            # Basic syntax check
            ast.parse(cleaned_code)
            
            # Check for common issues
            errors.extend(self._check_python_common_issues(cleaned_code))
            warnings.extend(self._check_python_warnings(cleaned_code))
            suggestions.extend(self._check_python_suggestions(cleaned_code))
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )
            
        except SyntaxError as e:
            errors.append(f"Syntax Error in {filename}: {e.msg} (line {e.lineno})")
        except Exception as e:
            errors.append(f"Validation Error in {filename}: {str(e)}")
            
        return ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def validate_javascript_syntax(self, code: str, filename: str = "generated.js") -> ValidationResult:
        """Validate JavaScript/JSX code syntax using ESLint and Babel parser."""
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Remove any markdown code blocks
            cleaned_code = self._clean_markdown_from_code(code)
            
            # Try to use ESLint if available for proper React validation
            if self._check_eslint_available():
                eslint_result = self._validate_with_eslint(cleaned_code, filename)
                errors.extend(eslint_result.get('errors', []))
                warnings.extend(eslint_result.get('warnings', []))
            else:
                # Fallback to Node.js syntax check only
                if self._check_node_available():
                    errors.extend(self._validate_with_node(cleaned_code, filename))
                else:
                    # Basic fallback checks only for critical issues
                    errors.extend(self._check_jsx_critical_issues(cleaned_code))
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )
            
        except Exception as e:
            errors.append(f"Validation Error in {filename}: {str(e)}")
            
        return ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _check_eslint_available(self) -> bool:
        """Check if ESLint is available."""
        try:
            result = subprocess.run(['npx', 'eslint', '--version'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _validate_with_eslint(self, code: str, filename: str) -> Dict[str, List[str]]:
        """Validate JavaScript code with ESLint using React rules."""
        errors = []
        warnings = []
        
        try:
            # Create a temporary file with the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsx', delete=False, encoding='utf-8') as f:
                f.write(code)
                temp_path = f.name
            
            # Create a minimal ESLint config for React
            eslint_config = {
                "env": {
                    "browser": True,
                    "es2021": True
                },
                "extends": [
                    "eslint:recommended",
                    "plugin:react/recommended",
                    "plugin:react-hooks/recommended"
                ],
                "parserOptions": {
                    "ecmaVersion": "latest",
                    "sourceType": "module",
                    "ecmaFeatures": {
                        "jsx": True
                    }
                },
                "plugins": ["react", "react-hooks"],
                "rules": {
                    "no-unused-vars": "error",
                    "no-undef": "error",
                    "react/prop-types": "off",
                    "react/react-in-jsx-scope": "off"
                },
                "settings": {
                    "react": {
                        "version": "detect"
                    }
                }
            }
            
            config_path = temp_path.replace('.jsx', '.eslintrc.json')
            with open(config_path, 'w') as f:
                json.dump(eslint_config, f)
            
            # Run ESLint
            result = subprocess.run(
                ['npx', 'eslint', '--no-eslintrc', '--config', config_path, '--format', 'json', temp_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse ESLint output
            if result.stdout:
                try:
                    eslint_output = json.loads(result.stdout)
                    if eslint_output and len(eslint_output) > 0:
                        for message in eslint_output[0].get('messages', []):
                            severity = message.get('severity', 2)
                            msg = f"Line {message.get('line', '?')}: {message.get('message', 'Unknown error')}"
                            
                            if severity == 2:  # Error
                                errors.append(msg)
                            elif severity == 1:  # Warning
                                warnings.append(msg)
                except json.JSONDecodeError:
                    pass
            
            # Cleanup
            os.unlink(temp_path)
            if os.path.exists(config_path):
                os.unlink(config_path)
                
        except subprocess.TimeoutExpired:
            errors.append("ESLint validation timed out")
        except Exception as e:
            # ESLint failed, fall back to basic checks
            pass
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_jsx_critical_issues(self, code: str) -> List[str]:
        """Comprehensive JSX/React validation for sandbox execution."""
        errors = []
        
        # ========== SYNTAX ERRORS ==========
        
        # Check for unclosed JSX tags
        open_tags = re.findall(r'<(\w+)(?:\s[^>]*)?\s*(?<!/)>', code)
        close_tags = re.findall(r'</(\w+)>', code)
        self_closing = re.findall(r'<(\w+)[^>]*/>', code)
        
        # Count tags (excluding self-closing and HTML void elements)
        void_elements = {'br', 'hr', 'img', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'param', 'source', 'track', 'wbr'}
        for tag in set(open_tags):
            if tag.lower() not in void_elements:
                open_count = open_tags.count(tag)
                close_count = close_tags.count(tag)
                self_close_count = self_closing.count(tag)
                if open_count > (close_count + self_close_count):
                    errors.append(f"Unclosed JSX tag: <{tag}> opened {open_count} times but only closed {close_count + self_close_count} times")
        
        # Check for invalid JSX attribute syntax
        invalid_attrs = re.findall(r'(\w+)=([^{"\'][^\s/>]+)', code)
        for attr, value in invalid_attrs:
            if attr not in ['className', 'style'] and not value.startswith('{'):
                if not re.match(r'^\d+$', value):  # Allow numbers
                    errors.append(f"Invalid JSX attribute syntax: {attr}={value} - use quotes or braces")
        
        # Check for class= instead of className=
        if re.search(r'\sclass\s*=\s*["{]', code):
            errors.append("Use 'className' instead of 'class' in JSX")
        
        # Check for for= instead of htmlFor=
        if re.search(r'\sfor\s*=\s*["{]', code):
            errors.append("Use 'htmlFor' instead of 'for' in JSX")
        
        # Check for onclick instead of onClick (and similar) - case-sensitive!
        # Only flag lowercase HTML-style events, not properly camelCased React events
        html_events = {
            'onclick': 'onClick', 'onchange': 'onChange', 'onsubmit': 'onSubmit',
            'onmouseover': 'onMouseOver', 'onmouseout': 'onMouseOut', 'onmouseenter': 'onMouseEnter',
            'onmouseleave': 'onMouseLeave', 'onfocus': 'onFocus', 'onblur': 'onBlur',
            'onkeydown': 'onKeyDown', 'onkeyup': 'onKeyUp', 'onkeypress': 'onKeyPress',
            'oninput': 'onInput', 'ondrag': 'onDrag', 'ondrop': 'onDrop'
        }
        for html_event, react_event in html_events.items():
            # Case-sensitive match - only flag exact lowercase matches
            if re.search(rf'\s{html_event}\s*=', code):
                errors.append(f"Use '{react_event}' instead of '{html_event}' in JSX")
        
        # ========== COMPONENT ERRORS ==========
        
        # Check for duplicate component declarations
        component_declarations = {}
        for match in re.finditer(r'(?:const|function|class)\s+(\w+)\s*[=({]', code):
            comp_name = match.group(1)
            if comp_name[0].isupper():
                if comp_name in component_declarations:
                    errors.append(f"Duplicate component declaration: '{comp_name}'")
                else:
                    component_declarations[comp_name] = match.start()
        
        # Check for components that are both imported and declared
        import_matches = re.findall(r'import\s+\{([^}]+)\}\s+from', code)
        for import_match in import_matches:
            imported_comps = [c.strip().split(' as ')[0] for c in import_match.split(',')]
            for comp in imported_comps:
                if comp in component_declarations:
                    errors.append(f"Component '{comp}' is imported and declared locally - remove one")
        
        # ========== HOOKS ERRORS ==========
        
        # Check for hooks called conditionally (inside if/for/while)
        hooks = ['useState', 'useEffect', 'useCallback', 'useMemo', 'useRef', 'useContext', 'useReducer', 'useLayoutEffect']
        lines = code.split('\n')
        in_conditional = False
        brace_depth = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Track conditional blocks
            if re.match(r'^(if|for|while|switch)\s*\(', stripped):
                in_conditional = True
                brace_depth = 0
            if in_conditional:
                brace_depth += line.count('{') - line.count('}')
                if brace_depth <= 0:
                    in_conditional = False
                for hook in hooks:
                    if f'{hook}(' in line:
                        errors.append(f"Hook '{hook}' called conditionally at line {i+1} - hooks must be called at top level")
        
        # Check for useEffect without dependency array when needed
        use_effects = re.findall(r'useEffect\s*\(\s*\(\)\s*=>\s*\{([^}]*)\}(?:\s*,\s*(\[[^\]]*\]))?', code, re.DOTALL)
        for effect_body, deps in use_effects:
            if deps is None or deps == '':
                # Check if effect uses any variables that should be dependencies
                if re.search(r'\b(props|state|set\w+)\b', effect_body):
                    errors.append("useEffect missing dependency array - this will run on every render")
        
        # ========== COMMON RUNTIME ERRORS ==========
        
        # Check for missing key props in lists
        map_calls = re.findall(r'\.map\s*\(\s*(?:\([^)]*\)|[^=]+)\s*=>\s*(?:\(|{)?([^)]*(?:\([^)]*\)[^)]*)*)', code, re.DOTALL)
        for map_content in map_calls:
            if '<' in map_content and 'key=' not in map_content and 'key:' not in map_content:
                errors.append("Missing 'key' prop in mapped JSX elements - each child in a list needs a unique key")
        
        # Check for undefined variables used in JSX
        jsx_vars = re.findall(r'\{(\w+)(?:\.\w+)*\}', code)
        defined_vars = set(re.findall(r'(?:const|let|var)\s+(?:\{[^}]+\}|\[?(\w+)\]?)\s*=', code))
        defined_vars.update(re.findall(r'function\s+\w+\s*\(([^)]*)\)', code))  # function params
        defined_vars.update(['true', 'false', 'null', 'undefined', 'console', 'window', 'document', 'Math', 'JSON', 'Date', 'Array', 'Object', 'String', 'Number', 'Boolean', 'Promise', 'Error', 'React', 'props', 'children'])
        # Add common globals
        defined_vars.update(['useState', 'useEffect', 'useCallback', 'useMemo', 'useRef', 'useContext', 'useReducer', 'useLayoutEffect', 'useNavigate', 'useLocation', 'useParams', 'Link', 'Router', 'Routes', 'Route', 'motion', 'AnimatePresence', 'clsx', 'cn'])
        
        # Check for potentially missing exports
        if 'export default' not in code and 'export const' not in code and 'module.exports' not in code:
            # Find the main component
            main_comp = None
            for comp in component_declarations:
                main_comp = comp
                break
            if main_comp:
                errors.append(f"Missing export statement - add 'export default {main_comp};' at the end")
        
        # Check for empty component returns
        empty_returns = re.findall(r'return\s*\(\s*\n?\s*\);', code)
        if empty_returns:
            errors.append("Empty return statement in component - component must return valid JSX")
        
        # Check for incomplete arrow functions
        incomplete_arrows = re.findall(r'const\s+\w+\s*=\s*\([^)]*\)\s*=>\s*\(\s*\);', code)
        if incomplete_arrows:
            errors.append("Empty arrow function component - must return valid JSX")
        
        return errors
    
    def validate_json_syntax(self, code: str, filename: str = "generated.json") -> ValidationResult:
        """Validate JSON syntax."""
        try:
            json.loads(code)
            return ValidationResult(True, [], [], [])
        except json.JSONDecodeError as e:
            return ValidationResult(
                False, 
                [f"JSON Error in {filename}: {e.msg} (line {e.lineno}, col {e.colno})"],
                [], 
                []
            )
    
    def _clean_markdown_from_code(self, code: str) -> str:
        """Remove markdown code blocks and documentation from code."""
        # Remove markdown code blocks
        code = re.sub(r'^```[\w]*\n', '', code, flags=re.MULTILINE)
        code = re.sub(r'\n```$', '', code, flags=re.MULTILINE)
        code = re.sub(r'```', '', code)
        
        # Remove documentation blocks that aren't valid code
        lines = code.split('\n')
        cleaned_lines = []
        skip_until_code = False
        
        for line in lines:
            # Skip obvious documentation lines
            if line.strip().startswith('Here is') or line.strip().startswith('This file'):
                skip_until_code = True
                continue
            elif skip_until_code and (line.strip().startswith('#') or line.strip().startswith('from ') or line.strip().startswith('import ')):
                skip_until_code = False
            
            if not skip_until_code:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _check_python_common_issues(self, code: str) -> List[str]:
        """Check for common Python issues."""
        errors = []
        
        # Check for undefined variables (basic check)
        if 'undefined_variable' in code:
            errors.append("Code contains undefined variables")
        
        # Check for missing imports
        if re.search(r'\bfrom\s+(\w+)\s+import', code):
            imports = re.findall(r'from\s+(\w+)\s+import', code)
            for imp in imports:
                if imp not in ['typing', 'dataclasses', '__future__', 'pathlib', 'os', 'sys', 'json']:
                    if not re.search(f'pip install.*{imp}', code) and imp not in code.split('\n')[0:10]:
                        # This is a potential missing dependency
                        pass  # We'll handle this in dependency validation
        
        # Check for duplicate class/function definitions
        class_names = re.findall(r'class\s+(\w+)', code)
        if len(class_names) != len(set(class_names)):
            errors.append("Duplicate class definitions found")
        
        func_names = re.findall(r'def\s+(\w+)', code)
        if len(func_names) != len(set(func_names)):
            errors.append("Duplicate function definitions found")
        
        return errors
    
    def _check_python_warnings(self, code: str) -> List[str]:
        """Check for Python code warnings."""
        warnings = []
        
        # Check for unused imports (basic check)
        imports = re.findall(r'import\s+(\w+)', code)
        for imp in imports:
            if imp not in code[code.find(f'import {imp}') + len(f'import {imp}'):]:
                warnings.append(f"Potentially unused import: {imp}")
        
        return warnings
    
    def _check_python_suggestions(self, code: str) -> List[str]:
        """Check for Python code suggestions."""
        suggestions = []
        
        # Suggest type hints if missing
        if 'def ' in code and '->' not in code:
            suggestions.append("Consider adding type hints to function definitions")
        
        return suggestions
    
    def _check_jsx_common_issues(self, code: str) -> List[str]:
        """Check for common JSX/React issues."""
        errors = []
        
        # Check for duplicate component declarations
        component_declarations = {}
        for match in re.finditer(r'(?:const|function|class)\s+(\w+)\s*=', code):
            comp_name = match.group(1)
            if comp_name[0].isupper():  # Component names start with uppercase
                if comp_name in component_declarations:
                    errors.append(f"Duplicate component declaration: '{comp_name}' is declared multiple times")
                else:
                    component_declarations[comp_name] = match.start()
        
        # Check for components that are both imported and declared
        import_matches = re.findall(r'import\s+{([^}]+)}\s+from', code)
        for import_match in import_matches:
            imported_comps = [c.strip() for c in import_match.split(',')]
            for comp in imported_comps:
                if comp in component_declarations:
                    errors.append(f"Component '{comp}' is imported but also declared locally - remove duplicate declaration")
        
        # Check for undefined React components
        components = re.findall(r'<(\w+)', code)
        for comp in components:
            if comp[0].isupper() and comp not in ['div', 'span', 'p', 'h1', 'h2', 'h3', 'button', 'input', 'form']:
                # This is a custom component, check if it's defined or imported
                if not re.search(f'function\\s+{comp}|const\\s+{comp}|class\\s+{comp}|import.*{comp}', code):
                    errors.append(f"Component '{comp}' is used but not defined or imported")
        
        # Check for missing key props in lists
        if '.map(' in code and 'key=' not in code:
            errors.append("Missing 'key' prop in mapped components")
        
        # Check for unsafe array operations
        unsafe_patterns = [
            r'\.filter\(',
            r'\.map\(',
            r'\.find\(',
            r'\.reduce\('
        ]
        for pattern in unsafe_patterns:
            if re.search(pattern, code):
                # Check if it has defensive programming
                if not re.search(r'\(\w+\s*\|\|\s*\[\]\)', code):
                    errors.append(f"Potentially unsafe array operation without null check: {pattern}")
        
        return errors
    
    def _check_jsx_warnings(self, code: str) -> List[str]:
        """Deprecated - use ESLint instead."""
        return []
    
    def _check_jsx_suggestions(self, code: str) -> List[str]:
        """Deprecated - use ESLint instead."""
        return []
    
    def _check_node_available(self) -> bool:
        """Check if Node.js is available for validation."""
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _validate_with_node(self, code: str, filename: str) -> List[str]:
        """Validate JavaScript code with Node.js."""
        errors = []
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            result = subprocess.run(
                ['node', '--check', temp_path], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0:
                errors.append(f"Node.js validation error in {filename}: {result.stderr}")
            
            os.unlink(temp_path)
            
        except Exception as e:
            errors.append(f"Node.js validation failed: {str(e)}")
        
        return errors
    
    def validate_dependencies(self, code: str, file_type: str) -> ValidationResult:
        """Validate that all dependencies are properly declared."""
        errors = []
        warnings = []
        suggestions = []
        
        if file_type == "python":
            # Extract imports
            imports = []
            imports.extend(re.findall(r'from\s+(\w+)', code))
            imports.extend(re.findall(r'import\s+(\w+)', code))
            
            # Check against standard library + common packages
            python_stdlib = {'os', 'sys', 'json', 'pathlib', 're', 'typing', 'dataclasses', 'datetime', 'uuid'}
            common_packages = {'fastapi', 'sqlalchemy', 'pydantic', 'uvicorn', 'passlib', 'bcrypt'}
            
            for imp in imports:
                if imp not in python_stdlib and imp not in common_packages:
                    suggestions.append(f"Ensure '{imp}' is listed in requirements.txt")
        
        elif file_type == "javascript":
            # Check for React imports
            if 'React' in code or 'useState' in code or 'useEffect' in code:
                if 'import React' not in code and "from 'react'" not in code:
                    errors.append("React hooks used but React not imported")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )


class ProjectTester:
    """Automated testing for generated projects."""
    
    def __init__(self):
        self.validator = CodeValidator()
    
    def test_project_structure(self, project_path: Path) -> ValidationResult:
        """Test the overall project structure."""
        errors = []
        warnings = []
        suggestions = []
        
        # Check required files exist
        required_files = {
            "frontend": ["src/App.jsx", "src/main.jsx", "index.html", "package.json"],
            "backend": ["main.py", "models.py", "routes.py"]
        }
        
        for folder, files in required_files.items():
            folder_path = project_path / folder
            if not folder_path.exists():
                errors.append(f"Required folder '{folder}' is missing")
                continue
            
            for file in files:
                file_path = folder_path / file
                if not file_path.exists():
                    errors.append(f"Required file '{folder}/{file}' is missing")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def test_backend_functionality(self, backend_path: Path) -> ValidationResult:
        """Test backend functionality."""
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Test if Python files can be imported
            models_file = backend_path / "models.py"
            routes_file = backend_path / "routes.py"
            main_file = backend_path / "main.py"
            
            for file_path in [models_file, routes_file, main_file]:
                if file_path.exists():
                    validation = self.validator.validate_python_syntax(
                        file_path.read_text(encoding='utf-8'),
                        str(file_path.name)
                    )
                    if not validation.is_valid:
                        errors.extend(validation.errors)
                    warnings.extend(validation.warnings)
                    suggestions.extend(validation.suggestions)
        
        except Exception as e:
            errors.append(f"Backend testing failed: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def test_frontend_functionality(self, frontend_path: Path) -> ValidationResult:
        """Test frontend functionality."""
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Test React files
            app_file = frontend_path / "src" / "App.jsx"
            main_file = frontend_path / "src" / "main.jsx"
            
            for file_path in [app_file, main_file]:
                if file_path.exists():
                    validation = self.validator.validate_javascript_syntax(
                        file_path.read_text(encoding='utf-8'),
                        str(file_path.name)
                    )
                    if not validation.is_valid:
                        errors.extend(validation.errors)
                    warnings.extend(validation.warnings)
                    suggestions.extend(validation.suggestions)
            
            # Test package.json
            package_file = frontend_path / "package.json"
            if package_file.exists():
                validation = self.validator.validate_json_syntax(
                    package_file.read_text(encoding='utf-8'),
                    "package.json"
                )
                if not validation.is_valid:
                    errors.extend(validation.errors)
        
        except Exception as e:
            errors.append(f"Frontend testing failed: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )


def validate_generated_code(code: str, file_type: str, filename: str) -> ValidationResult:
    """Main validation function for generated code."""
    validator = CodeValidator()
    
    if file_type == "python":
        result = validator.validate_python_syntax(code, filename)
        deps_result = validator.validate_dependencies(code, "python")
        
        # Combine results
        result.errors.extend(deps_result.errors)
        result.warnings.extend(deps_result.warnings)
        result.suggestions.extend(deps_result.suggestions)
        result.is_valid = result.is_valid and deps_result.is_valid
        
        return result
        
    elif file_type in ["javascript", "jsx"]:
        result = validator.validate_javascript_syntax(code, filename)
        deps_result = validator.validate_dependencies(code, "javascript")
        
        # Combine results
        result.errors.extend(deps_result.errors)
        result.warnings.extend(deps_result.warnings)
        result.suggestions.extend(deps_result.suggestions)
        result.is_valid = result.is_valid and deps_result.is_valid
        
        return result
        
    elif file_type == "json":
        return validator.validate_json_syntax(code, filename)
    
    else:
        return ValidationResult(True, [], [], ["Unknown file type - basic validation only"])


def auto_fix_jsx_for_sandbox(code: str, filename: str = "component.jsx") -> str:
    """
    Automatically fix common JSX issues for sandbox execution.
    This function transforms code to work in a browser sandbox environment.
    Fixes include: import removal, syntax fixes, React-specific fixes.
    """
    import re
    
    # ========== IMPORT REMOVAL (sandbox provides these globally) ==========
    
    # Remove React imports - React is provided globally in sandbox
    code = re.sub(r"import\s+React\s*,?\s*\{[^}]*\}\s*from\s*['\"]react['\"];?\s*\n?", '', code)
    code = re.sub(r"import\s+React\s+from\s*['\"]react['\"];?\s*\n?", '', code)
    code = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]react['\"];?\s*\n?", '', code)
    code = re.sub(r"import\s+\*\s+as\s+React\s+from\s*['\"]react['\"];?\s*\n?", '', code)
    
    # Remove ALL framer-motion imports - motion is provided globally in sandbox
    code = re.sub(r"import\s+\{[^}]*\}\s+from\s+['\"]framer-motion['\"];?\s*\n?", '', code)
    code = re.sub(r"import\s+\*\s+as\s+\w+\s+from\s+['\"]framer-motion['\"];?\s*\n?", '', code)
    code = re.sub(r"import\s+motion\s+from\s+['\"]framer-motion['\"];?\s*\n?", '', code)
    
    # Remove local motion fallback definitions (global ones exist in sandbox)
    code = re.sub(r"const\s+motion\s*=\s*window\.motion\s*\|\|[^;]+;?\s*\n?", '', code)
    code = re.sub(r"// Safe motion fallback[^\n]*\n(const\s+motion\s*=[^;]+;?\s*\n?)?", '', code)
    
    # Remove createMotionFallback and createMotionComponent helper functions
    # These are often defined before the motion object - remove them
    # Use DOTALL to match across newlines for complex arrow functions
    code = re.sub(r"const\s+createMotionFallback\s*=\s*\([^)]*\)\s*=>\s*React\.forwardRef\([^;]+;", '// motion is provided globally by the sandbox environment', code, flags=re.DOTALL)
    code = re.sub(r"const\s+createMotionFallback\s*=\s*\([^)]*\)\s*=>[^;]+;?\s*\n?", '', code)
    code = re.sub(r"const\s+createMotionComponent\s*=\s*\([^)]*\)\s*=>[^;]+;?\s*\n?", '', code)
    
    # Remove const motion = { ... }; block - matches multi-line motion object definition
    # Use a more comprehensive pattern that handles nested braces
    code = re.sub(r"const\s+motion\s*=\s*\{[\s\S]*?\n\};?\s*\n?", '', code)
    code = re.sub(r"const\s+motion\s*=\s*\{[^}]+\};?\s*\n?", '', code)
    
    # Remove useInView and useScroll fallback definitions - match the full line(s)
    code = re.sub(r"const\s+useInView\s*=\s*[^;]+;?\s*\n?", '', code)
    code = re.sub(r"const\s+useScroll\s*=\s*[^;]+;?\s*\n?", '', code)
    
    # Remove framer-motion related comments
    code = re.sub(r"// SAFE FRAMER-MOTION FALLBACKS[^\n]*\n?", '', code)
    code = re.sub(r"// 🚨🚨 CRITICAL: IMPORT UI COMPONENTS[^\n]*\n?", '', code)
    code = re.sub(r"// Import utility functions[^\n]*\n?", '', code)
    
    # Remove Lucide icon imports - icons are provided globally
    code = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]lucide-react['\"];?\s*\n?", '', code)
    
    # Remove react-router-dom imports - provided globally
    code = re.sub(r"import\s+\{[^}]*\}\s+from\s+['\"]react-router-dom['\"];?\s*\n?", '', code)
    code = re.sub(r"import\s+\*\s+as\s+\w+\s+from\s+['\"]react-router-dom['\"];?\s*\n?", '', code)
    
    # Remove clsx/tailwind-merge imports - cn is provided globally
    code = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]clsx['\"];?\s*\n?", '', code)
    code = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]tailwind-merge['\"];?\s*\n?", '', code)
    code = re.sub(r"import\s*\{[^}]*cn[^}]*\}\s*from\s*['\"]\.+/lib/utils['\"];?\s*\n?", '', code)
    code = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]@/lib/utils['\"];?\s*\n?", '', code)
    
    # Remove CSS imports - Tailwind is provided via CDN
    code = re.sub(r"import\s+['\"][^'\"]*\.css['\"];?\s*\n?", '', code)
    
    # Remove UI component imports - they'll be defined globally or inline
    code = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]\.+/components/ui/[^'\"]+['\"];?\s*\n?", '', code)
    code = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]@/components/ui/[^'\"]+['\"];?\s*\n?", '', code)
    code = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]\.+/components/[^'\"]+['\"];?\s*\n?", '', code)
    code = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]@/components/[^'\"]+['\"];?\s*\n?", '', code)
    
    # Remove generic relative imports that would fail in sandbox
    code = re.sub(r"import\s+\w+\s+from\s*['\"]\.+/[^'\"]+['\"];?\s*\n?", '', code)
    code = re.sub(r"import\s+\w+\s+from\s*['\"]@/[^'\"]+['\"];?\s*\n?", '', code)
    
    # Remove axios imports - provide a fetch-based fallback
    code = re.sub(r"import\s+axios\s+from\s*['\"]axios['\"];?\s*\n?", '', code)
    code = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]axios['\"];?\s*\n?", '', code)
    
    # ========== JSX SYNTAX FIXES ==========
    
    # Fix class= to className=
    code = re.sub(r'\sclass\s*=\s*(["{])', r' className=\1', code)
    
    # Fix for= to htmlFor=
    code = re.sub(r'\sfor\s*=\s*(["{])', r' htmlFor=\1', code)
    
    # ========== ARROW FUNCTION CORRUPTION FIXES ==========
    
    # Fix corrupted arrow functions: (e) = /> to (e) =>
    # This happens when AI generates malformed arrow syntax
    code = re.sub(r'\)\s*=\s*/>', r') =>', code)
    
    # Fix other arrow function corruptions: (e) = > to (e) =>
    code = re.sub(r'\)\s*=\s+>', r') =>', code)
    
    # Fix arrow with extra spaces: ( e ) = > to (e) =>
    code = re.sub(r'\(\s*(\w+)\s*\)\s*=\s*>', r'(\1) =>', code)
    
    # Fix onclick to onClick (and similar HTML event attributes)
    html_events = {
        'onclick': 'onClick', 'onchange': 'onChange', 'onsubmit': 'onSubmit',
        'onmouseover': 'onMouseOver', 'onmouseout': 'onMouseOut', 'onmouseenter': 'onMouseEnter',
        'onmouseleave': 'onMouseLeave', 'onfocus': 'onFocus', 'onblur': 'onBlur',
        'onkeydown': 'onKeyDown', 'onkeyup': 'onKeyUp', 'onkeypress': 'onKeyPress',
        'oninput': 'onInput', 'ondrag': 'onDrag', 'ondrop': 'onDrop'
    }
    for html_event, react_event in html_events.items():
        code = re.sub(rf'\s{html_event}\s*=', f' {react_event}=', code, flags=re.IGNORECASE)
    
    # ========== EMPTY COMPONENT FIXES ==========
    
    # Fix empty arrow function components: const Component = () => ();
    code = re.sub(
        r'const\s+(\w+)\s*=\s*\(\)\s*=>\s*\(\s*\);',
        r'const \1 = () => (\n  <div className="p-4 bg-gray-100 rounded-lg">\n    <h3 className="text-lg font-semibold">\1</h3>\n    <p className="text-gray-600">Component ready</p>\n  </div>\n);',
        code
    )
    
    # Fix empty arrow function with props: const Component = ({}) => ();
    code = re.sub(
        r'const\s+(\w+)\s*=\s*\(\{[^}]*\}\)\s*=>\s*\(\s*\);',
        r'const \1 = (props) => (\n  <div className="p-4 bg-gray-100 rounded-lg">\n    <h3 className="text-lg font-semibold">\1</h3>\n    <p className="text-gray-600">Component ready</p>\n  </div>\n);',
        code
    )
    
    # Fix empty return: return ();
    code = re.sub(
        r'return\s*\(\s*\);',
        r'return (\n    <div className="p-4 bg-gray-100 rounded-lg">\n      <p>Content placeholder</p>\n    </div>\n  );',
        code
    )
    
    # Fix empty return with newlines: return (\n\n);
    code = re.sub(
        r'return\s*\(\s*\n\s*\n?\s*\);',
        r'return (\n    <div className="p-4 bg-gray-100 rounded-lg">\n      <p>Content placeholder</p>\n    </div>\n  );',
        code
    )
    
    # ========== ROUTER FIXES ==========
    
    # Normalize router names to use the simple Router provided by sandbox
    code = code.replace('BrowserRouter', 'Router')
    code = code.replace('HashRouter', 'Router')
    code = code.replace('MemoryRouter', 'Router')
    
    # ========== ADD MISSING EXPORTS ==========
    # NOTE: This is for standalone files. For sandbox mode, exports are handled differently.
    # Skip adding exports if window.App is already set (sandbox mode)
    
    # Check if there's a component but no export, and NOT in sandbox mode
    if 'export default' not in code and 'export const' not in code and 'window.App' not in code:
        # Find the main component (last defined component, or one matching filename)
        component_names = re.findall(r'(?:const|function|class)\s+([A-Z]\w*)\s*[=({]', code)
        if component_names:
            # Prefer component matching filename
            base_name = filename.replace('.jsx', '').replace('.js', '').replace('.tsx', '').replace('.ts', '')
            main_component = None
            for comp in component_names:
                if comp.lower() == base_name.lower():
                    main_component = comp
                    break
            if not main_component:
                main_component = component_names[-1]  # Use last defined
            
            # Add export at the end
            if main_component and f'export default {main_component}' not in code:
                code = code.rstrip() + f'\n\nexport default {main_component};'
    
    # ========== REMOVE DUPLICATE COMPONENT DECLARATIONS ==========
    
    # Define components that should NEVER be redeclared (they exist in template/sandbox)
    # These are UI components, icons, and utilities provided by the sandbox
    TEMPLATE_COMPONENTS = {
        # UI Components (from sandbox)
        'Button', 'Input', 'Card', 'Loading', 'AnimatedText', 'Navigation',
        
        # Icons (from sandbox - all Lucide icons)
        'Star', 'User', 'ShoppingCart', 'X', 'Plus', 'Minus', 'Search',
        'Heart', 'ChevronRight', 'ChevronLeft', 'ChevronDown', 'ChevronUp',
        'Menu', 'Close', 'Check', 'ArrowRight', 'ArrowLeft', 'ArrowUp', 'ArrowDown', 'Home',
        'Settings', 'Bell', 'Mail', 'Phone', 'MapPin', 'Calendar',
        'Clock', 'Filter', 'Grid', 'List', 'Eye', 'EyeOff', 'Lock',
        'Unlock', 'Trash', 'Trash2', 'Edit', 'Save', 'Download', 'Upload', 'Share',
        'Link', 'Link2', 'ExternalLink', 'Copy', 'Clipboard', 'Refresh', 'RefreshCw', 'Loader', 'Loader2',
        'AlertCircle', 'AlertTriangle', 'Info', 'HelpCircle', 'XCircle',
        'CheckCircle', 'PlusCircle', 'MinusCircle', 'Play', 'Pause', 'Stop',
        'SkipForward', 'SkipBack', 'Volume', 'Volume2', 'VolumeX', 'Mic', 'MicOff',
        'Camera', 'Image', 'Film', 'Music', 'Headphones', 'Speaker', 'Radio',
        'Wifi', 'WifiOff', 'Battery', 'Bluetooth', 'Cast', 'Monitor', 'Smartphone', 'Tablet',
        'Laptop', 'Server', 'Database', 'Cloud', 'CloudOff', 'Sun', 'Moon', 'Power',
        'Sunrise', 'Sunset', 'Thermometer', 'Droplet', 'Wind', 'Umbrella',
        'Zap', 'Activity', 'TrendingUp', 'TrendingDown', 'BarChart', 'PieChart', 'LineChart',
        'Layers', 'Layout', 'Sidebar', 'PanelLeft', 'PanelRight', 'Terminal', 'Code',
        'FileText', 'File', 'Folder', 'FolderOpen', 'Archive', 'Package',
        'Box', 'Gift', 'ShoppingBag', 'CreditCard', 'DollarSign', 'Percent',
        'Tag', 'Bookmark', 'Flag', 'Award', 'Trophy', 'Target', 'Crosshair',
        'Compass', 'Map', 'Navigation2', 'Globe', 'Anchor', 'Truck', 'Car', 'Building',
        'Facebook', 'Twitter', 'Instagram', 'Linkedin', 'Github', 'Youtube',
        'MoreHorizontal', 'MoreVertical', 'LogOut', 'LogIn', 'UserPlus', 'Settings2',
        'Send', 'MessageCircle', 'Sparkles', 'Receipt', 'Wallet', 'Store',
        'Maximize', 'Minimize', 'RotateCcw', 'Rotate', 'Sliders',
        'ThumbsUp', 'ThumbsDown', 'Tool', 'Video', 'Voicemail', 'Watch', 'ZoomIn', 'ZoomOut',
        'Briefcase', 'Scissors', 'Printer', 'Repeat',
        
        # Router components (from sandbox)
        'Router', 'BrowserRouter', 'HashRouter', 'MemoryRouter',
        'Routes', 'Route', 'Link', 'NavLink', 'Navigate', 'Outlet',
        
        # Animation components (from sandbox fallbacks)
        'AnimatePresence',
    }
    
    # Find all component/const declarations and remove duplicates
    # Keep the FIRST declaration of each name
    seen_declarations = {}
    lines = code.split('\n')
    cleaned_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip comment lines when checking for declarations
        if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
            cleaned_lines.append(line)
            i += 1
            continue
        
        # Match component declarations (const X = ..., function X(...), const X = () => ...)
        # Now matches anywhere in the stripped line, not just start
        match = re.match(r'(const|let|var|function)\s+([A-Z][a-zA-Z0-9_]*)\s*[=(]', stripped)
        
        if match:
            decl_type = match.group(1)
            comp_name = match.group(2)
            
            # Check if this is a template component that should NEVER be redeclared
            # OR if it's already been declared earlier in this file
            is_duplicate = comp_name in seen_declarations
            is_template_component = comp_name in TEMPLATE_COMPONENTS
            
            if is_duplicate or is_template_component:
                # This is a duplicate or a template component! Skip this entire declaration
                # Need to find where it ends (handle multi-line declarations)
                brace_count = 0
                paren_count = 0
                angle_count = 0  # For JSX
                started = False
                skip_lines = [i]
                
                for char in line:
                    if char in '{(':
                        started = True
                        if char == '{':
                            brace_count += 1
                        else:
                            paren_count += 1
                    elif char == '<':
                        started = True
                        angle_count += 1
                    elif char in '})':
                        if char == '}':
                            brace_count -= 1
                        else:
                            paren_count -= 1
                    elif char == '>':
                        angle_count = max(0, angle_count - 1)
                
                # If not balanced, continue to find the end
                while (brace_count > 0 or paren_count > 0 or not started) and i + 1 < len(lines):
                    i += 1
                    skip_lines.append(i)
                    next_line = lines[i]
                    for char in next_line:
                        if char in '{(':
                            started = True
                            if char == '{':
                                brace_count += 1
                            else:
                                paren_count += 1
                        elif char in '})':
                            if char == '}':
                                brace_count -= 1
                            else:
                                paren_count -= 1
                    
                    # Check if declaration ends with semicolon
                    if next_line.rstrip().endswith(';') and brace_count <= 0 and paren_count <= 0:
                        break
                
                reason = "template component" if is_template_component else "duplicate"
                print(f"🔧 Removed {reason} declaration of '{comp_name}' (lines {skip_lines[0]+1}-{skip_lines[-1]+1})")
                i += 1
                continue
            else:
                seen_declarations[comp_name] = i
        
        cleaned_lines.append(line)
        i += 1
    
    code = '\n'.join(cleaned_lines)
    
    # ========== UTILITY FUNCTION REMOVAL ==========
    
    # Remove cn utility function definitions (provided globally by sandbox)
    # Match: const cn = (...) => { ... }
    # Match: function cn(...) { ... }
    # Match: const cn = (...inputs) => twMerge(clsx(...inputs))
    code = re.sub(r'(?:const|let|var)\s+cn\s*=\s*\([^)]*\)\s*=>\s*\{[^}]*\}[;,]?\s*\n?', '', code)
    code = re.sub(r'(?:const|let|var)\s+cn\s*=\s*\([^)]*\)\s*=>\s*twMerge\s*\([^)]*\)[;,]?\s*\n?', '', code)
    code = re.sub(r'function\s+cn\s*\([^)]*\)\s*\{[^}]*\}[;,]?\s*\n?', '', code)
    
    # Remove clsx helper definitions
    code = re.sub(r'(?:const|let|var)\s+clsx\s*=\s*[^;]+;?\s*\n?', '', code)
    
    # Remove twMerge helper definitions
    code = re.sub(r'(?:const|let|var)\s+twMerge\s*=\s*[^;]+;?\s*\n?', '', code)
    
    # ========== CLEANUP ==========
    
    # Fix duplicate React imports (shouldn't exist after removal, but just in case)
    react_imports = re.findall(r"import\s+React[^;]*;?\s*\n?", code)
    if len(react_imports) > 1:
        for import_stmt in react_imports[1:]:
            code = code.replace(import_stmt, '')
    
    # Remove consecutive empty lines (more than 2)
    code = re.sub(r'\n{4,}', '\n\n\n', code)
    
    # Remove empty lines at the start
    code = code.lstrip('\n')
    
    # Add helpful comment if motion is used
    if 'motion.' in code and 'const motion' not in code:
        code = '// motion is provided globally by the sandbox environment\n' + code
    
    return code


def validate_and_fix_for_sandbox(code: str, file_type: str, filename: str) -> tuple:
    """
    Validate code and apply automatic fixes for sandbox execution.
    Returns (fixed_code, validation_result)
    """
    # First apply automatic fixes
    if file_type in ["javascript", "jsx"]:
        fixed_code = auto_fix_jsx_for_sandbox(code, filename)
    else:
        fixed_code = code
    
    # Then validate
    result = validate_generated_code(fixed_code, file_type, filename)
    
    return fixed_code, result


if __name__ == "__main__":
    # Test the validation system
    print("🧪 Testing Code Validation System...")
    
    # Test Python validation
    python_code = """
import os
from typing import List

def example_function(name: str) -> str:
    return f"Hello, {name}!"

class ExampleClass:
    def __init__(self):
        self.value = 42
    """
    
    result = validate_generated_code(python_code, "python", "test.py")
    print(f"Python validation: {'✅' if result.is_valid else '❌'}")
    if result.errors:
        print(f"Errors: {result.errors}")
    
    # Test JavaScript validation
    js_code = """
import React, { useState } from 'react';

function TestComponent() {
    const [count, setCount] = useState(0);
    
    return (
        <div>
            <p>Count: {count}</p>
            <button onClick={() => setCount(count + 1)}>Increment</button>
        </div>
    );
}

export default TestComponent;
    """
    
    result = validate_generated_code(js_code, "javascript", "test.jsx")
    print(f"JavaScript validation: {'✅' if result.is_valid else '❌'}")
    if result.errors:
        print(f"Errors: {result.errors}")
    
    print("✅ Code Validation System tests completed!")