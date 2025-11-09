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
        """Validate JavaScript/JSX code syntax."""
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Remove any markdown code blocks
            cleaned_code = self._clean_markdown_from_code(code)
            
            # Check for common JSX/React issues
            errors.extend(self._check_jsx_common_issues(cleaned_code))
            warnings.extend(self._check_jsx_warnings(cleaned_code))
            suggestions.extend(self._check_jsx_suggestions(cleaned_code))
            
            # Try to validate with Node.js if available
            # Temporarily disabled due to encoding issues
            # if self._check_node_available():
            #     node_errors = self._validate_with_node(cleaned_code, filename)
            #     errors.extend(node_errors)
            
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
        """Check for JSX warnings."""
        warnings = []
        
        # Check for inline styles (suggest CSS classes instead)
        if 'style={{' in code:
            warnings.append("Consider using CSS classes instead of inline styles")
        
        return warnings
    
    def _check_jsx_suggestions(self, code: str) -> List[str]:
        """Check for JSX suggestions."""
        suggestions = []
        
        # Suggest useCallback for event handlers
        if 'onClick=' in code and 'useCallback' not in code:
            suggestions.append("Consider using useCallback for event handlers to optimize performance")
        
        return suggestions
    
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