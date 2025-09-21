import { useState, useEffect, useCallback } from 'react';

// Best Practice: Use environment variables for configuration.
// Create a .env file in the `frontend` directory with:
// VITE_API_URL=http://localhost:8001
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

// A reusable loading spinner component for better UX
const Spinner = () => (
  
);

// A reusable component for displaying error messages
const ErrorMessage = ({ message }) => (
  
    Error:
    {message}
  
);

// A styled card component for displaying a single portfolio item
const ItemCard = ({ item }) => (
  
    
      {item.name}
      ID: {item.id}
    
    {item.description}
    
      Created: {new Date(item.created_at).toLocaleString()}
    
  
);

function App() {
  const [items, setItems] = useState([]);
  const [newItemName, setNewItemName] = useState('');
  const [newItemDescription, setNewItemDescription] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const fetchItems = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/items`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setItems(data);
    } catch (e) {
      console.error("Failed to fetch items:", e);
      setError("Could not load portfolio items. Please check the API connection and try again.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newItemName || !newItemDescription) {
        setError("Both name and description are required.");
        return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/items`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: newItemName, description: newItemDescription }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      // In a real app, you might optimistically add the returned item to the state.
      // Since the backend is mocked, we'll just refetch the entire list.
      setNewItemName('');
      setNewItemDescription('');
      await fetchItems(); // Refresh the list with new data
    } catch (e) {
      console.error("Failed to create item:", e);
      setError("Failed to create the item. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    
      
        
          My Portfolio
        
      

      
        
          
            Add a New Project
            
              
                Project Name
                 setNewItemName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                  placeholder="e.g., E-commerce Platform"
                  disabled={isSubmitting}
                  required
                />
              
              
                Description
                 setNewItemDescription(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                  rows="4"
                  placeholder="A short description of the project."
                  disabled={isSubmitting}
                  required
                />
              
              {error && }
              
                  
                    {isSubmitting ? 'Submitting...' : 'Add Project'}
                  
              
            
          
        

        
          Projects
          {isLoading ? (
            
              
            
          ) : items.length > 0 ? (
            
              {items.map((item) => )}
            
          ) : (
             
                No projects found. Add one using the form above!
             
          )}
        
      
    
  );
}

export default App;