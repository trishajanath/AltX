"""
Enhanced Project Generator - Clean, Modern React + FastAPI Generation
Fixes issues with poor code quality and duplicate file creation
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

class ModernProjectGenerator:
    """Enhanced generator for React + FastAPI projects with clean architecture"""
    
    def __init__(self):
        self.component_templates = {
            'todo': {
                'components': ['TaskList', 'TaskItem', 'AddTask', 'TaskFilter'],
                'apis': [
                    {'path': '/api/tasks', 'methods': ['GET', 'POST']},
                    {'path': '/api/tasks/{id}', 'methods': ['GET', 'PUT', 'DELETE']}
                ],
                'models': ['Task'],
                'features': ['CRUD operations', 'filtering', 'status updates']
            },
            'chat': {
                'components': ['ChatWindow', 'MessageList', 'MessageInput', 'UserList'],
                'apis': [
                    {'path': '/api/messages', 'methods': ['GET', 'POST']},
                    {'path': '/api/chat/ws', 'methods': ['WebSocket']}
                ],
                'models': ['Message', 'User'],
                'features': ['real-time messaging', 'WebSocket support', 'user presence']
            },
            'ecommerce': {
                'components': ['ProductGrid', 'ProductCard', 'Cart', 'Checkout'],
                'apis': [
                    {'path': '/api/products', 'methods': ['GET']},
                    {'path': '/api/cart', 'methods': ['GET', 'POST', 'PUT']},
                    {'path': '/api/orders', 'methods': ['POST']}
                ],
                'models': ['Product', 'CartItem', 'Order'],
                'features': ['product catalog', 'shopping cart', 'checkout flow']
            },
            'blog': {
                'components': ['PostList', 'PostCard', 'PostDetail', 'CommentSection'],
                'apis': [
                    {'path': '/api/posts', 'methods': ['GET', 'POST']},
                    {'path': '/api/posts/{id}', 'methods': ['GET', 'PUT', 'DELETE']},
                    {'path': '/api/comments', 'methods': ['GET', 'POST']}
                ],
                'models': ['Post', 'Comment', 'Author'],
                'features': ['content management', 'comments', 'rich text editing']
            },
            'dashboard': {
                'components': ['Dashboard', 'StatCard', 'Chart', 'DataTable'],
                'apis': [
                    {'path': '/api/stats', 'methods': ['GET']},
                    {'path': '/api/analytics', 'methods': ['GET']},
                    {'path': '/api/reports', 'methods': ['GET']}
                ],
                'models': ['Metric', 'Report', 'ChartData'],
                'features': ['data visualization', 'real-time updates', 'export functionality']
            }
        }
    
    def detect_app_type(self, idea: str) -> str:
        """Detect the app type from the idea description"""
        idea_lower = idea.lower()
        
        # Priority order for detection
        if any(word in idea_lower for word in ['todo', 'task', 'checklist', 'manage tasks']):
            return 'todo'
        elif any(word in idea_lower for word in ['chat', 'messaging', 'conversation', 'talk']):
            return 'chat'
        elif any(word in idea_lower for word in ['ecommerce', 'shop', 'store', 'product', 'buy', 'sell']):
            return 'ecommerce'
        elif any(word in idea_lower for word in ['blog', 'article', 'post', 'content', 'write']):
            return 'blog'
        elif any(word in idea_lower for word in ['dashboard', 'analytics', 'chart', 'data', 'metrics']):
            return 'dashboard'
        else:
            return 'todo'  # Default fallback
    
    async def generate_project(self, project_path: Path, idea: str, project_name: str) -> List[str]:
        """Generate a complete React + FastAPI project"""
        files_created = []
        
        # Detect app type
        app_type = self.detect_app_type(idea)
        template = self.component_templates[app_type]
        
        # Create directories
        frontend_path = project_path / "frontend"
        backend_path = project_path / "backend"
        frontend_path.mkdir(parents=True, exist_ok=True)
        backend_path.mkdir(parents=True, exist_ok=True)
        
        # Generate React frontend
        frontend_files = await self.generate_react_frontend(
            frontend_path, idea, project_name, app_type, template
        )
        files_created.extend([f"frontend/{f}" for f in frontend_files])
        
        # Generate FastAPI backend
        backend_files = await self.generate_fastapi_backend(
            backend_path, idea, project_name, app_type, template
        )
        files_created.extend([f"backend/{f}" for f in backend_files])
        
        # Generate root files
        root_files = await self.generate_root_files(project_path, idea, project_name)
        files_created.extend(root_files)
        
        return files_created
    
    async def generate_react_frontend(self, frontend_path: Path, idea: str, project_name: str, 
                                    app_type: str, template: Dict) -> List[str]:
        """Generate modern React frontend with Vite and TailwindCSS"""
        files_created = []
        
        # Create package.json
        package_json = {
            "name": project_name.lower().replace(" ", "-"),
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
                "@headlessui/react": "^1.7.17"
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
        
        # Create Vite config
        vite_config = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'https://api.xverta.com',
        changeOrigin: true,
      }
    }
  }
})'''
        
        with open(frontend_path / "vite.config.js", "w") as f:
            f.write(vite_config)
        files_created.append("vite.config.js")
        
        # Create Tailwind config
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
        files_created.append("tailwind.config.js")
        
        # Create PostCSS config
        postcss_config = '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}'''
        
        with open(frontend_path / "postcss.config.js", "w") as f:
            f.write(postcss_config)
        files_created.append("postcss.config.js")
        
        # Create index.html
        index_html = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>'''
        
        with open(frontend_path / "index.html", "w") as f:
            f.write(index_html)
        files_created.append("index.html")
        
        # Create src directory
        src_path = frontend_path / "src"
        src_path.mkdir(exist_ok=True)
        components_path = src_path / "components"
        components_path.mkdir(exist_ok=True)
        
        # Create main.jsx
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
        files_created.append("src/main.jsx")
        
        # Create index.css with TailwindCSS
        index_css = '''@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply font-sans antialiased;
  }
}

@layer components {
  .btn {
    @apply px-4 py-2 rounded-md font-medium transition-colors duration-200;
  }
  
  .btn-primary {
    @apply bg-blue-600 text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2;
  }
  
  .btn-secondary {
    @apply bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2;
  }
  
  .card {
    @apply bg-white rounded-lg shadow-sm border border-gray-200;
  }
}'''
        
        with open(src_path / "index.css", "w") as f:
            f.write(index_css)
        files_created.append("src/index.css")
        
        # Generate App.jsx based on app type
        app_jsx = await self.generate_app_component(idea, project_name, app_type, template)
        with open(src_path / "App.jsx", "w") as f:
            f.write(app_jsx)
        files_created.append("src/App.jsx")
        
        # Generate components
        for component in template['components']:
            component_code = await self.generate_react_component(component, app_type, idea)
            with open(components_path / f"{component}.jsx", "w") as f:
                f.write(component_code)
            files_created.append(f"src/components/{component}.jsx")
        
        return files_created
    
    async def generate_fastapi_backend(self, backend_path: Path, idea: str, project_name: str,
                                     app_type: str, template: Dict) -> List[str]:
        """Generate FastAPI backend with proper structure"""
        files_created = []
        
        # Create requirements.txt
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
'''
        
        with open(backend_path / "requirements.txt", "w") as f:
            f.write(requirements)
        files_created.append("requirements.txt")
        
        # Generate main.py
        main_py = await self.generate_fastapi_main(project_name, app_type, template)
        with open(backend_path / "main.py", "w") as f:
            f.write(main_py)
        files_created.append("main.py")
        
        # Generate models.py
        models_py = await self.generate_pydantic_models(app_type, template)
        with open(backend_path / "models.py", "w") as f:
            f.write(models_py)
        files_created.append("models.py")
        
        # Generate routes.py
        routes_py = await self.generate_api_routes(app_type, template)
        with open(backend_path / "routes.py", "w") as f:
            f.write(routes_py)
        files_created.append("routes.py")
        
        # Generate database.py
        database_py = await self.generate_database_setup(app_type)
        with open(backend_path / "database.py", "w") as f:
            f.write(database_py)
        files_created.append("database.py")
        
        return files_created
    
    async def generate_root_files(self, project_path: Path, idea: str, project_name: str) -> List[str]:
        """Generate root configuration files"""
        files_created = []
        
        # Create README.md
        readme = f'''# {project_name}

{idea}

## Tech Stack

- **Frontend**: React 18 + Vite + TailwindCSS
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Authentication**: JWT tokens
- **Real-time**: WebSockets (if applicable)

## Getting Started

### Prerequisites

- Node.js 18+ (for frontend)
- Python 3.9+ (for backend)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd {project_name.lower().replace(" ", "-")}
   ```

2. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

3. **Install backend dependencies**
   ```bash
   cd ../backend
   pip install -r requirements.txt
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8001
   ```

2. **Start the frontend development server**
   ```bash
   cd frontend
   npm run dev
   ```

The application will be available at:
- **Frontend**: https://xverta.com
- **Backend API**: https://api.xverta.com
- **API Documentation**: https://api.xverta.com/docs

## Features

- Modern React frontend with responsive design
- FastAPI backend with automatic API documentation
- Real-time updates and interactions
- Clean, maintainable code structure
- Production-ready configuration

## API Endpoints

The backend provides RESTful API endpoints documented at `/docs` when running.

## Development

This project follows modern development practices:

- **Frontend**: Component-based architecture with hooks
- **Backend**: Clean API design with proper error handling
- **Database**: SQLAlchemy ORM with Pydantic models
- **Styling**: Utility-first CSS with TailwindCSS
- **Type Safety**: TypeScript-ready structure

## License

MIT License
'''
        
        with open(project_path / "README.md", "w") as f:
            f.write(readme)
        files_created.append("README.md")
        
        # Create .gitignore
        gitignore = '''# Dependencies
node_modules/
__pycache__/
*.pyc
.venv/
env/

# Build outputs
dist/
build/
*.egg-info/

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Database
*.db
*.sqlite
*.sqlite3

# Temporary files
tmp/
temp/
'''
        
        with open(project_path / ".gitignore", "w") as f:
            f.write(gitignore)
        files_created.append(".gitignore")
        
        return files_created

    async def generate_app_component(self, idea: str, project_name: str, app_type: str, template: Dict) -> str:
        """Generate the main App.jsx component"""
        
        if app_type == 'todo':
            return '''import React, { useState, useEffect } from 'react'
import TaskList from './components/TaskList'
import AddTask from './components/AddTask'
import TaskFilter from './components/TaskFilter'
import { Plus, CheckCircle } from 'lucide-react'

function App() {
  const [tasks, setTasks] = useState([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTasks()
  }, [])

  const fetchTasks = async () => {
    try {
      const response = await fetch('/api/tasks')
      if (response.ok) {
        const data = await response.json()
        // Ensure we always have an array
        setTasks(Array.isArray(data) ? data : [])
      } else {
        // If API fails, set empty array
        setTasks([])
      }
    } catch (error) {
      console.error('Error fetching tasks:', error)
      // On error, set empty array to prevent crashes
      setTasks([])
    } finally {
      setLoading(false)
    }
  }

  const addTask = async (taskData) => {
    try {
      const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData)
      })
      
      if (response.ok) {
        const newTask = await response.json()
        setTasks(prev => Array.isArray(prev) ? [...prev, newTask] : [newTask])
      }
    } catch (error) {
      console.error('Error adding task:', error)
    }
  }

  const updateTask = async (taskId, updates) => {
    try {
      const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      })
      
      if (response.ok) {
        const updatedTask = await response.json()
        setTasks(prev => Array.isArray(prev) ? prev.map(task => 
          task.id === taskId ? updatedTask : task
        ) : [updatedTask])
      }
    } catch (error) {
      console.error('Error updating task:', error)
    }
  }

  const deleteTask = async (taskId) => {
    try {
      const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        setTasks(prev => Array.isArray(prev) ? prev.filter(task => task.id !== taskId) : [])
      }
    } catch (error) {
      console.error('Error deleting task:', error)
    }
  }

  const filteredTasks = Array.isArray(tasks) ? tasks.filter(task => {
    if (filter === 'active') return !task.completed
    if (filter === 'completed') return task.completed
    return true
  }) : []

  const completedCount = Array.isArray(tasks) ? tasks.filter(task => task.completed).length : 0
  const totalCount = Array.isArray(tasks) ? tasks.length : 0

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <CheckCircle className="h-8 w-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">Task Manager</h1>
          </div>
          <p className="text-gray-600">
            {totalCount === 0 
              ? 'No tasks yet. Add your first task below!' 
              : `${completedCount} of ${totalCount} tasks completed`
            }
          </p>
        </div>

        <div className="space-y-6">
          <AddTask onAdd={addTask} />
          
          {totalCount > 0 && (
            <TaskFilter 
              current={filter} 
              onChange={setFilter}
              counts={{
                all: totalCount,
                active: totalCount - completedCount,
                completed: completedCount
              }}
            />
          )}
          
          <TaskList 
            tasks={filteredTasks}
            onUpdate={updateTask}
            onDelete={deleteTask}
          />
        </div>
      </div>
    </div>
  )
}

export default App'''

        elif app_type == 'chat':
            return '''import React, { useState, useEffect, useRef } from 'react'
import ChatWindow from './components/ChatWindow'
import MessageInput from './components/MessageInput'
import { MessageCircle, Users } from 'lucide-react'

function App() {
  const [messages, setMessages] = useState([])
  const [users, setUsers] = useState([])
  const [currentUser] = useState({ id: 1, name: 'You', avatar: 'User' })
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)

  useEffect(() => {
    fetchMessages()
    connectWebSocket()
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const fetchMessages = async () => {
    try {
      const response = await fetch('/api/messages')
      if (response.ok) {
        const data = await response.json()
        // Ensure we always have an array
        setMessages(Array.isArray(data) ? data : [])
      } else {
        // If API fails, set empty array
        setMessages([])
      }
    } catch (error) {
      console.error('Error fetching messages:', error)
      // On error, set empty array to prevent crashes
      setMessages([])
    }
  }

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/chat/ws`
    
    wsRef.current = new WebSocket(wsUrl)
    
    wsRef.current.onopen = () => {
      setConnected(true)
      console.log('WebSocket connected')
    }
    
    wsRef.current.onmessage = (event) => {
      const message = JSON.parse(event.data)
      setMessages(prev => Array.isArray(prev) ? [...prev, message] : [message])
    }
    
    wsRef.current.onclose = () => {
      setConnected(false)
      console.log('WebSocket disconnected')
      // Attempt to reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000)
    }
  }

  const sendMessage = async (content) => {
    const messageData = {
      content,
      user_id: currentUser.id,
      user_name: currentUser.name,
      timestamp: new Date().toISOString()
    }

    // Send via WebSocket if connected, otherwise use REST API
    if (connected && wsRef.current) {
      wsRef.current.send(JSON.stringify(messageData))
    } else {
      try {
        const response = await fetch('/api/messages', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(messageData)
        })
        
        if (response.ok) {
          const newMessage = await response.json()
          setMessages(prev => Array.isArray(prev) ? [...prev, newMessage] : [newMessage])
        }
      } catch (error) {
        console.error('Error sending message:', error)
      }
    }
  }

  return (
    <div className="h-screen bg-gray-100 flex flex-col">
      <header className="bg-white shadow-sm border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MessageCircle className="h-8 w-8 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">Chat Room</h1>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`h-3 w-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-600">
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-gray-500" />
              <span className="text-sm text-gray-600">
                {users.length || 1} online
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
        <ChatWindow 
          messages={messages} 
          currentUser={currentUser}
        />
        
        <MessageInput 
          onSend={sendMessage}
          disabled={!connected}
          placeholder={connected ? "Type your message..." : "Connecting..."}
        />
      </div>
    </div>
  )
}

export default App'''

        # Default fallback for other app types
        return f'''import React, {{ useState, useEffect }} from 'react'
import {{ Home, Sparkles }} from 'lucide-react'

function App() {{
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {{
    fetchData()
  }}, [])

  const fetchData = async () => {{
    try {{
      const response = await fetch('/api/data')
      if (response.ok) {{
        const result = await response.json()
        // Ensure we always have an array
        setData(Array.isArray(result) ? result : [])
      }} else {{
        // If API fails, set empty array
        setData([])
      }}
    }} catch (error) {{
      console.error('Error fetching data:', error)
      // On error, set empty array to prevent crashes
      setData([])
    }} finally {{
      setLoading(false)
    }}
  }}

  if (loading) {{
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }}

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto py-8 px-4">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="h-10 w-10 text-blue-600" />
            <h1 className="text-4xl font-bold text-gray-900">{project_name}</h1>
          </div>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            {idea}
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {{/* Add your components here */}}
        </div>
      </div>
    </div>
  )
}}

export default App'''

    async def generate_react_component(self, component_name: str, app_type: str, idea: str) -> str:
        """Generate individual React components based on type"""
        
        if app_type == 'todo':
            if component_name == 'TaskList':
                return '''import React from 'react'
import TaskItem from './TaskItem'

function TaskList({ tasks, onUpdate, onDelete }) {
  // Ensure tasks is always an array
  const taskArray = Array.isArray(tasks) ? tasks : []
  
  if (taskArray.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 text-lg mb-2">No tasks found</div>
        <div className="text-gray-500">Add a task above to get started</div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {taskArray.map(task => (
        <TaskItem
          key={task.id}
          task={task}
          onUpdate={onUpdate}
          onDelete={onDelete}
        />
      ))}
    </div>
  )
}

export default TaskList'''

            elif component_name == 'TaskItem':
                return '''import React, { useState } from 'react'
import { Check, X, Edit3, Trash2 } from 'lucide-react'

function TaskItem({ task, onUpdate, onDelete }) {
  const [isEditing, setIsEditing] = useState(false)
  const [editText, setEditText] = useState(task.title)

  const handleToggleComplete = () => {
    onUpdate(task.id, { ...task, completed: !task.completed })
  }

  const handleEdit = () => {
    if (isEditing) {
      onUpdate(task.id, { ...task, title: editText })
    }
    setIsEditing(!isEditing)
  }

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this task?')) {
      onDelete(task.id)
    }
  }

  return (
    <div className={`card p-4 transition-all duration-200 ${
      task.completed ? 'bg-green-50 border-green-200' : 'hover:shadow-md'
    }`}>
      <div className="flex items-center gap-3">
        <button
          onClick={handleToggleComplete}
          className={`flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${
            task.completed
              ? 'bg-green-500 border-green-500 text-white'
              : 'border-gray-300 hover:border-green-500'
          }`}
        >
          {task.completed && <Check className="h-4 w-4" />}
        </button>

        <div className="flex-1">
          {isEditing ? (
            <input
              type="text"
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleEdit()}
              className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              autoFocus
            />
          ) : (
            <div className={`${
              task.completed ? 'line-through text-gray-500' : 'text-gray-900'
            }`}>
              <h3 className="font-medium">{task.title}</h3>
              {task.description && (
                <p className="text-sm text-gray-600 mt-1">{task.description}</p>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleEdit}
            className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
            title={isEditing ? 'Save' : 'Edit'}
          >
            <Edit3 className="h-4 w-4" />
          </button>
          
          <button
            onClick={handleDelete}
            className="p-1 text-gray-400 hover:text-red-600 transition-colors"
            title="Delete"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default TaskItem'''

            elif component_name == 'AddTask':
                return '''import React, { useState } from 'react'
import { Plus } from 'lucide-react'

function AddTask({ onAdd }) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [isExpanded, setIsExpanded] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!title.trim()) return

    setIsSubmitting(true)
    try {
      await onAdd({
        title: title.trim(),
        description: description.trim(),
        completed: false
      })
      
      setTitle('')
      setDescription('')
      setIsExpanded(false)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="card p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex items-center gap-3">
          <Plus className="h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Add a new task..."
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onFocus={() => setIsExpanded(true)}
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isSubmitting}
          />
        </div>

        {isExpanded && (
          <div className="space-y-4 ml-8">
            <textarea
              placeholder="Add a description (optional)..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              disabled={isSubmitting}
            />
            
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={!title.trim() || isSubmitting}
                className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Adding...' : 'Add Task'}
              </button>
              
              <button
                type="button"
                onClick={() => {
                  setIsExpanded(false)
                  setTitle('')
                  setDescription('')
                }}
                className="btn btn-secondary"
                disabled={isSubmitting}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  )
}

export default AddTask'''

            elif component_name == 'TaskFilter':
                return '''import React from 'react'

function TaskFilter({ current, onChange, counts }) {
  const filters = [
    { key: 'all', label: 'All', count: counts.all },
    { key: 'active', label: 'Active', count: counts.active },
    { key: 'completed', label: 'Completed', count: counts.completed }
  ]

  return (
    <div className="flex justify-center">
      <div className="bg-white rounded-lg p-1 shadow-sm border border-gray-200">
        <div className="flex gap-1">
          {filters.map(filter => (
            <button
              key={filter.key}
              onClick={() => onChange(filter.key)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                current === filter.key
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              {filter.label}
              {filter.count !== undefined && (
                <span className={`ml-1 text-xs ${
                  current === filter.key ? 'text-blue-200' : 'text-gray-400'
                }`}>
                  ({filter.count})
                </span>
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default TaskFilter'''

        # Generate other component types similarly...
        # For now, return a basic component structure
        return f'''import React from 'react'

function {component_name}() {{
  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">{component_name}</h2>
      <p className="text-gray-600">Component implementation goes here</p>
    </div>
  )
}}

export default {component_name}'''

    async def generate_fastapi_main(self, project_name: str, app_type: str, template: Dict) -> str:
        """Generate FastAPI main.py with proper structure"""
        return '''from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

from routes import router as api_router
from database import init_db

load_dotenv()

app = FastAPI(
    title="''' + project_name + ''' API",
    description="Modern FastAPI backend for ''' + project_name.lower() + '''",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://xverta.com", "https://www.xverta.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {
        "message": "Welcome to ''' + project_name + ''' API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "''' + project_name.lower() + '''"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
'''

    async def generate_pydantic_models(self, app_type: str, template: Dict) -> str:
        """Generate Pydantic models for the app type"""
        if app_type == 'todo':
            return '''from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: bool = False

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: Optional[bool] = None

class Task(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime
    updated_at: datetime
'''
        
        elif app_type == 'chat':
            return '''from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    user_name: str = Field(..., min_length=1, max_length=50)

class MessageCreate(MessageBase):
    user_id: Optional[int] = None

class Message(MessageBase):
    id: int
    user_id: Optional[int] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    avatar: Optional[str] = None

class User(UserBase):
    id: int
    is_online: bool = True

    class Config:
        from_attributes = True
'''

        # Default model structure
        return '''from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

class Item(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
'''

    async def generate_api_routes(self, app_type: str, template: Dict) -> str:
        """Generate API routes for the app type"""
        if app_type == 'todo':
            return '''from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from database import get_db, Task as TaskDB
from models import Task, TaskCreate, TaskUpdate, TaskResponse

router = APIRouter()

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(db: Session = Depends(get_db)):
    """Get all tasks"""
    try:
        tasks = db.query(TaskDB).order_by(TaskDB.created_at.desc()).all()
        return tasks
    except Exception as e:
        # If database isn't ready, return empty list
        print(f"Database error in get_tasks: {e}")
        return []

@router.post("/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    db_task = TaskDB(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task"""
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task"""
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    return task

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task"""
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}

@router.get("/tasks/stats/summary")
async def get_task_stats(db: Session = Depends(get_db)):
    """Get task statistics"""
    total = db.query(TaskDB).count()
    completed = db.query(TaskDB).filter(TaskDB.completed == True).count()
    active = total - completed
    
    return {
        "total": total,
        "completed": completed,
        "active": active,
        "completion_rate": round((completed / total * 100) if total > 0 else 0, 2)
    }
'''

        # Default API routes
        return '''from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from models import Item, ItemCreate, ItemUpdate

router = APIRouter()

# In-memory storage (replace with database in production)
items = []
next_id = 1

@router.get("/data", response_model=List[Item])
async def get_items():
    """Get all items"""
    try:
        return items
    except Exception as e:
        # If there's any error, return empty list
        print(f"Error in get_items: {e}")
        return []

@router.post("/data", response_model=Item)
async def create_item(item: ItemCreate):
    """Create a new item"""
    global next_id
    new_item = Item(
        id=next_id,
        **item.dict(),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    items.append(new_item)
    next_id += 1
    return new_item

@router.get("/data/{item_id}", response_model=Item)
async def get_item(item_id: int):
    """Get a specific item"""
    item = next((item for item in items if item.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/data/{item_id}", response_model=Item)
async def update_item(item_id: int, item_update: ItemUpdate):
    """Update an item"""
    item = next((item for item in items if item.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = item_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    item.updated_at = datetime.now()
    return item

@router.delete("/data/{item_id}")
async def delete_item(item_id: int):
    """Delete an item"""
    global items
    item = next((item for item in items if item.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    items = [item for item in items if item.id != item_id]
    return {"message": "Item deleted successfully"}
'''

    async def generate_database_setup(self, app_type: str) -> str:
        """Generate database configuration"""
        if app_type == 'todo':
            return '''from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

        # Default database setup
        return '''from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''