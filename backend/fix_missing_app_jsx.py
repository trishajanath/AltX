#!/usr/bin/env python3
"""
Fix script to add missing App.jsx files to generated projects
"""

from pathlib import Path


def create_fallback_app_jsx(project_name: str) -> str:
    """Create a basic fallback App.jsx component"""
    return f'''import React from 'react';

function App() {{
  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Welcome to {project_name}</h1>
        <p className="text-gray-300 mb-4">Your application is ready!</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-md mx-auto">
          <div className="bg-gray-800 p-4 rounded-lg">
            <h3 className="font-semibold mb-2">Frontend</h3>
            <p className="text-sm text-gray-400">React + Vite + Tailwind CSS</p>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg">
            <h3 className="font-semibold mb-2">Backend</h3>
            <p className="text-sm text-gray-400">FastAPI + Python</p>
          </div>
        </div>
        <div className="mt-8">
          <p className="text-blue-400 text-sm">Ready for development!</p>
        </div>
      </div>
    </div>
  );
}}

export default App;'''


def fix_missing_app_jsx():
    """Find and fix projects missing App.jsx"""
    projects_dir = Path("generated_projects")
    
    if not projects_dir.exists():
        print("No generated_projects directory found")
        return
    
    fixed_count = 0
    total_projects = 0
    
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue
            
        total_projects += 1
        frontend_src = project_dir / "frontend" / "src"
        app_jsx_path = frontend_src / "App.jsx"
        
        if frontend_src.exists() and not app_jsx_path.exists():
            print(f"🔧 Fixing missing App.jsx in {project_dir.name}")
            
            try:
                # Extract project name from directory
                project_name = project_dir.name.replace("app-", "").replace("-", " ").title()
                if project_name.startswith("App "):
                    project_name = project_name[4:]  # Remove "App " prefix
                
                if not project_name or len(project_name) < 3:
                    project_name = "Your Project"
                
                # Create the fallback App.jsx
                fallback_content = create_fallback_app_jsx(project_name)
                app_jsx_path.write_text(fallback_content, encoding="utf-8")
                
                print(f"✅ Created App.jsx for {project_dir.name}")
                fixed_count += 1
                
            except Exception as e:
                print(f"❌ Failed to fix {project_dir.name}: {e}")
        else:
            if app_jsx_path.exists():
                print(f"✓ {project_dir.name} already has App.jsx")
            else:
                print(f"⚠️ {project_dir.name} missing frontend/src directory")
    
    print(f"\n📊 Summary:")
    print(f"   Total projects: {total_projects}")
    print(f"   Fixed projects: {fixed_count}")
    print(f"   No issues: {total_projects - fixed_count}")


if __name__ == "__main__":
    fix_missing_app_jsx()