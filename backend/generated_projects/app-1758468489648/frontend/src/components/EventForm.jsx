import React, { useState } from 'react';
import PropTypes from 'prop-types';

/**
 * EventForm Component
 * A modal form for adding a new college event.
 * Manages its own state for form fields and performs basic validation.
 */
function EventForm({ onSave, onClose }) {
  const [formData, setFormData] = useState({
    title: '',
    organizer: '',
    location: '',
    date: '',
    time: '',
    description: '',
  });
  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.title.trim()) newErrors.title = 'Event title is required.';
    if (!formData.organizer.trim()) newErrors.organizer = 'Organizer/Club is required.';
    if (!formData.location.trim()) newErrors.location = 'Location is required.';
    if (!formData.date) newErrors.date = 'Date is required.';
    if (!formData.time) newErrors.time = 'Time is required.';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validate()) {
      onSave(formData);
    }
  };

  return (
    
       e.stopPropagation()}>
        Add New Event

            {/* Title */}
            
              Event Title
              
              {errors.title && {errors.title}}

            {/* Organizer */}
            
              Organizer / Club
              
              {errors.organizer && {errors.organizer}}

            {/* Location */}
            
              Location
              
              {errors.location && {errors.location}}

            {/* Date */}
            
              Date
              
              {errors.date && {errors.date}}

            {/* Time */}
            
              Time
              
              {errors.time && {errors.time}}

            {/* Description */}
            
              Description

              Cancel

              Save Event

  );
}

EventForm.propTypes = {
  onSave: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default EventForm;