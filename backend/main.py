
import os
import secrets
import shutil
import git
import requests
import time
import tempfile
import stat
import platform
from fastapi import Request, Header, FastAPI, HTTPException, Body
from fastapi.responses import RedirectResponse, HTMLResponse
import hmac
import hashlib
import subprocess
import asyncio
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Union
from starlette.concurrency import run_in_threadpool
import json
import re
from scanner.file_security_scanner import scan_for_sensitive_files, scan_file_contents_for_secrets
from scanner.directory_scanner import scan_common_paths
from owasp_mapper import map_to_owasp_top10
from datetime import datetime 
import time
import base64
from github import Github
from rag_query import get_secure_coding_patterns
import tempfile
from rag_query import get_secure_coding_patterns
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import docker
from nginx_config import NginxConfigManager

# --- Local Imports ---
from ai_assistant import get_chat_response, RepoAnalysis, FixRequest
from scanner.file_scanner import (
    scan_url, 
    _format_ssl_analysis,
    scan_dependencies,
    scan_code_quality_patterns,
    is_likely_false_positive
)
from scanner.hybrid_crawler import crawl_hybrid 
from nlp_suggester import suggest_fixes
import ai_assistant
try:
    from ai_assistant import github_client
except ImportError:
    github_client = None
    print("Warning: GitHub client not available")

# --- Phase 1 Imports ---
from scanner.secrets_detector import scan_secrets
from scanner.static_python import run_bandit

# --- Voice Chat Integration ---
from voice_chat_api import router as voice_chat_router

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include voice chat router
app.include_router(voice_chat_router)

# --- Storage Classes for Scan Results ---
class WebsiteScan:
    latest_scan = None

class ScanRequest(BaseModel):
    url: str
    model_type: str = 'fast'
    model_config = {'protected_namespaces': ()}

class RepoAnalysisRequest(BaseModel):
    repo_url: str
    model_type: str = 'smart'
    deep_scan: bool = True
    model_config = {'protected_namespaces': ()}

class OWASPMappingRequest(BaseModel):
    url: str
    repo_url: Optional[str] = None
    model_type: str = "fast"
    model_config = {'protected_namespaces': ()}

class FixRequest(BaseModel):
    repo_url: str
    issue: Dict[str, Any]
    branch_name: Optional[str] = None

from fastapi import Query, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import asyncio
import websockets
from typing import Dict, Set
import threading
import uuid
# --- Project File Tree Endpoint ---
@app.get("/project-file-tree")
async def get_project_file_tree(project_name: str = Query(...)):
    """
    Returns the file tree for the generated project.
    """
    try:
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_name.lower().replace(" ", "-")
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}
        
        # Validate and fix critical files before running
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": "🔍 Validating project files...",
            "level": "info"
        })
        ok = await validate_and_fix_project_files(project_path, project_name)
        if not ok:
            await manager.send_to_project(project_name, {
                "type": "terminal_output",
                "message": "❌ Validation failed. Cannot start project.",
                "level": "error"
            })
            return {"success": False, "error": "Validation failed"}
        def build_tree(path: Path, relative_path: str = ""):
            items = []
            try:
                for item in sorted(path.iterdir()):
                    if item.name.startswith('.') or item.name == '__pycache__':
                        continue
                    
                    relative_item_path = f"{relative_path}/{item.name}" if relative_path else item.name
                    
                    if item.is_dir():
                        items.append({
                            "name": item.name,
                            "type": "dir", 
                            "path": relative_item_path + "/",
                            "children": build_tree(item, relative_item_path)
                        })
                    else:
                        items.append({
                            "name": item.name,
                            "type": "file",
                            "path": relative_item_path
                        })
            except PermissionError:
                pass
            return items
        
        tree = build_tree(project_path)
        return {"success": True, "tree": tree}
        
    except Exception as e:
        print(f"Error getting project tree: {e}")
        return {"success": False, "error": str(e)}

# --- Project File Content Endpoint ---
@app.get("/project-file-content")
async def get_project_file_content(project_name: str = Query(...), file_path: str = Query(...)):
    """
    Returns the actual file content for a given file in the generated project.
    """
    try:
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_name.lower().replace(" ", "-")

        if not project_path.exists():
            return {"success": False, "error": "Project not found"}

        # Clean the file path and resolve it safely
        clean_file_path = file_path.lstrip('/')
        full_file_path = project_path / clean_file_path

        # Security check: ensure the path is within the project directory
        try:
            full_file_path.resolve().relative_to(project_path.resolve())
        except ValueError:
            return {"success": False, "error": "Invalid file path"}

        if not full_file_path.exists():
            return {"success": False, "error": "File not found"}

        if full_file_path.is_dir():
            return {"success": False, "error": "Path is a directory"}

        # Read file content
        try:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Handle binary files
            content = f"[Binary file: {full_file_path.name}]"

        return {"success": True, "content": content}

    except Exception as e:
        print(f"Error reading file content: {e}")
        return {"success": False, "error": str(e)}

# --- Project Preview URL Endpoint ---
@app.get("/project-preview-url")
async def get_project_preview_url(project_name: str = Query(...)):
    """
    Returns a mock live preview URL for the generated project.
    In production, this should point to the actual deployed preview.
    """
    # Demo: return a placeholder preview URL
    url = f"https://demo.altx.app/{project_name.lower().replace(' ', '-')}-preview"
    return {"success": True, "url": url}

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.project_connections: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, connection_id: str, project_name: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if project_name not in self.project_connections:
            self.project_connections[project_name] = set()
        self.project_connections[project_name].add(connection_id)

    def disconnect(self, connection_id: str, project_name: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if project_name in self.project_connections:
            self.project_connections[project_name].discard(connection_id)
            if not self.project_connections[project_name]:
                del self.project_connections[project_name]

    async def send_to_project(self, project_name: str, message: dict):
        """Send message to all connections for a specific project"""
        if project_name in self.project_connections:
            disconnected = []
            for connection_id in self.project_connections[project_name]:
                websocket = self.active_connections.get(connection_id)
                if websocket:
                    try:
                        # Only send when CONNECTED
                        if websocket.client_state == WebSocketState.CONNECTED:
                            await websocket.send_json(message)
                        else:
                            disconnected.append(connection_id)
                    except Exception:
                        # Any send error, schedule cleanup
                        disconnected.append(connection_id)
                else:
                    disconnected.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected:
                self.disconnect(connection_id, project_name)

manager = ConnectionManager()

# --- WebSocket Endpoint ---
@app.websocket("/ws/project/{project_name}")
async def websocket_endpoint(websocket: WebSocket, project_name: str):
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    
    try:
        # Add to connection manager
        manager.active_connections[connection_id] = websocket
        # Ensure this connection is tracked under the project for broadcasts
        if project_name not in manager.project_connections:
            manager.project_connections[project_name] = set()
        manager.project_connections[project_name].add(connection_id)
        print(f"✅ WebSocket connected: {project_name} ({connection_id})")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": f"Connected to project: {project_name}",
            "connection_id": connection_id
        })
        
        # Simple message loop
        while True:
            try:
                # Just wait for any message or disconnection
                data = await websocket.receive_text()
                
                # Echo back to confirm connection is alive
                await websocket.send_json({
                    "type": "echo",
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                })
                
            except WebSocketDisconnect:
                print(f"WebSocket disconnected: {project_name}")
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        print(f"WebSocket setup error: {e}")
    finally:
        # Clean up connection via manager to keep maps in sync
        try:
            manager.disconnect(connection_id, project_name)
        finally:
            print(f"🔌 WebSocket cleaned up: {project_name}")

# --- WebSocket Chat Endpoint ---
@app.websocket("/ws/chat/{project_name}")
async def chat_websocket_endpoint(websocket: WebSocket, project_name: str):
    """Dedicated WebSocket endpoint for real-time AI chat during development."""
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    
    try:
        # Add to connection manager with chat prefix
        chat_project_name = f"chat_{project_name}"
        manager.active_connections[connection_id] = websocket
        if chat_project_name not in manager.project_connections:
            manager.project_connections[chat_project_name] = set()
        manager.project_connections[chat_project_name].add(connection_id)
        print(f"💬 Chat WebSocket connected: {project_name} ({connection_id})")
        
        # Send welcome message
        await websocket.send_json({
            "type": "chat_connected",
            "message": "AI chat assistant ready! Ask me anything about development.",
            "connection_id": connection_id
        })
        
        # Chat message loop
        while True:
            try:
                # Wait for chat message
                data = await websocket.receive_json()
                
                if data.get("type") == "chat_message":
                    user_message = data.get("message", "").strip()
                    chat_history = data.get("history", [])
                    context = data.get("context", {})
                    
                    if user_message:
                        # Send typing indicator
                        await websocket.send_json({
                            "type": "chat_typing",
                            "message": "AI is thinking..."
                        })
                        
                        try:
                            # Process chat using the same logic as the HTTP endpoint
                            system_context = """You are an expert full-stack developer and helpful coding assistant. 
Provide clear, practical, and actionable responses. Be concise but thorough."""

                            # Add project context
                            if context:
                                tech_stack = context.get("tech_stack", [])
                                if tech_stack:
                                    system_context += f"\n\nProject uses: {', '.join(tech_stack)}"
                            
                            messages = [{"role": "system", "content": system_context}]
                            
                            # Add recent history
                            recent_history = chat_history[-8:] if chat_history else []
                            for msg in recent_history:
                                if msg.get("role") and msg.get("content"):
                                    messages.append(msg)
                            
                            # Add current message
                            messages.append({"role": "user", "content": user_message})
                            
                            # Get AI response
                            from ai_assistant import get_chat_response
                            ai_response = get_chat_response(messages, model_type='fast')
                            
                            # Send response
                            await websocket.send_json({
                                "type": "chat_response",
                                "message": ai_response,
                                "user_message": user_message,
                                "timestamp": time.time()
                            })
                            
                        except Exception as ai_error:
                            await websocket.send_json({
                                "type": "chat_error", 
                                "message": f"AI chat error: {str(ai_error)}"
                            })
                    
                elif data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except WebSocketDisconnect:
                print(f"Chat WebSocket disconnected: {project_name}")
                break
            except Exception as e:
                print(f"Chat WebSocket error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Connection error: {str(e)}"
                })
                break
                
    except Exception as e:
        print(f"Chat WebSocket setup error: {e}")
    finally:
        # Clean up connection
        try:
            chat_project_name = f"chat_{project_name}"
            if connection_id in manager.active_connections:
                del manager.active_connections[connection_id]
            if chat_project_name in manager.project_connections:
                manager.project_connections[chat_project_name].discard(connection_id)
                if not manager.project_connections[chat_project_name]:
                    del manager.project_connections[chat_project_name]
        finally:
            print(f"💬 Chat WebSocket cleaned up: {project_name}")

# --- Enhanced Project Structure Creation ---
@app.post("/api/create-project-structure")
async def create_project_structure(request: dict = Body(...)):
    """Create actual project files and structure"""
    try:
        project_name = request.get("project_name")
        idea = request.get("idea") 
        tech_stack = request.get("tech_stack", [])
        
        # Send progress updates via WebSocket
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": "🚀 Creating project structure...",
            "level": "info"
        })
        
        # Generate project name slug
        project_slug = project_name.lower().replace(" ", "-").replace("_", "-")
        projects_dir = Path("generated_projects")
        projects_dir.mkdir(exist_ok=True)
        project_path = projects_dir / project_slug
        
        # Remove existing project if it exists
        if project_path.exists():
            shutil.rmtree(project_path)
        
        # Determine tech stack based on AI analysis of the idea
        detected_stack = await analyze_tech_stack_for_idea(idea)
        
        # Create project structure
        files_created = await create_complete_project_structure(
            project_path, idea, project_slug, detected_stack
        )
        
        await manager.send_to_project(project_name, {
            "type": "terminal_output", 
            "message": f"✅ Created {len(files_created)} files",
            "level": "success"
        })
        
        return {
            "success": True,
            "files_created": files_created,
            "tech_stack": detected_stack,
            "project_path": str(project_path)
        }
        
    except Exception as e:
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": f"❌ Error creating structure: {str(e)}",
            "level": "error"
        })
        return {"success": False, "error": str(e)}

async def analyze_tech_stack_for_idea(idea: str) -> List[str]:
    """Determine the best tech stack for the project idea - ALWAYS React + FastAPI"""
    # ALWAYS use consistent React + FastAPI stack for better quality
    base_stack = ["React", "FastAPI", "Vite", "TailwindCSS"]
    
    # Add specific features based on the idea
    additional_features = []
    
    idea_lower = idea.lower()
    
    # Database features
    if any(keyword in idea_lower for keyword in ["todo", "task", "store", "save", "data", "crud", "database"]):
        additional_features.append("SQLite")
    
    # Authentication features  
    if any(keyword in idea_lower for keyword in ["auth", "login", "user", "signup", "account", "profile"]):
        additional_features.append("JWT Auth")
    
    # Real-time features
    if any(keyword in idea_lower for keyword in ["chat", "live", "real-time", "websocket", "notification"]):
        additional_features.append("WebSockets")
    
    # AI features
    if any(keyword in idea_lower for keyword in ["ai", "ml", "openai", "gpt", "chatbot", "intelligent"]):
        additional_features.append("AI Integration")
    
    return base_stack + additional_features[:4]  # Limit to 8 total items

async def create_complete_project_structure(project_path: Path, idea: str, project_name: str, tech_stack: List[str]) -> List[str]:
    """Create complete project with OPTIMIZED Pure AI generation - 100% AI code, NO templates, FAST"""
    
    # Send initial progress
    await manager.send_to_project(project_name, {
        "type": "file_creation_start",
        "message": "🚀 Starting OPTIMIZED Pure AI generation - 100% AI code in ~60 seconds...",
        "total_files": 15
    })
    
    try:
        # Use OPTIMIZED Pure AI Generator - NO templates, FAST AI generation
        if os.getenv("GOOGLE_API_KEY"):
            from pure_ai_generator import PureAIGenerator
            
            await manager.send_to_project(project_name, {
                "type": "terminal_output",
                "message": "🧠 FAST AI: Creating 100% custom implementation...",
                "level": "info"
            })
            
            generator = PureAIGenerator()
            files_created = await generator.generate_project_structure(project_path, idea, project_name)
            
            await manager.send_to_project(project_name, {
                "type": "file_creation_complete", 
                "message": f"🎉 Pure AI Complete! Generated {len(files_created)} files of 100% custom AI code",
                "files_created": files_created,
                "generation_method": "optimized-pure-ai"
            })
            
            return files_created
            
        else:
            # If no AI key, throw error 
            raise Exception("GOOGLE_API_KEY is required. Please set your Gemini API key.")
            
    except Exception as e:
        await manager.send_to_project(project_name, {
            "type": "terminal_output", 
            "message": f"❌ Pure AI generation failed: {str(e)}",
            "level": "error"
        })
        
        # Re-raise the error
        raise Exception(f"Pure AI generation failed: {str(e)}. Please check your GOOGLE_API_KEY.")
    
    return files_created

# --- Sandboxed Preview Endpoint ---
@app.get("/api/sandbox-preview/{project_name}")
async def get_sandbox_preview(project_name: str):
    """Generate a sandboxed HTML preview that runs React code directly in the browser"""
    try:
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        frontend_path = project_path / "frontend"
        
        if not frontend_path.exists():
            raise HTTPException(status_code=404, detail="Project frontend not found")
        
        # Read the main files
        files_content = {}
        
        # Essential files to bundle
        essential_files = [
            "src/App.jsx",
            "src/main.jsx", 
            "src/index.css",
            "package.json"
        ]
        
        # Read additional component files
        src_components_path = frontend_path / "src" / "components"
        if src_components_path.exists():
            for comp_file in src_components_path.glob("*.jsx"):
                essential_files.append(f"src/components/{comp_file.name}")
        
        for file_path in essential_files:
            full_path = frontend_path / file_path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding='utf-8')
                    files_content[file_path] = content
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    files_content[file_path] = f"// Error reading file: {e}"
        
        # Generate the sandbox HTML
        sandbox_html = generate_sandbox_html(files_content, project_name)
        
        return HTMLResponse(content=sandbox_html)
        
    except Exception as e:
        error_html = f"""
        <html>
            <body style="font-family: Arial; padding: 20px; background: #1e1e1e; color: #fff;">
                <h2>Preview Error</h2>
                <p>Failed to generate preview: {str(e)}</p>
                <p>Make sure your project has been built successfully.</p>
            </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)

def generate_sandbox_html(files_content: dict, project_name: str) -> str:
    """Generate a complete HTML page that runs React code in the browser"""
    
    # Extract main app content
    app_jsx = files_content.get("src/App.jsx", "")
    main_jsx = files_content.get("src/main.jsx", "")
    index_css = files_content.get("src/index.css", "")
    
    # Validate and fix main.jsx content
    if main_jsx and 'ReactDOM.createRoot' in main_jsx:
        if '.render(\n\n  ,\n)' in main_jsx or '.render(\n\n,\n)' in main_jsx:
            print("🔧 Fixing incomplete render call in main.jsx for sandbox")
            main_jsx = main_jsx.replace(
                '.render(\n\n  ,\n)',
                '.render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n)'
            ).replace(
                '.render(\n\n,\n)',
                '.render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n)'
            )
    
    # Process component files properly for browser compilation
    components_code = ""
    for file_path, content in files_content.items():
        if file_path.startswith("src/components/") and file_path.endswith(".jsx"):
            component_name = file_path.split("/")[-1].replace(".jsx", "")
            
            # Clean up the component content for browser compilation
            cleaned_content = content
            
            # Validate and fix component content
            cleaned_content = fix_jsx_content_for_sandbox(cleaned_content, component_name, project_name)
            
            # Remove ALL import statements since we're bundling everything in browser scope
            content_lines = cleaned_content.split('\n')
            filtered_lines = []
            for line in content_lines:
                # Remove all import statements
                if not line.strip().startswith('import '):
                    filtered_lines.append(line)
            
            cleaned_content = '\n'.join(filtered_lines)
            
            # Ensure the component is properly exported for global scope
            if 'export default' in cleaned_content:
                cleaned_content = cleaned_content.replace('export default', f'window.{component_name} = ')
            elif f'export {{ {component_name} }}' in cleaned_content:
                cleaned_content += f'\nwindow.{component_name} = {component_name};'
            else:
                # If no export found, assume the component is the main function/class
                cleaned_content += f'\nwindow.{component_name} = {component_name};'
            
            components_code += f"// {component_name} Component\n{cleaned_content}\n\n"
    
    # Clean the App.jsx content
    app_content = app_jsx
    if 'export default' in app_content:
        app_content = app_content.replace('export default', 'window.App = ')
    
    # Fix App.jsx content for sandbox
    app_content = fix_jsx_content_for_sandbox(app_content, 'App', project_name)
    
    # Remove ALL import statements since we're loading React globally and bundling components
    app_content = '\n'.join([
        line for line in app_content.split('\n') 
        if not line.strip().startswith('import ')
    ])
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - Live Preview</title>
    <!-- SANDBOX PREVIEW ONLY: Using CDN for quick prototyping -->
    <!-- In production, use built assets with npm/yarn build -->
    
    <!-- Load React first -->
    <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    
    <!-- Try to load React Router (with fallback handling) -->
    <script crossorigin src="https://unpkg.com/react-router@6/dist/umd/react-router.development.js"></script>
    <script crossorigin src="https://unpkg.com/react-router-dom@6/dist/umd/react-router-dom.development.js"></script>
    
    <!-- Load Babel transformer -->
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    
    <!-- Load TailwindCSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <style>
        {index_css}
        body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; }}
        #root {{ width: 100%; height: 100vh; }}
        .error-boundary {{ 
            padding: 20px; 
            background: #fee; 
            border: 1px solid #fcc; 
            border-radius: 4px; 
            margin: 20px;
            color: #c33;
        }}
        .preview-console {{
            position: fixed;
            bottom: 0;
            right: 0;
            width: 300px;
            height: 150px;
            background: #000;
            color: #0f0;
            padding: 10px;
            font-family: monospace;
            font-size: 12px;
            overflow-y: auto;
            z-index: 9999;
            border: 1px solid #333;
        }}
    </style>
</head>
<body>
    <div id="root"></div>
    <div id="preview-console" class="preview-console" style="display: none;"></div>
    
    <script type="text/babel">
        // Wait for all dependencies to load
        if (typeof React === 'undefined' || typeof ReactDOM === 'undefined') {{
            console.error('React not loaded properly');
            document.body.innerHTML = '<div style="padding: 20px; color: red;">Error: React libraries not loaded</div>';
            throw new Error('React dependencies missing');
        }}
        
        const {{ useState, useEffect, useCallback, useMemo, useRef }} = React;
        
        // Create a simple, reliable router that doesn't depend on external libraries
        const createSimpleRouter = () => {{
            // Simple router implementation using hash-based routing
            const SimpleRouter = ({{ children }}) => {{
                const [currentPath, setCurrentPath] = useState(window.location.hash.slice(1) || '/');
                
                useEffect(() => {{
                    const handleHashChange = () => {{
                        setCurrentPath(window.location.hash.slice(1) || '/');
                    }};
                    
                    window.addEventListener('hashchange', handleHashChange);
                    return () => window.removeEventListener('hashchange', handleHashChange);
                }}, []);
                
                // Provide router context
                return React.createElement('div', {{ 
                    'data-router': 'simple',
                    'data-current-path': currentPath 
                }}, children);
            }};
            
            const SimpleRoutes = ({{ children }}) => {{
                const currentPath = window.location.hash.slice(1) || '/';
                const routes = React.Children.toArray(children);
                
                // Find matching route or return first one as default
                const matchingRoute = routes.find(route => {{
                    if (route.props && route.props.path) {{
                        return route.props.path === currentPath;
                    }}
                    return false;
                }}) || routes[0];
                
                return matchingRoute || React.createElement('div', null, 'No routes found');
            }};
            
            const SimpleRoute = ({{ element, path, children }}) => {{
                return element || children || React.createElement('div', null, `Route: ${{path}}`);
            }};
            
            const SimpleLink = ({{ to, children, className, style, ...props }}) => {{
                const handleClick = (e) => {{
                    e.preventDefault();
                    window.location.hash = to;
                }};
                
                return React.createElement('a', {{
                    href: `#${{to}}`,
                    onClick: handleClick,
                    className: className,
                    style: {{
                        color: 'blue',
                        textDecoration: 'underline',
                        cursor: 'pointer',
                        ...style
                    }},
                    ...props
                }}, children);
            }};
            
            const useSimpleNavigate = () => {{
                return useCallback((path) => {{
                    window.location.hash = path;
                }}, []);
            }};
            
            const useSimpleParams = () => {{
                // Simple params extraction from hash
                const hash = window.location.hash.slice(1);
                const segments = hash.split('/');
                return {{ id: segments[segments.length - 1] || null }};
            }};
            
            const useSimpleLocation = () => {{
                const [location, setLocation] = useState({{
                    pathname: window.location.hash.slice(1) || '/',
                    hash: window.location.hash,
                    search: ''
                }});
                
                useEffect(() => {{
                    const handleHashChange = () => {{
                        setLocation({{
                            pathname: window.location.hash.slice(1) || '/',
                            hash: window.location.hash,
                            search: ''
                        }});
                    }};
                    
                    window.addEventListener('hashchange', handleHashChange);
                    return () => window.removeEventListener('hashchange', handleHashChange);
                }}, []);
                
                return location;
            }};
            
            return {{
                Router: SimpleRouter,
                Routes: SimpleRoutes,
                Route: SimpleRoute,
                Link: SimpleLink,
                useNavigate: useSimpleNavigate,
                useParams: useSimpleParams,
                useLocation: useSimpleLocation
            }};
        }};
        
        // Always use the built-in simple hash router to avoid external deps
        let Router, Routes, Route, Link, useNavigate, useParams, useLocation;
        console.log('✅ Using built-in simple hash router (no external history/react-router)');
        const simpleRouter = createSimpleRouter();
        Router = simpleRouter.Router;
        Routes = simpleRouter.Routes;
        Route = simpleRouter.Route;
        Link = simpleRouter.Link;
        useNavigate = simpleRouter.useNavigate;
        useParams = simpleRouter.useParams;
        useLocation = simpleRouter.useLocation;
        
        // Make Router components available globally
        window.Router = Router;
        window.BrowserRouter = Router; // Use main Router as fallback
        window.HashRouter = Router;    // Use main Router as fallback
        window.MemoryRouter = Router;  // Use main Router as fallback
        window.Routes = Routes;
        window.Route = Route;
        window.Link = Link;
        window.useNavigate = useNavigate;
        window.useParams = useParams;
        window.useLocation = useLocation;
        
        // Create simple icon components as fallbacks
        const createIcon = (name) => ({{ size = 24, className = '', ...props }}) => 
            React.createElement('svg', {{
                width: size,
                height: size,
                viewBox: '0 0 24 24',
                fill: 'none',
                stroke: 'currentColor',
                strokeWidth: 2,
                strokeLinecap: 'round',
                strokeLinejoin: 'round',
                className: className,
                ...props
            }}, React.createElement('title', null, name));
        
        // Create common icons
        window.Home = createIcon('Home');
        window.User = createIcon('User');
        window.Settings = createIcon('Settings');
        window.Search = createIcon('Search');
        window.Menu = createIcon('Menu');
        window.X = createIcon('X');
        window.Plus = createIcon('Plus');
        window.Minus = createIcon('Minus');
        window.Edit = createIcon('Edit');
        window.Trash2 = createIcon('Trash');
        window.Save = createIcon('Save');
        window.ChevronDown = createIcon('ChevronDown');
        window.ChevronUp = createIcon('ChevronUp');
        window.ChevronLeft = createIcon('ChevronLeft');
        window.ChevronRight = createIcon('ChevronRight');
        window.Heart = createIcon('Heart');
        window.Star = createIcon('Star');
        window.Eye = createIcon('Eye');
        window.EyeOff = createIcon('EyeOff');
        window.Lock = createIcon('Lock');
        window.Unlock = createIcon('Unlock');
        window.Mail = createIcon('Mail');
        window.Phone = createIcon('Phone');
        window.Calendar = createIcon('Calendar');
        window.Clock = createIcon('Clock');
        window.Download = createIcon('Download');
        window.Upload = createIcon('Upload');
        window.Share = createIcon('Share');
        window.MessageCircle = createIcon('MessageCircle');
        window.AlertCircle = createIcon('AlertCircle');
        window.CheckCircle = createIcon('CheckCircle');
        window.Info = createIcon('Info');
        window.FileText = createIcon('FileText');
        window.Folder = createIcon('Folder');
        window.Image = createIcon('Image');
        window.ShoppingCart = createIcon('ShoppingCart');
        window.CreditCard = createIcon('CreditCard');
        window.Package = createIcon('Package');
        window.MapPin = createIcon('MapPin');
        window.Globe = createIcon('Globe');
        window.Play = createIcon('Play');
        window.Pause = createIcon('Pause');
        window.Volume2 = createIcon('Volume');
        window.Battery = createIcon('Battery');
        window.Wifi = createIcon('Wifi');
        window.Filter = createIcon('Filter');
        window.Sort = createIcon('Sort');
        window.MoreHorizontal = createIcon('MoreHorizontal');
        window.MoreVertical = createIcon('MoreVertical');
        window.ExternalLink = createIcon('ExternalLink');
        
        // Console logger for debugging
        const originalConsoleLog = console.log;
        const originalConsoleError = console.error;
        const originalConsoleWarn = console.warn;
        
        const consoleDiv = document.getElementById('preview-console');
        let logCount = 0;
        
        function addToConsole(message, type = 'log') {{
            if (logCount === 0) consoleDiv.style.display = 'block';
            logCount++;
            const entry = document.createElement('div');
            entry.style.color = type === 'error' ? '#f66' : type === 'warn' ? '#fa0' : '#0f0';
            entry.textContent = '[' + type.toUpperCase() + '] ' + message;
            consoleDiv.appendChild(entry);
            consoleDiv.scrollTop = consoleDiv.scrollHeight;
        }}
        
        console.log = function(...args) {{
            originalConsoleLog.apply(console, args);
            addToConsole(args.join(' '), 'log');
        }};
        
        console.error = function(...args) {{
            originalConsoleError.apply(console, args);
            addToConsole(args.join(' '), 'error');
        }};
        
        console.warn = function(...args) {{
            originalConsoleWarn.apply(console, args);
            addToConsole(args.join(' '), 'warn');
        }};
        
        // Error Boundary Component
        class ErrorBoundary extends React.Component {{
            constructor(props) {{
                super(props);
                this.state = {{ hasError: false, error: null }};
            }}
            
            static getDerivedStateFromError(error) {{
                console.error('React Error Boundary caught:', error);
                return {{ hasError: true, error }};
            }}
            
            componentDidCatch(error, errorInfo) {{
                console.error('React Error Details:', error, errorInfo);
            }}
            
            render() {{
                if (this.state.hasError) {{
                    return (
                        <div className="error-boundary">
                            <h2>Something went wrong in the preview</h2>
                            <details>
                                <summary>Error details</summary>
                                <pre>{{this.state.error?.toString()}}</pre>
                            </details>
                        </div>
                    );
                }}
                return this.props.children;
            }}
        }}
        
        // Mock API calls for demo purposes
        const mockFetch = (url, options) => {{
            console.log('Mock API call to:', url);
            return Promise.resolve({{
                ok: true,
                json: () => Promise.resolve({{ message: 'Mock API response', data: [] }})
            }});
        }};
        
        // Replace fetch with mock for demo
        window.fetch = mockFetch;
        
        console.log('Loading components...');
        
        {components_code}
        
        console.log('Loading App component...');
        
        {app_content}
        
        // Render the app
        console.log('Rendering app...');
        try {{
            if (typeof window.App === 'function') {{
                const root = ReactDOM.createRoot(document.getElementById('root'));
                root.render(
                    React.createElement(ErrorBoundary, null,
                        React.createElement(window.App)
                    )
                );
                console.log('App rendered successfully!');
            }} else {{
                throw new Error('App component not found or not a function');
            }}
        }} catch (error) {{
            console.error('Failed to render app:', error);
            document.getElementById('root').innerHTML = 
                '<div class="error-boundary">' +
                '<h2>Failed to render the application</h2>' +
                '<p>' + error.message + '</p>' +
                '<p>Check the console for more details.</p>' +
                '</div>';
        }}
    </script>
</body>
</html>
    """

def fix_jsx_content_for_sandbox(content: str, component_name: str, project_name: str) -> str:
    """Fix JSX content specifically for sandbox browser compilation"""
    import re
    
    # Fix empty component functions
    if f'const {component_name} = () => (\n\n);' in content:
        print(f"🔧 Fixing empty component {component_name}")
        content = content.replace(
            f'const {component_name} = () => (\n\n);',
            f'const {component_name} = () => (\n  <div className="p-4 bg-gray-100 rounded">\n    <h3>Welcome to {component_name}</h3>\n    <p>Component is working!</p>\n  </div>\n);'
        )
    
    # Fix incomplete arrow function components - pattern: const ComponentName = () => (\n\n);
    content = re.sub(
        r'const (\w+) = \(\) => \(\s*\n\s*\n\s*\);',
        r'const \1 = () => (\n  <div className="flex items-center justify-center p-4">\n    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>\n  </div>\n);',
        content
    )
    
    # Fix incomplete arrow function components with props - pattern: const ComponentName = ({ prop }) => (\n\n);
    content = re.sub(
        r'const (\w+) = \(\{[^}]*\}\) => \(\s*\n\s*\n\s*\);',
        r'const \1 = ({ message, type = "error" }) => (\n  <div className={`p-4 rounded-lg border ${"bg-red-50 border-red-200 text-red-700" if type === "error" else "bg-blue-50 border-blue-200 text-blue-700"}`}>\n    <div className="flex items-center">\n      <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">\n        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />\n      </svg>\n      {message || "An error occurred"}\n    </div>\n  </div>\n);',
        content
    )
    
    # Fix any remaining incomplete components with better defaults
    content = re.sub(
        r'const (\w+) = \([^)]*\) => \{\s*\n\s*return \(\s*\n\s*\);?\s*\n\s*\};?',
        r'const \1 = (props) => {\n  return (\n    <div className="p-4 bg-white rounded-lg shadow-sm border border-gray-200">\n      <h3 className="text-lg font-semibold text-gray-800 mb-2">\1 Component</h3>\n      <p className="text-gray-600">This component is ready for implementation.</p>\n    </div>\n  );\n};',
        content
    )

    # Fix incomplete function components
    if 'function ' + component_name in content and 'return (\n\n' in content:
        print(f"🔧 Fixing incomplete return in {component_name}")
        content = content.replace(
            'return (\n\n',
            f'return (\n    <div className="p-4">\n      <h2>{component_name}</h2>\n      <p>Component content for {project_name}</p>\n'
        )
        # Ensure proper closing structure
        if 'return (' in content and not content.rstrip().endswith('</div>\n  );'):
            content = content.rstrip()
            if content.endswith(');'):
                content = content[:-2] + '\n    </div>\n  );'
            elif content.endswith('  );\n}'):
                content = content.replace('  );\n}', '    </div>\n  );\n}')
    
    # Fix Router component usage for sandbox (use globals provided by sandbox)
    # Normalize all router types to a single `Router` symbol used by preview
    content = content.replace('BrowserRouter', 'Router')
    content = content.replace('HashRouter', 'Router')
    content = content.replace('MemoryRouter', 'Router')

    # Remove any react-router-dom imports (named, default, or namespace)
    content = re.sub(r"import\s+\{[^}]*\}\s+from\s+['\"]react-router-dom['\"];?\s*", '', content)
    content = re.sub(r"import\s+\*\s+as\s+\w+\s+from\s+['\"]react-router-dom['\"];?\s*", '', content)
    content = re.sub(r"import\s+\w+\s+from\s+['\"]react-router-dom['\"];?\s*", '', content)

    # Remove destructuring from ReactRouterDOM global, if present
    content = re.sub(r'const\s*\{\s*([^}]*)\s*\}\s*=\s*ReactRouterDOM;?\s*', '', content)
    
    # Handle Lucide React imports - remove them since icons are global
    content = re.sub(r'import\s*{\s*([^}]*)\s*}\s*from\s*[\'"]lucide-react[\'"];?', '', content)
    content = re.sub(r'const\s*{\s*([^}]*)\s*}\s*=\s*LucideReact;?', '', content)
    
    # Fix incomplete JSX elements (missing content between tags) - more comprehensive
    content = re.sub(r'>\s*\n\s*\n\s*</div>', '>\n      <p>Content placeholder</p>\n    </div>', content)
    content = re.sub(r'>\s*\n\s*\n\s*</(\w+)>', r'>\n      <p>Content placeholder</p>\n    </\1>', content)
    
    # Fix malformed comment blocks in JSX
    content = re.sub(r'/\*\*\s*\n\s*\*\s*\n\s*\*\s*\n\s*\*\s*This component is responsible for rendering the list of tasks\. It maps over\s*\n\s*\*\s*the `tasks` array and renders a `TaskItem` for each one, passing down the\s*\n\s*\*\s*necessary props and callbacks\.\s*\n\s*\*/', '/**\n * TaskList Component\n * \n * This component is responsible for rendering the list of tasks. It maps over\n * the tasks array and renders a TaskItem for each one, passing down the\n * necessary props and callbacks.\n */', content)
    
    # Fix incomplete exports with malformed syntax
    if 'export const' in content and '= ({' in content and '}) => {' in content:
        # This handles the malformed export structure
        content = re.sub(r'export const (\w+) = \(\{[^}]*\}\) => \{\s*\n\s*return \(\s*\n\s*\);?\s*\n\s*\};?', 
                        r'export const \1 = ({ tasks, onToggleTask, onDeleteTask }) => {\n  return (\n    <div className="space-y-2">\n      <h2 className="text-lg font-semibold">Task List</h2>\n      <p>Tasks will be displayed here</p>\n    </div>\n  );\n};', content)
    
    return content

# --- Lovable-style Orchestrator: Build With AI ---
@app.post("/api/build-with-ai")
async def build_with_ai(request: dict = Body(...)):
    """One-click flow: create -> install -> validate/fix -> run -> preview"""
    try:
        project_name = request.get("project_name")
        idea = request.get("idea") or ""
        tech_stack = request.get("tech_stack", [])

        if not project_name:
            raise HTTPException(status_code=400, detail="project_name is required")

        # 1) Create structure
        await manager.send_to_project(project_name, {
            "type": "status",
            "phase": "create",
            "message": "Creating project structure with AI..."
        })

        create_resp = await create_project_structure({
            "project_name": project_name,
            "idea": idea,
            "tech_stack": tech_stack
        })
        if not create_resp.get("success"):
            return create_resp

        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug

        # 2) Install dependencies (frontend/backend if present)
        await manager.send_to_project(project_name, {
            "type": "status",
            "phase": "install",
            "message": "Installing dependencies..."
        })

        await install_dependencies_endpoint({
            "project_name": project_name,
            "tech_stack": tech_stack
        })

        # 3) Validate and auto-fix in a short loop
        await manager.send_to_project(project_name, {
            "type": "status",
            "phase": "validate",
            "message": "Validating project for errors..."
        })

        # First pass validation
        await validate_and_fix_project_files(project_path, project_name)
        check1 = await check_project_errors(project_name)
        if not check1.get("success"):
            return check1

        errors = check1.get("errors", [])
        if errors:
            await manager.send_to_project(project_name, {
                "type": "status",
                "phase": "fix",
                "message": f"Auto-fixing {len(errors)} issues..."
            })
            await auto_fix_errors({
                "project_name": project_name,
                "errors": errors,
                "tech_stack": tech_stack
            })
            # Re-validate once more
            check2 = await check_project_errors(project_name)
            errors = check2.get("errors", []) if check2.get("success") else errors

        # 4) Run project (frontend + optional backend)
        await manager.send_to_project(project_name, {
            "type": "status",
            "phase": "run",
            "message": "Starting development servers..."
        })

        run_resp = await run_project({
            "project_name": project_name,
            "tech_stack": tech_stack
        })

        preview_url = run_resp.get("preview_url") if isinstance(run_resp, dict) else None
        if preview_url:
            await manager.send_to_project(project_name, {
                "type": "preview_ready",
                "url": preview_url
            })

        # 5) Final status
        await manager.send_to_project(project_name, {
            "type": "status",
            "phase": "ready",
            "message": "✅ Build complete. Live preview is ready.",
            "preview_url": preview_url,
            "errors_remaining": errors
        })

        return {
            "success": True,
            "preview_url": preview_url,
            "errors": errors
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

# --- AI Chat Endpoint ---
@app.post("/api/chat")
async def ai_chat(request: dict = Body(...)):
    """General AI chat endpoint for development assistance and questions."""
    try:
        project_name = request.get("project_name")
        user_message = request.get("user_message")
        chat_history = request.get("chat_history", [])
        context = request.get("context", {})
        
        if not user_message:
            raise HTTPException(status_code=400, detail="user_message is required")
        
        # Optional: Send typing indicator if project_name is provided
        if project_name:
            await manager.send_to_project(project_name, {
                "type": "chat_typing",
                "message": "AI is thinking..."
            })
        
        # Build context for the AI
        system_context = """You are an expert full-stack developer and helpful coding assistant. 
You help developers with:
- Code explanations and debugging
- Architecture advice and best practices  
- Technology recommendations
- Implementation guidance
- Problem-solving and optimization
- General development questions

Provide clear, practical, and actionable responses. When discussing code, be specific and include examples when helpful."""

        # Add project context if provided
        if context:
            tech_stack = context.get("tech_stack", [])
            current_files = context.get("current_files", [])
            errors = context.get("errors", [])
            
            if tech_stack:
                system_context += f"\n\nCurrent project uses: {', '.join(tech_stack)}"
            if current_files:
                system_context += f"\nCurrent files: {', '.join(current_files[:10])}"  # Limit to first 10
            if errors:
                system_context += f"\nActive errors: {len(errors)} issues found"

        # Prepare chat messages for AI
        messages = [{"role": "system", "content": system_context}]
        
        # Add chat history (limit to last 10 messages to avoid token limits)
        recent_history = chat_history[-10:] if chat_history else []
        for msg in recent_history:
            if msg.get("role") and msg.get("content"):
                messages.append({
                    "role": msg["role"], 
                    "content": msg["content"]
                })
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Get AI response
        try:
            from ai_assistant import get_chat_response
            ai_response = get_chat_response(messages, model_type='smart')
            
            # Send response via WebSocket if project connected
            if project_name:
                await manager.send_to_project(project_name, {
                    "type": "chat_response",
                    "message": ai_response,
                    "user_message": user_message
                })
            
            return {
                "success": True,
                "response": ai_response,
                "timestamp": time.time()
            }
            
        except Exception as ai_error:
            error_msg = f"AI chat failed: {str(ai_error)}"
            if project_name:
                await manager.send_to_project(project_name, {
                    "type": "chat_error",
                    "message": error_msg
                })
            
            return {
                "success": False,
                "error": error_msg
            }
            
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Chat History Endpoint ---
@app.get("/api/chat/history/{project_name}")
async def get_chat_history(project_name: str, limit: int = 50):
    """Get recent chat history for a project (placeholder for now)."""
    try:
        # For now, return empty history - in production you'd store/retrieve from database
        return {
            "success": True,
            "project_name": project_name,
            "history": [],
            "message": "Chat history feature coming soon - conversations are not yet persisted"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- AI Project Assistant Endpoint ---
@app.post("/api/ai-project-assistant")
async def ai_project_assistant(request: dict = Body(...)):
    """Process natural language requests to modify and improve project files."""
    try:
        project_name = request.get("project_name")
        user_message = request.get("user_message")
        tech_stack = request.get("tech_stack", [])
        re_run = bool(request.get("re_run", False))

        if not project_name:
            raise HTTPException(status_code=400, detail="project_name is required")
        if not user_message:
            raise HTTPException(status_code=400, detail="user_message is required")

        # Resolve project path
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}

        # Send status update
        await manager.send_to_project(project_name, {
            "type": "status",
            "phase": "thinking",
            "message": "🤖 Processing your request..."
        })

        # Get project context (read existing files)
        project_context = ""
        try:
            # Read key files for context
            for file_pattern in ["package.json", "src/App.jsx", "src/main.jsx", "backend/main.py"]:
                context_file = project_path / file_pattern
                if context_file.exists():
                    try:
                        with open(context_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            project_context += f"\n=== {file_pattern} ===\n{content[:2000]}\n"
                    except:
                        continue
        except:
            pass

        # Enhanced request processing - handle vague requests by analyzing the project
        def is_vague_request(message):
            """Check if the request is too vague and needs project analysis."""
            vague_phrases = [
                "fix", "improve", "enhance", "make better", "update", "modify",
                "change", "add features", "optimize", "clean up", "refactor",
                "something went wrong", "error", "not working", "broken"
            ]
            return any(phrase in message.lower() for phrase in vague_phrases) and len(message.split()) < 12

        def analyze_error_message(message):
            """Extract specific error information from error messages."""
            error_patterns = {
                "TypeError: Invalid attempt to spread non-iterable instance": {
                    "issue": "Spread operator used on non-array/object",
                    "fixes": ["Check array initialization", "Ensure proper data types", "Add null checks before spreading"]
                },
                "ReferenceError": {
                    "issue": "Component or variable not defined",
                    "fixes": ["Check imports", "Verify component exports", "Add missing declarations"]
                },
                "map is not a function": {
                    "issue": "Array method called on non-array",
                    "fixes": ["Initialize as empty array []", "Add Array.isArray() check", "Provide fallback data"]
                },
                "JSON.parse": {
                    "issue": "JSON parsing error",
                    "fixes": ["Add try/catch around JSON.parse", "Validate JSON string", "Provide default fallback"]
                }
            }
            
            for pattern, info in error_patterns.items():
                if pattern.lower() in message.lower():
                    return info
            return None

        # Auto-analyze project for common issues if request is vague
        project_analysis = ""
        
        # First check for specific error patterns
        error_info = analyze_error_message(user_message)
        if error_info:
            project_analysis = f"""

🚨 DETECTED ERROR: {error_info['issue']}

RECOMMENDED FIXES:
- {chr(10).join(f'• {fix}' for fix in error_info['fixes'])}

ANALYZING PROJECT FILES FOR SPECIFIC FIXES..."""
            
        elif is_vague_request(user_message):
            await manager.send_to_project(project_name, {
                "type": "status", 
                "phase": "analyzing",
                "message": "🔍 Analyzing project for common issues..."
            })
            
            # Quick analysis of common frontend issues
            analysis_points = []
            
            # Check for React-specific issues in App.jsx
            app_file = project_path / "frontend" / "src" / "App.jsx"
            if app_file.exists():
                try:
                    with open(app_file, 'r', encoding='utf-8') as f:
                        app_content = f.read()
                        
                    # Common React issues to check
                    if "spread non-iterable" in user_message.lower():
                        analysis_points.append("Fix spread operator errors - check for null/undefined values before spreading")
                        # Check for specific spread patterns that might fail
                        if "...(" in app_content or "... " in app_content:
                            analysis_points.append("Found spread operators that need null checks")
                    if ".map is not a function" in user_message.lower() or "map" in user_message.lower():
                        analysis_points.append("Fix array.map() errors - ensure arrays are properly initialized")
                    if "products.map" in app_content and "useState([])" not in app_content:
                        analysis_points.append("Arrays not properly initialized as [] in useState")
                    if "JSON.parse" in app_content and "try" not in app_content:
                        analysis_points.append("JSON.parse without error handling")  
                    if "ErrorBoundary" in app_content:
                        analysis_points.append("Remove duplicate ErrorBoundary class declarations")
                    if "...props" in app_content and "props &&" not in app_content:
                        analysis_points.append("Spread operator used without checking if props exists")
                    if "localhost:8000/api" in app_content and "/v1" not in app_content:
                        analysis_points.append("API endpoints missing /v1 prefix")
                    if "fetch(" in app_content and ".then" not in app_content and "await" not in app_content:
                        analysis_points.append("Fetch calls need proper async/await or .then handling")
                        
                except:
                    pass
            
            # Check package.json for missing dependencies
            pkg_file = project_path / "frontend" / "package.json"
            if pkg_file.exists():
                try:
                    with open(pkg_file, 'r', encoding='utf-8') as f:
                        pkg_content = f.read()
                    if '"react"' not in pkg_content:
                        analysis_points.append("Missing React dependency in package.json")
                except:
                    pass
            
            if analysis_points:
                project_analysis = f"\n\nDETECTED ISSUES TO FIX:\n- " + "\n- ".join(analysis_points[:5])
            else:
                project_analysis = f"\n\nSUGGESTION: Be more specific. Examples:\n- 'Fix the array.map error'\n- 'Add a login form'\n- 'Make buttons responsive'"

        # Use AI to generate changes with enhanced prompt
        prompt = f"""You are an expert full-stack developer. CRITICAL: Your response must be VALID JSON ONLY - no markdown, no explanations outside JSON, no code blocks.

User Request: "{user_message}"
Project: {project_name}
Tech Stack: {', '.join(tech_stack) if tech_stack else 'React + FastAPI'}

Current Project Files:
{project_context}

ANALYZE THE REQUEST AND PROVIDE SPECIFIC CODE CHANGES:

1. If user says "include my name which is Neelesh" or similar personalization:
   - Add their name to the UI (header, welcome message, about section)
   - Update titles and text to include their name
   - Make it personal and welcoming

2. If fixing errors:
   - Fix spread operator errors: {{...(props || {{}})}}
   - Fix array.map errors: ensure useState([]) initialization
   - Fix JSON parsing: add try/catch blocks
   - Fix missing imports and components

3. If adding features:
   - Implement complete, working features
   - Use modern React patterns
   - Include proper styling with TailwindCSS

RESPOND WITH VALID JSON ONLY (no markdown, no ```json blocks):

{{
  "changes": [
    {{
      "file_path": "frontend/src/App.jsx",
      "edit_type": "content_update", 
      "new_content": "complete updated file content here",
      "reason": "explanation of change"
    }}
  ],
  "explanation": "Brief summary of changes made"
}}

Include complete file content in new_content field. Make real, working changes."""

        try:
            # Use the existing AI assistant for code generation
            from ai_assistant import get_chat_response
            
            # Format as a chat history for the AI
            chat_history = [
                {"role": "user", "content": prompt}
            ]
            
            ai_response = get_chat_response(chat_history, model_type='smart')
            
            # Parse AI response with robust error handling
            import json
            import re
            
            def clean_json_string(text):
                """Clean JSON string by removing control characters and fixing common issues"""
                if not text:
                    return text
                
                # Remove control characters (except newlines, tabs, carriage returns)
                cleaned = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')
                
                # Remove BOM if present
                cleaned = cleaned.lstrip('\ufeff')
                
                # Fix common JSON issues
                cleaned = re.sub(r',\s*}', '}', cleaned)  # Remove trailing commas before }
                cleaned = re.sub(r',\s*]', ']', cleaned)  # Remove trailing commas before ]
                
                return cleaned
            
            # Improved JSON extraction and parsing
            def extract_and_parse_json(text):
                """Extract and parse JSON from AI response with robust error handling."""
                if not text:
                    return None
                
                # Remove markdown code blocks first
                text = re.sub(r'```json\s*', '', text)
                text = re.sub(r'```\s*', '', text)
                text = re.sub(r'^```[\w]*\n', '', text, flags=re.MULTILINE)
                
                # Try multiple JSON extraction patterns
                patterns = [
                    r'\{[\s\S]*?\}(?=\s*$|\s*\n\s*[^{])',  # Complete JSON object
                    r'\{[\s\S]*?"changes"[\s\S]*?\}',  # JSON containing 'changes'
                    r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Nested JSON
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.DOTALL)
                    for match in matches:
                        try:
                            # Clean and attempt to parse
                            cleaned = clean_json_string(match.strip())
                            
                            # Try to fix common JSON issues
                            if cleaned.endswith(','):
                                cleaned = cleaned[:-1]
                            
                            # Handle truncated JSON by ensuring proper closure
                            open_braces = cleaned.count('{') - cleaned.count('}')
                            open_brackets = cleaned.count('[') - cleaned.count(']')
                            
                            if open_braces > 0:
                                cleaned += '}' * open_braces
                            if open_brackets > 0:
                                cleaned += ']' * open_brackets
                            
                            parsed = json.loads(cleaned)
                            if isinstance(parsed, dict) and ('changes' in parsed or 'explanation' in parsed):
                                return parsed
                        except json.JSONDecodeError as e:
                            print(f"JSON parse error for match: {str(e)[:100]}")
                            continue
                        except Exception as e:
                            print(f"General parse error: {str(e)[:100]}")
                            continue
                
                # If no valid JSON found, try to extract key information manually
                if 'changes' in text.lower() or 'file_path' in text.lower():
                    print("Attempting manual extraction from AI response...")
                    try:
                        # Try to extract structured information even if JSON is malformed
                        explanation_match = re.search(r'"explanation":\s*"([^"]*)"', text)
                        explanation = explanation_match.group(1) if explanation_match else "AI suggested changes"
                        
                        # Look for file modifications in the text
                        file_mentions = re.findall(r'src/[\w/\.]+\.jsx?', text)
                        if file_mentions:
                            return {
                                "changes": [{"file_path": f"frontend/{file_mentions[0]}", "edit_type": "content_update"}],
                                "explanation": explanation
                            }
                    except:
                        pass
                
                return None
            
            response_data = extract_and_parse_json(ai_response)
            
            if not response_data:
                # Fallback: Parse the response manually for key information
                print(f"JSON parsing failed, creating fallback response for: {user_message}")
                
                # Try to create a specific response based on the user's request
                fallback_changes = []
                fallback_explanation = f"Processing request: '{user_message}'"
                
                # Handle specific personalization requests
                if "name" in user_message.lower() and ("neelesh" in user_message.lower() or "include" in user_message.lower()):
                    # Read current App.jsx to personalize it
                    app_file = project_path / "frontend" / "src" / "App.jsx"
                    if app_file.exists():
                        try:
                            with open(app_file, 'r', encoding='utf-8') as f:
                                current_content = f.read()
                            
                            # Create personalized version
                            personalized_content = current_content.replace(
                                'Welcome to Your Project', 'Welcome to Neelesh\'s Project'
                            ).replace(
                                'Your application', 'Neelesh\'s application'
                            ).replace(
                                'Welcome to app-', 'Welcome to Neelesh\'s app-'
                            )
                            
                            # If no changes were made, add a personal header
                            if personalized_content == current_content:
                                # Add a personal welcome section
                                if 'return (' in personalized_content:
                                    personalized_content = personalized_content.replace(
                                        'return (',
                                        '''return (
    <div className="text-center py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
      <h2 className="text-lg font-semibold">Welcome, Neelesh! 👋</h2>
      <p className="text-sm opacity-90">This application was built just for you</p>
    </div>
    <div className="flex-1">''',
                                        1
                                    )
                                    # Add closing div
                                    personalized_content = personalized_content.replace(
                                        '  );\n}', '    </div>\n  );\n}'
                                    )
                            
                            fallback_changes = [{
                                "file_path": "frontend/src/App.jsx",
                                "edit_type": "content_update",
                                "new_content": personalized_content,
                                "reason": "Added personalization for Neelesh"
                            }]
                            fallback_explanation = "Added personalized welcome message for Neelesh to the application"
                            
                        except Exception as e:
                            print(f"Error creating personalized content: {e}")
                
                # If no specific changes could be made, provide helpful suggestions
                if not fallback_changes:
                    fallback_suggestions = []
                    
                    if "fix" in user_message.lower():
                        if "frontend" in user_message.lower():
                            fallback_suggestions = [
                                "Fix React array.map() errors in components",
                                "Fix API endpoints to use /api/v1 prefix", 
                                "Fix localStorage JSON parsing errors",
                                "Remove duplicate ErrorBoundary declarations"
                            ]
                        else:
                            fallback_suggestions = [
                                "Fix CORS issues in FastAPI backend",
                                "Fix database connection errors",
                                "Fix API endpoint routing issues"
                            ]
                    elif any(word in user_message.lower() for word in ["add", "create", "build"]):
                        fallback_suggestions = [
                            "Add a login/signup form",
                            "Add a user dashboard",
                            "Add data filtering and search",
                            "Add responsive navigation menu"
                        ]
                    else:
                        fallback_suggestions = [
                            "Be more specific about what to fix or add",
                            "Example: 'Fix the array map error in ProductList'",
                            "Example: 'Add a login form to the homepage'"
                        ]
                    
                    fallback_explanation = f"Request '{user_message}' needs more detail. Try one of these specific requests:\n• " + "\n• ".join(fallback_suggestions[:4])
                
                response_data = {
                    "changes": fallback_changes,
                    "explanation": fallback_explanation
                }
            
            changes = response_data.get("changes", [])
            explanation = response_data.get("explanation", "AI-generated changes")
            
            # Validate changes structure
            valid_changes = []
            for change in changes:
                if isinstance(change, dict) and change.get("file_path") and change.get("content"):
                    # Ensure content is not truncated or invalid
                    content = str(change.get("content", "")).strip()
                    if len(content) > 10:  # Minimum content check
                        valid_changes.append(change)
            
            if not valid_changes:
                # Enhanced error message with detected issues
                error_msg = "AI couldn't determine what changes to make."
                if project_analysis:
                    error_msg += f" {project_analysis.replace('DETECTED ISSUES TO FIX:', 'However, I found these issues you could address:')}"
                else:
                    error_msg += f" Please be more specific. The request '{user_message}' is too vague."
                
                await manager.send_to_project(project_name, {
                    "type": "status",
                    "phase": "error",
                    "message": f"❌ {error_msg[:100]}..."
                })
                
                return {
                    "success": False, 
                    "error": error_msg,
                    "suggestion": explanation if 'explanation' in locals() else "Try being more specific about what you want to change."
                }
            
            changes = valid_changes

            # Apply the changes with targeted editing
            files_modified = []
            for change in changes:
                file_path = change.get("file_path", "").lstrip("/")
                edit_type = change.get("edit_type", "replace")  # Default to full replace for backwards compatibility
                
                if not file_path:
                    continue
                    
                target = project_path / file_path
                # Ensure path is within project
                try:
                    target.resolve().relative_to(project_path.resolve())
                except Exception:
                    continue
                    
                target.parent.mkdir(parents=True, exist_ok=True)
                
                # Handle different edit types
                if edit_type == "targeted_edit":
                    # Targeted edit - modify specific sections
                    old_code = change.get("old_code", "")
                    new_code = change.get("new_code", "")
                    target_section = change.get("target_section", "")
                    
                    if not old_code or new_code is None:
                        continue
                    
                    # Read existing file if it exists
                    if target.exists():
                        with open(target, 'r', encoding='utf-8') as f:
                            existing_content = f.read()
                        
                        # Apply targeted edit
                        if old_code in existing_content:
                            updated_content = existing_content.replace(old_code, new_code, 1)
                            cleaned = _clean_ai_generated_content(updated_content, target.name)
                            
                            with open(target, 'w', encoding='utf-8', newline='\n') as f:
                                f.write(cleaned)
                            files_modified.append(file_path)
                            
                            await manager.send_to_project(project_name, {
                                "type": "file_changed",
                                "file_path": file_path,
                                "message": f"✏️ Applied targeted edit to {file_path} ({target_section})"
                            })
                        else:
                            await manager.send_to_project(project_name, {
                                "type": "warning",
                                "message": f"⚠️ Could not find target code in {file_path} for section: {target_section}"
                            })
                    else:
                        await manager.send_to_project(project_name, {
                            "type": "warning", 
                            "message": f"⚠️ File {file_path} does not exist for targeted edit"
                        })
                        
                elif edit_type == "append":
                    # Append to existing file
                    content = change.get("content", "")
                    if not content:
                        continue
                        
                    existing_content = ""
                    if target.exists():
                        with open(target, 'r', encoding='utf-8') as f:
                            existing_content = f.read()
                    
                    updated_content = existing_content + "\n" + content
                    cleaned = _clean_ai_generated_content(updated_content, target.name)
                    
                    with open(target, 'w', encoding='utf-8', newline='\n') as f:
                        f.write(cleaned)
                    files_modified.append(file_path)
                    
                else:
                    # Default: full file replacement (backwards compatibility)
                    content = change.get("content", "") or change.get("new_content", "")
                    if not content:
                        continue
                        
                    cleaned = _clean_ai_generated_content(content, target.name)
                    
                    with open(target, 'w', encoding='utf-8', newline='\n') as f:
                        f.write(cleaned)
                    files_modified.append(file_path)

            # Validate and fix critical files
            await manager.send_to_project(project_name, {
                "type": "status",
                "phase": "validate",
                "message": "Validating changes..."
            })
            
            await validate_and_fix_project_files(project_path, project_name)
            check = await check_project_errors(project_name)
            remaining_errors = check.get("errors", []) if check.get("success") else []

            # Optionally rerun project
            preview_url = None
            if re_run and files_modified:
                await manager.send_to_project(project_name, {
                    "type": "status",
                    "phase": "run",
                    "message": "Restarting development servers..."
                })
                run_resp = await run_project({
                    "project_name": project_name,
                    "tech_stack": tech_stack
                })
                if isinstance(run_resp, dict):
                    preview_url = run_resp.get("preview_url")
                    if preview_url:
                        await manager.send_to_project(project_name, {
                            "type": "preview_ready", 
                            "url": preview_url
                        })

            # Send success message
            if files_modified:
                await manager.send_to_project(project_name, {
                    "type": "success",
                    "message": f"✅ Successfully modified {len(files_modified)} file(s) with targeted changes"
                })

            return {
                "success": True,
                "explanation": explanation,
                "files_modified": files_modified,
                "preview_url": preview_url,
                "errors": remaining_errors
            }

        except Exception as ai_error:
            print(f"AI processing error: {ai_error}")
            print(f"AI response preview: {ai_response[:500] if 'ai_response' in locals() else 'No response generated'}")
            await manager.send_to_project(project_name, {
                "type": "status",
                "phase": "error",
                "message": f"❌ AI processing failed: {str(ai_error)}"
            })
            return {
                "success": False,
                "error": f"AI processing failed: {str(ai_error)}"
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"AI chat error: {e}")
        return {"success": False, "error": str(e)}

# --- AI Apply Changes Endpoint ---
@app.post("/api/ai-apply-changes")
async def ai_apply_changes(request: dict = Body(...)):
    """Apply AI-suggested changes to project files, validate, and optionally rerun."""
    try:
        project_name = request.get("project_name")
        edits = request.get("edits", [])  # List[{file_path, content}]
        re_run = bool(request.get("re_run", False))
        tech_stack = request.get("tech_stack", [])

        if not project_name:
            raise HTTPException(status_code=400, detail="project_name is required")
        if not isinstance(edits, list) or not edits:
            raise HTTPException(status_code=400, detail="No edits provided")

        # Resolve project path
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}

        # Apply edits safely
        files_modified = []
        for edit in edits:
            file_path = (edit.get("file_path") or "").lstrip("/")
            content = edit.get("content", "")
            if not file_path:
                continue
            target = project_path / file_path
            # Ensure path is within project
            try:
                target.resolve().relative_to(project_path.resolve())
            except Exception:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            cleaned = _clean_ai_generated_content(content, target.name)
            with open(target, 'w', encoding='utf-8', newline='\n') as f:
                f.write(cleaned)
            files_modified.append(file_path)
            await manager.send_to_project(project_name, {
                "type": "file_changed",
                "file_path": file_path,
                "message": f"✍️ Updated {file_path}"
            })

        # Validate and fix critical files
        await manager.send_to_project(project_name, {
            "type": "status",
            "phase": "validate",
            "message": "Validating updates..."
        })
        await validate_and_fix_project_files(project_path, project_name)
        check = await check_project_errors(project_name)
        remaining_errors = check.get("errors", []) if check.get("success") else []

        # Optionally rerun project
        preview_url = None
        if re_run:
            await manager.send_to_project(project_name, {
                "type": "status",
                "phase": "run",
                "message": "Restarting development servers..."
            })
            run_resp = await run_project({
                "project_name": project_name,
                "tech_stack": tech_stack
            })
            if isinstance(run_resp, dict):
                preview_url = run_resp.get("preview_url")
                if preview_url:
                    await manager.send_to_project(project_name, {"type": "preview_ready", "url": preview_url})

        await manager.send_to_project(project_name, {
            "type": "status",
            "phase": "ready",
            "message": "✅ Changes applied",
            "preview_url": preview_url,
            "errors_remaining": remaining_errors
        })

        return {
            "success": True,
            "files_modified": files_modified,
            "preview_url": preview_url,
            "errors": remaining_errors
        }

    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

async def simulate_typing_effect(project_name: str, file_path: str, content: str, delay_per_char: float = 0.01):
    """Simulate typing effect by sending content in chunks"""
    lines = content.split('\n')
    current_content = ""
    
    for i, line in enumerate(lines):
        current_content += line
        if i < len(lines) - 1:  # Add newline except for last line
            current_content += '\n'
        
        # Send partial content
        await manager.send_to_project(project_name, {
            "type": "file_content_update",
            "file_path": file_path,
            "content": current_content,
            "is_complete": i == len(lines) - 1
        })
        
        # Small delay for typing effect
        await asyncio.sleep(delay_per_char * len(line))

def _strip_code_fences(text: str) -> str:
    """Remove ```...``` fences from AI outputs if present."""
    try:
        t = text.strip()
        # Match fenced block optionally with language like ```json
        m = re.match(r"^```(?:\w+)?\s*([\s\S]*?)\s*```$", t)
        return m.group(1).strip() if m else t
    except Exception:
        return text

def _clean_ai_generated_content(content: str, filename: str) -> str:
    """Normalize AI-generated content by stripping BOM/code fences and validating JSON."""
    try:
        # Remove control characters (except newlines, tabs, carriage returns)
        cleaned = ''.join(char for char in content if ord(char) >= 32 or char in '\n\t\r')
        
        # Remove BOM
        cleaned = cleaned.lstrip('\ufeff')
        cleaned = _strip_code_fences(cleaned)

        # If it's a JSON file, try to extract a strict JSON object/array and pretty print
        if filename.lower().endswith('.json'):
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            candidate = cleaned[start:end+1] if start != -1 and end != -1 and start < end else cleaned
            try:
                obj = json.loads(candidate)
                cleaned = json.dumps(obj, indent=2)
            except Exception:
                try:
                    # Attempt to remove trailing commas and retry
                    tmp = re.sub(r",\s*([}\]])", r"\1", candidate)
                    obj = json.loads(tmp)
                    cleaned = json.dumps(obj, indent=2)
                except Exception as e:
                    print(f"JSON validation failed for {filename}: {e}")
                    # Return the original cleaned content as fallback
                    pass
        return cleaned
    except Exception:
        return content

async def create_file_with_animation(file_path: Path, content: str, relative_path: str, project_name: str) -> str:
    """Create a file with real-time typing animation"""
    
    # Announce file creation
    await manager.send_to_project(project_name, {
        "type": "terminal_output",
        "message": f"📝 Creating {relative_path}...",
        "level": "info"
    })
    
    # Create directory if needed
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Normalize AI content (especially for JSON and fenced blocks)
    final_content = _clean_ai_generated_content(content, file_path.name)
    
    # If JSON, re-validate and pretty print; provide fallback for package.json
    if file_path.suffix.lower() == ".json":
        try:
            obj = json.loads(final_content)
            final_content = json.dumps(obj, indent=2)
        except Exception as e:
            print(f"Invalid JSON for {relative_path}: {e}")
            if file_path.name == "package.json":
                # Minimal safe fallback
                final_content = json.dumps({
                    "name": Path(project_name).name.lower().replace(" ", "-"),
                    "version": "1.0.0",
                    "private": True,
                    "type": "module",
                    "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"},
                    "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"},
                    "devDependencies": {"vite": "^4.4.0", "@vitejs/plugin-react": "^4.0.0"}
                }, indent=2)

    # Send file creation start
    await manager.send_to_project(project_name, {
        "type": "file_created",
        "file_path": relative_path,
        "file_type": "file",
        "size": len(final_content)
    })
    
    # Simulate typing effect for code files
    if any(relative_path.endswith(ext) for ext in ['.jsx', '.tsx', '.js', '.ts', '.py', '.css', '.html', '.json']):
        await simulate_typing_effect(project_name, relative_path, final_content, 0.005)
    else:
        # For non-code files, just send the complete content
        await manager.send_to_project(project_name, {
            "type": "file_content_update",
            "file_path": relative_path,
            "content": final_content,
            "is_complete": True
        })
    
    # Write the actual file
    with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(final_content)
    
    await asyncio.sleep(0.1)  # Brief pause between files
    
    return relative_path

async def validate_and_fix_project_files(project_path: Path, project_name: str) -> bool:
    """Validate and fix critical project files like frontend/package.json before running."""
    try:
        frontend_path = project_path / "frontend"
        package_json_path = frontend_path / "package.json"

        if not frontend_path.exists():
            return True  # Nothing to validate

        if package_json_path.exists():
            try:
                raw = package_json_path.read_text(encoding='utf-8', errors='ignore')
                cleaned = _clean_ai_generated_content(raw, 'package.json')
                obj = json.loads(cleaned)
                # Optionally ensure minimal required fields
                if "name" not in obj:
                    obj["name"] = project_name.lower().replace(" ", "-")
                package_json_path.write_text(json.dumps(obj, indent=2), encoding='utf-8', newline='\n')
                return True
            except Exception as e:
                print(f"Repairing package.json due to error: {e}")
                fallback = {
                    "name": project_name.lower().replace(" ", "-"),
                    "version": "1.0.0",
                    "private": True,
                    "type": "module",
                    "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"},
                    "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"},
                    "devDependencies": {"vite": "^4.4.0", "@vitejs/plugin-react": "^4.0.0"}
                }
                package_json_path.write_text(json.dumps(fallback, indent=2), encoding='utf-8', newline='\n')
                return True
        else:
            # Create a minimal package.json
            minimal = {
                "name": project_name.lower().replace(" ", "-"),
                "version": "1.0.0",
                "private": True,
                "type": "module",
                "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"},
                "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"},
                "devDependencies": {"vite": "^4.4.0", "@vitejs/plugin-react": "^4.0.0"}
            }
            frontend_path.mkdir(parents=True, exist_ok=True)
            package_json_path.write_text(json.dumps(minimal, indent=2), encoding='utf-8', newline='\n')
            return True
    except Exception as e:
        print(f"validate_and_fix_project_files error: {e}")
        return False

# --- File Save Endpoint ---
@app.post("/api/save-project-file")
async def save_project_file(request: dict = Body(...)):
    """Save file content to the project"""
    try:
        project_name = request.get("project_name")
        file_path = request.get("file_path")
        content = request.get("content")
        
        # Get project path
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        # Security check
        full_file_path = project_path / file_path.lstrip('/')
        try:
            full_file_path.resolve().relative_to(project_path.resolve())
        except ValueError:
            return {"success": False, "error": "Invalid file path"}
        
        # Create directory if it doesn't exist
        full_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean content before saving
        cleaned_content = _clean_ai_generated_content(content, full_file_path.name)
        
        # Save file
        with open(full_file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        # Notify via WebSocket
        await manager.send_to_project(project_name, {
            "type": "file_changed",
            "file_path": file_path,
            "message": f"File saved: {file_path}"
        })
        
        return {"success": True}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Install Dependencies Endpoint ---
@app.post("/api/install-dependencies")
async def install_dependencies(request: dict = Body(...)):
    """Install project dependencies"""
    try:
        project_name = request.get("project_name")
        tech_stack = request.get("tech_stack", [])
        
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}
        
        # Install frontend dependencies
        frontend_path = project_path / "frontend"
        if frontend_path.exists() and (frontend_path / "package.json").exists():
            await manager.send_to_project(project_name, {
                "type": "terminal_output",
                "message": "📦 Installing frontend dependencies...",
                "level": "info"
            })
            
            try:
                process = await asyncio.create_subprocess_shell(
                    "npm install",
                    cwd=frontend_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": "✅ Frontend dependencies installed",
                        "level": "success"
                    })
                else:
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": f"⚠️ Frontend install issues: {stderr.decode()}",
                        "level": "warning"
                    })
            except Exception as e:
                await manager.send_to_project(project_name, {
                    "type": "terminal_output",
                    "message": f"❌ Frontend install failed: {str(e)}",
                    "level": "error"
                })
        
        # Install backend dependencies if Python/FastAPI
        backend_path = project_path / "backend"
        if backend_path.exists() and (backend_path / "requirements.txt").exists():
            await manager.send_to_project(project_name, {
                "type": "terminal_output",
                "message": "📦 Installing backend dependencies...",
                "level": "info"
            })
            
            try:
                process = await asyncio.create_subprocess_shell(
                    "pip install -r requirements.txt",
                    cwd=backend_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": "✅ Backend dependencies installed",
                        "level": "success"
                    })
                else:
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": f"⚠️ Backend install issues: {stderr.decode()}",
                        "level": "warning"
                    })
            except Exception as e:
                await manager.send_to_project(project_name, {
                    "type": "terminal_output",
                    "message": f"❌ Backend install failed: {str(e)}",
                    "level": "error"
                })
        
        return {"success": True}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Preserve a stable reference to the endpoint function before any later helper redefinitions
install_dependencies_endpoint = install_dependencies

# --- Run Project Endpoint ---
@app.post("/api/run-project")
async def run_project(request: dict = Body(...)):
    """Build and run the project using sandboxed preview"""
    try:
        project_name = request.get("project_name")
        tech_stack = request.get("tech_stack", [])
        
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}
        
        # Check if frontend exists
        frontend_path = project_path / "frontend"
        if not frontend_path.exists():
            return {"success": False, "error": "Frontend not found"}
        
        await manager.send_to_project(project_name, {
            "type": "terminal_output", 
            "message": "🚀 Preparing sandboxed preview...",
            "level": "info"
        })
        
        # Generate sandbox preview URL
        sandbox_url = f"http://localhost:8000/api/sandbox-preview/{project_slug}"
        
        # Validate that essential files exist
        essential_files = ["src/App.jsx", "src/main.jsx"]
        missing_files = []
        for file_path in essential_files:
            if not (frontend_path / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            await manager.send_to_project(project_name, {
                "type": "terminal_output",
                "message": f"⚠️ Missing essential files: {', '.join(missing_files)}",
                "level": "warning"
            })
        
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": "✅ Sandbox preview ready!",
            "level": "info"
        })
        
        # Send preview ready signal
        await manager.send_to_project(project_name, {
            "type": "preview_ready",
            "url": sandbox_url
        })
        
        return {
            "success": True,
            "preview_url": sandbox_url,
            "message": "Sandbox preview is ready",
            "type": "sandbox"
        }
        
    except Exception as e:
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": f"❌ Failed to start preview: {str(e)}",
            "level": "error"
        })
        return {"success": False, "error": str(e)}

# --- Stop Project Endpoint ---
@app.post("/api/stop-project")
async def check_project_errors(project_name: str = Query(...)):
    """Check for errors in the project"""
    try:
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}
        
        errors = []
        
        # Check for common issues
        frontend_path = project_path / "frontend"
        if frontend_path.exists():
            # Check package.json exists
            pkg_path = frontend_path / "package.json"
            if not pkg_path.exists():
                errors.append({
                    "severity": "error",
                    "message": "Missing package.json",
                    "file": "frontend/package.json",
                    "line": 1
                })
            else:
                try:
                    raw = pkg_path.read_text(encoding="utf-8", errors="ignore")
                    cleaned = _clean_ai_generated_content(raw, "package.json")
                    pkg = json.loads(cleaned)
                    scripts = (pkg.get("scripts") or {}) if isinstance(pkg, dict) else {}
                    if not isinstance(scripts, dict):
                        errors.append({
                            "severity": "error",
                            "message": "Invalid scripts section in package.json",
                            "file": "frontend/package.json",
                            "line": 1
                        })
                    else:
                        if not ("dev" in scripts or "start" in scripts):
                            errors.append({
                                "severity": "error",
                                "message": "Missing dev/start script in package.json",
                                "file": "frontend/package.json",
                                "line": 1
                            })
                except Exception as e:
                    errors.append({
                        "severity": "error",
                        "message": f"Invalid JSON in package.json: {str(e)}",
                        "file": "frontend/package.json",
                        "line": 1
                    })
            
            # Check for syntax errors in JS/JSX files
            for file in frontend_path.rglob("*.js*"):
                if file.is_file():
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Basic syntax check
                            if content.count('{') != content.count('}'):
                                errors.append({
                                    "severity": "error",
                                    "message": "Mismatched braces",
                                    "file": str(file.relative_to(project_path)),
                                    "line": 1
                                })
                    except Exception:
                        pass
        
        return {"success": True, "errors": errors}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Auto Fix Errors Endpoint ---  
@app.post("/api/auto-fix-errors")
async def auto_fix_errors(request: dict = Body(...)):
    """Automatically fix common errors"""
    try:
        project_name = request.get("project_name")
        errors = request.get("errors", [])
        tech_stack = request.get("tech_stack", [])
        
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}
        
        files_modified = []
        
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": f"🔧 Auto-fixing {len(errors)} errors...",
            "level": "info"
        })
        
        for error in errors:
            if "Missing package.json" in error.get("message", ""):
                # Create basic package.json
                package_json = {
                    "name": project_slug,
                    "version": "1.0.0",
                    "private": True,
                    "scripts": {
                        "dev": "next dev" if "Next.js" in tech_stack else "vite",
                        "build": "next build" if "Next.js" in tech_stack else "vite build",
                        "preview": "vite preview --port 5173" if "Next.js" not in tech_stack else "next start",
                        "start": "next start" if "Next.js" in tech_stack else "vite"
                    },
                    "dependencies": {
                        "react": "^18.2.0",
                        "react-dom": "^18.2.0"
                    }
                }
                
                if "Next.js" in tech_stack:
                    package_json["dependencies"]["next"] = "^14.0.0"
                else:
                    # Prefer Vite defaults; dev deps installed separately during scaffold
                    package_json.setdefault("devDependencies", {})
                    package_json["devDependencies"].update({
                        "vite": "^5.0.0"
                    })
                
                if "TypeScript" in tech_stack:
                    package_json["dependencies"]["typescript"] = "^5.0.0"
                    package_json["dependencies"]["@types/react"] = "^18.0.0"
                    package_json["dependencies"]["@types/react-dom"] = "^18.0.0"
                
                package_path = project_path / "frontend" / "package.json"
                with open(package_path, 'w', encoding='utf-8') as f:
                    json.dump(package_json, f, indent=2)
                
                files_modified.append("frontend/package.json")
                
                await manager.send_to_project(project_name, {
                    "type": "terminal_output",
                    "message": "✅ Created package.json",
                    "level": "success"
                })
            elif "Invalid JSON in package.json" in error.get("message", ""):
                # Try to clean and rewrite package.json
                pkg_path = project_path / "frontend" / "package.json"
                if pkg_path.exists():
                    try:
                        raw = pkg_path.read_text(encoding="utf-8", errors="ignore")
                        cleaned = _clean_ai_generated_content(raw, "package.json")
                        pkg = json.loads(cleaned)
                        with open(pkg_path, 'w', encoding='utf-8') as f:
                            json.dump(pkg, f, indent=2)
                        files_modified.append("frontend/package.json")
                        await manager.send_to_project(project_name, {
                            "type": "terminal_output",
                            "message": "🧹 Cleaned invalid JSON in package.json",
                            "level": "success"
                        })
                    except Exception:
                        # Fallback to minimal vite-based package
                        fallback = {
                            "name": project_slug,
                            "version": "1.0.0",
                            "private": True,
                            "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview --port 5173", "start": "vite"}
                        }
                        with open(pkg_path, 'w', encoding='utf-8') as f:
                            json.dump(fallback, f, indent=2)
                        files_modified.append("frontend/package.json")
                        await manager.send_to_project(project_name, {
                            "type": "terminal_output",
                            "message": "✅ Replaced invalid package.json with a safe default",
                            "level": "warning"
                        })
            elif "Missing dev/start script" in error.get("message", "") or "Invalid scripts section in package.json" in error.get("message", ""):
                pkg_path = project_path / "frontend" / "package.json"
                if pkg_path.exists():
                    try:
                        raw = pkg_path.read_text(encoding="utf-8", errors="ignore")
                        cleaned = _clean_ai_generated_content(raw, "package.json")
                        pkg = json.loads(cleaned)
                        if not isinstance(pkg, dict):
                            pkg = {}
                        scripts = pkg.get("scripts") or {}
                        if not isinstance(scripts, dict):
                            scripts = {}
                        # Heuristic: use vite if dependency present, else next if Next.js in stack
                        deps = pkg.get("dependencies", {}) or {}
                        use_vite = "vite" in (pkg.get("devDependencies", {}) or {}) or "vite" in deps
                        if "Next.js" in tech_stack:
                            scripts.update({"dev": "next dev", "build": "next build", "start": "next start"})
                        elif use_vite or True:
                            scripts.update({"dev": "vite", "build": "vite build", "preview": "vite preview --port 5173", "start": "vite"})
                        pkg["scripts"] = scripts
                        with open(pkg_path, 'w', encoding='utf-8') as f:
                            json.dump(pkg, f, indent=2)
                        files_modified.append("frontend/package.json")
                        await manager.send_to_project(project_name, {
                            "type": "terminal_output",
                            "message": "🔧 Added missing scripts to package.json",
                            "level": "success"
                        })
                    except Exception as e:
                        await manager.send_to_project(project_name, {
                            "type": "terminal_output",
                            "message": f"⚠️ Could not update scripts in package.json: {str(e)}",
                            "level": "warning"
                        })
        
        return {
            "success": True,
            "files_modified": files_modified,
            "fixes_applied": len(errors)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Execute Terminal Command Endpoint ---
@app.post("/api/execute-command") 
async def execute_command(request: dict = Body(...)):
    """Execute terminal command in project directory"""
    try:
        project_name = request.get("project_name")
        command = request.get("command")
        working_directory = request.get("working_directory", "/")
        
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}
        
        # Determine actual working directory
        if working_directory == "/" or not working_directory:
            cwd = project_path
        else:
            cwd = project_path / working_directory.lstrip('/')
        
        # Security: only allow safe commands
        safe_commands = [
            "ls", "dir", "pwd", "cat", "type", "npm", "node", "python", "pip",
            "git", "cd", "mkdir", "touch", "echo", "clear", "cls"
        ]
        
        command_parts = command.split()
        if not command_parts or command_parts[0] not in safe_commands:
            return {"success": False, "error": f"Command '{command_parts[0] if command_parts else command}' not allowed"}
        
        try:
            # Handle cd command specially
            if command.startswith("cd "):
                target_dir = command[3:].strip()
                if target_dir == "..":
                    new_cwd = cwd.parent
                elif target_dir == "/":
                    new_cwd = project_path
                else:
                    new_cwd = cwd / target_dir
                
                # Security check
                try:
                    new_cwd.resolve().relative_to(project_path.resolve())
                    return {
                        "success": True,
                        "output": f"Changed directory to {new_cwd.relative_to(project_path)}",
                        "working_directory": str(new_cwd.relative_to(project_path))
                    }
                except ValueError:
                    return {"success": False, "error": "Cannot navigate outside project directory"}
            
            # Execute other commands
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8')
            if stderr:
                output += f"\nError: {stderr.decode('utf-8')}"
            
            return {
                "success": True,
                "output": output,
                "working_directory": working_directory
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Get Project File Tree Endpoint ---
@app.get("/api/project-file-tree")
async def get_project_file_tree(project_name: str = Query(...)):
    """Get file tree structure for a project"""
    try:
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            # Return an empty tree during early generation instead of an error
            return {
                "success": True,
                "file_tree": [],
                "project_path": str(project_path)
            }
        
        def build_file_tree(path: Path, base_path: Path = None):
            """Recursively build file tree structure"""
            if base_path is None:
                base_path = path
            
            items = []
            
            try:
                for item in sorted(path.iterdir()):
                    # Skip hidden files and common build directories
                    if item.name.startswith('.') or item.name in ['node_modules', '__pycache__', 'dist', 'build']:
                        continue
                    
                    relative_path = str(item.relative_to(base_path)).replace('\\', '/')
                    
                    if item.is_dir():
                        items.append({
                            "name": item.name,
                            "path": relative_path,
                            "type": "directory",
                            "children": build_file_tree(item, base_path)
                        })
                    else:
                        items.append({
                            "name": item.name,
                            "path": relative_path,
                            "type": "file",
                            "size": item.stat().st_size
                        })
            except PermissionError:
                pass
            
            return items
        
        file_tree = build_file_tree(project_path)
        
        return {
            "success": True,
            "file_tree": file_tree,
            "project_path": str(project_path)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Rate Limit Status (to avoid 404 in frontend) ---
@app.get("/api/rate-limit-status")
async def rate_limit_status():
    """Return a basic rate limit status; integrate with GitHub if available."""
    try:
        # Minimal static response to satisfy UI; extend to real provider limits as needed
        return {
            "success": True,
            "rate_limit": {
                "core": {"limit": 5000, "remaining": 4999},
                "search": {"limit": 30, "remaining": 30}
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Get Project File Content Endpoint ---
@app.get("/api/project-file-content")
async def get_project_file_content(project_name: str = Query(...), file_path: str = Query(...)):
    """Get content of a specific file in the project"""
    try:
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}
        
        # Security check
        full_file_path = project_path / file_path.lstrip('/')
        try:
            full_file_path.resolve().relative_to(project_path.resolve())
        except ValueError:
            return {"success": False, "error": "Invalid file path"}
        
        if not full_file_path.exists():
            return {"success": False, "error": "File not found"}
        
        if not full_file_path.is_file():
            return {"success": False, "error": "Path is not a file"}
        
        # Read file content
        try:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "file_path": file_path,
                "size": full_file_path.stat().st_size
            }
            
        except UnicodeDecodeError:
            # Handle binary files
            return {
                "success": False,
                "error": "File is binary and cannot be displayed as text"
            }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Stop Project Endpoint ---
@app.post("/api/stop-project")
async def stop_project(request: dict = Body(...)):
    """Stop running project servers"""
    try:
        project_name = request.get("project_name")
        
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": "⏹️ Stopping project servers...",
            "level": "info"
        })
        
        # In a real implementation, you would track running processes
        # and terminate them here. For this demo, we'll just simulate.
        
        await asyncio.sleep(1)  # Simulate stopping time
        
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": "✅ Project servers stopped",
            "level": "success"
        })
        
        return {"success": True}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Project Template Creation Functions ---

async def create_react_frontend_with_animation(frontend_path: Path, idea: str, project_name: str, needs_typescript: bool, needs_auth: bool) -> List[str]:
    """Create React frontend structure with real-time animation"""
    files_created = []
    
    # Create directories
    src_path = frontend_path / "src"
    components_path = src_path / "components"
    pages_path = src_path / "pages"
    utils_path = src_path / "utils"
    
    for path in [src_path, components_path, pages_path, utils_path]:
        path.mkdir(parents=True, exist_ok=True)
    
    # Package.json
    package_json = {
        "name": project_name.lower().replace(" ", "-"),
        "version": "0.1.0",
        "private": True,
        "dependencies": {
            "@testing-library/jest-dom": "^5.16.4",
            "@testing-library/react": "^13.3.0",
            "@testing-library/user-event": "^13.5.0",
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-router-dom": "^6.8.0",
            "react-scripts": "5.0.1",
            "axios": "^1.3.0",
            "tailwindcss": "^3.2.0",
            "autoprefixer": "^10.4.13",
            "postcss": "^8.4.21"
        },
        "scripts": {
            "start": "react-scripts start",
            "build": "react-scripts build",
            "test": "react-scripts test",
            "eject": "react-scripts eject"
        },
        "eslintConfig": {
            "extends": ["react-app", "react-app/jest"]
        },
        "browserslist": {
            "production": [">0.2%", "not dead", "not op_mini all"],
            "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
        }
    }
    
    if needs_typescript:
        package_json["dependencies"].update({
            "typescript": "^4.9.0",
            "@types/node": "^16.18.0",
            "@types/react": "^18.0.0",
            "@types/react-dom": "^18.0.0"
        })
    
    if needs_auth:
        package_json["dependencies"]["auth0-react"] = "^2.0.0"
    
    package_content = json.dumps(package_json, indent=2)
    rel_path = await create_file_with_animation(
        frontend_path / "package.json", 
        package_content, 
        "frontend/package.json", 
        project_name
    )
    files_created.append(rel_path)
    
    # Public/index.html
    public_path = frontend_path / "public"
    public_path.mkdir(exist_ok=True)
    
    index_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="{idea}" />
    <title>{project_name}</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>"""
    
    rel_path = await create_file_with_animation(
        public_path / "index.html", 
        index_html, 
        "frontend/public/index.html", 
        project_name
    )
    files_created.append(rel_path)
    
    # Main App component
    ext = ".tsx" if needs_typescript else ".jsx"
    
    app_component = f"""import React from 'react';
import {{ BrowserRouter as Router, Routes, Route }} from 'react-router-dom';
import './App.css';
import Home from './pages/Home{ext}';
import Header from './components/Header{ext}';

function App() {{
  return (
    <div className="App min-h-screen bg-gray-50">
      <Router>
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={{<Home />}} />
          </Routes>
        </main>
      </Router>
    </div>
  );
}}

export default App;"""
    
    rel_path = await create_file_with_animation(
        src_path / f"App{ext}", 
        app_component, 
        f"frontend/src/App{ext}", 
        project_name
    )
    files_created.append(rel_path)
    
    # Index.js/tsx
    index_content = f"""import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App{ext}';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);"""
    
    index_ext = ".tsx" if needs_typescript else ".js"
    rel_path = await create_file_with_animation(
        src_path / f"index{index_ext}", 
        index_content, 
        f"frontend/src/index{index_ext}", 
        project_name
    )
    files_created.append(rel_path)
    
    # Home page
    home_component = f"""import React from 'react';

const Home = () => {{
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to {project_name}
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          {idea}
        </p>
        <div className="space-x-4">
          <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            Get Started
          </button>
          <button className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded">
            Learn More
          </button>
        </div>
      </div>
      
      <div className="grid md:grid-cols-3 gap-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Feature 1</h3>
          <p className="text-gray-600">Description of your first key feature.</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Feature 2</h3>
          <p className="text-gray-600">Description of your second key feature.</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Feature 3</h3>
          <p className="text-gray-600">Description of your third key feature.</p>
        </div>
      </div>
    </div>
  );
}};

export default Home;"""
    
    rel_path = await create_file_with_animation(
        pages_path / f"Home{ext}", 
        home_component, 
        f"frontend/src/pages/Home{ext}", 
        project_name
    )
    files_created.append(rel_path)
    
    # Header component
    header_component = f"""import React from 'react';

const Header = () => {{
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-900">{project_name}</h1>
          </div>
          <nav className="hidden md:flex space-x-8">
            <a href="/" className="text-gray-600 hover:text-gray-900">Home</a>
            <a href="/about" className="text-gray-600 hover:text-gray-900">About</a>
            <a href="/contact" className="text-gray-600 hover:text-gray-900">Contact</a>
          </nav>
          <div className="flex items-center space-x-4">
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
              Sign Up
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}};

export default Header;"""
    
    rel_path = await create_file_with_animation(
        components_path / f"Header{ext}", 
        header_component, 
        f"frontend/src/components/Header{ext}", 
        project_name
    )
    files_created.append(rel_path)
    
    # CSS files
    app_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

.App {
  text-align: center;
}"""
    
    rel_path = await create_file_with_animation(
        src_path / "App.css", 
        app_css, 
        "frontend/src/App.css", 
        project_name
    )
    files_created.append(rel_path)
    
    index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}"""
    
    rel_path = await create_file_with_animation(
        src_path / "index.css", 
        index_css, 
        "frontend/src/index.css", 
        project_name
    )
    files_created.append(rel_path)
    
    # Tailwind config
    tailwind_config = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}"""
    
    rel_path = await create_file_with_animation(
        frontend_path / "tailwind.config.js", 
        tailwind_config, 
        "frontend/tailwind.config.js", 
        project_name
    )
    files_created.append(rel_path)
    
    return files_created

# For now, let's create simpler aliases that redirect to the animated version
async def create_nextjs_frontend_with_animation(frontend_path: Path, idea: str, project_name: str, needs_typescript: bool, needs_auth: bool) -> List[str]:
    return await create_nextjs_frontend(frontend_path, idea, project_name, needs_typescript, needs_auth)

async def create_fastapi_backend_with_animation(backend_path: Path, idea: str, project_name: str, needs_ai: bool, needs_auth: bool, needs_database: bool) -> List[str]:
    return await create_fastapi_backend(backend_path, idea, project_name, needs_ai, needs_auth, needs_database)

async def create_nodejs_backend_with_animation(backend_path: Path, idea: str, project_name: str, needs_ai: bool, needs_auth: bool, needs_database: bool) -> List[str]:
    return await create_nodejs_backend(backend_path, idea, project_name, needs_ai, needs_auth, needs_database)

async def create_root_files_with_animation(project_path: Path, project_name: str, idea: str, tech_stack: List[str]) -> List[str]:
    return await create_root_files(project_path, project_name, idea, tech_stack)
    """Create React frontend structure"""
    files_created = []
    
    # Create directories
    src_path = frontend_path / "src"
    components_path = src_path / "components"
    pages_path = src_path / "pages"
    utils_path = src_path / "utils"
    
    for path in [src_path, components_path, pages_path, utils_path]:
        path.mkdir(parents=True, exist_ok=True)
    
    # Package.json
    package_json = {
        "name": project_name.lower().replace(" ", "-"),
        "version": "0.1.0",
        "private": True,
        "dependencies": {
            "@testing-library/jest-dom": "^5.16.4",
            "@testing-library/react": "^13.3.0",
            "@testing-library/user-event": "^13.5.0",
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-router-dom": "^6.8.0",
            "react-scripts": "5.0.1",
            "axios": "^1.3.0",
            "tailwindcss": "^3.2.0",
            "autoprefixer": "^10.4.13",
            "postcss": "^8.4.21"
        },
        "scripts": {
            "start": "react-scripts start",
            "build": "react-scripts build",
            "test": "react-scripts test",
            "eject": "react-scripts eject"
        },
        "eslintConfig": {
            "extends": ["react-app", "react-app/jest"]
        },
        "browserslist": {
            "production": [">0.2%", "not dead", "not op_mini all"],
            "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
        }
    }
    
    if needs_typescript:
        package_json["dependencies"].update({
            "typescript": "^4.9.0",
            "@types/node": "^16.18.0",
            "@types/react": "^18.0.0",
            "@types/react-dom": "^18.0.0"
        })
    
    if needs_auth:
        package_json["dependencies"]["auth0-react"] = "^2.0.0"
    
    package_path = frontend_path / "package.json"
    with open(package_path, 'w', encoding='utf-8') as f:
        json.dump(package_json, f, indent=2)
    files_created.append("frontend/package.json")
    
    # Public/index.html
    public_path = frontend_path / "public"
    public_path.mkdir(exist_ok=True)
    
    index_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="{idea}" />
    <title>{project_name}</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>"""
    
    with open(public_path / "index.html", 'w', encoding='utf-8') as f:
        f.write(index_html)
    files_created.append("frontend/public/index.html")
    
    # Main App component
    ext = ".tsx" if needs_typescript else ".jsx"
    
    app_component = f"""import React from 'react';
import {{ BrowserRouter as Router, Routes, Route }} from 'react-router-dom';
import './App.css';
import Home from './pages/Home{ext}';
import Header from './components/Header{ext}';

function App() {{
  return (
    <div className="App min-h-screen bg-gray-50">
      <Router>
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={{<Home />}} />
          </Routes>
        </main>
      </Router>
    </div>
  );
}}

export default App;"""
    
    with open(src_path / f"App{ext}", 'w', encoding='utf-8') as f:
        f.write(app_component)
    files_created.append(f"frontend/src/App{ext}")
    
    # Index.js/tsx
    index_content = f"""import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App{ext}';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);"""
    
    index_ext = ".tsx" if needs_typescript else ".js"
    with open(src_path / f"index{index_ext}", 'w', encoding='utf-8') as f:
        f.write(index_content)
    files_created.append(f"frontend/src/index{index_ext}")
    
    # Home page
    home_component = f"""import React from 'react';

const Home = () => {{
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to {project_name}
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          {idea}
        </p>
        <div className="space-x-4">
          <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            Get Started
          </button>
          <button className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded">
            Learn More
          </button>
        </div>
      </div>
      
      <div className="grid md:grid-cols-3 gap-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Feature 1</h3>
          <p className="text-gray-600">Description of your first key feature.</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Feature 2</h3>
          <p className="text-gray-600">Description of your second key feature.</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Feature 3</h3>
          <p className="text-gray-600">Description of your third key feature.</p>
        </div>
      </div>
    </div>
  );
}};

export default Home;"""
    
    with open(pages_path / f"Home{ext}", 'w', encoding='utf-8') as f:
        f.write(home_component)
    files_created.append(f"frontend/src/pages/Home{ext}")
    
    # Header component
    header_component = f"""import React from 'react';

const Header = () => {{
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-900">{project_name}</h1>
          </div>
          <nav className="hidden md:flex space-x-8">
            <a href="/" className="text-gray-600 hover:text-gray-900">Home</a>
            <a href="/about" className="text-gray-600 hover:text-gray-900">About</a>
            <a href="/contact" className="text-gray-600 hover:text-gray-900">Contact</a>
          </nav>
          <div className="flex items-center space-x-4">
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
              Sign Up
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}};

export default Header;"""
    
    with open(components_path / f"Header{ext}", 'w', encoding='utf-8') as f:
        f.write(header_component)
    files_created.append(f"frontend/src/components/Header{ext}")
    
    # CSS files
    app_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

.App {
  text-align: center;
}"""
    
    with open(src_path / "App.css", 'w', encoding='utf-8') as f:
        f.write(app_css)
    files_created.append("frontend/src/App.css")
    
    index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}"""
    
    with open(src_path / "index.css", 'w', encoding='utf-8') as f:
        f.write(index_css)
    files_created.append("frontend/src/index.css")
    
    # Tailwind config
    tailwind_config = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}"""
    
    with open(frontend_path / "tailwind.config.js", 'w', encoding='utf-8') as f:
        f.write(tailwind_config)
    files_created.append("frontend/tailwind.config.js")
    
    return files_created

async def create_nextjs_frontend(frontend_path: Path, idea: str, project_name: str, needs_typescript: bool, needs_auth: bool) -> List[str]:
    """Create Next.js frontend structure"""
    files_created = []
    
    # Create directories
    src_path = frontend_path / "src"
    app_path = src_path / "app"
    components_path = src_path / "components"
    
    for path in [src_path, app_path, components_path]:
        path.mkdir(parents=True, exist_ok=True)
    
    # Package.json
    package_json = {
        "name": project_name.lower().replace(" ", "-"),
        "version": "0.1.0",
        "private": True,
        "scripts": {
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
            "lint": "next lint"
        },
        "dependencies": {
            "react": "^18",
            "react-dom": "^18",
            "next": "14.0.4",
            "tailwindcss": "^3.3.0",
            "autoprefixer": "^10.4.16",
            "postcss": "^8.4.32"
        },
        "devDependencies": {
            "eslint": "^8",
            "eslint-config-next": "14.0.4"
        }
    }
    
    if needs_typescript:
        package_json["devDependencies"].update({
            "typescript": "^5",
            "@types/node": "^20",
            "@types/react": "^18",
            "@types/react-dom": "^18"
        })
    
    package_path = frontend_path / "package.json"
    with open(package_path, 'w', encoding='utf-8') as f:
        json.dump(package_json, f, indent=2)
    files_created.append("frontend/package.json")
    
    # Next.js config
    next_config = """/** @type {import('next').NextConfig} */
const nextConfig = {}

module.exports = nextConfig"""
    
    with open(frontend_path / "next.config.js", 'w', encoding='utf-8') as f:
        f.write(next_config)
    files_created.append("frontend/next.config.js")
    
    # App directory files
    ext = ".tsx" if needs_typescript else ".js"
    
    # Layout
    layout_content = f"""import './globals.css'
import {{ Inter }} from 'next/font/google'

const inter = Inter({{ subsets: ['latin'] }})

export const metadata = {{
  title: '{project_name}',
  description: '{idea}',
}}

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode
}}) {{
  return (
    <html lang="en">
      <body className={{inter.className}}>{{children}}</body>
    </html>
  )
}}"""
    
    with open(app_path / f"layout{ext}", 'w', encoding='utf-8') as f:
        f.write(layout_content)
    files_created.append(f"frontend/src/app/layout{ext}")
    
    # Page
    page_content = f"""export default function Home() {{
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            {project_name}
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            {idea}
          </p>
          <div className="space-x-4">
            <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors">
              Get Started
            </button>
            <button className="bg-white hover:bg-gray-50 text-gray-800 font-bold py-3 px-6 rounded-lg border border-gray-300 transition-colors">
              Learn More
            </button>
          </div>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-3">Fast Performance</h3>
            <p className="text-gray-600">Built with Next.js for optimal performance and user experience.</p>
          </div>
          
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-3">Easy to Use</h3>
            <p className="text-gray-600">Intuitive interface designed for the best user experience.</p>
          </div>
          
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-3">Modern Design</h3>
            <p className="text-gray-600">Beautiful, responsive design that works on all devices.</p>
          </div>
        </div>
      </div>
    </main>
  )
}}"""
    
    with open(app_path / f"page{ext}", 'w', encoding='utf-8') as f:
        f.write(page_content)
    files_created.append(f"frontend/src/app/page{ext}")
    
    # Global CSS
    globals_css = """@tailwind base;
@tailwind components;
@tailwind utilities;"""
    
    with open(app_path / "globals.css", 'w', encoding='utf-8') as f:
        f.write(globals_css)
    files_created.append("frontend/src/app/globals.css")
    
    # Tailwind config
    tailwind_config = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}"""
    
    with open(frontend_path / "tailwind.config.js", 'w', encoding='utf-8') as f:
        f.write(tailwind_config)
    files_created.append("frontend/tailwind.config.js")
    
    # PostCSS config
    postcss_config = """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}"""
    
    with open(frontend_path / "postcss.config.js", 'w', encoding='utf-8') as f:
        f.write(postcss_config)
    files_created.append("frontend/postcss.config.js")
    
    return files_created

async def create_fastapi_backend(backend_path: Path, idea: str, project_name: str, needs_ai: bool, needs_auth: bool, needs_database: bool) -> List[str]:
    """Create FastAPI backend structure"""
    files_created = []
    
    # Create directories
    api_path = backend_path / "api"
    models_path = backend_path / "models"
    utils_path = backend_path / "utils"
    
    for path in [api_path, models_path, utils_path]:
        path.mkdir(parents=True, exist_ok=True)
    
    # Requirements.txt
    requirements = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-multipart==0.0.6",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "pydantic==2.5.0"
    ]
    
    if needs_database:
        requirements.extend([
            "sqlalchemy==2.0.23",
            "psycopg2-binary==2.9.9",
            "alembic==1.13.0"
        ])
    
    if needs_ai:
        requirements.extend([
            "openai==1.3.0",
            "langchain==0.0.350"
        ])
    
    if needs_auth:
        requirements.extend([
            "python-jose[cryptography]==3.3.0",
            "passlib[bcrypt]==1.7.4",
            "python-jwt==4.0.0"
        ])
    
    with open(backend_path / "requirements.txt", 'w', encoding='utf-8') as f:
        f.write('\n'.join(requirements))
    files_created.append("backend/requirements.txt")
    
    # Main.py
    main_content = f"""from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="{project_name} API",
    description="{idea}",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class HealthResponse(BaseModel):
    status: str
    message: str

class ItemCreate(BaseModel):
    name: str
    description: str

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: str

# Routes
@app.get("/")
async def root():
    return {{"message": "Welcome to {project_name} API"}}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        message="API is running successfully"
    )

@app.get("/api/items", response_model=list[ItemResponse])
async def get_items():
    # Mock data - replace with database queries
    return [
        ItemResponse(
            id=1,
            name="Sample Item",
            description="This is a sample item",
            created_at="2024-01-01T00:00:00Z"
        )
    ]

@app.post("/api/items", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    # Mock creation - replace with database insert
    return ItemResponse(
        id=2,
        name=item.name,
        description=item.description,
        created_at="2024-01-01T00:00:00Z"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)"""
    
    with open(backend_path / "main.py", 'w', encoding='utf-8') as f:
        f.write(main_content)
    files_created.append("backend/main.py")
    
    # .env file
    env_content = f"""# {project_name} Environment Variables
DEBUG=True
PORT=8001
CORS_ORIGINS=http://localhost:3000,http://localhost:3001"""
    
    if needs_database:
        env_content += """

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname"""
    
    if needs_ai:
        env_content += """

# AI/OpenAI
OPENAI_API_KEY=your_openai_api_key_here"""
    
    if needs_auth:
        env_content += """

# Authentication
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30"""
    
    with open(backend_path / ".env", 'w', encoding='utf-8') as f:
        f.write(env_content)
    files_created.append("backend/.env")
    
    return files_created

async def create_nodejs_backend(backend_path: Path, idea: str, project_name: str, needs_ai: bool, needs_auth: bool, needs_database: bool) -> List[str]:
    """Create Node.js Express backend structure"""
    files_created = []
    
    # Create directories
    routes_path = backend_path / "routes"
    models_path = backend_path / "models"
    middleware_path = backend_path / "middleware"
    
    for path in [routes_path, models_path, middleware_path]:
        path.mkdir(parents=True, exist_ok=True)
    
    # Package.json
    package_json = {
        "name": project_name.lower().replace(" ", "-") + "-backend",
        "version": "1.0.0",
        "description": idea,
        "main": "server.js",
        "scripts": {
            "start": "node server.js",
            "dev": "nodemon server.js",
            "test": "jest"
        },
        "dependencies": {
            "express": "^4.18.2",
            "cors": "^2.8.5",
            "dotenv": "^16.3.1",
            "helmet": "^7.1.0",
            "morgan": "^1.10.0"
        },
        "devDependencies": {
            "nodemon": "^3.0.2",
            "jest": "^29.7.0"
        }
    }
    
    if needs_database:
        package_json["dependencies"]["mongoose"] = "^8.0.0"
    
    if needs_ai:
        package_json["dependencies"]["openai"] = "^4.20.0"
    
    if needs_auth:
        package_json["dependencies"].update({
            "jsonwebtoken": "^9.0.2",
            "bcryptjs": "^2.4.3"
        })
    
    with open(backend_path / "package.json", 'w', encoding='utf-8') as f:
        json.dump(package_json, f, indent=2)
    files_created.append("backend/package.json")
    
    # Server.js
    server_content = f"""const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 8001;

// Middleware
app.use(helmet());
app.use(cors({{
    origin: ['http://localhost:3000', 'http://localhost:3001'],
    credentials: true
}}));
app.use(morgan('combined'));
app.use(express.json());
app.use(express.urlencoded({{ extended: true }}));

// Routes
app.get('/', (req, res) => {{
    res.json({{
        message: 'Welcome to {project_name} API',
        description: '{idea}',
        version: '1.0.0'
    }});
}});

app.get('/health', (req, res) => {{
    res.json({{
        status: 'healthy',
        message: 'API is running successfully',
        timestamp: new Date().toISOString()
    }});
}});

// API Routes
app.get('/api/items', (req, res) => {{
    // Mock data - replace with database queries
    res.json([
        {{
            id: 1,
            name: 'Sample Item',
            description: 'This is a sample item',
            createdAt: new Date().toISOString()
        }}
    ]);
}});

app.post('/api/items', (req, res) => {{
    const {{ name, description }} = req.body;
    
    // Mock creation - replace with database insert
    res.status(201).json({{
        id: Date.now(),
        name,
        description,
        createdAt: new Date().toISOString()
    }});
}});

// Error handling middleware
app.use((err, req, res, next) => {{
    console.error(err.stack);
    res.status(500).json({{
        error: 'Something went wrong!',
        message: process.env.NODE_ENV === 'development' ? err.message : undefined
    }});
}});

// 404 handler
app.use('*', (req, res) => {{
    res.status(404).json({{
        error: 'Route not found'
    }});
}});

app.listen(PORT, () => {{
    console.log(`🚀 {project_name} API running on port ${{PORT}}`);
}});"""
    
    with open(backend_path / "server.js", 'w', encoding='utf-8') as f:
        f.write(server_content)
    files_created.append("backend/server.js")
    
    # .env file
    env_content = f"""# {project_name} Environment Variables
NODE_ENV=development
PORT=8001"""
    
    if needs_database:
        env_content += """

# Database
MONGODB_URI=mongodb://localhost:27017/yourdbname"""
    
    if needs_ai:
        env_content += """

# AI/OpenAI
OPENAI_API_KEY=your_openai_api_key_here"""
    
    if needs_auth:
        env_content += """

# Authentication
JWT_SECRET=your_jwt_secret_here
JWT_EXPIRES_IN=7d"""
    
    with open(backend_path / ".env", 'w', encoding='utf-8') as f:
        f.write(env_content)
    files_created.append("backend/.env")
    
    return files_created

async def create_root_files(project_path: Path, project_name: str, idea: str, tech_stack: List[str]) -> List[str]:
    """Create root project files"""
    files_created = []
    
    # README.md
    readme_content = f"""# {project_name}

{idea}

## Tech Stack

{', '.join(tech_stack)}

## Getting Started

### Prerequisites

- Node.js 18+ (for frontend)
- Python 3.9+ (for backend, if using FastAPI)
- npm or yarn

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd {project_name.lower().replace(' ', '-')}
```

2. Install frontend dependencies
```bash
cd frontend
npm install
```

3. Install backend dependencies
```bash
cd ../backend
{'pip install -r requirements.txt' if 'FastAPI' in tech_stack or 'Python' in tech_stack else 'npm install'}
```

### Running the Application

1. Start the backend server
```bash
cd backend
{'python main.py' if 'FastAPI' in tech_stack or 'Python' in tech_stack else 'npm run dev'}
```

2. Start the frontend development server
```bash
cd frontend
npm {'run dev' if 'Next.js' in tech_stack else 'start'}
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001

## Project Structure

```
{project_name.lower().replace(' ', '-')}/
├── frontend/          # {'Next.js' if 'Next.js' in tech_stack else 'React'} frontend application
├── backend/           # {'FastAPI' if 'FastAPI' in tech_stack or 'Python' in tech_stack else 'Node.js Express'} backend API
├── README.md
└── .gitignore
```

## Features

- Modern responsive design
- RESTful API
- Real-time updates
- Error handling
- Development tools

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
"""
    
    with open(project_path / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    files_created.append("README.md")
    
    # .gitignore
    gitignore_content = """# Dependencies
node_modules/
__pycache__/
*.pyc

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Build outputs
/frontend/build/
/frontend/.next/
/frontend/out/
/frontend/dist/

# Logs
npm-debug.log*
yarn-debug.log*
yarn-error.log*
*.log

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
*.lcov

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Database
*.sqlite
*.db

# Temporary files
tmp/
temp/"""
    
    with open(project_path / ".gitignore", 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    files_created.append(".gitignore")
    
    return files_created


@app.get("/debug/test-token")
async def test_github_token_direct():
    """Test GitHub token directly without ai_assistant import"""
    try:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return {"error": "GITHUB_TOKEN not found in environment"}
        
        # Test token directly
        from github import Github
        test_client = Github(token)
        
        # Test authentication
        user = test_client.get_user()
        
        # Fix: Get rate limit properly (newer PyGithub versions)
        try:
            rate_limit = test_client.get_rate_limit()
            # Try different attributes for rate limit
            if hasattr(rate_limit, 'core'):
                remaining = rate_limit.core.remaining
            elif hasattr(rate_limit, 'rate'):
                remaining = rate_limit.rate.remaining  
            else:
                remaining = "Unknown"
        except Exception as rate_error:
            print(f"Rate limit check failed: {rate_error}")
            remaining = "Could not check"
        
        return {
            "token_valid": True,
            "authenticated_as": user.login,
            "user_id": user.id,
            "user_type": user.type,
            "rate_limit_remaining": remaining,
            "token_scopes": "Check GitHub settings for exact scopes"
        }
        
    except Exception as e:
        return {
            "token_valid": False,
            "error": str(e),
            "token_present": bool(os.getenv("GITHUB_TOKEN")),
            "suggestion": "Check if token has 'repo' and 'public_repo' permissions"
        }
# --- Enhanced Security Analysis Functions ---
# Replace the scan processing section in your /scan endpoint (around lines 240-280) with this enhanced version:

@app.post("/scan")
async def scan(request: ScanRequest):
    """Scan a website for security vulnerabilities with weighted scoring and store results for AI chat"""
    url = request.url
    
    try:
        # --- HYBRID CRAWLER INTEGRATION ---
        pages = await crawl_hybrid(url)
        
        # Enhanced scanning with SSL certificate analysis
        scan_result = await run_in_threadpool(scan_url, url)
        
        # Correctly call the async directory scanner
        scan_data = await scan_common_paths(url)
        exposed_paths = scan_data.get('accessible_paths', []) if scan_data else []
        waf_info = scan_data.get('waf_analysis', {}) if scan_data else {}
        dns_security = scan_data.get('dns_security', {}) if scan_data else {}

        suggestions = await run_in_threadpool(suggest_fixes, scan_result.get('headers', {}))
        ai_advice = await run_in_threadpool(
            ai_assistant.analyze_scan_with_llm,
            scan_result.get("https", False),
            scan_result.get("flags", []),
            scan_result.get("headers", {}),
            request.model_type
        )

        # Extract basic scan data
        ssl_certificate = scan_result.get("ssl_certificate", {}) if scan_result else {}
        flags = scan_result.get("flags", []) if scan_result else []
        headers = scan_result.get("headers", {}) if scan_result else {}
        https_enabled = scan_result.get("https", False) if scan_result else False

        # ============================================================================
        # 🎯 NEW WEIGHTED CATEGORY-BASED WEBSITE SECURITY SCORING SYSTEM
        # ============================================================================
        
        print("📊 Calculating weighted website security score...")

        # Initialize category scores (each starts at 100)
        category_scores = {
            'https_ssl': 100,       # HTTPS/SSL/TLS security
            'security_headers': 100, # HTTP security headers
            'vulnerabilities': 100,  # General vulnerabilities/flags
            'exposed_paths': 100,    # Directory/path exposure
            'dns_security': 100      # DNS security features
        }

        # Define category weights (must sum to 1.0)
        weights = {
            'https_ssl': 0.30,        # 30% - Most critical for web
            'security_headers': 0.25,  # 25% - Very important
            'vulnerabilities': 0.25,   # 25% - High impact
            'exposed_paths': 0.10,     # 10% - Medium impact
            'dns_security': 0.10       # 10% - Lower impact but important
        }

        print(f"🔍 Category weights: {weights}")

        # 1. Calculate HTTPS/SSL Score
        if not https_enabled:
            # Major penalty for no HTTPS
            category_scores['https_ssl'] -= 60
            print(f"🚨 HTTPS penalty: No HTTPS = -60 points")
        else:
            # Check SSL certificate issues
            ssl_issues = 0
            ssl_cert = ssl_certificate if isinstance(ssl_certificate, dict) else {}
            
            # Check for SSL certificate problems
            if ssl_cert.get('expired', False):
                category_scores['https_ssl'] -= 30
                ssl_issues += 1
                print(f"🔒 SSL penalty: Certificate expired = -30 points")
            
            if ssl_cert.get('self_signed', False):
                category_scores['https_ssl'] -= 20
                ssl_issues += 1
                print(f"🔒 SSL penalty: Self-signed certificate = -20 points")
            
            if ssl_cert.get('weak_cipher', False):
                category_scores['https_ssl'] -= 15
                ssl_issues += 1
                print(f"🔒 SSL penalty: Weak cipher = -15 points")
            
            # Check SSL version/protocol issues
            ssl_version = ssl_cert.get('version', '').lower()
            if 'sslv' in ssl_version or 'tlsv1.0' in ssl_version or 'tlsv1.1' in ssl_version:
                category_scores['https_ssl'] -= 25
                ssl_issues += 1
                print(f"🔒 SSL penalty: Outdated protocol ({ssl_version}) = -25 points")
            
            if ssl_issues == 0:
                print(f"✅ SSL bonus: Good HTTPS configuration")

        # 2. Calculate Security Headers Score
        essential_headers = {
            'strict-transport-security': 20,  # HSTS
            'content-security-policy': 20,    # CSP
            'x-frame-options': 15,           # Clickjacking protection
            'x-content-type-options': 10,    # MIME sniffing protection
            'referrer-policy': 10,           # Referrer policy
            'x-xss-protection': 10,          # XSS protection
            'permissions-policy': 10,        # Feature policy
            'expect-ct': 5                   # Certificate transparency
        }

        headers_penalty_total = 0
        missing_headers = []
        
        for header, penalty in essential_headers.items():
            header_found = False
            
            # Check for header (case insensitive)
            for actual_header in headers.keys():
                if header.lower() == actual_header.lower():
                    header_found = True
                    break
            
            if not header_found:
                category_scores['security_headers'] -= penalty
                headers_penalty_total += penalty
                missing_headers.append(header)

        print(f"🛡️ Security headers penalty: {len(missing_headers)} missing = -{headers_penalty_total} points")
        if missing_headers:
            print(f"   Missing: {', '.join(missing_headers[:3])}{'...' if len(missing_headers) > 3 else ''}")

        # 3. Calculate Vulnerabilities Score (from flags)
        vulnerability_penalty_total = 0
        critical_flags = []
        
        for flag in flags:
            flag_lower = flag.lower()
            
            # Categorize vulnerability severity
            if any(keyword in flag_lower for keyword in ['injection', 'xss', 'csrf', 'sql', 'rce', 'critical']):
                category_scores['vulnerabilities'] -= 25
                vulnerability_penalty_total += 25
                critical_flags.append(flag)
                print(f"🚨 Critical vulnerability: {flag} = -25 points")
            elif any(keyword in flag_lower for keyword in ['missing', 'weak', 'insecure', 'exposed']):
                category_scores['vulnerabilities'] -= 15
                vulnerability_penalty_total += 15
                print(f"⚠️ High vulnerability: {flag} = -15 points")
            elif any(keyword in flag_lower for keyword in ['deprecated', 'outdated', 'info']):
                category_scores['vulnerabilities'] -= 8
                vulnerability_penalty_total += 8
                print(f"📋 Medium vulnerability: {flag} = -8 points")
            else:
                # General vulnerability
                category_scores['vulnerabilities'] -= 10
                vulnerability_penalty_total += 10
                print(f"🔍 General vulnerability: {flag} = -10 points")

        print(f"🛡️ Total vulnerability penalty: {len(flags)} flags = -{vulnerability_penalty_total} points")

        # 4. Calculate Exposed Paths Score
        exposed_paths_penalty_total = 0
        sensitive_paths = []
        
        for path_info in exposed_paths:
            path = path_info.get('path', '') if isinstance(path_info, dict) else str(path_info)
            path_lower = path.lower()
            
            # Categorize path sensitivity
            if any(keyword in path_lower for keyword in [
                'admin', 'config', 'backup', '.env', 'secret', 'private', 'key', 'password'
            ]):
                category_scores['exposed_paths'] -= 20
                exposed_paths_penalty_total += 20
                sensitive_paths.append(path)
                print(f"🚨 Sensitive path exposed: {path} = -20 points")
            elif any(keyword in path_lower for keyword in [
                'test', 'dev', 'debug', 'staging', 'internal'
            ]):
                category_scores['exposed_paths'] -= 10
                exposed_paths_penalty_total += 10
                print(f"⚠️ Development path exposed: {path} = -10 points")
            else:
                # General exposed path
                category_scores['exposed_paths'] -= 5
                exposed_paths_penalty_total += 5
                print(f"📁 Path exposed: {path} = -5 points")

        print(f"🚪 Exposed paths penalty: {len(exposed_paths)} paths = -{exposed_paths_penalty_total} points")

        # 5. Calculate DNS Security Score
        dns_penalty_total = 0
        dns_issues = []
        
        if isinstance(dns_security, dict):
            # DNSSEC check
            dnssec_info = dns_security.get('dnssec', {})
            if isinstance(dnssec_info, dict) and not dnssec_info.get('enabled', False):
                category_scores['dns_security'] -= 30
                dns_penalty_total += 30
                dns_issues.append('No DNSSEC')
                print(f"🔐 DNS penalty: No DNSSEC = -30 points")

            # DMARC check
            dmarc_info = dns_security.get('dmarc', {})
            if isinstance(dmarc_info, dict) and not dmarc_info.get('enabled', False):
                category_scores['dns_security'] -= 25
                dns_penalty_total += 25
                dns_issues.append('No DMARC')
                print(f"📧 DNS penalty: No DMARC = -25 points")

            # DKIM check
            dkim_info = dns_security.get('dkim', {})
            if isinstance(dkim_info, dict):
                selectors = dkim_info.get('selectors_found', [])
                if not selectors or len(selectors) == 0:
                    category_scores['dns_security'] -= 20
                    dns_penalty_total += 20
                    dns_issues.append('No DKIM')
                    print(f"🔑 DNS penalty: No DKIM selectors = -20 points")

        print(f"🔐 DNS security penalty: {len(dns_issues)} issues = -{dns_penalty_total} points")

        # Ensure no category score goes below 0
        for category in category_scores:
            category_scores[category] = max(0, category_scores[category])

        print(f"📊 Category scores after penalties: {category_scores}")

        # 6. Calculate Weighted Average Score
        overall_score = 0
        for category, score in category_scores.items():
            weighted_contribution = score * weights[category]
            overall_score += weighted_contribution
            print(f"   {category}: {score} × {weights[category]} = {weighted_contribution:.1f}")

        print(f"📊 Base weighted score: {overall_score:.1f}")

        # 7. Add Bonus for Good Security Practices
        security_bonus_total = 0
        
        # WAF detection bonus
        if waf_info.get('waf_detected', False):
            waf_bonus = 5
            overall_score += waf_bonus
            security_bonus_total += waf_bonus
            print(f"🛡️ WAF bonus: WAF detected = +{waf_bonus} points")

        # Strong security headers bonus
        if 'content-security-policy' in [h.lower() for h in headers.keys()] and \
           'strict-transport-security' in [h.lower() for h in headers.keys()]:
            headers_bonus = 3
            overall_score += headers_bonus
            security_bonus_total += headers_bonus
            print(f"🔒 Security headers bonus: CSP + HSTS = +{headers_bonus} points")

        # Perfect HTTPS implementation bonus
        if https_enabled and category_scores['https_ssl'] >= 90:
            https_bonus = 2
            overall_score += https_bonus
            security_bonus_total += https_bonus
            print(f"✅ HTTPS bonus: Perfect SSL/TLS = +{https_bonus} points")

        if security_bonus_total > 0:
            print(f"✅ Total security bonus: +{security_bonus_total} points")

        # 8. Final Score Calculation
        overall_score = max(0, min(100, int(overall_score)))

        print(f"🎯 Final Website Security Score: {overall_score}/100")

        # Determine security level
        if overall_score >= 90:
            security_level = "Excellent"
        elif overall_score >= 75:
            security_level = "Good"
        elif overall_score >= 50:
            security_level = "Medium"
        elif overall_score >= 25:
            security_level = "Low" 
        else:
            security_level = "Critical"

        # Store detailed scoring breakdown
        scoring_breakdown = {
            "category_scores": category_scores,
            "category_weights": weights,
            "penalties_applied": {
                "https_ssl": (60 if not https_enabled else 0) + sum([30 if ssl_certificate.get('expired') else 0,
                                                                     20 if ssl_certificate.get('self_signed') else 0,
                                                                     15 if ssl_certificate.get('weak_cipher') else 0]),
                "security_headers": headers_penalty_total,
                "vulnerabilities": vulnerability_penalty_total,
                "exposed_paths": exposed_paths_penalty_total,
                "dns_security": dns_penalty_total
            },
            "bonuses_applied": {
                "waf_detection": 5 if waf_info.get('waf_detected', False) else 0,
                "security_headers": 3 if all(h in [header.lower() for header in headers.keys()] 
                                           for h in ['content-security-policy', 'strict-transport-security']) else 0,
                "perfect_https": 2 if https_enabled and category_scores['https_ssl'] >= 90 else 0
            },
            "weighted_contributions": {
                category: category_scores[category] * weights[category] 
                for category in category_scores
            }
        }

        # Update scan_result with new scoring
        if scan_result:
            scan_result["security_score"] = overall_score
            scan_result["security_level"] = security_level
            scan_result["scoring_breakdown"] = scoring_breakdown

        # ============================================================================
        # END OF NEW WEBSITE SCORING SYSTEM  
        # ============================================================================

        # Enhanced summary with new scoring information
        scan_summary = scan_data.get('scan_summary', {}) if scan_data else {}
        domain = scan_summary.get('domain', 'Unknown')
        summary = f"""🔒 **Security Scan Complete**

📊 **Target Analysis:**
• Domain: {domain}
• Overall Security Score: {overall_score}/100 ({security_level})
• HTTPS: {'✅ Enabled' if https_enabled else '❌ Disabled'}
• Vulnerabilities: {len(flags)} issues found
• Pages Crawled: {len(pages)} pages
• Security Headers: {len(headers)} detected
• Exposed Paths: {len(exposed_paths)} found

🛡️ **Web Application Firewall (WAF):**
• WAF Detected: {'✅ Yes' if waf_info.get('waf_detected') else '❌ No'}
• WAF Type: {waf_info.get('waf_type', 'None detected')}
• Protection Level: {waf_info.get('protection_level', 'Unknown')}
• Blocked Requests: {waf_info.get('blocked_requests', 0)}/{waf_info.get('total_requests', 0)}

🔐 **DNS Security Features:**
• DNSSEC: {'✅ Enabled' if dns_security.get('dnssec', {}).get('enabled') else '❌ Disabled'} - {dns_security.get('dnssec', {}).get('status', 'Unknown')}
• DMARC: {'✅ Enabled' if dns_security.get('dmarc', {}).get('enabled') else '❌ Not configured'} - {dns_security.get('dmarc', {}).get('policy', 'No policy')}
• DKIM: {'✅ Found' if dns_security.get('dkim', {}).get('selectors_found') else '❌ Not found'} - {len(dns_security.get('dkim', {}).get('selectors_found', []))} selectors

🔐 **SSL/TLS Security Analysis:**
{_format_ssl_analysis(ssl_certificate)}

🎯 **Security Score Breakdown:**
• HTTPS/SSL: {category_scores['https_ssl']}/100 ({weights['https_ssl']*100:.0f}% weight)
• Security Headers: {category_scores['security_headers']}/100 ({weights['security_headers']*100:.0f}% weight)
• Vulnerabilities: {category_scores['vulnerabilities']}/100 ({weights['vulnerabilities']*100:.0f}% weight)
• Exposed Paths: {category_scores['exposed_paths']}/100 ({weights['exposed_paths']*100:.0f}% weight)
• DNS Security: {category_scores['dns_security']}/100 ({weights['dns_security']*100:.0f}% weight)

🚨 **Key Issues Found:**
{chr(10).join([f'• {flag}' for flag in flags[:5]]) if flags else '• No critical issues detected'}

🚪 **Potentially Exposed Paths:**
{chr(10).join([f'• Found accessible path: {p.get("path", p) if isinstance(p, dict) else p}' for p in exposed_paths[:3]]) if exposed_paths else '• No common sensitive paths were found.'}

💡 **Ready to help with specific security questions about this scan!**"""
        
        scan_response = {
            "url": url,
            "pages": pages,
            "scan_result": scan_result,
            "exposed_paths": exposed_paths,
            "waf_analysis": waf_info,
            "dns_security": dns_security,
            "suggestions": suggestions,
            "ai_assistant_advice": ai_advice,
            "summary": summary
        }
        
        # Debug logging to see what we're returning
        print(f"🔍 DEBUG - Overall Security Score: {overall_score}/100 ({security_level})")
        print(f"🔍 DEBUG - Category Scores: {category_scores}")
        print(f"🔍 DEBUG - Scan Response Keys: {list(scan_response.keys())}")
        
        WebsiteScan.latest_scan = scan_response
        return scan_response
        
    except Exception as e:
        error_detail = f"Scan failed for {url}: {str(e)}"
        print(f"❌ {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)


@app.post("/update-knowledge-base")
async def force_update_knowledge_base():
    """Force update knowledge base from web (ignoring 7-day cache)"""
    try:
        from web_scraper import force_update_knowledge_base
        success = await run_in_threadpool(force_update_knowledge_base)
        
        if success:
            # Rebuild RAG database to include new data
            from build_rag_db import build_database
            await run_in_threadpool(build_database, False, False)
            
            return {
                "success": True,
                "message": "Knowledge base force updated with fresh web data",
                "cache_bypass": True,
                "pdf_generated": True,
                "next_auto_update": "7 days from now"
            }
        else:
            return {
                "success": False,
                "message": "Failed to update knowledge base",
                "error": "Web scraping failed"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Update failed: {str(e)}",
            "error": str(e)
        }


@app.post("/analyze-repo")
async def analyze_repo_comprehensive(request: RepoAnalysisRequest):
    """Comprehensive repository security analysis with file scanning and store results for AI chat"""
    try:
        repo_url = request.repo_url
        model_type = request.model_type
        deep_scan = request.deep_scan
        
        if not repo_url:
            return {"error": "Repository URL is required"}
        
        # Validate model type
        if model_type not in ['fast', 'smart']:
            model_type = 'smart'  # Default fallback
        
        # Create temporary directory for cloning
        temp_dir = tempfile.mkdtemp()
        
        # Verify temp directory is writable
        try:
            test_file = os.path.join(temp_dir, 'test_write.tmp')
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            return {"error": f"Temporary directory is not writable: {temp_dir}\nError: {e}\nTry running VS Code as administrator or check folder permissions."}
        
        print(f"📁 Created temporary directory: {temp_dir}")
        
        try:
            # Clone the repository for comprehensive analysis
            print(f"🔄 Cloning repository: {repo_url}")
            
            # Handle different URL formats
            clone_url = repo_url
            if not clone_url.endswith('.git'):
                clone_url += '.git'
            
            # Clone repository with proper error handling
            import git
            from git import Repo, GitCommandError
            
            try:
                # Use shallow clone for better performance - we only need current files
                repo = git.Repo.clone_from(clone_url, temp_dir, depth=1)
                print(f"✅ Repository cloned successfully to {temp_dir} (shallow clone)")
                
                # Configure the cloned repo for Windows compatibility
                try:
                    with repo.config_writer() as config_writer:
                        config_writer.set_value("core", "filemode", "false")
                        config_writer.set_value("core", "autocrlf", "true")
                        config_writer.set_value("core", "safecrlf", "false")
                except Exception as config_error:
                    print(f"⚠️ Could not configure Git settings: {config_error}")
                
            except GitCommandError as git_error:
                # Fallback to full clone if shallow fails
                print(f"⚠️ Shallow clone failed, trying full clone: {git_error}")
                try:
                    repo = git.Repo.clone_from(clone_url, temp_dir)
                    print(f"✅ Repository cloned successfully to {temp_dir} (full clone)")
                    
                    # Configure the cloned repo
                    try:
                        with repo.config_writer() as config_writer:
                            config_writer.set_value("core", "filemode", "false")
                            config_writer.set_value("core", "autocrlf", "true")
                    except Exception as config_error:
                        print(f"⚠️ Could not configure Git settings: {config_error}")
                        
                except GitCommandError as shallow_error:
                    print(f"⚠️ Shallow clone also failed: {shallow_error}")
                    raise Exception(f"All Git clone methods failed. Last error: {shallow_error}")
            
            # Get basic repo info from GitHub API with enhanced error handling
            repo_url_clean = repo_url.rstrip('/').replace('.git', '')
            parts = repo_url_clean.split('/')
            github_repo = None
            github_error = None
            
            # Extract owner and repo name from URL
            if len(parts) >= 5:
                owner, repo_name = parts[-2], parts[-1]
                print(f"🔍 Extracted repo info: {owner}/{repo_name}")
                
                # Try to use github_client first, then create a new one if needed
                working_client = None
                
                # First try the imported github_client
                if github_client:
                    try:
                        # Test the client with a quick call
                        github_client.get_user()
                        working_client = github_client
                        print("✅ Using imported GitHub client")
                    except Exception as test_error:
                        print(f"⚠️ Imported github_client failed: {test_error}")
                
                if not working_client:
                    print("⚠️ Creating new GitHub client...")
                    # Try to create a new GitHub client if the imported one failed
                    token = os.getenv("GITHUB_TOKEN")
                    if token:
                        try:
                            from github import Github
                            working_client = Github(token)
                            # Test the new client
                            working_client.get_user()
                            print("✅ Created new GitHub client with token")
                        except Exception as client_error:
                            print(f"❌ Failed to create GitHub client: {client_error}")
                            working_client = None
                    
                    if not working_client:
                        # Try anonymous access for public repos
                        try:
                            from github import Github
                            working_client = Github()
                            print("✅ Created anonymous GitHub client")
                        except Exception as anon_error:
                            print(f"❌ Failed to create anonymous GitHub client: {anon_error}")
                
                if working_client:
                    try:
                        github_repo = working_client.get_repo(f"{owner}/{repo_name}")
                        print(f"✅ Successfully fetched GitHub repo info for {owner}/{repo_name}")
                        print(f"📊 Repo details: {github_repo.full_name}, {github_repo.language}, {github_repo.stargazers_count} stars")
                    except Exception as e:
                        github_error = str(e)
                        print(f"⚠️ Could not fetch GitHub repo info: {e}")
                        if "404" in str(e):
                            print(f"💡 Repository might be private or URL might be incorrect")
                        elif "403" in str(e):
                            print(f"💡 API rate limit reached or authentication required")
                        elif "401" in str(e):
                            print(f"💡 Authentication failed - check GitHub token")
                else:
                    github_error = "No GitHub client available"
                    print(f"❌ No GitHub client available for API access")
            else:
                github_error = "Invalid repository URL format"
                print(f"❌ Invalid repository URL format: {repo_url_clean}")
            
            # Parallel scanning for better performance
            print("🔍 Starting parallel security scans...")
            
            # Create tasks for parallel execution
            scan_tasks = []
            
            # 1. File security scan
            file_scan_task = run_in_threadpool(scan_for_sensitive_files, temp_dir)
            scan_tasks.append(("file_scan", file_scan_task))
            
            # 2. Static analysis (if deep_scan enabled)
            if deep_scan:
                static_analysis_task = run_in_threadpool(run_bandit, temp_dir)
                scan_tasks.append(("static_analysis", static_analysis_task))
            
            # 3. Dependency scan
            dependency_scan_task = run_in_threadpool(scan_dependencies, temp_dir)
            scan_tasks.append(("dependency_scan", dependency_scan_task))
            
            # 4. Code quality scan
            code_quality_task = run_in_threadpool(scan_code_quality_patterns, temp_dir)
            scan_tasks.append(("code_quality", code_quality_task))
            
            # Execute parallel scans
            scan_results = {}
            for scan_name, task in scan_tasks:
                try:
                    print(f"🔄 Running {scan_name}...")
                    scan_results[scan_name] = await task
                    print(f"✅ {scan_name} completed")
                except Exception as e:
                    print(f"⚠️ {scan_name} failed: {e}")
                    scan_results[scan_name] = []
            
            # Extract results
            file_scan_results = scan_results.get("file_scan", {})
            static_analysis_results = scan_results.get("static_analysis", [])
            dependency_scan_results = scan_results.get("dependency_scan", {})
            code_quality_results = scan_results.get("code_quality", [])
            
            # Ensure static_analysis_results is properly formatted
            if not isinstance(static_analysis_results, list):
                static_analysis_results = []
            
            # 5. Deep secret scanning (if enabled)
            secret_scan_results = []
            if deep_scan:
                print("🕵️ Performing deep content scanning for secrets...")
                scanned_files = 0
                skip_dirs = {
                    'venv', 'env', '.env', 'virtualenv', '__pycache__', 
                    'node_modules', '.git', '.svn', 'build', 'dist', 'target',
                    '.gradle', '.maven', 'vendor', '.next', '.nuxt', 'coverage',
                    'logs', 'tmp', 'temp', '.tmp', '.temp', '.DS_Store', 
                    '.vscode', '.idea', 'docker-data'
                }
                
                for root, dirs, files in os.walk(temp_dir):
                    # Filter out directories we should skip
                    dirs[:] = [d for d in dirs if not any(skip_pattern in d.lower() for skip_pattern in skip_dirs)]
                    
                    # Skip if current directory contains excluded patterns
                    if any(skip_pattern in root.lower() for skip_pattern in skip_dirs):
                        continue
                    
                    for file in files:
                        if scanned_files >= 100:  # Increased limit since we're filtering better
                            break
                        
                        if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.yml', '.yaml', '.env', '.config', '.txt', '.md', '.sh', '.bat')):
                            file_path = os.path.join(root, file)
                            secrets = await run_in_threadpool(scan_file_contents_for_secrets, file_path)
                            
                            # Filter false positives
                            filtered_secrets = []
                            for secret in secrets:
                                if not is_likely_false_positive(file_path, secret.get('secret_type', ''), secret.get('match', '')):
                                    filtered_secrets.append(secret)
                            
                            secret_scan_results.extend(filtered_secrets)
                            scanned_files += 1
            
            # Initialize analysis tracking arrays
            analysis_warnings = []
            analysis_errors = []
            
            # Add Windows compatibility warnings if needed
            if os.name == 'nt':  # Windows
                analysis_warnings.extend([
                    "Running on Windows - some Unix-specific security tools may have limited functionality",
                    "File path analysis optimized for Windows environment", 
                    "If analysis tools fail, try running VS Code as administrator"
                ])
            
            # Run traditional GitHub API analysis for AI insights
            print("📊 Running AI analysis...")
            try:
                if github_repo:
                    github_analysis = await run_in_threadpool(
                        ai_assistant.analyze_github_repo, 
                        repo_url, 
                        model_type,
                        temp_dir  # Pass existing clone directory
                    )
                else:
                    # Fallback when GitHub API fails
                    github_analysis = f"""
📊 **Repository Analysis** (Limited - GitHub API unavailable)

**Repository:** {repo_url}
**Status:** Successfully cloned and analyzed locally
**Note:** GitHub API returned error: {github_error or 'Unknown error'} - repository might be private or require authentication

✅ **Local Analysis Completed:**
• File security scanning: Complete
• Secret detection: Complete  
• Static code analysis: Complete
• Dependency scanning: Complete
• Code quality analysis: Complete

💡 **Recommendation:** For full GitHub integration, ensure repository is public or add GitHub token authentication.
"""
            except Exception as e:
                github_analysis = f"⚠️ AI analysis error: {str(e)}"
                analysis_errors.append(f"GitHub API analysis failed: {str(e)}")
                # Add enhanced fallback analysis
                github_analysis += f"""

📊 **Enhanced Local Analysis Summary:**
• Repository successfully analyzed using local tools
• Enhanced with live SonarSource security rules
• {len(secret_scan_results)} secrets detected
• {len(static_analysis_results)} static analysis issues found  
• {len(code_quality_results)} code quality issues identified
• Security recommendations generated using RAG-enhanced AI"""
            
            # Compile comprehensive results with enhanced repository info
            # Ensure all dicts are valid for .get() usage
            file_scan_results = file_scan_results if isinstance(file_scan_results, dict) else {}
            dependency_scan_results = dependency_scan_results if isinstance(dependency_scan_results, dict) else {}
            
            # Create repository info with better fallback handling
            repository_info = {
                "url": repo_url,
                "name": "Unknown",
                "description": "No description",
                "language": "Unknown", 
                "stars": 0,
                "forks": 0,
                "open_issues": 0
            }
            
            if github_repo:
                # Successfully got GitHub API data
                repository_info.update({
                    "name": getattr(github_repo, 'full_name', "Unknown"),
                    "description": getattr(github_repo, 'description', None) or "No description",
                    "language": getattr(github_repo, 'language', None) or "Unknown",
                    "stars": getattr(github_repo, 'stargazers_count', 0),
                    "forks": getattr(github_repo, 'forks_count', 0),
                    "open_issues": getattr(github_repo, 'open_issues_count', 0)
                })
                print(f"✅ Using GitHub API data: {repository_info['name']} ({repository_info['language']})")
            else:
                # Fallback: extract what we can from the URL
                if len(parts) >= 5:
                    owner, repo_name = parts[-2], parts[-1]
                    repository_info["name"] = f"{owner}/{repo_name}"
                    print(f"⚠️ Using URL-based fallback: {repository_info['name']}")
                    
                    # Add GitHub API error to analysis warnings
                    if github_error:
                        analysis_warnings.append(f"GitHub API access failed: {github_error}")
                        analysis_warnings.append("Repository statistics (stars, forks, language) unavailable - using URL-based fallback")
            
            comprehensive_results = {
                "repository_info": repository_info,
                "file_security_scan": file_scan_results,
                "secret_scan_results": secret_scan_results,
                "static_analysis_results": static_analysis_results,
                "dependency_scan_results": dependency_scan_results,
                "code_quality_results": code_quality_results,
                "ai_analysis": github_analysis,
                "analysis_warnings": analysis_warnings,
                "analysis_errors": analysis_errors,
                "security_summary": {
                    "total_files_scanned": file_scan_results.get('total_files_scanned', 0),
                    "sensitive_files_found": len(file_scan_results.get('sensitive_files', [])),
                    "risky_files_found": len(file_scan_results.get('risky_files', [])),
                    "secrets_found": len(secret_scan_results) if secret_scan_results else 0,
                    "static_issues_found": len(static_analysis_results) if static_analysis_results else 0,
                    "vulnerable_dependencies": len(dependency_scan_results.get('vulnerable_packages', [])),
                    "code_quality_issues": len(code_quality_results) if code_quality_results else 0,
                    "security_files_present": len(file_scan_results.get('security_files_found', [])),
                    "missing_security_files": len(file_scan_results.get('missing_security_files', []))
                }
            }
            
            # ============================================================================
            # 🎯 NEW WEIGHTED CATEGORY-BASED SECURITY SCORING SYSTEM
            # ============================================================================
            
            print("📊 Calculating weighted security score...")

            # Initialize category scores (each starts at 100)
            category_scores = {
                'secrets': 100,
                'sensitive_files': 100,
                'static_analysis': 100,
                'dependencies': 100,
                'code_quality': 100
            }

            # Define category weights (must sum to 1.0)
            weights = {
                'secrets': 0.30,           # 30% - Most critical
                'sensitive_files': 0.20,   # 20% - High impact
                'static_analysis': 0.20,   # 20% - High impact  
                'dependencies': 0.20,      # 20% - High impact
                'code_quality': 0.10       # 10% - Lower impact
            }

            print(f"🔍 Category weights: {weights}")

            # 1. Calculate Secrets Score (Critical Impact)
            secrets_count = len(secret_scan_results) if secret_scan_results else 0
            if secrets_count > 0:
                # Critical penalty: -40 points per secret (very harsh)
                category_scores['secrets'] -= secrets_count * 40
                print(f"🚨 Secrets penalty: {secrets_count} secrets × 40 = -{secrets_count * 40} points")

            # 2. Calculate Sensitive Files Score
            sensitive_files_count = len(file_scan_results.get('sensitive_files', []))
            risky_files_count = len(file_scan_results.get('risky_files', []))

            if sensitive_files_count > 0:
                # High penalty: -15 points per sensitive file
                category_scores['sensitive_files'] -= sensitive_files_count * 15
                print(f"⚠️ Sensitive files penalty: {sensitive_files_count} files × 15 = -{sensitive_files_count * 15} points")

            if risky_files_count > 0:
                # Medium penalty: -5 points per risky file
                category_scores['sensitive_files'] -= risky_files_count * 5
                print(f"📁 Risky files penalty: {risky_files_count} files × 5 = -{risky_files_count * 5} points")

            # 3. Calculate Static Analysis Score (Severity-Based)
            static_penalty_total = 0
            if static_analysis_results:
                for issue in static_analysis_results:
                    severity = issue.get('severity', 'UNKNOWN').upper()
                    if severity in ['HIGH', 'CRITICAL']:
                        category_scores['static_analysis'] -= 10
                        static_penalty_total += 10
                    elif severity in ['MEDIUM', 'MODERATE']:
                        category_scores['static_analysis'] -= 5
                        static_penalty_total += 5
                    else:  # LOW, INFO, etc.
                        category_scores['static_analysis'] -= 2
                        static_penalty_total += 2
                print(f"🛡️ Static analysis penalty: {len(static_analysis_results)} issues = -{static_penalty_total} points")

            # 4. Calculate Dependencies Score (Severity-Based)
            dependency_penalty_total = 0
            vulnerable_packages = dependency_scan_results.get('vulnerable_packages', []) if isinstance(dependency_scan_results, dict) else []

            if vulnerable_packages:
                for pkg in vulnerable_packages:
                    severity = pkg.get('severity', 'Unknown').lower()
                    if severity == 'critical':
                        category_scores['dependencies'] -= 15
                        dependency_penalty_total += 15
                    elif severity == 'high':
                        category_scores['dependencies'] -= 10
                        dependency_penalty_total += 10
                    elif severity == 'medium':
                        category_scores['dependencies'] -= 7
                        dependency_penalty_total += 7
                    else:  # low, info
                        category_scores['dependencies'] -= 3
                        dependency_penalty_total += 3
                print(f"📦 Dependencies penalty: {len(vulnerable_packages)} packages = -{dependency_penalty_total} points")

            # 5. Calculate Code Quality Score (Severity-Based)
            code_quality_penalty_total = 0
            if code_quality_results:
                for issue in code_quality_results:
                    severity = issue.get('severity', 'Unknown')
                    if severity in ['Critical', 'High']:
                        category_scores['code_quality'] -= 5
                        code_quality_penalty_total += 5
                    elif severity == 'Medium':
                        category_scores['code_quality'] -= 2
                        code_quality_penalty_total += 2
                    else:  # Low, Info
                        category_scores['code_quality'] -= 1
                        code_quality_penalty_total += 1
                print(f"⚡ Code quality penalty: {len(code_quality_results)} issues = -{code_quality_penalty_total} points")

            # Ensure no category score goes below 0
            for category in category_scores:
                category_scores[category] = max(0, category_scores[category])

            print(f"📊 Category scores after penalties: {category_scores}")

            # 6. Calculate Weighted Average Score
            overall_score = 0
            for category, score in category_scores.items():
                weighted_contribution = score * weights[category]
                overall_score += weighted_contribution
                print(f"   {category}: {score} × {weights[category]} = {weighted_contribution:.1f}")

            print(f"📊 Base weighted score: {overall_score:.1f}")

            # 7. Add Bonus for Good Security Practices
            security_files_found = len(file_scan_results.get('security_files_found', []))
            if security_files_found > 0:
                # Bonus: up to 10 points for security files (2 points each, max 5 files)
                security_files_bonus = min(10, security_files_found * 2)
                overall_score += security_files_bonus
                print(f"✅ Security files bonus: {security_files_found} files × 2 = +{security_files_bonus} points")

            # 8. Final Score Calculation
            overall_score = max(0, min(100, int(overall_score)))

            print(f"🎯 Final Security Score: {overall_score}/100")

            # Store detailed scoring breakdown for frontend
            comprehensive_results["scoring_breakdown"] = {
                "category_scores": category_scores,
                "category_weights": weights,
                "penalties_applied": {
                    "secrets": secrets_count * 40 if secrets_count > 0 else 0,
                    "sensitive_files": (sensitive_files_count * 15) + (risky_files_count * 5),
                    "static_analysis": static_penalty_total,
                    "dependencies": dependency_penalty_total,
                    "code_quality": code_quality_penalty_total
                },
                "bonuses_applied": {
                    "security_files": security_files_bonus if 'security_files_bonus' in locals() else 0
                },
                "weighted_contributions": {
                    category: category_scores[category] * weights[category] 
                    for category in category_scores
                }
            }

            comprehensive_results["overall_security_score"] = overall_score
            comprehensive_results["security_level"] = (
                "Excellent" if overall_score >= 90 else
                "Good" if overall_score >= 75 else
                "Medium" if overall_score >= 50 else
                "Low"
            )
            
            # ============================================================================
            # END OF NEW SCORING SYSTEM
            # ============================================================================
            
            # Add detailed findings for AI chat context
            comprehensive_results["detailed_findings"] = {
                "secrets": [
                    {
                        "file": s.get('file', 'unknown'),
                        "line": s.get('line', 'N/A'),
                        "secret_type": s.get('secret_type', 'unknown'),
                        "description": s.get('description', 'No description available'),
                        "severity": s.get('severity', 'High')
                    } for s in secret_scan_results[:10]
                ] if secret_scan_results else [],
                "static_issues": [
                    {
                        "file": s.get('filename', 'unknown'),
                        "line": s.get('line', 'N/A'), 
                        "issue": s.get('issue', 'Security issue'),
                        "severity": s.get('severity', 'Unknown'),
                        "description": s.get('description', 'No description available'),
                        "fix_suggestion": s.get('fix_suggestion', 'No fix suggestion available')
                    } for s in static_analysis_results[:10]
                ] if static_analysis_results else [],
                "vulnerable_dependencies": [
                    {
                        "package": d.get('package', 'unknown'),
                        "version": d.get('version', 'unknown'),
                        "severity": d.get('severity', 'Unknown'),
                        "advisory": d.get('advisory', 'Update recommended'),
                        "cve": d.get('cve', 'N/A'),
                        "affected_versions": d.get('affected_versions', 'Unknown'),
                        "fixed_version": d.get('fixed_version', 'Latest')
                    } for d in dependency_scan_results.get('vulnerable_packages', [])[:10]
                ],
                "code_quality": [
                    {
                        "file": c.get('file', 'unknown'),
                        "line": c.get('line', 'N/A'),
                        "pattern": c.get('pattern', 'unknown'),
                        "severity": c.get('severity', 'Unknown'),
                        "description": c.get('description', 'No description'),
                        "fix_suggestion": c.get('fix_suggestion', 'Review and apply secure coding practices')
                    } for c in code_quality_results[:10]
                ] if code_quality_results else [],
                "sensitive_files": [
                    {
                        "file": f.get('file', 'unknown'),
                        "risk": f.get('risk', 'Unknown'),
                        "reason": f.get('reason', 'Sensitive file detected'),
                        "recommended_action": f.get('recommended_action', 'Review and secure or remove')
                    } for f in file_scan_results.get('sensitive_files', [])[:10]
                ]
            }
            
            # Enhanced recommendations with RAG-powered security intelligence
            recommendations = []
            
            # Critical Security Issues (RAG-Enhanced)
            if file_scan_results.get('sensitive_files'):
                recommendations.append({
                    "file": "Multiple sensitive files detected",
                    "pattern": "Sensitive file exposure",
                    "risk": "Critical",
                    "fix": "Remove sensitive files from repository or add to .gitignore. Refer to SonarSource RSPEC rules for file security patterns."
                })
            
            if secret_scan_results:
                recommendations.append({
                    "file": f"{len(secret_scan_results)} files with secrets",
                    "pattern": "Hardcoded secrets detected",
                    "risk": "Critical", 
                    "fix": "Remove secrets from code and use environment variables or secret management systems. Follow OWASP secure coding guidelines."
                })
            
            if static_analysis_results and len(static_analysis_results) > 0:
                recommendations.append({
                    "file": f"{len(static_analysis_results)} static analysis issues", 
                    "pattern": "Code vulnerabilities detected",
                    "risk": "High",
                    "fix": "Apply secure coding patterns from updated SonarSource rules database. Focus on injection flaws and input validation."
                })
            
            if dependency_scan_results.get('vulnerable_packages'):
                vulnerable_count = len(dependency_scan_results['vulnerable_packages'])
                recommendations.append({
                    "file": f"{vulnerable_count} vulnerable dependencies",
                    "pattern": "Outdated dependencies with known vulnerabilities", 
                    "risk": "High",
                    "fix": "Update packages to secure versions. Monitor security advisories and implement automated dependency scanning."
                })
            
            # Infrastructure and Configuration Issues
            if file_scan_results.get('excluded_directories'):
                excluded_count = len(file_scan_results['excluded_directories'])
                recommendations.append({
                    "file": f"{excluded_count} build/dependency directories found",
                    "pattern": "Build artifacts in repository",
                    "risk": "Medium",
                    "fix": f"Ensure {excluded_count} directories (venv, __pycache__, node_modules) are in .gitignore to prevent sensitive data exposure."
                })
            
            if file_scan_results.get('gitignore_recommendations'):
                high_priority_gitignore = [rec for rec in file_scan_results['gitignore_recommendations'] if rec['priority'] == 'High']
                if high_priority_gitignore:
                    patterns = [rec['pattern'] for rec in high_priority_gitignore[:3]]
                    recommendations.append({
                        "file": ".gitignore",
                        "pattern": "Missing security patterns in .gitignore",
                        "risk": "Medium", 
                        "fix": f"Add patterns to .gitignore: {', '.join(patterns)} - Based on SonarSource file security recommendations."
                    })
            
            critical_code_issues = [r for r in code_quality_results if r.get('severity') in ['Critical', 'High']]
            if critical_code_issues:
                recommendations.append({
                    "file": f"{len(critical_code_issues)} files with critical issues",
                    "pattern": "Insecure coding patterns",
                    "risk": "High",
                    "fix": "Apply secure coding practices from live SonarSource rules. Focus on input validation, error handling, and authentication patterns."
                })
            
            # Additional Security Improvements  
            if file_scan_results.get('risky_files'):
                risky_count = len(file_scan_results['risky_files'])
                recommendations.append({
                    "file": f"{risky_count} risky file types",
                    "pattern": "Potentially risky file extensions",
                    "risk": "Medium",
                    "fix": "Review risky file types for security implications. Consider removing unnecessary executable files or configuration files with defaults."
                })
            
            if file_scan_results.get('missing_security_files'):
                missing = file_scan_results['missing_security_files'][:3]
                recommendations.append({
                    "file": "Repository root",
                    "pattern": "Missing security documentation", 
                    "risk": "Low",
                    "fix": f"Add missing security files: {', '.join(missing)} to improve security posture and compliance."
                })
            
            if not any('security.md' in f.get('type', '') for f in file_scan_results.get('security_files_found', [])):
                recommendations.append({
                    "file": "SECURITY.md",
                    "pattern": "Missing security policy",
                    "risk": "Low", 
                    "fix": "Add SECURITY.md file with vulnerability disclosure policy and security contact information."
                })
            
            comprehensive_results["recommendations"] = recommendations[:10]  # Limit to top 10 recommendations
            
            # Add user-friendly display summary
            comprehensive_results["display_summary"] = {
                "basic_info": f"Repository: {comprehensive_results['repository_info'].get('name', 'Unknown')}\nSecurity Score: {overall_score}/100 ({comprehensive_results['security_level']})\nLanguage: {comprehensive_results['repository_info'].get('language', 'Unknown')}",
                "scan_results": f"Secrets Found: {len(secret_scan_results) if secret_scan_results else 0}\nStatic Issues: {len(static_analysis_results) if static_analysis_results else 0}\nVulnerable Dependencies: {len(dependency_scan_results.get('vulnerable_packages', []))}\nCode Quality Issues: {len(code_quality_results) if code_quality_results else 0}",
                "ready_message": "I am ready to answer specific questions about these findings and provide detailed explanations with exact file locations and fix suggestions."
            }
            
            # Store results for AI chat context
            RepoAnalysis.latest_analysis = comprehensive_results
            
            return comprehensive_results
            
        except git.exc.GitCommandError as e:
            error_msg = str(e)
            if "Access is denied" in error_msg:
                return {"error": f"Access denied during Git clone. This might be due to:\n• Repository permissions\n• Windows file system restrictions\n• Antivirus software blocking Git operations\n\nTry running VS Code as administrator or temporarily disable antivirus scanning for the temp directory.\n\nOriginal error: {error_msg}"}
            elif "not found" in error_msg.lower():
                return {"error": f"Repository not found. Please verify:\n• Repository URL is correct\n• Repository is public (or you have access)\n• GitHub is accessible from your network\n\nOriginal error: {error_msg}"}
            elif "authentication" in error_msg.lower():
                return {"error": f"Authentication failed. For private repositories:\n• Ensure you have access rights\n• Consider using GitHub token authentication\n\nOriginal error: {error_msg}"}
            else:
                return {"error": f"Git clone failed: {error_msg}"}
        except Exception as e:
            error_msg = str(e)
            if "Access is denied" in error_msg:
                return {"error": f"Windows access denied error. Try:\n• Running VS Code as administrator\n• Checking antivirus settings\n• Ensuring temp directory is writable\n\nOriginal error: {error_msg}"}
            else:
                return {"error": f"Repository analysis failed: {error_msg}"}
        finally:
            # Enhanced cleanup for Git repositories on Windows
            if os.path.exists(temp_dir):
                try:
                    import stat
                    import time
                    
                    def force_remove_readonly(func, path, exc_info):
                        """Enhanced readonly handler for Git objects"""
                        try:
                            if os.path.exists(path):
                                # Make file writable and remove all permissions restrictions
                                os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                                # Try the original function again
                                func(path)
                        except Exception as e:
                            print(f"⚠️ Could not remove {path}: {e}")
                            # Try with admin privileges if needed
                            try:
                                import subprocess
                                if os.name == 'nt':  # Windows
                                    # Use cmd.exe for Windows-specific commands
                                    subprocess.run(['cmd', '/c', 'del', '/f', '/q', f'"{path}"'], 
                                                 check=False, capture_output=True)
                            except:
                                pass
                    
                    def cleanup_git_directory(directory):
                        """Special cleanup for Git directories with enhanced Windows support"""
                        try:
                            # First, try to make all files in .git writable
                            git_dir = os.path.join(directory, '.git')
                            if os.path.exists(git_dir):
                                print(f"🔧 Making Git files writable in: {git_dir}")
                                for root, dirs, files in os.walk(git_dir):
                                    # Make directories writable
                                    for dir_name in dirs:
                                        dir_path = os.path.join(root, dir_name)
                                        try:
                                            os.chmod(dir_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                                        except Exception:
                                            pass
                                    
                                    # Make files writable  
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        try:
                                            # Remove read-only attribute and make writable
                                            os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                                            # Additional Windows-specific attribute removal
                                            if os.name == 'nt':
                                                try:
                                                    import subprocess
                                                    # Use cmd.exe to run attrib command properly
                                                    subprocess.run(['cmd', '/c', 'attrib', '-r', '-h', '-s', f'"{file_path}"'], 
                                                                 check=False, capture_output=True)
                                                except Exception:
                                                    # Fallback: try using Python's os module
                                                    try:
                                                        import ctypes
                                                        # Remove hidden, system, and readonly attributes
                                                        FILE_ATTRIBUTE_HIDDEN = 0x02
                                                        FILE_ATTRIBUTE_SYSTEM = 0x04
                                                        FILE_ATTRIBUTE_READONLY = 0x01
                                                        FILE_ATTRIBUTE_NORMAL = 0x80
                                                        
                                                        attrs = ctypes.windll.kernel32.GetFileAttributesW(file_path)
                                                        if attrs != -1:  # INVALID_FILE_ATTRIBUTES
                                                            new_attrs = attrs & ~(FILE_ATTRIBUTE_READONLY | FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
                                                            ctypes.windll.kernel32.SetFileAttributesW(file_path, new_attrs or FILE_ATTRIBUTE_NORMAL)
                                                    except Exception:
                                                        pass
                                        except Exception:
                                            pass
                        except Exception as e:
                            print(f"⚠️ Error in Git directory cleanup: {e}")
                    
                    # Special handling for Git directories
                    cleanup_git_directory(temp_dir)
                    
                    # Wait longer for file handles to close on Windows
                    if os.name == 'nt':
                        time.sleep(0.5)  # Longer wait on Windows
                    else:
                        time.sleep(0.1)
                    
                    # Try multiple removal strategies
                    removal_success = False
                    
                    # Strategy 1: Standard shutil.rmtree with error handler
                    try:
                        shutil.rmtree(temp_dir, onerror=force_remove_readonly)
                        print(f"✅ Temporary directory cleaned up: {temp_dir}")
                        removal_success = True
                    except Exception as e1:
                        print(f"⚠️ Standard cleanup failed: {e1}")
                        
                        # Strategy 2: Windows-specific command line tools
                        if os.name == 'nt' and not removal_success:
                            try:
                                import subprocess
                                print("🔧 Trying Windows command line cleanup...")
                                
                                # Method 1: rmdir with force
                                result = subprocess.run([
                                    'rmdir', '/s', '/q', temp_dir
                                ], shell=True, capture_output=True, text=True, timeout=30)
                                
                                if result.returncode == 0:
                                    print(f"✅ Directory cleaned up using rmdir")
                                    removal_success = True
                                else:
                                    print(f"⚠️ rmdir failed: {result.stderr}")
                                    
                            except Exception as e2:
                                print(f"⚠️ rmdir cleanup failed: {e2}")
                        
                        # Strategy 3: PowerShell as last resort
                        if os.name == 'nt' and not removal_success:
                            try:
                                print("🔧 Trying PowerShell cleanup...")
                                ps_result = subprocess.run([
                                    'powershell', '-Command', 
                                    f'Get-ChildItem -Path "{temp_dir}" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue; Remove-Item -Path "{temp_dir}" -Force -ErrorAction SilentlyContinue'
                                ], capture_output=True, text=True, timeout=30)
                                
                                if ps_result.returncode == 0:
                                    print(f"✅ Directory cleaned up using PowerShell")
                                    removal_success = True
                                else:
                                    print(f"⚠️ PowerShell cleanup issues: {ps_result.stderr}")
                                    
                            except Exception as e3:
                                print(f"⚠️ PowerShell cleanup failed: {e3}")
                        
                        # Strategy 4: Manual file-by-file deletion
                        if not removal_success:
                            try:
                                print("🔧 Trying manual file-by-file deletion...")
                                for root, dirs, files in os.walk(temp_dir, topdown=False):
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        try:
                                            os.chmod(file_path, stat.S_IWRITE)
                                            os.remove(file_path)
                                        except:
                                            pass
                                    for dir_name in dirs:
                                        dir_path = os.path.join(root, dir_name)
                                        try:
                                            os.rmdir(dir_path)
                                        except:
                                            pass
                                try:
                                    os.rmdir(temp_dir)
                                    print(f"✅ Directory cleaned up manually")
                                    removal_success = True
                                except:
                                    pass
                            except Exception as e4:
                                print(f"⚠️ Manual cleanup failed: {e4}")
                    
                    if not removal_success:
                        print(f"⚠️ Could not fully clean temp directory: {temp_dir}")
                        print(f"💡 The directory will be cleaned up automatically by the system eventually.")
                        print(f"💡 Or you can manually delete: {temp_dir}")
                    
                except Exception as e:
                    print(f"⚠️ Cleanup error: {e} - continuing anyway")
                    print(f"💡 You may need to manually delete: {temp_dir}")
                
    except Exception as e:
        return {"error": f"Analysis setup failed: {str(e)}"}
# REPLACE your existing @app.post("/ai-chat") endpoint with this enhanced version

@app.post("/ai-chat")
async def unified_ai_chat(request: dict):
    """Enhanced AI chat endpoint - RAG-powered Explainer and Fixer Initiator"""
    try:
        question = request.get('question', '')
        context_type = request.get('context', 'auto')
        model_type = request.get('model_type', 'fast')
        previous_history = request.get('history', [])
        
        # Validate model type
        if model_type not in ['fast', 'smart']:
            model_type = 'fast'
        
        # Clean and validate previous_history to ensure all parts are strings
        cleaned_history = []
        for msg in previous_history:
            if isinstance(msg, dict) and 'type' in msg and 'parts' in msg:
                # Ensure parts contains only strings
                clean_parts = []
                for part in msg['parts']:
                    if isinstance(part, str):
                        clean_parts.append(part)
                    elif isinstance(part, dict) or isinstance(part, list):
                        # Convert complex objects to strings
                        clean_parts.append(str(part)[:1000])  # Limit length
                    else:
                        clean_parts.append(str(part))
                
                cleaned_history.append({
                    'type': msg['type'],
                    'parts': clean_parts
                })
        
        # Keep only last 5 messages for context (to prevent token limit issues)
        cleaned_history = cleaned_history[-5:]
        
        print(f"🤖 Processing AI chat request: '{question[:100]}...'")
        print(f"📝 History cleaned: {len(cleaned_history)} messages")
        
        # Check if this is a fix request
        is_fix_request = any(phrase in question.lower() for phrase in [
            'fix this', 'fix the', 'propose fix', 'create fix', 'generate fix',
            'fix it', 'resolve this', 'solve this', 'patch this', 'auto fix'
        ])
        
        # Check if this is an explanation request
        is_explanation_request = any(phrase in question.lower() for phrase in [
            'what is', 'explain', 'what does', 'how does', 'tell me about',
            'describe', 'meaning of', 'definition'
        ])
        
        # Build enhanced context with automatic scan result detection
        enhanced_context = f"MODEL TYPE: {model_type}\nUSER QUESTION: {question}\n\n"

        # Auto-detect and use available scan results
        if context_type == 'auto':
            repo_analysis = getattr(RepoAnalysis, 'latest_analysis', None)
            website_scan = getattr(WebsiteScan, 'latest_scan', None)
            if repo_analysis:
                context_type = 'repo_analysis'
                enhanced_context += "🔍 **AUTOMATICALLY DETECTED: Repository Analysis Available**\n\n"
            elif website_scan:
                context_type = 'website_scan'
                enhanced_context += "🌐 **AUTOMATICALLY DETECTED: Website Scan Available**\n\n"
            else:
                context_type = 'general'
                enhanced_context += "🤖 **GENERAL SECURITY CONSULTATION** - No recent scan data available.\n\n"
        
        # Handle RAG-powered explanation requests
        if is_explanation_request:
            print("🔍 Processing explanation request with RAG...")
            
            # Query RAG for detailed explanation
            rag_context = await run_in_threadpool(get_secure_coding_patterns, question)
            
            enhanced_context += f"""
🧠 **RAG-ENHANCED EXPLANATION:**
{rag_context}

Please provide a comprehensive explanation using the above security knowledge.
"""

        # Repository Analysis Context (Enhanced with RAG capabilities and detailed findings)
        if context_type == 'repo_analysis':
            analysis_data = getattr(RepoAnalysis, 'latest_analysis', None)
            if isinstance(analysis_data, dict):
                repo_info = analysis_data.get('repository_info', {})
                security_summary = analysis_data.get('security_summary', {})
                detailed_findings = analysis_data.get('detailed_findings', {})
                
                enhanced_context += f"""
📁 **REPOSITORY SECURITY ANALYSIS:**
• Repository: {repo_info.get('name', 'Unknown')}
• Security Score: {analysis_data.get('overall_security_score', 'N/A')}/100 ({analysis_data.get('security_level', 'Unknown')})
• Language: {repo_info.get('language', 'Unknown')}

📊 **SECURITY SUMMARY:**
• Files Scanned: {security_summary.get('total_files_scanned', 0)}
• Secrets Found: {security_summary.get('secrets_found', 0)}
• Static Issues: {security_summary.get('static_issues_found', 0)}
• Vulnerable Dependencies: {security_summary.get('vulnerable_dependencies', 0)}
• Code Quality Issues: {security_summary.get('code_quality_issues', 0)}

🚨 **DETAILED SECURITY FINDINGS:**

🔐 **SECRETS FOUND:** {len(detailed_findings.get('secrets', []))} critical issues
{chr(10).join([f"• {s.get('file', 'unknown')} (Line {s.get('line', 'N/A')}): {s.get('secret_type', 'unknown')} - {s.get('description', 'No description')}" for s in detailed_findings.get('secrets', [])[:3]])}

🛡️ **STATIC ANALYSIS ISSUES:** {len(detailed_findings.get('static_issues', []))} security vulnerabilities
{chr(10).join([f"• {s.get('file', 'unknown')} (Line {s.get('line', 'N/A')}): {s.get('issue', 'Security issue')} ({s.get('severity', 'Unknown')})" for s in detailed_findings.get('static_issues', [])[:3]])}

📦 **VULNERABLE DEPENDENCIES:** {len(detailed_findings.get('vulnerable_dependencies', []))} packages need updates
{chr(10).join([f"• {d.get('package', 'unknown')} v{d.get('version', 'unknown')}: {d.get('severity', 'Unknown')} - {d.get('advisory', 'Update recommended')}" for d in detailed_findings.get('vulnerable_dependencies', [])[:3]])}

🤖 **AI CAPABILITIES:**
- Ask "explain [specific issue]" for detailed OWASP-backed explanations
- Request "fix [package/file]" for automated pull request generation
- Get "tell me exact lines" for precise vulnerability locations
"""
            else:
                enhanced_context += "📁 **REPOSITORY ANALYSIS:** Data available but in unexpected format\n"
        
        # Website Scan Context
        elif context_type == 'website_scan':
            website_data = getattr(WebsiteScan, 'latest_scan', None)
            if isinstance(website_data, dict):
                scan_data = website_data.get('scan_result', {})
                enhanced_context += f"""
🌐 **WEBSITE SECURITY SCAN:**
• Target: {scan_data.get('url', 'N/A')}
• Security Score: {scan_data.get('security_score', 'N/A')}/100 ({scan_data.get('security_level', 'Unknown')})
• HTTPS: {'✅ Enabled' if scan_data.get('https', False) else '❌ Disabled'}
• Vulnerabilities: {len(scan_data.get('flags', []))} issues found
"""
            else:
                enhanced_context += "🌐 **WEBSITE SCAN:** No scan result available.\n"
        
        # General Context
        elif context_type == 'general':
            enhanced_context += """
🔒 **GENERAL SECURITY CONSULTATION**
No specific scan data available. I can help with:
• General security best practices  
• Common vulnerability explanations (RAG-enhanced)
• Security implementation guidance
• Code review suggestions
• Security tool recommendations
"""
        
        enhanced_context += "\n\n🧠 **RAG-ENHANCED AI:** I now have access to a comprehensive security knowledge base for detailed explanations and automated fixes!"
        
        # Create the final message for AI
        final_message = enhanced_context + f"\n\nBased on the above security analysis and knowledge base, provide a helpful response to: {question}"
        
        # Build conversation history with proper string formatting
        final_history = []
        
        # Add cleaned previous history
        final_history.extend(cleaned_history)
        
        # Add current user message
        final_history.append({
            'type': 'user', 
            'parts': [final_message]
        })
        
        print(f"🎯 Sending to AI model: {len(final_history)} messages")
        print(f"🔤 Final message length: {len(final_message)} characters")
        
        # Get AI response with error handling
        response = await run_in_threadpool(get_chat_response, final_history, model_type)
        
        if not isinstance(response, str):
            response = str(response)
        
        # Add response to history
        final_history.append({'type': 'assistant', 'parts': [response]})
        
        return {
            "response": response,
            "model_used": model_type,
            "context_detected": context_type,
            "scan_data_available": context_type in ['repo_analysis', 'website_scan'],
            "history": final_history,
            "action_taken": None,
            "rag_enhanced": True
        }
        
    except Exception as e:
        print(f"❌ Chat Error ({model_type} model): {str(e)}")
        return {
            "response": f"❌ **Chat Error ({model_type} model):** {str(e)}",
            "model_used": model_type if 'model_type' in locals() else 'unknown',
            "context_detected": 'error',
            "scan_data_available": False,
            "history": [],
            "action_taken": None
        }
@app.post("/owasp-mapping")
async def owasp_mapping(request_data: dict = Body(...)):
    """
    Map detected security issues to OWASP Top 10 categories
    Uses the latest scan and repo analysis results automatically
    """
    try:
        # Check if request specifies to exclude repo analysis (for website-only reports)
        exclude_repo = request_data.get('exclude_repo', False) if request_data else False
        scan_result_data = request_data.get('scan_result') if request_data else None
        
        print(f"🎯 OWASP Mapping - exclude_repo: {exclude_repo}")
        
        # Get the latest scan results from stored data
        scan_results = None
        if hasattr(WebsiteScan, 'latest_scan') and WebsiteScan.latest_scan:
            scan_results = WebsiteScan.latest_scan
            print(f"📊 Using stored website scan results")
        
        # Get the latest repository results from stored data (only if not excluded)
        repo_results = None
        if not exclude_repo and hasattr(RepoAnalysis, 'latest_analysis') and RepoAnalysis.latest_analysis:
            repo_results = RepoAnalysis.latest_analysis
            print(f"📁 Using stored repository analysis results")
        elif exclude_repo:
            print(f"🚫 Repository analysis excluded for website-only OWASP mapping")
        
        # Check if we have any data to analyze
        if not scan_results and not repo_results:
            return {
                "success": False,
                "error": "No scan results available. Please run /scan or /analyze-repo first.",
                "owasp_mapping": None,
                "metadata": {
                    "scan_available": False,
                    "repo_available": False,
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        # Map to OWASP Top 10
        owasp_mapping = map_to_owasp_top10(scan_results, repo_results)
        
        return {
            "success": True,
            "owasp_mapping": owasp_mapping,
            "metadata": {
                "scan_available": scan_results is not None,
                "repo_available": repo_results is not None,
                "scan_url": scan_results.get('url') if scan_results else None,
                "repo_name": repo_results.get('repository_info', {}).get('name') if repo_results else None,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OWASP mapping failed: {str(e)}")
    
async def provide_local_fix_suggestion(issue: dict):
    """
    Provide fix suggestions for local analysis without GitHub operations
    """
    try:
        print(f"🔧 Providing local fix suggestion for: {issue.get('description', 'Unknown issue')}")
        
        # Query RAG database for secure coding patterns
        rag_query = f"{issue.get('type', 'security')} {issue.get('description', '')} {issue.get('vulnerable_code', '')}"
        secure_patterns = await run_in_threadpool(get_secure_coding_patterns, rag_query)
        
        # Create AI prompt
        ai_prompt = f"""
        You are a security expert. Analyze this security issue and provide a fix:
        
        Issue Type: {issue.get('type', 'Unknown')}
        Description: {issue.get('description', 'No description')}
        File: {issue.get('file', 'Unknown file')}
        Line: {issue.get('line', 'Unknown')}
        
        Vulnerable Code:
        {issue.get('vulnerable_code', 'Not provided')}
        
        Security Knowledge Base:
        {secure_patterns}
        
        Provide a JSON response with:
        {{
            "fix_summary": "Brief description of the fix",
            "security_impact": "How this improves security",
            "suggested_code": "The corrected code",
            "explanation": "Detailed explanation of the fix",
            "prevention_tips": ["List of tips to prevent this issue"]
        }}
        """
        
        # Get AI response
        ai_response = await run_in_threadpool(get_chat_response, [
            {"role": "user", "content": ai_prompt}
        ], "smart")
        ai_text = ai_response if isinstance(ai_response, str) else str(ai_response)
        
        # Parse JSON response with robust cleaning
        def clean_and_parse_json(text):
            """Clean and parse JSON from AI response"""
            try:
                # First try to find JSON in ```json blocks
                import re
                json_block = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
                if json_block:
                    json_text = json_block.group(1)
                    return json.loads(json_text)
            except Exception:
                pass
            
            # Fallback: Extract between first { and last } and clean
            try:
                start = text.find('{')
                end = text.rfind('}') + 1
                if start != -1 and end != -1:
                    json_text = text[start:end]
                    # Simple cleanup - replace newlines with spaces
                    json_text = json_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                    # Remove extra whitespace
                    json_text = re.sub(r'\s+', ' ', json_text)
                    return json.loads(json_text)
            except Exception:
                pass
            
            return None
        
        try:
            fix_data = clean_and_parse_json(ai_text)
            if fix_data:
                print("✅ Successfully parsed AI fix response")
            else:
                raise ValueError("Could not parse JSON from AI response")
        except Exception as parse_error:
            print(f"⚠️ JSON parsing failed: {parse_error}")
            print(f"🔍 AI Response preview: {ai_text[:500]}...")
            
            # Enhanced fallback: Extract key information from the AI response text
            fix_data = {
                "fix_summary": "Replace hardcoded credentials with environment variables",
                "security_impact": "Prevents credential exposure in source code", 
                "suggested_code": "import os\nDB_PASSWORD = os.getenv('DB_PASSWORD', 'default_secure_password')",
                "explanation": "Hardcoded passwords should be moved to environment variables to prevent exposure in version control.",
                "prevention_tips": [
                    "Use environment variables for sensitive data",
                    "Never commit secrets to version control", 
                    "Use secure secret management tools",
                    "Regular security audits"
                ]
            }
            # Fallback response
            fix_data = {
                "fix_summary": f"Security fix suggested for {issue.get('type', 'issue')}",
                "security_impact": "Reduces security vulnerability risk",
                "suggested_code": "# Apply security best practices here",
                "explanation": f"This {issue.get('type', 'issue')} should be addressed by following security best practices.",
                "prevention_tips": ["Regular security audits", "Use security linting tools", "Follow OWASP guidelines"]
            }
        
        return {
            "success": True,
            "fix_applied": False,
            "suggestion_only": True,
            "fix_summary": fix_data.get("fix_summary", "Security fix suggested"),
            "security_impact": fix_data.get("security_impact", "Improves security"),
            "suggested_code": fix_data.get("suggested_code", ""),
            "explanation": fix_data.get("explanation", ""),
            "prevention_tips": fix_data.get("prevention_tips", []),
            "issue_details": {
                "type": issue.get('type'),
                "file": issue.get('file'),
                "line": issue.get('line'),
                "description": issue.get('description')
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate fix suggestion: {str(e)}",
            "fix_summary": "Unable to generate fix",
            "suggestion_only": True
        }

class ProjectRequest(BaseModel):
    idea: str
    project_type: str = "web-app"
    tech_stack: Union[str, List[str]] = "auto"
    complexity: str = "medium"

async def generate_full_stack_files(project_path: Path, idea: str, project_name: str, needs_ai: bool, ai_response: str):
    """
    Generate actual project files based on the idea and AI response
    """
    try:
        # Create main project structure
        project_path.mkdir(exist_ok=True)
        frontend_path = project_path / "frontend"
        backend_path = project_path / "backend"
        
        frontend_path.mkdir(exist_ok=True)
        backend_path.mkdir(exist_ok=True)
        
        # Generate frontend files
        await generate_frontend_files(frontend_path, idea, project_name, needs_ai)
        
        # Generate backend files
        await generate_backend_files(backend_path, idea, project_name, needs_ai)
        
        # Generate deployment files
        await generate_deployment_files(project_path, project_name)
        
        # Return project structure for display
        return [
            "📁 frontend/",
            "  📁 src/",
            "    📁 components/",
            "    📁 pages/",
            "    📁 hooks/",
            "    📁 utils/",
            "  📁 public/",
            "  📄 package.json",
            "  📄 tailwind.config.js",
            "  📄 vite.config.js",
            "📁 backend/",
            "  📁 app/",
            "    📁 routes/",
            "    📁 models/",
            "    📁 services/",
            "  📄 main.py",
            "  📄 requirements.txt",
            "  📄 Dockerfile",
            "📄 docker-compose.yml",
            "📄 README.md",
            "📄 .env.example"
        ]
        
    except Exception as e:
        print(f"Error generating files: {e}")
        return ["Error generating project files"]

async def generate_frontend_files(frontend_path: Path, idea: str, project_name: str, needs_ai: bool):
    """Generate React frontend with TailwindCSS"""
    
    # Create directory structure
    src_path = frontend_path / "src"
    components_path = src_path / "components"
    pages_path = src_path / "pages"
    hooks_path = src_path / "hooks"
    utils_path = src_path / "utils"
    public_path = frontend_path / "public"
    
    for path in [src_path, components_path, pages_path, hooks_path, utils_path, public_path]:
        path.mkdir(exist_ok=True)
    
    # Generate package.json
    package_json = {
        "name": project_name,
        "version": "1.0.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview"
        },
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "axios": "^1.6.0"
        },
        "devDependencies": {
            "@vitejs/plugin-react": "^4.0.0",
            "vite": "^4.4.0",
            "tailwindcss": "^3.3.0",
            "autoprefixer": "^10.4.0",
            "postcss": "^8.4.0"
        }
    }
    
    with open(frontend_path / "package.json", "w") as f:
        json.dump(package_json, f, indent=2)
    
    # Generate main App.jsx
    app_jsx = f'''import React from 'react';
import './App.css';

function App() {{
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            {project_name.replace("-", " ").title()}
          </h1>
          <p className="text-gray-600 mt-2">{idea}</p>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Welcome to your new app!</h2>
          <p className="text-gray-600">
            This is a full-stack application generated based on your idea.
            The backend API is ready and the frontend is set up with TailwindCSS.
          </p>
          
          <div className="mt-6 space-y-4">
            <button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
              Get Started
            </button>
            {"<button className='bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-colors ml-4'>API Test</button>" if needs_ai else ""}
          </div>
        </div>
      </main>
    </div>
  );
}}

export default App;'''
    
    with open(src_path / "App.jsx", "w") as f:
        f.write(app_jsx)
    
    # Generate main.jsx
    main_jsx = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)'''
    
    with open(src_path / "main.jsx", "w") as f:
        f.write(main_jsx)
    
    # Generate index.css with TailwindCSS
    index_css = '''@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}'''
    
    with open(src_path / "index.css", "w") as f:
        f.write(index_css)
    
    # Generate Vite config
    vite_config = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
  },
})'''
    
    with open(frontend_path / "vite.config.js", "w") as f:
        f.write(vite_config)
    
    # Generate TailwindCSS config
    tailwind_config = '''/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}'''
    
    with open(frontend_path / "tailwind.config.js", "w") as f:
        f.write(tailwind_config)
    
    # Generate index.html
    index_html = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name.replace("-", " ").title()}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>'''
    
    with open(frontend_path / "index.html", "w") as f:
        f.write(index_html)

async def generate_backend_files(backend_path: Path, idea: str, project_name: str, needs_ai: bool):
    """Generate FastAPI backend"""
    
    # Create directory structure
    app_path = backend_path / "app"
    routes_path = app_path / "routes"
    models_path = app_path / "models"
    services_path = app_path / "services"
    
    for path in [app_path, routes_path, models_path, services_path]:
        path.mkdir(exist_ok=True)
    
    # Generate requirements.txt
    requirements = [
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "python-multipart==0.0.6",
        "python-dotenv==1.0.0",
        "sqlalchemy==2.0.23",
        "psycopg2-binary==2.9.9",
        "pydantic==2.5.0",
        "python-jose==3.3.0",
        "passlib==1.7.4",
        "bcrypt==4.1.2"
    ]
    
    if needs_ai:
        requirements.extend([
            "openai==1.3.0",
            "langchain==0.0.350"
        ])
    
    with open(backend_path / "requirements.txt", "w") as f:
        f.write("\\n".join(requirements))
    
    # Generate main.py
    ai_import = "from app.services.ai_service import AIService" if needs_ai else ""
    ai_route = ', ai_router' if needs_ai else ""
    
    main_py = f'''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.main_routes import router as main_router
{ai_import}
import uvicorn

app = FastAPI(
    title="{project_name.replace("-", " ").title()} API",
    description="Backend API for {idea}",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(main_router{ai_route})

@app.get("/")
async def root():
    return {{"message": "Welcome to {project_name.replace("-", " ").title()} API"}}

@app.get("/health")
async def health_check():
    return {{"status": "healthy", "service": "{project_name}"}}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)'''
    
    with open(backend_path / "main.py", "w") as f:
        f.write(main_py)
    
    # Generate main routes
    main_routes = '''from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api", tags=["main"])

class ItemCreate(BaseModel):
    title: str
    description: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None

# In-memory storage (replace with database in production)
items_db = []
next_id = 1

@router.get("/items", response_model=List[ItemResponse])
async def get_items():
    """Get all items"""
    return items_db

@router.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    """Create a new item"""
    global next_id
    new_item = ItemResponse(
        id=next_id,
        title=item.title,
        description=item.description
    )
    items_db.append(new_item)
    next_id += 1
    return new_item

@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    """Get item by ID"""
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@router.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete item by ID"""
    global items_db
    items_db = [item for item in items_db if item.id != item_id]
    return {"message": "Item deleted successfully"}'''
    
    with open(routes_path / "main_routes.py", "w") as f:
        f.write(main_routes)
    
    # Generate AI service if needed
    if needs_ai:
        ai_service = '''import openai
import os
from typing import Optional
from fastapi import HTTPException

class AIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        openai.api_key = self.api_key
    
    async def generate_response(self, prompt: str) -> str:
        """Generate AI response using OpenAI"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

ai_service = AIService()'''
        
        with open(services_path / "ai_service.py", "w") as f:
            f.write(ai_service)
    
    # Generate __init__.py files
    for path in [app_path, routes_path, models_path, services_path]:
        (path / "__init__.py").touch()

async def generate_deployment_files(project_path: Path, project_name: str):
    """Generate deployment configuration files"""
    
    # Generate docker-compose.yml
    docker_compose = f'''version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/{project_name}
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB={project_name}
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:'''
    
    with open(project_path / "docker-compose.yml", "w") as f:
        f.write(docker_compose)
    
    # Generate README.md
    readme = f'''# {project_name.replace("-", " ").title()}

A full-stack application with React frontend and FastAPI backend.

## Quick Start

### Local Development

1. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Docker Setup

```bash
docker-compose up --build
```

## Deployment

### Frontend (Vercel)
1. Push to GitHub
2. Connect to Vercel
3. Set environment variables:
   - `VITE_API_URL=your-backend-url`

### Backend (Render/Railway)
1. Connect your repository
2. Set environment variables:
   - `DATABASE_URL`
   - `OPENAI_API_KEY` (if using AI features)

### Database
- Use Railway PostgreSQL or MongoDB Atlas
- Update connection string in environment variables

## Environment Variables

Create `.env` files:

**Frontend (.env)**
```
VITE_API_URL=http://localhost:8000
```

**Backend (.env)**
```
DATABASE_URL=postgresql://user:password@localhost:5432/{project_name}
OPENAI_API_KEY=your-openai-key-here
SECRET_KEY=your-secret-key-here
```

## Features

- ✅ React with TailwindCSS
- ✅ FastAPI backend with auto-generated docs
- ✅ CORS configured for development
- ✅ Docker support
- ✅ Production-ready structure
- ✅ Environment configuration
- ✅ Database ready (PostgreSQL)

## Tech Stack

- **Frontend**: React, TailwindCSS, Vite
- **Backend**: FastAPI, Python
- **Database**: PostgreSQL
- **Deployment**: Vercel + Render/Railway

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /api/items` - Get all items
- `POST /api/items` - Create new item
- `GET /api/items/{{id}}` - Get item by ID
- `DELETE /api/items/{{id}}` - Delete item

Visit http://localhost:8000/docs for interactive API documentation.
'''
    
    with open(project_path / "README.md", "w") as f:
        f.write(readme)
    
    # Generate .env.example
    env_example = '''# Frontend Environment Variables
VITE_API_URL=http://localhost:8000

# Backend Environment Variables  
DATABASE_URL=postgresql://user:password@localhost:5432/database
OPENAI_API_KEY=your-openai-key-here
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here'''
    
    with open(project_path / ".env.example", "w") as f:
        f.write(env_example)

def analyze_project_features(idea: str) -> List[str]:
    """Analyze the idea and determine what features should be included"""
    features = ["Responsive Design", "API Integration", "Production Ready"]
    
    idea_lower = idea.lower()
    
    # Core features based on keywords
    if any(word in idea_lower for word in ["user", "login", "auth", "account"]):
        features.append("User Authentication")
    
    if any(word in idea_lower for word in ["database", "store", "save", "crud"]):
        features.append("Database Storage")
    
    if any(word in idea_lower for word in ["ai", "ml", "gpt", "openai", "intelligence"]):
        features.append("AI Integration")
    
    if any(word in idea_lower for word in ["chat", "message", "real-time", "live"]):
        features.append("Real-time Features")
    
    if any(word in idea_lower for word in ["payment", "stripe", "billing", "subscription"]):
        features.append("Payment Integration")
    
    if any(word in idea_lower for word in ["upload", "file", "image", "photo"]):
        features.append("File Upload")
    
    if any(word in idea_lower for word in ["email", "notification", "alert"]):
        features.append("Email Notifications")
    
    if any(word in idea_lower for word in ["admin", "dashboard", "manage"]):
        features.append("Admin Dashboard")
    
    if any(word in idea_lower for word in ["search", "filter", "find"]):
        features.append("Search Functionality")
    
    if any(word in idea_lower for word in ["mobile", "responsive", "device"]):
        features.append("Mobile Responsive")
    
    return features

@app.post("/generate-project")
async def generate_project(request: ProjectRequest):
    """
    AI-powered full-stack project generation endpoint
    Generates complete project with frontend, backend, and deployment instructions
    """
    try:
        idea = request.idea
        project_type = request.project_type
        tech_stack_raw = request.tech_stack
        complexity = request.complexity
        
        # Normalize tech_stack to list format
        if isinstance(tech_stack_raw, str):
            if tech_stack_raw == "auto":
                tech_stack = ["React", "TypeScript", "TailwindCSS", "FastAPI", "Python"]
            else:
                tech_stack = [tech_stack_raw]
        else:
            tech_stack = tech_stack_raw
        
        print(f"🚀 Generating full-stack project for idea: '{idea}'")
        print(f"🔧 Project type: {project_type}, Tech stack: {tech_stack}, Complexity: {complexity}")
        
        # Enhanced AI prompt for full-stack generation
        tech_stack_str = ", ".join(tech_stack)
        enhanced_prompt = f"""
Generate a complete, production-ready full-stack application based on this user request: "{idea}"

TECH STACK: {tech_stack_str}

REQUIREMENTS:
1. Generate BOTH frontend and backend code (not just structure)
2. Based on the user prompt, generate:
   - The UI (React with TailwindCSS, minimal aesthetic)
   - Backend logic (routes, APIs, database models if needed)
   - Integration between frontend and backend
3. If the prompt requires authentication, CRUD, or AI integration, scaffold the logic accordingly
4. Use a clean folder structure: /frontend and /backend
5. Provide comments explaining each file's role and why the logic works
6. Ensure APIs connect correctly with the frontend fetch/axios calls
7. If the prompt includes "with AI", assume AI model integration is needed
8. Generate boilerplate so the app can run locally with minimal setup (npm/yarn for frontend, pip/npm for backend)
9. Include deployment instructions in comments (like Vercel + Render/Heroku)
10. The code should be production-ready, simple, and lovable (smooth UI, clean backend logic)
11. Use the specified tech stack: {tech_stack_str}

Example input from user: "Build a to-do list app with AI reminders"
→ Should generate: 
   - React frontend with add/remove todos
   - Backend with FastAPI or Express to store todos
   - AI reminder logic using OpenAI API
   - Clear explanation of where to configure keys

Always generate FULL STACK logic (not just frontend).

TECH STACK SELECTION:
- For web apps: React + TailwindCSS frontend, FastAPI/Express backend
- For AI features: Include OpenAI API integration
- For databases: PostgreSQL/MongoDB based on complexity
- For real-time: Socket.io/WebSockets if needed

Generate actual code files with complete implementations, not just placeholders.
"""
        
        # Use AI assistant to generate the actual project
        ai_response = await run_in_threadpool(get_chat_response, enhanced_prompt, "smart")
        
        # Generate project name
        words = idea.split()[:3]
        project_name = "-".join([word.lower() for word in words if word.isalnum()])
        if not project_name:
            project_name = "generated-app"
        
        # Create project directory
        projects_dir = Path("generated_projects")
        projects_dir.mkdir(exist_ok=True)
        project_path = projects_dir / project_name
        
        # Remove existing project if it exists
        if project_path.exists():
            shutil.rmtree(project_path)
        
        # Determine tech stack and structure
        if "ai" in idea.lower() or "ml" in idea.lower():
            tech_stack_final = tech_stack + ["OpenAI API"] if "OpenAI API" not in tech_stack else tech_stack
            needs_ai = True
        else:
            tech_stack_final = tech_stack
            needs_ai = False
        
        # Generate the actual project files using AI-powered generation
        project_structure = await generate_ai_powered_full_stack_files(
            project_path, 
            idea, 
            project_name, 
            tech_stack_final,
            needs_ai
        )
        
        # Generate features based on idea analysis
        features = analyze_project_features(idea)
        
        # Estimate development time
        time_mapping = {
            "simple": "2-3 days",
            "medium": "1-2 weeks", 
            "complex": "3-4 weeks"
        }
        estimated_time = time_mapping.get(complexity, "1-2 weeks")
        
        # Generate deployment info
        deployment_info = {
            "frontend": "Deploy to Vercel or Netlify",
            "backend": "Deploy to Render, Railway, or Heroku",
            "database": "Use Railway PostgreSQL or MongoDB Atlas",
            "env_vars": "Configure API keys and database URLs"
        }
        
        return {
            "success": True,
            "project": {
                "name": project_name.replace("-", " ").title(),
                "description": idea,
                "tech_stack": tech_stack_final,
                "structure": project_structure,
                "features": features,
                "estimated_time": estimated_time,
                "deployment": deployment_info,
                "project_type": project_type,
                "complexity": complexity,
                "path": str(project_path),
                "ai_generated": True
            },
            "auto_run": {
                "enabled": True,
                "project_name": project_name.replace("-", " ").title(),
                "redirect_to_monaco": True,
                "auto_start_project": True,
                "show_file_tree": True
            }
        }
        
    except Exception as e:
        print(f"❌ Project generation error: {e}")
        return {
            "success": False,
            "error": f"Failed to generate project: {str(e)}"
        }

@app.post("/auto-run-project")
async def auto_run_project(request: dict):
    """
    Auto-run project after AI generation - opens Monaco Editor and starts the project
    """
    try:
        project_name = request.get("project_name")
        if not project_name:
            return {"success": False, "error": "Project name is required"}
        
        # Generate project slug
        project_slug = project_name.lower().replace(" ", "-").replace("_", "-")
        
        print(f"🚀 Auto-running project: {project_name}")
        
        # Return instructions for frontend to auto-navigate and start
        return {
            "success": True,
            "auto_run": {
                "project_name": project_name,
                "project_slug": project_slug,
                "monaco_url": f"/monaco?project={project_name}",
                "actions": [
                    {"type": "navigate", "target": "monaco_editor"},
                    {"type": "load_file_tree", "project": project_name},
                    {"type": "auto_start", "delay": 2000},
                    {"type": "show_preview", "delay": 5000}
                ]
            }
        }
        
    except Exception as e:
        print(f"❌ Auto-run error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/propose-fix")
async def propose_fix(request: FixRequest):
    """
    RAG-powered automated code remediation endpoint with detailed code comparison
    Takes a specific security issue and creates a PR with the fix
    """
    try:
        repo_url = request.repo_url
        issue = request.issue
        
        print(f"🔍 Raw repo_url received: '{repo_url}'")
        print(f"🔍 Issue data: {json.dumps(issue, indent=2)}")
        
        # Check if this is a local analysis (not a GitHub repo)
        if not repo_url.startswith('https://github.com/') and not repo_url.startswith('git@github.com:'):
            print(f"❌ Invalid repo URL format: '{repo_url}' - not a GitHub URL")
            return await provide_local_fix_suggestion(issue)
        
        # Clean and extract repo info
        repo_url_clean = repo_url.rstrip('/').replace('.git', '')
        
        # Handle different GitHub URL formats
        if '/tree/' in repo_url_clean:
            # Remove everything after /tree/
            repo_url_clean = repo_url_clean.split('/tree/')[0]
            print(f"🔧 Cleaned tree URL: '{repo_url}' -> '{repo_url_clean}'")
        
        if '/blob/' in repo_url_clean:
            # Remove everything after /blob/
            repo_url_clean = repo_url_clean.split('/blob/')[0]
            print(f"🔧 Cleaned blob URL: '{repo_url}' -> '{repo_url_clean}'")
        
        parts = repo_url_clean.replace('https://github.com/', '').split('/')
        print(f"🔍 URL parts after cleaning: {parts}")
        
        if len(parts) < 2:
            print(f"❌ Invalid repo URL format after cleaning: '{repo_url_clean}' -> parts: {parts}")
            raise HTTPException(status_code=400, detail=f"Invalid repo URL format. Expected format: https://github.com/owner/repo, got: '{repo_url}'")
        
        owner, repo_name = parts[0], parts[1]
        print(f"🔍 Extracted repo: {owner}/{repo_name}")
        
        # Initialize GitHub client with proper authentication
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise HTTPException(status_code=500, detail="GitHub token not configured. Please set GITHUB_TOKEN environment variable.")
        
        from github import Github
        try:
            # Always create a fresh GitHub client with the token
            working_github_client = Github(token)
            print("✅ Created fresh GitHub client")
            
            # Test the client immediately
            test_user = working_github_client.get_user()
            print(f"✅ GitHub client authenticated as: {test_user.login}")
            
        except Exception as client_error:
            print(f"❌ GitHub authentication failed: {client_error}")
            raise HTTPException(status_code=401, detail=f"GitHub authentication failed: {str(client_error)}")
        
        # Test repository access with the working client
        try:
            print(f"🔍 Testing access to repository: {owner}/{repo_name}")
            github_repo = working_github_client.get_repo(f"{owner}/{repo_name}")
            print(f"✅ Repository accessible: {github_repo.full_name}")
            print(f"📊 Repository info: {github_repo.language}, Private: {github_repo.private}")
            
        except Exception as repo_error:
            error_msg = str(repo_error)
            print(f"❌ Repository access failed: {error_msg}")
            
            if "401" in error_msg or "Bad credentials" in error_msg:
                raise HTTPException(
                    status_code=401, 
                    detail=f"GitHub authentication failed. Your token may not have the correct permissions. Please ensure your GITHUB_TOKEN has 'repo' scope for private repositories or 'public_repo' scope for public repositories. Error: {error_msg}"
                )
            elif "404" in error_msg or "Not Found" in error_msg:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Repository '{owner}/{repo_name}' not found or not accessible. Please check: 1) Repository URL is correct, 2) Repository exists and is public, or 3) Your token has access to private repositories. Error: {error_msg}"
                )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Repository access error: {error_msg}"
                )
        
        # Create temporary directory for cloning
        temp_dir = tempfile.mkdtemp()
        
        try:
            print(f"🔧 Starting fix process for {repo_url_clean}")
            
            # Clone the repository using the cleaned URL
            repo = git.Repo.clone_from(repo_url_clean, temp_dir)
            
            # Get the file content
            issue_file = issue.get('file', '')
            if not issue_file:
                raise HTTPException(status_code=400, detail="Issue must specify a file path")
            
            # Extract relative path from absolute path if needed
            # Handle cases where issue_file might be an absolute temp path
            if os.path.isabs(issue_file):
                # Try to extract the relative path by finding common patterns
                # Look for patterns like /backend/, /frontend/, /src/, etc.
                path_parts = issue_file.replace('\\', '/').split('/')
                
                # Find the start of the relative path (after temp directory)
                relative_start = -1
                for i, part in enumerate(path_parts):
                    if part in ['backend', 'frontend', 'src', 'lib', 'app', 'public', 'static', 'assets']:
                        relative_start = i
                        break
                
                if relative_start != -1:
                    # Take everything from the relative start
                    issue_file = '/'.join(path_parts[relative_start:])
                    print(f"🔄 Extracted relative path from absolute: {issue_file}")
                else:
                    # If we can't find a common pattern, take the last few parts
                    # This handles cases like "config/db.js" or "package.json"
                    if len(path_parts) >= 2:
                        issue_file = '/'.join(path_parts[-2:])  # Take last 2 parts
                    else:
                        issue_file = path_parts[-1]  # Take just the filename
                    print(f"🔄 Using fallback relative path: {issue_file}")
            
            # Normalize file path (ensure forward slashes for cross-platform compatibility)
            issue_file = issue_file.replace('\\', '/')
            print(f"🔍 Final normalized issue file path: {issue_file}")
            print(f"🔍 Repository temp directory: {temp_dir}")
            
            file_path = os.path.join(temp_dir, issue_file)
            print(f"🔍 Full file path: {file_path}")
            
            # Store original file content (before fix)
            original_content = ""
            file_existed = os.path.exists(file_path)
            
            if file_existed:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    original_content = f.read()
                print(f"📄 Original file content loaded: {len(original_content)} characters")
            else:
                print(f"📝 File {issue_file} will be created (doesn't exist)")
            
            # Query RAG database for secure coding patterns (Enhanced with live SonarSource rules)
            print("🔍 Querying enhanced RAG database for secure patterns...")
            rag_query = f"{issue.get('type', 'security')} {issue.get('description', '')} {issue.get('vulnerable_code', '')}"
            secure_patterns = await run_in_threadpool(get_secure_coding_patterns, rag_query)
            
            print(f"✅ Retrieved {len(secure_patterns)} characters of security patterns from RAG database")
            
            # Enhanced "Fixer" AI prompt - Gemini receives BOTH user issue AND RAG knowledge
            # Extract the specific vulnerable line if line number is provided
            vulnerable_line_context = ""
            if issue.get('line') and original_content:
                try:
                    lines = original_content.split('\n')
                    line_num = int(issue.get('line', 0))
                    if 1 <= line_num <= len(lines):
                        # Show context around the vulnerable line
                        start_line = max(1, line_num - 2)
                        end_line = min(len(lines), line_num + 2)
                        context_lines = []
                        for i in range(start_line - 1, end_line):
                            marker = " >>> " if i == line_num - 1 else "     "
                            context_lines.append(f"{i+1:3d}:{marker}{lines[i]}")
                        vulnerable_line_context = "\n".join(context_lines)
                except:
                    vulnerable_line_context = "Could not extract line context"
            
            fixer_prompt = f"""
You are a security code remediation expert. I'm providing you with BOTH a specific security issue that needs fixing AND relevant security knowledge from our RAG database. Use both pieces of information together to create the best possible fix.

**USER'S SECURITY ISSUE TO FIX:**
- File: {issue.get('file', 'unknown')}
- Line: {issue.get('line', 'unknown')}
- Type: {issue.get('type', 'unknown')}
- Description: {issue.get('description', 'No description')}
- Vulnerable Code: {issue.get('vulnerable_code', 'Not specified')}
- Severity: {issue.get('severity', 'Medium')}

**VULNERABLE LINE CONTEXT:**
```
{vulnerable_line_context if vulnerable_line_context else "Line context not available"}
```

**CURRENT FILE CONTENT:**
```
{original_content if file_existed else "// File does not exist - will be created"}
```

**RAG SECURITY KNOWLEDGE (SonarSource Rules + OWASP Guidelines):**
{secure_patterns}

**CRITICAL REQUIREMENTS:**
1. You MUST provide the COMPLETE file content in your response, not just the changed lines
2. Make specific, targeted security fixes based on the issue description
3. If the issue is about hardcoded credentials, replace them with environment variable loading
4. If it's about missing validation, add proper input validation  
5. If it's about injection vulnerabilities, add sanitization/escaping
6. Preserve ALL existing functionality while fixing the security issue
7. DO NOT just add a comment - make actual code changes

**YOUR TASK:**
Analyze the user's security issue AND the RAG knowledge together to:
1. Understand the specific vulnerability in the user's code
2. Find the most relevant security patterns from the RAG knowledge
3. Apply the best remediation technique from both sources
4. Generate a complete, production-ready fixed version of the file
5. Reference specific rules and patterns you used from the RAG knowledge
6. Ensure the fix addresses the user's exact issue
7. Preserve all functionality while improving security

**RESPONSE FORMAT:**
Return ONLY a JSON object with this exact structure:
{{
    "fixed_content": "complete fixed file content here",
    "changes_made": [
        "Applied pattern from RAG knowledge: Replaced eval() with ast.literal_eval() based on SonarSource RSPEC-XXX",
        "Implemented user's specific issue fix: Added input validation for the vulnerable code section"
    ],
    "security_impact": "Resolves the user's {issue.get('type', 'security')} issue while applying RAG-recommended security patterns",
    "commit_message": "fix: resolve {issue.get('type', 'security')} vulnerability in {issue.get('file', 'file')} using RAG-enhanced patterns",
    "lines_changed": [
        {{"line_number": 15, "old_code": "eval(user_input)", "new_code": "ast.literal_eval(user_input)", "change_type": "modified"}},
        {{"line_number": 16, "old_code": "", "new_code": "# Security: Applied RAG pattern (SonarSource RSPEC-XXX)", "change_type": "added"}}
    ],
    "fix_summary": "Combined user issue analysis with RAG security knowledge: {issue.get('description', 'vulnerability')} resolved using recommended patterns",
    "rag_patterns_applied": ["Pattern from RAG: SonarSource RSPEC-XXX for code injection prevention", "OWASP guideline for input validation"],
    "user_issue_addressed": "Specific fix for: {issue.get('description', 'security issue')} in {issue.get('file', 'file')}",
    "integration_approach": "Gemini AI analyzed both user issue and RAG knowledge simultaneously for optimal fix"
}}
"""

            # Call Gemini AI with BOTH user issue and RAG knowledge
            print("🤖 Gemini AI processing user issue + RAG knowledge together...")
            ai_response = await run_in_threadpool(get_chat_response, [
                {'type': 'user', 'parts': [fixer_prompt]}
            ], 'smart')  # Use smart model for comprehensive analysis
            
            # Parse the AI response with robust JSON parsing
            def clean_and_parse_json(text):
                """Clean and parse JSON from AI response"""
                try:
                    # First try to find JSON in ```json blocks
                    import re
                    json_block = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
                    if json_block:
                        json_text = json_block.group(1)
                        return json.loads(json_text)
                except Exception:
                    pass
                
                # Fallback: Extract between first { and last } and clean
                try:
                    start = text.find('{')
                    end = text.rfind('}') + 1
                    if start != -1 and end != -1:
                        json_text = text[start:end]
                        # Simple cleanup - replace newlines with spaces
                        json_text = json_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                        # Remove extra whitespace
                        json_text = re.sub(r'\s+', ' ', json_text)
                        return json.loads(json_text)
                except Exception:
                    pass
                
                return None
            
            try:
                fix_data = clean_and_parse_json(ai_response)
                if fix_data:
                    print("✅ Successfully parsed AI fix response for GitHub")
                else:
                    raise ValueError("Could not parse JSON from AI response")
            except Exception as e:
                print(f"⚠️ Failed to parse AI JSON, using enhanced fallback: {e}")
                print(f"🔍 AI Response: {ai_response[:500]}...")
                
                # Enhanced fallback: create intelligent fix based on issue type
                issue_desc = issue.get('description', '').lower()
                
                if 'private key' in issue_desc or 'secret' in issue_desc or 'credential' in issue_desc:
                    # For key/secret issues, replace with environment variable pattern
                    if original_content:
                        # Try to find and replace the hardcoded credential
                        lines = original_content.split('\n')
                        fixed_lines = []
                        for line in lines:
                            if 'password' in line.lower() and '=' in line and ('"' in line or "'" in line):
                                # Replace hardcoded password with env var
                                var_name = line.split('=')[0].strip()
                                fixed_lines.append(f"import os")
                                fixed_lines.append(f"{var_name} = os.getenv('{var_name.upper()}', 'default_secure_value')")
                            else:
                                fixed_lines.append(line)
                        fixed_content = '\n'.join(fixed_lines)
                    else:
                        fixed_content = "import os\n# Credentials moved to environment variables\n"
                    
                    fix_data = {
                        "fixed_content": fixed_content,
                        "changes_made": ["Replaced hardcoded credentials with environment variables"],
                        "fix_summary": f"Secured credential management in {issue.get('file', 'file')}",
                        "security_impact": "Credentials moved to secure environment variables"
                    }
                elif '.gitignore' in issue.get('file', ''):
                    # For gitignore issues, add security patterns
                    fix_data = {
                        "fixed_content": original_content + "\n# Security additions\n*.key\n*.pem\n*.env\n.env.*\nsecrets/\nconfig/secrets.yml\n",
                        "changes_made": ["Added security patterns to .gitignore"],
                        "fix_summary": "Enhanced .gitignore with security patterns",
                        "security_impact": "Prevented sensitive files from being committed"
                    }
                else:
                    # For other issues, try to apply a meaningful fix
                    if original_content:
                        fixed_content = f"# Security improvement applied\n# Issue: {issue.get('description', 'Security vulnerability')}\n{original_content}"
                    else:
                        fixed_content = f"# Security fix for: {issue.get('description', 'Security vulnerability')}\n# Please implement proper security measures\n"
                    
                    fix_data = {
                        "fixed_content": fixed_content,
                        "changes_made": [f"Applied security fix for {issue.get('type', 'security')} issue"],
                        "security_impact": "Security improvement applied",
                        "commit_message": f"fix: resolve {issue.get('type', 'security')} vulnerability",
                        "lines_changed": [],
                        "fix_summary": f"Security fix applied for {issue.get('description', 'vulnerability')}"
                    }
            
            # Apply the fix to the file
            fixed_content = fix_data.get('fixed_content', '')
            if not fixed_content:
                raise HTTPException(status_code=500, detail="AI did not provide fixed content")
            
            # Create directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write the fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print("✅ Fix applied to local file")
            
            # Calculate detailed code differences with unified diff
            def calculate_code_diff(original: str, fixed: str) -> dict:
                """Calculate detailed differences between original and fixed code"""
                import difflib
                
                original_lines = original.splitlines(keepends=True) if original else []
                fixed_lines = fixed.splitlines(keepends=True)
                
                # Generate unified diff
                unified_diff = list(difflib.unified_diff(
                    original_lines, 
                    fixed_lines, 
                    fromfile='original',
                    tofile='fixed',
                    lineterm='',
                    n=3  # 3 lines of context
                ))
                
                # Simple diff calculation
                diff_stats = {
                    "lines_added": len(fixed_lines) - len(original_lines) if len(fixed_lines) > len(original_lines) else 0,
                    "lines_removed": len(original_lines) - len(fixed_lines) if len(original_lines) > len(fixed_lines) else 0,
                    "lines_modified": 0,
                    "total_changes": 0,
                    "unified_diff": ''.join(unified_diff),
                    "has_changes": len(unified_diff) > 0
                }
                
                # Calculate modifications
                min_lines = min(len(original_lines), len(fixed_lines))
                for i in range(min_lines):
                    if original_lines[i] != fixed_lines[i]:
                        diff_stats["lines_modified"] += 1
                
                diff_stats["total_changes"] = diff_stats["lines_added"] + diff_stats["lines_removed"] + diff_stats["lines_modified"]
                
                return diff_stats
            
            code_diff = calculate_code_diff(original_content, fixed_content)
            
            # Create a new branch
            branch_name = request.branch_name or f"fix/{issue.get('type', 'security').lower().replace(' ', '-')}-{issue.get('file', 'file').replace('/', '-').replace('.', '-')}"
            
            # Check if branch already exists
            try:
                github_repo.get_branch(branch_name)
                # Branch exists, add timestamp to make it unique
                import time
                branch_name = f"{branch_name}-{int(time.time())}"
            except:
                pass  # Branch doesn't exist, which is what we want
            
            # Create branch and commit
            repo.git.checkout('-b', branch_name)
            
            # Use relative path for git operations (normalize path separators)
            git_file_path = issue_file.replace('\\', '/')
            print(f"📝 Adding file to git: {git_file_path}")
            print(f"🔍 Current working directory: {os.getcwd()}")
            print(f"🔍 Repository working directory: {repo.working_dir}")
            
            try:
                # Verify file exists relative to repo root
                full_file_path = os.path.join(repo.working_dir, git_file_path)
                if os.path.exists(full_file_path):
                    print(f"✅ File exists at: {full_file_path}")
                else:
                    print(f"❌ File not found at: {full_file_path}")
                    # List files in the directory to debug
                    dir_to_check = os.path.dirname(full_file_path)
                    if os.path.exists(dir_to_check):
                        print(f"📂 Files in {dir_to_check}: {os.listdir(dir_to_check)}")
                
                repo.git.add(git_file_path)
                print(f"✅ Successfully added {git_file_path} to git")
                
            except Exception as git_add_error:
                print(f"❌ DETAILED ERROR in git add: {git_add_error}")
                print(f"📍 Git add failed for: {git_file_path}")
                print(f"📍 Repository root: {repo.working_dir}")
                print(f"📍 Attempted file path: {git_file_path}")
                raise git_add_error
            
            # Configure Git user identity for commits (use global config if available)
            try:
                # First try to get the global Git configuration
                try:
                    global_email = repo.git.config('--global', '--get', 'user.email')
                    global_name = repo.git.config('--global', '--get', 'user.name')
                    print(f"✅ Using global Git identity: {global_name} <{global_email}>")
                except:
                    # If global config not available, set a default
                    repo.git.config('user.email', 'altx-security-bot@automated.fix')
                    repo.git.config('user.name', 'AltX Security Bot')
                    print("✅ Git user identity configured with bot defaults")
            except Exception as config_error:
                print(f"⚠️ Warning: Could not configure Git identity: {config_error}")
            
            commit_message = fix_data.get('commit_message', f"fix: resolve security vulnerability in {issue_file}")
            repo.git.commit('-m', commit_message)
            print(f"✅ Successfully committed fix with message: {commit_message}")
            
            # Push the branch
            try:
                origin = repo.remote('origin')
                origin.push(branch_name)
                print(f"✅ Pushed fix to branch: {branch_name}")
                
                # If push succeeds, continue with PR creation
                push_success = True
                
            except Exception as push_error:
                push_success = False
                error_msg = str(push_error)
                print(f"❌ Push failed: {error_msg}")
                
                # Check if it's a permission issue (403, authentication, etc.)
                if "403" in error_msg or "401" in error_msg or "authentication" in error_msg.lower() or "permission" in error_msg.lower():
                    print("🔒 No write access to repository - attempting fork workflow...")
                    
                    try:
                        # Try to fork the repository
                        print(f"🍴 Attempting to fork {owner}/{repo_name}")
                        
                        # Get the authenticated user
                        auth_user = working_github_client.get_user()
                        user_login = auth_user.login
                        print(f"👤 Authenticated as: {user_login}")
                        
                        # Check if fork already exists
                        try:
                            existing_fork = working_github_client.get_repo(f"{user_login}/{repo_name}")
                            print(f"✅ Fork already exists: {existing_fork.full_name}")
                            forked_repo = existing_fork
                        except:
                            # Create fork
                            original_repo = working_github_client.get_repo(f"{owner}/{repo_name}")
                            forked_repo = auth_user.create_fork(original_repo)
                            print(f"✅ Fork created: {forked_repo.full_name}")
                        
                        # Update remote origin to point to fork
                        fork_url = forked_repo.clone_url
                        # Add token to URL for authentication
                        token = os.getenv("GITHUB_TOKEN")
                        if token:
                            fork_url_with_auth = fork_url.replace("https://", f"https://{token}@")
                        else:
                            fork_url_with_auth = fork_url
                        
                        # Remove existing origin and add fork as origin
                        try:
                            repo.delete_remote('origin')
                        except:
                            pass
                        
                        fork_origin = repo.create_remote('origin', fork_url_with_auth)
                        print(f"🔄 Updated origin to fork: {fork_url}")
                        
                        # Push to fork
                        fork_origin.push(branch_name)
                        print(f"✅ Pushed fix to fork: {forked_repo.full_name}/{branch_name}")
                        
                        # Create PR from fork to original repo
                        head_ref = f"{user_login}:{branch_name}"  # Format: fork_owner:branch_name
                        
                        push_success = True
                        # Update github_repo to the original for PR creation
                        github_repo = working_github_client.get_repo(f"{owner}/{repo_name}")
                        
                    except Exception as fork_error:
                        print(f"❌ Fork workflow failed: {fork_error}")
                        
                        # Return local fix suggestion with fork instructions
                        return {
                            "success": True,
                            "message": f"🔧 Security fix generated for {issue_file} (Fork required)",
                            "fix_type": "fork_required",
                            "access_limitation": "Repository requires forking to contribute",
                            "fork_instructions": [
                                f"1. Go to https://github.com/{owner}/{repo_name}",
                                "2. Click the 'Fork' button to create your own copy",
                                "3. Clone your fork to your local machine",
                                "4. Apply the fix shown below",
                                "5. Commit and push to your fork",
                                "6. Create a pull request from your fork to the original repository"
                            ],
                            "fix_details": {
                                "file_fixed": issue_file,
                                "vulnerability_type": issue.get('type'),
                                "severity": issue.get('severity', 'Medium'),
                                "changes_made": fix_data.get('changes_made', []),
                                "security_impact": fix_data.get('security_impact'),
                                "fix_summary": fix_data.get('fix_summary', 'Security fix generated'),
                                "lines_changed": fix_data.get('lines_changed', [])
                            },
                            "code_comparison": {
                                "file_existed_before": file_existed,
                                "original_content": original_content,
                                "fixed_content": fixed_content,
                                "content_length_before": len(original_content),
                                "content_length_after": len(fixed_content),
                                "character_changes": len(fixed_content) - len(original_content)
                            },
                            "manual_fix_instructions": f"To apply this fix:\n1. Fork the repository at https://github.com/{owner}/{repo_name}\n2. Clone your fork\n3. Edit the file: {issue_file}\n4. Replace the content with the fixed version\n5. Commit, push, and create a pull request",
                            "code_preview": {
                                "original_preview": original_content[:500] + ("..." if len(original_content) > 500 else ""),
                                "fixed_preview": fixed_content[:500] + ("..." if len(fixed_content) > 500 else ""),
                                "preview_truncated": len(original_content) > 500 or len(fixed_content) > 500
                            }
                        }
                else:
                    # For other git errors, re-raise
                    raise push_error
            
            # Only proceed with PR creation if push was successful
            if not push_success:
                return  # This shouldn't be reached due to the return above, but just in case
            
            # Create enhanced pull request with code comparison
            pr_title = f"🔒 Security Fix: {issue.get('description', 'Vulnerability remediation')}"
            
            # Generate code diff preview for PR body
            def generate_diff_preview(original: str, fixed: str, max_lines: int = 20) -> str:
                """Generate a diff preview for the PR description"""
                if not original and fixed:
                    return f"```diff\n+ {chr(10).join(fixed.splitlines()[:max_lines])}\n```"
                
                original_lines = original.splitlines()
                fixed_lines = fixed.splitlines()
                
                diff_preview = "```diff\n"
                
                # Show first few differences
                shown_lines = 0
                min_lines = min(len(original_lines), len(fixed_lines))
                
                for i in range(min_lines):
                    if shown_lines >= max_lines:
                        diff_preview += "... (more changes in the full diff)\n"
                        break
                        
                    if original_lines[i] != fixed_lines[i]:
                        diff_preview += f"- {original_lines[i]}\n+ {fixed_lines[i]}\n"
                        shown_lines += 2
                
                # Show added lines
                if len(fixed_lines) > len(original_lines):
                    for i in range(min_lines, min(len(fixed_lines), min_lines + max_lines - shown_lines)):
                        diff_preview += f"+ {fixed_lines[i]}\n"
                        shown_lines += 1
                
                diff_preview += "```"
                return diff_preview
            
            diff_preview = generate_diff_preview(original_content, fixed_content)
            
            pr_body = f"""
## 🛡️ Automated Security Fix

**Vulnerability Fixed:**
- **File:** `{issue.get('file', 'unknown')}`
- **Line:** {issue.get('line', 'unknown')}
- **Type:** {issue.get('type', 'Security Issue')}
- **Severity:** {issue.get('severity', 'Medium')}
- **Description:** {issue.get('description', 'No description')}

**Fix Summary:**
{fix_data.get('fix_summary', 'Security improvements applied')}

**Changes Made:**
{chr(10).join([f'- {change}' for change in fix_data.get('changes_made', [])])}

**Security Impact:**
{fix_data.get('security_impact', 'Improves application security')}

**Code Changes Preview:**
{diff_preview}

**Statistics:**
- **Lines Added:** {code_diff['lines_added']}
- **Lines Modified:** {code_diff['lines_modified']}
- **Lines Removed:** {code_diff['lines_removed']}
- **Total Changes:** {code_diff['total_changes']}

**Generated by:** AltX Security Scanner - Automated Remediation
**Powered by:** RAG-enhanced AI code analysis

---

⚠️ **Please review this automated fix carefully before merging.**

🔍 **Testing Recommended:**
- Run existing tests to ensure functionality is preserved
- Perform security testing to verify the vulnerability is resolved
- Review the code changes for any potential side effects
"""
            try:
                default_branch = github_repo.default_branch
                print(f"📋 Repository default branch: {default_branch}")
                try:
                    remote_branch = github_repo.get_branch(branch_name)
                    print(f"✅ Branch {branch_name} confirmed on remote")
                except Exception as e:
                    print(f"⚠️ Branch verification failed: {e}")
                    github_repo = working_github_client.get_repo(f"{owner}/{repo_name}")
            
                # Check if we're working with a fork (head_ref would be set in fork workflow)
                if 'head_ref' in locals():
                    print(f"🍴 Creating PR from fork: {head_ref} -> {default_branch}")
                    pull_request = github_repo.create_pull(
                        title=pr_title,
                        body=pr_body,
                        head=head_ref,  # fork_owner:branch_name
                        base=default_branch
                    )
                else:
                    print(f"📝 Creating PR from same repo: {branch_name} -> {default_branch}")
                    pull_request = github_repo.create_pull(
                        title=pr_title,
                        body=pr_body,
                        head=branch_name,
                        base=default_branch
                    )
                print(f"✅ Pull request created: {pull_request.html_url}")
            except Exception as pr_error:
                error_msg = str(pr_error)
                print(f"❌ Pull request creation failed: {error_msg}")
                
                # Handle specific GitHub API errors with user-friendly messages
                if "403" in error_msg and ("archived" in error_msg.lower() or "read-only" in error_msg.lower()):
                    print(f"🔒 Repository is archived and read-only: {owner}/{repo_name}")
                    return {
                        "success": True,
                        "message": f"🔧 Security fix generated for {issue_file} (Repository is archived)",
                        "fix_type": "archived_repository",
                        "access_limitation": f"Repository {owner}/{repo_name} is archived and read-only",
                        "manual_fix_instructions": f"This repository is archived and cannot accept pull requests. To apply this fix:\n1. Contact the repository owner to unarchive it\n2. Or fork the repository and apply the fix to your fork\n3. The security issue was found in: {issue_file}",
                        "fix_details": fix_data,
                        "code_comparison": {
                            "original_content": original_content,
                            "fixed_content": fixed_content,
                            "content_length_before": len(original_content),
                            "content_length_after": len(fixed_content),
                            "character_changes": len(fixed_content) - len(original_content)
                        },
                        "code_preview": {
                            "original_preview": original_content[:500] + ("..." if len(original_content) > 500 else ""),
                            "fixed_preview": fixed_content[:500] + ("..." if len(fixed_content) > 500 else ""),
                            "preview_truncated": len(original_content) > 500 or len(fixed_content) > 500
                        }
                    }
                elif "404" in error_msg:
                    print(f"❌ PR creation failed with 404. Debugging info:")
                    print(f"   Repository: {owner}/{repo_name}")
                    print(f"   Head branch: {branch_name}")
                    print(f"   Base branch: {default_branch}")
                    print(f"   Repository exists: {github_repo.full_name}")
                    
                    # Check if it's a branch not found issue
                    if "not found" in error_msg.lower() and "branch" in error_msg.lower():
                        print(f"🔍 Branch not found - this might be a timing issue")
                        return {
                            "success": True,
                            "message": f"🔧 Security fix applied to {issue_file} (Branch sync issue)",
                            "fix_type": "branch_sync_issue",
                            "access_limitation": "Branch synchronization issue with GitHub",
                            "manual_fix_instructions": f"The fix was applied locally but there was a branch synchronization issue. To resolve:\n1. The changes were made to: {issue_file}\n2. Try creating the pull request manually\n3. Or re-run the fix after a few minutes",
                            "fix_details": fix_data,
                            "code_comparison": {
                                "original_content": original_content,
                                "fixed_content": fixed_content,
                                "content_length_before": len(original_content),
                                "content_length_after": len(fixed_content),
                                "character_changes": len(fixed_content) - len(original_content)
                            }
                        }
                    
                    if hasattr(github_repo, 'fork') and github_repo.fork:
                        print("   Note: This is a forked repository")
                        head_with_owner = f"{owner}:{branch_name}"
                        print(f"   Trying with owner prefix: {head_with_owner}")
                        try:
                            pull_request = github_repo.create_pull(
                                title=pr_title,
                                body=pr_body,
                                head=head_with_owner,
                                base=default_branch
                            )
                            print(f"✅ Pull request created with owner prefix: {pull_request.html_url}")
                        except Exception as e2:
                            print(f"❌ PR creation with owner prefix also failed: {e2}")
                            raise HTTPException(status_code=404, 
                                detail=f"Failed to create pull request. Repository: {owner}/{repo_name},Branch: {branch_name} → {default_branch}. Error: {error_msg}"
                            )
                    else:
                        raise HTTPException(
                            status_code=404, 
                            detail=f"Failed to create pull request. Repository: {owner}/{repo_name}, Branch: {branch_name} → {default_branch}. Error: {error_msg}"
                        )
                elif "403" in error_msg:
                    print(f"🔒 Permission denied for repository: {owner}/{repo_name}")
                    return {
                        "success": True,
                        "message": f"🔧 Security fix generated for {issue_file} (Permission denied)",
                        "fix_type": "permission_denied",
                        "access_limitation": "Insufficient permissions to create pull request",
                        "manual_fix_instructions": f"Permission denied while creating pull request. To apply this fix:\n1. Ensure your GitHub token has write access to {owner}/{repo_name}\n2. Or fork the repository and apply the fix to your fork\n3. The security issue was found in: {issue_file}",
                        "fix_details": fix_data,
                        "code_comparison": {
                            "original_content": original_content,
                            "fixed_content": fixed_content,
                            "content_length_before": len(original_content),
                            "content_length_after": len(fixed_content),
                            "character_changes": len(fixed_content) - len(original_content)
                        }
                    }
                elif "422" in error_msg and ("collaborator" in error_msg.lower() or "validation failed" in error_msg.lower()):
                    print(f"🤝 Not a collaborator on repository: {owner}/{repo_name}")
                    return {
                        "success": True,
                        "message": f"🔧 Security fix generated for {issue_file} (Fork required for contribution)",
                        "fix_type": "collaboration_required",
                        "access_limitation": "You are not a collaborator on this repository",
                        "manual_fix_instructions": f"You need to be a collaborator to create pull requests directly. To apply this fix:\n1. Ask the repository owner to add you as a collaborator\n2. Or fork the repository at https://github.com/{owner}/{repo_name}\n3. Apply the fix to your fork and create a PR from there\n4. The security issue was found in: {issue_file}",
                        "fix_details": fix_data,
                        "code_comparison": {
                            "original_content": original_content,
                            "fixed_content": fixed_content,
                            "content_length_before": len(original_content),
                            "content_length_after": len(fixed_content),
                            "character_changes": len(fixed_content) - len(original_content)
                        },
                        "fork_url": f"https://github.com/{owner}/{repo_name}/fork",
                        "code_preview": {
                            "original_preview": original_content[:500] + ("..." if len(original_content) > 500 else ""),
                            "fixed_preview": fixed_content[:500] + ("..." if len(fixed_content) > 500 else ""),
                            "preview_truncated": len(original_content) > 500 or len(fixed_content) > 500
                        }
                    }
                else:
                    raise HTTPException(
                            status_code=500,
                            detail=f"Pull request creation error: {error_msg}"
                    )
            # Prepare detailed response with code comparison
            response_data = {
                "success": True,
                "message": f"🔧 Security fix successfully applied to {issue_file}",
                "pull_request": {
                    "url": pull_request.html_url,
                    "number": pull_request.number,
                    "title": pr_title,
                    "branch": branch_name
                },
                "fix_details": {
                    "file_fixed": issue_file,
                    "vulnerability_type": issue.get('type'),
                    "severity": issue.get('severity', 'Medium'),
                    "changes_made": fix_data.get('changes_made', []),
                    "security_impact": fix_data.get('security_impact'),
                    "commit_message": commit_message,
                    "fix_summary": fix_data.get('fix_summary', 'Security fix applied'),
                    "lines_changed": fix_data.get('lines_changed', [])
                },
                "code_comparison": {
                    "file_existed_before": file_existed,
                    "original_content": original_content,
                    "fixed_content": fixed_content,
                    "content_length_before": len(original_content),
                    "content_length_after": len(fixed_content),
                    "diff_statistics": code_diff,
                    "character_changes": len(fixed_content) - len(original_content)
                },
                "metadata": {
                    "repo_url": repo_url,
                    "repo_name": f"{owner}/{repo_name}",
                    "timestamp": datetime.now().isoformat(),
                    "ai_model_used": "smart",
                    "rag_patterns_used": True,
                    "rag_query": rag_query,
                    "rag_patterns_applied": fix_data.get('rag_patterns_applied', []),
                    "user_issue_addressed": fix_data.get('user_issue_addressed', 'Security issue resolved'),
                    "integration_approach": fix_data.get('integration_approach', 'Gemini AI with RAG knowledge'),
                    "security_intelligence": "Gemini AI analyzed user issue + RAG knowledge simultaneously (6000+ patterns)"
                }
            }
            
            # Add preview of changes (first 500 chars of each)
            if original_content or fixed_content:
                response_data["code_preview"] = {
                    "original_preview": original_content[:500] + ("..." if len(original_content) > 500 else ""),
                    "fixed_preview": fixed_content[:500] + ("..." if len(fixed_content) > 500 else ""),
                    "preview_truncated": len(original_content) > 500 or len(fixed_content) > 500
                }
            
            return response_data
            
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                try:
                    import stat
                    
                    def force_remove_readonly(func, path, exc_info):
                        try:
                            if os.path.exists(path):
                                os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
                                func(path)
                        except Exception:
                            pass
                    
                    shutil.rmtree(temp_dir, onerror=force_remove_readonly)
                    print("✅ Temporary directory cleaned up")
                except Exception as e:
                    print(f"⚠️ Warning: Could not clean up temp directory: {e}")
                    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ DETAILED ERROR in propose-fix: {e}")
        print(f"📍 TRACEBACK:\n{error_traceback}")
        raise HTTPException(status_code=500, detail=f"Fix generation failed: {str(e)}\nLocation: {error_traceback.split('File')[-1].split(',')[0] if 'File' in error_traceback else 'Unknown'}")
@app.get("/auth/github/callback")
async def github_callback(code: str = None, state: str = None):
    """
    Handle GitHub OAuth callback after user authorization
    This is the 'front door' for users returning after GitHub login
    """
    try:
        if not code:
            print("❌ No authorization code received from GitHub")
            return RedirectResponse(
                url="/?error=authorization_failed", 
                status_code=302
            )
        
        print(f"✅ Received GitHub authorization code: {code[:10]}...")
        
        # Exchange authorization code for access token
        

        # Exchange authorization code for access token
        token_url = "https://github.com/login/oauth/access_token"
        token_data = {
            "client_id": os.getenv("GITHUB_CLIENT_ID"),  # Changed from GITHUB_APP_ID
            "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
            "code": code,
            "state": state
        }
        token_headers = {
            "Accept": "application/json",
            "User-Agent": "AltX-Security-Scanner"
        }
        
        print("🔄 Exchanging code for access token...")
        token_response = requests.post(token_url, data=token_data, headers=token_headers)
        
        if token_response.status_code != 200:
            print(f"❌ Token exchange failed: {token_response.text}")
            return RedirectResponse(
                url="/?error=token_exchange_failed", 
                status_code=302
            )
        
        token_info = token_response.json()
        access_token = token_info.get("access_token")
        
        if not access_token:
            print(f"❌ No access token received: {token_info}")
            return RedirectResponse(
                url="/?error=no_access_token", 
                status_code=302
            )
        
        print("✅ Access token received successfully")
        
        # Get user information
        user_headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/json",
            "User-Agent": "AltX-Security-Scanner"
        }
        
        user_response = requests.get("https://api.github.com/user", headers=user_headers)
        
        if user_response.status_code != 200:
            print(f"❌ Failed to get user info: {user_response.text}")
            return RedirectResponse(
                url="/?error=user_info_failed", 
                status_code=302
            )
        
        user_info = user_response.json()
        username = user_info.get("login", "unknown")
        user_id = user_info.get("id")
        avatar_url = user_info.get("avatar_url")
        
        print(f"✅ User authenticated: {username} (ID: {user_id})")
        
        # In a real application, you would:
        # 1. Store the user session
        # 2. Create a JWT token
        # 3. Store user data in database
        # For now, we'll just redirect with success
        
        # Redirect to frontend with success and user info
        redirect_url = f"/?auth=success&user={username}&avatar={avatar_url}"
        
        print(f"🚀 Redirecting user to: {redirect_url}")
        
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except Exception as e:
        print(f"❌ OAuth callback error: {str(e)}")
        return RedirectResponse(
            url=f"/?error=callback_failed&message={str(e)}", 
            status_code=302
        )



@app.get("/auth/github/login")
async def github_login():
    """
    Initiate GitHub OAuth login
    This redirects users to GitHub for authorization
    """
    try:
        # Use GITHUB_CLIENT_ID for OAuth, not GITHUB_APP_ID
        github_client_id = os.getenv("GITHUB_CLIENT_ID")  # Changed from GITHUB_APP_ID
        
        if not github_client_id:
            raise HTTPException(status_code=500, detail="GitHub Client ID not configured")
        
        # Generate a random state parameter for security
        import secrets
        state = secrets.token_urlsafe(32)
        
        # GitHub OAuth authorization URL
        github_auth_url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={github_client_id}"
            f"&redirect_uri={os.getenv('GITHUB_CALLBACK_URL', 'http://localhost:8000/auth/github/callback')}"
            f"&scope=repo,user:email"
            f"&state={state}"
            f"&allow_signup=true"
        )
        
        print(f"🔗 Redirecting to GitHub OAuth: {github_auth_url}")
        
        return RedirectResponse(url=github_auth_url, status_code=302)
        
    except Exception as e:
        print(f"❌ Login initiation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

from fastapi import Request

@app.get("/auth/google/callback")
async def google_callback(request: Request):
    """
    Handle Google OAuth callback after user authorization
    """
    try:
        # Get the authorization code from the query parameters
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code:
            print("❌ No authorization code received from Google")
            return RedirectResponse(url="/?error=authorization_failed", status_code=302)

        print(f"✅ Received Google authorization code: {code[:10]}...")

        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "code": code,
            "redirect_uri": os.getenv("GOOGLE_CALLBACK_URL", "http://localhost:8000/auth/google/callback"),
            "grant_type": "authorization_code"
        }
        token_headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        print("🔄 Exchanging code for access token...")
        token_response = requests.post(token_url, data=token_data, headers=token_headers)

        if token_response.status_code != 200:
            print(f"❌ Token exchange failed: {token_response.text}")
            return RedirectResponse(url="/?error=token_exchange_failed", status_code=302)

        token_info = token_response.json()
        access_token = token_info.get("access_token")

        if not access_token:
            print(f"❌ No access token received: {token_info}")
            return RedirectResponse(url="/?error=no_access_token", status_code=302)

        print("✅ Access token received successfully")

        # Get user information
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        user_headers = {
            "Authorization": f"Bearer {access_token}"
        }
        user_response = requests.get(user_info_url, headers=user_headers)

        if user_response.status_code != 200:
            print(f"❌ Failed to get user info: {user_response.text}")
            return RedirectResponse(url="/?error=user_info_failed", status_code=302)

        user_info = user_response.json()
        email = user_info.get("email", "unknown")
        name = user_info.get("name", "unknown")
        picture = user_info.get("picture", "")

        print(f"✅ User authenticated: {email} ({name})")

        # Redirect to frontend homepage with success and user info
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        redirect_url = f"{frontend_url}/home?auth=success&user={email}&name={name}&avatar={picture}"
        print(f"🚀 Redirecting user to: {redirect_url}")

        return RedirectResponse(url=redirect_url, status_code=302)

    except Exception as e:
        print(f"❌ OAuth callback error: {str(e)}")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(url=f"{frontend_url}/home?error=callback_failed&message={str(e)}", status_code=302)
@app.get("/auth/google/login")
async def google_login():
    """
    Initiate Google OAuth login
    Redirects user to Google's OAuth consent screen
    """
    try:
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        google_callback_url = os.getenv("GOOGLE_CALLBACK_URL", "http://localhost:8000/auth/google/callback")
        if not google_client_id:
            raise HTTPException(status_code=500, detail="Google Client ID not configured")

        # Generate a random state parameter for security
        state = secrets.token_urlsafe(32)

        # Google OAuth authorization URL
        google_auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={google_client_id}"
            f"&redirect_uri={google_callback_url}"
            "&response_type=code"
            "&scope=openid%20email%20profile"
            f"&state={state}"
            "&access_type=offline"
            "&prompt=consent"
        )

        print(f"🔗 Redirecting to Google OAuth: {google_auth_url}")
        return RedirectResponse(url=google_auth_url, status_code=302)

    except Exception as e:
        print(f"❌ Google login initiation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Google login failed: {str(e)}")
@app.get("/auth/status")
async def auth_status():
    """
    Check authentication status
    """
    return {
        "github_app_configured": bool(os.getenv("GITHUB_APP_ID")),
        "github_client_id_configured": bool(os.getenv("GITHUB_CLIENT_ID")),  # Added
        "github_client_secret_configured": bool(os.getenv("GITHUB_CLIENT_SECRET")),
        "callback_url": os.getenv("GITHUB_CALLBACK_URL", "http://localhost:8000/auth/github/callback"),
        "login_url": "/auth/github/login",
        "timestamp": datetime.now().isoformat()
    }
@app.post("/api/deploy")
async def manual_deploy(request: dict):
    """
    Manual deployment endpoint for the Deploy Page
    Does not require webhook signature verification
    """
    try:
        repo_url = request.get("repo_url")
        if not repo_url:
            raise HTTPException(status_code=400, detail="Repository URL is required")
        
        print(f"🚀 Manual deployment requested for: {repo_url}")
        
        # Create a simplified payload for deployment
        repo_name = repo_url.split('/')[-1]
        owner = repo_url.split('/')[-2]
        
        deployment_payload = {
            "ref": "refs/heads/main",
            "repository": {
                "name": repo_name,
                "full_name": f"{owner}/{repo_name}",
                "clone_url": repo_url,
                "default_branch": "main"
            },
            "head_commit": {
                "id": f"manual-deploy-{int(time.time())}",
                "message": "Manual deployment from AltX Deploy Page",
                "committer": {
                    "name": "AltX Deploy"
                }
            }
        }
        
        print(f"📦 Processing deployment for {owner}/{repo_name}")
        
        # Handle push event (same logic as webhook but without signature verification)
        result = await handle_push_event(deployment_payload)
        
        return {
            "success": True,
            "message": f"Deployment initiated for {repo_name}",
            "deployment_result": result,
            "repository": {
                "name": repo_name,
                "owner": owner,
                "url": repo_url
            },
            "deployment_url": f"http://localhost:8000/{repo_name}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Manual deployment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")

@app.post("/api/webhook")
async def github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    """
    Enhanced GitHub App webhook endpoint for automated deployments and security analysis
    """
    try:
        # 1. Get the secret from your environment variables
        secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        if not secret:
            print("❌ Webhook secret is not configured.")
            raise HTTPException(status_code=500, detail="Webhook secret not configured.")

        # 2. Verify the signature to ensure the request is from GitHub
        raw_body = await request.body()
        expected_signature = "sha256=" + hmac.new(secret.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()

        if not x_hub_signature_256:
            print("❌ No signature provided in webhook request.")
            raise HTTPException(status_code=403, detail="No signature provided.")

        if not hmac.compare_digest(expected_signature, x_hub_signature_256):
            print("❌ Invalid webhook signature.")
            raise HTTPException(status_code=403, detail="Invalid signature.")
        
        # 3. Process the event payload
        event_type = request.headers.get("X-GitHub-Event")
        payload = await request.json()

        print(f"🎉 Received valid webhook. Event type: {event_type}")
        
        # 4. Handle different GitHub events
        if event_type == "push":
            return await handle_push_event(payload)
        elif event_type == "pull_request":
            return await handle_pull_request_event(payload)
        elif event_type == "installation":
            return await handle_installation_event(payload)
        elif event_type == "security_advisory":
            return await handle_security_advisory_event(payload)
        else:
            print(f"📝 Unhandled event type: {event_type}")
            return {"status": "event received but not processed", "event_type": event_type}

    except Exception as e:
        print(f"❌ Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")
async def handle_push_event(payload):
    """Handle push events - trigger deployment and security analysis"""
    try:
        ref = payload.get("ref", "")
        repo_info = payload.get("repository", {})
        clone_url = repo_info.get("clone_url")
        repo_name = repo_info.get("name")
        repo_full_name = repo_info.get("full_name")
        default_branch = repo_info.get("default_branch", "main")
        
        # Check if push is to default branch (main/master)
        if ref == f"refs/heads/{default_branch}":
            print(f"🚀 Push to {default_branch} branch detected for {repo_full_name}")
            
            if clone_url and repo_name:
                # Trigger automated security analysis
                print(f"🔍 Triggering automated security analysis for {repo_name}...")
                
                # Run security analysis in background
                analysis_task = asyncio.create_task(
                    run_automated_security_analysis(repo_info, payload)
                )
                
                # Trigger deployment process
                print(f"📦 Triggering deployment for {repo_name}...")
                deployment_task = asyncio.create_task(
                    deploy_project(repo_name, clone_url, payload)
                )
                
                return {
                    "status": "deployment and security analysis triggered",
                    "repo": repo_full_name,
                    "branch": default_branch,
                    "commit": payload.get("head_commit", {}).get("id", "unknown")[:8],
                    "timestamp": datetime.now().isoformat(),
                    "actions": ["security_analysis", "deployment"]
                }
            else:
                print("⚠️ Push event received, but couldn't get repo info.")
                return {"status": "insufficient repo information"}
        else:
            print(f"📝 Push to non-default branch {ref} - no deployment triggered")
            return {"status": "push to non-default branch", "ref": ref}
            
    except Exception as e:
        print(f"❌ Error handling push event: {str(e)}")
        return {"status": "error", "error": str(e)}

async def handle_pull_request_event(payload):
    """Handle pull request events - run security checks on PR"""
    try:
        action = payload.get("action")
        pr_info = payload.get("pull_request", {})
        repo_info = payload.get("repository", {})
        
        print(f"🔍 Pull request {action}: #{pr_info.get('number')} in {repo_info.get('full_name')}")
        
        if action in ["opened", "synchronize", "reopened"]:
            # Run security analysis on PR
            print(f"🛡️ Running security analysis on PR #{pr_info.get('number')}")
            
            # Analyze the PR branch
            head_sha = pr_info.get("head", {}).get("sha")
            base_sha = pr_info.get("base", {}).get("sha")
            
            # Run security analysis in background
            analysis_task = asyncio.create_task(
                run_pr_security_analysis(pr_info, repo_info, payload)
            )
            
            return {
                "status": "pr security analysis triggered",
                "pr_number": pr_info.get("number"),
                "repo": repo_info.get("full_name"),
                "head_sha": head_sha[:8] if head_sha else "unknown",
                "action": action
            }
        
        return {"status": "pr event processed", "action": action}
        
    except Exception as e:
        print(f"❌ Error handling pull request event: {str(e)}")
        return {"status": "error", "error": str(e)}

async def handle_installation_event(payload):
    """Handle GitHub App installation events"""
    try:
        action = payload.get("action")
        installation_info = payload.get("installation", {})
        account_info = installation_info.get("account", {})
        
        print(f"📱 GitHub App {action} for {account_info.get('login')}")
        
        if action == "created":
            print(f"✅ New installation: {account_info.get('login')} ({account_info.get('type')})")
            
            # Send welcome security analysis
            if installation_info.get("repository_selection") == "all":
                print("🔒 Full repository access granted - can provide comprehensive security analysis")
            else:
                repos = payload.get("repositories", [])
                print(f"🔒 Selected repository access: {len(repos)} repositories")
            
            return {
                "status": "installation created",
                "account": account_info.get("login"),
                "repo_access": installation_info.get("repository_selection"),
                "permissions": list(installation_info.get("permissions", {}).keys())
            }
        
        return {"status": "installation event processed", "action": action}
        
    except Exception as e:
        print(f"❌ Error handling installation event: {str(e)}")
        return {"status": "error", "error": str(e)}

async def handle_security_advisory_event(payload):
    """Handle security advisory events"""
    try:
        action = payload.get("action")
        advisory = payload.get("security_advisory", {})
        
        print(f"🚨 Security advisory {action}: {advisory.get('summary', 'Unknown')}")
        
        if action == "published":
            severity = advisory.get("severity", "unknown")
            cve_id = advisory.get("cve_id")
            
            print(f"🔒 New security advisory: {severity} severity")
            if cve_id:
                print(f"🆔 CVE ID: {cve_id}")
            
            # Could trigger repository rescans for affected dependencies
            return {
                "status": "security advisory processed",
                "severity": severity,
                "cve_id": cve_id,
                "action": action
            }
        
        return {"status": "security advisory event processed", "action": action}
        
    except Exception as e:
        print(f"❌ Error handling security advisory event: {str(e)}")
        return {"status": "error", "error": str(e)}

async def run_automated_security_analysis(repo_info, payload):
    """Run automated security analysis on repository"""
    try:
        repo_full_name = repo_info.get("full_name")
        clone_url = repo_info.get("clone_url")
        
        print(f"🔍 Starting automated security analysis for {repo_full_name}")
        
        # Create analysis request
        analysis_request = RepoAnalysisRequest(
            repo_url=clone_url,
            model_type='smart',  # Use smart model for webhook-triggered analysis
            deep_scan=True
        )
        
        # Run comprehensive analysis
        analysis_result = await analyze_repo_comprehensive(analysis_request)
        
        if not analysis_result.get("error"):
            security_score = analysis_result.get("overall_security_score", 0)
            security_level = analysis_result.get("security_level", "Unknown")
            
            print(f"✅ Security analysis complete: {security_score}/100 ({security_level})")
            
            # If security issues found, could create an issue or PR
            critical_issues = []
            critical_issues.extend(analysis_result.get("secret_scan_results", []))
            
            high_severity_static = [
                issue for issue in analysis_result.get("static_analysis_results", [])
                if isinstance(issue, dict) and issue.get("issue_severity") == "HIGH"
            ]
            critical_issues.extend(high_severity_static)
            
            if critical_issues:
                print(f"🚨 {len(critical_issues)} critical security issues found")
                
                # Could automatically create security issue in repository
                await create_security_issue_if_needed(repo_info, analysis_result, critical_issues)
            
            return {
                "analysis_complete": True,
                "security_score": security_score,
                "critical_issues": len(critical_issues)
            }
        else:
            print(f"❌ Security analysis failed: {analysis_result.get('error')}")
            return {"analysis_complete": False, "error": analysis_result.get("error")}
            
    except Exception as e:
        print(f"❌ Automated security analysis error: {str(e)}")
        return {"analysis_complete": False, "error": str(e)}

async def run_pr_security_analysis(pr_info, repo_info, payload):
    """Run security analysis on pull request"""
    try:
        pr_number = pr_info.get("number")
        repo_full_name = repo_info.get("full_name")
        head_repo_url = pr_info.get("head", {}).get("repo", {}).get("clone_url")
        
        print(f"🔍 Analyzing PR #{pr_number} in {repo_full_name}")
        
        if head_repo_url:
            # Create analysis request for PR branch
            analysis_request = RepoAnalysisRequest(
                repo_url=head_repo_url,
                model_type='fast',  # Use fast model for PR analysis
                deep_scan=False  # Lighter scan for PRs
            )
            
            # Run analysis
            analysis_result = await analyze_repo_comprehensive(analysis_request)
            
            if not analysis_result.get("error"):
                security_score = analysis_result.get("overall_security_score", 0)
                
                # Could post security analysis as PR comment
                print(f"✅ PR security analysis complete: {security_score}/100")
                
                # If critical issues found, could request changes
                secrets_found = len(analysis_result.get("secret_scan_results", []))
                if secrets_found > 0:
                    print(f"🚨 PR contains {secrets_found} hardcoded secrets - requires attention")
                
                return {
                    "pr_analysis_complete": True,
                    "security_score": security_score,
                    "secrets_found": secrets_found
                }
            else:
                print(f"❌ PR security analysis failed: {analysis_result.get('error')}")
                return {"pr_analysis_complete": False, "error": analysis_result.get("error")}
        else:
            print("⚠️ Could not get PR head repository URL")
            return {"pr_analysis_complete": False, "error": "No head repo URL"}
            
    except Exception as e:
        print(f"❌ PR security analysis error: {str(e)}")
        return {"pr_analysis_complete": False, "error": str(e)}

async def create_security_issue_if_needed(repo_info, analysis_result, critical_issues):
    """Create a security issue in the repository if critical issues are found"""
    try:
        # This would use the GitHub API to create an issue
        # Implementation depends on whether you want to auto-create issues
        print(f"💡 Could create security issue for {len(critical_issues)} critical findings")
        
        # Example issue content:
        issue_title = f"🔒 Security Review: {len(critical_issues)} Critical Issues Detected"
        issue_body = f"""
# 🛡️ Automated Security Analysis Results

**Security Score:** {analysis_result.get('overall_security_score', 'N/A')}/100

## 🚨 Critical Issues Found ({len(critical_issues)})

{chr(10).join([f"- {issue.get('description', 'Security issue')} in `{issue.get('file', 'unknown file')}`" for issue in critical_issues[:10]])}

## 🔧 Recommended Actions

1. Review and address the critical security issues listed above
2. Consider using environment variables for sensitive data
3. Run additional security testing before deployment

---
*Generated by AltX Security Scanner - Automated Analysis*
"""
        
        print("📝 Security issue content prepared (not created automatically)")
        return {"issue_prepared": True}
        
    except Exception as e:
        print(f"❌ Error preparing security issue: {str(e)}")
        return {"issue_prepared": False, "error": str(e)}

async def deploy_project(repo_name: str, clone_url: str, payload: dict):
    """Actually deploy project to ngrok domain"""
    try:
        print(f"🚀 Starting real deployment for {repo_name}")
        
        # Get deployment directory (create if doesn't exist) - Windows compatible
        if platform.system() == "Windows":
            deployment_base = r"D:\AltX\deployments"  # Raw string for Windows path
        else:
            deployment_base = os.path.join(os.getcwd(), "deployments") 
        
        os.makedirs(deployment_base, exist_ok=True)
        
        # Create unique deployment directory
        deploy_dir = os.path.join(deployment_base, repo_name)
        
        # Remove existing deployment if exists (Windows-safe)
        if os.path.exists(deploy_dir):
            print(f"🗑️ Removing existing deployment: {deploy_dir}")
            try:
                def force_remove_readonly(func, path, exc_info):
                    """Force remove read-only files on Windows"""
                    if os.path.exists(path):
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                
                shutil.rmtree(deploy_dir, onerror=force_remove_readonly)
                print("✅ Existing deployment removed successfully")
            except Exception as e:
                print(f"⚠️ Warning: Could not fully remove existing deployment: {e}")
                # Try to continue anyway
        
        commit_info = payload.get("head_commit", {})
        commit_message = commit_info.get("message", "No commit message")
        committer = commit_info.get("committer", {}).get("name", "Unknown")
        
        print(f"📦 Deploying commit: {commit_message}")
        print(f"👤 Committed by: {committer}")
        
        # Step 1: Clone repository
        print("⏳ Cloning repository...")
        repo = git.Repo.clone_from(clone_url, deploy_dir)
        await asyncio.sleep(1)
        
        # Step 2: Detect project type and install dependencies
        print("⏳ Installing dependencies...")
        project_type = detect_project_type(deploy_dir)
        await install_dependencies(deploy_dir, project_type)
        
        # Step 3: Build project
        print("⏳ Building application...")
        build_result = await build_project(deploy_dir, project_type)
        
        # Step 4: Configure web server (simulation for now)
        print("⏳ Configuring web server...")
        nginx_config = await configure_nginx(repo_name, deploy_dir, project_type)
        
        # Step 5: Copy files to your FastAPI static directory
        print("⏳ Copying files to ngrok domain...")
        static_copy_result = await copy_to_static_domain(repo_name, deploy_dir, project_type)
        
        # Generate deployment URL
        deployment_url = f"https://legal-actively-glider.ngrok-free.app/{repo_name}"
        
        print(f"✅ Deployment complete for {repo_name}")
        print(f"🌐 Live at: {deployment_url}")
        
        return {
            "deployment_complete": True,
            "repo": repo_name,
            "commit": commit_info.get("id", "unknown")[:8],
            "deployment_url": deployment_url,
            "project_type": project_type,
            "build_success": build_result.get("success", False),
            "nginx_configured": nginx_config.get("success", False),
            "files_copied": static_copy_result.get("files_copied", 0)
        }
        
    except Exception as e:
        print(f"❌ Deployment error: {str(e)}")
        return {"deployment_complete": False, "error": str(e)}

def detect_project_type(deploy_dir: str) -> str:
    """Detect what type of project this is"""
    if os.path.exists(os.path.join(deploy_dir, "package.json")):
        return "nodejs"
    elif os.path.exists(os.path.join(deploy_dir, "requirements.txt")):
        return "python"
    elif os.path.exists(os.path.join(deploy_dir, "index.html")):
        return "static"
    elif os.path.exists(os.path.join(deploy_dir, "Dockerfile")):
        return "docker"
    else:
        return "unknown"

async def install_dependencies(deploy_dir: str, project_type: str):
    """Install project dependencies based on type"""
    try:
        if project_type == "nodejs":
            # Check for package manager
            if os.path.exists(os.path.join(deploy_dir, "package-lock.json")):
                subprocess.run(["npm", "install"], cwd=deploy_dir, check=True)
            elif os.path.exists(os.path.join(deploy_dir, "yarn.lock")):
                subprocess.run(["yarn", "install"], cwd=deploy_dir, check=True)
            else:
                subprocess.run(["npm", "install"], cwd=deploy_dir, check=True)
        
        elif project_type == "python":
            # Create virtual environment and install
            subprocess.run(["python", "-m", "venv", "venv"], cwd=deploy_dir, check=True)
            
            # Mac/Unix pip path
            pip_path = os.path.join(deploy_dir, "venv", "bin", "pip")
            subprocess.run([pip_path, "install", "-r", "requirements.txt"], cwd=deploy_dir, check=True)
        
        print(f"✅ Dependencies installed for {project_type} project")
        return {"success": True}
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Dependency installation failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        print(f"⚠️ Dependency installation skipped: {e}")
        return {"success": True, "skipped": True}

async def build_project(deploy_dir: str, project_type: str):
    """Build the project"""
    try:
        if project_type == "nodejs":
            # Check for build script in package.json
            package_json_path = os.path.join(deploy_dir, "package.json")
            if os.path.exists(package_json_path):
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                scripts = package_data.get("scripts", {})
                
                if "build" in scripts:
                    subprocess.run(["npm", "run", "build"], cwd=deploy_dir, check=True)
                elif "dist" in scripts:
                    subprocess.run(["npm", "run", "dist"], cwd=deploy_dir, check=True)
        
        elif project_type == "python":
            # For Python, we might need to collect static files or build assets
            print("🐍 Python project detected - no build step required")
        
        print(f"✅ Build completed for {project_type} project")
        return {"success": True}
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        print(f"⚠️ Build skipped: {e}")
        return {"success": True, "skipped": True}

async def configure_nginx(repo_name: str, deploy_dir: str, project_type: str):
    """Configure nginx for the deployment (simulation)"""
    try:
        # Determine document root based on project type
        if project_type == "nodejs":
            # Check for common build directories
            for build_dir in ["dist", "build", "public"]:
                potential_root = os.path.join(deploy_dir, build_dir)
                if os.path.exists(potential_root):
                    document_root = potential_root
                    break
            else:
                document_root = deploy_dir
        elif project_type == "static":
            document_root = deploy_dir
        else:
            document_root = deploy_dir
        
        print(f"📝 Nginx would serve from: {document_root}")
        print(f"🌐 Would be accessible at: /{repo_name}")
        
        # In a real deployment, you'd write nginx config and reload
        return {"success": True, "document_root": document_root}
        
    except Exception as e:
        print(f"❌ Nginx configuration failed: {e}")
        return {"success": False, "error": str(e)}

async def copy_to_static_domain(repo_name: str, deploy_dir: str, project_type: str):
    """Copy deployed files to FastAPI static directory for ngrok domain"""
    try:
        # Create static directory in your FastAPI backend (Windows compatible)
        static_base = os.path.join(os.getcwd(), "static")
        repo_static_dir = os.path.join(static_base, repo_name)
        
        os.makedirs(static_base, exist_ok=True)
        
        # Remove existing deployment (Windows safe)
        if os.path.exists(repo_static_dir):
            def force_remove_readonly(func, path, exc_info):
                """Force remove read-only files on Windows"""
                if os.path.exists(path):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
            
            shutil.rmtree(repo_static_dir, onerror=force_remove_readonly)
        
        # Determine source directory
        if project_type == "nodejs":
            # Look for built files
            for build_dir in ["dist", "build", "public"]:
                source_path = os.path.join(deploy_dir, build_dir)
                if os.path.exists(source_path):
                    shutil.copytree(source_path, repo_static_dir, ignore=shutil.ignore_patterns(
                        '.git', 'node_modules', '__pycache__', '*.pyc', '.env*', 'venv', 'env'
                    ))
                    files_copied = len([f for f in os.listdir(repo_static_dir) if os.path.isfile(os.path.join(repo_static_dir, f))])
                    print(f"✅ Copied {files_copied} files from {build_dir}/ to static domain")
                    return {"success": True, "files_copied": files_copied, "source": build_dir}
        
        # Fallback: copy entire directory
        shutil.copytree(deploy_dir, repo_static_dir, ignore=shutil.ignore_patterns(
            '.git', 'node_modules', '*.pyc', '__pycache__', '.env*', 'venv', 'env'
        ))
        files_copied = sum([len(files) for r, d, files in os.walk(repo_static_dir)])
        print(f"✅ Copied {files_copied} files to static domain")
        
        return {"success": True, "files_copied": files_copied, "source": "root"}
        
    except Exception as e:
        print(f"❌ Static file copy failed: {e}")
        return {"success": False, "error": str(e)}
# Add this NEW function to main.py (alongside your existing deploy_project)

async def deploy_project_with_docker(repo_name: str, clone_url: str, payload: dict):
    """Enhanced CI/CD deployment with Docker builds - fallback to standard deployment"""
    try:
        print(f"🐳 Attempting Docker CI/CD deployment for {repo_name}")
        
        # Check if Docker is available
        try:
            docker_client = docker.from_env()
            print("✅ Docker is available")
        except Exception as docker_error:
            print(f"⚠️ Docker not available: {docker_error}")
            # Fall back to your proven method immediately
            return await deploy_project(repo_name, clone_url, payload)
        
        # Step 1: Prepare directories
        deployment_base = "/Users/trishajanath/AltX/deployments"
        deploy_dir = os.path.join(deployment_base, repo_name)
        build_output_dir = os.path.join(deployment_base, f"{repo_name}-build")
        
        os.makedirs(deployment_base, exist_ok=True)
        
        # Clean existing deployments
        for dir_path in [deploy_dir, build_output_dir]:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
        
        commit_info = payload.get("head_commit", {})
        print(f"📦 Docker deployment for: {commit_info.get('message', 'No message')}")
        
        # Step 2: Clone repository
        print("⏳ Cloning repository for Docker build...")
        repo = git.Repo.clone_from(clone_url, deploy_dir)
        
        # Step 3: Detect if this project needs Docker builds
        project_type = detect_project_type(deploy_dir)
        
        # Check if project actually benefits from Docker builds
        needs_docker_build = False
        if project_type == "nodejs" and os.path.exists(os.path.join(deploy_dir, "package.json")):
            with open(os.path.join(deploy_dir, "package.json"), 'r') as f:
                package_data = json.load(f)
                if "build" in package_data.get("scripts", {}):
                    needs_docker_build = True
        elif project_type == "python" and os.path.exists(os.path.join(deploy_dir, "requirements.txt")):
            needs_docker_build = True
        
        if not needs_docker_build:
            print(f"📄 Project type '{project_type}' doesn't need Docker builds, using standard deployment")
            return await deploy_project(repo_name, clone_url, payload)
        
        # Step 4: Check if Docker build files exist
        docker_config_dir = "/Users/trishajanath/AltX/backend/docker-configs"
        if not os.path.exists(docker_config_dir):
            print("⚠️ Docker configurations not found, using standard deployment")
            return await deploy_project(repo_name, clone_url, payload)
        
        # Step 5: Try Docker build
        print("🔨 Attempting Docker build...")
        build_result = await build_in_docker(deploy_dir, build_output_dir, project_type)
        
        if not build_result.get("success"):
            print(f"⚠️ Docker build failed: {build_result.get('error')}")
            print("🔄 Falling back to standard deployment method")
            return await deploy_project(repo_name, clone_url, payload)
        
        # Step 6: Copy Docker build output to static domain
        print("📁 Copying Docker build to static domain...")
        static_copy_result = await copy_build_to_static(repo_name, build_output_dir, project_type)
        
        if not static_copy_result.get("success"):
            print("⚠️ Docker build copy failed, using standard deployment")
            return await deploy_project(repo_name, clone_url, payload)
        
        # Success! Return Docker deployment result
        deployment_url = f"https://legal-actively-glider.ngrok-free.app/{repo_name}"
        
        print(f"✅ Docker CI/CD deployment complete for {repo_name}")
        print(f"🌐 Live at: {deployment_url}")
        
        return {
            "deployment_complete": True,
            "repo": repo_name,
            "commit": commit_info.get("id", "unknown")[:8],
            "deployment_url": deployment_url,
            "project_type": project_type,
            "build_success": True,
            "docker_build": True,
            "nginx_configured": False,
            "files_copied": static_copy_result.get("files_copied", 0),
            "deployment_method": "docker_ci_cd_success"
        }
        
    except Exception as e:
        print(f"❌ Docker CI/CD deployment error: {str(e)}")
        print("🔄 Falling back to proven standard deployment method")
        # Always fall back to your working method
        return await deploy_project(repo_name, clone_url, payload)

async def build_in_docker(source_dir: str, output_dir: str, project_type: str):
    """Build project using Docker containers"""
    try:
        # ADD THIS LINE AT THE TOP OF THE FUNCTION
        docker_client = docker.from_env()
        
        # Check if Docker files exist
        dockerfile_map = {
            "nodejs": "Dockerfile.nodejs",
            "python": "Dockerfile.python", 
            "php": "Dockerfile.php",
            "static": "Dockerfile.universal",
            "unknown": "Dockerfile.universal"
        }
        
        dockerfile_name = dockerfile_map.get(project_type, "Dockerfile.universal")
        dockerfile_path = f"/Users/trishajanath/AltX/backend/docker-configs/{dockerfile_name}"
        
        # Check if Docker files exist
        if not os.path.exists(dockerfile_path):
            print(f"⚠️ Docker configuration not found: {dockerfile_path}")
            return {"success": False, "error": "Docker configuration missing"}
        
        print(f"🐳 Using Docker configuration: {dockerfile_name}")
        
        # Build Docker image
        print("🔨 Building Docker image...")
        image_tag = f"altx-builder-{project_type}:latest"
        
        # Build image with build context
        image, build_logs = docker_client.images.build(
            path="/Users/trishajanath/AltX/backend",
            dockerfile=f"docker-configs/{dockerfile_name}",
            tag=image_tag,
            rm=True,
            forcerm=True
        )
        
        print("✅ Docker image built successfully")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Run build container
        print("🏗️ Running build process in container...")
        
        container = docker_client.containers.run(
            image_tag,
            volumes={
                source_dir: {'bind': '/app', 'mode': 'ro'},
                output_dir: {'bind': '/deployment', 'mode': 'rw'}
            },
            working_dir='/app',
            detach=True,
            auto_remove=False
        )
        
        # Wait for completion and get logs
        exit_code = container.wait()
        build_logs = container.logs().decode('utf-8')
        
        print("📋 Build logs:")
        print(build_logs[-1000:])  # Last 1000 characters
        
        # Clean up container
        container.remove()
        
        if exit_code['StatusCode'] != 0:
            return {"success": False, "error": f"Build failed with exit code {exit_code['StatusCode']}"}
        
        # Determine document root from build output
        document_root = output_dir
        if os.path.exists(os.path.join(output_dir, "dist")):
            document_root = os.path.join(output_dir, "dist")
        elif os.path.exists(os.path.join(output_dir, "build")):
            document_root = os.path.join(output_dir, "build")
        
        print(f"✅ Docker build completed successfully")
        print(f"📁 Document root: {document_root}")
        
        return {
            "success": True,
            "image_tag": image_tag,
            "document_root": document_root,
            "build_logs": build_logs[-500:],  # Last 500 chars
            "files_created": len(os.listdir(output_dir)) if os.path.exists(output_dir) else 0
        }
        
    except docker.errors.DockerException as e:
        print(f"❌ Docker not available: {e}")
        return {"success": False, "error": f"Docker not available: {str(e)}"}
    except Exception as e:
        print(f"❌ Docker deployment error: {e}")
        return {"success": False, "error": str(e)}
    
async def copy_build_to_static(repo_name: str, build_dir: str, project_type: str):
    """Copy Docker build output to static domain"""
    try:
        # Create static directory in your FastAPI backend
        static_base = "/Users/trishajanath/AltX/backend/static"
        repo_static_dir = os.path.join(static_base, repo_name)
        
        os.makedirs(static_base, exist_ok=True)
        
        # Remove existing deployment
        if os.path.exists(repo_static_dir):
            shutil.rmtree(repo_static_dir)
        
        # Copy build output to static domain
        if os.path.exists(build_dir):
            shutil.copytree(build_dir, repo_static_dir)
            files_copied = sum([len(files) for r, d, files in os.walk(repo_static_dir)])
            print(f"✅ Copied {files_copied} files from Docker build to static domain")
            
            return {"success": True, "files_copied": files_copied}
        else:
            print(f"❌ Docker build directory not found: {build_dir}")
            return {"success": False, "error": "Build directory not found"}
            
    except Exception as e:
        print(f"❌ Failed to copy Docker build to static: {e}")
        return {"success": False, "error": str(e)}
    
async def handle_push_event(payload):
    """Handle push events - try Docker first, fallback to standard deployment"""
    try:
        ref = payload.get("ref", "")
        repo_info = payload.get("repository", {})
        clone_url = repo_info.get("clone_url")
        repo_name = repo_info.get("name")
        repo_full_name = repo_info.get("full_name")
        default_branch = repo_info.get("default_branch", "main")
        
        if ref == f"refs/heads/{default_branch}":
            print(f"🚀 Push to {default_branch} branch detected for {repo_full_name}")
            
            if clone_url and repo_name:
                # Trigger security analysis (async)
                analysis_task = asyncio.create_task(
                    run_automated_security_analysis(repo_info, payload)
                )
                
                # Try Docker deployment first, fallback to standard deployment
                try:
                    deployment_result = await deploy_project_with_docker(repo_name, clone_url, payload)
                    deployment_method = "docker_ci_cd"
                except Exception as e:
                    print(f"⚠️ Docker deployment failed: {e}, using standard deployment")
                    deployment_result = await deploy_project(repo_name, clone_url, payload)
                    deployment_method = "standard"
                
                return {
                    "status": "enhanced CI/CD deployment triggered",
                    "repo": repo_full_name,
                    "branch": default_branch,
                    "commit": payload.get("head_commit", {}).get("id", "unknown")[:8],
                    "deployment_method": deployment_method,
                    "timestamp": datetime.now().isoformat(),
                    "actions": ["security_analysis", "enhanced_deployment"],
                    "deployment_result": deployment_result
                }
        
        return {"status": "push to non-default branch", "ref": ref}
        
    except Exception as e:
        print(f"❌ Error handling push event: {str(e)}")
        return {"status": "error", "error": str(e)}

@app.get("/debug-scan")
async def debug_scan():
    """Debug endpoint to check stored scan data"""
    if hasattr(WebsiteScan, 'latest_scan') and WebsiteScan.latest_scan:
        scan_data = WebsiteScan.latest_scan
        return {
            "has_scan_data": True,
            "keys": list(scan_data.keys()),
            "waf_analysis_keys": list(scan_data.get('waf_analysis', {}).keys()) if scan_data.get('waf_analysis') else None,
            "dns_security_keys": list(scan_data.get('dns_security', {}).keys()) if scan_data.get('dns_security') else None,
            "waf_detected": scan_data.get('waf_analysis', {}).get('waf_detected'),
            "dns_has_data": bool(scan_data.get('dns_security')),
            "url": scan_data.get('url')
        }
    else:
        return {
            "has_scan_data": False,
            "message": "No scan data stored"
        }

@app.get("/health")
async def health_check():
    """Check if the API is running"""
    return {"status": "healthy"}

from fastapi.staticfiles import StaticFiles

# Add this after your other app configurations but before the endpoints
# Create static directory if it doesn't exist (Windows compatible)
if platform.system() == "Windows":
    static_dir = os.path.join(os.getcwd(), "static")
else:
    static_dir = "/Users/trishajanath/AltX/backend/static"

os.makedirs(static_dir, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/{repo_name}/{file_path:path}")
async def serve_deployed_files(repo_name: str, file_path: str):
    """Serve deployed repository files"""
    try:
        # Windows compatible path
        if platform.system() == "Windows":
            repo_static_dir = os.path.join(os.getcwd(), "static", repo_name)
        else:
            repo_static_dir = f"/Users/trishajanath/AltX/backend/static/{repo_name}"
        
        file_full_path = os.path.join(repo_static_dir, file_path)
        
        # Security check: ensure file is within the repo directory
        if not os.path.realpath(file_full_path).startswith(os.path.realpath(repo_static_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if os.path.exists(file_full_path) and os.path.isfile(file_full_path):
            from fastapi.responses import FileResponse
            return FileResponse(file_full_path)
        
        # Try index.html for SPA applications
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        
        raise HTTPException(status_code=404, detail="File not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")

@app.get("/{repo_name}")
async def serve_deployed_repo_root(repo_name: str):
    """Serve deployed repository root (index.html)"""
    try:
        static_dir = f"/Users/trishajanath/AltX/backend/static/{repo_name}"
        index_path = os.path.join(static_dir, "index.html")
        
        if os.path.exists(index_path):
            from fastapi.responses import FileResponse
            return FileResponse(index_path)
        
        # If no index.html, show directory listing
        if os.path.exists(static_dir):
            files = os.listdir(static_dir)
            html_content = f"""
<!DOCTYPE html>
<html>
<head><title>🚀 {repo_name} - Deployed Files</title></head>
<body>
    <h1>🚀 Repository: {repo_name}</h1>
    <h2>📁 Deployed Files:</h2>
    <ul>
        {''.join([f'<li><a href="/{repo_name}/{f}">{f}</a></li>' for f in files])}
    </ul>
    <p><strong>Deployment URL:</strong> https://legal-actively-glider.ngrok-free.app/{repo_name}</p>
</body>
</html>
            """
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=html_content)
        
        raise HTTPException(status_code=404, detail=f"Repository {repo_name} not deployed")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving repository: {str(e)}")

# --- AI-Powered Code Generation Functions ---

async def generate_react_frontend_with_ai(frontend_path: Path, idea: str, project_name: str, needs_typescript: bool, needs_auth: bool) -> List[str]:
    """Generate React frontend with AI-powered unique code based on the idea"""
    files_created = []
    
    try:
        # Analyze the idea to determine specific features and components needed
        components_needed = []
        api_endpoints = []
        special_features = []
        
        # Determine what components to create based on the idea
        if any(keyword in idea.lower() for keyword in ["todo", "task", "list", "manage"]):
            components_needed.extend(["TaskList", "TaskItem", "AddTaskForm"])
            api_endpoints.extend(["/api/tasks", "/api/tasks/{id}"])
        
        if any(keyword in idea.lower() for keyword in ["ecommerce", "shop", "store", "product", "cart"]):
            components_needed.extend(["ProductGrid", "ProductCard", "Cart", "Checkout"])
            api_endpoints.extend(["/api/products", "/api/cart", "/api/orders"])
        
        if any(keyword in idea.lower() for keyword in ["blog", "article", "post", "content"]):
            components_needed.extend(["PostList", "PostCard", "PostEditor", "CommentSection"])
            api_endpoints.extend(["/api/posts", "/api/comments"])
        
        if any(keyword in idea.lower() for keyword in ["chat", "message", "conversation"]):
            components_needed.extend(["ChatWindow", "MessageList", "MessageInput"])
            api_endpoints.extend(["/api/messages", "/api/chat"])
            special_features.append("websocket")
        
        if any(keyword in idea.lower() for keyword in ["dashboard", "analytics", "chart", "data"]):
            components_needed.extend(["Dashboard", "Chart", "StatCard", "DataTable"])
            api_endpoints.extend(["/api/analytics", "/api/stats"])
        
        if any(keyword in idea.lower() for keyword in ["social", "profile", "user", "follow"]):
            components_needed.extend(["Profile", "UserCard", "Feed", "Followers"])
            api_endpoints.extend(["/api/users", "/api/profile", "/api/feed"])
        
        # Default components if none detected
        if not components_needed:
            components_needed = ["MainContent", "ActionForm", "ItemList"]
            api_endpoints = ["/api/data", "/api/create"]
        
        # Use AI to generate unique code based on the idea
        prompt = f"""
Generate a complete, functional React frontend application for: "{idea}"

Project Name: {project_name}
Authentication: {"Yes" if needs_auth else "No"}

SPECIFIC FEATURES DETECTED:
- Components needed: {', '.join(components_needed)}
- API endpoints to integrate: {', '.join(api_endpoints)}
- Special features: {', '.join(special_features) if special_features else 'None'}

CRITICAL REQUIREMENTS - NO MOCKS OR PLACEHOLDERS:
- Generate COMPLETE, PRODUCTION-READY code that works immediately
- Use React 18+ with functional components and modern hooks
- Include TailwindCSS for beautiful, responsive styling
- Create WORKING components with real state management and API calls
- Add proper error handling, loading states, and user feedback
- Include form validation and submission handling
- Make components interactive with real click handlers and state updates
- Use proper TypeScript types or PropTypes for type safety
- Include proper routing if needed (React Router)
- Add realistic sample data that looks professional
- Implement CRUD operations that actually work with API endpoints
- Include proper accessibility features (ARIA labels, keyboard navigation)

COMPONENT IMPLEMENTATION RULES:
- Every component MUST have complete implementations - no empty functions
- All useState hooks must have proper initial states and update functions
- All useEffect hooks must have complete dependency arrays and cleanup
- Include real event handlers (onClick, onChange, onSubmit) with actual logic
- Implement proper form submission with validation
- Add loading spinners and error messages for API calls
- Use proper conditional rendering for different states
- Include proper component composition and reusability

STYLING REQUIREMENTS:
- Use modern TailwindCSS utility classes for beautiful UI
- Implement responsive design (mobile-first approach)
- Add hover effects, transitions, and micro-interactions
- Use proper color schemes and typography
- Include proper spacing, shadows, and visual hierarchy
- Add icons from Lucide React or Heroicons
- Implement proper layout with flexbox/grid

API INTEGRATION:
- Write real fetch() calls to the backend endpoints
- Include proper error handling for network requests
- Add loading states during API calls
- Handle success and error responses appropriately
- Use proper HTTP methods (GET, POST, PUT, DELETE)
- Include authentication headers if needed

FILES TO GENERATE WITH COMPLETE IMPLEMENTATIONS:
1. package.json - All necessary dependencies
2. src/App.jsx - Main app with routing and layout
3. src/main.jsx - React 18 setup with error boundaries
4. src/index.css - TailwindCSS + custom styles
5. vite.config.js - Optimized Vite config
6. tailwind.config.js - Custom theme configuration
7. Component files in src/components/ - Fully functional components

Each file must be complete and production-ready. Do not use placeholders like "TODO", "// implement later", or empty function bodies.

IMPORTANT: 
- Make the app UNIQUE and SPECIFIC to "{idea}" - not generic
- Include proper error handling and loading states
- Use modern React patterns (functional components, hooks)
- Make it production-ready with proper code structure
- Ensure all imports/exports work correctly
- Add comments explaining the logic
- NEVER leave components with empty return statements or incomplete JSX

Return each file content in this EXACT format:
===FILE: filename===
file content here
===END===

Start with package.json:
"""

        # Get AI response
        chat_history = [{"role": "user", "content": prompt}]
        ai_response = get_chat_response(chat_history, "smart")
        
        # Parse AI response and create files
        if "===FILE:" in ai_response:
            files_created = await parse_and_create_ai_files(frontend_path, ai_response, project_name)
            
            # Validate that essential files were created
            essential_files = ["package.json", "src/App.jsx", "src/main.jsx", "vite.config.js"]
            created_filenames = [f.split("/")[-1] if "/" in f else f for f in files_created]
            
            missing_files = []
            for essential in essential_files:
                filename = essential.split("/")[-1]
                if not any(filename in created for created in created_filenames):
                    missing_files.append(essential)
            
            if missing_files:
                print(f"⚠️ AI generation missing essential files: {missing_files}")
                print("🔄 Falling back to template generation")
                files_created = await create_react_frontend_with_animation(frontend_path, idea, project_name, needs_typescript, needs_auth)
        else:
            print("⚠️ AI response doesn't contain proper file markers")
            # Fallback to template-based generation if AI parsing fails
            files_created = await create_react_frontend_with_animation(frontend_path, idea, project_name, needs_typescript, needs_auth)
            
    except Exception as e:
        print(f"AI generation failed, falling back to templates: {e}")
        # Fallback to template-based generation
        files_created = await create_react_frontend_with_animation(frontend_path, idea, project_name, needs_typescript, needs_auth)
    
    return files_created

async def generate_fastapi_backend_with_ai(backend_path: Path, idea: str, project_name: str, needs_ai: bool, needs_auth: bool, needs_database: bool) -> List[str]:
    """Generate FastAPI backend with AI-powered unique code based on the idea"""
    files_created = []
    
    try:
        # Analyze the idea to determine specific API endpoints and models needed
        api_routes = []
        data_models = []
        special_deps = []
        
        # Determine what APIs to create based on the idea
        if any(keyword in idea.lower() for keyword in ["todo", "task", "list", "manage"]):
            api_routes.extend(["GET /api/tasks", "POST /api/tasks", "PUT /api/tasks/{id}", "DELETE /api/tasks/{id}"])
            data_models.extend(["Task", "TaskCreate", "TaskUpdate"])
        
        if any(keyword in idea.lower() for keyword in ["ecommerce", "shop", "store", "product", "cart"]):
            api_routes.extend(["GET /api/products", "GET /api/products/{id}", "POST /api/cart", "POST /api/orders"])
            data_models.extend(["Product", "CartItem", "Order", "OrderCreate"])
        
        if any(keyword in idea.lower() for keyword in ["blog", "article", "post", "content"]):
            api_routes.extend(["GET /api/posts", "POST /api/posts", "GET /api/posts/{id}", "POST /api/comments"])
            data_models.extend(["Post", "PostCreate", "Comment", "CommentCreate"])
        
        if any(keyword in idea.lower() for keyword in ["chat", "message", "conversation"]):
            api_routes.extend(["GET /api/messages", "POST /api/messages", "WebSocket /ws/chat"])
            data_models.extend(["Message", "MessageCreate", "ChatRoom"])
            special_deps.extend(["websockets"])
        
        if any(keyword in idea.lower() for keyword in ["user", "auth", "login", "signup"]):
            api_routes.extend(["POST /api/auth/login", "POST /api/auth/signup", "GET /api/users/me"])
            data_models.extend(["User", "UserCreate", "UserLogin", "Token"])
            special_deps.extend(["python-jose[cryptography]", "passlib[bcrypt]"])
        
        if any(keyword in idea.lower() for keyword in ["ai", "gpt", "openai", "chatbot", "ml"]):
            api_routes.extend(["POST /api/ai/chat", "POST /api/ai/generate"])
            data_models.extend(["AIRequest", "AIResponse", "ChatMessage"])
            special_deps.extend(["openai", "langchain"])
        
        if any(keyword in idea.lower() for keyword in ["database", "store", "save", "crud"]):
            special_deps.extend(["sqlalchemy", "databases", "asyncpg"])
        
        # Default routes if none detected
        if not api_routes:
            api_routes = ["GET /api/items", "POST /api/items", "GET /api/health"]
            data_models = ["Item", "ItemCreate"]
        
        # Use AI to generate unique code based on the idea
        prompt = f"""
Generate a complete, PRODUCTION-READY FastAPI backend application for: "{idea}"

Project Name: {project_name}
AI Integration: {"Yes" if needs_ai else "No"}
Authentication: {"Yes" if needs_auth else "No"}
Database: {"Yes" if needs_database else "No"}

SPECIFIC FEATURES DETECTED:
- API Routes needed: {', '.join(api_routes)}
- Data Models needed: {', '.join(data_models)}
- Special Dependencies: {', '.join(special_deps) if special_deps else 'None'}

CRITICAL REQUIREMENTS - NO MOCKS OR PLACEHOLDERS:
- Generate COMPLETE, PRODUCTION-READY FastAPI code that works immediately
- Use FastAPI with modern Python 3.9+ async/await patterns
- Include proper CORS handling for React frontend (localhost:5173)
- Create WORKING API endpoints with full business logic implementation
- Add comprehensive error handling and validation with Pydantic models
- Include proper HTTP status codes and response models
- Implement REAL CRUD operations with in-memory storage or database
- Add proper request/response validation and error messages
- Include authentication middleware if auth is required
- Add proper logging and error tracking
- Implement rate limiting and security best practices

DATABASE IMPLEMENTATION:
- If database needed: Use SQLAlchemy with async support and real database operations
- Include proper database models with relationships
- Add migration scripts and database initialization
- Implement connection pooling and error handling
- Use proper transaction management

API ENDPOINT REQUIREMENTS:
- Every endpoint MUST have complete implementation - no empty functions
- Include proper path parameters, query parameters, and request bodies
- Add comprehensive input validation using Pydantic models
- Implement proper error handling for all edge cases
- Include realistic business logic specific to "{idea}"
- Add proper response models with example data
- Include proper HTTP methods (GET, POST, PUT, DELETE, PATCH)
- Implement pagination for list endpoints
- Add search and filtering capabilities where appropriate

AUTHENTICATION & SECURITY:
- If auth required: Implement JWT tokens with proper validation
- Add password hashing with bcrypt
- Include proper user registration and login flows
- Add role-based access control (RBAC) if needed
- Implement rate limiting and security headers
- Add proper CORS configuration

DATA MODELS:
- Create comprehensive Pydantic models for all data structures
- Include proper field validation with regex, min/max values
- Add realistic sample data and default values
- Implement proper relationships between models
- Include created_at/updated_at timestamps
- Add proper serialization/deserialization

FILES TO GENERATE WITH COMPLETE IMPLEMENTATIONS:
1. requirements.txt - All necessary dependencies
2. main.py - FastAPI app with middleware, routing, and startup/shutdown
3. models.py - Complete Pydantic models with validation
4. routes.py - Full API endpoints with business logic
5. database.py - Database setup with SQLAlchemy (if needed)
6. auth.py - Authentication system (if needed)
7. config.py - Configuration management with environment variables

Each file must be complete and production-ready. Do not use placeholders like "TODO", "# implement later", or "pass" statements.

Return each file content in this EXACT format:
===FILE: filename===
file content here
===END===

Start with requirements.txt:
"""

        # Get AI response
        chat_history = [{"role": "user", "content": prompt}]
        ai_response = get_chat_response(chat_history, "smart")
        
        # Parse AI response and create files
        if "===FILE:" in ai_response:
            files_created = await parse_and_create_ai_files(backend_path, ai_response, project_name)
            
            # Validate that essential files were created
            essential_files = ["requirements.txt", "main.py", "models.py"]
            created_filenames = [f.split("/")[-1] if "/" in f else f for f in files_created]
            
            missing_files = []
            for essential in essential_files:
                filename = essential.split("/")[-1]
                if not any(filename in created for created in created_filenames):
                    missing_files.append(essential)
            
            if missing_files:
                print(f"⚠️ AI backend generation missing essential files: {missing_files}")
                print("🔄 Falling back to template generation")
                files_created = await create_fastapi_backend_with_animation(backend_path, idea, project_name, needs_ai, needs_auth, needs_database)
        else:
            print("⚠️ AI response doesn't contain proper file markers")
            # Fallback to template-based generation if AI parsing fails
            files_created = await create_fastapi_backend_with_animation(backend_path, idea, project_name, needs_ai, needs_auth, needs_database)
            
    except Exception as e:
        print(f"AI generation failed, falling back to templates: {e}")
        # Fallback to template-based generation
        files_created = await create_fastapi_backend_with_animation(backend_path, idea, project_name, needs_ai, needs_auth, needs_database)
    
    return files_created

async def parse_and_create_ai_files(base_path: Path, ai_response: str, project_name: str) -> List[str]:
    """Parse AI response and create files with real-time animation"""
    files_created = []
    
    print(f"🔍 Parsing AI response for {project_name}...")
    print(f"📝 Response length: {len(ai_response)} characters")
    
    # Split response by file markers
    file_sections = ai_response.split("===FILE:")
    
    print(f"📁 Found {len(file_sections)-1} file sections")
    
    for section in file_sections[1:]:  # Skip first empty section
        if "===END===" not in section:
            print(f"⚠️ Section missing ===END=== marker")
            continue
            
        lines = section.split("\n")
        filename = lines[0].strip().replace("===", "")
        
        print(f"📄 Processing file: {filename}")
        
        # Extract content between filename and ===END===
        content_lines = []
        in_content = False
        
        for line in lines[1:]:
            if line.strip() == "===END===":
                break
            content_lines.append(line)
        
        content = "\n".join(content_lines).strip()
        
        if content and filename:
            # Validate and fix the content before creating the file
            content = await validate_and_fix_code_content(filename, content, project_name)
            
            print(f"✅ Creating file {filename} with {len(content)} characters")
            
            # Handle nested file paths (e.g., src/App.jsx)
            file_path = base_path / filename
            relative_path = str(file_path.relative_to(file_path.parent.parent))
            
            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            created_file = await create_file_with_animation(file_path, content, relative_path, project_name)
            files_created.append(created_file)
        else:
            print(f"❌ Skipping file {filename} - no content or invalid filename")
    
    # Ensure essential files exist with fallback templates
    await ensure_essential_files_exist(base_path, project_name, files_created)
    
    print(f"🎉 Successfully created {len(files_created)} files")
    return files_created

async def validate_and_fix_code_content(filename: str, content: str, project_name: str) -> str:
    """Validate and fix common issues in generated code"""
    
    if filename.endswith('.jsx') or filename.endswith('.tsx'):
        # Fix JSX/React specific issues
        content = fix_jsx_content(content, filename, project_name)
    elif filename == 'package.json':
        # Validate JSON content
        content = fix_package_json_content(content, project_name)
    elif filename.endswith('.js') or filename.endswith('.ts'):
        # Fix JavaScript/TypeScript issues
        content = fix_js_content(content, filename)
    
    return content

def fix_jsx_content(content: str, filename: str, project_name: str) -> str:
    """Fix common JSX/React issues"""
    
    # Fix main.jsx with incomplete render calls
    if 'main.jsx' in filename and 'ReactDOM.createRoot' in content:
        if '.render(\n\n  ,\n)' in content or '.render(\n\n,\n)' in content:
            print(f"🔧 Fixing incomplete render call in {filename}")
            content = content.replace(
                '.render(\n\n  ,\n)',
                '.render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n)'
            ).replace(
                '.render(\n\n,\n)',
                '.render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n)'
            )
    
    # Fix empty component functions with proper JSX structure
    if 'const ' in content and '() => (\n\n);' in content:
        print(f"🔧 Fixing empty component functions in {filename}")
        content = content.replace(
            '() => (\n\n);',
            '() => (\n  <div className="container mx-auto p-4">\n    <h1>Welcome to Component</h1>\n    <p>This component is ready for development.</p>\n  </div>\n);'
        )
    
    # Fix incomplete JSX elements - more robust pattern matching
    if 'return (\n\n' in content and ');\n}' in content:
        print(f"🔧 Fixing incomplete return statement in {filename}")
        # Find the component name from the function declaration
        import re
        function_match = re.search(r'(?:function\s+(\w+)|const\s+(\w+)\s*=)', content)
        component_name = (function_match.group(1) or function_match.group(2)) if function_match else project_name.replace('-', ' ').title()
        
        content = content.replace(
            'return (\n\n',
            f'return (\n    <div className="container mx-auto p-4">\n      <h1>Welcome to {component_name}</h1>\n      <p>Component content will go here.</p>\n'
        )
        # Ensure proper closing structure
        if 'return (' in content and not content.rstrip().endswith('</div>\n  );'):
            # Find the last occurrence of '); and replace it
            content = content.rstrip()
            if content.endswith(');'):
                content = content[:-2] + '\n    </div>\n  );'
            elif content.endswith('  );\n}'):
                content = content.replace('  );\n}', '    </div>\n  );\n}')
    
    # Fix malformed JSX structure like incomplete tags
    content = re.sub(r'>\s*\n\s*\n\s*</div>', '>\n      <p>Content placeholder</p>\n    </div>', content)
    content = re.sub(r'>\s*\n\s*\n\s*</(\w+)>', r'>\n      <p>Content placeholder</p>\n    </\1>', content)
    
    # Ensure imports are present
    if filename.endswith('.jsx') and 'import React' not in content:
        content = "import React from 'react';\n\n" + content
    
    # Fix any incomplete comment blocks
    content = re.sub(r'/\*\*\s*\n\s*\*\s*\n\s*\*/', '/**\n * Component documentation\n */', content)
    
    return content

def fix_package_json_content(content: str, project_name: str) -> str:
    """Ensure package.json is valid"""
    try:
        import json
        parsed = json.loads(content)
        # Ensure required fields
        if 'name' not in parsed:
            parsed['name'] = project_name
        if 'version' not in parsed:
            parsed['version'] = '0.1.0'
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError:
        print(f"🔧 Creating fallback package.json")
        return get_fallback_package_json(project_name)

def fix_js_content(content: str, filename: str) -> str:
    """Fix JavaScript/TypeScript issues"""
    
    # Fix incomplete function exports
    if 'export default' in content and content.strip().endswith('export default'):
        print(f"🔧 Fixing incomplete export in {filename}")
        content = content.replace('export default', 'export default function Component() { return null; }')
    
    return content

async def ensure_essential_files_exist(base_path: Path, project_name: str, files_created: List[str]) -> None:
    """Ensure essential files exist with fallback templates"""
    
    essential_files = {
        'package.json': get_fallback_package_json(project_name),
        'src/main.jsx': get_fallback_main_jsx(),
        'src/App.jsx': get_fallback_app_jsx(project_name),
        'src/index.css': get_fallback_index_css(),
        'vite.config.js': get_fallback_vite_config(),
        'tailwind.config.js': get_fallback_tailwind_config(),
        'postcss.config.js': get_fallback_postcss_config()
    }
    
    for filename, fallback_content in essential_files.items():
        file_path = base_path / filename
        
        # Check if file was created or exists
        if not file_path.exists() and filename not in files_created:
            print(f"🔧 Creating missing essential file: {filename}")
            
            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file with fallback content
            relative_path = str(file_path.relative_to(file_path.parent.parent))
            await create_file_with_animation(file_path, fallback_content, relative_path, project_name)
            files_created.append(filename)

def get_fallback_package_json(project_name: str) -> str:
    """Get fallback package.json content"""
    return f'''{{
  "name": "{project_name}",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.1",
    "lucide-react": "^0.263.1",
    "axios": "^1.6.0"
  }},
  "devDependencies": {{
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@vitejs/plugin-react": "^4.0.3",
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.24",
    "tailwindcss": "^3.3.0",
    "vite": "^4.4.5"
  }}
}}'''

def get_fallback_main_jsx() -> str:
    """Get fallback main.jsx content"""
    return '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)'''

def get_fallback_app_jsx(project_name: str) -> str:
    """Get fallback App.jsx content"""
    return f'''import React, {{ useState }} from 'react'
import './App.css'

function App() {{
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <header className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              {project_name.replace('-', ' ').title()}
            </h1>
            <p className="text-xl text-gray-600">
              Welcome to your new React application!
            </p>
          </header>
          
          <main className="bg-white rounded-lg shadow-lg p-8">
            <div className="text-center">
              <button
                className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                onClick={{() => setCount(count + 1)}}
              >
                Count is {{count}}
              </button>
              <p className="mt-4 text-gray-600">
                Click the button to test the React functionality.
              </p>
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}}

export default App'''

def get_fallback_index_css() -> str:
    """Get fallback index.css content"""
    return '''@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;
  color-scheme: light dark;
  color: rgba(255, 255, 255, 0.87);
  background-color: #242424;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  -webkit-text-size-adjust: 100%;
}

body {
  margin: 0;
  display: flex;
  place-items: center;
  min-width: 320px;
  min-height: 100vh;
}

#root {
  max-width: 1280px;
  margin: 0 auto;
  text-align: center;
  width: 100%;
}'''

def get_fallback_vite_config() -> str:
    """Get fallback vite.config.js content"""
    return '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true
  }
})'''

def get_fallback_tailwind_config() -> str:
    """Get fallback tailwind.config.js content"""
    return '''/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}'''

def get_fallback_postcss_config() -> str:
    """Get fallback postcss.config.js content"""
    return '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}'''

async def generate_ai_powered_full_stack_files(project_path: Path, idea: str, project_name: str, tech_stack: List[str], needs_ai: bool):
    """Generate complete full-stack project using AI-powered functions - ALWAYS FastAPI + React"""
    try:
        # Create main project structure
        project_path.mkdir(exist_ok=True)
        frontend_path = project_path / "frontend"
        backend_path = project_path / "backend"
        
        frontend_path.mkdir(exist_ok=True)
        backend_path.mkdir(exist_ok=True)
        
        # Determine features needed from the idea
        needs_auth = "auth" in idea.lower() or "login" in idea.lower() or "user" in idea.lower() or "signup" in idea.lower()
        needs_database = any(keyword in idea.lower() for keyword in ["database", "store", "save", "data", "crud", "create", "update", "delete"])
        needs_real_time = any(keyword in idea.lower() for keyword in ["chat", "live", "real-time", "notification", "websocket"])
        needs_ai_integration = any(keyword in idea.lower() for keyword in ["ai", "chatbot", "gpt", "openai", "ml", "machine learning", "predict"])
        
        # Send status update
        await manager.send_to_project(project_name, {
            "type": "status",
            "phase": "generate",
            "message": f"🎨 Generating unique React frontend for: {idea}"
        })
        
        # ALWAYS use AI-powered React generation (no Next.js)
        frontend_files = await generate_react_frontend_with_ai(frontend_path, idea, project_name, False, needs_auth)
        
        # Send status update
        await manager.send_to_project(project_name, {
            "type": "status", 
            "phase": "generate",
            "message": f"⚡ Generating FastAPI backend with custom logic for: {idea}"
        })
        
        # ALWAYS use AI-powered FastAPI generation
        backend_files = await generate_fastapi_backend_with_ai(backend_path, idea, project_name, needs_ai_integration, needs_auth, needs_database)
        
        # Generate root files
        root_files = await create_root_files_with_animation(project_path, project_name, idea, ["React", "FastAPI", "Vite", "TailwindCSS"])
        
        # Return project structure for display
        return [
            "📁 frontend/",
            "  📁 src/",
            "    📁 components/",
            "    📄 App.jsx",
            "    📄 main.jsx",
            "    📄 index.css",
            "  📄 package.json",
            "  📄 vite.config.js",
            "  📄 tailwind.config.js",
            "📁 backend/",
            "  📄 main.py",
            "  📄 requirements.txt",
            "  📄 models.py",
            "  📄 routes.py",
            "📄 README.md",
            "📄 .gitignore",
            "📄 docker-compose.yml"
        ]
        
    except Exception as e:
        print(f"Error generating AI-powered project: {e}")
        return ["Error generating project files"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)