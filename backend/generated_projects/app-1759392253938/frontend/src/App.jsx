import React, { useState, useEffect, useCallback } from 'react';

// Try to import all React Bits UI components with fallbacks
let Button, Card, CardHeader, CardBody;
try {
  const ButtonModule = require('./components/ui/Button');
  Button = ButtonModule.Button;
} catch (error) {
  console.log('Using fallback Button component');
  // Fallback Button component
  Button = ({ children, variant = 'primary', size = 'md', className = '', ...props }) => {
    const variants = {
      primary: 'bg-blue-600 hover:bg-blue-700 text-white',
      secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
      outline: 'border border-gray-300 hover:bg-gray-50 text-gray-700'
    };
    const sizes = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base', 
      lg: 'px-6 py-3 text-lg'
    };
    return (
      <button 
        className={`inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${variants[variant]} ${sizes[size]} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  };
}

try {
  const CardModule = require('./components/ui/Card');
  Card = CardModule.Card;
  CardHeader = CardModule.CardHeader;
  CardBody = CardModule.CardBody;
} catch (error) {
  console.log('Using fallback Card components');
  // Fallback Card components
  Card = ({ children, className = '' }) => (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      {children}
    </div>
  );
  CardHeader = ({ children, className = '' }) => (
    <div className={`px-6 py-4 border-b border-gray-200 ${className}`}>
      {children}
    </div>
  );
  CardBody = ({ children, className = '' }) => (
    <div className={`px-6 py-4 ${className}`}>
      {children}
    </div>
  );
}

// Try to import AnimatedText components with fallback
let SplitText, GradientText;
try {
  const AnimatedTextModule = require('./components/ui/AnimatedText');
  SplitText = AnimatedTextModule.SplitText;
  GradientText = AnimatedTextModule.GradientText;
} catch (error) {
  console.log('Using fallback AnimatedText components');
  // Fallback SplitText component
  SplitText = ({ text, className = '' }) => (
    <span className={`inline-block ${className}`}>{text}</span>
  );
  
  // Fallback GradientText component  
  GradientText = ({ text, className = '' }) => (
    <span className={`bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent ${className}`}>
      {text}
    </span>
  );
}

// Try to import Navigation components with fallback
let NavBar, NavLink;
try {
  const NavigationModule = require('./components/ui/Navigation');
  NavBar = NavigationModule.NavBar;
  NavLink = NavigationModule.NavLink;
} catch (error) {
  console.log('Using fallback Navigation components');
  // Fallback NavBar component
  NavBar = ({ children, className = '' }) => (
    <nav className={`bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {children}
        </div>
      </div>
    </nav>
  );
  
  // Fallback NavLink component
  NavLink = ({ href, children, isActive, className = '' }) => (
    <a
      href={href}
      className={`inline-flex items-center px-1 pt-1 text-sm font-medium transition-colors duration-200 ${
        isActive
          ? 'border-b-2 border-blue-500 text-blue-600'
          : 'text-gray-500 hover:text-gray-700'
      } ${className}`}
    >
      {children}
    </a>
  );
}

// Fallback SpinnerLoader in case of import issues
const SpinnerLoader = ({ size = 'md', className = '' }) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8', 
    lg: 'w-12 h-12'
  };
  
  return (
    <div className={`${sizes[size]} border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin ${className}`} />
  );
};

const SkeletonLoader = ({ className = '', lines = 3 }) => (
  <div className={`animate-pulse space-y-3 ${className}`}>
    {Array.from({ length: lines }).map((_, i) => (
      <div key={i} className="h-4 bg-gray-200 rounded-md"></div>
    ))}
  </div>
);

// Try to import Lucide React icons with fallbacks
let Download, Github, ExternalLink, X;
try {
  const LucideModule = require('lucide-react');
  Download = LucideModule.Download;
  Github = LucideModule.Github;
  ExternalLink = LucideModule.ExternalLink;
  X = LucideModule.X;
} catch (error) {
  console.log('Using fallback icon components');
  // Fallback icon components using simple Unicode symbols
  Download = ({ className = '', ...props }) => (
    <span className={`inline-block ${className}`} {...props}>⬇</span>
  );
  Github = ({ className = '', ...props }) => (
    <span className={`inline-block ${className}`} {...props}>⚡</span>
  );
  ExternalLink = ({ className = '', ...props }) => (
    <span className={`inline-block ${className}`} {...props}>↗</span>
  );
  X = ({ className = '', ...props }) => (
    <span className={`inline-block ${className}`} {...props}>✕</span>
  );
}

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Simple Tag component for project tags
const Tag = ({ children, variant = 'primary', className = '' }) => {
  const variants = {
    primary: 'bg-blue-600 text-blue-100',
    secondary: 'bg-gray-600 text-gray-100'
  };
  
  return (
    <span className={`inline-block px-3 py-1 text-xs font-medium rounded-full ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
};

// A reusable Section component for consistent styling
const Section = ({ id, title, children, className = '' }) => (
  <section id={id} className={`py-20 md:py-28 px-4 sm:px-6 lg:px-8 ${className}`}>
    <div className="container mx-auto max-w-6xl">
      <h2 className="text-3xl md:text-4xl font-bold text-center mb-12 text-slate-100">
        <SplitText>{title}</SplitText>
      </h2>
      {children}
    </div>
  </section>
);

// Main App Component
export default function App() {
  const [projects, setProjects] = useState([]);
  const [aboutData, setAboutData] = useState(null);
  const [skills, setSkills] = useState([]);
  const [experience, setExperience] = useState([]);
  
  const [selectedProject, setSelectedProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [projectsRes, aboutRes, skillsRes, experienceRes] = await Promise.all([
        fetch(`${API_BASE_URL}/projects`),
        fetch(`${API_BASE_URL}/about`),
        fetch(`${API_BASE_URL}/skills`),
        fetch(`${API_BASE_URL}/experience`),
      ]);

      if (!projectsRes.ok || !aboutRes.ok || !skillsRes.ok || !experienceRes.ok) {
        throw new Error('Network response was not ok for one or more resources.');
      }

      const projectsData = await projectsRes.json();
      const aboutData = await aboutRes.json();
      const skillsData = await skillsRes.json();
      const experienceData = await experienceRes.json();

      setProjects(projectsData.data || []);
      setAboutData(aboutData.data || {});
      setSkills(skillsData.data || []);
      setExperience(experienceData.data || []);

    } catch (err) {
      console.error("Failed to fetch data:", err);
      setError("Sorry, I couldn't load the portfolio data. Please try again later.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleProjectClick = (project) => {
    setSelectedProject(project);
    document.body.style.overflow = 'hidden';
  };

  const handleCloseModal = () => {
    setSelectedProject(null);
    document.body.style.overflow = 'auto';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex justify-center items-center">
        <SpinnerLoader size="lg" className="border-blue-400 border-t-white" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 flex justify-center items-center text-center text-red-400 px-4">
        <div>
          <h1 className="text-2xl font-bold mb-4">An Error Occurred</h1>
          <p>{error}</p>
          <Button onClick={fetchData} className="mt-6">Try Again</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 text-slate-300 font-sans antialiased">
      <NavBar className="glass-morphism">
        <div className="flex items-center space-x-8">
          <GradientText className="text-2xl font-bold">Portfolio</GradientText>
          <div className="hidden md:flex space-x-6">
            <NavLink href="#projects">Projects</NavLink>
            <NavLink href="#skills">Skills</NavLink>
            <NavLink href="#experience">Experience</NavLink>
            <NavLink href="#contact">Contact</NavLink>
          </div>
        </div>
      </NavBar>
      
      <main>
        {/* Hero Section */}
        <section className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-slate-900 via-blue-900 to-purple-900">
          <div className="text-center">
            <SplitText className="text-5xl md:text-7xl font-bold mb-6">
              <GradientText>Hello, I'm a Developer</GradientText>
            </SplitText>
            <p className="text-xl md:text-2xl mb-8 text-gray-300 max-w-2xl mx-auto">
              Crafting beautiful digital experiences with modern technologies
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button variant="primary" size="lg">View My Work</Button>
              <Button variant="secondary" size="lg">Get In Touch</Button>
            </div>
          </div>
        </section>

        {/* Dynamic Project Showcase */}
        <Section id="projects" title="My Creations">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {Array.isArray(projects) && projects.map((project) => (
              <Card 
                key={project.id} 
                className="transform hover:-translate-y-2 transition-transform duration-300 ease-in-out cursor-pointer"
                onClick={() => handleProjectClick(project)}
              >
                <img src={project.imageUrl} alt={project.title} className="w-full h-48 object-cover rounded-t-lg" />
                <div className="p-6">
                  <h3 className="text-xl font-bold text-slate-100 mb-2">{project.title}</h3>
                  <p className="text-slate-400 text-sm mb-4">{project.shortDescription}</p>
                  <div className="flex flex-wrap gap-2">
                    {Array.isArray(project.tags) && project.tags.slice(0, 4).map(tag => <Tag key={tag}>{tag}</Tag>)}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </Section>

        {/* About Me Section */}
        {aboutData && (
          <Section id="about" title="About Me" className="bg-slate-800/50">
            <div className="flex flex-col md:flex-row items-center gap-10 md:gap-16">
              <img src={aboutData.imageUrl} alt="Profile" className="w-48 h-48 md:w-60 md:h-60 rounded-full object-cover shadow-2xl shadow-cyan-500/20 flex-shrink-0" />
              <div className="text-center md:text-left">
                <p className="text-lg leading-relaxed mb-6">{aboutData.bio}</p>
                <Button 
                  onClick={() => window.open(aboutData.resumeUrl, '_blank')}
                  variant="primary"
                  size="lg"
                >
                  <Download className="mr-2" size={16} />
                  Download Resume
                </Button>
              </div>
            </div>
          </Section>
        )}

        {/* Skills & Experience Display */}
        <Section id="experience" title="Skills & Experience">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
            {/* Skills */}
            <div>
              <h3 className="text-2xl font-semibold text-slate-100 mb-6 text-center lg:text-left">Technical Skills</h3>
              <div className="flex flex-wrap justify-center lg:justify-start gap-4">
                {Array.isArray(skills) && skills.map(skill => (
                  <div key={skill.name} className="bg-slate-800 py-2 px-4 rounded-lg flex items-center gap-2 transition-colors hover:bg-cyan-500/20">
                    {/* In a real app, you might use an icon library here */}
                    <span className="text-cyan-400 text-xl">❖</span>
                    <span className="font-medium text-slate-200">{skill.name}</span>
                  </div>
                ))}
              </div>
            </div>
            {/* Experience */}
            <div>
              <h3 className="text-2xl font-semibold text-slate-100 mb-6 text-center lg:text-left">Career Journey</h3>
              <div className="relative border-l-2 border-slate-700 pl-8 space-y-12">
                {Array.isArray(experience) && experience.map((job, index) => (
                  <div key={index} className="relative">
                    <div className="absolute -left-[42px] top-1 h-4 w-4 rounded-full bg-cyan-400 ring-8 ring-slate-900"></div>
                    <p className="text-sm font-semibold text-cyan-400">{job.startDate} - {job.endDate}</p>
                    <h4 className="text-xl font-bold text-slate-100 mt-1">{job.title}</h4>
                    <p className="text-md text-slate-400 mb-2">{job.company}</p>
                    <p className="text-sm leading-relaxed">{job.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Section>
      </main>

      {/* Project Detail Modal */}
      {selectedProject && (
        <div 
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex justify-center items-center p-4 animate-fade-in"
          onClick={handleCloseModal}
        >
          <div 
            className="bg-slate-800 rounded-lg shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto relative animate-slide-in-up"
            onClick={(e) => e.stopPropagation()}
          >
            <button onClick={handleCloseModal} className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors z-10">
              <X size={24} />
            </button>
            <img src={selectedProject.imageUrl} alt={selectedProject.title} className="w-full h-64 object-cover rounded-t-lg" />
            <div className="p-8">
              <h2 className="text-3xl font-bold text-white mb-2">{selectedProject.title}</h2>
              <div className="flex flex-wrap gap-2 mb-6">
                {Array.isArray(selectedProject.tags) && selectedProject.tags.map(tag => <Tag key={tag} variant="secondary">{tag}</Tag>)}
              </div>
              <p className="text-slate-300 leading-relaxed mb-6">{selectedProject.longDescription}</p>
              <div className="flex items-center gap-4">
                {selectedProject.liveUrl && (
                  <Button as="a" href={selectedProject.liveUrl} target="_blank" rel="noopener noreferrer" variant="primary">
                    <ExternalLink className="mr-2" size={16} />
                    Live Demo
                  </Button>
                )}
                {selectedProject.repoUrl && (
                  <Button as="a" href={selectedProject.repoUrl} target="_blank" rel="noopener noreferrer" variant="outline">
                    <Github className="mr-2" size={16} />
                    View Code
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}