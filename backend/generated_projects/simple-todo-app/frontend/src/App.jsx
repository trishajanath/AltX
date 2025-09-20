```javascript
import React, { useState, useEffect, useMemo } from 'react';
import { v4 as uuidv4 } from 'uuid';
import Header from './components/Header';
import TodoForm from './components/TodoForm';
import TodoList from './components/TodoList';
import FilterControls from './components/FilterControls';
import Spinner from './components/Spinner';

// Custom Hook for localStorage persistence
const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error("Error reading from localStorage", error);
      return initialValue;
    }
  });

  const setValue = (value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error("Error writing to localStorage", error);
    }
  };

  return [storedValue, setValue];
};

function App() {
  const [todos, setTodos] = useLocalStorage('todos', []);
  const [filter, setFilter] = useState('all'); // 'all', 'active', 'completed'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Simulate initial data loading
  useEffect(() => {
    setLoading(true);
    setError(null);
    try {
      // The useLocalStorage hook already handles the loading,
      // but we simulate an async fetch for demonstration.
      setTimeout(() => {
        setLoading(false);
      }, 500);
    } catch (e) {
      setError("Failed to load todos. Please refresh the page.");
      setLoading(false);
    }
  }, []);

  const addTodo = (text) => {
    const newTodo = {
      id: uuidv4(),
      text,
      completed: false,
      createdAt: new Date().toISOString(),
    };
    setTodos([newTodo, ...todos]);
  };

  const toggleTodo = (id) => {
    setTodos(
      todos.map((todo) =>
        todo.id === id ? { ...todo, completed: !todo.completed } : todo
      )
    );
  };

  const deleteTodo = (id) => {
    setTodos(todos.filter((todo) => todo.id !== id));
  };
  
  const clearCompleted = () => {
    setTodos(todos.filter((todo) => !todo.completed));
  }

  const filteredTodos = useMemo(() => {
    switch (filter) {
      case 'active':
        return todos.filter((todo) => !todo.completed);
      case 'completed':
        return todos.filter((todo) => todo.completed);
      default:
        return todos;
    }
  }, [todos, filter]);

  return (

             t.completed)}
            />

            {loading ? (

            ) : error ? (
              {error}
            ) : (
              
            )}

          A modern React Todo App built with Vite and TailwindCSS.

  );
}

// 
🛡️ Security Note: For a production application handling sensitive data,
// local storage is not ideal as it's accessible via JavaScript (XSS risk).
// Consider using a secure backend with proper authentication and database storage.
// This implementation is suitable for non-sensitive, client-side-only data.

export default App;
```