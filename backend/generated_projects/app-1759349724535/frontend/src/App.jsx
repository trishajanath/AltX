import React, { useState, useEffect, useCallback } from 'react';

// --- Helper Functions for Safe LocalStorage ---

const getCachedData = (key) => {
  try {
    const item = localStorage.getItem(key);
    // Ensure item is not null, undefined, or the string 'undefined' before parsing
    if (item && item !== 'undefined') {
      try {
        // Second try/catch specifically for parsing, as it can fail
        return JSON.parse(item);
      } catch (parseError) {
        console.error(`Error parsing JSON from localStorage for key "${key}":`, parseError);
        return null;
      }
    }
  } catch (error) {
    console.error(`Error accessing localStorage for key "${key}":`, error);
  }
  return null;
};

const setCachedData = (key, data) => {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (error) {
    console.error(`Error setting localStorage for key "${key}":`, error);
  }
};


// --- UI Components (Internal to App.jsx) ---

const Nav = ({ currentView, setView }) => (
  <nav className="bg-gray-800 text-white p-4 shadow-md sticky top-0 z-50">
    <div className="container mx-auto flex justify-between items-center">
      <h1 className="text-2xl font-bold text-cyan-400">Creative Solutions Inc.</h1>
      <div className="space-x-6">
        {['Home', 'Services', 'Portfolio'].map((viewName) => (
          <button
            key={viewName}
            onClick={() => setView(viewName.toLowerCase())}
            className={`text-lg font-medium transition-colors duration-300 ${
              currentView === viewName.toLowerCase()
                ? 'text-cyan-400 border-b-2 border-cyan-400'
                : 'text-gray-300 hover:text-white'
            }`}
          >
            {viewName}
          </button>
        ))}
      </div>
    </div>
  </nav>
);

const HomePage = ({ setView }) => (
  <div className="flex items-center justify-center h-[calc(100vh-64px)] bg-gray-900 text-white text-center">
    <div className="max-w-4xl mx-auto px-4">
      <h1 className="text-5xl md:text-7xl font-extrabold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-500">
        Innovate, Create, Elevate
      </h1>
      <p className="text-xl md:text-2xl text-gray-300 mb-8">
        We build stunning, high-performance web solutions that drive results.
      </p>
      <div className="space-x-4">
        <button
          onClick={() => setView('services')}
          className="bg-cyan-500 hover:bg-cyan-600 text-white font-bold py-3 px-8 rounded-full transition-transform transform hover:scale-105 duration-300"
        >
          Our Services
        </button>
        <button
          onClick={() => setView('portfolio')}
          className="bg-transparent border-2 border-cyan-500 hover:bg-cyan-500 text-cyan-500 hover:text-white font-bold py-3 px-8 rounded-full transition duration-300"
        >
          View Our Work
        </button>
      </div>
    </div>
  </div>
);

const ServicesPage = ({ services }) => (
  <div className="bg-gray-100 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
    <div className="container mx-auto">
      <div className="text-center mb-12">
        <h2 className="text-4xl font-extrabold text-gray-900">Our Offerings</h2>
        <p className="mt-4 text-lg text-gray-600">
          We provide a wide range of services to bring your vision to life.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {Array.isArray(services) && services.length > 0 ? (
          services.map((service) => (
            <div key={service.id} className="bg-white p-8 rounded-lg shadow-lg hover:shadow-xl transition-shadow duration-300">
              <div className="text-cyan-500 mb-4">
                {/* A placeholder for an icon */}
                <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">{service.name}</h3>
              <p className="text-gray-600">{service.description}</p>
            </div>
          ))
        ) : (
          <p className="text-gray-500 col-span-full text-center">No services available at the moment.</p>
        )}
      </div>
    </div>
  </div>
);

const PortfolioPage = ({ projects }) => (
  <div className="bg-gray-100 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
    <div className="container mx-auto">
      <div className="text-center mb-12">
        <h2 className="text-4xl font-extrabold text-gray-900">Our Portfolio</h2>
        <p className="mt-4 text-lg text-gray-600">
          A showcase of our passion, dedication, and expertise.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {Array.isArray(projects) && projects.length > 0 ? (
          projects.map((project) => (
            <div key={project.id} className="bg-white rounded-lg shadow-lg overflow-hidden group">
              <div className="relative">
                <img
                  src={project.imageUrl || `https://picsum.photos/seed/${project.id}/600/400`}
                  alt={project.title}
                  className="w-full h-60 object-cover transition-transform duration-500 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                  <a href={project.link} target="_blank" rel="noopener noreferrer" className="text-white border-2 border-white py-2 px-4 rounded-md hover:bg-white hover:text-black">
                    View Project
                  </a>
                </div>
              </div>
              <div className="p-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{project.title}</h3>
                <p className="text-gray-600 mb-4">{project.description}</p>
                <div className="flex flex-wrap gap-2">
                  {Array.isArray(project.technologies) && project.technologies.map((tech) => (
                    <span key={tech} className="bg-cyan-100 text-cyan-800 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded-full">
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))
        ) : (
          <p className="text-gray-500 col-span-full text-center">No projects to display right now.</p>
        )}
      </div>
    </div>
  </div>
);

// --- Main App Component ---

function App() {
  // State initialization
  const [view, setView] = useState('home');
  const [services, setServices] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_BASE_URL = 'http://localhost:8000/api/v1';

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    // Attempt to load from cache first
    const cachedServices = getCachedData('services');
    const cachedProjects = getCachedData('projects');

    if (cachedServices && cachedProjects) {
      setServices(cachedServices);
      setProjects(cachedProjects);
      setLoading(false);
      return;
    }

    try {
      const [servicesResponse, projectsResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/services`),
        fetch(`${API_BASE_URL}/projects`),
      ]);

      if (!servicesResponse.ok) {
        throw new Error(`Failed to fetch services: ${servicesResponse.status} ${servicesResponse.statusText}`);
      }
      if (!projectsResponse.ok) {
        throw new Error(`Failed to fetch projects: ${projectsResponse.status} ${projectsResponse.statusText}`);
      }

      const servicesData = await servicesResponse.json();
      const projectsData = await projectsResponse.json();

      // Ensure data is an array before setting state
      const validServices = Array.isArray(servicesData) ? servicesData : [];
      const validProjects = Array.isArray(projectsData) ? projectsData : [];

      setServices(validServices);
      setProjects(validProjects);

      // Cache the new data
      setCachedData('services', validServices);
      setCachedData('projects', validProjects);

    } catch (err) {
      console.error("API Fetch Error:", err);
      setError(err.message || 'An unexpected error occurred. Please try again later.');
      // CRITICAL: Ensure state is a valid array on failure to prevent render errors
      setServices([]);
      setProjects([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex justify-center items-center h-screen bg-gray-100">
          <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-cyan-500"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex justify-center items-center h-screen bg-red-50 text-red-700 p-4">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-2">Oops! Something went wrong.</h2>
            <p>{error}</p>
            <button
              onClick={fetchData}
              className="mt-4 bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded"
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    switch (view) {
      case 'services':
        return <ServicesPage services={services} />;
      case 'portfolio':
        return <PortfolioPage projects={projects} />;
      case 'home':
      default:
        return <HomePage setView={setView} />;
    }
  };

  return (
    <div className="App">
      <Nav currentView={view} setView={setView} />
      <main>
        {renderContent()}
      </main>
    </div>
  );
}

export default App;