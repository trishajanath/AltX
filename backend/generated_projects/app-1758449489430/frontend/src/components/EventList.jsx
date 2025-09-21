import React from 'react';
import { format } from 'date-fns';
import { FaCalendarAlt, FaClock, FaMapMarkerAlt, FaBuilding, FaTag } from 'react-icons/fa';
import { CgSpinner } from 'react-icons/cg';

// Sub-component for a single event card for better organization
const EventCard = ({ event }) => {
    const categoryColors = {
        Academic: 'bg-blue-100 text-blue-800 border-blue-300',
        Sports: 'bg-green-100 text-green-800 border-green-300',
        Social: 'bg-purple-100 text-purple-800 border-purple-300',
        Workshop: 'bg-yellow-100 text-yellow-800 border-yellow-300',
        Default: 'bg-gray-100 text-gray-800 border-gray-300',
    };

    const cardColor = categoryColors[event.category] || categoryColors.Default;

    return (

                    {event.title}
                    
                        {event.category}

                {event.description}

                    {format(new Date(event.date), 'EEEE, MMMM d, yyyy')}

                    {format(new Date(event.date), 'p')}

                    {event.location}

                    Hosted by: {event.department}

    );
};

// Main list component
function EventList({ events, isLoading, error }) {
    if (isLoading) {
        return (

                Loading Events...
            
        );
    }

    if (error) {
        return (
            
                Error
                {error}
            
        );
    }

    if (events.length === 0) {
        return (
            
                No Events Found
                There are no events matching your criteria. Try another filter or check back later!
            
        );
    }

    return (
        
            {events.map(event => (
                
            ))}
        
    );
}

export default EventList;