import React from 'react';

```javascript
import { useState } from 'react';
import { Plus, LoaderCircle } from 'lucide-react';

/**
 * 🔬 Expert Code Review: AddTaskForm Component
 * This component demonstrates several best practices for form handling in React.
 * 1.  **Controlled Component**: The input's value is controlled by React state (`taskText`). This provides a single source of truth and allows for easy validation, transformation, and resetting of the input field.
 * 2.  **Local Loading State**: A local `isSubmitting` state is used to provide immediate feedback to the user upon form submission. It disables the button to prevent duplicate submissions while the async `onAddTask` operation is in progress.
 * 3.  **Error Handling**: The `try...finally` block is critical. It ensures that `setIsSubmitting(false)` is called regardless of whether the `onAddTask` promise succeeds or fails. This prevents the form from getting stuck in a disabled state if an API error occurs.
 * 4.  **Accessibility**: The button is disabled when submitting, which is important for accessibility as it prevents users from interacting with it while an action is pending. The `htmlFor` attribute on the label is also a key accessibility feature.
 *
 * @param {{ onAddTask: (text: string) => Promise }} props
 */
function AddTaskForm({ onAddTask }) {
  const [taskText, setTaskText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmedText = taskText.trim();

    if (!trimmedText) {
      // Prevents adding empty tasks
      return;
    }
    
    setIsSubmitting(true);
    try {
      await onAddTask(trimmedText);
      setTaskText(''); // Clear input on successful submission
    } catch (error) {
      // Error is handled by the parent component (App.jsx)
      // We don't need to show an alert here, just stop the loading spinner
      console.error("Submission failed in AddTaskForm:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1>Welcome to Test Fixed App</h1>
        New Task
      
       setTaskText(e.target.value)}
        placeholder="Add a new task..."
        className="flex-grow p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-primary transition duration-150"
        disabled={isSubmitting}
      />
      
        {isSubmitting ? (
          
        ) : (
          <>
            
            Add Task
          
        )}

    </div>
  );
}

export default AddTaskForm;
```