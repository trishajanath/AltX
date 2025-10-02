import React, { useState, useEffect } from 'react';
import { getEvents } from './services/api';
import EventCard from './components/EventCard';
import EventForm from './components/EventForm';
import { PlusCircle, Loader, AlertTriangle } from 'lucide-react';

function App() {
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isFormOpen, setIsFormOpen] = useState(false);

  const fetchEvents = async () => {
    try {
      setIsLoading(true);
      const data = await getEvents();
      setEvents(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch events. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const handleEventCreated = (newEvent) => {
    setEvents(prevEvents => [newEvent, ...prevEvents].sort((a, b) => new Date(a.start_date) - new Date(b.start_date)));
    fetchEvents(); // Or just update state locally for better performance
  };

  return (
    
      
        
          College Event Manager
           setIsFormOpen(true)} 
            className="flex items-center bg-teal-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-teal-500 transition-transform transform hover:scale-105 duration-300 ease-in-out"
          >
            
            Add Event
          
        
      

      
        {isLoading && (
          
            
          
        )}

        {error && (
          
            
            {error}
          
        )}

        {!isLoading && !error && (
          
            {events.length > 0 ? (
              events.map(event => (
                
              ))
            ) : (
              
                No events found.
                Click 'Add Event' to get started!
              
            )}
          
        )}
      

       setIsFormOpen(false)} 
        onEventCreated={handleEventCreated} 
      />
    
  );
}

export default App;