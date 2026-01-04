import React, { useState, useMemo } from 'react';

// UTILITY: Class Name Merger (simplified version of clsx/tailwind-merge)
const cn = (...classes) => {
  return classes.filter(Boolean).join(' ');
};

// STYLES: shadcn/ui style variants
const buttonVariants = {
  default: "bg-white text-black hover:bg-gray-200",
  destructive: "bg-red-500 text-white hover:bg-red-600",
  outline: "border border-white bg-transparent hover:bg-white hover:text-black",
  secondary: "bg-gray-800 text-white hover:bg-gray-700",
  ghost: "hover:bg-gray-800",
  link: "text-white underline-offset-4 hover:underline",
};

const cardVariants = {
  default: "bg-gray-900 border border-gray-700 rounded-lg shadow-lg",
};

const badgeVariants = {
    default: "border-transparent bg-gray-700 text-gray-200",
    secondary: "border-transparent bg-blue-500 text-white",
}

// ERROR BOUNDARY COMPONENT (Critical Requirement)
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-black text-white">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-red-500">Something went wrong.</h1>
            <p className="mt-4">Please refresh the page or try again later.</p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// ICONS (Defined as proper React components)
const Code = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>;
const Briefcase = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>;
const GraduationCap = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M22 10v6M2 10l10-5 10 5-10 5z"></path><path d="M6 12v5c3 3 9 3 12 0v-5"></path></svg>;
const Mail = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><rect width="20" height="16" x="2" y="4" rx="2"></rect><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path></svg>;
const Download = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>;
const ArrowRight = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>;
const Github = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>;
const Linkedin = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg>;
const Menu = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><line x1="4" x2="20" y1="12" y2="12" /><line x1="4" x2="20" y1="6" y2="6" /><line x1="4" x2="20" y1="18" y2="18" /></svg>;

// REUSABLE UI COMPONENTS (shadcn/ui style)
const Button = ({ children, variant = "default", className = "", ...props }) => (
  <button className={cn("inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 disabled:opacity-50 disabled:pointer-events-none", buttonVariants[variant], className)} {...props}>
    {children}
  </button>
);

const Card = ({ children, className = "", variant = "default" }) => <div className={cn(cardVariants[variant], className)}>{children}</div>;
const CardHeader = ({ children, className = "" }) => <div className={cn("p-6", className)}>{children}</div>;
const CardTitle = ({ children, className = "" }) => <h3 className={cn("text-xl font-semibold tracking-tight text-white", className)}>{children}</h3>;
const CardDescription = ({ children, className = "" }) => <p className={cn("text-sm text-gray-400", className)}>{children}</p>;
const CardContent = ({ children, className = "" }) => <div className={cn("p-6 pt-0", className)}>{children}</div>;

const Badge = ({ children, variant = "default", className = "" }) => (
    <div className={cn("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2", badgeVariants[variant], className)}>
        {children}
    </div>
);

// MOCK DATA
const projectsData = [
  {
    title: "AI-Powered Financial Analyst Chatbot",
    description: "A conversational AI that provides real-time stock analysis and market insights using natural language processing and financial data APIs.",
    tags: ["FastAPI", "Python", "NLP", "React"],
    imageUrl: "https://images.unsplash.com/photo-1611162617213-6d221bde38ac?q=80&w=800&auto=format&fit=crop",
    caseStudyUrl: "#",
  },
  {
    title: "E-commerce Recommendation Engine",
    description: "Developed a collaborative filtering model to provide personalized product recommendations, increasing user engagement by 20%.",
    tags: ["Python", "Data Analysis", "Machine Learning"],
    imageUrl: "https://images.unsplash.com/photo-1522199755839-a2bacb67c546?q=80&w=800&auto=format&fit=crop",
    caseStudyUrl: "#",
  },
  {
    title: "Interactive Data Visualization Dashboard",
    description: "A web-based dashboard for visualizing complex sales data, built with React and D3.js, allowing for dynamic filtering and exploration.",
    tags: ["React", "JavaScript", "Data Analysis"],
    imageUrl: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=800&auto=format&fit=crop",
    caseStudyUrl: "#",
  },
  {
    title: "Cloud-Native API Gateway",
    description: "A secure and scalable API gateway using FastAPI and Docker, deployed on AWS to manage microservices communication.",
    tags: ["FastAPI", "Python", "AWS", "Docker"],
    imageUrl: "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?q=80&w=800&auto=format&fit=crop",
    caseStudyUrl: "#",
  },
];

const skillsData = [
  { name: "Python", proficiency: "Expert", icon: "🐍" },
  { name: "JavaScript", proficiency: "Advanced", icon: "📜" },
  { name: "React", proficiency: "Advanced", icon: "⚛️" },
  { name: "FastAPI", proficiency: "Advanced", icon: "🚀" },
  { name: "SQL", proficiency: "Expert", icon: "🗃️" },
  { name: "AWS", proficiency: "Intermediate", icon: "☁️" },
  { name: "Docker", proficiency: "Intermediate", icon: "🐳" },
  { name: "Git", proficiency: "Expert", icon: "🌿" },
];

const timelineData = [
  {
    type: "work",
    title: "Software Development Intern",
    company: "Innovatech Solutions Inc.",
    date: "May 2023 - Aug 2023",
    description: "Contributed to a production FastAPI backend, developed new API endpoints, and wrote unit tests, improving code coverage by 15%. Collaborated with the frontend team to integrate new features.",
    icon: <Briefcase className="h-5 w-5 text-white" />,
  },
  {
    type: "education",
    title: "Master of Science in Computer Science",
    company: "Georgia Institute of Technology",
    date: "Expected May 2025",
    description: "Specializing in Machine Learning and Interactive Intelligence. Coursework includes: Deep Learning, Data Visualization, and High-Performance Computing.",
    icon: <GraduationCap className="h-5 w-5 text-white" />,
  },
  {
    type: "work",
    title: "Data Analyst Co-op",
    company: "Data Insights Corp.",
    date: "Jan 2022 - Aug 2022",
    description: "Cleaned and analyzed large datasets to identify market trends. Created automated reports and dashboards using Python and SQL, providing key insights to the marketing team.",
    icon: <Briefcase className="h-5 w-5 text-white" />,
  },
  {
    type: "education",
    title: "Bachelor of Science in Computer Engineering",
    company: "University of Illinois Urbana-Champaign",
    date: "Graduated May 2023",
    description: "Graduated with High Honors. Senior capstone project involved building a low-cost IoT sensor network for agricultural monitoring.",
    icon: <GraduationCap className="h-5 w-5 text-white" />,
  },
];

// Smooth scroll helper with guard to avoid errors when an anchor is missing
const scrollToSection = (id) => {
  const el = typeof document !== 'undefined' ? document.getElementById(id) : null;
  if (el && typeof el.scrollIntoView === 'function') {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } else {
    // Fallback: update hash so the browser can attempt to navigate, but do not throw
    window.location.hash = `#${id}`;
  }
};

// SECTION COMPONENTS
const Header = () => {
  const [isOpen, setIsOpen] = useState(false);
  const navLinks = ["About", "Projects", "Experience", "Contact"];

  return (
    <header className="sticky top-0 z-50 w-full bg-black/70 backdrop-blur-sm">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 md:px-6">
        <a href="#" className="text-xl font-bold tracking-tighter">
          Nilisha S.
        </a>
        <nav className="hidden md:flex items-center space-x-6">
          {navLinks.map(link => (
            <button
              key={link}
              onClick={() => scrollToSection(link.toLowerCase())}
              className="text-sm font-medium text-gray-300 hover:text-white transition-colors"
            >
              {link}
            </button>
          ))}
        </nav>
        <div className="hidden md:flex items-center space-x-4">
            <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white"><Github className="h-5 w-5" /></a>
            <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white"><Linkedin className="h-5 w-5" /></a>
        </div>
        <button className="md:hidden" onClick={() => setIsOpen(!isOpen)}>
          <Menu className="h-6 w-6" />
        </button>
      </div>
      {isOpen && (
        <div className="md:hidden bg-black pb-4">
          <nav className="flex flex-col items-center space-y-4">
            {navLinks.map(link => (
              <button
                key={link}
                onClick={() => {
                  scrollToSection(link.toLowerCase());
                  setIsOpen(false);
                }}
                className="text-sm font-medium text-gray-300 hover:text-white transition-colors"
              >
                {link}
              </button>
            ))}
            <div className="flex items-center space-x-4 pt-2">
                <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white"><Github className="h-6 w-6" /></a>
                <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white"><Linkedin className="h-6 w-6" /></a>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
};

const HeroSection = () => (
  <section className="relative w-full py-24 md:py-32 lg:py-40 overflow-hidden">
    <div className="absolute inset-0 bg-black z-10">
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/40 via-purple-900/30 to-black opacity-50"></div>
    </div>
    <div className="container mx-auto px-4 md:px-6 text-center relative z-20">
      <h1 className="text-4xl md:text-6xl lg:text-7xl font-extrabold tracking-tighter text-white">
        Nilisha Sharma
      </h1>
      <p className="mt-4 max-w-2xl mx-auto text-lg md:text-xl text-gray-300">
        Full-Stack Developer & Data Enthusiast. I build intelligent, scalable web applications that solve real-world problems.
      </p>
      <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
        <Button 
          variant="default" 
          className="text-base px-6 py-3"
          onClick={() => window.open('/nilisha-sharma-resume.pdf', '_blank')}
        >
          <Download className="mr-2 h-5 w-5" />
          Download Resume
        </Button>
        <Button 
          variant="outline" 
          className="text-base px-6 py-3"
          onClick={() => scrollToSection('contact')}
        >
          Get In Touch
        </Button>
      </div>
    </div>
  </section>
);

const AboutSection = () => (
  <section id="about" className="py-20 md:py-28 bg-black">
    <div className="container mx-auto px-4 md:px-6">
      <div className="grid md:grid-cols-2 gap-12 items-center">
        <div>
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white">About Me</h2>
          <p className="mt-4 text-gray-300">
            I am a passionate developer with a strong foundation in computer science and a specialization in machine learning. My journey in tech is driven by a curiosity to understand complex systems and a desire to build efficient, user-centric solutions.
          </p>
          <p className="mt-4 text-gray-300">
            From crafting responsive frontends with React to architecting robust backends with FastAPI, I enjoy working across the full stack. I'm particularly interested in the intersection of web development and data science, where I can leverage data to create smarter, more personalized user experiences.
          </p>
        </div>
        <div>
          <h3 className="text-2xl font-semibold text-white mb-6">My Tech Stack</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {skillsData.map((skill) => (
              <div key={skill.name} className="group relative flex flex-col items-center justify-center p-4 bg-gray-900 border border-gray-800 rounded-lg transition-all duration-300 hover:border-blue-500 hover:-translate-y-1">
                <span className="text-4xl mb-2">{skill.icon}</span>
                <p className="font-medium text-white">{skill.name}</p>
                <div className="absolute inset-0 flex items-center justify-center bg-blue-600/90 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <p className="text-white font-bold text-sm">{skill.proficiency}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  </section>
);

const ProjectsSection = () => {
  const [activeTag, setActiveTag] = useState("All");
  const tags = useMemo(() => ["All", ...new Set(projectsData.flatMap(p => p.tags))], []);

  const filteredProjects = useMemo(() => {
    if (activeTag === "All") return projectsData;
    return projectsData.filter(p => p.tags.includes(activeTag));
  }, [activeTag]);

  return (
    <section id="projects" className="py-20 md:py-28 bg-gray-950">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white">Projects Showcase</h2>
          <p className="mt-3 max-w-2xl mx-auto text-gray-400">
            A selection of my work. Filter by technology to see what I can do.
          </p>
        </div>
        <div className="flex justify-center flex-wrap gap-2 mb-12">
          {tags.map(tag => (
            <button
              key={tag}
              onClick={() => setActiveTag(tag)}
              className={cn(
                "px-4 py-2 text-sm font-medium rounded-full transition-colors",
                activeTag === tag 
                  ? "bg-white text-black" 
                  : "bg-gray-800 text-gray-300 hover:bg-gray-700"
              )}
            >
              {tag}
            </button>
          ))}
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredProjects.map((project, index) => (
            <Card key={index} className="flex flex-col overflow-hidden group">
              <div className="overflow-hidden">
                <img src={project.imageUrl} alt={project.title} className="w-full h-48 object-cover transition-transform duration-300 group-hover:scale-105" />
              </div>
              <CardHeader>
                <CardTitle>{project.title}</CardTitle>
                <div className="flex flex-wrap gap-2 mt-3">
                  {project.tags.map(tag => <Badge key={tag}>{tag}</Badge>)}
                </div>
              </CardHeader>
              <CardContent className="flex-grow">
                <CardDescription>{project.description}</CardDescription>
              </CardContent>
              <div className="p-6 pt-0">
                <Button variant="link" className="p-0 h-auto text-blue-400" as="a" href={project.caseStudyUrl}>
                  View Case Study <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

const TimelineSection = () => (
  <section id="experience" className="py-20 md:py-28 bg-black">
    <div className="container mx-auto px-4 md:px-6">
      <div className="text-center mb-16">
        <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white">Education & Experience</h2>
        <p className="mt-3 max-w-2xl mx-auto text-gray-400">My professional and academic journey.</p>
      </div>
      <div className="relative max-w-3xl mx-auto">
        <div className="absolute left-1/2 top-0 h-full w-0.5 bg-gray-700 -translate-x-1/2"></div>
        {timelineData.map((item, index) => (
          <div key={index} className="relative mb-12 group">
            <div className={cn(
              "flex items-center",
              index % 2 === 0 ? "flex-row-reverse text-left md:text-right" : "text-left"
            )}>
              <div className="w-1/2 px-4">
                <div className={cn("md:flex items-center gap-4", index % 2 === 0 ? "md:flex-row-reverse" : "")}>
                  <div className="hidden md:block p-3 bg-gray-800 border-2 border-gray-700 rounded-full group-hover:border-blue-500 transition-colors">
                    {item.icon}
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">{item.date}</p>
                    <h3 className="text-lg font-semibold text-white mt-1">{item.title}</h3>
                    <p className="text-md font-medium text-gray-300">{item.company}</p>
                    <p className="text-sm text-gray-400 mt-2">{item.description}</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 bg-gray-600 rounded-full border-2 border-gray-800 group-hover:bg-blue-500 transition-colors"></div>
          </div>
        ))}
      </div>
    </div>
  </section>
);

const ContactSection = () => {
  const [status, setStatus] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("Sending...");
    
    // This is where you would integrate with a backend (e.g., FastAPI)
    // For this example, we'll simulate a network request.
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      // const response = await fetch('YOUR_FASTAPI_ENDPOINT', { method: 'POST', body: new FormData(e.target) });
      // if (response.ok) {
      //   setStatus("Message sent successfully!");
      //   e.target.reset();
      // } else {
      //   setStatus("Failed to send message. Please try again.");
      // }
      setStatus("Message sent successfully!");
      e.target.reset();
    } catch (error) {
      console.error("Contact form error:", error);
      setStatus("An error occurred. Please try again later.");
    }
  };

  return (
    <section id="contact" className="py-20 md:py-28 bg-gray-950">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white">Contact Me</h2>
          <p className="mt-3 max-w-2xl mx-auto text-gray-400">
            Have a question or want to work together? Feel free to reach out.
          </p>
        </div>
        <div className="max-w-xl mx-auto">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-2">Name</label>
                <input type="text" name="name" id="name" required className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">Email</label>
                <input type="email" name="email" id="email" required className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:ring-blue-500 focus:border-blue-500" />
              </div>
            </div>
            <div>
              <label htmlFor="message" className="block text-sm font-medium text-gray-300 mb-2">Message</label>
              <textarea name="message" id="message" rows="5" required className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:ring-blue-500 focus:border-blue-500"></textarea>
            </div>
            <div className="text-center">
              <Button type="submit" variant="default" className="px-8 py-3">
                Send Message
              </Button>
            </div>
            {status && <p className="text-center text-sm mt-4 text-gray-400">{status}</p>}
          </form>
        </div>
      </div>
    </section>
  );
};

const Footer = () => (
  <footer className="bg-black border-t border-gray-800">
    <div className="container mx-auto px-4 md:px-6 py-6 flex flex-col sm:flex-row justify-between items-center">
      <p className="text-sm text-gray-400">&copy; {new Date().getFullYear()} Nilisha Sharma. All Rights Reserved.</p>
      <div className="flex items-center space-x-4 mt-4 sm:mt-0">
        <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white"><Github className="h-5 w-5" /></a>
        <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white"><Linkedin className="h-5 w-5" /></a>
      </div>
    </div>
  </footer>
);

// Main App Component
const App = () => {
  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-black text-white font-sans antialiased">
        <Header />
        <main>
          <HeroSection />
          <AboutSection />
          <ProjectsSection />
          <TimelineSection />
          <ContactSection />
        </main>
        <Footer />
      </div>
    </ErrorBoundary>
  );
};

export default App;