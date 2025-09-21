import React from 'react';
import PropTypes from 'prop-types';

/**
 * Helper function to format date for display.
 * e.g., '2023-11-15' becomes 'Nov 15, 2023'
 */
const formatDate = (dateString) => {
  const options = { year: 'numeric', month: 'short', day: 'numeric' };
  return new Date(dateString + 'T00:00:00').toLocaleDateString(undefined, options);
};

// SVG Icons for better visuals without extra dependencies
const CalendarIcon = () => (
  <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const LocationIcon = () => (
  <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

/**
 * EventCard Component
 * Displays the details of a single college event in a card format.
 */
function EventCard({ event, onDelete }) {
  const { id, title, description, date, time, location, organizer } = event;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-200">
      <div className="flex justify-between items-start mb-3">
        <span className="text-sm text-gray-500 font-medium">{organizer}</span>
        <button
          onClick={() => onDelete(id)}
          className="text-sm text-red-600 hover:text-red-800 font-medium transition duration-200"
          aria-label={`Delete event: ${title}`}
        >
          Delete
        </button>
      </div>
      
      <h3 className="text-xl font-bold text-gray-800 mb-2">{title}</h3>
      <p className="text-gray-600 mb-4">{description}</p>
      
      <div className="space-y-2 text-sm text-gray-700">
        <div className="flex items-center">
          <CalendarIcon />
          <span>{formatDate(date)} at {time}</span>
        </div>
        
        <div className="flex items-center">
          <LocationIcon />
          <span>{location}</span>
        </div>
      </div>
    </div>
  );
}

EventCard.propTypes = {
  event: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    description: PropTypes.string,
    date: PropTypes.string.isRequired,
    time: PropTypes.string,
    location: PropTypes.string,
    organizer: PropTypes.string,
  }).isRequired,
  onDelete: PropTypes.func.isRequired,
};

export default EventCard;