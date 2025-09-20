```javascript
import React, { useState } from 'react';
import { Plus } from 'lucide-react';

const TodoForm = ({ onAddTodo }) => {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmedText = text.trim();
    if (trimmedText) {
      onAddTodo(trimmedText);
      setText('');
    }
  };

  return (
    
       setText(e.target.value)}
        placeholder="What needs to be done?"
        className="input-field flex-grow"
        aria-label="New todo input"
      />

  );
};

export default TodoForm;
```