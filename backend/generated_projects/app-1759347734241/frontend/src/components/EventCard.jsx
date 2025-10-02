import React from 'react';
import { Calendar, MapPin, AlignLeft } from 'lucide-react';

const EventCard = ({ event }) => {
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    
      
        {event.name}
        
        
          
          {event.location}
        

        
            
                
                
                    Starts: {formatDate(event.start_date)}
                    Ends: {formatDate(event.end_date)}
                
            
            
                
                {event.description}
            
        

      
    
  );
};

export default EventCard;