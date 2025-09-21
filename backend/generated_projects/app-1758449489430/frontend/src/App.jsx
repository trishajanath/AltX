import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Header from './components/Header';
import EventList from './components/EventList';
import EventFormModal from './components/EventFormModal';
import { FaFilter } from 'react-icons/fa';

// Mock API functions for clarity
const fetchEventsAPI = async () => {
    const response = await fetch('/api/data');
    if (!response.ok) {
        throw new Error('Failed to fetch events.');
    }
    return response.json();
};

const createEventAPI = async (eventData) => {
    const response = await fetch('/api/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(eventData),
    });
    if (!response.ok) {
        throw new Error('Failed to create event.');
    }
    return response.json();
};

const EVENT_CATEGORIES = ['All', 'Academic', 'Sports', 'Social', 'Workshop'];

export default function App() {
    const [events, setEvents] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [activeFilter, setActiveFilter] = useState('All');

    // Fetch initial events on component mount
    useEffect(() => {
        const loadEvents = async () => {
            try {
                setIsLoading(true);
                setError(null);
                const data = await fetchEventsAPI();
                // Sort events by date, newest first
                const sortedData = data.sort((a, b) => new Date(b.date) - new Date(a.date));
                setEvents(sortedData);
            } catch (err) {
                setError(err.message || 'An unexpected error occurred.');
            } finally {
                setIsLoading(false);
            }
        };
        loadEvents();
    }, []);

    // Memoized callback for event submission
    const handleAddEvent = useCallback(async (newEventData) => {
        try {
            const newEvent = await createEventAPI(newEventData);
            // Optimistic UI update: add new event to the list immediately
            setEvents(prevEvents => [newEvent, ...prevEvents].sort((a, b) => new Date(b.date) - new Date(a.date)));
            setIsModalOpen(false); // Close modal on success
            return { success: true };
        } catch (err) {
            console.error("Submission Error:", err);
            return { success: false, message: err.message || "Could not save the event." };
        }
    }, []);
    
    // Memoized list of filtered events to prevent re-calculation on every render
    const filteredEvents = useMemo(() => {
        if (activeFilter === 'All') {
            return events;
        }
        return events.filter(event => event.category === activeFilter);
    }, [events, activeFilter]);

    return (
        
             setIsModalOpen(true)} />

                    Upcoming Events

                            {EVENT_CATEGORIES.map(category => (
                                 setActiveFilter(category)}
                                    className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                                        activeFilter === category
                                            ? 'bg-brand-primary text-white shadow'
                                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                    }`}
                                >
                                    {category}
                                
                            ))}

             setIsModalOpen(false)}
                onSubmit={handleAddEvent}
                categories={EVENT_CATEGORIES.filter(c => c !== 'All')}
            />
        
    );
}