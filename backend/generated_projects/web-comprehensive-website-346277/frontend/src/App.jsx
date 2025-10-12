import React, { useState, useEffect, createContext, useContext, useCallback } from 'react';

// UTILS (for cn function)
const cn = (...classes) => classes.filter(Boolean).join(' ');

// SHADCN/UI STYLE DEFINITIONS
const buttonVariants = {
  default: "bg-blue-600 text-white hover:bg-blue-700",
  destructive: "bg-red-500 text-white hover:bg-red-600",
  outline: "border border-blue-500 bg-transparent text-blue-400 hover:bg-blue-500 hover:text-black",
  secondary: "bg-gray-700 text-gray-200 hover:bg-gray-600",
  ghost: "hover:bg-gray-800 hover:text-gray-100",
  link: "text-blue-400 underline-offset-4 hover:underline",
};

const cardVariants = {
  default: "bg-gray-900 border border-gray-700 rounded-lg shadow-md text-gray-300",
};

// --- CONTEXT DEFINITIONS ---

// AUTHENTICATION CONTEXT
const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

// NOTIFICATION CONTEXT
const NotificationContext = createContext(null);
export const useNotification = () => useContext(NotificationContext);

// --- ICON COMPONENTS ---

const User = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>;
const X = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>;
const Menu = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>;
const Search = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>;
const MapPin = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>;
const BookOpen = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>;
const Users = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>;
const Briefcase = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>;
const Calendar = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>;
const Download = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>;

// --- UI COMPONENTS ---

const Button = React.forwardRef(({ className, variant, ...props }, ref) => (
  <button
    className={cn(
      "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none disabled:opacity-50 disabled:cursor-not-allowed",
      buttonVariants[variant] || buttonVariants.default,
      className
    )}
    ref={ref}
    {...props}
  />
));

const Card = ({ children, className, variant = "default" }) => (
  <div className={cn(cardVariants[variant], className)}>{children}</div>
);

const Modal = ({ isOpen, onClose, children, title }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto text-gray-200">
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-xl font-semibold text-blue-400">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X /></button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};

const LoadingSpinner = () => (
  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>
);

const Toast = ({ message, type = "success", onClose }) => (
  <div className={cn(
    "fixed top-5 right-5 p-4 rounded-md shadow-lg z-[100] text-white",
    type === "success" ? "bg-green-600" : "bg-red-600"
  )}>
    <div className="flex items-center justify-between">
      <span>{message}</span>
      <button onClick={onClose} className="ml-4 -mr-2 p-1 rounded-md hover:bg-white/20"><X /></button>
    </div>
  </div>
);

const Input = React.forwardRef(({ className, ...props }, ref) => (
    <input
        className={cn(
            "flex h-10 w-full rounded-md border border-gray-600 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900",
            className
        )}
        ref={ref}
        {...props}
    />
));

const Select = React.forwardRef(({ className, children, ...props }, ref) => (
    <select
        className={cn(
            "flex h-10 w-full rounded-md border border-gray-600 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900",
            className
        )}
        ref={ref}
        {...props}
    >
        {children}
    </select>
));

// --- AUTHENTICATION COMPONENTS ---

const LoginModal = ({ isOpen, onClose, onSwitchToSignup }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const auth = useAuth();
  const showNotification = useNotification();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch('http://localhost:8001/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await response.json();
      if (response.ok) {
        auth.login(data.access_token, data.user);
        showNotification('Login successful!', 'success');
        onClose();
      } else {
        setError(data.detail || 'Login failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Student & Faculty Login">
      <form onSubmit={handleLogin} className="space-y-4">
        {error && <div className="text-red-400 text-sm bg-red-900/50 p-2 rounded">{error}</div>}
        <Input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <Input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner /> : 'Login'}
        </Button>
        <p className="text-sm text-center text-gray-400">
          Don't have an account?{' '}
          <button type="button" onClick={onSwitchToSignup} className="font-medium text-blue-400 hover:underline">
            Sign up
          </button>
        </p>
      </form>
    </Modal>
  );
};

const SignupModal = ({ isOpen, onClose, onSwitchToLogin }) => {
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const auth = useAuth();
  const showNotification = useNotification();

  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch('http://localhost:8001/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await response.json();
      if (response.ok) {
        auth.login(data.access_token, data.user);
        showNotification('Account created successfully!', 'success');
        onClose();
      } else {
        setError(data.detail || 'Registration failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create an Account">
      <form onSubmit={handleSignup} className="space-y-4">
        {error && <div className="text-red-400 text-sm bg-red-900/50 p-2 rounded">{error}</div>}
        <Input type="text" placeholder="Full Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
        <Input type="email" placeholder="Email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} required />
        <Input type="password" placeholder="Password" value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} required />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner /> : 'Sign Up'}
        </Button>
        <p className="text-sm text-center text-gray-400">
          Already have an account?{' '}
          <button type="button" onClick={onSwitchToLogin} className="font-medium text-blue-400 hover:underline">
            Login
          </button>
        </p>
      </form>
    </Modal>
  );
};

// --- API HOOK ---
const useApi = () => {
    const auth = useAuth();
    const showNotification = useNotification();

    const apiFetch = useCallback(async (url, options = {}) => {
        const token = localStorage.getItem('token');
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(`http://localhost:8001/api/v1${url}`, { ...options, headers });

            if (response.status === 401) {
                auth.logout();
                showNotification('Session expired. Please log in again.', 'error');
                throw new Error('Unauthorized');
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            
            if (response.status === 204) { // No Content
                return null;
            }

            return await response.json();
        } catch (error) {
            console.error('API Fetch Error:', error);
            throw error;
        }
    }, [auth, showNotification]);

    return apiFetch;
};


// --- HEADER & NAVIGATION ---

const Header = () => {
  const auth = useAuth();
  const [isLoginOpen, setLoginOpen] = useState(false);
  const [isSignupOpen, setSignupOpen] = useState(false);
  const [isMenuOpen, setMenuOpen] = useState(false);

  const navLinks = [
    { name: 'Academics', href: '#programs' },
    { name: 'Faculty', href: '#faculty' },
    { name: 'Campus Life', href: '#tour' },
    { name: 'News & Events', href: '#events' },
    { name: 'Alumni', href: '#alumni' },
  ];

  return (
    <>
      <header className="bg-black/80 backdrop-blur-sm border-b border-gray-800 sticky top-0 z-40 text-blue-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <a href="#" className="text-2xl font-bold text-blue-400">PSG Tech</a>
            </div>
            <nav className="hidden md:flex md:space-x-8">
              {navLinks.map(link => (
                <a key={link.name} href={link.href} className="text-sm font-medium hover:text-white transition-colors">{link.name}</a>
              ))}
            </nav>
            <div className="flex items-center">
              {auth.user ? (
                <div className="flex items-center space-x-4">
                  <span className="hidden sm:inline text-sm">Welcome, {auth.user.name.split(' ')[0]}</span>
                  <Button variant="outline" onClick={auth.logout}>Logout</Button>
                </div>
              ) : (
                <div className="hidden md:flex items-center space-x-2">
                  <Button variant="ghost" onClick={() => setLoginOpen(true)}>Login</Button>
                  <Button onClick={() => setSignupOpen(true)}>Sign Up</Button>
                </div>
              )}
              <div className="md:hidden ml-4">
                <Button variant="ghost" onClick={() => setMenuOpen(!isMenuOpen)}><Menu /></Button>
              </div>
            </div>
          </div>
        </div>
        {isMenuOpen && (
          <div className="md:hidden bg-black border-t border-gray-800">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
              {navLinks.map(link => (
                <a key={link.name} href={link.href} className="block px-3 py-2 rounded-md text-base font-medium hover:bg-gray-800 hover:text-white">{link.name}</a>
              ))}
              <div className="border-t border-gray-700 my-2"></div>
              {auth.user ? (
                 <Button variant="outline" onClick={auth.logout} className="w-full mt-2">Logout</Button>
              ) : (
                <div className="flex flex-col space-y-2 mt-2">
                  <Button variant="ghost" onClick={() => { setLoginOpen(true); setMenuOpen(false); }} className="w-full">Login</Button>
                  <Button onClick={() => { setSignupOpen(true); setMenuOpen(false); }} className="w-full">Sign Up</Button>
                </div>
              )}
            </div>
          </div>
        )}
      </header>
      <LoginModal 
        isOpen={isLoginOpen} 
        onClose={() => setLoginOpen(false)} 
        onSwitchToSignup={() => { setLoginOpen(false); setSignupOpen(true); }}
      />
      <SignupModal 
        isOpen={isSignupOpen} 
        onClose={() => setSignupOpen(false)} 
        onSwitchToLogin={() => { setSignupOpen(false); setLoginOpen(true); }}
      />
    </>
  );
};

// --- FEATURE COMPONENTS ---

const Section = ({ id, title, subtitle, children }) => (
    <section id={id} className="py-16 sm:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
                <h2 className="text-3xl font-bold tracking-tight text-blue-400 sm:text-4xl">{title}</h2>
                <p className="mt-3 max-w-2xl mx-auto text-lg text-gray-400">{subtitle}</p>
            </div>
            {children}
        </div>
    </section>
);

const ProgramFinder = () => {
    const [programs, setPrograms] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ level: 'All', department: 'All' });
    const apiFetch = useApi();

    useEffect(() => {
        const fetchPrograms = async () => {
            try {
                setLoading(true);
                const data = await apiFetch('/programs');
                setPrograms(data);
            } catch (err) {
                setError('Failed to load academic programs. Please try again later.');
            } finally {
                setLoading(false);
            }
        };
        fetchPrograms();
    }, [apiFetch]);

    const departments = ['All', ...new Set(programs.map(p => p.department))];
    const levels = ['All', ...new Set(programs.map(p => p.level))];

    const filteredPrograms = programs.filter(p => 
        (filters.level === 'All' || p.level === filters.level) &&
        (filters.department === 'All' || p.department === filters.department)
    );

    return (
        <Section id="programs" title="Interactive Program Finder" subtitle="Discover the right path for your future at PSG College of Technology.">
            <div className="flex flex-col md:flex-row gap-4 mb-8 justify-center">
                <Select value={filters.level} onChange={e => setFilters({...filters, level: e.target.value})}>
                    {levels.map(level => <option key={level} value={level}>{level}</option>)}
                </Select>
                <Select value={filters.department} onChange={e => setFilters({...filters, department: e.target.value})}>
                    {departments.map(dept => <option key={dept} value={dept}>{dept}</option>)}
                </Select>
            </div>
            {loading && <div className="flex justify-center"><LoadingSpinner /></div>}
            {error && <p className="text-center text-red-400">{error}</p>}
            {!loading && !error && (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {filteredPrograms.map(program => (
                        <Card key={program.id} className="flex flex-col p-6 hover:border-blue-500 transition-all">
                            <h3 className="text-xl font-semibold text-blue-300">{program.name}</h3>
                            <p className="text-sm text-gray-400 mt-1">{program.department} - {program.level}</p>
                            <p className="mt-4 flex-grow text-gray-300">{program.description}</p>
                            <div className="mt-6">
                                <Button variant="link" className="p-0">View Syllabus & Eligibility</Button>
                            </div>
                        </Card>
                    ))}
                </div>
            )}
        </Section>
    );
};

const VirtualTour = () => {
    const [activeHotspot, setActiveHotspot] = useState(null);
    const hotspots = [
        { id: 1, name: 'F-Block Labs', description: 'State-of-the-art laboratories for Computer Science and Information Technology students, equipped with the latest hardware and software.', top: '30%', left: '25%' },
        { id: 2, name: 'Central Library', description: 'A vast repository of knowledge with thousands of books, journals, and digital resources available to all students and faculty.', top: '50%', left: '60%' },
        { id: 3, name: 'Sports Complex', description: 'Extensive facilities for various indoor and outdoor sports, promoting physical fitness and a competitive spirit.', top: '70%', left: '40%' },
    ];

    return (
        <Section id="tour" title="Virtual Campus Tour" subtitle="Explore our vibrant campus from anywhere in the world.">
            <div className="relative aspect-video w-full max-w-5xl mx-auto rounded-lg overflow-hidden border-2 border-gray-700">
                <img src="https://via.placeholder.com/1280x720/000022/FFFFFF?text=PSG+Campus+View" alt="Campus aerial view" className="w-full h-full object-cover" />
                {hotspots.map(spot => (
                    <button 
                        key={spot.id} 
                        className="absolute w-8 h-8 rounded-full bg-blue-500/70 backdrop-blur-sm flex items-center justify-center text-white animate-pulse transform -translate-x-1/2 -translate-y-1/2"
                        style={{ top: spot.top, left: spot.left }}
                        onClick={() => setActiveHotspot(spot)}
                    >
                        <MapPin />
                    </button>
                ))}
            </div>
            <Modal isOpen={!!activeHotspot} onClose={() => setActiveHotspot(null)} title={activeHotspot?.name}>
                <img src={`https://via.placeholder.com/600x400/111133/FFFFFF?text=${activeHotspot?.name}`} alt={activeHotspot?.name} className="w-full rounded-md mb-4" />
                <p className="text-gray-300">{activeHotspot?.description}</p>
            </Modal>
        </Section>
    );
};

const StudentResourceHub = () => {
    const [resources, setResources] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const apiFetch = useApi();

    useEffect(() => {
        const fetchResources = async () => {
            try {
                setLoading(true);
                const data = await apiFetch('/student/resources');
                setResources(data);
            } catch (err) {
                setError('Could not load resources. Please ensure you are logged in.');
            } finally {
                setLoading(false);
            }
        };
        fetchResources();
    }, [apiFetch]);

    return (
        <Section id="hub" title="Centralized Student Hub" subtitle="Your one-stop portal for all academic needs.">
            {loading && <div className="flex justify-center"><LoadingSpinner /></div>}
            {error && <p className="text-center text-red-400 bg-red-900/50 p-4 rounded-md">{error}</p>}
            {!loading && !error && (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {resources.map(resource => (
                        <Card key={resource.id} className="p-6">
                            <div className="flex items-center gap-4">
                                <div className="bg-blue-900/50 p-3 rounded-full text-blue-400">
                                    {resource.type === 'calendar' && <Calendar />}
                                    {resource.type === 'circular' && <Download />}
                                    {resource.type === 'schedule' && <BookOpen />}
                                </div>
                                <div>
                                    <h3 className="text-lg font-semibold text-blue-300">{resource.title}</h3>
                                    <a href={resource.url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-500 hover:underline">Access Now</a>
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            )}
        </Section>
    );
};

const NewsAndEvents = () => {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filter, setFilter] = useState('All');
    const apiFetch = useApi();

    useEffect(() => {
        const fetchItems = async () => {
            try {
                setLoading(true);
                const data = await apiFetch('/events');
                setItems(data);
            } catch (err) {
                setError('Failed to load news and events.');
            } finally {
                setLoading(false);
            }
        };
        fetchItems();
    }, [apiFetch]);

    const departments = ['All', ...new Set(items.map(item => item.department))];
    const filteredItems = items.filter(item => filter === 'All' || item.department === filter);

    return (
        <Section id="events" title="Department News & Events" subtitle="Stay updated with the latest happenings across campus.">
            <div className="flex justify-center mb-8">
                <div className="flex space-x-2 p-1 bg-gray-800 rounded-lg">
                    {departments.map(dept => (
                        <Button key={dept} variant={filter === dept ? 'default' : 'ghost'} onClick={() => setFilter(dept)}>{dept}</Button>
                    ))}
                </div>
            </div>
            {loading && <div className="flex justify-center"><LoadingSpinner /></div>}
            {error && <p className="text-center text-red-400">{error}</p>}
            {!loading && !error && (
                <div className="space-y-8 max-w-4xl mx-auto">
                    {filteredItems.map(item => (
                        <Card key={item.id} className="p-6 flex flex-col sm:flex-row gap-6">
                            <div className="flex-shrink-0 text-center">
                                <p className="text-3xl font-bold text-blue-400">{new Date(item.date).getDate()}</p>
                                <p className="text-sm text-gray-400">{new Date(item.date).toLocaleString('default', { month: 'short' })}</p>
                            </div>
                            <div>
                                <span className="text-xs font-semibold uppercase tracking-wider bg-blue-900 text-blue-300 px-2 py-1 rounded">{item.type}</span>
                                <h3 className="text-xl font-semibold text-blue-300 mt-2">{item.title}</h3>
                                <p className="text-sm text-gray-500">Department of {item.department}</p>
                                <p className="mt-3 text-gray-300">{item.description}</p>
                            </div>
                        </Card>
                    ))}
                </div>
            )}
        </Section>
    );
};

const FacultyDirectory = () => {
    const [faculty, setFaculty] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const apiFetch = useApi();

    useEffect(() => {
        const fetchFaculty = async () => {
            try {
                setLoading(true);
                const data = await apiFetch('/faculty');
                setFaculty(data);
            } catch (err) {
                setError('Failed to load faculty directory.');
            } finally {
                setLoading(false);
            }
        };
        fetchFaculty();
    }, [apiFetch]);

    const filteredFaculty = faculty.filter(f =>
        f.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        f.department.toLowerCase().includes(searchTerm.toLowerCase()) ||
        f.research_interests.some(interest => interest.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    return (
        <Section id="faculty" title="Searchable Faculty Directory" subtitle="Connect with our distinguished academic and research staff.">
            <div className="max-w-lg mx-auto mb-8 relative">
                <Input 
                    type="text" 
                    placeholder="Search by name, department, or research interest (e.g., Machine Learning)" 
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    className="pl-10"
                />
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Search className="text-gray-500" />
                </div>
            </div>
            {loading && <div className="flex justify-center"><LoadingSpinner /></div>}
            {error && <p className="text-center text-red-400">{error}</p>}
            {!loading && !error && (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {filteredFaculty.map(prof => (
                        <Card key={prof.id} className="p-6 text-center">
                            <img src={prof.image_url} alt={prof.name} className="w-24 h-24 rounded-full mx-auto mb-4 border-2 border-blue-500" />
                            <h3 className="text-xl font-semibold text-blue-300">{prof.name}</h3>
                            <p className="text-gray-400">{prof.qualifications}</p>
                            <p className="text-sm text-blue-500 mt-1">{prof.department}</p>
                            <p className="text-xs text-gray-500 mt-4">Research Interests:</p>
                            <div className="flex flex-wrap justify-center gap-2 mt-2">
                                {prof.research_interests.map(interest => (
                                    <span key={interest} className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded-full">{interest}</span>
                                ))}
                            </div>
                        </Card>
                    ))}
                </div>
            )}
        </Section>
    );
};

const AlumniNetwork = () => {
    const [spotlights, setSpotlights] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const apiFetch = useApi();

    useEffect(() => {
        const fetchSpotlights = async () => {
            try {
                setLoading(true);
                const data = await apiFetch('/alumni/spotlight');
                setSpotlights(data);
            } catch (err) {
                setError('Could not load alumni stories. Please ensure you are logged in.');
            } finally {
                setLoading(false);
            }
        };
        fetchSpotlights();
    }, [apiFetch]);

    return (
        <Section id="alumni" title="Alumni Network & Success Stories" subtitle="Join a global network of leaders and innovators.">
            <div className="text-center mb-10">
                <Button size="lg">Register on the Alumni Network</Button>
            </div>
            <h3 className="text-2xl font-bold text-center text-blue-400 mb-8">Alumni Spotlight</h3>
            {loading && <div className="flex justify-center"><LoadingSpinner /></div>}
            {error && <p className="text-center text-red-400 bg-red-900/50 p-4 rounded-md">{error}</p>}
            {!loading && !error && (
                <div className="grid lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
                    {spotlights.map(alumnus => (
                        <Card key={alumnus.id} className="p-6 flex items-start gap-6">
                            <img src={alumnus.image_url} alt={alumnus.name} className="w-20 h-20 rounded-full flex-shrink-0 border-2 border-blue-500" />
                            <div>
                                <h4 className="text-xl font-semibold text-blue-300">{alumnus.name}</h4>
                                <p className="text-sm text-gray-400">{alumnus.company} - Class of {alumnus.graduation_year}</p>
                                <blockquote className="mt-3 border-l-4 border-gray-700 pl-4 text-gray-300 italic">
                                    "{alumnus.story}"
                                </blockquote>
                            </div>
                        </Card>
                    ))}
                </div>
            )}
        </Section>
    );
};

// --- MAIN APP COMPONENT ---

const App = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    try {
      const token = localStorage.getItem('token');
      const savedUser = localStorage.getItem('user');
      if (token && savedUser) {
        setUser(JSON.parse(savedUser));
      }
    } catch (error) {
      console.error("Failed to parse user from localStorage", error);
      localStorage.removeItem('user');
      localStorage.removeItem('token');
    } finally {
      setLoading(false);
    }
  }, []);

  const login = (token, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    showNotification('Logged out successfully', 'success');
  };

  const showNotification = (message, type = 'success') => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  };

  const authContextValue = { user, login, logout };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <AuthContext.Provider value={authContextValue}>
      <NotificationContext.Provider value={showNotification}>
        <div className="min-h-screen bg-black text-gray-300 font-sans">
          <Header />
          <main>
            {/* Hero Section */}
            <section className="relative bg-gray-900 py-20 sm:py-32">
                <div className="absolute inset-0 bg-black opacity-50"></div>
                <div 
                    className="absolute inset-0 bg-cover bg-center" 
                    style={{backgroundImage: "url('https://via.placeholder.com/1920x1080/000011/000011?text=.')"}}
                ></div>
                <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl md:text-6xl">
                        <span className="block">PSG College of Technology</span>
                        <span className="block text-blue-400">Engineering the Future</span>
                    </h1>
                    <p className="mt-6 max-w-lg mx-auto text-xl text-gray-300 sm:max-w-3xl">
                        A central hub for academic excellence, innovative research, and a vibrant campus community.
                    </p>
                    <div className="mt-10 max-w-sm mx-auto sm:max-w-none sm:flex sm:justify-center space-y-4 sm:space-y-0 sm:space-x-4">
                        <a href="#programs"><Button size="lg" className="w-full sm:w-auto">Find Your Program</Button></a>
                        <a href="#tour"><Button size="lg" variant="outline" className="w-full sm:w-auto">Take a Virtual Tour</Button></a>
                    </div>
                </div>
            </section>

            {/* Features Sections */}
            <ProgramFinder />
            <VirtualTour />
            {user && <StudentResourceHub />}
            <NewsAndEvents />
            <FacultyDirectory />
            {user && <AlumniNetwork />}
            {!user && (
                <section className="bg-gray-900 py-16">
                    <div className="max-w-4xl mx-auto text-center px-4">
                        <Users className="mx-auto h-12 w-12 text-blue-400" />
                        <h2 className="mt-6 text-3xl font-bold text-blue-300">Unlock More Features</h2>
                        <p className="mt-4 text-lg text-gray-400">
                            Log in or create an account to access the Student Hub, connect with our Alumni Network, and get a personalized experience.
                        </p>
                    </div>
                </section>
            )}
          </main>

          <footer className="bg-gray-900 border-t border-gray-800">
            <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8 text-center">
                <p className="text-gray-400">&copy; {new Date().getFullYear()} PSG College of Technology. All rights reserved.</p>
                <p className="text-xs text-gray-500 mt-2">This is a fictional portal for demonstration purposes.</p>
            </div>
          </footer>

          {/* Notifications Container */}
          <div className="fixed top-0 right-0 p-4 space-y-2">
            {notifications.map(n => (
              <Toast key={n.id} message={n.message} type={n.type} onClose={() => setNotifications(prev => prev.filter(item => item.id !== n.id))} />
            ))}
          </div>
        </div>
      </NotificationContext.Provider>
    </AuthContext.Provider>
  );
};

export default App;