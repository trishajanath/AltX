import React from 'react';

// --- Lucide Icon Components (VALID icons only) ---
const Star = ({ className = "w-6 h-6" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
  </svg>
);

const Users = ({ className = "w-6 h-6" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
    <circle cx="9" cy="7" r="4"></circle>
    <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
  </svg>
);

const Zap = ({ className = "w-6 h-6" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
  </svg>
);

// Fix: Ensure all components are properly defined
window.Zap = Zap; // Temporary debug fix

const MapPin = ({ className = "w-6 h-6" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"></path>
    <circle cx="12" cy="10" r="3"></circle>
  </svg>
);

const Package = ({ className = "w-6 h-6" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M16.5 9.4a4.5 4.5 0 1 1-9 0 4.5 4.5 0 0 1 9 0Z"></path>
    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"></path>
    <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
    <line x1="12" y1="22.08" x2="12" y2="12"></line>
  </svg>
);

const CheckCircle = ({ className = "w-6 h-6" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
    <polyline points="22 4 12 14.01 9 11.01"></polyline>
  </svg>
);

const ArrowRight = ({ className = "w-6 h-6" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <line x1="5" y1="12" x2="19" y2="12"></line>
    <polyline points="12 5 19 12 12 19"></polyline>
  </svg>
);

const Twitter = ({ className = "w-6 h-6" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M22 4s-.7 2.1-2 3.4c1.6 1.4 3.3 4.9 3.3 4.9-6.1 1.2-12.1 1.2-12.1 1.2s-2.8-.7-4.4-2.1c0 0-4.2 2.8-7.3 2.8 0 0 3.3-1.4 4.7-4.2 0 0-1.4-2.8-2.8-4.2 0 0 4.2 1.4 5.6 1.4 0 0-1.4-4.2-6.3-7.3 0 0 4.2 2.1 7.3 2.1 0 0 2.8-2.1 5.6-2.1 0 0 1.4 2.8 1.4 2.8z"></path>
  </svg>
);

const Facebook = ({ className = "w-6 h-6" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path>
  </svg>
);

const Instagram = ({ className = "w-6 h-6" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
    <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
  </svg>
);

// --- Inline Button Component ---
const Button = ({ children, className = '', as = 'button', ...props }) => {
  const Tag = as;
  return (
    <Tag
      className={`inline-flex items-center justify-center gap-2 px-6 py-3 font-semibold text-white bg-blue-600 rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 ${className}`}
      {...props}
    >
      {children}
    </Tag>
  );
};

// --- Main App Component ---
export default function App() {
  const features = [
    {
      icon: <Package className="w-8 h-8 text-blue-600" />,
      name: "The 'Yes' Proposal Creator",
      description: "Draft detailed proposals with rich-text, required resources, and success metrics to formalize ideas before commitment.",
    },
    {
      icon: <Users className="w-8 h-8 text-blue-600" />,
      name: "Multi-Stakeholder Commitment Board",
      description: "Invite stakeholders to signal commitment with a timestamped, digital 'Yes' signature, creating an immutable record of agreement.",
    },
    {
      icon: <MapPin className="w-8 h-8 text-blue-600" />,
      name: "Actionable Milestone Tracker",
      description: "Automatically generate a Kanban board from every 'Yes' to break down work into trackable milestones with assignees and due dates.",
    },
    {
      icon: <Zap className="w-8 h-8 text-blue-600" />,
      name: "Accelerated Decision Making",
      description: "Eliminate ambiguity and endless discussion loops. Move from consensus to committed action in record time.",
    },
  ];

  const proposals = [
    {
      title: "Q3 Mobile App Redesign",
      status: "In Progress",
      progress: 75,
      image: "https://images.unsplash.com/300x200/?mobile",
      team: [1, 2, 3],
    },
    {
      title: "Launch 'Project Phoenix' API",
      status: "In Progress",
      progress: 40,
      image: "https://images.unsplash.com/300x200/?code",
      team: [4, 5, 1],
    },
    {
      title: "New Employee Onboarding Workflow",
      status: "Seeking Commitment",
      progress: 0,
      image: "https://images.unsplash.com/300x200/?team",
      team: [6, 7],
    },
    {
      title: "2024 Content Marketing Strategy",
      status: "Committed",
      progress: 10,
      image: "https://images.unsplash.com/300x200/?marketing",
      team: [8, 9, 2],
    },
    {
      title: "Customer Feedback Portal",
      status: "Completed",
      progress: 100,
      image: "https://images.unsplash.com/300x200/?analytics",
      team: [1, 5, 8],
    },
    {
      title: "Upgrade to Cloud Infrastructure",
      status: "In Progress",
      progress: 60,
      image: "https://images.unsplash.com/300x200/?cloud",
      team: [4, 5, 10],
    },
    {
      title: "A/B Testing Framework",
      status: "Seeking Commitment",
      progress: 0,
      image: "https://images.unsplash.com/300x200/?data",
      team: [1, 4],
    },
    {
      title: "Annual Team Offsite Planning",
      status: "Committed",
      progress: 25,
      image: "https://images.unsplash.com/300x200/?travel",
      team: [6, 7, 9],
    },
  ];

  return (
    <div className="bg-gray-50 text-gray-800 font-sans">
      {/* Header */}
      <header className="absolute top-0 left-0 right-0 z-10 bg-transparent text-white">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="text-2xl font-bold tracking-wider flex items-center gap-2">
            <CheckCircle className="w-7 h-7 text-blue-400" />
            yes
          </div>
          <nav className="hidden md:flex items-center space-x-6">
            <a href="#" className="hover:text-blue-300 transition-colors">Features</a>
            <a href="#" className="hover:text-blue-300 transition-colors">Pricing</a>
            <a href="#" className="hover:text-blue-300 transition-colors">Company</a>
          </nav>
          <Button as="a" href="#" className="hidden md:inline-flex px-5 py-2 text-sm">
            Sign In
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <main>
        <section className="relative bg-gradient-to-br from-gray-900 via-slate-800 to-gray-900 text-white pt-32 pb-20">
          <div className="container mx-auto px-6 text-center">
            <h1 className="text-4xl md:text-6xl font-extrabold leading-tight mb-4">
              From Idea to Action, Together.
            </h1>
            <p className="text-lg md:text-xl text-gray-300 max-w-3xl mx-auto mb-8">
              yes is the collaborative platform that turns proposals into committed action. Align your team, secure commitments, and track progress from a single source of truth.
            </p>
            <div className="flex justify-center items-center gap-4">
              <Button as="a" href="#" className="text-lg">
                Create Your First Proposal <ArrowRight className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section id="features" className="py-20 bg-white">
          <div className="container mx-auto px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900">A Better Way to Say 'Yes'</h2>
              <p className="text-lg text-gray-600 mt-2 max-w-2xl mx-auto">
                Our platform is built on three core pillars to ensure every commitment is clear, accountable, and actionable.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {features.map((feature, index) => (
                <div key={index} className="bg-gray-50 p-8 rounded-xl border border-gray-200 hover:shadow-lg transition-shadow">
                  <div className="flex items-center justify-center h-16 w-16 rounded-full bg-blue-100 mb-5">
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-bold mb-2">{feature.name}</h3>
                  <p className="text-gray-600">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="bg-slate-100 py-20">
          <div className="container mx-auto px-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
              <div className="p-4">
                <p className="text-5xl font-extrabold text-blue-600">92%</p>
                <p className="text-lg text-gray-700 mt-2">Faster Team Alignment</p>
              </div>
              <div className="p-4">
                <p className="text-5xl font-extrabold text-blue-600">3x</p>
                <p className="text-lg text-gray-700 mt-2">Increase in Project Velocity</p>
              </div>
              <div className="p-4">
                <p className="text-5xl font-extrabold text-blue-600">10,000+</p>
                <p className="text-lg text-gray-700 mt-2">Teams Building with 'Yes'</p>
              </div>
            </div>
          </div>
        </section>

        {/* Main Content Area (Proposals Grid) */}
        <section id="proposals" className="py-20 bg-white">
          <div className="container mx-auto px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900">Active Commitments</h2>
              <p className="text-lg text-gray-600 mt-2 max-w-2xl mx-auto">
                See what high-impact teams are building right now.
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
              {proposals.map((proposal, index) => (
                <div key={index} className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden flex flex-col group transition-all hover:shadow-xl hover:-translate-y-1">
                  <img src={proposal.image} alt={proposal.title} className="w-full h-40 object-cover" />
                  <div className="p-5 flex flex-col flex-grow">
                    <div className="flex-grow">
                      <span className={`inline-block px-2 py-1 text-xs font-semibold rounded-full mb-2 ${
                        proposal.status === 'In Progress' ? 'bg-yellow-100 text-yellow-800' :
                        proposal.status === 'Seeking Commitment' ? 'bg-blue-100 text-blue-800' :
                        proposal.status === 'Committed' ? 'bg-indigo-100 text-indigo-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {proposal.status}
                      </span>
                      <h3 className="text-lg font-bold text-gray-900">{proposal.title}</h3>
                    </div>
                    <div className="mt-4">
                      <p className="text-sm text-gray-500 mb-2">Committed Stakeholders:</p>
                      <div className="flex items-center">
                        {proposal.team.map(id => (
                          <img key={id} src={`https://i.pravatar.cc/40?u=${id}`} alt="avatar" className="w-8 h-8 rounded-full border-2 border-white -ml-2" />
                        ))}
                      </div>
                    </div>
                    <div className="mt-4">
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${proposal.progress}%` }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300">
        <div className="container mx-auto px-6 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div>
              <h4 className="font-bold text-white mb-4">Product</h4>
              <ul>
                <li className="mb-2"><a href="#" className="hover:text-white">Features</a></li>
                <li className="mb-2"><a href="#" className="hover:text-white">Integrations</a></li>
                <li className="mb-2"><a href="#" className="hover:text-white">Pricing</a></li>
                <li className="mb-2"><a href="#" className="hover:text-white">Changelog</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Company</h4>
              <ul>
                <li className="mb-2"><a href="#" className="hover:text-white">About Us</a></li>
                <li className="mb-2"><a href="#" className="hover:text-white">Careers</a></li>
                <li className="mb-2"><a href="#" className="hover:text-white">Blog</a></li>
                <li className="mb-2"><a href="#" className="hover:text-white">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Resources</h4>
              <ul>
                <li className="mb-2"><a href="#" className="hover:text-white">Help Center</a></li>
                <li className="mb-2"><a href="#" className="hover:text-white">API Docs</a></li>
                <li className="mb-2"><a href="#" className="hover:text-white">System Status</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Legal</h4>
              <ul>
                <li className="mb-2"><a href="#" className="hover:text-white">Terms of Service</a></li>
                <li className="mb-2"><a href="#" className="hover:text-white">Privacy Policy</a></li>
              </ul>
            </div>
          </div>
          <div className="mt-12 border-t border-gray-700 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-400">&copy; {new Date().getFullYear()} Yes Inc. All rights reserved.</p>
            <div className="flex space-x-4 mt-4 md:mt-0">
              <a href="#" className="text-gray-400 hover:text-white"><Twitter /></a>
              <a href="#" className="text-gray-400 hover:text-white"><Facebook /></a>
              <a href="#" className="text-gray-400 hover:text-white"><Instagram /></a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}