import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import MainContent from './components/MainContent';
import { BookOpenCheck } from 'lucide-react';

//  MOCK API SETUP 
// This section simulates a backend API for demonstration purposes.
// In a real application, you would remove this and the server would handle this logic.
import { Server, Model } from 'miragejs';

// Initialize MirageJS mock server
if (window.server) {
  window.server.shutdown();
}
window.server = new Server({
  models: {
    event: Model,
  },
  seeds(server) {
    server.create('event', { 
      id: '1', 
      title: 'Guest Lecture: The Future of AI', 
      department: 'Computer Science', 
      location: 'Thompson Hall, Room 201', 
      eventDate: new Date('2024-10-26T14:00:00'),
      description: 'Join us for an insightful talk by Dr. Evelyn Reed on the advancements and ethical implications of artificial intelligence.'
    });
    server.create('event', { 
      id: '2', 
      title: 'Annual Arts & Humanities Fair', 
      department: 'Arts & Humanities', 
      location: 'University Quad', 
      eventDate: new Date('2024-11-05T10:00:00'),
      description: 'Explore student projects, club showcases, and live performances at our annual fair.'
    });
  },
  routes() {
    this.namespace = 'api';
    this.timing = 1000; // Simulate network delay

    this.get('/data', (schema) => {
      return schema.events.all();
    });

    this.post('/create', (schema, request) => {
      const attrs = JSON.parse(request.requestBody);
      return schema.events.create(attrs);
    });

    this.delete('/data/:id', (schema, request) => {
      const id = request.params.id;
      const event = schema.events.find(id);
      if (event) {
        event.destroy();
        return { success: true, id };
      }
      return new Response(404, { some: 'header' }, { errors: [ 'Event not found' ]});
    });
  },
});
//  END MOCK API SETUP 

function App() {
  // State management for events, loading status, and errors
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Fetches all events from the API when the component mounts.
   * Uses a mock API for demonstration purposes.
   */
  const fetchEvents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // API call to get all events
      const response = await axios.get('/api/data');
      setEvents(response.data.events);
    } catch (err) {
      console.error("Failed to fetch events:", err);
      setError('Could not retrieve events. Please check the network connection or try again later.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  /**
   * Handles adding a new event.
   * @param {object} newEvent - The event object from the form.
   */
  const handleAddEvent = useCallback(async (newEvent) => {
    try {
      // API call to create a new event
      const response = await axios.post('/api/create', newEvent);
      // Add the new event to the state immutably
      setEvents(prevEvents => [...prevEvents, response.data.event]);
      return { success: true };
    } catch (err) {
      console.error("Failed to add event:", err);
      return { success: false, message: 'Failed to add event. Please try again.' };
    }
  }, []);

  /**
   * Handles removing an event.
   * @param {string} eventId - The ID of the event to remove.
   */
  const handleRemoveEvent = useCallback(async (eventId) => {
    try {
      // Optimistic UI update: remove the event from the list immediately
      setEvents(prevEvents => prevEvents.filter(event => event.id !== eventId));
      // API call to delete the event
      await axios.delete(`/api/data/${eventId}`);
    } catch (err) {
      console.error("Failed to remove event:", err);
      // If the API call fails, we could potentially roll back the state,
      // but for this simple app, we'll log the error and show an alert.
      alert('Failed to remove event from the server. The event might reappear on refresh.');
      // To rollback, you would refetch the data: fetchEvents();
    }
  }, []);

  return (

            Campus Events Board

        &copy; {new Date().getFullYear()} University Name. All Rights Reserved.

  );
}

export default App;