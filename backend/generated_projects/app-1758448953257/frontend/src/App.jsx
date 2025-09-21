import React, { useState, useEffect, useCallback } from 'react';
import AddTaskForm from './components/AddTaskForm';
import TaskList from './components/TaskList';
import { CheckCircle, Zap } from 'lucide-react';

//  Mock API Service 
// In a real app, this would be in a separate file (e.g., src/services/api.js)
// and would use `fetch` or `axios` to make real network requests.
const mockApi = {
  // Initial sample data
  tasks: [
    { id: 1, text: 'Review project requirements', completed: false },
    { id: 2, text: 'Design the new UI layout', completed: true },
    { id: 3, text: 'Build the main components', completed: false },
  ],
  
  // Simulates fetching tasks from a server
  getTasks: async () => {
    console.log('API: Fetching tasks...');
    await new Promise(res => setTimeout(res, 800)); // Simulate network delay
    // To test error state, uncomment the following line:
    // if (Math.random() > 0.7) throw new Error("Failed to fetch tasks!");
    return [...mockApi.tasks];
  },

  // Simulates adding a new task
  addTask: async (text) => {
    console.log(`API: Adding task "${text}"...`);
    await new Promise(res => setTimeout(res, 500));
    const newTask = { id: Date.now(), text, completed: false };
    mockApi.tasks.push(newTask);
    return newTask;
  },

  // Simulates deleting a task
  deleteTask: async (id) => {
    console.log(`API: Deleting task with id ${id}...`);
    await new Promise(res => setTimeout(res, 500));
    const index = mockApi.tasks.findIndex(task => task.id === id);
    if (index === -1) throw new Error("Task not found!");
    mockApi.tasks.splice(index, 1);
    return { success: true };
  },

  // Simulates toggling a task's completion status
  toggleTask: async (id) => {
    console.log(`API: Toggling task with id ${id}...`);
    await new Promise(res => setTimeout(res, 300));
    const task = mockApi.tasks.find(task => task.id === id);
    if (!task) throw new Error("Task not found!");
    task.completed = !task.completed;
    return task;
  }
};
//  End Mock API Service 

function App() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch initial tasks when the component mounts
  useEffect(() => {
    const fetchInitialTasks = async () => {
      try {
        setError(null);
        setLoading(true);
        const fetchedTasks = await mockApi.getTasks();
        setTasks(fetchedTasks);
      } catch (err) {
        setError(err.message || 'An unexpected error occurred.');
      } finally {
        setLoading(false);
      }
    };
    fetchInitialTasks();
  }, []);

  // Handler to add a new task
  const handleAddTask = useCallback(async (text) => {
    if (!text.trim()) return; // Prevent adding empty tasks
    try {
      const newTask = await mockApi.addTask(text);
      setTasks(prevTasks => [...prevTasks, newTask]);
    } catch (err) {
      alert("Failed to add task. Please try again."); // Simple user feedback
    }
  }, []);

  // Handler to delete a task
  const handleDeleteTask = useCallback(async (id) => {
    try {
      await mockApi.deleteTask(id);
      setTasks(prevTasks => prevTasks.filter(task => task.id !== id));
    } catch (err) {
      alert("Failed to delete task. Please try again.");
    }
  }, []);

  // Handler to toggle a task's completion status
  const handleToggleTask = useCallback(async (id) => {
    try {
      const updatedTask = await mockApi.toggleTask(id);
      setTasks(prevTasks => 
        prevTasks.map(task => (task.id === id ? updatedTask : task))
      );
    } catch (err) {
      alert("Failed to update task. Please try again.");
    }
  }, []);

  const completedTasks = tasks.filter(task => task.completed).length;
  const totalTasks = tasks.length;

  return (

            TaskFlow

            A simple and effective way to manage your daily tasks.

            Your Tasks

              {completedTasks} / {totalTasks} Completed

            {loading ? (
              Loading tasks...
            ) : error ? (
              
                Error: {error}
                Please try refreshing the page.
              
            ) : (
              
            )}

          Built with React & TailwindCSS by GitHub Copilot.

  );
}

export default App;