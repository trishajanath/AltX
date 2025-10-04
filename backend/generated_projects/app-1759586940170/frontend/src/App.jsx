import React, { useState, useEffect } from 'react';
import { Star, Users, Download, Github, CheckCircle, Zap, TrendingUp, Shield } from 'lucide-react';

// Inline components
const Button = ({ children, variant = 'primary', size = 'md', className = '', ...props }) => {
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
    outline: 'border border-gray-300 hover:bg-gray-50 text-gray-700'
  };
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg'
  };
  return (
    <button 
      className={`rounded-md font-medium transition-colors ${variants[variant]} ${sizes[size]} ${className}`}
      {...(props || {})}
    >
      {children}
    </button>
  );
};

const Card = ({ children, className = '' }) => (
  <div className={`bg-white rounded-lg border shadow-sm p-6 ${className}`}>
    {children}
  </div>
);

function App() {
  const [stats, setStats] = useState([
    { label: '50,000+ Active Users', value: '50K+', icon: Users },
    { label: '99.9% Uptime Guaranteed', value: '99.9%', icon: Shield },
    { label: '10x Faster Performance', value: '10x', icon: TrendingUp },
    { label: '24/7 Expert Support', value: '24/7', icon: CheckCircle }
  ]);

  const [features, setFeatures] = useState([
    {
      title: 'AI-Powered Analytics',
      description: 'Real-time insights with machine learning algorithms that analyze user behavior patterns and predict future trends.',
      icon: Zap,
      image: 'https://images.unsplash.com/1600x900/?technology,analytics'
    },
    {
      title: 'Advanced Dashboard',
      description: 'Customizable dashboards with drag-and-drop widgets, real-time charts, and interactive data visualization.',
      icon: TrendingUp,
      image: 'https://images.unsplash.com/1600x900/?dashboard,charts'
    },
    {
      title: 'Enterprise Security',
      description: 'Bank-level encryption, multi-factor authentication, and compliance with SOC 2 and GDPR standards.',
      icon: Shield,
      image: 'https://images.unsplash.com/1600x900/?security,technology'
    },
    {
      title: 'Team Collaboration',
      description: 'Built-in chat, file sharing, project management tools, and real-time collaboration features.',
      icon: Users,
      image: 'https://images.unsplash.com/1600x900/?teamwork,collaboration'
    },
    {
      title: 'API Integration',
      description: 'Connect with 1000+ popular tools and services through our comprehensive REST API and webhooks.',
      icon: Download,
      image: 'https://images.unsplash.com/1600x900/?api,integration'
    },
    {
      title: 'Smart Automation',
      description: 'Workflow automation that learns from your patterns and suggests optimizations to boost productivity.',
      icon: CheckCircle,
      image: 'https://images.unsplash.com/1600x900/?automation,workflow'
    }
  ]);

  const [projects, setProjects] = useState([
    { id: 1, name: 'E-commerce Platform', status: 'Active', users: 15420, revenue: '$125K' },
    { id: 2, name: 'Marketing Dashboard', status: 'Active', users: 8950, revenue: '$89K' },
    { id: 3, name: 'Customer Portal', status: 'Active', users: 12300, revenue: '$156K' },
    { id: 4, name: 'Analytics Engine', status: 'Beta', users: 3200, revenue: '$45K' },
    { id: 5, name: 'Mobile App Backend', status: 'Active', users: 22100, revenue: '$198K' },
    { id: 6, name: 'AI Recommendation System', status: 'Active', users: 18700, revenue: '$167K' },
    { id: 7, name: 'Real-time Chat Platform', status: 'Active', users: 9800, revenue: '$76K' },
    { id: 8, name: 'Video Streaming Service', status: 'Beta', users: 5400, revenue: '$67K' },
    { id: 9, name: 'IoT Device Manager', status: 'Active', users: 7600, revenue: '$92K' },
    { id: 10, name: 'Blockchain Wallet', status: 'Active', users: 11200, revenue: '$134K' },
    { id: 11, name: 'Social Media Aggregator', status: 'Active', users: 14800, revenue: '$145K' },
    { id: 12, name: 'Document Management', status: 'Active', users: 6900, revenue: '$58K' }
  ]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                app-1759586940170
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="outline" size="sm">Sign In</Button>
              <Button size="sm">Get Started</Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-600 via-purple-600 to-indigo-800 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-5xl font-bold mb-6 animate-fade-in">
            Transform Your Business with AI-Powered Solutions
          </h2>
          <p className="text-xl mb-8 text-blue-100 max-w-3xl mx-auto">
            Unlock the power of artificial intelligence to streamline operations, boost productivity, 
            and drive unprecedented growth for your organization.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100">
              Start Free Trial
            </Button>
            <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-blue-600">
              Watch Demo
            </Button>
          </div>
          <img 
            src="https://images.unsplash.com/1200x600/?technology,dashboard,analytics" 
            alt="Platform Dashboard"
            className="mt-12 mx-auto rounded-xl shadow-2xl border border-white/20"
          />
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => {
              const IconComponent = stat.icon;
              return (
                <div key={index} className="text-center">
                  <div className="flex justify-center mb-4">
                    <div className="p-3 bg-blue-100 rounded-full">
                      <IconComponent className="w-6 h-6 text-blue-600" />
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-gray-900 mb-2">{stat.value}</div>
                  <div className="text-gray-600">{stat.label}</div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h3 className="text-4xl font-bold text-gray-900 mb-4">
              Powerful Features Built for Modern Teams
            </h3>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Everything you need to build, deploy, and scale your applications with confidence.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const IconComponent = feature.icon;
              return (
                <Card key={index} className="hover:shadow-xl transition-shadow duration-300">
                  <img 
                    src={feature.image} 
                    alt={feature.title}
                    className="w-full h-48 object-cover rounded-lg mb-4"
                  />
                  <div className="flex items-center mb-3">
                    <IconComponent className="w-5 h-5 text-blue-600 mr-3" />
                    <h4 className="text-lg font-semibold text-gray-900">{feature.title}</h4>
                  </div>
                  <p className="text-gray-600">{feature.description}</p>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Main Content - Projects Dashboard */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center mb-12">
            <h3 className="text-3xl font-bold text-gray-900">Active Projects</h3>
            <Button>Create New Project</Button>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {projects.map((project) => (
              <Card key={project.id} className="hover:shadow-lg transition-shadow cursor-pointer">
                <div className="flex justify-between items-start mb-3">
                  <h4 className="font-semibold text-gray-900">{project.name}</h4>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    project.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {project.status}
                  </span>
                </div>
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex justify-between">
                    <span>Users:</span>
                    <span className="font-medium">{project.users.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Revenue:</span>
                    <span className="font-medium text-green-600">{project.revenue}</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="py-20 bg-blue-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h3 className="text-3xl font-bold mb-4">Trusted by Industry Leaders</h3>
          <p className="text-xl text-blue-100 mb-12">
            Join thousands of companies that have transformed their operations with our platform
          </p>
          <div className="grid md:grid-cols-3 gap-8">
            <Card className="bg-white/10 backdrop-blur-md border-white/20">
              <div className="flex items-center mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                ))}
              </div>
              <p className="text-blue-100 mb-4">
                "This platform has revolutionized our workflow. We've seen a 300% increase in productivity since implementation."
              </p>
              <div className="text-white font-semibold">Sarah Johnson, CTO at TechCorp</div>
            </Card>
            
            <Card className="bg-white/10 backdrop-blur-md border-white/20">
              <div className="flex items-center mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                ))}
              </div>
              <p className="text-blue-100 mb-4">
                "Outstanding support and incredibly intuitive interface. Our team was up and running in just one day."
              </p>
              <div className="text-white font-semibold">Michael Chen, Product Manager at StartupXYZ</div>
            </Card>
            
            <Card className="bg-white/10 backdrop-blur-md border-white/20">
              <div className="flex items-center mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                ))}
              </div>
              <p className="text-blue-100 mb-4">
                "The AI-powered insights have helped us make better decisions and stay ahead of our competition."
              </p>
              <div className="text-white font-semibold">Emily Rodriguez, CEO at InnovateLab</div>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-purple-600 to-indigo-600 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h3 className="text-4xl font-bold mb-6">Ready to Transform Your Business?</h3>
          <p className="text-xl text-purple-100 mb-8">
            Join over 50,000 companies using our platform to drive growth and innovation.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-white text-purple-600 hover:bg-gray-100">
              Start Your Free Trial
            </Button>
            <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-purple-600">
              Contact Sales
            </Button>
          </div>
          <p className="text-sm text-purple-200 mt-4">
            No credit card required • 14-day free trial • Cancel anytime
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <h4 className="text-lg font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white">Features</a></li>
                <li><a href="#" className="hover:text-white">Pricing</a></li>
                <li><a href="#" className="hover:text-white">API</a></li>
                <li><a href="#" className="hover:text-white">Documentation</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-lg font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white">About</a></li>
                <li><a href="#" className="hover:text-white">Blog</a></li>
                <li><a href="#" className="hover:text-white">Careers</a></li>
                <li><a href="#" className="hover:text-white">Press</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-lg font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white">Help Center</a></li>
                <li><a href="#" className="hover:text-white">Contact</a></li>
                <li><a href="#" className="hover:text-white">Status</a></li>
                <li><a href="#" className="hover:text-white">Security</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-lg font-semibold mb-4">Connect</h4>
              <div className="flex space-x-4">
                <Github className="w-6 h-6 text-gray-400 hover:text-white cursor-pointer" />
                <Users className="w-6 h-6 text-gray-400 hover:text-white cursor-pointer" />
                <Download className="w-6 h-6 text-gray-400 hover:text-white cursor-pointer" />
              </div>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-12 pt-8 text-center text-gray-400">
            <p>&copy; 2024 app-1759586940170. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;