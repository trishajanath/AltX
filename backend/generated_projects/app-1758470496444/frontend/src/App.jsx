import React from 'react';

```javascript
import { useState, useEffect, useCallback, useMemo } from 'react';
import { TaskList } from './components/TaskList';
import { AddTaskForm } from './components/AddTaskForm';
import { CheckSquare, ListTodo, LoaderCircle } from 'lucide-react';

// 🔬 MOCK API: In a real-world application, this would be in a separate service file.
// We use setTimeout to simulate network latency.
const mockApi = {
  fetchTasks: async () => {
    console.log("API: Fetching tasks...");
    return new Promise(resolve => {
      setTimeout(() => {
        const tasks = [
          { id: 1, text: 'Analyze Q2 security audit findings', completed: false },
          { id: 2, text: 'Develop a new secure coding pattern for React', completed: true },
          { id: 3, text: 'Prepare presentation for the DevSecOps meeting', completed: false },
        ];
        console.log("API: Fetched tasks successfully.");
        resolve(tasks);
      }, 1000);
    });
  },
  addTask: async (text) => {
    console.log(`API: Adding task "${text}"...`);
    return new Promise(resolve => {
      setTimeout(() => {
        const newTask = { id: Date.now(), text, completed: false };
        console.log("API: Task added successfully.");
        resolve(newTask);
      }, 500);
    });
  },
  updateTask: async (id, updates) => {
    console.log(`API: Updating task ${id}...`, updates);
    return new Promise(resolve => {
      setTimeout(() => {
        console.log("API: Task updated successfully.");
        resolve({ id, ...updates });
      }, 300);
    });
  },
  deleteTask: async (id) => {
    console.log(`API: Deleting task ${id}...`);
    return new Promise(resolve => {
      setTimeout(() => {
        console.log("API: Task deleted successfully.");
        resolve();
      }, 500);
    });
  }
};

function App() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // 'all', 'active', 'completed'

  useEffect(() => {
    const loadTasks = async () => {
      try {
        setLoading(true);
        setError(null);
        const fetchedTasks = await mockApi.fetchTasks();
        setTasks(fetchedTasks);
      } catch (err) {
        setError('Failed to fetch tasks. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadTasks();
  }, []);

  const handleAddTask = useCallback(async (text) => {
    if (!text.trim()) return; // Basic validation
    try {
      const newTask = await mockApi.addTask(text);
      setTasks(prevTasks => [newTask, ...prevTasks]);
    } catch (err) {
      setError('Failed to add task.');
    }
  }, []);

  const handleToggleTask = useCallback(async (id, completed) => {
    // Optimistic UI update
    setTasks(prevTasks =>
      prevTasks.map(task =>
        task.id === id ? { ...task, completed } : task
      )
    );
    try {
      await mockApi.updateTask(id, { completed });
    } catch (err) {
      setError('Failed to update task. Reverting change.');
      // Revert on failure
      setTasks(prevTasks =>
        prevTasks.map(task =>
          task.id === id ? { ...task, completed: !completed } : task
        )
      );
    }
  }, []);

  const handleDeleteTask = useCallback(async (id) => {
    // Optimistic UI update
    const originalTasks = tasks;
    setTasks(prevTasks => prevTasks.filter(task => task.id !== id));
    try {
      await mockApi.deleteTask(id);
    } catch (err) {
      setError('Failed to delete task. Reverting change.');
      setTasks(originalTasks); // Revert on failure
    }
  }, [tasks]);

  const filteredTasks = useMemo(() => {
    switch (filter) {
      case 'active':
        return tasks.filter(task => !task.completed);
      case 'completed':
        return tasks.filter(task => task.completed);
      default:
        return tasks;
    }
  }, [tasks, filter]);

  const activeTasksCount = useMemo(() => tasks.filter(task => !task.completed).length, [tasks]);

  const FilterButton = ({ value, label }) => (
     setFilter(value)}
      className={`px-3 py-1 text-sm rounded-md transition-colors ${
        filter === value
          ? 'bg-brand-primary text-white'
          : 'bg-brand-bg-light text-brand-text-secondary hover:bg-brand-border'
      }`}
    >
      {label}
    
  );

  return (
    <div className="container mx-auto p-4">
      <h1>Welcome to App 1758470496444</h1>
            TaskMaster
          
          A modern, secure, and delightful To-Do experience.

                {activeTasksCount} {activeTasksCount === 1 ? 'task' : 'tasks'} left

          {error && {error}}

          {loading ? (

              Loading your tasks...
            
          ) : (
            
          )}

          {!loading && tasks.length === 0 && (

                You're all caught up!
            
          )}

    </div>
  );
}

export default App;
```