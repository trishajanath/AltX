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
import sys
import shutil
from functools import lru_cache

# Path to esbuild binary - handle Windows (.cmd) vs Unix
def get_esbuild_path():
    """Get the correct esbuild path for the current OS."""
    base_dir = os.path.dirname(__file__)
    
    if sys.platform == 'win32':
        # On Windows, use the .cmd wrapper or npx
        cmd_path = os.path.join(base_dir, 'node_modules', '.bin', 'esbuild.cmd')
        if os.path.exists(cmd_path):
            return cmd_path
        # Fallback: try npx
        npx_path = shutil.which('npx')
        if npx_path:
            return None  # Signal to use npx
    else:
        # Unix-like systems
        bin_path = os.path.join(base_dir, 'node_modules', '.bin', 'esbuild')
        if os.path.exists(bin_path):
            return bin_path
    
    # Last resort: check if esbuild is in PATH
    return shutil.which('esbuild')

ESBUILD_PATH = get_esbuild_path()

# Cache for compiled code
_compile_cache = {}

# Reserved JavaScript built-in names that user code shouldn't shadow
RESERVED_BUILTINS = ['Map', 'Set', 'Array', 'Object', 'Promise', 'JSON', 'Date', 'Error', 'Number', 'String', 'Boolean', 'Symbol', 'Function']

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
    
    # CRITICAL: Rename user components that shadow built-in names
    # e.g., "const Map = " -> "const MapComponent = "
    for builtin in RESERVED_BUILTINS:
        # Rename component declarations: const Map = ..., function Map(...), class Map ...
        clean_code = re.sub(
            rf'\b(const|let|var)\s+{builtin}\s*=',
            rf'\1 {builtin}Component =',
            clean_code
        )
        clean_code = re.sub(
            rf'\bfunction\s+{builtin}\s*\(',
            rf'function {builtin}Component(',
            clean_code
        )
        clean_code = re.sub(
            rf'\bclass\s+{builtin}\s+',
            rf'class {builtin}Component ',
            clean_code
        )
        # Also rename JSX usage: <Map ... -> <MapComponent ...
        clean_code = re.sub(
            rf'<{builtin}(\s|>|/)',
            rf'<{builtin}Component\1',
            clean_code
        )
        clean_code = re.sub(
            rf'</{builtin}>',
            rf'</{builtin}Component>',
            clean_code
        )
    
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
        # Build the command - handle npx fallback
        if ESBUILD_PATH:
            cmd = [
                ESBUILD_PATH,
                '--format=esm',            # ES modules format
                '--jsx=transform',         # Transform JSX syntax
                '--jsx-factory=React.createElement',
                '--jsx-fragment=React.Fragment',
                '--target=es2020',         # Modern browser target
                '--loader=jsx',            # Treat input as JSX
            ]
        else:
            # Use npx as fallback
            cmd = [
                'npx', 'esbuild',
                '--format=esm',
                '--jsx=transform',
                '--jsx-factory=React.createElement',
                '--jsx-fragment=React.Fragment',
                '--target=es2020',
                '--loader=jsx',
            ]
        
        # Use stdin to pass code to esbuild (avoids file extension issues)
        result = subprocess.run(
            cmd,
            input=clean_code,
            capture_output=True,
            text=True,
            encoding='utf-8',  # Explicit UTF-8 to handle emojis/Unicode
            timeout=10,  # 10 second timeout
            shell=(sys.platform == 'win32')  # Use shell on Windows for .cmd files
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or 'Unknown esbuild error'
            print(f"❌ esbuild transform error: {error_msg}")
            # Return a SAFE fallback that doesn't contain JSX - just show an error message
            safe_error = error_msg.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '')
            return f'''// JSX Transform Error - esbuild failed
console.error('JSX compilation failed:', '{safe_error[:200]}');
const App = function() {{
    return React.createElement('div', {{
        style: {{
            padding: '20px',
            backgroundColor: '#1e1e1e',
            color: '#f87171',
            fontFamily: 'monospace',
            minHeight: '100vh'
        }}
    }},
        React.createElement('h2', null, '⚠️ JSX Compilation Error'),
        React.createElement('p', null, 'The code could not be transformed. Please check the syntax.'),
        React.createElement('pre', {{
            style: {{ 
                background: '#2d2d2d', 
                padding: '10px', 
                borderRadius: '4px',
                overflow: 'auto',
                maxHeight: '200px'
            }}
        }}, '{safe_error[:500]}')
    );
}};
window.App = App;
'''
        
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
        # Return a safe fallback that doesn't contain JSX
        return _create_error_fallback("esbuild not found. Please install it with: npm install esbuild")
    except subprocess.TimeoutExpired:
        print("❌ esbuild timeout - code too complex?")
        return _create_error_fallback("Code compilation timed out. The code may be too complex.")
    except Exception as e:
        print(f"❌ JSX precompile error: {e}")
        return _create_error_fallback(f"JSX precompile error: {str(e)}")


def _create_error_fallback(error_msg: str) -> str:
    """Create a safe JavaScript fallback that displays an error without using JSX."""
    safe_error = error_msg.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '').replace('<', '&lt;').replace('>', '&gt;')
    return f'''// JSX Transform Error - Fallback Mode
console.error('JSX compilation failed:', '{safe_error[:300]}');
const App = function() {{
    return React.createElement('div', {{
        style: {{
            padding: '20px',
            backgroundColor: '#1e1e1e',
            color: '#f87171',
            fontFamily: 'monospace',
            minHeight: '100vh'
        }}
    }},
        React.createElement('h2', null, '⚠️ Build Error'),
        React.createElement('p', null, '{safe_error[:200]}'),
        React.createElement('p', {{style: {{color: '#888', marginTop: '20px'}}}}, 
            'Please check the server logs for more details.')
    );
}};
window.App = App;
'''


def clear_compile_cache():
    """Clear the compilation cache."""
    global _compile_cache
    _compile_cache = {}


# Test if esbuild is available
def check_esbuild():
    """Check if esbuild is installed and working."""
    try:
        if ESBUILD_PATH:
            cmd = [ESBUILD_PATH, '--version']
        else:
            cmd = ['npx', 'esbuild', '--version']
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',  # Explicit UTF-8 to handle emojis/Unicode
            timeout=10,
            shell=(sys.platform == 'win32')
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
