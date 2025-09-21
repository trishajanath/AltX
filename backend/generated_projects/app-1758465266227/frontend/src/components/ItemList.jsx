import React from 'react';
import PropTypes from 'prop-types';
import { Calendar, MapPin, Trash2, AlertTriangle, Info } from 'lucide-react';
import { format } from 'date-fns';

/**
 * Renders a single event card with details and a remove button.
 */
const EventCard = ({ event, onRemove }) => {
  const formattedDate = format(new Date(event.eventDate), "eee, MMM d, yyyy");
  const formattedTime = format(new Date(event.eventDate), "h:mm a");

  return (

        {event.department}
        {event.title}

            {formattedDate} at {formattedTime}

            {event.location}

        {event.description && (
          
            {event.description}
          
        )}

         onRemove(event.id)}
          className="flex items-center gap-2 text-sm text-red-600 hover:text-red-800 font-medium transition-colors"
          aria-label={`Remove event: ${event.title}`}
        >
          
          Remove

  );
};

EventCard.propTypes = {
  event: PropTypes.object.isRequired,
  onRemove: PropTypes.func.isRequired,
};

/**
 * Displays a list of college events.
 * Handles loading, error, and empty states gracefully.
 */
function ItemList({ events, loading, error, onRemoveEvent }) {

  // Loading State: Show skeleton cards
  if (loading) {
    return (
      
         Upcoming Events
        {[...Array(3)].map((_, i) => (

        ))}
      
    );
  }

  // Error State: Show an error message
  if (error) {
    return (

            An error occurred
            {error}

    );
  }

  // Sort events by date, earliest first
  const sortedEvents = [...events].sort((a, b) => new Date(a.eventDate) - new Date(b.eventDate));

  return (
    
      Upcoming Events
      
      {/* Empty State: Show a message when no events are available */}
      {sortedEvents.length === 0 ? (

            No Events Found
            
                There are currently no upcoming events. Add one using the form!

      ) : (
        
          {sortedEvents.map(event => (
            
          ))}
        
      )}
    
  );
}

ItemList.propTypes = {
  events: PropTypes.array.isRequired,
  loading: PropTypes.bool.isRequired,
  error: PropTypes.string,
  onRemoveEvent: PropTypes.func.isRequired,
};

export default ItemList;