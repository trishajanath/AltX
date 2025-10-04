import React, { useState, useEffect, useCallback } from 'react';

// Import all React Bits components with comprehensive fallbacks
let Button, Card, CardHeader, CardBody;
try {
  const ButtonModule = require('./components/ui/Button');
  Button = ButtonModule.Button;
} catch (error) {
  // Fallback Button
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
        {...(props || {})}
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

// Import AnimatedText with fallback for reliability
let SplitText, GradientText;
try {
  const AnimatedTextModule = require('./components/ui/AnimatedText');
  SplitText = AnimatedTextModule.SplitText;
  GradientText = AnimatedTextModule.GradientText;
} catch (error) {
  // Fallback SplitText
  SplitText = ({ text, className = '' }) => (
    <span className={`inline-block ${className}`}>{text}</span>
  );
  // Fallback GradientText  
  GradientText = ({ text, className = '' }) => (
    <span className={`bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent ${className}`}>
      {text}
    </span>
  );
}

// Import Navigation with fallback for reliability
let NavBar, NavLink;
try {
  const NavigationModule = require('./components/ui/Navigation');
  NavBar = NavigationModule.NavBar;
  NavLink = NavigationModule.NavLink;
} catch (error) {
  // Fallback NavBar
  NavBar = ({ children, className = '' }) => (
    <nav className={`bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">{children}</div>
      </div>
    </nav>
  );
  NavLink = ({ href, children, isActive, className = '' }) => (
    <a href={href} className={`inline-flex items-center px-1 pt-1 text-sm font-medium transition-colors ${isActive ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'} ${className}`}>
      {children}
    </a>
  );
}

// Import Lucide React icons with fallbacks
let Download, Github, ExternalLink, X;
try {
  const LucideModule = require('lucide-react');
  Download = LucideModule.Download;
  Github = LucideModule.Github;
  ExternalLink = LucideModule.ExternalLink;
  X = LucideModule.X;
} catch (error) {
  // Fallback icon components using Unicode symbols
  Download = ({ className = '', ...props }) => (
    <span className={`inline-block ${className}`} {...(props || {})} >⬇</span>
  );
  Github = ({ className = '', ...props }) => (
    <span className={`inline-block ${className}`} {...(props || {})} >⚡</span>
  );
  ExternalLink = ({ className = '', ...props }) => (
    <span className={`inline-block ${className}`} {...(props || {})} >↗</span>
  );
  X = ({ className = '', ...props }) => (
    <span className={`inline-block ${className}`} {...(props || {})} >✕</span>
  );
}

// Include inline SpinnerLoader to avoid import issues
const SpinnerLoader = ({ size = 'md', className = '' }) => {
  const sizes = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' };
  return <div className={`${sizes[size]} border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin ${className}`} />;
};

// --- Helper Components ---

const Section = ({ children, id, className = '' }) => (
  <section id={id} className={`py-16 md:py-24 ${className}`}>
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
      {children}
    </div>
  </section>
);

const SectionTitle = ({ children }) => (
  <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">
    <GradientText text={children} />
  </h2>
);

const TechTag = ({ children }) => (
  <span className="inline-block bg-blue-100 text-blue-800 text-xs font-medium mr-2 mb-2 px-2.5 py-0.5 rounded-full">
    {children}
  </span>
);

// --- Main Feature Components ---

const AppNavbar = () => {
  const [activeSection, setActiveSection] = useState('home');

  useEffect(() => {
    const sections = document.querySelectorAll('section[id]');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          setActiveSection(entry.target.id);
        }
      });
    }, { rootMargin: "-50% 0px -50% 0px" });

    sections.forEach(section => observer.observe(section));
    return () => sections.forEach(section => observer.unobserve(section));
  }, []);

  return (
    <NavBar>
      <div className="flex items-center">
        <a href="#home" className="text-xl font-bold text-gray-800">
          <GradientText text="DevFolio" />
        </a>
      </div>
      <div className="hidden sm:flex sm:items-center sm:space-x-8">
        <NavLink href="#projects" isActive={activeSection === 'projects'}>Projects</NavLink>
        <NavLink href="#about" isActive={activeSection === 'about'}>About</NavLink>
        <NavLink href="#contact" isActive={activeSection === 'contact'}>Contact</NavLink>
      </div>
    </NavBar>
  );
};

const HeroSectionComponent = () => (
  <Section id="home" className="bg-gray-50 min-h-screen flex items-center -mt-16 pt-16">
    <div className="text-center w-full">
      <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-4">
        <SplitText text="Creative Full-Stack Developer" className="block" />
      </h1>
      <p className="max-w-2xl mx-auto text-lg md:text-xl text-gray-600 mb-8">
        I build modern, responsive, and user-friendly web applications from concept to deployment.
      </p>
      <div className="flex justify-center space-x-4">
        <Button as="a" href="#contact" size="lg" variant="primary">
          Get In Touch
        </Button>
        <Button as="a" href="/resume.pdf" download size="lg" variant="outline">
          <Download className="w-5 h-5 mr-2" />
          Download CV
        </Button>
      </div>
    </div>
  </Section>
);

const ProjectsSection = ({ projects, loading, error }) => (
  <Section id="projects" className="bg-white">
    <SectionTitle>My Projects</SectionTitle>
    {loading && <div className="flex justify-center"><SpinnerLoader size="lg" /></div>}
    {error && <p className="text-center text-red-500">{error}</p>}
    {!loading && !error && (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {Array.isArray(projects) && projects.length > 0 ? (
          projects.map((project, index) => (
            <Card key={project.id || index} className="flex flex-col transition-transform duration-300 hover:scale-105 hover:shadow-xl">
              <CardHeader>
                <h3 className="text-xl font-bold text-gray-900">{project.name}</h3>
              </CardHeader>
              <CardBody className="flex-grow">
                <p className="text-gray-600 mb-4">{project.description}</p>
                <div className="mb-4">
                  {Array.isArray(project.tags) && project.tags.map(tag => <TechTag key={tag}>{tag}</TechTag>)}
                </div>
              </CardBody>
              <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
                {project.github_url && (
                  <Button as="a" href={project.github_url} target="_blank" rel="noopener noreferrer" variant="secondary" size="sm">
                    <Github className="w-4 h-4 mr-2" /> Code
                  </Button>
                )}
                {project.live_url && (
                  <Button as="a" href={project.live_url} target="_blank" rel="noopener noreferrer" variant="primary" size="sm">
                    <ExternalLink className="w-4 h-4 mr-2" /> Live Demo
                  </Button>
                )}
              </div>
            </Card>
          ))
        ) : (
          <p className="text-center text-gray-500 col-span-full">No projects found. Check back later!</p>
        )}
      </div>
    )}
  </Section>
);

const AboutSection = () => {
  const skills = ['React', 'Node.js', 'Express', 'MongoDB', 'PostgreSQL', 'TailwindCSS', 'Docker', 'AWS', 'JavaScript (ES6+)', 'TypeScript'];
  const experiences = [
    { role: 'Senior Frontend Developer', company: 'Tech Solutions Inc.', period: '2020 - Present', desc: 'Leading the development of a large-scale SaaS platform using React and TypeScript, improving performance by 30%.' },
    { role: 'Full-Stack Developer', company: 'Digital Creations', period: '2018 - 2020', desc: 'Developed and maintained client websites and internal tools using the MERN stack.' },
  ];

  return (
    <Section id="about" className="bg-gray-50">
      <SectionTitle>About Me</SectionTitle>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div className="prose prose-lg text-gray-600">
          <p>
            Hello! I'm a passionate Full-Stack Developer with over 5 years of experience in creating dynamic and efficient web applications. My expertise lies in the JavaScript ecosystem, particularly with React for the frontend and Node.js for the backend.
          </p>
          <p>
            I thrive on solving complex problems and am committed to writing clean, scalable, and well-documented code. I'm always eager to learn new technologies and improve my craft.
          </p>
        </div>
        <div>
          <h3 className="text-2xl font-bold mb-4 text-gray-800">My Skills</h3>
          <div className="flex flex-wrap mb-8">
            {skills.map(skill => <TechTag key={skill}>{skill}</TechTag>)}
          </div>
          <h3 className="text-2xl font-bold mb-4 text-gray-800">Experience</h3>
          <div className="space-y-6">
            {experiences.map(exp => (
              <div key={exp.company}>
                <h4 className="text-lg font-semibold text-gray-900">{exp.role} at {exp.company}</h4>
                <p className="text-sm text-gray-500 mb-1">{exp.period}</p>
                <p className="text-gray-600">{exp.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Section>
  );
};

const ContactSection = () => {
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [formStatus, setFormStatus] = useState({ status: 'idle', message: '' }); // idle, sending, success, error

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormStatus({ status: 'sending', message: '' });
    try {
      const response = await fetch('http://localhost:8000/api/v1/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok.');
      }
      
      setFormStatus({ status: 'success', message: 'Message sent successfully! I will get back to you soon.' });
      setFormData({ name: '', email: '', message: '' });
    } catch (error) {
      setFormStatus({ status: 'error', message: 'Something went wrong. Please try again later.' });
    }
  };

  return (
    <Section id="contact" className="bg-white">
      <SectionTitle>Get In Touch</SectionTitle>
      <div className="max-w-2xl mx-auto">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">Name</label>
            <input type="text" name="name" id="name" required value={formData.name} onChange={handleInputChange} className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
            <input type="email" name="email" id="email" required value={formData.email} onChange={handleInputChange} className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
          </div>
          <div>
            <label htmlFor="message" className="block text-sm font-medium text-gray-700">Message</label>
            <textarea name="message" id="message" rows="4" required value={formData.message} onChange={handleInputChange} className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"></textarea>
          </div>
          <div className="flex items-center justify-between">
            <Button type="submit" size="lg" disabled={formStatus.status === 'sending'}>
              {formStatus.status === 'sending' ? <SpinnerLoader size="sm" className="mr-2" /> : null}
              {formStatus.status === 'sending' ? 'Sending...' : 'Send Message'}
            </Button>
            {formStatus.status === 'success' && <p className="text-green-600">{formStatus.message}</p>}
            {formStatus.status === 'error' && <p className="text-red-600">{formStatus.message}</p>}
          </div>
        </form>
      </div>
    </Section>
  );
};

const AppFooter = () => (
  <footer className="bg-gray-800 text-white py-6">
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
      <p>&copy; {new Date().getFullYear()} DevFolio. All rights reserved.</p>
    </div>
  </footer>
);


const App1759582442022 = () => {
  const [projects, setProjects] = useState([]);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [projectsError, setProjectsError] = useState(null);

  const fetchProjects = useCallback(async () => {
    setProjectsLoading(true);
    setProjectsError(null);
    try {
      const response = await fetch('http://localhost:8000/api/v1/projects');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setProjects(data.projects || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
      setProjectsError("Failed to load projects. Please try refreshing the page.");
    } finally {
      setProjectsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return (
    <div className="bg-gray-50 text-gray-800 font-sans antialiased">
      <AppNavbar />
      <main>
        <HeroSectionComponent />
        <ProjectsSection projects={projects} loading={projectsLoading} error={projectsError} />
        <AboutSection />
        <ContactSection />
      </main>
      <AppFooter />
    </div>
  );
};

export default App1759582442022;