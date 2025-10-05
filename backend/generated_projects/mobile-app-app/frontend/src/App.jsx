import React from 'react';
import { Star, Users, Zap, MapPin, Clock, Package, ArrowRight, CheckCircle, Twitter, Facebook, Instagram } from 'lucide-react';

// Reusable Inline Button Component
const Button = ({ children, className = '', icon: Icon, ...props }) => {
  return (
    <button
      className={`inline-flex items-center justify-center px-6 py-3 font-semibold text-white bg-blue-600 rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-300 ${className}`}
      {...props}
    >
      {children}
      {Icon && <Icon className="w-5 h-5 ml-2" />}
    </button>
  );
};

// Feature Card Component
const FeatureCard = ({ icon: Icon, title, description }) => (
  <div className="p-6 bg-white rounded-xl shadow-lg flex flex-col items-start">
    <div className="flex items-center justify-center w-12 h-12 mb-4 text-blue-600 bg-blue-100 rounded-full">
      <Icon className="w-6 h-6" />
    </div>
    <h3 className="mb-2 text-xl font-bold text-gray-900">{title}</h3>
    <p className="text-gray-600">{description}</p>
  </div>
);

// Stat Item Component
const StatItem = ({ icon: Icon, value, label }) => (
  <div className="text-center">
    <Icon className="w-10 h-10 mx-auto mb-2 text-blue-500" />
    <p className="text-4xl font-bold text-gray-900">{value}</p>
    <p className="text-lg text-gray-600">{label}</p>
  </div>
);

// Assignment Card Component
const AssignmentCard = ({ title, course, dueDate, priority, imageUrl }) => {
  const priorityStyles = {
    'Do First': 'border-red-500',
    'Schedule': 'border-yellow-500',
    'Delegate': 'border-blue-500',
    'Eliminate': 'border-gray-400',
  };
  const priorityBgStyles = {
    'Do First': 'bg-red-100 text-red-800',
    'Schedule': 'bg-yellow-100 text-yellow-800',
    'Delegate': 'bg-blue-100 text-blue-800',
    'Eliminate': 'bg-gray-100 text-gray-800',
  };

  return (
    <div className={`bg-white rounded-lg shadow-md overflow-hidden border-l-4 ${priorityStyles[priority] || 'border-gray-300'}`}>
      <img src={imageUrl} alt={title} className="object-cover w-full h-32" />
      <div className="p-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-lg font-semibold text-gray-800">{title}</h4>
          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${priorityBgStyles[priority] || 'bg-gray-200'}`}>
            {priority}
          </span>
        </div>
        <p className="text-sm text-gray-600">{course}</p>
        <p className="mt-2 text-sm font-medium text-gray-700">Due: {dueDate}</p>
      </div>
    </div>
  );
};


export default function App() {
  const features = [
    {
      icon: Zap,
      title: 'Syllabus Scan & Go',
      description: "Upload your syllabus, and our AI instantly populates your schedule with every assignment and due date. Say goodbye to manual entry.",
    },
    {
      icon: Clock,
      title: 'Smart Deadline Reminders',
      description: "Receive intelligent push notifications: 7-day warnings for big projects, 24-hour heads-ups, and 'Due Today' summaries to keep you on track.",
    },
    {
      icon: CheckCircle,
      title: 'Prioritize Like a Pro',
      description: "Use the integrated Eisenhower Matrix to sort tasks by urgency and importance. Visually drag and drop assignments to focus your energy effectively.",
    },
    {
      icon: MapPin,
      title: 'Centralized Dashboard',
      description: "View all your courses, upcoming deadlines, and progress in a single, clean dashboard. Clarity brings calm and control.",
    },
  ];

  const sampleAssignments = [
    { title: 'Midterm Essay', course: 'History 101', dueDate: 'Oct 25, 2023', priority: 'Do First', topic: 'history' },
    { title: 'Problem Set 5', course: 'Calculus II', dueDate: 'Oct 18, 2023', priority: 'Do First', topic: 'math' },
    { title: 'Lab Report #3', course: 'Chemistry Lab', dueDate: 'Nov 2, 2023', priority: 'Schedule', topic: 'science' },
    { title: 'Final Project Proposal', course: 'Computer Science', dueDate: 'Nov 15, 2023', priority: 'Schedule', topic: 'code' },
    { title: 'Weekly Reading Response', course: 'Literature Seminar', dueDate: 'Oct 19, 2023', priority: 'Delegate', topic: 'books' },
    { title: 'Character Sketches', course: 'Creative Writing', dueDate: 'Oct 30, 2023', priority: 'Schedule', topic: 'writing' },
    { title: 'Market Analysis', course: 'Business 101', dueDate: 'Nov 8, 2023', priority: 'Schedule', topic: 'business' },
    { title: 'Peer Review Draft', course: 'Academic Writing', dueDate: 'Oct 22, 2023', priority: 'Delegate', topic: 'teamwork' },
  ];

  return (
    <div className="bg-gray-50 font-sans">
      {/* Hero Section */}
      <header className="relative text-white">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600 to-indigo-800"></div>
        <div className="relative max-w-6xl px-4 py-24 mx-auto text-center sm:py-32">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">
            Ace Your Semester, Stress-Free.
          </h1>
          <p className="max-w-2xl mx-auto mt-6 text-lg text-blue-100">
            Meet your new academic superpower. Our app intelligently organizes your assignments, tracks deadlines, and helps you prioritize what truly matters. Stop juggling, start achieving.
          </p>
          <div className="mt-10">
            <Button className="px-8 py-4 text-lg" icon={ArrowRight}>
              Download the App
            </Button>
          </div>
        </div>
      </header>

      <main>
        {/* Features Section */}
        <section id="features" className="py-16 bg-white sm:py-24">
          <div className="max-w-6xl px-4 mx-auto">
            <div className="text-center">
              <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
                Everything You Need to Succeed
              </h2>
              <p className="max-w-2xl mx-auto mt-4 text-xl text-gray-600">
                Powerful features designed to save you time and reduce anxiety.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-8 mt-12 md:grid-cols-2 lg:grid-cols-2">
              {features.map((feature, index) => (
                <FeatureCard key={index} {...feature} />
              ))}
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section id="stats" className="py-16 bg-gray-50 sm:py-24">
          <div className="max-w-6xl px-4 mx-auto">
            <div className="grid grid-cols-1 gap-8 text-center md:grid-cols-3">
              <StatItem icon={Users} value="50,000+" label="Students Empowered" />
              <StatItem icon={Package} value="1.2 Million" label="Assignments Managed" />
              <StatItem icon={Star} value="4.8 / 5" label="Average App Store Rating" />
            </div>
          </div>
        </section>

        {/* Main Content Area - App Showcase */}
        <section id="showcase" className="py-16 bg-white sm:py-24">
          <div className="max-w-6xl px-4 mx-auto">
            <div className="text-center">
              <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
                Your Command Center for Success
              </h2>
              <p className="max-w-2xl mx-auto mt-4 text-xl text-gray-600">
                Visualize your workload with clear, actionable cards for every task.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-6 mt-12 sm:grid-cols-2 lg:grid-cols-4">
              {sampleAssignments.map((assignment, index) => (
                <AssignmentCard 
                  key={index} 
                  {...assignment} 
                  imageUrl={`https://images.unsplash.com/300x200/?${assignment.topic},study&random=${index}`}
                />
              ))}
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300">
        <div className="max-w-6xl px-4 py-12 mx-auto">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            <div>
              <h3 className="text-sm font-semibold tracking-wider text-white uppercase">Solutions</h3>
              <ul className="mt-4 space-y-4">
                <li><a href="#" className="hover:text-white">Syllabus Scan</a></li>
                <li><a href="#" className="hover:text-white">Prioritization</a></li>
                <li><a href="#" className="hover:text-white">Reminders</a></li>
                <li><a href="#" className="hover:text-white">Analytics</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold tracking-wider text-white uppercase">Support</h3>
              <ul className="mt-4 space-y-4">
                <li><a href="#" className="hover:text-white">Pricing</a></li>
                <li><a href="#" className="hover:text-white">Documentation</a></li>
                <li><a href="#" className="hover:text-white">Guides</a></li>
                <li><a href="#" className="hover:text-white">API Status</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold tracking-wider text-white uppercase">Company</h3>
              <ul className="mt-4 space-y-4">
                <li><a href="#" className="hover:text-white">About</a></li>
                <li><a href="#" className="hover:text-white">Blog</a></li>
                <li><a href="#" className="hover:text-white">Jobs</a></li>
                <li><a href="#" className="hover:text-white">Press</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold tracking-wider text-white uppercase">Legal</h3>
              <ul className="mt-4 space-y-4">
                <li><a href="#" className="hover:text-white">Claim</a></li>
                <li><a href="#" className="hover:text-white">Privacy</a></li>
                <li><a href="#" className="hover:text-white">Terms</a></li>
              </ul>
            </div>
          </div>
          <div className="pt-8 mt-8 border-t border-gray-800 md:flex md:items-center md:justify-between">
            <div className="flex space-x-6 md:order-2">
              <a href="#" className="text-gray-400 hover:text-white">
                <Twitter className="w-6 h-6" />
              </a>
              <a href="#" className="text-gray-400 hover:text-white">
                <Facebook className="w-6 h-6" />
              </a>
              <a href="#" className="text-gray-400 hover:text-white">
                <Instagram className="w-6 h-6" />
              </a>
            </div>
            <p className="mt-8 text-base text-gray-400 md:mt-0 md:order-1">
              &copy; 2023 Student Assignment Manager. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}