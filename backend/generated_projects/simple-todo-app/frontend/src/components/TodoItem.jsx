```javascript
import React from 'react';
import { Trash2 } from 'lucide-react';

const TodoItem = ({ todo, onToggle, onDelete }) => {
  return (

         onToggle(todo.id)}
          className="form-checkbox h-5 w-5 text-highlight bg-secondary border-gray-500 rounded focus:ring-highlight"
        />
        
          {todo.text}

       onDelete(todo.id)}
        className="ml-4 p-1 text-gray-500 hover:text-red-400 transition-colors duration-200"
        aria-label={`Delete todo: ${todo.text}`}
      >

  );
};

export default TodoItem;
```