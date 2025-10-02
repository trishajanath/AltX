import React, { useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/solid';

const AddCourseModal = ({ isOpen, onClose, onAddCourse }) => {
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const result = await onAddCourse({ name, code, description });
    
    setIsSubmitting(false);

    if (result.success) {
      // Clear form and close modal on success
      setName('');
      setCode('');
      setDescription('');
      onClose();
    } else {
      // Display error message from backend
      setError(result.message || 'An unexpected error occurred.');
    }
  };

  const handleClose = () => {
    // Reset state when closing
    setName('');
    setCode('');
    setDescription('');
    setError(null);
    onClose();
  };
  
  if (!isOpen) {
    return null;
  }

  return (
    
      
        
          
            Add New Course
          
          
            
            Close modal
          
        
        
          {error && (
            
              Error: 
              {error}
            
          )}
          
            Course Name
             setName(e.target.value)}
              className="bg-gray-50 border border-gray-300 text-text-primary text-sm rounded-lg focus:ring-primary focus:border-primary block w-full p-2.5"
              placeholder="e.g., Advanced Web Development"
              required
            />
          
          
            Course Code
             setCode(e.target.value)}
              className="bg-gray-50 border border-gray-300 text-text-primary text-sm rounded-lg focus:ring-primary focus:border-primary block w-full p-2.5"
              placeholder="e.g., CS455"
              required
            />
          
          
            Description (Optional)
             setDescription(e.target.value)}
              className="block p-2.5 w-full text-sm text-text-primary bg-gray-50 rounded-lg border border-gray-300 focus:ring-primary focus:border-primary"
              placeholder="A brief summary of the course content..."
            >
          
          
            
              Cancel
            
            
              {isSubmitting ? 'Adding...' : 'Add Course'}
            
          
        
      
    
  );
};

export default AddCourseModal;