import { useState, useEffect } from 'react';
import { apiUrl } from '../config/api';

export const useRecentProjects = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRecentProjects = async () => {
      try {
        setLoading(true);
        
        const response = await fetch(apiUrl('api/project-history'));
            if (response.ok) break;
          } catch (err) {
            lastError = err;
            continue;
          }
        }
        
        if (!response || !response.ok) {
          throw new Error(lastError?.message || 'Backend server not available');
        }
        
        const data = await response.json();
        if (data.success) {
          // Limit to 5 most recent projects
          setProjects(data.projects.slice(0, 5) || []);
        } else {
          throw new Error(data.error || 'Failed to fetch projects');
        }
      } catch (err) {
        console.error('Error fetching recent projects:', err);
        setError(err.message);
        // Set mock data for testing when API is not available
        setProjects([
          {
            name: "E-commerce Site",
            slug: "ecommerce-test",
            created_date: Date.now() / 1000 - 3600 * 2, // 2 hours ago
            tech_stack: ["React", "TailwindCSS"]
          },
          {
            name: "Analytics Dashboard", 
            slug: "analytics-test",
            created_date: Date.now() / 1000 - 3600 * 24, // 1 day ago
            tech_stack: ["React", "FastAPI"]
          }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchRecentProjects();
  }, []);

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours} hours ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays === 1) return 'Yesterday';
    if (diffInDays < 7) return `${diffInDays} days ago`;
    
    return date.toLocaleDateString();
  };

  return { projects, loading, error, formatTimeAgo };
};