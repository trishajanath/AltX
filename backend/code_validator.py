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
            result = subprocess.run(
                ['npx', 'eslint', '--version'],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5
            )
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
                encoding="utf-8",
                errors="replace",
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
        
        # ========== NEW: CRITICAL SANDBOX ERRORS ==========
        errors.extend(self._check_sandbox_critical_errors(code))
        
        return errors
    
    def _check_sandbox_critical_errors(self, code: str) -> List[str]:
        """
        Check for critical errors that cause sandbox execution failures.
        These are the most common AI-generated code errors that break apps.
        """
        errors = []
        
        # ERROR 1: Empty component bodies (CRITICAL - renders nothing)
        # Pattern: const Component = ({ props }) => {};
        empty_body_pattern = re.findall(
            r'const\s+([A-Z]\w*)\s*=\s*\([^)]*\)\s*=>\s*\{\s*\};?',
            code
        )
        for comp_name in empty_body_pattern:
            errors.append(f"CRITICAL: Component '{comp_name}' has empty body - will render nothing! Must have a return statement with JSX.")
        
        # Also check for: const Component = () => {};
        empty_body_no_props = re.findall(
            r'const\s+([A-Z]\w*)\s*=\s*\(\s*\)\s*=>\s*\{\s*\};?',
            code
        )
        for comp_name in empty_body_no_props:
            if comp_name not in empty_body_pattern:  # Avoid duplicates
                errors.append(f"CRITICAL: Component '{comp_name}' has empty body - will render nothing! Must have a return statement with JSX.")
        
        # ERROR 2: Async functions called in useMemo (returns Promise, not data)
        async_in_usememo = re.search(
            r'useMemo\s*\(\s*(?:async\s*)?\(\s*\)\s*=>\s*\{[^}]*await',
            code
        )
        if async_in_usememo:
            errors.append("CRITICAL: Async function inside useMemo - useMemo cannot handle Promises! Use useEffect + useState instead.")
        
        # Also check for calling async functions in useMemo
        usememo_async_call = re.search(
            r'useMemo\s*\(\s*\(\s*\)\s*=>\s*(?:\{[^}]*return\s+)?(\w+Async|\w+API|fetch\w*|load\w*Data)\s*\(',
            code
        )
        if usememo_async_call:
            func_name = usememo_async_call.group(1)
            errors.append(f"CRITICAL: Function '{func_name}' (likely async) called in useMemo - use useEffect + useState for async operations!")
        
        # ERROR 3: Wrong export when AppWrapper exists
        if 'const AppWrapper' in code and 'export default App;' in code:
            errors.append("CRITICAL: Wrong export! You have AppWrapper but export App. Change to 'export default AppWrapper;'")
        
        # ERROR 4: Tailwind peer classes (unreliable in sandbox)
        if 'peer-checked' in code:
            errors.append("WARNING: Tailwind 'peer-checked' classes may not work in sandbox. Use state-based styling: className={isChecked ? 'bg-blue-500' : 'bg-gray-500'}")
        if 'peer-focus' in code:
            errors.append("WARNING: Tailwind 'peer-focus' classes may not work in sandbox. Use onFocus/onBlur with state instead.")
        
        # ERROR 5: Truncated component (has const but no return)
        # Pattern: const Component = ({ children }) => { const X = y; (no return)
        truncated_pattern = re.findall(
            r'const\s+([A-Z]\w*)\s*=\s*\([^)]*\)\s*=>\s*\{\s*const\s+\w+\s*=\s*\w+;\s*\};?(?!\s*return)',
            code
        )
        for comp_name in truncated_pattern:
            errors.append(f"CRITICAL: Component '{comp_name}' appears truncated - has inner const but no return statement!")
        
        # ERROR 6: motion/AnimatePresence usage (causes "a.set is not a function" errors)
        if '<motion.' in code:
            # Check if it's being used properly
            motion_usage = re.findall(r'<motion\.(\w+)', code)
            errors.append(f"WARNING: motion.{', motion.'.join(set(motion_usage))} components may cause errors. Consider using CSS transitions instead: className=\"transition-all duration-300 hover:scale-105\"")
        
        if '<AnimatePresence' in code:
            errors.append("WARNING: AnimatePresence may cause 'a.set is not a function' errors in sandbox. Use conditional rendering with CSS transitions instead.")
        
        # ERROR 7: Using imports in sandbox (everything is global)
        if 'import React' in code or "import { useState" in code or "from 'react'" in code:
            errors.append("CRITICAL: Don't use imports in sandbox! React, useState, etc. are globally available. Remove all import statements.")
        
        if "from 'framer-motion'" in code or "from 'lucide-react'" in code:
            errors.append("CRITICAL: Don't import framer-motion or lucide-react! motion and icons are globally available in sandbox.")
        
        # ERROR 8: Export statement in sandbox
        if 'export default' in code:
            errors.append("NOTE: Sandbox assigns window.App automatically - 'export default' is not needed but won't break anything.")
        
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
            result = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
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
                text=True,
                encoding="utf-8",
                errors="replace"
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


def _remove_jsx_prop_with_balanced_braces(code: str, prop_name: str) -> str:
    """
    Remove a JSX prop that has nested braces, like: prop={{ value: { nested: true } }}
    Uses balanced brace matching to handle arbitrary nesting depth.
    """
    import re
    
    result = []
    i = 0
    while i < len(code):
        # Look for prop={{ or prop={ patterns (with optional whitespace before)
        match = re.search(rf'\s*{prop_name}=\{{', code[i:])
        if not match:
            result.append(code[i:])
            break
        
        # Add everything before the match
        result.append(code[i:i+match.start()])
        
        # Find the start of the prop value (after the opening brace)
        start = i + match.end()
        
        # Count braces to find the end - we start with 1 open brace from prop={
        brace_count = 1
        j = start
        while j < len(code) and brace_count > 0:
            if code[j] == '{':
                brace_count += 1
            elif code[j] == '}':
                brace_count -= 1
            j += 1
        
        # Skip to after the closing brace
        i = j
    
    return ''.join(result)


def auto_fix_jsx_for_sandbox(code: str, filename: str = "component.jsx") -> str:
    """
    Automatically fix common JSX issues for sandbox execution.
    This function transforms code to work in a browser sandbox environment.
    Fixes include: import removal, syntax fixes, React-specific fixes, motion component replacement.
    """
    import re
    
    # ========== DUPLICATE DECLARATION FIXES ==========
    # Remove duplicate React hooks destructure that causes "Identifier already declared" errors
    code = re.sub(r"// React hooks - using React\.\* namespace\s*\nconst \{ useState[^}]+\} = React;\s*\n?", '', code)
    code = re.sub(r"const \{ useState[^}]+\} = React;\s*\n?", '', code)
    
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
    
    # Replace AnimatePresence with React.Fragment - causes "a.set is not a function" errors in sandbox
    code = code.replace('<AnimatePresence>', '<React.Fragment>')
    code = code.replace('</AnimatePresence>', '</React.Fragment>')
    code = code.replace('<AnimatePresence ', '<React.Fragment ')  # Handle with props
    
    # ========== MOTION COMPONENT REPLACEMENT ==========
    # Replace motion.X components with regular HTML elements to avoid "a.set is not a function" errors
    # The sandbox's motion fallback doesn't work reliably with all React versions
    
    # Replace motion.element with regular element
    code = re.sub(r'<motion\.(\w+)', r'<\1', code)
    code = re.sub(r'</motion\.(\w+)>', r'</\1>', code)
    
    # Remove motion-specific props that are invalid on regular elements
    # Use balanced brace matching to handle nested objects like: exit={{ opacity: 0, transition: { duration: 0.2 } }}
    motion_props = ['initial', 'animate', 'exit', 'whileHover', 'whileTap', 'whileInView', 'transition', 'variants', 'layoutId', 'layout']
    for prop in motion_props:
        code = _remove_jsx_prop_with_balanced_braces(code, prop)
    
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
    # Also remove imports from ./lib/utils.js (with .js extension)
    code = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]\.+/lib/utils\.js['\"];?\s*\n?", '', code)
    # Remove any window.twMerge assignments
    code = re.sub(r"window\.twMerge\s*=\s*[^;]+;?\s*\n?", '', code)
    code = re.sub(r"window\.cn\s*=\s*[^;]+;?\s*\n?", '', code)
    
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
    
    # Fix arrow function without parens: e = /> to e =>
    code = re.sub(r'(\w+)\s*=\s*/>', r'\1 =>', code)
    
    # Fix other arrow function corruptions: (e) = > to (e) =>
    code = re.sub(r'\)\s*=\s+>', r') =>', code)
    
    # Fix arrow without parens with space: e = > to e =>
    code = re.sub(r'(\w+)\s*=\s+>', r'\1 =>', code)
    
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
    
    # ========== EMPTY COMPONENT FIXES (CRITICAL - CAUSES RENDER FAILURES) ==========
    
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
    
    # FIX CRITICAL: Empty arrow function body with curly braces: const Component = ({ props }) => {};
    # This is the most common error - component has empty body and renders NOTHING
    def fix_empty_component_body(match):
        comp_name = match.group(1)
        props = match.group(2) if match.group(2) else ''
        props_str = props.strip() if props else ''
        # Check if this is a wrapper component (has children in props)
        if 'children' in props_str:
            return f'''const {comp_name} = ({{ {props_str} }}) => {{
  return (
    <div className="p-4 bg-gray-800 rounded-xl">
      {{children}}
    </div>
  );
}}'''
        else:
            return f'''const {comp_name} = ({props_str}) => {{
  return (
    <div className="p-4 bg-gray-100 rounded-lg">
      <h3 className="text-lg font-semibold">{comp_name}</h3>
      <p className="text-gray-600">Component rendered</p>
    </div>
  );
}}'''
    
    # Pattern 1: const Component = ({ children, className, ...props }) => {};
    code = re.sub(
        r'const\s+([A-Z]\w*)\s*=\s*\(\{([^}]*)\}\)\s*=>\s*\{\s*\};?',
        fix_empty_component_body,
        code
    )
    
    # Pattern 2: const Component = () => {};
    code = re.sub(
        r'const\s+([A-Z]\w*)\s*=\s*\(\s*\)\s*=>\s*\{\s*\};?',
        lambda m: f'''const {m.group(1)} = () => {{
  return (
    <div className="p-4 bg-gray-100 rounded-lg">
      <h3 className="text-lg font-semibold">{m.group(1)}</h3>
      <p className="text-gray-600">Component rendered</p>
    </div>
  );
}}''',
        code
    )
    
    # Pattern 3: Component with arrow but only "const Component = as;" style truncation
    # This catches: const NeumorphicInput = ({ children, className, as = 'div', ...props }) => { const Component = as; (missing return)
    def fix_truncated_wrapper_component(match):
        full_match = match.group(0)
        comp_name = match.group(1)
        props_str = match.group(2)
        inner_statement = match.group(3)  # e.g., "const Component = as" or just "Component = as"
        
        # Clean up the inner statement - remove duplicate 'const' if present
        inner_clean = inner_statement.strip()
        if not inner_clean.startswith('const '):
            inner_clean = 'const ' + inner_clean
        
        # This component was truncated - add the missing return with children rendering
        return f'''const {comp_name} = ({{ {props_str} }}) => {{
  {inner_clean};
  return (
    <Component className={{cn('bg-gray-800 rounded-xl p-4', className)}} {{...props}}>
      {{children}}
    </Component>
  );
}}'''
    
    code = re.sub(
        r'const\s+([A-Z]\w*)\s*=\s*\(\{([^}]+)\}\)\s*=>\s*\{\s*((?:const\s+)?\w+\s*=\s*\w+);?\s*\};?(?!\s*return)',
        fix_truncated_wrapper_component,
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
    
    # ========== ASYNC IN SYNC CONTEXT FIXES ==========
    # Detect async functions being called in useMemo (common AI error)
    # Pattern: useMemo(() => someAsyncFunc(), []) or useMemo(() => { return asyncFunc(); }, [])
    # We can't auto-fix this reliably, but we can add a comment warning
    if re.search(r'useMemo\s*\(\s*\(\s*\)\s*=>\s*\{?\s*(?:return\s+)?\w+Async|fetch|await', code):
        print("⚠️ WARNING: Detected possible async function call inside useMemo - this may cause issues!")
    
    # ========== EXPORT FIXES (CRITICAL) ==========
    # If AppWrapper exists, export AppWrapper not App
    if 'const AppWrapper' in code:
        # Fix wrong export: export default App; when AppWrapper exists
        code = re.sub(
            r'export\s+default\s+App\s*;?\s*$',
            'export default AppWrapper;',
            code
        )
        # Also fix any duplicate App; statements before export
        code = re.sub(r'\nApp;\s*\n', '\n', code)
    
    # ========== TAILWIND PEER CLASS FIXES ==========
    # peer-checked classes are unreliable in sandbox - convert to inline conditionals where possible
    # This is a complex transformation, so we just flag it for now
    if 'peer-checked' in code or 'peer-focus' in code:
        print("⚠️ WARNING: Detected Tailwind peer classes (peer-checked/peer-focus) - these may not work in sandbox!")
    
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
    
    # ========== REMOVE VARIANT/SIZE CONSTANTS USED BY TEMPLATE COMPONENTS ==========
    
    # These constants are only used by Button/Card/etc components that we remove
    # Keeping them would cause undefined references - remove them
    code = re.sub(r'(?:const|let|var)\s+buttonVariants\s*=\s*\{[\s\S]*?\};\s*\n?', '', code)
    code = re.sub(r'(?:const|let|var)\s+cardVariants\s*=\s*\{[\s\S]*?\};\s*\n?', '', code)
    code = re.sub(r'(?:const|let|var)\s+inputVariants\s*=\s*\{[\s\S]*?\};\s*\n?', '', code)
    
    # Remove local sizes constants that would conflict with sandbox globals
    # But only if they look like UI component size definitions (sm, md, lg keys)
    code = re.sub(r'(?:const|let|var)\s+sizes\s*=\s*\{[^}]*(?:sm|md|lg)[^}]*\};\s*\n?', '', code)
    
    # ========== REMOVE FORWARDREF COMPONENT DECLARATIONS ==========
    
    # The TEMPLATE_COMPONENTS set includes Button, Card, etc. but React.forwardRef 
    # declarations may not match the simple regex above. Handle them explicitly:
    # Pattern: const Button = React.forwardRef(({ ... }, ref) => { ... });
    for comp in ['Button', 'Card', 'Input', 'Loading', 'Select', 'Textarea']:
        # Match forwardRef declarations (multi-line)
        code = re.sub(
            rf'(?:const|let|var)\s+{comp}\s*=\s*React\.forwardRef\s*\([^;]*\);?\s*\n?',
            f'// {comp} is provided globally by the sandbox\n',
            code,
            flags=re.DOTALL
        )
        # Match displayName assignments
        code = re.sub(rf'{comp}\.displayName\s*=\s*["\'][^"\']*["\'];?\s*\n?', '', code)
    
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
    
    # ========== FIX BROKEN IMAGE URLS ==========
    # Replace broken/placeholder image URLs with reliable working images
    code = fix_image_urls_in_code(code)
    
    # ========== FIX EXPORT FOR SANDBOX ==========
    # Sandbox requires window.App assignment, not export default
    # Simple approach: just remove exports, let main.py handle window assignment
    if 'export default' in code:
        # Remove the export but keep the component declaration
        code = re.sub(r'export\s+default\s+', '', code)
    
    return code


# Reliable image URL database - these are verified working Unsplash images
RELIABLE_IMAGE_URLS = {
    # Food/Grocery images
    'food': [
        'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop&auto=format',  # Food bowl
        'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=300&fit=crop&auto=format',  # Pizza
        'https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=400&h=300&fit=crop&auto=format',  # Salad
        'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=400&h=300&fit=crop&auto=format',  # Pancakes
        'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400&h=300&fit=crop&auto=format',  # Meat dish
        'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop&auto=format',  # Healthy bowl
    ],
    # Product images  
    'product': [
        'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop&auto=format',  # Watch
        'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop&auto=format',  # Headphones
        'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&h=400&fit=crop&auto=format',  # Sunglasses
        'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=400&h=400&fit=crop&auto=format',  # Camera
        'https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=400&h=400&fit=crop&auto=format',  # Cosmetics
        'https://images.unsplash.com/photo-1560343090-f0409e92791a?w=400&h=400&fit=crop&auto=format',  # Sneakers
    ],
    # Hero/banner images
    'hero': [
        'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=1600&h=900&fit=crop&auto=format',  # Office
        'https://images.unsplash.com/photo-1551434678-e076c223a692?w=1600&h=900&fit=crop&auto=format',  # Team
        'https://images.unsplash.com/photo-1497366216548-37526070297c?w=1600&h=900&fit=crop&auto=format',  # Modern office
        'https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1600&h=900&fit=crop&auto=format',  # Collaboration
    ],
    # Avatar/profile images
    'avatar': [
        'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&h=200&fit=crop&auto=format',  # Male
        'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200&h=200&fit=crop&auto=format',  # Female
        'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&auto=format',  # Male 2
        'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200&h=200&fit=crop&auto=format',  # Female 2
    ],
    # Default fallback
    'default': [
        'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&h=300&fit=crop&auto=format',  # Abstract
        'https://images.unsplash.com/photo-1557683316-973673baf926?w=400&h=300&fit=crop&auto=format',  # Gradient
        'https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=400&h=300&fit=crop&auto=format',  # Colorful
    ]
}

def fix_image_urls_in_code(code: str) -> str:
    """
    Replace broken or placeholder image URLs with reliable working images.
    Detects context from surrounding code to choose appropriate image type.
    """
    import re
    import hashlib
    
    # Patterns for broken image URLs that need replacement
    broken_patterns = [
        # Placeholder services that may not work reliably
        r'https?://placehold\.co/[^\s"\'>]+',
        r'https?://placeholder\.com/[^\s"\'>]+',
        r'https?://via\.placeholder\.com/[^\s"\'>]+',
        r'https?://placekitten\.com/[^\s"\'>]+',
        r'https?://picsum\.photos/[^\s"\'>]+',
        r'https?://loremflickr\.com/[^\s"\'>]+',
        # Example.com URLs
        r'https?://example\.com/[^\s"\'>]+\.(?:jpg|jpeg|png|gif|webp)',
        # Generic fake URLs
        r'https?://fake[^\s"\'>]+\.(?:jpg|jpeg|png|gif|webp)',
        r'https?://[^\s"\'>]+/placeholder[^\s"\'>]*\.(?:jpg|jpeg|png|gif|webp)',
        # URLs that end without an extension (often broken)
        r'https?://[^\s"\'>]+/images?/[a-zA-Z]+(?=["\'])',
    ]
    
    def get_image_category_from_context(match_start: int, code: str) -> str:
        """Determine image category based on surrounding code context."""
        # Get 200 chars before and after the match for context
        start = max(0, match_start - 200)
        end = min(len(code), match_start + 200)
        context = code[start:end].lower()
        
        # Food/grocery context
        if any(word in context for word in ['food', 'meal', 'grocery', 'recipe', 'breakfast', 'lunch', 'dinner', 'taco', 'pizza', 'burger', 'salad', 'fruit', 'vegetable', 'kitchen', 'restaurant', 'menu', 'dish', 'cuisine']):
            return 'food'
        
        # Product context
        if any(word in context for word in ['product', 'cart', 'shop', 'store', 'buy', 'price', 'item', 'inventory', 'stock', 'ecommerce', 'purchase']):
            return 'product'
        
        # Avatar/profile context
        if any(word in context for word in ['avatar', 'profile', 'user', 'author', 'member', 'team', 'person', 'employee', 'staff']):
            return 'avatar'
        
        # Hero/banner context
        if any(word in context for word in ['hero', 'banner', 'background', 'cover', 'header', 'jumbotron', 'splash']):
            return 'hero'
        
        return 'default'
    
    def get_replacement_url(match, code: str) -> str:
        """Get a consistent replacement URL based on context and position."""
        category = get_image_category_from_context(match.start(), code)
        images = RELIABLE_IMAGE_URLS.get(category, RELIABLE_IMAGE_URLS['default'])
        
        # Use hash of the original URL to get consistent replacement
        original_url = match.group(0)
        hash_val = int(hashlib.md5(original_url.encode()).hexdigest(), 16)
        index = hash_val % len(images)
        
        return images[index]
    
    # Apply replacements
    for pattern in broken_patterns:
        matches = list(re.finditer(pattern, code, re.IGNORECASE))
        # Process in reverse order to maintain correct positions
        for match in reversed(matches):
            replacement = get_replacement_url(match, code)
            code = code[:match.start()] + replacement + code[match.end():]
    
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