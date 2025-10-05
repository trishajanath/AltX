import React from 'react';

// --- VALID LUCIDE ICON COMPONENTS ---
// As per the instructions, only these specific icons are used.
// They are defined as inline functional components.

const Star = ({ className = 'w-6 h-6' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
  </svg>
);

const Users = ({ className = 'w-6 h-6' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
  </svg>
);

const Zap = ({ className = 'w-6 h-6' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
  </svg>
);

const MapPin = ({ className = 'w-6 h-6' }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
        <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"></path><circle cx="12" cy="10" r="3"></circle>
    </svg>
);

const Clock = ({ className = 'w-6 h-6' }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
        <circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>
    </svg>
);

const Package = ({ className = 'w-6 h-6' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <line x1="16.5" y1="9.4" x2="7.5" y2="4.21"></line><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line>
  </svg>
);

const Heart = ({ className = 'w-6 h-6' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
  </svg>
);

const ArrowRight = ({ className = 'w-6 h-6' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline>
  </svg>
);

const CheckCircle = ({ className = 'w-6 h-6' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>
  </svg>
);

const Twitter = ({ className = 'w-6 h-6' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M22 4s-.7 2.1-2 3.4c1.6 1.4 3.3 4.9 3.3 4.9s-5.2-.1-7.1-.2c-1.4 5.7-7.2 6.3-7.2 6.3s-4.9-1.7-5.2-3.3c-1.2 1.5-2.6 2.3-2.6 2.3s2.1-1.2 2.1-3.2c0 0-5.1-1.3-5.4-5.9c0 0 1.5.9 3.3.9s-3.3-2.1-3.3-5.6c0 0 2.3 1.3 3.3 1.3s-2.1-6.1 2.6-6.1c2.6 0 5.5 4.1 5.5 4.1s3.3-1.3 3.3-1.3c-.6 1.3-1.3 2.6-1.3 2.6s2.1-.6 2.1-.6z"></path>
  </svg>
);

const Facebook = ({ className = 'w-6 h-6' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path>
  </svg>
);

const Instagram = ({ className = 'w-6 h-6' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="18.5" y1="5.5" x2="18.51" y2="5.5"></line>
  </svg>
);


// --- INLINE BUTTON COMPONENT ---
const Button = ({ children, className }) => (
  <button className={`inline-flex items-center justify-center gap-2 px-6 py-3 font-semibold text-white bg-blue-600 rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 transition-all duration-300 ${className}`}>
    {children}
  </button>
);

// --- DATA FOR SECTIONS ---
const features = [
  {
    icon: <Package className="w-8 h-8 text-blue-400" />,
    name: 'Goal Decomposition',
    description: "Break down large goals into smaller, actionable milestones. Create a clear roadmap and celebrate every step of your journey.",
  },
  {
    icon: <Zap className="w-8 h-8 text-blue-400" />,
    name: 'Flexible Habit Tracking',
    description: "Track daily, weekly, or custom habits. Build powerful streaks and stay motivated with visual progress indicators.",
  },
  {
    icon: <Heart className="w-8 h-8 text-blue-400" />,
    name: 'Interactive Vision Board',
    description: "Create a digital canvas of your dreams. Arrange images, quotes, and notes to keep your aspirations in sharp focus.",
  },
  {
    icon: <Star className="w-8 h-8 text-blue-400" />,
    name: 'Progress Analytics',
    description: "Visualize your journey with insightful charts. Understand your patterns, celebrate your wins, and stay on track.",
  },
];

const stats = [
  {
    icon: <CheckCircle className="w-10 h-10 text-green-400" />,
    value: '120,000+',
    label: 'Goals Achieved',
  },
  {
    icon: <Users className="w-10 h-10 text-indigo-400" />,
    value: '75,000+',
    label: 'Active Users',
  },
  {
    icon: <Star className="w-10 h-10 text-yellow-400" />,
    value: '4.9/5',
    label: 'User Rating',
  },
];

const sampleItems = [
  {
    type: 'GOAL',
    title: 'Run a Marathon',
    progress: 50,
    milestones: ['Run 5k', 'Run 10k', 'Run Half-Marathon'],
    image: 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?ixlib=rb-4.0.3&q=80&w=300&h=200&auto=format&fit=crop',
  },
  {
    type: 'HABIT',
    title: 'Meditate Daily',
    streak: 21,
    frequency: 'Daily',
    image: 'https://images.unsplash.com/photo-1506126613408-4e0596027091?ixlib=rb-4.0.3&q=80&w=300&h=200&auto=format&fit=crop',
  },
  {
    type: 'VISION',
    title: 'Trip to Japan',
    description: 'Save up for a 2-week adventure.',
    image: 'https://images.unsplash.com/photo-1524413840807-0c3cb6fa808d?ixlib=rb-4.0.3&q=80&w=300&h=200&auto=format&fit=crop',
  },
  {
    type: 'GOAL',
    title: 'Write a Novel',
    progress: 25,
    milestones: ['Outline Chapters', 'Write 10k words', 'First Draft'],
    image: 'https://images.unsplash.com/photo-1455390582262-044cdead277a?ixlib=rb-4.0.3&q=80&w=300&h=200&auto=format&fit=crop',
  },
  {
    type: 'HABIT',
    title: 'Read 20 Pages',
    streak: 5,
    frequency: '5x a week',
    image: 'https://images.unsplash.com/photo-1532012197267-da84d127e765?ixlib=rb-4.0.3&q=80&w=300&h=200&auto=format&fit=crop',
  },
  {
    type: 'VISION',
    title: 'Learn Guitar',
    description: 'Master the basics and play one full song.',
    image: 'https://images.unsplash.com/photo-1550291652-6ea9114a47b1?ixlib=rb-4.0.3&q=80&w=300&h=200&auto=format&fit=crop',
  },
  {
    type: 'GOAL',
    title: 'Launch a Side Project',
    progress: 70,
    milestones: ['Ideation', 'Build MVP', 'Get First 10 Users'],
    image: 'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?ixlib=rb-4.0.3&q=80&w=300&h=200&auto=format&fit=crop',
  },
  {
    type: 'HABIT',
    title: 'Workout 3x a Week',
    streak: 12,
    frequency: '3x a week',
    image: 'https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?ixlib=rb-4.0.3&q=80&w=300&h=200&auto=format&fit=crop',
  },
];


// --- MAIN APP COMPONENT ---
export default function App() {
  return (
    <div className="bg-gray-900 text-gray-200 font-sans">
      
      {/* --- HERO SECTION --- */}
      <header className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-800 to-indigo-900 opacity-90"></div>
        <div className="relative container mx-auto px-6 py-24 md:py-32 text-center">
          <h1 className="text-5xl md:text-7xl font-extrabold text-white leading-tight tracking-tighter">
            Say <span className="text-blue-400">yes</span> to your ambitions.
          </h1>
          <p className="mt-6 max-w-2xl mx-auto text-lg md:text-xl text-indigo-200">
            The all-in-one tracker to deconstruct your goals, build lasting habits, and visualize your success. Turn your dreams into your daily reality.
          </p>
          <div className="mt-10">
            <Button>
              Start Your Journey <ArrowRight className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </header>

      <main>
        {/* --- FEATURES SECTION --- */}
        <section id="features" className="py-20 sm:py-24 bg-gray-900">
          <div className="container mx-auto px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-white">A Powerful Toolkit for Your Growth</h2>
              <p className="mt-4 text-lg text-gray-400">Everything you need to plan, track, and achieve.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {features.map((feature) => (
                <div key={feature.name} className="bg-gray-800/50 p-6 rounded-xl border border-gray-700 hover:border-blue-500 hover:bg-gray-800 transition-all duration-300">
                  <div className="flex items-center justify-center h-12 w-12 rounded-lg bg-blue-900/50 mb-4">
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">{feature.name}</h3>
                  <p className="text-gray-400">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* --- STATS SECTION --- */}
        <section className="py-20 sm:py-24 bg-gray-800/50">
          <div className="container mx-auto px-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
              {stats.map((stat) => (
                <div key={stat.label} className="p-4">
                  <div className="flex items-center justify-center mb-3">
                    {stat.icon}
                  </div>
                  <p className="text-4xl font-extrabold text-white">{stat.value}</p>
                  <p className="text-lg text-gray-400">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* --- MAIN CONTENT AREA (SAMPLE ITEMS) --- */}
        <section id="dashboard-preview" className="py-20 sm:py-24">
          <div className="container mx-auto px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-white">Your Dashboard, Your Life</h2>
              <p className="mt-4 text-lg text-gray-400">See your goals, habits, and visions come to life.</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {sampleItems.map((item, index) => (
                <div key={index} className="bg-gray-800 rounded-lg overflow-hidden shadow-lg border border-gray-700 group transform hover:-translate-y-2 transition-transform duration-300">
                  <img src={item.image} alt={item.title} className="w-full h-32 object-cover" />
                  <div className="p-5">
                    <span className={`inline-block px-2 py-1 text-xs font-semibold rounded-full mb-3 ${
                      item.type === 'GOAL' ? 'bg-purple-600/20 text-purple-300' :
                      item.type === 'HABIT' ? 'bg-green-600/20 text-green-300' :
                      'bg-yellow-600/20 text-yellow-300'
                    }`}>
                      {item.type}
                    </span>
                    <h3 className="text-lg font-bold text-white mb-2">{item.title}</h3>
                    {item.type === 'GOAL' && (
                      <div>
                        <div className="w-full bg-gray-700 rounded-full h-2.5 mb-2">
                          <div className="bg-purple-500 h-2.5 rounded-full" style={{ width: `${item.progress}%` }}></div>
                        </div>
                        <p className="text-sm text-gray-400">{item.progress}% complete</p>
                      </div>
                    )}
                    {item.type === 'HABIT' && (
                      <div className="flex items-center gap-2 text-green-400">
                        <Zap className="w-4 h-4" />
                        <p className="text-sm font-semibold">{item.streak} day streak</p>
                      </div>
                    )}
                    {item.type === 'VISION' && (
                      <p className="text-sm text-gray-400">{item.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      {/* --- FOOTER --- */}
      <footer className="bg-gray-900 border-t border-gray-800">
        <div className="container mx-auto px-6 py-12">
          <div className="md:flex md:items-center md:justify-between">
            <div className="flex justify-center md:order-2">
              <a href="#" className="text-gray-400 hover:text-white mx-3"><Twitter /></a>
              <a href="#" className="text-gray-400 hover:text-white mx-3"><Facebook /></a>
              <a href="#" className="text-gray-400 hover:text-white mx-3"><Instagram /></a>
            </div>
            <div className="mt-8 md:mt-0 md:order-1">
              <p className="text-center text-sm text-gray-400">
                &copy; {new Date().getFullYear()} yes. All rights reserved. Your goals are waiting.
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}