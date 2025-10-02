import React, { useState } from 'react';
import { createEvent } from '../services/api';
import { X } from 'lucide-react';

const EventForm = ({ isOpen, onClose, onEventCreated }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const eventData = {
      name,
      description,
      location,
      start_date: new Date(startDate).toISOString(),
      end_date: new Date(endDate).toISOString(),
    };

    try {
      const newEvent = await createEvent(eventData);
      onEventCreated(newEvent);
      onClose();
      // Reset form
      setName('');
      setDescription('');
      setLocation('');
      setStartDate('');
      setEndDate('');
    } catch (err) {
      setError(err.response?.data?.detail || 'An unexpected error occurred.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    
      
        
            
        
        Create New Event
        
        {error && {error}}
        
        
          
            Event Name
             setName(e.target.value)} required className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-teal-500 focus:border-teal-500" />
          
          
            Location
             setLocation(e.target.value)} required className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-teal-500 focus:border-teal-500" />
          
          
            
              Start Date & Time
               setStartDate(e.target.value)} required className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-teal-500 focus:border-teal-500" />
            
            
              End Date & Time
               setEndDate(e.target.value)} required className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-teal-500 focus:border-teal-500" />
            
          
          
            Description
             setDescription(e.target.value)} rows="3" className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-teal-500 focus:border-teal-500">
          
          
            Cancel
            
              {isSubmitting ? 'Creating...' : 'Create Event'}
            
          
        
      
    
  );
};

export default EventForm;