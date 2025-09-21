import React from 'react';
import { Trash2 } from 'lucide-react';

/**
 * TaskItem Component
 * @param {object} props - Component props
 * @param {object} props.task - The task object to display
 * @param {function(number): void} props.onDeleteTask - Callback to delete this task
 * @param {function(number): void} props.onToggleTask - Callback to toggle this task's completion
 *
 * This component represents a single task in the list. It displays the task's
 * text and provides controls for toggling its completion status and deleting it.
 */
function TaskItem({ task, onDeleteTask, onToggleTask }) {
  return (
    
       onToggleTask(task.id)}
        className="h-5 w-5 rounded border-gray-300 text-brand-primary focus:ring-brand-secondary"
        aria-label={`Mark task as ${task.completed ? 'incomplete' : 'complete'}`}
      />
      
        {task.text}
      
       onDeleteTask(task.id)}
        className="btn-icon text-gray-400 hover:text-red-600"
        aria-label={`Delete task: ${task.text}`}
      >

  );
}

export default TaskItem;