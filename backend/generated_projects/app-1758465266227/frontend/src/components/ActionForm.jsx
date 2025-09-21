import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { PlusCircle, LoaderCircle } from 'lucide-react';

/**
 * ActionForm component provides a user interface for adding new college events.
 * It includes fields relevant to a campus event and handles form state,
 * validation, submission, and loading indicators.
 */
function ActionForm({ onAddEvent }) {
  const [formData, setFormData] = useState({
    title: '',
    department: '',
    location: '',
    eventDate: '',
    description: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title || !formData.department || !formData.location || !formData.eventDate) {
      setError('Please fill out all required fields.');
      return;
    }
    setError(null);
    setIsSubmitting(true);

    // Combine date and time (assuming time is part of the date input for simplicity)
    const eventData = {
      ...formData,
      eventDate: new Date(formData.eventDate).toISOString(),
    };

    const result = await onAddEvent(eventData);

    if (result.success) {
      // Reset form on successful submission
      setFormData({
        title: '',
        department: '',
        location: '',
        eventDate: '',
        description: '',
      });
    } else {
      setError(result.message);
    }
    setIsSubmitting(false);
  };

  return (
    
      Add New Event
      
        {error && {error}}

          Event Title

          Department

          Location / Room

          Date & Time

          Description (Optional)

          {isSubmitting ? (
            
          ) : (
            
          )}
          {isSubmitting ? 'Adding Event...' : 'Add Event'}

  );
}

ActionForm.propTypes = {
  onAddEvent: PropTypes.func.isRequired,
};

export default ActionForm;