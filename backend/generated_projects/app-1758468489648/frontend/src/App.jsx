import React, { useState, useEffect, useCallback } from 'react';
import EventList from './components/EventList';
import EventForm from './components/EventForm';

//  Mock API 
// In a real application, this data would come from a server.
const initialEvents = [
  { id: 1, title: 'AI Club: Introduction to Machine Learning', description: 'Join us for the first meeting of the AI Club! We will cover the basics of ML and our plans for the semester.', date: '2023-11-15', time: '18:00', location: 'Engineering Bldg, Room 301', organizer: 'AI Club' },
  { id: 2, title: 'Career Fair Prep Workshop', description: 'Get your resume ready and practice your elevator pitch with career services. Don\'t miss out!', date: '2023-11-20', time: '15:00', location: 'Student Union, Hall B', organizer: 'Career Services' },
  { id: 3, title: 'Campus Movie Night: "The Social Network"', description: 'Free popcorn and a great movie under the stars on the main quad.', date: '2023-11-22', time: '20:00', location: 'Main Quad', organizer: 'Student Activities Board' },
];

// Simulates a network request
const api = {
  getEvents: async () => {
    console.log('Fetching events...');
    return new Promise(resolve => setTimeout(() => resolve([...initialEvents]), 1000));
  },
  addEvent: async (event) => {
    console.log('Adding event...', event);
    const newEvent = { ...event, id: Date.now() };
    initialEvents.push(newEvent);
    return new Promise(resolve => setTimeout(() => resolve(newEvent), 500));
  },
  deleteEvent: async (id) => {
    console.log(`Deleting event ${id}...`);
    const index = initialEvents.findIndex(e => e.id === id);
    if (index > -1) {
      initialEvents.splice(index, 1);
    }
    return new Promise(resolve => setTimeout(() => resolve({ success: true }), 500));
  },
};
//  End Mock API 

function App() {
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Fetch events on initial component mount
  useEffect(() => {
    const fetchEvents = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await api.getEvents();
        setEvents(data);
      } catch (err) {
        setError('Failed to fetch events. Please try refreshing the page.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchEvents();
  }, []);

  // Handler to add a new event
  const handleAddEvent = useCallback(async (newEventData) => {
    try {
      const addedEvent = await api.addEvent(newEventData);
      setEvents(prevEvents => [addedEvent, ...prevEvents].sort((a,b) => new Date(a.date) - new Date(b.date)));
      setIsModalOpen(false); // Close modal on success
    } catch (err) {
      setError('Failed to add event. Please try again.');
      console.error(err);
    }
  }, []);

  // Handler to delete an event
  const handleDeleteEvent = useCallback(async (id) => {
    // Optimistic UI update
    const originalEvents = [...events];
    setEvents(prevEvents => prevEvents.filter(event => event.id !== id));
    
    try {
      await api.deleteEvent(id);
    } catch (err) {
      setError('Failed to delete event. Please try again.');
      // Revert if API call fails
      setEvents(originalEvents);
      console.error(err);
    }
  }, [events]);

  return (

            Hill Valley University Events
          
           setIsModalOpen(true)}
            className="bg-accent-gold text-university-blue font-bold py-2 px-4 rounded-md hover:bg-yellow-400 transition duration-300 transform hover:scale-105"
          >
            + Add Event

        {isLoading && (

        )}

        {error && (
          
            Error
            {error}
          
        )}

        {!isLoading && !error && (
          
        )}

      {isModalOpen && (
         setIsModalOpen(false)}
        />
      )}
    
  );
}

export default App;