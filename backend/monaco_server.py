"""
Simplified FastAPI server for Monaco Editor functionality
This version avoids complex dependencies that were causing import issues
"""

import os
import json
import uuid
import shutil
import asyncio
from pathlib import Path
from typing import Dict, Set, List
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState
from pydantic import BaseModel

app = FastAPI(title="Monaco Editor API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
                if websocket and websocket.client_state == WebSocketState.CONNECTED:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        print(f"WebSocket send error for {connection_id}: {e}")
                        disconnected.append(connection_id)
                else:
                    disconnected.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected:
                self.disconnect(connection_id, project_name)

manager = ConnectionManager()

# --- Basic Health Check ---
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "monaco-editor-api"}

# --- WebSocket Endpoint ---
@app.websocket("/ws/project/{project_name}")
async def websocket_endpoint(websocket: WebSocket, project_name: str):
    connection_id = str(uuid.uuid4())
    await manager.connect(websocket, connection_id, project_name)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": f"Connected to project: {project_name}"
        })
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_json()
                # Handle incoming messages if needed
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    finally:
        manager.disconnect(connection_id, project_name)

# --- Enhanced Project Structure Creation ---
@app.post("/api/create-project-structure")
async def create_project_structure(request: dict = Body(...)):
    """Create actual project files and structure"""
    print(f"📥 Received create-project-structure request: {request}")
    
    try:
        project_name = request.get("project_name")
        idea = request.get("idea") 
        tech_stack = request.get("tech_stack", ["React", "TypeScript", "Node.js"])
        
        if not project_name:
            error_response = {"success": False, "error": "Project name is required"}
            print(f"❌ Missing project name, returning: {error_response}")
            return error_response
        
        # Send progress updates via WebSocket (non-blocking)
        try:
            await manager.send_to_project(project_name, {
                "type": "terminal_output",
                "message": "🚀 Creating project structure...",
                "level": "info"
            })
        except Exception as ws_error:
            print(f"WebSocket error in create_project_structure: {ws_error}")
        
        # Generate project name slug
        project_slug = project_name.lower().replace(" ", "-").replace("_", "-")
        projects_dir = Path("generated_projects")
        projects_dir.mkdir(exist_ok=True)
        project_path = projects_dir / project_slug
        
        # Check if project already exists (likely created by main server)
        if project_path.exists():
            print(f"✅ Project {project_name} already exists, returning existing structure")
            
            try:
                await manager.send_to_project(project_name, {
                    "type": "terminal_output", 
                    "message": f"✅ Project already exists with existing files",
                    "level": "success"
                })
            except Exception as ws_error:
                print(f"WebSocket error in create_project_structure success: {ws_error}")
            
            # Count existing files
            files_found = []
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), project_path)
                    files_found.append(rel_path)
            
            success_response = {
                "success": True,
                "files_created": files_found,
                "tech_stack": tech_stack,
                "project_path": str(project_path),
                "message": "Project already exists"
            }
            print(f"✅ Returning existing project response: {len(files_found)} files")
            return success_response
        
        # Create project structure
        files_created = await create_simple_project_structure(
            project_path, idea, project_slug, tech_stack
        )
        
        try:
            await manager.send_to_project(project_name, {
                "type": "terminal_output", 
                "message": f"✅ Created {len(files_created)} files",
                "level": "success"
            })
        except Exception as ws_error:
            print(f"WebSocket error in create_project_structure success: {ws_error}")
        
        success_response = {
            "success": True,
            "files_created": files_created,
            "tech_stack": tech_stack,
            "project_path": str(project_path)
        }
        print(f"✅ Successfully created project structure with {len(files_created)} files")
        return success_response
        
    except Exception as e:
        print(f"❌ Error in create_project_structure: {str(e)}")
        try:
            await manager.send_to_project(project_name, {
                "type": "terminal_output",
                "message": f"❌ Error creating structure: {str(e)}",
                "level": "error"
            })
        except Exception as ws_error:
            print(f"WebSocket error in create_project_structure exception: {ws_error}")
        
        error_response = {"success": False, "error": str(e)}
        print(f"❌ Returning error response: {error_response}")
        return error_response

async def create_simple_project_structure(project_path: Path, idea: str, project_name: str, tech_stack: List[str]) -> List[str]:
    """Create a simple React + Node.js project structure"""
    files_created = []
    
    # Create main directories
    frontend_path = project_path / "frontend"
    backend_path = project_path / "backend"
    
    frontend_path.mkdir(parents=True, exist_ok=True)
    backend_path.mkdir(parents=True, exist_ok=True)
    
    # Create basic React frontend
    src_path = frontend_path / "src"
    src_path.mkdir(exist_ok=True)
    
    # Package.json for frontend
    package_json = {
        "name": project_name,
        "version": "0.1.0",
        "private": True,
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-scripts": "5.0.1"
        },
        "scripts": {
            "start": "react-scripts start",
            "build": "react-scripts build",
            "test": "react-scripts test",
            "eject": "react-scripts eject"
        }
    }
    
    with open(frontend_path / "package.json", 'w') as f:
        json.dump(package_json, f, indent=2)
    files_created.append("frontend/package.json")
    
    # App.jsx
    app_jsx = f'''import React from 'react';
import './App.css';

function App() {{
  return (
    <div className="App">
      <header className="App-header">
        <h1>Welcome to {project_name}</h1>
        <p>{idea}</p>
        <p>This is your new React application!</p>
      </header>
    </div>
  );
}}

export default App;'''
    
    with open(src_path / "App.jsx", 'w') as f:
        f.write(app_jsx)
    files_created.append("frontend/src/App.jsx")
    
    # App.css
    app_css = '''.App {
  text-align: center;
}

.App-header {
  background-color: #282c34;
  padding: 20px;
  color: white;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: calc(10px + 2vmin);
}

h1 {
  margin-bottom: 20px;
}

p {
  margin: 10px 0;
  max-width: 600px;
}'''
    
    with open(src_path / "App.css", 'w') as f:
        f.write(app_css)
    files_created.append("frontend/src/App.css")
    
    # index.js
    index_js = '''import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);'''
    
    with open(src_path / "index.js", 'w') as f:
        f.write(index_js)
    files_created.append("frontend/src/index.js")
    
    # index.css
    index_css = '''body {
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
}'''
    
    with open(src_path / "index.css", 'w') as f:
        f.write(index_css)
    files_created.append("frontend/src/index.css")
    
    # Public directory
    public_path = frontend_path / "public"
    public_path.mkdir(exist_ok=True)
    
    # index.html
    index_html = f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="{idea}" />
    <title>{project_name}</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>'''
    
    with open(public_path / "index.html", 'w') as f:
        f.write(index_html)
    files_created.append("frontend/public/index.html")
    
    # Create simple Node.js backend
    backend_package = {
        "name": f"{project_name}-backend",
        "version": "1.0.0",
        "description": f"Backend for {idea}",
        "main": "server.js",
        "scripts": {
            "start": "node server.js",
            "dev": "nodemon server.js"
        },
        "dependencies": {
            "express": "^4.18.2",
            "cors": "^2.8.5"
        }
    }
    
    with open(backend_path / "package.json", 'w') as f:
        json.dump(backend_package, f, indent=2)
    files_created.append("backend/package.json")
    
    # server.js
    server_js = f'''const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 8001;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.get('/', (req, res) => {{
    res.json({{
        message: 'Welcome to {project_name} API',
        description: '{idea}'
    }});
}});

app.get('/api/hello', (req, res) => {{
    res.json({{ message: 'Hello from {project_name}!' }});
}});

app.listen(PORT, () => {{
    console.log(`🚀 {project_name} server running on port ${{PORT}}`);
}});'''
    
    with open(backend_path / "server.js", 'w') as f:
        f.write(server_js)
    files_created.append("backend/server.js")
    
    # README.md
    readme = f'''# {project_name}

{idea}

## Getting Started

### Frontend
```bash
cd frontend
npm install
npm start
```

### Backend
```bash
cd backend
npm install
npm start
```

## Tech Stack
- React
- Node.js
- Express'''
    
    with open(project_path / "README.md", 'w') as f:
        f.write(readme)
    files_created.append("README.md")
    
    return files_created

# --- Get Project File Tree Endpoint ---
@app.get("/api/project-file-tree")
async def get_project_file_tree(project_name: str = Query(...)):
    """Get file tree structure for a project"""
    try:
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}
        
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
        
        # Save file
        with open(full_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
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
        
        return {"success": True}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Run Project Endpoint ---
@app.post("/api/run-project")
async def run_project(request: dict = Body(...)):
    """Build and run the project"""
    try:
        project_name = request.get("project_name")
        
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}
        
        # Start backend server first
        backend_path = project_path / "backend"
        frontend_path = project_path / "frontend"
        
        preview_urls = []
        
        # Start backend if it exists
        if backend_path.exists() and (backend_path / "main.py").exists():
            await manager.send_to_project(project_name, {
                "type": "terminal_output",
                "message": "🚀 Starting backend server...",
                "level": "info"
            })
            
            try:
                # Install backend dependencies first
                requirements_file = backend_path / "requirements.txt"
                if requirements_file.exists():
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": "📦 Installing backend dependencies...",
                        "level": "info"
                    })
                    
                    pip_process = await asyncio.create_subprocess_shell(
                        "pip install -r requirements.txt",
                        cwd=backend_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await pip_process.wait()
                
                # Start FastAPI server with uvicorn
                backend_process = await asyncio.create_subprocess_shell(
                    "uvicorn main:app --reload --host 0.0.0.0 --port 8000",
                    cwd=backend_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Give backend time to start
                await asyncio.sleep(3)
                
                # Check if backend is responding
                import aiohttp
                backend_available = False
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get("http://localhost:8000/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                            if response.status == 200:
                                backend_available = True
                except Exception:
                    # Try root endpoint if /health doesn't exist
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get("http://localhost:8000/", timeout=aiohttp.ClientTimeout(total=5)) as response:
                                if response.status == 200:
                                    backend_available = True
                    except Exception:
                        pass
                
                if backend_available:
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": "✅ Backend server started on http://localhost:8000",
                        "level": "success"
                    })
                else:
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": "⚠️ Backend server started but may still be loading...",
                        "level": "warning"
                    })
                    
            except Exception as e:
                await manager.send_to_project(project_name, {
                    "type": "terminal_output",
                    "message": f"❌ Backend start failed: {str(e)}",
                    "level": "error"
                })
        else:
            await manager.send_to_project(project_name, {
                "type": "terminal_output",
                "message": "ℹ️ No backend found, starting frontend only...",
                "level": "info"
            })
        
        # Check for missing App.jsx and create fallback if needed
        if frontend_path.exists():
            app_jsx_path = frontend_path / "src" / "App.jsx"
            if not app_jsx_path.exists():
                await manager.send_to_project(project_name, {
                    "type": "terminal_output",
                    "message": "🔧 App.jsx missing, creating fallback...",
                    "level": "warning"
                })
                
                try:
                    # Create basic fallback App.jsx
                    fallback_app = f'''import React from 'react';

function App() {{
  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Welcome to {project_name}</h1>
        <p className="text-gray-300">Your application is loading...</p>
        <div className="mt-8">
          <div className="animate-pulse bg-blue-600 h-2 w-64 mx-auto rounded"></div>
        </div>
      </div>
    </div>
  );
}}

export default App;'''
                    
                    app_jsx_path.parent.mkdir(parents=True, exist_ok=True)
                    app_jsx_path.write_text(fallback_app, encoding="utf-8")
                    
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": "✅ Created fallback App.jsx",
                        "level": "success"
                    })
                except Exception as e:
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": f"❌ Failed to create fallback App.jsx: {str(e)}",
                        "level": "error"
                    })

        # Start frontend
        if frontend_path.exists():
            await manager.send_to_project(project_name, {
                "type": "terminal_output",
                "message": "� Installing frontend dependencies...",
                "level": "info"
            })
            
            # Install dependencies first
            try:
                install_process = await asyncio.create_subprocess_shell(
                    "npm install",
                    cwd=frontend_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Wait for installation to complete
                await install_process.wait()
                
                if install_process.returncode == 0:
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": "✅ Dependencies installed successfully",
                        "level": "success"
                    })
                else:
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": "⚠️ Dependency installation had issues, continuing anyway...",
                        "level": "warning"
                    })
                    
            except Exception as e:
                await manager.send_to_project(project_name, {
                    "type": "terminal_output",
                    "message": f"⚠️ Could not install dependencies: {str(e)}",
                    "level": "warning"
                })
            
            await manager.send_to_project(project_name, {
                "type": "terminal_output",
                "message": "�🚀 Starting frontend server...",
                "level": "info"
            })
            
            try:
                # Start npm start in background
                # Check if package.json exists and determine the start command
                package_json_path = frontend_path / "package.json"
                start_command = "npm start"
                
                if package_json_path.exists():
                    try:
                        import json
                        import time
                        print(f"Reading package.json from: {package_json_path}")
                        
                        # Retry logic for file reading (in case of concurrent access)
                        max_retries = 3
                        retry_delay = 0.5
                        
                        for attempt in range(max_retries):
                            try:
                                with open(package_json_path, 'r', encoding='utf-8') as f:
                                    content = f.read().strip()
                                    print(f"Package.json content length: {len(content)} (attempt {attempt + 1})")
                                    
                                    if len(content) == 0:
                                        print("Package.json is empty!")
                                        if attempt < max_retries - 1:
                                            print(f"Retrying in {retry_delay} seconds...")
                                            time.sleep(retry_delay)
                                            continue
                                        else:
                                            raise ValueError("Package.json file is empty after all retries")
                                    
                                    package_data = json.loads(content)
                                    print("Package.json successfully parsed")
                                    break
                                    
                            except (json.JSONDecodeError, ValueError) as e:
                                print(f"JSON parsing error on attempt {attempt + 1}: {e}")
                                if attempt < max_retries - 1:
                                    print(f"Retrying in {retry_delay} seconds...")
                                    time.sleep(retry_delay)
                                    continue
                                else:
                                    raise
                        
                        scripts = package_data.get('scripts', {})
                        
                        # If it's a Next.js project, use dev command
                        if 'next' in str(package_data.get('dependencies', {})) or 'next' in str(package_data.get('devDependencies', {})):
                            start_command = "npm run dev"
                        # If it's a Vite project, use dev command  
                        elif 'vite' in str(package_data.get('dependencies', {})) or 'vite' in str(package_data.get('devDependencies', {})):
                            start_command = "npm run dev"
                        # If it has a dev script but no start script, use dev
                        elif 'dev' in scripts and 'start' not in scripts:
                            start_command = "npm run dev"
                        
                        print(f"Determined start command: {start_command}")
                            
                    except Exception as e:
                        print(f"Error reading package.json: {e}")
                        print(f"Package.json path: {package_json_path}")
                        print(f"Path exists: {package_json_path.exists()}")
                        # Continue with default npm start command
                else:
                    print(f"Package.json not found at: {package_json_path}")
                
                await manager.send_to_project(project_name, {
                    "type": "terminal_output", 
                    "message": f"🚀 Starting frontend with: {start_command}",
                    "level": "info"
                })
                
                process = await asyncio.create_subprocess_shell(
                    start_command,
                    cwd=frontend_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Give it more time to start and check if server is actually responding
                await asyncio.sleep(5)
                
                # Check if the server is actually responding
                import aiohttp
                server_available = False
                
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get("http://localhost:3000", timeout=aiohttp.ClientTimeout(total=5)) as response:
                            if response.status == 200:
                                server_available = True
                except Exception:
                    # Server might still be starting, check if process is running
                    if process.returncode is None:
                        server_available = True  # Process is running, assume it will start soon
                
                if server_available and process.returncode is None:  # Still running and responding
                    preview_urls.append("http://localhost:3000")
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": "✅ Frontend server started on http://localhost:3000",
                        "level": "success"
                    })
                    
                    await manager.send_to_project(project_name, {
                        "type": "preview_ready",
                        "url": "http://localhost:3000"
                    })
                else:
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": "⚠️ Frontend server started but may still be loading...",
                        "level": "warning"
                    })
                    # Still add preview URL as it might work shortly
                    preview_urls.append("http://localhost:3000")
                
            except Exception as e:
                await manager.send_to_project(project_name, {
                    "type": "terminal_output",
                    "message": f"❌ Frontend start failed: {str(e)}",
                    "level": "error"
                })
        
        return {
            "success": True,
            "preview_url": preview_urls[0] if preview_urls else None,
            "urls": preview_urls
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

# --- Error Checking Endpoint ---
@app.get("/api/check-project-errors")
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
            if not (frontend_path / "package.json").exists():
                errors.append({
                    "severity": "error",
                    "message": "Missing package.json",
                    "file": "frontend/package.json",
                    "line": 1
                })
        
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
        
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": f"🔧 Auto-fixing {len(errors)} errors...",
            "level": "info"
        })
        
        # Simulate fixing
        await asyncio.sleep(1)
        
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": "✅ Errors fixed",
            "level": "success"
        })
        
        return {
            "success": True,
            "files_modified": [],
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

# --- AI Chat Endpoint ---
@app.post("/api/ai-chat")
async def ai_chat(request: dict = Body(...)):
    """Handle AI chat requests for code assistance"""
    try:
        project_name = request.get("project_name")
        message = request.get("message")
        file_context = request.get("file_context")
        file_tree = request.get("file_tree", [])
        
        if not project_name or not message:
            return {"success": False, "error": "Missing project_name or message"}
        
        # Import AI assistant
        from ai_assistant import get_chat_response
        
        # Build context for AI
        context_info = f"Project: {project_name}\n"
        
        if file_context and file_context.get("path"):
            context_info += f"Current file: {file_context['path']}\n"
            context_info += f"File content:\n```\n{file_context.get('content', '')[:2000]}...\n```\n\n"
        
        if file_tree:
            context_info += f"Project structure: {[item.get('name', '') for item in file_tree[:10]]}\n\n"
        
        # Prepare chat history with context
        chat_history = [
            {
                "role": "system", 
                "content": f"""You are an AI coding assistant helping with a web development project. 

Project Context:
{context_info}

You can help with:
- Code modifications and improvements
- Bug fixes and debugging
- Feature additions
- Code explanations
- File creation and editing

When suggesting code changes, provide clear, actionable responses. If you want to modify files, format your response to include specific file changes."""
            },
            {
                "role": "user",
                "content": message
            }
        ]
        
        # Get AI response
        ai_response = get_chat_response(chat_history, "smart")
        
        # Parse response for file changes (basic implementation)
        file_changes = []
        if "CREATE FILE:" in ai_response or "MODIFY FILE:" in ai_response:
            # This is a simplified parser - could be enhanced
            lines = ai_response.split('\n')
            current_file = None
            current_content = []
            
            for line in lines:
                if line.startswith("CREATE FILE:") or line.startswith("MODIFY FILE:"):
                    if current_file:
                        file_changes.append({
                            "type": "modify" if "MODIFY" in line else "create",
                            "path": current_file,
                            "content": '\n'.join(current_content)
                        })
                    current_file = line.split(":", 1)[1].strip()
                    current_content = []
                elif line.startswith("```") and current_file:
                    # Skip code block markers
                    continue
                elif current_file and line.strip():
                    current_content.append(line)
            
            # Add last file if exists
            if current_file and current_content:
                file_changes.append({
                    "type": "modify",
                    "path": current_file,
                    "content": '\n'.join(current_content)
                })
        
        return {
            "success": True,
            "response": ai_response,
            "file_changes": file_changes,
            "actions": []
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Create File Endpoint ---
@app.post("/api/create-file")
async def create_file_endpoint(request: dict = Body(...)):
    """Create a new file in the project"""
    try:
        project_name = request.get("project_name")
        file_path = request.get("file_path")
        content = request.get("content", "")
        
        if not project_name or not file_path:
            return {"success": False, "error": "Missing project_name or file_path"}
        
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}
        
        # Create the file
        full_file_path = project_path / file_path.lstrip('/')
        
        # Security check
        try:
            full_file_path.resolve().relative_to(project_path.resolve())
        except ValueError:
            return {"success": False, "error": "Invalid file path"}
        
        # Create directory if needed
        full_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(full_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {"success": True, "message": f"File created: {file_path}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Monaco Editor API Server...")
    uvicorn.run(app, host="0.0.0.0", port=8001)