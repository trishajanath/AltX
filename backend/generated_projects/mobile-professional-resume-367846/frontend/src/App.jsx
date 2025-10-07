import React, { useState, useEffect, useCallback } from 'react';

// Utility function for conditional class names (inspired by clsx and tailwind-merge)
const cn = (...classes) => classes.filter(Boolean).join(' ');

// --- SVG ICONS AS REACT COMPONENTS ---

const Briefcase = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={cn("h-6 w-6", className)}>
    <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
  </svg>
);

const LayoutGrid = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={cn("h-6 w-6", className)}>
    <rect x="3" y="3" width="7" height="7"></rect>
    <rect x="14" y="3" width="7" height="7"></rect>
    <rect x="14" y="14" width="7" height="7"></rect>
    <rect x="3" y="14" width="7" height="7"></rect>
  </svg>
);

const FileDown = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={cn("h-6 w-6", className)}>
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
    <polyline points="7 10 12 15 17 10"></polyline>
    <line x1="12" y1="15" x2="12" y2="3"></line>
  </svg>
);

const BarChart2 = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={cn("h-6 w-6", className)}>
    <line x1="18" y1="20" x2="18" y2="10"></line>
    <line x1="12" y1="20" x2="12" y2="4"></line>
    <line x1="6" y1="20" x2="6" y2="14"></line>
  </svg>
);

const Mail = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={cn("h-6 w-6", className)}>
    <rect width="20" height="16" x="2" y="4" rx="2"></rect>
    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
  </svg>
);

const MessageSquare = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={cn("h-6 w-6", className)}>
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
  </svg>
);

const ChevronLeft = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={cn("h-6 w-6", className)}>
    <polyline points="15 18 9 12 15 6"></polyline>
  </svg>
);

const ChevronRight = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={cn("h-6 w-6", className)}>
    <polyline points="9 18 15 12 9 6"></polyline>
  </svg>
);

// --- SHADCN/UI STYLE COMPONENTS ---

const buttonVariants = {
  default: "bg-slate-900 text-white hover:bg-slate-900/90 dark:bg-slate-50 dark:text-slate-900 dark:hover:bg-slate-50/90",
  destructive: "bg-red-500 text-white hover:bg-red-500/90",
  outline: "border border-slate-200 bg-transparent hover:bg-slate-100",
  secondary: "bg-slate-100 text-slate-900 hover:bg-slate-100/80",
  ghost: "hover:bg-slate-100",
  link: "text-slate-900 underline-offset-4 hover:underline",
};

const Button = ({ children, variant = "default", className = "", ...props }) => (
  <button
    className={cn(
      "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
      buttonVariants[variant],
      className
    )}
    {...props}
  >
    {children}
  </button>
);

const cardVariants = {
  default: "rounded-xl border bg-white text-slate-950 shadow-sm",
};

const Card = ({ children, className = "", variant = "default" }) => (
  <div className={cn(cardVariants[variant], className)}>{children}</div>
);

const CardHeader = ({ children, className = "" }) => (
  <div className={cn("flex flex-col space-y-1.5 p-6", className)}>{children}</div>
);

const CardTitle = ({ children, className = "" }) => (
  <h3 className={cn("text-2xl font-semibold leading-none tracking-tight", className)}>{children}</h3>
);

const CardDescription = ({ children, className = "" }) => (
  <p className={cn("text-sm text-slate-500", className)}>{children}</p>
);

const CardContent = ({ children, className = "" }) => (
  <div className={cn("p-6 pt-0", className)}>{children}</div>
);

const Tag = ({ children, className }) => (
    <span className={cn("inline-block rounded-full bg-sky-100 px-3 py-1 text-xs font-medium text-sky-800", className)}>
        {children}
    </span>
);

// --- ERROR BOUNDARY COMPONENT ---

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
        <div className="flex h-screen w-full flex-col items-center justify-center bg-slate-100">
          <h1 className="text-2xl font-bold text-red-600">Something went wrong.</h1>
          <p className="text-slate-600">Please refresh the page to try again.</p>
        </div>
      );
    }
    return this.props.children;
  }
}

// --- APPLICATION COMPONENTS ---

const Header = () => (
  <header className="sticky top-0 z-50 w-full border-b border-slate-200/40 bg-white/80 backdrop-blur-lg">
    <div className="container mx-auto flex h-16 items-center justify-between px-4 md:px-6">
      <a href="#" className="flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" className="h-6 w-6"><rect width="256" height="256" fill="none"></rect><path d="M32,80V56a8,8,0,0,1,8-8H216a8,8,0,0,1,8,8V80" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="16"></path><path d="M224,176v24a8,8,0,0,1-8,8H40a8,8,0,0,1-8-8V176" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="16"></path><rect x="32" y="80" width="192" height="96" rx="8" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="16"></rect></svg>
        <span className="font-bold text-lg">PortfolioGen</span>
      </a>
      <Button>Get Started</Button>
    </div>
  </header>
);

const HeroSection = () => (
  <section className="relative w-full overflow-hidden bg-gradient-to-br from-sky-50 via-slate-50 to-violet-100 py-20 md:py-32">
    <div className="container mx-auto px-4 md:px-6 text-center">
      <h1 className="text-4xl md:text-6xl font-extrabold tracking-tighter text-slate-900">
        Your Career, Reimagined.
      </h1>
      <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
        Create a stunning, mobile-first digital resume and portfolio that stands out.
        Dynamic, interactive, and effortlessly professional.
      </p>
      <div className="mt-8 flex justify-center gap-4">
        <Button size="lg" className="px-8 py-3 text-base">Create Your Portfolio</Button>
        <Button variant="outline" size="lg" className="px-8 py-3 text-base bg-white">View Demo</Button>
      </div>
    </div>
  </section>
);

const features = [
  {
    icon: <Briefcase />,
    title: "Interactive Work Timeline",
    description: "An engaging, expandable timeline to showcase your professional journey, letting recruiters dive deep into your achievements.",
  },
  {
    icon: <LayoutGrid />,
    title: "Dynamic Project Showcase",
    description: "Present your work in a filterable grid. Tag projects by technology to let visitors find what's relevant to them instantly.",
  },
  {
    icon: <FileDown />,
    title: "One-Click PDF Resume",
    description: "Bridge the gap between digital and traditional. Generate a print-optimized PDF resume from your portfolio data with a single click.",
  },
  {
    icon: <BarChart2 />,
    title: "Skills Visualization",
    description: "Clearly communicate your expertise with categorized skills and proficiency indicators, giving a quick and clear summary of your abilities.",
  },
  {
    icon: <Mail />,
    title: "Integrated Contact Form",
    description: "A clean, built-in contact form with spam protection makes it easy for potential employers and clients to get in touch.",
  },
  {
    icon: <MessageSquare />,
    title: "Testimonials Carousel",
    description: "Build trust and credibility by showcasing recommendations from colleagues, managers, and clients in a sleek, modern carousel.",
  },
];

const FeaturesSection = () => (
  <section className="py-16 md:py-24 bg-white">
    <div className="container mx-auto px-4 md:px-6">
      <div className="text-center">
        <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
          A Dynamic Toolkit for Professionals
        </h2>
        <p className="mt-3 max-w-2xl mx-auto text-lg text-slate-600">
          Everything you need to build a professional brand that gets noticed.
        </p>
      </div>
      <div className="mt-12 grid gap-8 md:grid-cols-2 lg:grid-cols-3">
        {features.map((feature, index) => (
          <Card key={index} className="flex flex-col">
            <CardHeader>
              <div className="bg-sky-100 text-sky-600 rounded-lg p-3 w-fit">
                {feature.icon}
              </div>
              <CardTitle className="mt-4 !text-xl">{feature.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>{feature.description}</CardDescription>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  </section>
);

const InteractiveDemoSection = () => {
  const projects = [
    { title: 'AI-Powered Sales Dashboard', tags: ['React', 'Data Viz'], img: 'bg-violet-300' },
    { title: 'E-commerce Platform API', tags: ['FastAPI', 'PostgreSQL'], img: 'bg-sky-300' },
    { title: 'Mobile Task Manager', tags: ['React Native'], img: 'bg-emerald-300' },
    { title: 'Cloud Deployment Pipeline', tags: ['AWS', 'CI/CD'], img: 'bg-amber-300' },
  ];
  const skills = [
    { name: 'Python', level: 95 },
    { name: 'JavaScript / TypeScript', level: 90 },
    { name: 'React', level: 90 },
    { name: 'FastAPI', level: 85 },
    { name: 'SQL / NoSQL', level: 80 },
  ];
  const experience = [
    { role: 'Senior Software Engineer', company: 'Innovate Inc.', date: '2020 - Present' },
    { role: 'Software Engineer', company: 'Tech Solutions', date: '2018 - 2020' },
    { role: 'Junior Developer', company: 'CodeBase', date: '2016 - 2018' },
  ];

  return (
    <section className="py-16 md:py-24 bg-slate-50">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
            See It in Action
          </h2>
          <p className="mt-3 max-w-2xl mx-auto text-lg text-slate-600">
            Explore a live preview of a portfolio built with PortfolioGen.
          </p>
        </div>
        <div className="mt-12">
          <div className="relative mx-auto border-slate-800 dark:border-slate-800 bg-slate-800 border-[8px] rounded-t-xl h-[auto] max-w-sm md:max-w-md">
            <div className="rounded-xl overflow-hidden bg-white">
              <div className="w-full h-[24px] bg-slate-800 flex items-center justify-start px-2 gap-1">
                <div className="w-2 h-2 rounded-full bg-slate-600"></div>
                <div className="w-2 h-2 rounded-full bg-slate-600"></div>
                <div className="w-2 h-2 rounded-full bg-slate-600"></div>
              </div>
              <div className="bg-white p-4 h-[500px] overflow-y-auto">
                {/* Profile Header */}
                <div className="text-center">
                  <img src="https://i.pravatar.cc/100?u=a042581f4e29026704d" alt="Profile" className="w-20 h-20 rounded-full mx-auto" />
                  <h3 className="text-xl font-bold mt-2">Alex Doe</h3>
                  <p className="text-sm text-slate-500">Senior Full-Stack Developer</p>
                </div>

                {/* Experience Timeline */}
                <div className="mt-6">
                  <h4 className="font-bold text-slate-800">Work Experience</h4>
                  <div className="relative mt-2 pl-6 border-l-2 border-slate-200">
                    {experience.map((job, index) => (
                      <div key={index} className="mb-4 last:mb-0">
                        <span className="absolute -left-[9px] top-1 flex h-4 w-4 items-center justify-center rounded-full bg-sky-500 ring-4 ring-white"></span>
                        <p className="font-semibold text-sm">{job.role}</p>
                        <p className="text-xs text-slate-500">{job.company} &bull; {job.date}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Skills Section */}
                <div className="mt-6">
                  <h4 className="font-bold text-slate-800">Skills</h4>
                  <div className="space-y-2 mt-2">
                    {skills.map(skill => (
                      <div key={skill.name}>
                        <p className="text-sm font-medium">{skill.name}</p>
                        <div className="w-full bg-slate-200 rounded-full h-1.5">
                          <div className="bg-sky-500 h-1.5 rounded-full" style={{ width: `${skill.level}%` }}></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Projects Section */}
                <div className="mt-6">
                  <h4 className="font-bold text-slate-800">Projects</h4>
                  <div className="flex gap-2 mt-2 overflow-x-auto pb-2">
                    <Button variant="secondary" size="sm" className="text-xs h-7 px-3 bg-sky-500 text-white">All</Button>
                    <Button variant="outline" size="sm" className="text-xs h-7 px-3">React</Button>
                    <Button variant="outline" size="sm" className="text-xs h-7 px-3">FastAPI</Button>
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {projects.map(p => (
                      <div key={p.title} className={`rounded-lg h-20 ${p.img} p-2 flex flex-col justify-end`}>
                        <p className="text-xs font-bold text-white drop-shadow-sm">{p.title}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

const testimonials = [
  {
    quote: "PortfolioGen transformed my job search. I got three interviews within a week of sending out my new portfolio link. The interactive timeline is a game-changer.",
    name: "Sarah L.",
    title: "UX Designer",
    avatar: "https://i.pravatar.cc/150?u=a042581f4e29026704e"
  },
  {
    quote: "As a freelance developer, showcasing my projects is crucial. The tag-based filtering lets potential clients see exactly the skills they're looking for. Highly recommended!",
    name: "Michael B.",
    title: "Freelance Web Developer",
    avatar: "https://i.pravatar.cc/150?u=a042581f4e29026704f"
  },
  {
    quote: "The one-click PDF generation is a lifesaver. I can maintain a beautiful online presence and still have a traditional resume ready for any ATS system.",
    name: "Jessica T.",
    title: "Data Scientist",
    avatar: "https://i.pravatar.cc/150?u=a042581f4e29026704a"
  }
];

const TestimonialsSection = () => {
  const [currentIndex, setCurrentIndex] = useState(0);

  const nextTestimonial = useCallback(() => {
    setCurrentIndex((prevIndex) => (prevIndex + 1) % testimonials.length);
  }, []);

  const prevTestimonial = () => {
    setCurrentIndex((prevIndex) => (prevIndex - 1 + testimonials.length) % testimonials.length);
  };

  useEffect(() => {
    const timer = setInterval(nextTestimonial, 5000);
    return () => clearInterval(timer);
  }, [nextTestimonial]);

  return (
    <section className="py-16 md:py-24 bg-white">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
            Trusted by Professionals
          </h2>
          <p className="mt-3 max-w-2xl mx-auto text-lg text-slate-600">
            Hear what our users have to say about building their careers with PortfolioGen.
          </p>
        </div>
        <div className="relative mt-12 max-w-3xl mx-auto">
          <div className="overflow-hidden">
            <div className="flex transition-transform duration-500 ease-in-out" style={{ transform: `translateX(-${currentIndex * 100}%)` }}>
              {testimonials.map((testimonial, index) => (
                <div key={index} className="w-full flex-shrink-0 px-2">
                  <Card className="text-center">
                    <CardContent className="p-8">
                      <p className="text-lg italic text-slate-700">"{testimonial.quote}"</p>
                      <div className="mt-6 flex items-center justify-center">
                        <img src={testimonial.avatar} alt={testimonial.name} className="w-12 h-12 rounded-full" />
                        <div className="ml-4 text-left">
                          <p className="font-semibold text-slate-900">{testimonial.name}</p>
                          <p className="text-slate-500">{testimonial.title}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>
          </div>
          <Button onClick={prevTestimonial} variant="ghost" className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 rounded-full h-10 w-10 p-0">
            <ChevronLeft />
          </Button>
          <Button onClick={nextTestimonial} variant="ghost" className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 rounded-full h-10 w-10 p-0">
            <ChevronRight />
          </Button>
        </div>
      </div>
    </section>
  );
};

const CTASection = () => (
  <section className="py-16 md:py-24 bg-slate-50">
    <div className="container mx-auto px-4 md:px-6">
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 rounded-xl p-8 md:p-12 text-center">
        <h2 className="text-3xl md:text-4xl font-bold text-white">
          Ready to Build Your Digital Resume?
        </h2>
        <p className="mt-3 max-w-2xl mx-auto text-lg text-slate-300">
          Join thousands of professionals who are taking control of their personal brand.
          Get started for free.
        </p>
        <div className="mt-8">
          <Button size="lg" className="bg-white text-slate-900 hover:bg-slate-200 px-8 py-3 text-base">
            Start Building Now
          </Button>
        </div>
      </div>
    </div>
  </section>
);

const Footer = () => (
  <footer className="bg-white border-t">
    <div className="container mx-auto px-4 md:px-6 py-6 text-center text-sm text-slate-500">
      <p>&copy; {new Date().getFullYear()} PortfolioGen. All rights reserved.</p>
    </div>
  </footer>
);

// --- MAIN APP COMPONENT ---

const App = () => {
  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-white font-sans antialiased">
        <Header />
        <main>
          <HeroSection />
          <FeaturesSection />
          <InteractiveDemoSection />
          <TestimonialsSection />
          <CTASection />
        </main>
        <Footer />
      </div>
    </ErrorBoundary>
  );
};

export default App;