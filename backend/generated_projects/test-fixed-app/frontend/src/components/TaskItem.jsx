import React from 'react';

```javascript
import { Trash2, Check, Circle } from 'lucide-react';

/**
 * 🔬 Expert Code Review: TaskItem Component
 * This component encapsulates the display and interaction logic for a single task.
 * 1.  **Event Handling Security**: The `onClick` handlers for toggling and deleting do not contain business logic themselves. They simply call the prop functions (`onToggleComplete(task.id)`). This is a secure pattern as it ensures the component cannot perform actions it's not authorized to. The actual logic resides in the parent `App` component.
 * 2.  **Conditional Rendering and Styling**: The use of conditional classes (`task.completed ? '...' : '...'`) for styling provides immediate visual feedback. This is a secure way to reflect state, as it relies solely on the `task.completed` prop and doesn't involve manipulating the DOM directly, which could open XSS vulnerabilities if done improperly with user-generated content.
 * 3.  **Component Granularity**: By breaking down the UI into small, single-responsibility components like `TaskItem`, the codebase becomes easier to audit for security flaws and to maintain. Each component has a clearly defined and limited scope.
 *
 * @param {{ task: {id: number | string, text: string, completed: boolean}, onDeleteTask: (id: number | string) => void, onToggleComplete: (id: number | string) => void }} props
 */
function TaskItem({ task, onDeleteTask, onToggleComplete }) {
  return (
    
       onToggleComplete(task.id)}
        aria-label={task.completed ? 'Mark as incomplete' : 'Mark as complete'}
        className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center border-2 transition-colors duration-200 ${
          task.completed
            ? 'bg-primary border-primary text-white'
            : 'border-gray-300 text-transparent hover:border-primary'
        }`}
      >
        {task.completed ?  : }

        {task.text}

       onDeleteTask(task.id)}
        aria-label={`Delete task: ${task.text}`}
        className="flex-shrink-0 p-2 text-gray-400 rounded-full hover:bg-red-100 hover:text-danger transition-colors duration-200"
      >

  );
}

export default TaskItem;
```