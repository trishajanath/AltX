import React from 'react';
import EventCard from './EventCard';
import PropTypes from 'prop-types';

/**
 * EventList Component
 * Renders a grid of EventCard components.
 * Handles the display for when no events are available.
 */
function EventList({ events, onDelete }) {
  if (!events || events.length === 0) {
    return (

        No upcoming events
        Check back later or add a new event!
      
    );
  }

  return (
    
      {events.map((event) => (
        
      ))}
    
  );
}

EventList.propTypes = {
  events: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    description: PropTypes.string,
    date: PropTypes.string.isRequired,
    time: PropTypes.string,
    location: PropTypes.string,
    organizer: PropTypes.string,
  })).isRequired,
  onDelete: PropTypes.func.isRequired,
};

export default EventList;