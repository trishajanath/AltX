import React, { useState } from 'react';
import { PlusCircle } from 'lucide-react';

/**
 * AddTaskForm Component
 * @param {object} props - Component props
 * @param {function(string): void} props.onAddTask - Callback function to add a new task
 * 
 * This component renders a form for adding new tasks. It manages the
 * input field's state and calls the onAddTask prop on form submission.
 */
function AddTaskForm({ onAddTask }) {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim()) {
      // You could add more sophisticated validation feedback here
      return;
    }
    onAddTask(text);
    setText(''); // Reset input field after adding
  };

  return (
    
       setText(e.target.value)}
        placeholder="What needs to be done?"
        className="input-field flex-grow"
        aria-label="New task input"
      />

        Add Task

  );
}

export default AddTaskForm;