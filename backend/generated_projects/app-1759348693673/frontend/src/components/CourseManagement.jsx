import React, { useState, useEffect, useCallback } from 'react';
import AddCourseModal from './AddCourseModal';
import { PlusIcon, BookOpenIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const CourseManagement = () => {
  const [courses, setCourses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchCourses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/courses`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setCourses(data);
    } catch (e) {
      console.error("Failed to fetch courses:", e);
      setError("Failed to load courses. Please check the API connection and try again.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCourses();
  }, [fetchCourses]);

  const handleAddCourse = async (courseData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/courses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(courseData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      
      // On success, close modal and refresh course list
      setIsModalOpen(false);
      fetchCourses();
      return { success: true };
    } catch (e) {
      console.error("Failed to add course:", e);
      return { success: false, message: e.message };
    }
  };

  const renderContent = () => {
    if (isLoading) {
      return Loading courses...;
    }

    if (error) {
      return (
        
          
            
            
              Error
              {error}
            
          
        
      );
    }

    if (courses.length === 0) {
      return (
        
            
            No courses found
            Get started by adding a new course.
        
      );
    }

    return (
      
        
          
            
              Course Name
              Course Code
              Description
            
          
          
            {courses.map((course) => (
              
                {course.name}
                {course.code}
                {course.description || 'N/A'}
              
            ))}
          
        
      
    );
  };

  return (
    
      
        Course Management
         setIsModalOpen(true)}
          className="inline-flex items-center justify-center rounded-md border border-transparent bg-primary px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 transition-colors"
        >
          
          Add Course
        
      
      
      {renderContent()}

       setIsModalOpen(false)}
        onAddCourse={handleAddCourse}
      />
    
  );
};

export default CourseManagement;