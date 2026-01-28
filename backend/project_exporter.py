"""
Project Export Generator
========================
Generates exportable, production-ready project packages.

Features:
- Clean docker-compose.yml with no sandbox logic
- .env.example with all required configuration
- Production-ready backend (no sandbox-only code)
- Frontend configured with VITE_API_BASE_URL
- README with setup instructions
"""

import os
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import json

# Get the templates directory
TEMPLATES_DIR = Path(__file__).parent / "docker-configs"


class ProjectExporter:
    """
    Generates exportable project packages for local development.
    
    Ensures:
    - No sandbox-only logic in exported code
    - Clean docker-compose.yml
    - Proper .env.example
    - Frontend configured for VITE_API_BASE_URL
    """
    
    def __init__(self):
        self.templates_dir = TEMPLATES_DIR
    
    def export_project(
        self,
        project_name: str,
        project_files: Dict[str, str],
        output_path: Optional[str] = None,
        include_docker: bool = True,
    ) -> Dict[str, Any]:
        """
        Export a project as a production-ready package.
        
        Args:
            project_name: Name of the project
            project_files: Dict of filename -> content
            output_path: Optional path for the exported zip
            include_docker: Whether to include Docker files
        
        Returns:
            Dict with export details (path, files, size)
        """
        # Clean project name for filesystem
        project_slug = self._slugify(project_name)
        
        # Separate frontend and backend files
        frontend_files = {}
        backend_files = {}
        other_files = {}
        
        for filepath, content in project_files.items():
            if filepath.startswith('frontend/') or filepath.startswith('src/'):
                # Normalize frontend paths
                if filepath.startswith('src/'):
                    filepath = f"frontend/{filepath}"
                frontend_files[filepath] = content
            elif filepath.startswith('backend/'):
                backend_files[filepath] = content
            elif filepath.endswith(('.jsx', '.tsx', '.js', '.ts', '.css', '.html')) and not filepath.startswith('backend/'):
                # Frontend files without prefix
                frontend_files[f"frontend/src/{filepath}"] = content
            elif filepath.endswith('.py'):
                # Python files are backend
                backend_files[f"backend/{filepath}"] = content
            else:
                other_files[filepath] = content
        
        # Generate export package
        export_files = {}
        
        # Add frontend files
        for filepath, content in frontend_files.items():
            export_files[filepath] = content
        
        # Add backend files (clean, no sandbox logic)
        export_files.update(self._generate_backend_files(backend_files, project_name))
        
        # Add Docker files if requested
        if include_docker:
            export_files.update(self._generate_docker_files(project_slug))
        
        # Add README
        export_files["README.md"] = self._generate_readme(project_name, project_slug)
        
        # Add frontend config files if not present
        if "frontend/package.json" not in export_files:
            export_files["frontend/package.json"] = self._generate_package_json(project_name)
        
        if "frontend/vite.config.js" not in export_files:
            export_files["frontend/vite.config.js"] = self._generate_vite_config()
        
        # Add .gitignore
        export_files[".gitignore"] = self._generate_gitignore()
        
        # Create zip file
        if output_path:
            zip_path = output_path
        else:
            zip_path = f"/tmp/{project_slug}-export-{int(datetime.utcnow().timestamp())}.zip"
        
        self._create_zip(export_files, zip_path, project_slug)
        
        return {
            "success": True,
            "project_name": project_name,
            "project_slug": project_slug,
            "zip_path": zip_path,
            "file_count": len(export_files),
            "files": list(export_files.keys()),
            "size_bytes": os.path.getsize(zip_path) if os.path.exists(zip_path) else 0
        }
    
    def _slugify(self, name: str) -> str:
        """Convert name to filesystem-safe slug."""
        return "".join(c if c.isalnum() or c == '-' else '-' for c in name.lower()).strip('-')
    
    def _generate_backend_files(
        self,
        existing_files: Dict[str, str],
        project_name: str
    ) -> Dict[str, str]:
        """Generate clean backend files without sandbox logic."""
        files = {}
        
        # Use production template for main.py if not provided or contains sandbox logic
        main_py = existing_files.get("backend/main.py", "")
        
        if "SANDBOX" in main_py or "sandbox" in main_py.lower() or not main_py:
            # Use clean production template
            template_path = self.templates_dir / "export_main.py"
            if template_path.exists():
                files["backend/main.py"] = template_path.read_text()
            else:
                files["backend/main.py"] = self._get_default_main_py()
        else:
            files["backend/main.py"] = main_py
        
        # Add requirements
        req_path = self.templates_dir / "export_requirements.txt"
        if req_path.exists():
            files["backend/requirements.txt"] = req_path.read_text()
        else:
            files["backend/requirements.txt"] = self._get_default_requirements()
        
        # Add Dockerfile
        dockerfile_path = self.templates_dir / "export_backend.Dockerfile"
        if dockerfile_path.exists():
            files["backend/Dockerfile"] = dockerfile_path.read_text()
        
        # Copy other backend files (models, routes, etc.)
        for filepath, content in existing_files.items():
            if filepath not in files and filepath.startswith("backend/"):
                # Clean sandbox references
                clean_content = self._remove_sandbox_logic(content)
                files[filepath] = clean_content
        
        return files
    
    def _remove_sandbox_logic(self, content: str) -> str:
        """Remove sandbox-specific code from content."""
        # Simple approach: remove lines containing sandbox-only patterns
        # In a more sophisticated implementation, we'd use AST parsing
        lines = content.split('\n')
        clean_lines = []
        
        skip_block = False
        
        for line in lines:
            # Skip sandbox-only blocks
            if 'if settings.SANDBOX' in line or 'if SANDBOX' in line:
                skip_block = True
                continue
            
            if skip_block and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                skip_block = False
            
            if skip_block:
                continue
            
            # Remove sandbox-specific lines
            sandbox_patterns = [
                'SANDBOX_INSTANCE_ID',
                'sandbox-isolated-jwt',
                'demo@sandbox.local',
                'AUTO_CREATE_DEMO_USER',
                '/api/auth/demo-login',
            ]
            
            if any(pattern in line for pattern in sandbox_patterns):
                continue
            
            clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    def _generate_docker_files(self, project_slug: str) -> Dict[str, str]:
        """Generate Docker configuration files."""
        files = {}
        
        # docker-compose.yml
        compose_path = self.templates_dir / "export_docker-compose.yml"
        if compose_path.exists():
            files["docker-compose.yml"] = compose_path.read_text()
        
        # .env.example
        env_path = self.templates_dir / "export_.env.example"
        if env_path.exists():
            env_content = env_path.read_text()
            # Replace placeholder project name
            env_content = env_content.replace("my-app", project_slug)
            files[".env.example"] = env_content
        
        # Frontend Dockerfile
        frontend_dockerfile = self.templates_dir / "export_frontend.Dockerfile"
        if frontend_dockerfile.exists():
            files["frontend/Dockerfile"] = frontend_dockerfile.read_text()
        
        # Nginx config
        nginx_conf = self.templates_dir / "export_nginx.conf"
        if nginx_conf.exists():
            files["frontend/nginx.conf"] = nginx_conf.read_text()
        
        return files
    
    def _generate_readme(self, project_name: str, project_slug: str) -> str:
        """Generate README with setup instructions."""
        return f'''# {project_name}

Generated with AltX AI Builder.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Running with Docker (Recommended)

1. Copy the environment file and configure it:
   ```bash
   cp .env.example .env
   ```

2. **IMPORTANT**: Edit `.env` and set a secure `JWT_SECRET`:
   ```bash
   # Generate a secure secret
   openssl rand -hex 32
   ```

3. Start the application:
   ```bash
   docker-compose up --build
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Running Locally (Development)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt

# Set environment variables
export JWT_SECRET=your-secret-key
export DATABASE_URL=sqlite:///./data/app.db

# Run the server
uvicorn main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install

# Create .env.local with API URL
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local

# Run development server
npm run dev
```

## Project Structure

```
{project_slug}/
├── docker-compose.yml    # Docker orchestration
├── .env.example          # Environment template
├── README.md             # This file
├── backend/
│   ├── Dockerfile        # Backend container
│   ├── main.py           # FastAPI application
│   └── requirements.txt  # Python dependencies
└── frontend/
    ├── Dockerfile        # Frontend container
    ├── nginx.conf        # Nginx configuration
    ├── package.json      # Node dependencies
    ├── vite.config.js    # Vite configuration
    └── src/              # React source code
```

## Environment Variables

### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./data/app.db` |
| `JWT_SECRET` | Secret for JWT tokens | **Required** |
| `JWT_EXPIRATION_HOURS` | Token validity duration | `24` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `DEBUG` | Enable debug mode | `false` |

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` |

## API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

Generated by AltX AI Builder.
'''
    
    def _generate_package_json(self, project_name: str) -> str:
        """Generate frontend package.json."""
        slug = self._slugify(project_name)
        return json.dumps({
            "name": slug,
            "private": True,
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview",
                "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.20.0"
            },
            "devDependencies": {
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0",
                "@vitejs/plugin-react": "^4.2.0",
                "vite": "^5.0.0"
            }
        }, indent=2)
    
    def _generate_vite_config(self) -> str:
        """Generate vite.config.js with API proxy."""
        return '''import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [react()],
    server: {
      port: 3000,
      open: true,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true,
        }
      }
    },
    build: {
      outDir: 'dist',
      sourcemap: true
    },
    define: {
      // Make env vars available at build time
      'import.meta.env.VITE_API_BASE_URL': JSON.stringify(env.VITE_API_BASE_URL || 'http://localhost:8000')
    }
  }
})
'''
    
    def _generate_gitignore(self) -> str:
        """Generate .gitignore."""
        return '''# Dependencies
node_modules/
__pycache__/
*.pyc
venv/
.venv/

# Build outputs
dist/
build/
*.egg-info/

# Environment files
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Data
*.db
data/

# Logs
*.log
logs/

# Docker
.docker/
'''
    
    def _get_default_main_py(self) -> str:
        """Get default main.py if template not found."""
        return '''"""
FastAPI Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    def _get_default_requirements(self) -> str:
        """Get default requirements.txt."""
        return '''fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
sqlalchemy>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
pydantic[email]>=2.0.0
'''
    
    def _create_zip(
        self,
        files: Dict[str, str],
        output_path: str,
        project_slug: str
    ):
        """Create a zip archive of the project."""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filepath, content in files.items():
                # Add project slug as root folder
                archive_path = f"{project_slug}/{filepath}"
                zf.writestr(archive_path, content)


# Create global instance
project_exporter = ProjectExporter()


def export_project(
    project_name: str,
    project_files: Dict[str, str],
    output_path: Optional[str] = None,
    include_docker: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to export a project.
    
    Args:
        project_name: Name of the project
        project_files: Dict of filename -> content
        output_path: Optional path for the exported zip
        include_docker: Whether to include Docker files
    
    Returns:
        Dict with export details
    """
    return project_exporter.export_project(
        project_name=project_name,
        project_files=project_files,
        output_path=output_path,
        include_docker=include_docker
    )


# =============================================================================
# FastAPI Integration
# =============================================================================

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List

export_router = APIRouter(prefix="/api/export", tags=["Export"])


class ExportRequest(BaseModel):
    project_name: str = Field(..., description="Name of the project")
    project_files: Dict[str, str] = Field(..., description="Project files (path -> content)")
    include_docker: bool = Field(True, description="Include Docker configuration")


class ExportResponse(BaseModel):
    success: bool
    project_name: str
    project_slug: str
    file_count: int
    files: List[str]
    download_url: str


@export_router.post("/package", response_model=ExportResponse)
async def create_export_package(request: ExportRequest):
    """
    Create an exportable project package (zip).
    
    Returns a download URL for the packaged project.
    """
    try:
        result = export_project(
            project_name=request.project_name,
            project_files=request.project_files,
            include_docker=request.include_docker
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Export failed")
        
        # Generate download URL
        zip_filename = os.path.basename(result["zip_path"])
        download_url = f"/api/export/download/{zip_filename}"
        
        return ExportResponse(
            success=True,
            project_name=result["project_name"],
            project_slug=result["project_slug"],
            file_count=result["file_count"],
            files=result["files"],
            download_url=download_url
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@export_router.get("/download/{filename}")
async def download_export(filename: str):
    """Download an exported project package."""
    filepath = f"/tmp/{filename}"
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Export not found")
    
    return FileResponse(
        filepath,
        media_type="application/zip",
        filename=filename
    )


if __name__ == "__main__":
    # Test the exporter
    test_files = {
        "frontend/src/App.jsx": "export default function App() { return <div>Hello</div>; }",
        "backend/main.py": "# Test main.py with SANDBOX reference",
    }
    
    result = export_project("Test App", test_files)
    print(f"✅ Export complete: {result}")
