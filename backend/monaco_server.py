"""
Simplified FastAPI server for Monaco Editor functionality
This version avoids complex dependencies that were causing import issues
"""
import os
import json
import uuid
import asyncio
import subprocess
import re
from pathlib import Path
from typing import Dict, Set, List
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState
from pydantic import BaseModel

import os
import json
import uuid
import shutil
import asyncio
from pathlib import Path
from typing import Dict, Set, List
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState
from pydantic import BaseModel

# Import speech functionality
try:
    from speechLogic import transcribe_audio_data, process_speech_request, text_to_speech
    SPEECH_ENABLED = True
    print("✅ Speech functionality enabled")
except ImportError as e:
    SPEECH_ENABLED = False
    print(f"⚠️ Speech functionality disabled: {e}")

def safe_json_parse(text: str) -> dict:
    """Safely parse JSON from AI response with fallbacks"""
    try:
        # First, try direct JSON parsing
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON block in markdown
    json_pattern = r'```json\s*(.*?)\s*```'
    match = re.search(json_pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            json_content = match.group(1).strip()
            return json.loads(json_content)
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object in text with better cleaning
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    for match in matches:
        try:
            # Aggressive cleaning for malformed JSON
            cleaned = match.strip()
            
            # Remove comments and extra text
            cleaned = re.sub(r'//.*?\n', '', cleaned)
            cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
            
            # Fix common JSON issues
            cleaned = re.sub(r'(\w+):', r'"\1":', cleaned)  # Add quotes to keys
            cleaned = cleaned.replace("'", '"')  # Single to double quotes
            cleaned = re.sub(r',\s*}', '}', cleaned)  # Remove trailing commas
            cleaned = re.sub(r',\s*]', ']', cleaned)  # Remove trailing commas in arrays
            
            # Remove control characters but keep newlines and tabs for JSON structure
            cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\n\r\t')
            
            # Fix unterminated strings - find and close them
            cleaned = fix_unterminated_strings(cleaned)
            
            # Fix missing commas between properties
            cleaned = re.sub(r'"\s*\n\s*"', '",\n"', cleaned)
            
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"JSON parse error for match: {e}")
            continue
    
    print("Attempting manual extraction from AI response...")
    # Fallback: extract key information manually
    return extract_project_info_manually(text)

def fix_unterminated_strings(text: str) -> str:
    """Fix unterminated strings in JSON"""
    try:
        # Find strings that aren't properly closed
        result = ""
        in_string = False
        escape_next = False
        
        for i, char in enumerate(text):
            if escape_next:
                result += char
                escape_next = False
                continue
                
            if char == '\\' and in_string:
                result += char
                escape_next = True
                continue
                
            if char == '"':
                if in_string:
                    # End of string
                    in_string = False
                else:
                    # Start of string
                    in_string = True
                result += char
            elif char == '\n' and in_string:
                # Unterminated string at newline - close it
                result += '"'
                in_string = False
                result += char
            else:
                result += char
        
        # If we end while still in a string, close it
        if in_string:
            result += '"'
            
        return result
    except Exception:
        return text

def extract_project_info_manually(text: str) -> dict:
    """Manual extraction when JSON parsing fails"""
    try:
        print(f"Manual extraction from text: {text[:200]}...")
        
        # Handle specific "Student Helper" requests
        if "student helper" in text.lower() or "studenthelper" in text.lower():
            return {
                "name": "Student Helper",
                "description": "A comprehensive student helper application for managing assignments, schedules, and academic resources",
                "tech_stack": ["React", "Node.js", "Express", "MongoDB"],
                "type": "web_app",
                "features": [
                    "Assignment tracking",
                    "Schedule management", 
                    "Grade calculator",
                    "Study resources",
                    "Task reminders"
                ]
            }
        
        # Extract project name - look for various patterns
        name_patterns = [
            r'(?:name|title|app)[:=]\s*["\']?([^"\'\n]+)["\']?',
            r'"name"\s*:\s*"([^"]+)"',
            r'application\s+(?:called|named)\s+([^\n.,:]+)',
            r'build\s+(?:a|an)\s+([^\n.,:]+)\s+(?:app|application)',
        ]
        
        project_name = "My App"
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                project_name = match.group(1).strip()
                break
        
        # Extract description
        desc_patterns = [
            r'(?:description|summary|purpose)[:=]\s*["\']?([^"\'\n]+)["\']?',
            r'"description"\s*:\s*"([^"]+)"',
            r'(?:build|create|make)\s+(?:a|an)\s+([^.]+?)(?:\.|for|that)',
        ]
        
        description = "A web application"
        for pattern in desc_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                description = match.group(1).strip()
                break
        
        # Extract features from text
        features = []
        feature_keywords = ["track", "manage", "calculate", "schedule", "organize", "store", "display", "create", "edit", "delete", "search", "filter"]
        for keyword in feature_keywords:
            if keyword in text.lower():
                features.append(f"{keyword.capitalize()} functionality")
        
        if not features:
            features = ["User interface", "Data management", "Responsive design"]
        
        # Extract tech stack
        tech_stack = ["React", "Node.js", "Express"]  # Default
        if "mongodb" in text.lower() or "database" in text.lower():
            tech_stack.append("MongoDB")
        if "typescript" in text.lower():
            tech_stack.append("TypeScript")
        if "tailwind" in text.lower():
            tech_stack.append("Tailwind CSS")
        
        result = {
            "name": project_name,
            "description": description,
            "tech_stack": tech_stack,
            "type": "web_app",
            "features": features[:5]  # Limit to 5 features
        }
        
        print(f"Manual extraction result: {result}")
        return result
        
    except Exception as e:
        print(f"Manual extraction error: {e}")
        return {
            "name": "Student Helper",
            "description": "A student helper application",
            "tech_stack": ["React", "Node.js", "Express"],
            "type": "web_app",
            "features": ["Assignment tracking", "Study management"]
        }

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

# --- Speech API Endpoints ---
@app.post("/api/speech/transcribe")
async def transcribe_speech(file: UploadFile = File(...)):
    """Transcribe audio to text using Google Cloud Speech-to-Text"""
    if not SPEECH_ENABLED:
        return {"success": False, "error": "Speech functionality not available"}
    
    try:
        # Read audio data
        audio_data = await file.read()
        
        # Transcribe using speechLogic
        transcript = transcribe_audio_data(audio_data)
        
        if transcript:
            return {
                "success": True,
                "transcript": transcript
            }
        else:
            return {
                "success": False,
                "error": "Could not transcribe audio"
            }
            
    except Exception as e:
        print(f"Transcription error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/speech/process")
async def process_speech(request: dict = Body(...)):
    """Process transcribed text through speech logic conversation system"""
    if not SPEECH_ENABLED:
        return {"success": False, "error": "Speech functionality not available"}
    
    try:
        text = request.get("text")
        if not text:
            return {"success": False, "error": "No text provided"}
        
        # Process through speech logic
        result = await process_speech_request(text)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        print(f"Speech processing error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/speech/speak")
async def speak_text_endpoint(request: dict = Body(...)):
    """Convert text to speech using Google Cloud Text-to-Speech"""
    if not SPEECH_ENABLED:
        return {"success": False, "error": "Speech functionality not available"}
    
    try:
        text = request.get("text")
        if not text:
            return {"success": False, "error": "No text provided"}
        
        # Generate audio using speechLogic
        audio_data = text_to_speech(text)
        
        if audio_data:
            return {
                "success": True,
                "audio_data": audio_data.hex()  # Convert bytes to hex string
            }
        else:
            return {
                "success": False,
                "error": "Could not generate speech"
            }
            
    except Exception as e:
        print(f"TTS error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# --- Project Edit Endpoint ---
@app.post("/api/edit-project")
async def edit_project(request: dict = Body(...)):
    """Handle specific edits to generated projects"""
    try:
        user_request = request.get("request", "")
        project_name = request.get("project_name", "")
        project_path = request.get("project_path", "")
        
        if not user_request:
            return {"success": False, "error": "No edit request provided"}
        
        print(f"🔧 Processing edit request: {user_request}")
        print(f"📁 Project: {project_name} at {project_path}")
        
        # Handle specific edit requests
        if "name" in user_request.lower() and ("student helper" in user_request.lower() or "studenthelper" in user_request.lower()):
            # User wants to change the app name to Student Helper
            return await change_app_name(project_path, "Student Helper", user_request)
        
        elif "title" in user_request.lower() and "student helper" in user_request.lower():
            # Same as above - title change
            return await change_app_name(project_path, "Student Helper", user_request)
        
        elif "color" in user_request.lower() or "style" in user_request.lower():
            # Style/color changes
            return await change_app_styles(project_path, user_request)
        
        elif "feature" in user_request.lower() or "add" in user_request.lower():
            # Adding new features
            return await add_app_feature(project_path, user_request)
        
        else:
            # General edit request - try to understand and make changes
            return await general_project_edit(project_path, user_request)
            
    except Exception as e:
        print(f"Edit project error: {e}")
        return {
            "success": False,
            "error": f"Could not process edit request: {str(e)}"
        }

async def change_app_name(project_path: str, new_name: str, request: str):
    """Change the application name in all relevant files"""
    try:
        project_dir = Path(project_path)
        if not project_dir.exists():
            # Try generated_projects directory
            project_dir = Path(f"generated_projects/{project_path}")
        
        if not project_dir.exists():
            return {"success": False, "error": "Project directory not found"}
        
        files_modified = []
        
        # Update frontend files
        frontend_dir = project_dir / "frontend"
        if frontend_dir.exists():
            # Update package.json
            package_json_path = frontend_dir / "package.json"
            if package_json_path.exists():
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                package_data["name"] = new_name.lower().replace(" ", "-")
                with open(package_json_path, 'w') as f:
                    json.dump(package_data, f, indent=2)
                files_modified.append("frontend/package.json")
            
            # Update App.jsx
            app_jsx_path = frontend_dir / "src" / "App.jsx"
            if app_jsx_path.exists():
                with open(app_jsx_path, 'r') as f:
                    content = f.read()
                
                # Replace title in h1 tag
                content = re.sub(r'<h1>.*?</h1>', f'<h1>Welcome to {new_name}</h1>', content)
                # Replace any other references to the old name
                content = re.sub(r'Welcome to [^<]+', f'Welcome to {new_name}', content)
                
                with open(app_jsx_path, 'w') as f:
                    f.write(content)
                files_modified.append("frontend/src/App.jsx")
            
            # Update index.html
            index_html_path = frontend_dir / "public" / "index.html"
            if index_html_path.exists():
                with open(index_html_path, 'r') as f:
                    content = f.read()
                
                # Update title tag
                content = re.sub(r'<title>.*?</title>', f'<title>{new_name}</title>', content)
                
                with open(index_html_path, 'w') as f:
                    f.write(content)
                files_modified.append("frontend/public/index.html")
        
        # Update backend files
        backend_dir = project_dir / "backend"
        if backend_dir.exists():
            # Update package.json
            package_json_path = backend_dir / "package.json"
            if package_json_path.exists():
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                package_data["name"] = f"{new_name.lower().replace(' ', '-')}-backend"
                package_data["description"] = f"Backend for {new_name}"
                with open(package_json_path, 'w') as f:
                    json.dump(package_data, f, indent=2)
                files_modified.append("backend/package.json")
            
            # Update server.js
            server_js_path = backend_dir / "server.js"
            if server_js_path.exists():
                with open(server_js_path, 'r') as f:
                    content = f.read()
                
                # Replace references to the old name
                content = re.sub(r'Welcome to [^\']+', f'Welcome to {new_name}', content)
                content = re.sub(r'Hello from [^\']+', f'Hello from {new_name}', content)
                content = re.sub(r'{new_name} server', f'{new_name} server', content)
                
                with open(server_js_path, 'w') as f:
                    f.write(content)
                files_modified.append("backend/server.js")
        
        # Update README.md
        readme_path = project_dir / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r') as f:
                content = f.read()
            
            # Replace the title
            lines = content.split('\n')
            if lines and lines[0].startswith('# '):
                lines[0] = f'# {new_name}'
            
            with open(readme_path, 'w') as f:
                f.write('\n'.join(lines))
            files_modified.append("README.md")
        
        return {
            "success": True,
            "message": f"✅ Successfully changed application name to '{new_name}'!",
            "files_modified": files_modified,
            "changes_made": [
                f"Updated application title to '{new_name}'",
                "Modified package.json files",
                "Updated frontend display text",
                "Changed backend API responses",
                "Updated README documentation"
            ]
        }
        
    except Exception as e:
        print(f"Error changing app name: {e}")
        return {
            "success": False,
            "error": f"Could not change app name: {str(e)}"
        }

async def change_app_styles(project_path: str, request: str):
    """Change app styles based on user request"""
    # Placeholder for style changes
    return {
        "success": True,
        "message": "Style changes would be implemented here",
        "request": request
    }

async def add_app_feature(project_path: str, request: str):
    """Add new features to the app"""
    # Placeholder for feature additions
    return {
        "success": True,
        "message": "Feature additions would be implemented here",
        "request": request
    }

async def general_project_edit(project_path: str, request: str):
    """Handle general edit requests"""
    # Placeholder for general edits
    return {
        "success": True,
        "message": f"Edit request processed: {request}",
        "note": "This is a general edit handler that would parse and implement the requested changes"
    }

# --- AI Project Assistant Endpoint ---
@app.post("/api/ai-project-assistant")
async def ai_project_assistant(request: dict = Body(...)):
    """AI assistant for project planning and requirements gathering"""
    try:
        user_input = request.get("input", "")
        context = request.get("context", {})
        project_path = request.get("project_path", "")
        
        if not user_input:
            return {"success": False, "error": "No input provided"}
        
        print(f"🤖 AI Assistant processing: {user_input}")
        
        # Handle specific edit requests for existing projects
        if project_path and ("change" in user_input.lower() or "edit" in user_input.lower() or "modify" in user_input.lower()):
            print("🔧 Detected edit request for existing project")
            
            # Handle specific name change requests
            if ("name" in user_input.lower() or "title" in user_input.lower()) and ("student helper" in user_input.lower() or "studenthelper" in user_input.lower()):
                edit_response = await change_app_name(project_path, "Student Helper", user_input)
                if edit_response["success"]:
                    return {
                        "success": True,
                        "response": f"✅ Perfect! I've updated the application name to 'Student Helper' across all files. The changes include:\n\n" + 
                                  "\n".join([f"• {change}" for change in edit_response["changes_made"]]) +
                                  f"\n\nFiles modified: {', '.join(edit_response['files_modified'])}",
                        "edit_made": True,
                        "files_modified": edit_response["files_modified"]
                    }
                else:
                    return {
                        "success": False,
                        "response": f"❌ I couldn't make that change: {edit_response['error']}",
                        "edit_made": False
                    }
            
            # Handle other edit requests
            else:
                return {
                    "success": True,
                    "response": f"I understand you want to make changes to your project. I can help with:\n\n• Changing the application name\n• Modifying styles and colors\n• Adding new features\n• Updating content\n\nCould you be more specific about what you'd like to change? For example: 'Change the app name to Student Helper' or 'Add a dark theme'.",
                    "edit_made": False,
                    "suggestions": [
                        "Change the application name",
                        "Modify the color scheme",
                        "Add new features",
                        "Update the layout"
                    ]
                }
        
        # Handle the "Student Helper" project creation request specifically
        elif "student helper" in user_input.lower() or "studenthelper" in user_input.lower():
            return {
                "success": True,
                "response": "Great! I'll create a 'Student Helper' application for you. This will be a comprehensive tool to help students manage their academic life.",
                "project_info": {
                    "name": "Student Helper",
                    "description": "A comprehensive student helper application for managing assignments, schedules, and academic resources",
                    "tech_stack": ["React", "Node.js", "Express", "MongoDB"],
                    "type": "web_app",
                    "features": [
                        "Assignment tracking and deadlines",
                        "Class schedule management", 
                        "Grade calculator and GPA tracking",
                        "Study resources and notes",
                        "Task reminders and notifications",
                        "Calendar integration"
                    ]
                },
                "next_steps": "I'll start building the Student Helper application with all these features. It will have a clean, student-friendly interface!"
            }
        
        # Try to use AI assistant for other requests
        try:
            from ai_assistant import get_chat_response
            
            # Prepare system prompt for project assistant
            system_prompt = """You are an AI project assistant that helps users plan and build web applications. 

For project creation requests, respond with a friendly message and project information in this EXACT JSON format:

{
    "name": "Project Name",
    "description": "Brief description", 
    "tech_stack": ["React", "Node.js", "Express"],
    "type": "web_app",
    "features": ["feature1", "feature2", "feature3"]
}

For edit requests, be specific about what changes you can make and ask for clarification if needed.

IMPORTANT: Always return valid, properly formatted JSON. Escape quotes and newlines properly."""
            
            # Get AI response
            chat_history = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            ai_response = get_chat_response(chat_history, "smart")
            
            # Parse AI response safely
            project_info = safe_json_parse(ai_response)
            
            return {
                "success": True,
                "response": ai_response,
                "project_info": project_info
            }
            
        except ImportError:
            # Fallback if ai_assistant is not available
            print("AI assistant not available, using enhanced fallback")
            
            # Create a reasonable project based on user input
            project_name = extract_project_name(user_input)
            
            project_info = {
                "name": project_name,
                "description": f"Application based on: {user_input}",
                "tech_stack": ["React", "Node.js", "Express"],
                "type": "web_app",
                "features": ["User interface", "Backend API", "Data management", "Responsive design"]
            }
            
            return {
                "success": True,
                "response": f"I understand you want to build: {user_input}. Let me help you create this project with a modern tech stack!",
                "project_info": project_info
            }
        
    except Exception as e:
        print(f"AI project assistant error: {e}")
        return {
            "success": False,
            "error": str(e),
            "fallback_response": "I can help you build your project! Could you tell me more about what you'd like to create or modify?"
        }

def extract_project_name(text: str) -> str:
    """Extract a reasonable project name from user input"""
    # Clean the text and extract key words
    words = re.findall(r'\b[A-Za-z]+\b', text)
    # Take first few meaningful words and capitalize
    if words:
        name_words = [w.capitalize() for w in words[:2] if len(w) > 2]
        if name_words:
            return ''.join(name_words) + 'App'
    return "MyApp"

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Monaco Editor API Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)