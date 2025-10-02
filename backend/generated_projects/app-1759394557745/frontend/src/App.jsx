import React, { useState, useEffect, useCallback, useMemo } from 'react';

// Import all React Bits components with comprehensive fallbacks
let Button, Card, CardHeader, CardBody;
try {
  const ButtonModule = require('./components/ui/Button');
  Button = ButtonModule.Button;
} catch (error) {
  // Fallback Button
  Button = ({ children, variant = 'primary', size = 'md', className = '', ...props }) => {
    const variants = {
      primary: 'bg-blue-600 hover:bg-blue-700 text-white',
      secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
      outline: 'border border-gray-300 hover:bg-gray-50 text-gray-700'
    };
    const sizes = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base', 
      lg: 'px-6 py-3 text-lg'
    };
    return (
      <button 
        className={`inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${variants[variant]} ${sizes[size]} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  };
}

try {
  const CardModule = require('./components/ui/Card');
  Card = CardModule.Card;
  CardHeader = CardModule.CardHeader;
  CardBody = CardModule.CardBody;
} catch (error) {
  // Fallback Card components
  Card = ({ children, className = '' }) => (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      {children}
    </div>
  );
  CardHeader = ({ children, className = '' }) => (
    <div className={`px-6 py-4 border-b border-gray-200 ${className}`}>
      {children}
    </div>
  );
  CardBody = ({ children, className = '' }) => (
    <div className={`px-6 py-4 ${className}`}>
      {children}
    </div>
  );
}

// Import AnimatedText with fallback for reliability
let SplitText, GradientText;
try {
  const AnimatedTextModule = require('./components/ui/AnimatedText');
  SplitText = AnimatedTextModule.SplitText;
  GradientText = AnimatedTextModule.GradientText;
} catch (error) {
  // Fallback SplitText
  SplitText = ({ text, className = '' }) => (
    <span className={`inline-block ${className}`}>{text}</span>
  );
  // Fallback GradientText  
  GradientText = ({ text, className = '' }) => (
    <span className={`bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent ${className}`}>
      {text}
    </span>
  );
}

// Import Navigation with fallback for reliability
let NavBar, NavLink;
try {
  const NavigationModule = require('./components/ui/Navigation');
  NavBar = NavigationModule.NavBar;
  NavLink = NavigationModule.NavLink;
} catch (error) {
  // Fallback NavBar
  NavBar = ({ children, className = '' }) => (
    <nav className={`bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">{children}</div>
      </div>
    </nav>
  );
  NavLink = ({ href, children, isActive, className = '' }) => (
    <a href={href} className={`inline-flex items-center px-1 pt-1 text-sm font-medium transition-colors ${isActive ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'} ${className}`}>
      {children}
    </a>
  );
}

// Import Lucide React icons with fallbacks
let Download, Github, ExternalLink, X, Check, Circle;
try {
  const LucideModule = require('lucide-react');
  Download = LucideModule.Download;
  Github = LucideModule.Github;
  ExternalLink = LucideModule.ExternalLink;
  X = LucideModule.X;
  Check = LucideModule.Check;
  Circle = LucideModule.Circle;
} catch (error) {
  // Fallback icon components using Unicode symbols
  Download = ({ className = '', ...props }) => (
    <span className={`inline-block ${className}`} {...props}>⬇</span>
  );
  Github = ({ className = '', ...props }) => (
    <span className={`inline-block ${className}`} {...props}>⚡</span>
  );
  ExternalLink = ({ className = '', ...props }) => (
    <span className={`inline-block ${className}`} {...props}>↗</span>
  );
  X = ({ className = '', ...props }) => (
    <span className={`inline-block ${className}`} {...props}>✕</span>
  );
  Check = ({ className = '', ...props }) => (
    <span className={`inline-block ${className}`} {...props}>✓</span>
  );
  Circle = ({ className = '', ...props }) => (
    <span className={`inline-block ${className}`} {...props}>○</span>
  );
}

// Include inline SpinnerLoader to avoid import issues
const SpinnerLoader = ({ size = 'md', className = '' }) => {
  const sizes = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' };
  return <div className={`${sizes[size]} border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin ${className}`} />;
};

const API_URL = 'http://localhost:8000/api/v1/todos';

const Header = ({ onAddTodo }) => {
  const [newTodoText, setNewTodoText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (newTodoText.trim()) {
      onAddTodo(newTodoText.trim());
      setNewTodoText('');
    }
  };

  return (
    <header className="mb-6">
      <h1 className="text-center mb-4">
        <GradientText text="Modern Todo App" className="text-4xl md:text-5xl font-bold" />
      </h1>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={newTodoText}
          onChange={(e) => setNewTodoText(e.target.value)}
          placeholder="What needs to be done?"
          className="flex-grow bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 transition-all duration-300"
        />
        <Button type="submit" size="md">Add Todo</Button>
      </form>
    </header>
  );
};

const TodoApp = () => {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // 'all', 'active', 'completed'

  const fetchTodos = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(API_URL);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setTodos(data);
    } catch (e) {
      setError('Failed to fetch todos. Please try again later.');
      console.error("Fetch error:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTodos();
  }, [fetchTodos]);

  const addTodo = async (text) => {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, completed: false }),
      });
      if (!response.ok) throw new Error('Failed to add todo');
      const newTodo = await response.json();
      setTodos(prevTodos => [newTodo, ...prevTodos]);
    } catch (e) {
      setError('Failed to add todo.');
      console.error("Add error:", e);
    }
  };

  const toggleTodo = async (id, currentStatus) => {
    const originalTodos = [...todos];
    const updatedTodos = todos.map(todo =>
      todo.id === id ? { ...todo, completed: !todo.completed } : todo
    );
    setTodos(updatedTodos);

    try {
      const response = await fetch(`${API_URL}/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed: !currentStatus }),
      });
      if (!response.ok) {
        throw new Error('Failed to update todo');
      }
    } catch (e) {
      setError('Failed to update todo. Reverting changes.');
      setTodos(originalTodos);
      console.error("Update error:", e);
    }
  };

  const deleteTodo = async (id) => {
    const originalTodos = [...todos];
    setTodos(todos.filter(todo => todo.id !== id));

    try {
      const response = await fetch(`${API_URL}/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to delete todo');
      }
    } catch (e) {
      setError('Failed to delete todo. Reverting changes.');
      setTodos(originalTodos);
      console.error("Delete error:", e);
    }
  };

  const filteredTodos = useMemo(() => {
    if (!Array.isArray(todos)) return [];
    switch (filter) {
      case 'active':
        return todos.filter(todo => !todo.completed);
      case 'completed':
        return todos.filter(todo => todo.completed);
      default:
        return todos;
    }
  }, [todos, filter]);

  const FilterButtons = () => (
    <div className="flex justify-center items-center gap-2 border-t border-gray-200 pt-4 mt-4">
      <span className="text-sm text-gray-500 pr-2">Show:</span>
      <Button
        variant={filter === 'all' ? 'primary' : 'outline'}
        size="sm"
        onClick={() => setFilter('all')}
      >
        All
      </Button>
      <Button
        variant={filter === 'active' ? 'primary' : 'outline'}
        size="sm"
        onClick={() => setFilter('active')}
      >
        Active
      </Button>
      <Button
        variant={filter === 'completed' ? 'primary' : 'outline'}
        size="sm"
        onClick={() => setFilter('completed')}
      >
        Completed
      </Button>
    </div>
  );

  const renderContent = () => {
    if (loading) {
      return <div className="flex justify-center items-center h-64"><SpinnerLoader size="lg" /></div>;
    }
    if (error) {
      return <div className="text-center text-red-500 p-4 bg-red-50 rounded-lg">{error}</div>;
    }
    if (Array.isArray(filteredTodos) && filteredTodos.length > 0) {
      return (
        <ul className="space-y-2">
          {filteredTodos.map(todo => (
            <li
              key={todo.id}
              className="flex items-center p-3 bg-gray-50 rounded-lg transition-all duration-300 hover:bg-gray-100 group"
            >
              <button
                onClick={() => toggleTodo(todo.id, todo.completed)}
                className={`flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center mr-4 transition-all duration-300 ${
                  todo.completed
                    ? 'bg-blue-600 border-blue-600'
                    : 'border-gray-300 group-hover:border-blue-400'
                }`}
                aria-label={todo.completed ? 'Mark as incomplete' : 'Mark as complete'}
              >
                {todo.completed && <Check className="w-4 h-4 text-white" />}
              </button>
              <span className={`flex-grow text-gray-800 transition-colors duration-300 ${
                  todo.completed ? 'line-through text-gray-400' : ''
                }`}
              >
                {todo.text}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => deleteTodo(todo.id)}
                className="ml-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300 !p-2 border-red-200 text-red-500 hover:bg-red-50"
                aria-label="Delete todo"
              >
                <X className="w-4 h-4" />
              </Button>
            </li>
          ))}
        </ul>
      );
    }
    return (
      <div className="text-center text-gray-500 py-10">
        <p>No todos here. Looks like you're all caught up!</p>
      </div>
    );
  };

  return (
    <div className="bg-gray-100 min-h-screen font-sans p-4 sm:p-6 lg:p-8">
      <main className="max-w-2xl mx-auto">
        <Card className="overflow-hidden shadow-xl transform hover:-translate-y-1 transition-transform duration-300">
          <CardBody className="p-6 md:p-8">
            <Header onAddTodo={addTodo} />
            {renderContent()}
            {!loading && Array.isArray(todos) && todos.length > 0 && <FilterButtons />}
          </CardBody>
        </Card>
        <footer className="text-center mt-8 text-gray-500 text-sm">
            <p>Built with React & TailwindCSS</p>
            <a href="https://github.com/your-repo" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 hover:text-blue-600 transition-colors">
                <Github className="w-4 h-4" /> View on GitHub <ExternalLink className="w-4 h-4" />
            </a>
        </footer>
      </main>
    </div>
  );
};

export default TodoApp;