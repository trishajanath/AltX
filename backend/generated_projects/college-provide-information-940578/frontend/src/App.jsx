// PSG College of Technology Student Portal
import React, { useState, useEffect, useMemo } from 'react'; // Using React.useContext and React.createContext for consistency

// UTILITY FOR CLASSNAMES (SHADCN)
const cn = (...inputs) => {
  const classes = [];
  inputs.forEach(input => {
    if (typeof input === 'string') {
      classes.push(input);
    } else if (typeof input === 'object' && input !== null) {
      for (const key in input) {
        if (input[key]) {
          classes.push(key);
        }
      }
    }
  });
  return classes.join(' ');
};

// SHADCN STYLE VARIANTS
const buttonVariants = {
  default: "bg-blue-600 text-white hover:bg-blue-700",
  outline: "border border-blue-600 text-blue-600 hover:bg-blue-600 hover:text-white",
  ghost: "hover:bg-gray-700 hover:text-white",
  destructive: "bg-red-600 text-white hover:bg-red-700",
};

const cardVariants = {
  default: "bg-gray-800 border border-gray-700 rounded-lg shadow-md text-white",
};

// --- CONTEXT DEFINITIONS ---

const AuthContext = React.createContext(null);
const useAuth = () => React.useContext(AuthContext);

const CartContext = React.createContext(null);
const useCart = () => React.useContext(CartContext);

const NotificationContext = React.createContext(null);
const useNotification = () => React.useContext(NotificationContext);

// --- ICON COMPONENTS ---

const User = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>;
const ShoppingCart = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="8" cy="21" r="1"></circle><circle cx="19" cy="21" r="1"></circle><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57L23 6H6"></path></svg>;
const X = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>;
const Plus = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"></path><path d="M12 5v14"></path></svg>;
const Minus = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"></path></svg>;
const BookOpen = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>;
const Building = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="16" height="20" x="4" y="2" rx="2" ry="2"></rect><path d="M9 22v-4h6v4"></path><path d="M8 6h.01"></path><path d="M16 6h.01"></path><path d="M12 6h.01"></path><path d="M12 10h.01"></path><path d="M12 14h.01"></path><path d="M16 10h.01"></path><path d="M8 10h.01"></path><path d="M8 14h.01"></path><path d="M16 14h.01"></path></svg>;
const Users = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>;
const Calendar = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"></rect><line x1="16" x2="16" y1="2" y2="6"></line><line x1="8" x2="8" y1="2" y2="6"></line><line x1="3" x2="21" y1="10" y2="10"></line></svg>;
const CheckCircle = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>;
const Camera = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"></path><circle cx="12" cy="13" r="3"></circle></svg>;
const MessageSquare = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>;

// --- UI COMPONENTS ---

const Button = ({ children, variant = "default", className = "", ...props }) => (
  <button className={cn(buttonVariants[variant], "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none disabled:opacity-50 disabled:cursor-not-allowed", className)} {...props}>
    {children}
  </button>
);

const Card = ({ children, className = "" }) => (
  <div className={cn(cardVariants.default, className)}>
    {children}
  </div>
);

const Modal = ({ isOpen, onClose, children, title }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-700 rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto text-white" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-xl font-semibold text-blue-400">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X /></button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};

const LoadingSpinner = () => <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>;

const Toast = ({ message, type = "success", onClose }) => (
  <div className={cn("fixed top-20 right-4 p-4 rounded-md shadow-lg z-50 text-white", type === "success" ? "bg-green-600" : "bg-red-600")}>
    <div className="flex items-center justify-between">
      <span>{message}</span>
      <button onClick={onClose} className="ml-4 text-white hover:text-gray-200"><X /></button>
    </div>
  </div>
);

// --- AUTHENTICATION COMPONENTS ---

const LoginModal = ({ isOpen, onClose, onSuccess }) => {
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
      const response = await fetch('http://localhost:8001/api/v1/auth/login', {
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
    <Modal isOpen={isOpen} onClose={onClose} title="Login to Your Account">
      <form onSubmit={handleLogin} className="space-y-4">
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full px-3 py-2 border border-gray-600 bg-gray-800 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required />
        <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full px-3 py-2 border border-gray-600 bg-gray-800 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner /> : 'Login'}
        </Button>
      </form>
    </Modal>
  );
};

const SignupModal = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({ name: '', email: '', password: '', confirmPassword: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const showNotification = useNotification();

  const handleSignup = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await fetch('http://localhost:8001/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: formData.name, email: formData.email, password: formData.password })
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
    <Modal isOpen={isOpen} onClose={onClose} title="Create an Account">
      <form onSubmit={handleSignup} className="space-y-4">
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <input type="text" placeholder="Full Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} className="w-full px-3 py-2 border border-gray-600 bg-gray-800 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required />
        <input type="email" placeholder="Email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} className="w-full px-3 py-2 border border-gray-600 bg-gray-800 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required />
        <input type="password" placeholder="Password" value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} className="w-full px-3 py-2 border border-gray-600 bg-gray-800 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required />
        <input type="password" placeholder="Confirm Password" value={formData.confirmPassword} onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })} className="w-full px-3 py-2 border border-gray-600 bg-gray-800 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner /> : 'Sign Up'}
        </Button>
      </form>
    </Modal>
  );
};

// --- E-COMMERCE / APPLICATION FEE COMPONENTS ---

const CartModal = ({ isOpen, onClose }) => {
    const { cart, updateQuantity, removeFromCart, clearCart } = useCart();
    const showNotification = useNotification();
    const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

    const handleCheckout = () => {
        if (cart.length === 0) {
            showNotification("Your cart is empty.", "error");
            return;
        }
        // In a real app, this would redirect to a payment gateway
        showNotification("Proceeding to checkout!", "success");
        clearCart();
        onClose();
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Application Fee Cart">
            {cart.length === 0 ? (
                <p className="text-gray-400">Your cart is empty.</p>
            ) : (
                <div className="space-y-4">
                    {cart.map(item => (
                        <div key={item.id} className="flex items-center justify-between p-2 bg-gray-800 rounded">
                            <div>
                                <p className="font-semibold">{item.name}</p>
                                <p className="text-sm text-gray-400">${item.price.toFixed(2)}</p>
                            </div>
                            <div className="flex items-center space-x-2">
                                <Button variant="ghost" size="sm" onClick={() => updateQuantity(item.id, item.quantity - 1)} disabled={item.quantity <= 1}><Minus /></Button>
                                <span>{item.quantity}</span>
                                <Button variant="ghost" size="sm" onClick={() => updateQuantity(item.id, item.quantity + 1)}><Plus /></Button>
                                <Button variant="destructive" size="sm" onClick={() => removeFromCart(item.id)}><X /></Button>
                            </div>
                        </div>
                    ))}
                    <div className="pt-4 border-t border-gray-700 text-right">
                        <p className="text-lg font-bold">Total: ${total.toFixed(2)}</p>
                    </div>
                    <Button onClick={handleCheckout} className="w-full mt-4">
                        Proceed to Payment
                    </Button>
                </div>
            )}
        </Modal>
    );
};

// --- HEADER COMPONENT ---

const Header = () => {
  const { user, logout, login } = useAuth(); // Destructure 'login' here
  const { cartCount } = useCart();
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [showCart, setShowCart] = useState(false);

  return (
    <>
      <header className="bg-black/80 backdrop-blur-sm border-b border-gray-800 sticky top-0 z-40 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <BookOpen className="h-8 w-8 text-blue-400" />
              <h1 className="text-xl font-bold text-blue-400 ml-2">PSG College of Technology Portal</h1>
            </div>
            <nav className="hidden md:flex items-center space-x-6">
                <a href="#programs" className="text-gray-300 hover:text-blue-400 transition-colors">Programs</a>
                <a href="#admissions" className="text-gray-300 hover:text-blue-400 transition-colors">Admissions</a>
                <a href="#campus" className="text-gray-300 hover:text-blue-400 transition-colors">Campus Life</a>
                <a href="#faculty" className="text-gray-300 hover:text-blue-400 transition-colors">Faculty</a>
            </nav>
            <div className="flex items-center space-x-4">
              <button onClick={() => setShowCart(true)} className="relative text-gray-300 hover:text-blue-400">
                <ShoppingCart />
                {cartCount > 0 && (
                  <span className="absolute -top-2 -right-2 bg-blue-600 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                    {cartCount}
                  </span>
                )}
              </button>
              {user ? (
                <div className="flex items-center space-x-4">
                  <span className="text-gray-300 hidden sm:block">
                    Hi, {user.name?.split(' ')[0] || 'User'}
                  </span>
                  <Button variant="outline" onClick={logout}>Logout</Button>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <Button variant="ghost" onClick={() => setShowLogin(true)}>Login</Button>
                  <Button onClick={() => setShowSignup(true)}>Sign Up</Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>
      <LoginModal isOpen={showLogin} onClose={() => setShowLogin(false)} onSuccess={login} />
      <SignupModal isOpen={showSignup} onClose={() => setShowSignup(false)} onSuccess={login} />
      <CartModal isOpen={showCart} onClose={() => setShowCart(false)} />
    </>
  );
};

// --- FEATURE COMPONENTS ---

const HeroSection = () => (
    <section
        className="relative bg-black text-white py-40 px-4 sm:px-6 lg:px-8 text-center flex items-center justify-center bg-cover bg-center"
        style={{ backgroundImage: "url('https://placehold.co/1920x1080/1a202c/718096/png?text=PSG+College+Entrance+Gate')" }}
    >
        <div className="absolute inset-0 bg-black bg-opacity-60"></div>
        <div className="relative z-10">
            <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-cyan-300">
                Shape Your Future at PSG College of Technology
            </h1>
            <p className="text-lg md:text-xl text-gray-300 max-w-3xl mx-auto mb-8">
                The central hub for prospective and current students. Explore programs, campus life, and begin your journey with us today.
            </p>
            <div className="space-x-4">
                <a href="#programs"><Button className="px-8 py-3 text-lg">Explore Programs</Button></a>
                <a href="#admissions"><Button variant="outline" className="px-8 py-3 text-lg">Apply Now</Button></a>
            </div>
        </div>
    </section>
);

const ProgramCatalog = () => {
    const [programs, setPrograms] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({ department: 'All', level: 'All', session: 'All' });

    const MOCK_PROGRAMS = [
        { id: 1, name: 'B.Sc. Computer Science', department: 'Engineering', level: 'Bachelor\'s', session: 'Fall 2024', tuition: 15000, faculty: 'Dr. Alan Turing' },
        { id: 2, name: 'M.A. Psychology', department: 'Arts & Humanities', level: 'Master\'s', session: 'Fall 2024', tuition: 12000, faculty: 'Dr. Jean Piaget' },
        { id: 3, name: 'B.Eng. Mechanical Engineering', department: 'Engineering', level: 'Bachelor\'s', session: 'Spring 2025', tuition: 16000, faculty: 'Dr. Ada Lovelace' },
        { id: 4, name: 'Ph.D. Cognitive Neuroscience', department: 'Psychology', level: 'Doctorate', session: 'Fall 2024', tuition: 18000, faculty: 'Dr. Carl Sagan' },
        { id: 5, name: 'B.A. Business Administration', department: 'Business', level: 'Bachelor\'s', session: 'Fall 2024', tuition: 14000, faculty: 'Dr. Peter Drucker' },
        { id: 6, name: 'M.Sc. Data Science', department: 'Engineering', level: 'Master\'s', session: 'Spring 2025', tuition: 17500, faculty: 'Dr. Grace Hopper' },
    ];

    useEffect(() => {
        setLoading(true);
        setTimeout(() => {
            setPrograms(MOCK_PROGRAMS);
            setLoading(false);
        }, 1000);
    }, []);

    const filteredPrograms = useMemo(() => programs.filter(p => 
        (filters.department === 'All' || p.department === filters.department) &&
        (filters.level === 'All' || p.level === filters.level) &&
        (filters.session === 'All' || p.session === filters.session)
    ), [programs, filters]);

    const handleFilterChange = (e) => {
        setFilters(prev => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const FilterSelect = ({ name, options, value }) => (
        <select name={name} value={value} onChange={handleFilterChange} className="bg-gray-800 border border-gray-600 rounded-md px-3 py-2 text-white focus:ring-blue-500 focus:border-blue-500">
            {options.map(opt => <option key={opt} value={opt}>{opt}</option>)}
        </select>
    );

    return (
        <section id="programs" className="py-20 bg-black">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <h2 className="text-4xl font-bold text-center text-blue-400 mb-4">Academic Programs</h2>
                <p className="text-center text-gray-400 mb-12 max-w-2xl mx-auto">Filter our comprehensive catalog to find the program that's right for you.</p>
                <div className="flex flex-wrap justify-center gap-4 mb-12">
                    <FilterSelect name="department" value={filters.department} options={['All', 'Engineering', 'Arts & Humanities', 'Psychology', 'Business']} />
                    <FilterSelect name="level" value={filters.level} options={['All', 'Bachelor\'s', 'Master\'s', 'Doctorate']} />
                    <FilterSelect name="session" value={filters.session} options={['All', 'Fall 2024', 'Spring 2025']} />
                </div>
                {loading ? (
                    <div className="flex justify-center"><LoadingSpinner /></div>
                ) : (
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {filteredPrograms.map(p => (
                            <Card key={p.id} className="p-6 flex flex-col hover:border-blue-500 transition-all transform hover:-translate-y-1">
                                <h3 className="text-xl font-semibold text-blue-400 mb-2">{p.name}</h3>
                                <p className="text-gray-400 mb-1">Department: {p.department}</p>
                                <p className="text-gray-400 mb-4">Level: {p.level}</p>
                                <div className="mt-auto pt-4 border-t border-gray-700">
                                    <p className="font-semibold">Tuition: ${p.tuition}/year</p>
                                    <p className="text-sm text-gray-500">Faculty Highlight: {p.faculty}</p>
                                </div>
                            </Card>
                        ))}
                    </div>
                )}
            </div>
        </section>
    );
};

const AdmissionsGuide = () => {
    const steps = [
        { name: 'Submit Online Application', description: 'Complete your personal, academic, and extracurricular details.' },
        { name: 'Upload Required Documents', description: 'Transcripts, recommendation letters, and personal statement.' },
        { name: 'Schedule an Interview', description: 'Meet with our admissions committee to discuss your goals.' },
        { name: 'Pay Application Fee', description: 'Finalize your application with a one-time fee.' },
        { name: 'Receive Admission Decision', description: 'Check your portal for updates on your application status.' },
    ];
    const { addToCart } = useCart();
    const applicationFee = { id: 'app-fee-ug', name: 'Undergraduate Application Fee', price: 75 };

    return (
        <section id="admissions" className="py-20 bg-gray-900">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <h2 className="text-4xl font-bold text-center text-blue-400 mb-12">Step-by-Step Admissions Guide</h2>
                <div className="max-w-3xl mx-auto">
                    {steps.map((step, index) => (
                        <div key={index} className="flex items-start space-x-4 mb-6">
                            <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
                                {index + 1}
                            </div>
                            <div>
                                <h3 className="text-xl font-semibold text-white">{step.name}</h3>
                                <p className="text-gray-400">{step.description}</p>
                                {step.name === 'Pay Application Fee' && (
                                    <Button onClick={() => addToCart(applicationFee)} className="mt-2">Add Fee to Cart</Button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

const CampusTour = () => {
    const categories = {
        'Academic Buildings': ['PSG+Main+Building', 'PSG+Library', 'PSG+Laboratory'],
        'Student Life': ['PSG+Student+Center', 'PSG+Campus+Cafe', 'PSG+Common+Room'],
        'Athletics': ['PSG+Gymnasium', 'PSG+Sports+Grounds', 'PSG+Indoor+Stadium'],
        'Dormitories': ['PSG+Hostel+Room', 'PSG+Hostel+Lounge', 'PSG+Hostel+Exterior'],
    };
    const [activeCategory, setActiveCategory] = useState('Academic Buildings');

    return (
        <section id="campus" className="py-20 bg-black">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <h2 className="text-4xl font-bold text-center text-blue-400 mb-12">Immersive Campus Virtual Tour</h2>
                <div className="flex justify-center space-x-2 md:space-x-4 mb-8">
                    {Object.keys(categories).map(cat => (
                        <Button key={cat} variant={activeCategory === cat ? 'default' : 'outline'} onClick={() => setActiveCategory(cat)}>
                            {cat}
                        </Button>
                    ))}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {categories[activeCategory].map((img, index) => (
                        <div key={index} className="aspect-w-16 aspect-h-9 rounded-lg overflow-hidden group">
                            <img src={`https://placehold.co/600x400/1a202c/718096/png?text=${img}`} alt={`${activeCategory} view ${index + 1}`} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                            <div className="absolute inset-0 bg-black bg-opacity-20 group-hover:bg-opacity-0 transition-all"></div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

const FacultyDirectory = () => {
    const [faculty, setFaculty] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [department, setDepartment] = useState('All');

    const MOCK_FACULTY = [
        { id: 1, name: 'Dr. Evelyn Reed', department: 'Psychology', research: 'Cognitive Neuroscience, Memory', publications: 32, email: 'e.reed@psgtech.edu' },
        { id: 2, name: 'Prof. Samuel Chen', department: 'Engineering', research: 'Machine Learning, AI Ethics', publications: 45, email: 's.chen@psgtech.edu' },
        { id: 3, name: 'Dr. Maria Garcia', department: 'Arts & Humanities', research: 'Post-colonial Literature', publications: 18, email: 'm.garcia@psgtech.edu' },
        { id: 4, name: 'Prof. Ben Carter', department: 'Business', research: 'Sustainable Business Models', publications: 25, email: 'b.carter@psgtech.edu' },
    ];

    useEffect(() => {
        setLoading(true);
        setTimeout(() => {
            setFaculty(MOCK_FACULTY);
            setLoading(false);
        }, 500);
    }, []);

    const filteredFaculty = faculty.filter(f =>
        (f.name.toLowerCase().includes(search.toLowerCase())) &&
        (department === 'All' || f.department === department)
    );

    return (
        <section id="faculty" className="py-20 bg-gray-900">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <h2 className="text-4xl font-bold text-center text-blue-400 mb-12">Searchable Faculty Directory</h2>
                <div className="flex flex-col md:flex-row gap-4 mb-8 max-w-2xl mx-auto">
                    <input type="text" placeholder="Search by name..." value={search} onChange={e => setSearch(e.target.value)} className="w-full px-4 py-2 border border-gray-600 bg-gray-800 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-white" />
                    <select value={department} onChange={e => setDepartment(e.target.value)} className="w-full md:w-1/3 px-4 py-2 border border-gray-600 bg-gray-800 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-white">
                        <option>All</option>
                        <option>Psychology</option>
                        <option>Engineering</option>
                        <option>Arts & Humanities</option>
                        <option>Business</option>
                    </select>
                </div>
                {loading ? <div className="flex justify-center"><LoadingSpinner /></div> : (
                    <div className="grid md:grid-cols-2 gap-6">
                        {filteredFaculty.map(f => (
                            <Card key={f.id} className="p-6">
                                <h3 className="text-xl font-semibold text-blue-400">{f.name}</h3>
                                <p className="text-gray-400">{f.department} Department</p>
                                <p className="mt-2 text-sm"><strong className="text-gray-300">Research:</strong> {f.research}</p>
                                <p className="text-sm"><strong className="text-gray-300">Publications:</strong> {f.publications}</p>
                                <a href={`mailto:${f.email}`} className="text-blue-500 hover:underline text-sm mt-2 inline-block">Contact</a>
                            </Card>
                        ))}
                    </div>
                )}
            </div>
        </section>
    );
};

const EventsCalendar = () => {
    const events = [
        { date: 'Oct 15', type: 'Academic Deadline', title: 'Fall 2024 Application Deadline' },
        { date: 'Oct 22', type: 'Workshop', title: 'AI in Modern Research Workshop' },
        { date: 'Nov 05', type: 'Guest Lecture', title: 'Guest Lecture by Dr. Jane Goodall' },
        { date: 'Nov 18', type: 'Cultural Festival', title: 'Annual International Food Festival' },
    ];

    return (
        <section id="events" className="py-20 bg-black">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <h2 className="text-4xl font-bold text-center text-blue-400 mb-12">Dynamic Events & Academic Calendar</h2>
                <div className="space-y-6">
                    {events.map((event, index) => (
                        <Card key={index} className="p-4 flex items-center space-x-4">
                            <div className="text-center flex-shrink-0">
                                <p className="text-2xl font-bold text-blue-400">{event.date?.split(' ')[1] || 'TBD'}</p>
                                <p className="text-sm text-gray-400">{event.date?.split(' ')[0] || 'Date'}</p>
                            </div>
                            <div className="border-l border-gray-700 pl-4">
                                <span className="text-xs bg-blue-900 text-blue-300 px-2 py-1 rounded-full">{event.type}</span>
                                <h3 className="text-lg font-semibold text-white mt-1">{event.title}</h3>
                            </div>
                        </Card>
                    ))}
                </div>
            </div>
        </section>
    );
};

const Testimonials = () => {
    const testimonials = [
        { name: 'John Doe', major: 'Business, 2022', quote: 'The business program gave me the practical skills and network to launch my startup right after graduation. The faculty are true mentors.' },
        { name: 'Jane Smith', major: 'Computer Science, 2023', quote: 'I had access to state-of-the-art labs and research opportunities that led to an amazing job at a top tech company.' },
    ];

    return (
        <section id="testimonials" className="py-20 bg-gray-900">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <h2 className="text-4xl font-bold text-center text-blue-400 mb-12">Student & Alumni Voices</h2>
                <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                    {testimonials.map((t, i) => (
                        <Card key={i} className="p-8 text-center">
                            <MessageSquare className="mx-auto h-10 w-10 text-blue-500 mb-4" />
                            <p className="text-gray-300 italic">"{t.quote}"</p>
                            <p className="mt-4 font-semibold text-white">- {t.name}</p>
                            <p className="text-sm text-blue-400">{t.major}</p>
                        </Card>
                    ))}
                </div>
            </div>
        </section>
    );
};

const Footer = () => (
    <footer className="bg-black border-t border-gray-800 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-500">
            <p>Established 1951 &copy; {new Date().getFullYear()} PSG College of Technology. All Rights Reserved.</p>
            <p className="text-sm mt-2">college-provide-information-940578</p>
        </div>
    </footer>
);

// --- MAIN APP COMPONENT ---

const App = () => {
  const [user, setUser] = useState(null);
  const [cart, setCart] = useState([]);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const showNotification = (message, type = 'success') => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 3000);
  };

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    showNotification('Login successful!', 'success');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    showNotification('Logged out successfully', 'success');
  };

  const addToCart = (product) => {
    setCart(prev => {
      const existing = prev.find(item => item.id === product.id);
      if (existing) {
        return prev.map(item => item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item);
      }
      return [...prev, { ...product, quantity: 1 }];
    });
    showNotification(`Added ${product.name} to cart!`, 'success');
  };

  const removeFromCart = (productId) => {
    setCart(prev => prev.filter(item => item.id !== productId));
    showNotification('Item removed from cart.', 'success');
  };

  const updateQuantity = (productId, quantity) => {
    if (quantity < 1) {
      removeFromCart(productId);
      return;
    }
    setCart(prev => prev.map(item => item.id === productId ? { ...item, quantity } : item));
  };
  
  const clearCart = () => {
    setCart([]);
  };

  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  const authContextValue = { user, login: handleLoginSuccess, logout: handleLogout };
  const cartContextValue = { cart, addToCart, removeFromCart, updateQuantity, clearCart, cartCount };

  return (
    <AuthContext.Provider value={authContextValue}>
      <CartContext.Provider value={cartContextValue}>
        <NotificationContext.Provider value={showNotification}>
          <div className="min-h-screen bg-black font-sans">
            <Header />
            <main>
              <HeroSection />
              <ProgramCatalog />
              <AdmissionsGuide />
              <CampusTour />
              <FacultyDirectory />
              <EventsCalendar />
              <Testimonials />
            </main>
            <Footer />
            <div className="fixed top-4 right-4 z-50 space-y-2">
              {notifications.map(n => (
                <Toast key={n.id} message={n.message} type={n.type} onClose={() => setNotifications(prev => prev.filter(item => item.id !== n.id))} />
              ))}
            </div>
          </div>
        </NotificationContext.Provider>
      </CartContext.Provider>
    </AuthContext.Provider>
  );
};

export default App;