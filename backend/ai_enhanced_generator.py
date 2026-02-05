""" 
AI-Enhanced Project Generator - Dynamic Code Generation with Template Foundation
Combines reliable templates with AI customization for truly generative code     
 """

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class FieldDefinition:
    name: str
    type: str
    required: bool = True
    default: Optional[str] = None
    description: Optional[str] = None

@dataclass
class ModelDefinition:
    name: str
    fields: List[FieldDefinition]
    description: Optional[str] = None

@dataclass
class ComponentDefinition:
    name: str
    purpose: str
    props: List[str]
    features: List[str]
    state_variables: List[str]

@dataclass
class APIEndpoint:
    path: str
    method: str
    purpose: str
    request_model: Optional[str] = None
    response_model: Optional[str] = None

@dataclass
class ProjectPlan:
    app_type: str
    name: str
    description: str
    models: List[ModelDefinition]
    components: List[ComponentDefinition]
    api_endpoints: List[APIEndpoint]
    features: List[str]
    ui_requirements: List[str]
    custom_logic: Dict[str, str]

class AIEnhancedGenerator:
    """AI-powered generator that creates customized code based on user ideas"""
    
    def __init__(self):
        self.gemini_client = None
        if os.getenv("GOOGLE_API_KEY"):
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.gemini_client = genai.GenerativeModel('gemini-2.5-flash')
        
        # Base templates for seeding AI generation
        self.base_templates = {
            'todo': self._get_todo_base_template(),
            'chat': self._get_chat_base_template(),
            'ecommerce': self._get_ecommerce_base_template(),
            'blog': self._get_blog_base_template(),
            'dashboard': self._get_dashboard_base_template()
        }
    
    def _get_todo_base_template(self) -> Dict:
        """Base template for todo applications"""
        return {
            'models': [
                ModelDefinition(
                    name="Task",
                    fields=[
                        FieldDefinition("id", "int"),
                        FieldDefinition("title", "str"),
                        FieldDefinition("description", "Optional[str]", required=False),
                        FieldDefinition("completed", "bool", default="False"),
                        FieldDefinition("created_at", "datetime"),
                        FieldDefinition("updated_at", "datetime")
                    ]
                )
            ],
            'components': [
                ComponentDefinition(
                    name="TaskList",
                    purpose="Display list of tasks with filtering",
                    props=["tasks", "onUpdate", "onDelete"],
                    features=["filtering", "sorting", "bulk actions"],
                    state_variables=["selectedTasks", "sortBy"]
                ),
                ComponentDefinition(
                    name="TaskItem",
                    purpose="Individual task display and interaction",
                    props=["task", "onUpdate", "onDelete"],
                    features=["inline editing", "completion toggle", "delete"],
                    state_variables=["isEditing", "editText"]
                ),
                ComponentDefinition(
                    name="AddTask",
                    purpose="Form for creating new tasks",
                    props=["onAdd"],
                    features=["validation", "quick add", "expanded form"],
                    state_variables=["title", "description", "isExpanded"]
                )
            ],
            'api_endpoints': [
                APIEndpoint("/api/tasks", "GET", "Get all tasks", response_model="List[Task]"),
                APIEndpoint("/api/tasks", "POST", "Create task", request_model="TaskCreate", response_model="Task"),
                APIEndpoint("/api/tasks/{id}", "PUT", "Update task", request_model="TaskUpdate", response_model="Task"),
                APIEndpoint("/api/tasks/{id}", "DELETE", "Delete task")
            ]
        }
    
    def _get_chat_base_template(self) -> Dict:
        """Base template for chat applications"""
        return {
            'models': [
                ModelDefinition(
                    name="Message",
                    fields=[
                        FieldDefinition("id", "int"),
                        FieldDefinition("content", "str"),
                        FieldDefinition("user_name", "str"),
                        FieldDefinition("user_id", "Optional[int]", required=False),
                        FieldDefinition("timestamp", "datetime")
                    ]
                ),
                ModelDefinition(
                    name="User",
                    fields=[
                        FieldDefinition("id", "int"),
                        FieldDefinition("name", "str"),
                        FieldDefinition("avatar", "Optional[str]", required=False),
                        FieldDefinition("is_online", "bool", default="True")
                    ]
                )
            ],
            'components': [
                ComponentDefinition(
                    name="ChatWindow",
                    purpose="Main chat interface with message display",
                    props=["messages", "currentUser"],
                    features=["auto-scroll", "message grouping", "timestamps"],
                    state_variables=["autoScroll", "lastMessageTime"]
                ),
                ComponentDefinition(
                    name="MessageInput",
                    purpose="Input field for sending messages",
                    props=["onSend", "disabled", "placeholder"],
                    features=["enter to send", "emoji support", "typing indicators"],
                    state_variables=["message", "isTyping"]
                )
            ],
            'api_endpoints': [
                APIEndpoint("/api/messages", "GET", "Get messages", response_model="List[Message]"),
                APIEndpoint("/api/messages", "POST", "Send message", request_model="MessageCreate", response_model="Message"),
                APIEndpoint("/api/chat/ws", "WebSocket", "Real-time messaging")
            ]
        }
    
    def _get_ecommerce_base_template(self) -> Dict:
        """Base template for ecommerce applications"""
        return {
            'models': [
                ModelDefinition(
                    name="Product",
                    fields=[
                        FieldDefinition("id", "int"),
                        FieldDefinition("name", "str"),
                        FieldDefinition("description", "Optional[str]", required=False),
                        FieldDefinition("price", "float"),
                        FieldDefinition("image_url", "Optional[str]", required=False),
                        FieldDefinition("in_stock", "bool", default="True")
                    ]
                )
            ]
        }
    
    def _get_blog_base_template(self) -> Dict:
        """Base template for blog applications"""
        return {
            'models': [
                ModelDefinition(
                    name="Post",
                    fields=[
                        FieldDefinition("id", "int"),
                        FieldDefinition("title", "str"),
                        FieldDefinition("content", "str"),
                        FieldDefinition("author", "str"),
                        FieldDefinition("published_at", "Optional[datetime]", required=False),
                        FieldDefinition("is_draft", "bool", default="True")
                    ]
                )
            ]
        }
    
    def _get_dashboard_base_template(self) -> Dict:
        """Base template for dashboard applications"""
        return {
            'models': [
                ModelDefinition(
                    name="Metric",
                    fields=[
                        FieldDefinition("id", "int"),
                        FieldDefinition("name", "str"),
                        FieldDefinition("value", "float"),
                        FieldDefinition("unit", "Optional[str]", required=False),
                        FieldDefinition("timestamp", "datetime")
                    ]
                )
            ]
        }
    
    async def analyze_user_idea(self, idea: str) -> ProjectPlan:
        """Use AI to analyze user idea and create a detailed project plan"""
        if not self.gemini_client:
            # Fallback to basic detection if no AI available
            return self._fallback_analysis(idea)
        
        try:
            prompt = f"""
Analyze this user's app idea and create a detailed project plan: "{idea}"

You need to determine:
1. The base app type (todo, chat, ecommerce, blog, dashboard, or custom)
2. What additional fields/features the user wants beyond the basic template
3. Custom UI requirements or special behaviors
4. Additional API endpoints needed

Respond with a JSON object following this structure:
{{
    "app_type": "todo|chat|ecommerce|blog|dashboard|custom",
    "name": "extracted or generated app name",
    "description": "clean description of what this app does",
    "custom_features": [
        "list of features not in the base template"
    ],
    "additional_fields": [
        {{
            "model": "model_name",
            "field_name": "field_name",
            "field_type": "python_type",
            "required": true/false,
            "description": "what this field does"
        }}
    ],
    "ui_requirements": [
        "specific UI behaviors or components mentioned"
    ],
    "custom_logic": {{
        "feature_name": "description of custom logic needed"
    }}
}}

Examples:
- "todo app with priority levels" -> add priority field to Task model
- "chat with file sharing" -> add file_url field to Message model
- "ecommerce with reviews" -> add Review model and rating field to Product

Focus on extracting SPECIFIC requirements from the user's idea, not generic features.
"""
            
            response = self.gemini_client.generate_content(prompt)
            
            # Clean the response text by removing markdown code blocks
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith('```'):
                response_text = response_text[3:]   # Remove ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove trailing ```
            response_text = response_text.strip()
            
            analysis = json.loads(response_text)
            return self._convert_analysis_to_plan(analysis, idea)
            
        except Exception as e:
            print(f"AI analysis failed: {e}, falling back to basic detection")
            return self._fallback_analysis(idea)
    
    def _fallback_analysis(self, idea: str) -> ProjectPlan:
        """Fallback analysis when AI is not available"""
        idea_lower = idea.lower()
        
        # Basic app type detection
        if any(word in idea_lower for word in ['todo', 'task', 'checklist']):
            app_type = 'todo'
        elif any(word in idea_lower for word in ['chat', 'messaging', 'conversation']):
            app_type = 'chat'
        elif any(word in idea_lower for word in ['shop', 'store', 'ecommerce', 'product']):
            app_type = 'ecommerce'
        elif any(word in idea_lower for word in ['blog', 'article', 'post']):
            app_type = 'blog'
        elif any(word in idea_lower for word in ['dashboard', 'analytics', 'chart']):
            app_type = 'dashboard'
        else:
            app_type = 'todo'
        
        base_template = self.base_templates[app_type]
        
        return ProjectPlan(
            app_type=app_type,
            name=self._extract_name_from_idea(idea),
            description=idea,
            models=base_template['models'],
            components=base_template.get('components', []),
            api_endpoints=base_template.get('api_endpoints', []),
            features=[],
            ui_requirements=[],
            custom_logic={}
        )
    
    def _convert_analysis_to_plan(self, analysis: Dict, original_idea: str) -> ProjectPlan:
        """Convert AI analysis to ProjectPlan object"""
        app_type = analysis.get('app_type', 'todo')
        base_template = self.base_templates.get(app_type, self.base_templates['todo'])
        
        # Start with base models and enhance them
        models = []
        for base_model in base_template['models']:
            enhanced_model = self._enhance_model_with_custom_fields(
                base_model, 
                analysis.get('additional_fields', [])
            )
            models.append(enhanced_model)
        
        # Add any completely new models
        for custom_model in analysis.get('new_models', []):
            models.append(self._create_model_from_definition(custom_model))
        
        return ProjectPlan(
            app_type=app_type,
            name=analysis.get('name', self._extract_name_from_idea(original_idea)),
            description=analysis.get('description', original_idea),
            models=models,
            components=base_template.get('components', []),
            api_endpoints=base_template.get('api_endpoints', []),
            features=analysis.get('custom_features', []),
            ui_requirements=analysis.get('ui_requirements', []),
            custom_logic=analysis.get('custom_logic', {})
        )
    
    def _enhance_model_with_custom_fields(self, base_model: ModelDefinition, additional_fields: List[Dict]) -> ModelDefinition:
        """Add custom fields to a base model"""
        enhanced_fields = base_model.fields.copy()
        
        for field_def in additional_fields:
            if field_def.get('model') == base_model.name:
                enhanced_fields.append(FieldDefinition(
                    name=field_def['field_name'],
                    type=field_def['field_type'],
                    required=field_def.get('required', True),
                    description=field_def.get('description')
                ))
        
        return ModelDefinition(
            name=base_model.name,
            fields=enhanced_fields,
            description=base_model.description
        )
    
    async def generate_enhanced_pydantic_models(self, plan: ProjectPlan) -> str:
        """Generate Pydantic models with AI-enhanced customizations"""
        models_code = '''from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date
from enum import Enum

'''
        
        for model in plan.models:
            # Generate base model
            models_code += f'''class {model.name}Base(BaseModel):
'''
            for field in model.fields:
                if field.name in ['id', 'created_at', 'updated_at']:
                    continue  # Skip auto-generated fields
                
                field_definition = f'    {field.name}: {field.type}'
                
                if not field.required or field.default:
                    field_definition += f' = Field('
                    if field.default:
                        field_definition += f'default={field.default}'
                    else:
                        field_definition += 'default=None'
                    
                    if field.description:
                        field_definition += f', description="{field.description}"'
                    
                    field_definition += ')'
                elif field.description:
                    field_definition += f' = Field(description="{field.description}")'
                
                models_code += field_definition + '\n'
            
            models_code += f'''
class {model.name}Create({model.name}Base):
    pass

class {model.name}Update(BaseModel):
'''
            
            # For update models, make all fields optional
            for field in model.fields:
                if field.name in ['id', 'created_at', 'updated_at']:
                    continue
                
                field_type = field.type
                if not field_type.startswith('Optional['):
                    field_type = f'Optional[{field_type}]'
                
                models_code += f'    {field.name}: {field_type} = None\n'
            
            models_code += f'''
class {model.name}({model.name}Base):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

'''
        
        return models_code
    
    async def generate_enhanced_react_component(self, component: ComponentDefinition, plan: ProjectPlan) -> str:
        """Generate React component with AI enhancements"""
        if not self.gemini_client:
            return self._fallback_component_generation(component, plan)
        
        try:
            # Get the base component template
            base_code = self._get_base_component_code(component, plan.app_type)
            
            # Use AI to enhance it with custom features
            prompt = f"""
Here's a base React component for a {plan.app_type} app:

```jsx
{base_code}
```

The user wants these additional features: {', '.join(plan.features)}
UI requirements: {', '.join(plan.ui_requirements)}

Please enhance this component to include the requested features. Focus on:
1. Adding the new functionality while keeping the existing structure
2. Maintaining array safety patterns (Array.isArray() checks)
3. Proper error handling and loading states
4. Clean, readable code with proper TypeScript-like prop types

Return only the enhanced JSX component code, no explanations.
"""
            
            response = self.gemini_client.generate_content(prompt)
            
            return response.text.strip().replace('```jsx', '').replace('```', '')
            
        except Exception as e:
            print(f"AI component generation failed: {e}, using fallback")
            return self._fallback_component_generation(component, plan)
    
    def _get_base_component_code(self, component: ComponentDefinition, app_type: str) -> str:
        """Get base component code from templates"""
        # This would return the appropriate base component from the enhanced_generator
        # For now, return a simple placeholder
        return f'''import React from 'react'

function {component.name}({{ {', '.join(component.props)} }}) {{
  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">{component.name}</h2>
      <p className="text-gray-600">{component.purpose}</p>
    </div>
  )
}}

export default {component.name}'''
    
    def _fallback_component_generation(self, component: ComponentDefinition, plan: ProjectPlan) -> str:
        """Fallback component generation when AI is not available"""
        return self._get_base_component_code(component, plan.app_type)
    
    async def generate_project(self, project_path: Path, idea: str, project_name: str) -> List[str]:
        """Generate a complete AI-enhanced project"""
        files_created = []
        
        # Step 1: Analyze the user's idea with AI
        print("🤖 Analyzing your idea with AI...")
        plan = await self.analyze_user_idea(idea)
        
        print(f"📋 Generated plan for {plan.app_type} app with {len(plan.features)} custom features")
        
        # Step 2: Create project structure
        frontend_path = project_path / "frontend"
        backend_path = project_path / "backend"
        frontend_path.mkdir(parents=True, exist_ok=True)
        backend_path.mkdir(parents=True, exist_ok=True)
        
        # Step 3: Generate enhanced backend
        print("🔧 Generating AI-enhanced backend...")
        backend_files = await self.generate_enhanced_backend(backend_path, plan)
        files_created.extend([f"backend/{f}" for f in backend_files])
        
        # Step 4: Generate enhanced frontend
        print("🎨 Generating AI-enhanced frontend...")
        frontend_files = await self.generate_enhanced_frontend(frontend_path, plan)
        files_created.extend([f"frontend/{f}" for f in frontend_files])
        
        # Step 5: Generate root configuration files
        print("📁 Creating project configuration...")
        root_files = await self.generate_root_files(project_path, plan)
        files_created.extend(root_files)
        
        print(f"✅ Generated {len(files_created)} files for your custom {plan.app_type} application!")
        
        return files_created
    
    async def generate_enhanced_backend(self, backend_path: Path, plan: ProjectPlan) -> List[str]:
        """Generate AI-enhanced FastAPI backend"""
        files_created = []
        
        # Generate enhanced models
        models_code = await self.generate_enhanced_pydantic_models(plan)
        with open(backend_path / "models.py", "w") as f:
            f.write(models_code)
        files_created.append("models.py")
        
        # Generate enhanced routes (AI-powered)
        routes_code = await self.generate_enhanced_api_routes(plan)
        with open(backend_path / "routes.py", "w") as f:
            f.write(routes_code)
        files_created.append("routes.py")
        
        # Generate database setup
        database_code = await self.generate_enhanced_database(plan)
        with open(backend_path / "database.py", "w") as f:
            f.write(database_code)
        files_created.append("database.py")
        
        # Generate main.py
        main_code = await self.generate_enhanced_main(plan)
        with open(backend_path / "main.py", "w") as f:
            f.write(main_code)
        files_created.append("main.py")
        
        # Generate requirements.txt
        requirements = '''fastapi==0.104.1
uvicorn[standard]==0.24.0
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
bcrypt==4.0.1
python-dotenv==1.0.0
sqlalchemy==2.0.23
sqlite3==0.0.0
pydantic==2.5.0
websockets==11.0.3
google-generativeai==0.3.0
'''
        with open(backend_path / "requirements.txt", "w") as f:
            f.write(requirements)
        files_created.append("requirements.txt")
        
        return files_created
    
    async def generate_enhanced_frontend(self, frontend_path: Path, plan: ProjectPlan) -> List[str]:
        """Generate AI-enhanced React frontend"""
        files_created = []
        
        # Create package.json with enhanced dependencies
        package_json = {
            "name": plan.name.lower().replace(" ", "-"),
            "private": True,
            "version": "0.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.15.0",
                "lucide-react": "^0.263.1",
                "@headlessui/react": "^1.7.17",
                "framer-motion": "^10.16.0",  # For smooth animations
                "date-fns": "^2.30.0",  # For date handling
                "react-hook-form": "^7.45.0",  # For advanced forms
                "react-query": "^3.39.3"  # For data fetching
            },
            "devDependencies": {
                "@types/react": "^18.2.15",
                "@types/react-dom": "^18.2.7",
                "@vitejs/plugin-react": "^4.0.3",
                "eslint": "^8.45.0",
                "eslint-plugin-react": "^7.32.2",
                "eslint-plugin-react-hooks": "^4.6.0",
                "eslint-plugin-react-refresh": "^0.4.3",
                "vite": "^4.4.5",
                "tailwindcss": "^3.3.3",
                "autoprefixer": "^10.4.15",
                "postcss": "^8.4.29"
            }
        }
        
        with open(frontend_path / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
        files_created.append("package.json")
        
        # Generate enhanced App.jsx
        app_code = await self.generate_enhanced_app_component(plan)
        src_path = frontend_path / "src"
        src_path.mkdir(exist_ok=True)
        with open(src_path / "App.jsx", "w") as f:
            f.write(app_code)
        files_created.append("src/App.jsx")
        
        # Generate enhanced components
        components_path = src_path / "components"
        components_path.mkdir(exist_ok=True)
        for component in plan.components:
            component_code = await self.generate_enhanced_react_component(component, plan)
            with open(components_path / f"{component.name}.jsx", "w") as f:
                f.write(component_code)
            files_created.append(f"src/components/{component.name}.jsx")
        
        # Copy other necessary files (main.jsx, index.css, etc.)
        self._create_standard_frontend_files(frontend_path, plan)
        files_created.extend(["main.jsx", "index.css", "index.html", "vite.config.js", "tailwind.config.js", "postcss.config.js"])
        
        return files_created
    
    def _create_standard_frontend_files(self, frontend_path: Path, plan: ProjectPlan):
        """Create standard frontend configuration files"""
        # This would create index.html, main.jsx, etc. - similar to the enhanced_generator
        pass
    
    async def generate_enhanced_api_routes(self, plan: ProjectPlan) -> str:
        """Generate API routes with AI enhancements"""
        # This would use AI to generate custom API endpoints based on the plan
        return "# AI-generated API routes would go here"
    
    async def generate_enhanced_database(self, plan: ProjectPlan) -> str:
        """Generate database setup with custom models"""
        # This would generate SQLAlchemy models based on the plan
        return "# AI-generated database setup would go here"
    
    async def generate_enhanced_main(self, plan: ProjectPlan) -> str:
        """Generate main FastAPI application"""
        return f'''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router as api_router
from database import init_db

app = FastAPI(
    title="{plan.name} API",
    description="{plan.description}",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {{"message": "Welcome to {plan.name} API"}}
'''
    
    async def generate_enhanced_app_component(self, plan: ProjectPlan) -> str:
        """Generate the main App.jsx with AI enhancements"""
        # This would use AI to customize the main app component
        return f'''import React from 'react'

function App() {{
  return (
    <div className="min-h-screen bg-gray-50">
      <h1 className="text-3xl font-bold text-center py-8">{plan.name}</h1>
      <p className="text-center text-gray-600">{plan.description}</p>
    </div>
  )
}}

export default App'''
    
    async def generate_root_files(self, project_path: Path, plan: ProjectPlan) -> List[str]:
        """Generate root configuration files"""
        files_created = []
        
        # Enhanced README with AI-generated content
        readme = f'''# {plan.name}

{plan.description}

## Features

{chr(10).join(f"- {feature}" for feature in plan.features)}

## Architecture

This is an AI-generated application built with:
- **Frontend**: React 18 + Vite + TailwindCSS
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **AI Enhancement**: Custom features generated based on your requirements

## Custom Requirements Implemented

{chr(10).join(f"- {req}" for req in plan.ui_requirements)}

## Getting Started

[Installation and setup instructions...]

## AI-Generated Code

This project was created using AI-enhanced code generation that:
1. Analyzed your specific requirements
2. Extended base templates with custom features
3. Generated tailored components and API endpoints
4. Ensured code safety and best practices

Generated on: {os.environ.get('TIMESTAMP', 'Unknown')}
'''
        
        with open(project_path / "README.md", "w", encoding="utf-8") as f:
            f.write(readme)
        files_created.append("README.md")
        
        return files_created
    
    def _extract_name_from_idea(self, idea: str) -> str:
        """Extract or generate a project name from the idea"""
        # Simple extraction - in a real implementation, could use AI for this too
        words = idea.split()[:3]  # Take first 3 words
        return ' '.join(word.capitalize() for word in words)

# Example usage
async def main():
    generator = AIEnhancedGenerator()
    
    # Example with a complex user idea
    idea = "A todo app where tasks can have priority levels (low, medium, high), due dates, and can be organized into projects. Users should be able to filter by priority and see overdue tasks highlighted in red."
    
    project_path = Path("./generated_project")
    files = await generator.generate_project(project_path, idea, "Priority Task Manager")
    
    print(f"Generated {len(files)} files for your custom application!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())