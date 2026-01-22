"""
JSX Precompiler using esbuild
Transforms JSX to plain JavaScript on the server before sending to browser.
No more runtime transforms = no Babel/Sucrase errors.
"""

import subprocess
import tempfile
import os
import re
import hashlib
from functools import lru_cache

# Path to esbuild binary
ESBUILD_PATH = os.path.join(os.path.dirname(__file__), 'node_modules', '.bin', 'esbuild')

# Cache for compiled code
_compile_cache = {}

def precompile_jsx(jsx_code: str) -> str:
    """
    Precompile JSX to plain JavaScript using esbuild.
    This runs on the server, so the browser receives pure JS.
    
    Args:
        jsx_code: The JSX/React code to transform
        
    Returns:
        Plain JavaScript code ready for browser execution
    """
    
    # Check cache first
    code_hash = hashlib.md5(jsx_code.encode()).hexdigest()
    if code_hash in _compile_cache:
        return _compile_cache[code_hash]
    
    # Preprocess: Remove/comment out import/export statements
    # (sandbox provides everything globally)
    clean_code = jsx_code
    
    # Remove import statements completely (they're handled by global includes)
    # Handle: import X from 'y', import { X } from 'y', import 'y'
    clean_code = re.sub(
        r'^\s*import\s+(?:[\w{}\s,*]+\s+from\s+)?[\'"][^\'"]+[\'"]\s*;?\s*$',
        '',
        clean_code,
        flags=re.MULTILINE
    )
    
    # Remove export statements (keep the declaration)
    clean_code = re.sub(r'^(\s*)export\s+default\s+', r'\1', clean_code, flags=re.MULTILINE)
    clean_code = re.sub(r'^(\s*)export\s+\{[^}]*\}\s*;?\s*$', '', clean_code, flags=re.MULTILINE)
    clean_code = re.sub(r'^(\s*)export\s+(const|let|var|function|class)', r'\1\2', clean_code, flags=re.MULTILINE)
    
    try:
        # Use stdin to pass code to esbuild (avoids file extension issues)
        result = subprocess.run(
            [
                ESBUILD_PATH,
                '--format=esm',            # ES modules format
                '--jsx=transform',         # Transform JSX syntax
                '--jsx-factory=React.createElement',
                '--jsx-fragment=React.Fragment',
                '--target=es2020',         # Modern browser target
                '--loader=jsx',            # Treat input as JSX
            ],
            input=clean_code,
            capture_output=True,
            text=True,
            timeout=10  # 10 second timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or 'Unknown esbuild error'
            print(f"❌ esbuild transform error: {error_msg}")
            # Return original code with error comment
            return f"// JSX Transform Error: {error_msg}\n// Falling back to original code\n{clean_code}"
        
        compiled = result.stdout
        
        # Cache the result
        _compile_cache[code_hash] = compiled
        
        # Limit cache size
        if len(_compile_cache) > 100:
            # Remove oldest entries
            keys = list(_compile_cache.keys())[:50]
            for k in keys:
                del _compile_cache[k]
        
        return compiled
            
    except FileNotFoundError:
        print("❌ esbuild not found. Run: cd backend && npm install esbuild")
        # Fallback: return code as-is (will likely fail in browser but better than nothing)
        return clean_code
    except subprocess.TimeoutExpired:
        print("❌ esbuild timeout - code too complex?")
        return clean_code
    except Exception as e:
        print(f"❌ JSX precompile error: {e}")
        return clean_code


def clear_compile_cache():
    """Clear the compilation cache."""
    global _compile_cache
    _compile_cache = {}


# Test if esbuild is available
def check_esbuild():
    """Check if esbuild is installed and working."""
    try:
        result = subprocess.run(
            [ESBUILD_PATH, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ esbuild available: v{result.stdout.strip()}")
            return True
    except Exception as e:
        print(f"❌ esbuild not available: {e}")
    return False


if __name__ == "__main__":
    # Test the precompiler
    check_esbuild()
    
    test_jsx = """
    import React from 'react';
    
    const App = () => {
        const [count, setCount] = React.useState(0);
        return (
            <div className="app">
                <h1>Hello World</h1>
                <button onClick={() => setCount(c => c + 1)}>
                    Count: {count}
                </button>
            </div>
        );
    };
    
    export default App;
    """
    
    print("Input JSX:")
    print(test_jsx)
    print("\n" + "="*50 + "\n")
    print("Output JS:")
    print(precompile_jsx(test_jsx))
