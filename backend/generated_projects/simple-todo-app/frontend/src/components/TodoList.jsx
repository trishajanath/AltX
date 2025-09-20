```javascript
import React from 'react';
import TodoItem from './TodoItem';

const TodoList = ({ todos, onToggleTodo, onDeleteTodo }) => {
  if (todos.length === 0) {
    return (
      
        You're all caught up!
        Add a new task to get started.
      
    );
  }

  return (
    
      {todos.map((todo) => (
        
      ))}
    
  );
};

export default TodoList;
```