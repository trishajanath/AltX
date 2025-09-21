import React from 'react';

```javascript
import { useState } from 'react';
import { Plus } from 'lucide-react';

/**
 * AddTaskForm Component
 * @param {object} props
 * @param {function(string): void} props.onAddTask - Callback function to add a new task.
 * 
 * This component provides a controlled input form for adding new tasks.
 * It manages its own input state and handles form submission, including
 * preventing submission of empty tasks and clearing the input after a task is added.
 */
export const AddTaskForm = ({ onAddTask }) => {
  const [text, setText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) {
      return; // Prevent adding empty tasks
    }
    setIsSubmitting(true);
    try {
      await onAddTask(text);
      setText(''); // Clear input on successful addition
    } catch (error) {
      console.error("Error in form submission:", error);
      // Error is handled in the parent component, but you could add form-specific feedback here.
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    
       setText(e.target.value)}
        placeholder="What needs to be done?"
        className="input-field flex-grow"
        required
        disabled={isSubmitting}
      />

  );
};
```