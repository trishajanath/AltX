import React, { useState, useEffect, useRef } from 'react';

// --- UTILITY FOR CLASSNAMES ---
const cn = (...classes) => classes.filter(Boolean).join(' ');

// --- SAFE FRAMER-MOTION FALLBACKS (CRITICAL FOR BROWSER COMPATIBILITY) ---
const createMotionFallback = (element) => {
  const Component = ({ children, className, style, onClick, id, ...props }) => {
    // Filter out framer-motion specific props to avoid React warnings
    const validProps = { className, style, onClick, id };
    return React.createElement(element, validProps, children);
  };
  Component.displayName = `motion.${element}`;
  return Component;
};

const motion = {
  div: createMotionFallback('div'),
  span: createMotionFallback('span'),
  section: createMotionFallback('section'),
  h1: createMotionFallback('h1'),
  h2: createMotionFallback('h2'),
  button: createMotionFallback('button'),
  p: createMotionFallback('p'),
  nav: createMotionFallback('nav'),
  ul: createMotionFallback('ul'),
  li: createMotionFallback('li'),
};

const AnimatePresence = ({ children }) => <>{children}</>;

// --- CONTEXT DEFINITIONS (USING React.createContext) ---
const AuthContext = React.createContext(null);
const useAuth = () => React.useContext(AuthContext);

const NotificationContext = React.createContext(null);
const useNotification = () => React.useContext(NotificationContext);

// --- API CONFIGURATION ---
const API_URL = (typeof window !== 'undefined' && window.ENV?.API_URL) || 'http://localhost:8001/api/v1';

// --- ICON COMPONENTS ---
const Menu = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>;
const X = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="12"></line></svg>;
const BookOpen = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>;
const BarChart2 = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>;
const UploadCloud = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 16.2A4.5 4.5 0 0 0 17.5 8h-1.8A7 7 0 1 0 4 14.9"></path><path d="M12 12v9"></path><path d="m16 16-4-4-4 4"></path></svg>;
const Users = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>;
const FileText = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><line x1="10" y1="9" x2="8" y2="9"></line></svg>;
const Bell = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>;

// --- UI COMPONENTS (SHADCN STYLE) ---
const buttonVariants = {
  default: "bg-purple-600 text-white hover:bg-purple-700 shadow-lg shadow-purple-500/20",
  destructive: "bg-red-500 text-white hover:bg-red-600",
  outline: "border border-purple-400 bg-transparent hover:bg-purple-500/10 text-purple-300",
  ghost: "hover:bg-white/10 text-white",
  link: "text-primary underline-offset-4 hover:underline",
};

const Button = ({ children, variant = "default", className = "", ...props }) => (
  <button className={cn("inline-flex items-center justify-center rounded-md px-6 py-3 text-sm font-bold tracking-wider uppercase transition-all duration-300 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed hover:-translate-y-1", buttonVariants[variant], className)} {...props}>
    {children}
  </button>
);

const Modal = ({ isOpen, onClose, children, title }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <motion.div className="bg-gray-900/80 backdrop-blur-lg border border-white/10 rounded-2xl max-w-md w-full max-h-[90vh] overflow-y-auto text-white shadow-2xl shadow-purple-500/20">
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <h2 className="text-xl font-bold tracking-tight">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </motion.div>
    </div>
  );
};

const LoadingSpinner = () => <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-400"></div>;

const Toast = ({ message, type = "success", onClose }) => (
  <motion.div className={cn("fixed bottom-5 right-5 p-4 rounded-lg shadow-2xl z-50 border", type === "success" ? "bg-green-500/20 border-green-400 text-green-200 backdrop-blur-md" : "bg-red-500/20 border-red-400 text-red-200 backdrop-blur-md")}>
    <div className="flex items-center justify-between">
      <span>{message}</span>
      <button onClick={onClose} className="ml-4 text-white/70 hover:text-white">
        <X />
      </button>
    </div>
  </motion.div>
);

// --- AUTHENTICATION COMPONENTS ---
const AuthFormInput = (props) => (
  <input {...props} className="w-full px-4 py-3 bg-gray-800/50 border border-white/10 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all placeholder-gray-500" />
);

const LoginModal = ({ isOpen, onClose, onSuccess, onSwitchToSignup }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const showNotification = useNotification();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        onSuccess(data.user);
        onClose();
      } else {
        setError(data.detail || 'Login failed');
        showNotification(data.detail || 'Login failed', 'error');
      }
    } catch (err) {
      setError('Network error. Please try again.');
      showNotification('Network error. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Welcome Back">
      <form onSubmit={handleLogin} className="space-y-4">
        {error && <div className="text-red-400 text-sm bg-red-500/10 p-3 rounded-md">{error}</div>}
        <AuthFormInput type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <AuthFormInput type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner /> : 'Login'}
        </Button>
        <p className="text-center text-sm text-gray-400">
          Don't have an account?{' '}
          <button type="button" onClick={onSwitchToSignup} className="font-semibold text-purple-400 hover:underline">Sign Up</button>
        </p>
      </form>
    </Modal>
  );
};

const SignupModal = ({ isOpen, onClose, onSuccess, onSwitchToLogin }) => {
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const showNotification = useNotification();

  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        onSuccess(data.user);
        onClose();
      } else {
        setError(data.detail || 'Registration failed');
        showNotification(data.detail || 'Registration failed', 'error');
      }
    } catch (err) {
      setError('Network error. Please try again.');
      showNotification('Network error. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Your Account">
      <form onSubmit={handleSignup} className="space-y-4">
        {error && <div className="text-red-400 text-sm bg-red-500/10 p-3 rounded-md">{error}</div>}
        <AuthFormInput type="text" placeholder="Full Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
        <AuthFormInput type="email" placeholder="Email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} required />
        <AuthFormInput type="password" placeholder="Password" value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} required />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner /> : 'Create Account'}
        </Button>
        <p className="text-center text-sm text-gray-400">
          Already have an account?{' '}
          <button type="button" onClick={onSwitchToLogin} className="font-semibold text-purple-400 hover:underline">Login</button>
        </p>
      </form>
    </Modal>
  );
};

// --- NAVIGATION COMPONENT ---
const OverlayNav = ({ isOpen, onClose, onLogin, onSignup, onLogout, user }) => {
  if (!isOpen) return null;

  return (
    <motion.div className="fixed inset-0 bg-black/90 backdrop-blur-xl z-40 flex flex-col items-center justify-center text-white">
      <button onClick={onClose} className="absolute top-8 right-8 text-gray-400 hover:text-white transition-transform duration-300 hover:rotate-90">
        <X size={32} />
      </button>
      <motion.ul className="flex flex-col items-center space-y-8 text-3xl font-light tracking-widest text-center">
        <li><a href="#home" onClick={onClose} className="hover:text-purple-400 transition-colors">Home</a></li>
        <li><a href="#features" onClick={onClose} className="hover:text-purple-400 transition-colors">Features</a></li>
        <li><a href="#dashboard" onClick={onClose} className="hover:text-purple-400 transition-colors">Dashboard</a></li>
        <li className="pt-8">
          {user ? (
            <div className="flex flex-col items-center space-y-4">
              <span className="text-lg text-gray-300">Welcome, {user.name}</span>
              <Button variant="outline" onClick={() => { onLogout(); onClose(); }}>Logout</Button>
            </div>
          ) : (
            <div className="flex items-center space-x-4">
              <Button variant="outline" onClick={() => { onLogin(); onClose(); }}>Login</Button>
              <Button onClick={() => { onSignup(); onClose(); }}>Sign Up</Button>
            </div>
          )}
        </li>
      </motion.ul>
    </motion.div>
  );
};

// --- FEATURE CARD COMPONENT ---
const FeatureCard = ({ icon, title, description }) => (
  <motion.div className="bg-white/5 backdrop-blur-md p-8 rounded-2xl border border-white/10 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:shadow-purple-500/20 hover:border-purple-500/50">
    <div className="text-purple-400 mb-4">{icon}</div>
    <h3 className="text-xl font-bold tracking-tight mb-2 text-white">{title}</h3>
    <p className="text-gray-400 font-normal leading-relaxed">{description}</p>
  </motion.div>
);

// --- MAIN APP COMPONENT ---
const App = () => {
  const [user, setUser] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [showNav, setShowNav] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser && savedUser !== 'undefined' && savedUser !== 'null') {
      try {
        setUser(JSON.parse(savedUser));
      } catch (error) {
        console.error('Failed to parse saved user data:', error);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
    }
    // Add Google Fonts
    const link = document.createElement('link');
    link.href = "https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Space+Grotesk:wght@700&display=swap";
    link.rel = 'stylesheet';
    document.head.appendChild(link);
  }, []);

  const showNotification = (message, type = 'success') => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  };

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    showNotification('Login successful!', 'success');
  };

  const handleSignupSuccess = (userData) => {
    setUser(userData);
    showNotification('Account created successfully!', 'success');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    showNotification('Logged out successfully', 'success');
  };

  const features = [
    { icon: <BookOpen />, title: 'Interactive Course Dashboard', description: 'A central hub for students and instructors to view enrolled courses, deadlines, and announcements.' },
    { icon: <BarChart2 />, title: 'Dynamic Gradebook & Analytics', description: 'Automatic grade calculation and visual analytics to identify student performance trends.' },
    { icon: <UploadCloud />, title: 'Automated Assignment Submission', description: 'Securely upload assignments, with automatic timestamping and deadline enforcement.' },
    { icon: <Users />, title: 'Role-Based Access Control', description: 'Differentiated access levels for Administrators, Instructors, and Students for enhanced security.' },
    { icon: <FileText />, title: 'Resource & Syllabus Management', description: 'Organize course materials like syllabi, lecture notes, and external links in one place.' },
    { icon: <Bell />, title: 'Real-time Announcement System', description: 'Instant in-app notifications for all enrolled students about important course updates.' },
  ];

  return (
    <AuthContext.Provider value={{ user, login: handleLoginSuccess, logout: handleLogout }}>
      <NotificationContext.Provider value={showNotification}>
        <div style={{ fontFamily: "'Inter', sans-serif" }} className="bg-gray-900 text-white selection:bg-purple-500 selection:text-white">
          
          <button onClick={() => setShowNav(true)} className="fixed top-6 right-6 z-50 p-2 rounded-full bg-white/10 backdrop-blur-md hover:bg-white/20 transition-all duration-300 ring-1 ring-white/10">
            <Menu />
          </button>

          <OverlayNav 
            isOpen={showNav} 
            onClose={() => setShowNav(false)}
            onLogin={() => setShowLogin(true)}
            onSignup={() => setShowSignup(true)}
            onLogout={handleLogout}
            user={user}
          />

          <main className="h-screen overflow-y-scroll snap-y snap-mandatory">
            {/* Hero Section */}
            <motion.section id="home" className="immersive-section snap-start bg-gradient-to-br from-gray-900 via-purple-900 to-violet-800 relative overflow-hidden">
              <div className="immersive-bg"></div>
              <div className="immersive-content max-w-4xl mx-auto px-4">
                <motion.h1 style={{ fontFamily: "'Space Grotesk', sans-serif" }} className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tighter mb-6 bg-clip-text text-transparent bg-gradient-to-br from-white to-purple-300">
                  Learn Without Limits
                </motion.h1>
                <motion.p className="text-lg md:text-xl max-w-2xl mx-auto text-gray-300 leading-relaxed mb-10">
                  Welcome to web-provide-education-050728, the next-generation Education Management System designed to elevate the learning experience for everyone.
                </motion.p>
                <div className="flex justify-center items-center gap-4">
                  <Button onClick={() => user ? document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' }) : setShowSignup(true)}>
                    {user ? 'Explore Dashboard' : 'Get Started Free'}
                  </Button>
                  <Button variant="outline">Request a Demo</Button>
                </div>
              </div>
            </motion.section>

            {/* Features Section */}
            <motion.section id="features" className="immersive-section snap-start bg-gray-900 relative">
              <div className="immersive-bg" style={{ background: 'radial-gradient(circle at 70% 60%, rgba(168, 85, 247, 0.2), transparent 50%)' }}></div>
              <div className="immersive-content container mx-auto px-4 py-20">
                <motion.h2 className="text-4xl md:text-5xl font-bold tracking-tight text-center mb-4">A Smarter Way to Educate</motion.h2>
                <motion.p className="text-lg text-gray-400 text-center max-w-3xl mx-auto mb-16">
                  Our platform provides a comprehensive suite of tools to streamline every aspect of education management.
                </motion.p>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {features.map((feature, index) => (
                    <FeatureCard key={index} {...feature} />
                  ))}
                </div>
              </div>
            </motion.section>
            
            {/* Call to Action / Dashboard Preview Section */}
            <motion.section id="dashboard" className="immersive-section snap-start bg-gradient-to-br from-zinc-900 to-zinc-600 relative">
                <div className="immersive-bg" style={{ background: 'radial-gradient(circle at 20% 80%, rgba(236, 72, 153, 0.15), transparent 50%)' }}></div>
                <div className="immersive-content max-w-4xl mx-auto px-4 text-center">
                    <motion.h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-6">
                        Your Centralized Command Center
                    </motion.h2>
                    <motion.p className="text-lg md:text-xl text-gray-300 leading-relaxed mb-10">
                        {user ? `Welcome back, ${user.name}! Your dashboard is ready.` : 'Sign up to unlock your personalized dashboard and take control of your educational journey.'}
                    </motion.p>
                    {!user && (
                        <Button onClick={() => setShowSignup(true)} className="bg-gradient-to-r from-pink-500 to-red-500 hover:from-pink-600 hover:to-red-600 shadow-pink-500/30">
                            Create Your Account Now
                        </Button>
                    )}
                </div>
            </motion.section>

          </main>

          {/* Modals */}
          <AnimatePresence>
            {showLogin && (
              <LoginModal 
                isOpen={showLogin}
                onClose={() => setShowLogin(false)}
                onSuccess={handleLoginSuccess}
                onSwitchToSignup={() => { setShowLogin(false); setShowSignup(true); }}
              />
            )}
          </AnimatePresence>
          <AnimatePresence>
            {showSignup && (
              <SignupModal 
                isOpen={showSignup}
                onClose={() => setShowSignup(false)}
                onSuccess={handleSignupSuccess}
                onSwitchToLogin={() => { setShowSignup(false); setShowLogin(true); }}
              />
            )}
          </AnimatePresence>

          {/* Notifications */}
          <div className="fixed bottom-0 right-0 p-4 space-y-2">
            <AnimatePresence>
              {notifications.map(notification => (
                <Toast
                  key={notification.id}
                  message={notification.message}
                  type={notification.type}
                  onClose={() => setNotifications(prev => prev.filter(n => n.id !== notification.id))}
                />
              ))}
            </AnimatePresence>
          </div>
        </div>
      </NotificationContext.Provider>
    </AuthContext.Provider>
  );
};

export default App;