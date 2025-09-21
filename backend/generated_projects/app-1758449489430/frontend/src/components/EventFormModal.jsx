import React, { useState, Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { CgSpinner } from 'react-icons/cg';
import clsx from 'clsx';

function EventFormModal({ isOpen, onClose, onSubmit, categories }) {
    const [formData, setFormData] = useState({
        title: '',
        date: '',
        time: '',
        location: '',
        department: '',
        category: categories[0] || '',
        description: ''
    });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const resetForm = () => {
        setFormData({
            title: '',
            date: '',
            time: '',
            location: '',
            department: '',
            category: categories[0] || '',
            description: ''
        });
        setError('');
    }

    const handleClose = () => {
        if (isSubmitting) return;
        resetForm();
        onClose();
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        
        // Basic Validation
        if (!formData.title || !formData.date || !formData.time || !formData.location || !formData.department || !formData.description) {
            setError('Please fill out all required fields.');
            return;
        }

        setIsSubmitting(true);
        const eventDateTime = `${formData.date}T${formData.time}:00`;

        const result = await onSubmit({
          title: formData.title,
          date: eventDateTime,
          location: formData.location,
          department: formData.department,
          category: formData.category,
          description: formData.description
        });
        
        setIsSubmitting(false);

        if (result.success) {
            handleClose();
        } else {
            setError(result.message || 'An unknown error occurred.');
        }
    };
    
    return (

                                    Submit a New Event

                                    {error && {error}}

                                        Category
                                        
                                            {categories.map(cat => {cat})}

                                        Description

                                            Cancel

                                            {isSubmitting ?  : 'Submit'}

    );
}

// Reusable Input Field Component
const InputField = ({ label, ...props }) => (
    
        {label}

);

export default EventFormModal;