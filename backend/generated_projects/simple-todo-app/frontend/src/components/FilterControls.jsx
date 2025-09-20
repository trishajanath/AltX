```javascript
import React from 'react';

const FilterButton = ({ filterType, currentFilter, setFilter, children }) => {
  const isActive = filterType === currentFilter;
  return (
     setFilter(filterType)}
      className={`px-3 py-1 text-sm rounded-md transition-colors ${
        isActive
          ? 'bg-highlight text-white'
          : 'text-gray-400 hover:bg-accent'
      }`}
    >
      {children}
    
  );
};

const FilterControls = ({ filter, setFilter, onClearCompleted, hasCompletedTodos }) => {
  return (

          All

          Active

          Completed

      {hasCompletedTodos && (
        
          Clear Completed
        
      )}
    
  );
};

export default FilterControls;
```