import React from 'react';

```javascript
import { Trash2 } from 'lucide-react';

/**
 * TaskItem Component
 * @param {object} props
 * @param {object} props.task - The task object with id, text, and completed status.
 * @param {function(number, boolean): void} props.onToggle - Callback for toggling the task.
 * @param {function(number): void} props.onDelete - Callback for deleting the task.
 * 
 * This component represents a single To-Do item. It includes a custom checkbox
 * for toggling completion and a button for deletion. Visual state changes
 * (like strikethrough text) are handled via conditional classes.
 */
export const TaskItem = ({ task, onToggle, onDelete }) => {
  const handleToggle = () => {
    onToggle(task.id, !task.completed);
  };

  const handleDelete = (e) => {
    e.stopPropagation(); // Prevent the toggle from firing when delete is clicked
    onDelete(task.id);
  };

  return (
    <div className="container mx-auto p-4">
      <h1>Welcome to App 1758470496444</h1>
          {task.completed && (

          )}

          {task.text}

    </div>
  );
};
```