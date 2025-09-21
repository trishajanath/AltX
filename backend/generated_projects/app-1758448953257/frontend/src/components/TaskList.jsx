import React from 'react';
import TaskItem from './TaskItem';
import { ListTodo } from 'lucide-react';

/**
 * TaskList Component
 * @param {object} props - Component props
 * @param {Array} props.tasks - The array of task objects to display
 * @param {function(number): void} props.onDeleteTask - Callback to delete a task
 * @param {function(number): void} props.onToggleTask - Callback to toggle a task's completion
 *
 * This component is responsible for rendering the list of tasks.
 * It maps over the `tasks` array and renders a `TaskItem` for each one.
 * It also displays a message when there are no tasks.
 */
function TaskList({ tasks, onDeleteTask, onToggleTask }) {
  if (tasks.length === 0) {
    return (

        All Clear!
        You have no tasks. Add one above to get started.
      
    );
  }
  
  // Sort tasks to show uncompleted ones first
  const sortedTasks = [...tasks].sort((a, b) => a.completed - b.completed);

  return (
    
      {sortedTasks.map((task) => (
        
      ))}
    
  );
}

export default TaskList;