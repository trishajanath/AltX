import React, { useState, Component } from 'react';
import { twMerge } from 'tailwind-merge';
import { clsx } from 'clsx';

// Lib utility function (cn)
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// shadcn/ui style variants
const buttonVariants = {
  default: "bg-blue-600 text-white hover:bg-blue-700",
  destructive: "bg-red-500 text-white hover:bg-red-600",
  outline: "border border-gray-300 bg-transparent hover:bg-gray-100 hover:text-gray-900",
  secondary: "bg-gray-200 text-gray-900 hover:bg-gray-300",
  ghost: "hover:bg-gray-100 hover:text-gray-900",
  link: "text-blue-600 underline-offset-4 hover:underline",
};

const cardVariants = {
  default: "bg-white rounded-xl border border-gray-200 shadow-sm",
  interactive: "bg-white rounded-xl border border-gray-200 shadow-sm transition-all hover:shadow-md hover:-translate-y-1",
};

// Error Boundary Component
class ErrorBoundary extends Component {
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
        <div className="flex flex-col items-center justify-center min-h-screen bg-red-50 text-red-700">
          <h1 className="text-2xl font-bold">Something went wrong.</h1>
          <p>Please refresh the page or try again later.</p>
        </div>
      );
    }
    return this.props.children;
  }
}


// Icon Components
const Menu = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
);

const ArrowRight = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-2 h-4 w-4"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
);

const CheckCircle = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
);

const Bell = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
);

const BarChart2 = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
);

const Clock = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
);

const Star = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="text-yellow-400">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
  </svg>
);

const Users = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
    <circle cx="9" cy="7" r="4"></circle>
    <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
  </svg>
);

// Reusable UI Components
const Button = ({ children, variant = "default", className = "", ...props }) => (
  <button
    className={cn(
      "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 disabled:opacity-50",
      buttonVariants[variant],
      className
    )}
    {...props}
  >
    {children}
  </button>
);

const Card = ({ children, className = "", variant = "default", ...props }) => (
  <div className={cn(cardVariants[variant], className)} {...props}>
    {children}
  </div>
);

// Page Section Components
const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white/80 backdrop-blur-md">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 md:px-6">
        <a href="#" className="flex items-center gap-2">
          <CheckCircle className="h-6 w-6 text-blue-600" />
          <span className="font-bold text-lg text-gray-800">AssignTrack</span>
        </a>
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
          <a href="#features" className="text-gray-600 hover:text-gray-900 transition-colors">Features</a>
          <a href="#timeline" className="text-gray-600 hover:text-gray-900 transition-colors">Timeline</a>
          <a href="#testimonials" className="text-gray-600 hover:text-gray-900 transition-colors">Testimonials</a>
        </nav>
        <div className="flex items-center gap-4">
          <Button variant="ghost" className="hidden md:inline-flex">Log In</Button>
          <Button>Download App</Button>
          <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="md:hidden">
            <Menu />
          </button>
        </div>
      </div>
      {isMenuOpen && (
        <div className="md:hidden bg-white border-t border-gray-200">
          <nav className="flex flex-col items-center gap-4 p-4 text-sm font-medium">
            <a href="#features" className="text-gray-600 hover:text-gray-900">Features</a>
            <a href="#timeline" className="text-gray-600 hover:text-gray-900">Timeline</a>
            <a href="#testimonials" className="text-gray-600 hover:text-gray-900">Testimonials</a>
            <Button variant="outline" className="w-full">Log In</Button>
          </nav>
        </div>
      )}
    </header>
  );
};

const Hero = () => (
  <section className="relative w-full pt-20 pb-12 md:pt-32 md:pb-24 lg:pt-40 lg:pb-32">
    <div className="absolute inset-0 -z-10 bg-gradient-to-br from-blue-50 via-white to-indigo-50"></div>
    <div className="container mx-auto px-4 md:px-6 text-center">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl md:text-6xl">
          Never miss a deadline again.
        </h1>
        <p className="mt-6 text-lg text-gray-600">
          AssignTrack is a minimalist mobile app designed to help you effortlessly manage your academic workload. Reduce stress and focus on what matters: your studies.
        </p>
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button className="w-full sm:w-auto text-base px-8 py-3">
            Get Started for Free <ArrowRight />
          </Button>
          <Button variant="outline" className="w-full sm:w-auto text-base px-8 py-3">
            Learn More
          </Button>
        </div>
        <div className="mt-12 flex justify-center items-center gap-4">
            <div className="flex -space-x-2">
                <img className="inline-block h-10 w-10 rounded-full ring-2 ring-white" src="https://randomuser.me/api/portraits/women/79.jpg" alt="User"/>
                <img className="inline-block h-10 w-10 rounded-full ring-2 ring-white" src="https://randomuser.me/api/portraits/men/32.jpg" alt="User"/>
                <img className="inline-block h-10 w-10 rounded-full ring-2 ring-white" src="https://randomuser.me/api/portraits/women/50.jpg" alt="User"/>
            </div>
            <div>
                <div className="flex items-center">
                    <Star /><Star /><Star /><Star /><Star />
                </div>
                <p className="text-sm text-gray-500">Loved by 10,000+ students</p>
            </div>
        </div>
      </div>
    </div>
  </section>
);

const Features = () => {
  const featuresData = [
    {
      icon: <Clock />,
      name: 'Smart Due Date Parsing',
      description: "Type 'Essay due next friday' and the app sets the deadline to the upcoming Friday at 11:59 PM. Simple and fast.",
    },
    {
      icon: <Bell />,
      name: 'Configurable Push Reminders',
      description: 'Set multiple, custom reminders for each assignment (e.g., 1 week before, 24 hours before) to stay on track.',
    },
    {
      icon: <CheckCircle />,
      name: 'Sub-task Checklists',
      description: "Break down large projects like 'Term Paper' into manageable steps like 'Research', 'Outline', and 'Proofread'.",
    },
    {
      icon: <BarChart2 />,
      name: 'Completion Analytics',
      description: 'Visualize your on-time completion rate per course and track streaks to build better study habits.',
    },
  ];

  return (
    <section id="features" className="py-16 md:py-24 bg-gray-50">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Everything you need to succeed.
          </h2>
          <p className="mt-4 text-lg text-gray-600">
            AssignTrack's features are designed with one goal: to make your student life simpler and more organized.
          </p>
        </div>
        <div className="mt-12 grid gap-8 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
          {featuresData.map((feature) => (
            <Card key={feature.name} variant="interactive">
              <div className="p-6">
                <div className="flex items-center justify-center h-12 w-12 rounded-lg bg-blue-100 text-blue-600">
                  {feature.icon}
                </div>
                <h3 className="mt-6 text-lg font-semibold text-gray-900">{feature.name}</h3>
                <p className="mt-2 text-sm text-gray-600">{feature.description}</p>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

const DesignShowcase = () => {
  const courses = [
    { id: 'math', name: 'MATH-101', color: 'blue', textColor: 'text-blue-800', bgColor: 'bg-blue-100', borderColor: 'border-blue-500' },
    { id: 'hist', name: 'HIST-203', color: 'red', textColor: 'text-red-800', bgColor: 'bg-red-100', borderColor: 'border-red-500' },
    { id: 'biol', name: 'BIOL-310', color: 'green', textColor: 'text-green-800', bgColor: 'bg-green-100', borderColor: 'border-green-500' },
    { id: 'engl', name: 'ENGL-110', color: 'yellow', textColor: 'text-yellow-800', bgColor: 'bg-yellow-100', borderColor: 'border-yellow-500' },
  ];

  const assignments = [
    { title: 'Problem Set 3', courseId: 'math', due: 'Today, 5:00 PM' },
    { title: 'Photosynthesis Lab Report', courseId: 'biol', due: 'Tomorrow, 11:59 PM' },
    { title: 'Civil War Essay Outline', courseId: 'hist', due: 'Wednesday, 9:00 AM' },
    { title: 'Poetry Analysis Paper', courseId: 'engl', due: 'Friday, 5:00 PM' },
    { title: 'Midterm Exam', courseId: 'math', due: 'Next Monday, 10:00 AM' },
  ];

  const [activeCourse, setActiveCourse] = useState(null);

  const getCourse = (courseId) => courses.find(c => c.id === courseId);

  return (
    <section id="timeline" className="py-16 md:py-24 bg-white">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Visualize Your Workload
          </h2>
          <p className="mt-4 text-lg text-gray-600">
            Our color-coded timeline gives you an at-a-glance overview of your upcoming assignments, helping you plan your schedule effectively.
          </p>
        </div>
        <div className="mt-12 max-w-4xl mx-auto">
          <Card className="overflow-hidden">
            <div className="p-4 bg-gray-50 border-b">
              <h3 className="font-semibold text-gray-800">Course Management</h3>
              <p className="text-sm text-gray-500">Click a course to filter the timeline.</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {courses.map(course => (
                  <button
                    key={course.id}
                    onClick={() => setActiveCourse(activeCourse === course.id ? null : course.id)}
                    className={cn(
                      'px-3 py-1 text-xs font-medium rounded-full transition-all',
                      course.bgColor,
                      course.textColor,
                      activeCourse === course.id ? `ring-2 ring-offset-1 ${course.borderColor}` : 'hover:opacity-80'
                    )}
                  >
                    {course.name}
                  </button>
                ))}
              </div>
            </div>
            <div className="p-4 md:p-6">
              <h3 className="font-semibold text-gray-800 mb-4">Upcoming Assignment Timeline</h3>
              <div className="space-y-4">
                {assignments.map((assignment, index) => {
                  const course = getCourse(assignment.courseId);
                  const isFiltered = activeCourse && activeCourse !== assignment.courseId;
                  return (
                    <div
                      key={index}
                      className={cn(
                        'flex items-start gap-4 p-3 rounded-lg transition-opacity duration-300',
                        isFiltered ? 'opacity-30' : 'opacity-100',
                        course.bgColor
                      )}
                    >
                      <div className={cn('w-1.5 h-12 rounded-full', `bg-${course.color}-500`)}></div>
                      <div className="flex-1">
                        <p className={cn('font-semibold', course.textColor)}>{assignment.title}</p>
                        <p className="text-sm text-gray-500">{assignment.due}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
};

const Testimonials = () => {
  const testimonialsData = [
    {
      quote: "AssignTrack completely changed how I manage my coursework. The timeline view is a lifesaver, and I haven't missed a deadline since I started using it.",
      name: "Sarah J.",
      school: "UCLA, Computer Science",
    },
    {
      quote: "As someone who struggles with organization, this app is a game-changer. Breaking down big projects into sub-tasks makes them so much less daunting.",
      name: "Michael B.",
      school: "NYU, English Literature",
    },
    {
      quote: "The simplicity is its greatest strength. It does exactly what I need without any clutter. The smart due date parsing is pure magic!",
      name: "Emily C.",
      school: "University of Texas, Biology",
    },
  ];

  return (
    <section id="testimonials" className="py-16 md:py-24 bg-gray-50">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Trusted by students everywhere
          </h2>
          <p className="mt-4 text-lg text-gray-600">
            See what fellow students are saying about how AssignTrack has improved their academic life.
          </p>
        </div>
        <div className="mt-12 grid gap-8 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {testimonialsData.map((testimonial) => (
            <Card key={testimonial.name}>
              <div className="p-6 flex flex-col h-full">
                <div className="flex-grow">
                  <p className="text-gray-700">"{testimonial.quote}"</p>
                </div>
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center">
                      <Star /><Star /><Star /><Star /><Star />
                    </div>
                  </div>
                  <p className="mt-2 font-semibold text-gray-900">{testimonial.name}</p>
                  <p className="text-sm text-gray-500">{testimonial.school}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

const CTA = () => (
  <section className="py-16 md:py-24 bg-white">
    <div className="container mx-auto px-4 md:px-6">
      <div className="bg-blue-600 rounded-lg p-8 md:p-12 text-center">
        <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Ready to take control of your assignments?
        </h2>
        <p className="mt-4 text-lg text-blue-100 max-w-2xl mx-auto">
          Download AssignTrack today and transform your study habits. It's free to get started and available on iOS and Android.
        </p>
        <div className="mt-8">
          <Button variant="secondary" className="text-base px-8 py-3 bg-white text-blue-600 hover:bg-gray-100">
            Download Now
          </Button>
        </div>
      </div>
    </div>
  </section>
);

const Footer = () => (
  <footer className="bg-gray-100 border-t border-gray-200">
    <div className="container mx-auto px-4 md:px-6 py-8 flex flex-col sm:flex-row justify-between items-center">
      <p className="text-sm text-gray-500">
        &copy; {new Date().getFullYear()} AssignTrack. All rights reserved.
      </p>
      <div className="flex gap-4 mt-4 sm:mt-0">
        <a href="#" className="text-gray-500 hover:text-gray-800">Privacy Policy</a>
        <a href="#" className="text-gray-500 hover:text-gray-800">Terms of Service</a>
      </div>
    </div>
  </footer>
);

// Main App Component
const App = () => {
  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-white text-gray-800 font-sans antialiased">
        <Header />
        <main>
          <Hero />
          <Features />
          <DesignShowcase />
          <Testimonials />
          <CTA />
        </main>
        <Footer />
      </div>
    </ErrorBoundary>
  );
};

export default App;