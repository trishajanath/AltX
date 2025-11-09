import React, { useState, useEffect, useRef } from 'react';
// Safe fallbacks for all framer-motion functionality
console.log('Setting up Framer Motion fallbacks...');

// Fallback motion component that filters out animation props and renders regular HTML elements
const createMotionFallback = (element) => ({ 
  children, 
  className, 
  style, 
  onClick, 
  id,
  // Filter out all framer-motion specific props
  initial, 
  animate, 
  exit, 
  whileHover, 
  whileTap, 
  whileInView,
  // some generators use lowercase variants by mistake
  whileinview,
  whileFocus,
  whileDrag,
  transition,
  variants,
  custom,
  inherit,
  layout,
  layoutId,
  onAnimationStart,
  onAnimationComplete,
  onUpdate,
  onDrag,
  onDragStart,
  onDragEnd,
  onHoverStart,
  onHoverEnd,
  onTap,
  onTapStart,
  onTapCancel,
  onFocus,
  onBlur,
  onViewportEnter,
  onViewportLeave,
  ...validProps 
}) => React.createElement(element, { className, style, onClick, id, ...validProps }, children);

const motion = {
  div: createMotionFallback('div'),
  span: createMotionFallback('span'),
  section: createMotionFallback('section'),
  h1: createMotionFallback('h1'),
  button: createMotionFallback('button'),
  p: createMotionFallback('p'),
};

// Fallback hooks that return safe default values
const useScroll = () => ({ 
  scrollYProgress: { 
    get: () => 0,
    onChange: () => {},
    set: () => {},
    stop: () => {},
    destroy: () => {}
  } 
});

const useTransform = (source, inputRange, outputRange) => {
  // Return a mock MotionValue that always returns the first output value
  return {
    get: () => outputRange ? outputRange[0] : 0,
    set: () => {},
    onChange: () => {},
    stop: () => {},
    destroy: () => {}
  };
};

// Safe fallback component for AnimatePresence
const SafeAnimatePresence = ({ children, mode, ...props }) => {
  return <div {...props}>{children}</div>;
};

// UTILITY: Classname merger (mimics shadcn/ui's cn)
const cn = (...inputs) => {
  return inputs.filter(Boolean).join(' ');
};

// UTILITY: Component Variants (mimics shadcn/ui)
const buttonVariants = {
  default: "bg-purple-600 text-white hover:bg-purple-700 shadow-lg shadow-purple-500/30",
  destructive: "bg-red-500 text-white hover:bg-red-600",
  outline: "border border-white/20 bg-white/10 hover:bg-white/20 backdrop-blur-sm",
  secondary: "bg-pink-500 text-white hover:bg-pink-600",
  ghost: "hover:bg-white/10",
  link: "text-primary underline-offset-4 hover:underline",
};

const cardVariants = {
  default: "bg-white/5 backdrop-blur-lg border border-white/10 rounded-2xl shadow-2xl shadow-black/20",
};

// --- CONTEXT DEFINITIONS ---

// AUTHENTICATION CONTEXT (ALWAYS INCLUDE)
const AuthContext = React.createContext(null);
const useAuth = () => React.useContext(AuthContext);

// CART CONTEXT (E-COMMERCE)
const CartContext = React.createContext(null);
const useCart = () => React.useContext(CartContext);

// NOTIFICATION CONTEXT (ALWAYS INCLUDE)
const NotificationContext = React.createContext(null);
const useNotification = () => React.useContext(NotificationContext);


// --- PROVIDER COMPONENTS ---

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const storedToken = localStorage.getItem('token');
      const storedUser = localStorage.getItem('user');
      if (storedToken) {
        setToken(storedToken);
      }
      if (storedUser && storedUser !== 'undefined' && storedUser !== 'null') {
        try {
          const parsed = JSON.parse(storedUser);
          setUser(parsed);
        } catch (e) {
          console.warn('Stored user is not valid JSON, clearing user:', storedUser);
          localStorage.removeItem('user');
        }
      }
    } catch (error) {
      console.error("Failed to access localStorage", error);
      // don't aggressively clear all storage; remove problematic keys only
      localStorage.removeItem('user');
      localStorage.removeItem('token');
    } finally {
      setLoading(false);
    }
  }, []);

  const login = (userData, accessToken) => {
    localStorage.setItem('token', accessToken);
    localStorage.setItem('user', JSON.stringify(userData));
    setToken(accessToken);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  const value = { user, token, login, logout, loading, isAuthenticated: !!token };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

const CartProvider = ({ children }) => {
  const [cart, setCart] = useState([]);
  const showNotification = useNotification();

  const addToCart = (product, quantity = 1) => {
    setCart(prev => {
      const existingItem = prev.find(item => item.id === product.id);
      if (existingItem) {
        return prev.map(item =>
          item.id === product.id ? { ...item, quantity: item.quantity + quantity } : item
        );
      }
      return [...prev, { ...product, quantity }];
    });
    if (showNotification) {
        showNotification(`${product.name} added to cart`, 'success');
    }
  };

  const updateQuantity = (productId, newQuantity) => {
    setCart(prev => {
      if (newQuantity <= 0) {
        return prev.filter(item => item.id !== productId);
      }
      return prev.map(item =>
        item.id === productId ? { ...item, quantity: newQuantity } : item
      );
    });
  };

  const clearCart = () => setCart([]);
  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);
  const cartTotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

  const value = { cart, addToCart, updateQuantity, clearCart, cartCount, cartTotal };
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};

const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);

  const showNotification = (message, type = 'success', duration = 3000) => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, duration);
  };

  return (
    <NotificationContext.Provider value={showNotification}>
      {children}
      <div className="fixed top-5 right-5 z-[100] space-y-2">
        <SafeAnimatePresence mode="popLayout">
          {notifications.map(note => (
            <Toast key={note.id} message={note.message} type={note.type} />
          ))}
        </SafeAnimatePresence>
      </div>
    </NotificationContext.Provider>
  );
};


// --- ICON COMPONENTS ---

const User = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>;
const ShoppingCart = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="8" cy="21" r="1"></circle><circle cx="19" cy="21" r="1"></circle><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57L23 6H6"></path></svg>;
const X = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>;
const Plus = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"></path><path d="M12 5v14"></path></svg>;
const Minus = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"></path></svg>;
const Search = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>;
const Clock = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>;
const Zap = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>;
const Repeat = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 2.1l4 4-4 4"/><path d="M3 12.6A9 9 0 0 1 12 3a9 9 0 0 1 9 9"/><path d="M7 21.9l-4-4 4-4"/><path d="M21 11.4A9 9 0 0 1 12 21a9 9 0 0 1-9-9"/></svg>;


// --- UI COMPONENTS ---

const Button = ({ children, variant = "default", className = "", ...props }) => (
  <button className={cn(
    "inline-flex items-center justify-center rounded-full px-6 py-3 text-base font-semibold transition-all duration-300 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/50 disabled:opacity-50 disabled:cursor-not-allowed transform hover:-translate-y-1 hover:scale-105",
    buttonVariants[variant],
    className
  )} {...props}>
    {children}
  </button>
);

const Card = ({ children, className = "", variant = "default" }) => (
  <div className={cn(cardVariants[variant], className)}>
    {children}
  </div>
);

const Modal = ({ isOpen, onClose, children, title }) => (
  <SafeAnimatePresence>
    {isOpen && (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, y: 20 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.9, y: 20 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="bg-slate-800/80 backdrop-blur-xl border border-white/10 rounded-2xl max-w-md w-full max-h-[90vh] overflow-y-auto text-white shadow-2xl shadow-purple-500/10"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between p-6 border-b border-white/10">
            <h2 className="text-2xl font-bold tracking-tight">{title}</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors rounded-full p-1 hover:bg-white/10">
              <X />
            </button>
          </div>
          <div className="p-6">{children}</div>
        </motion.div>
      </motion.div>
    )}
  </SafeAnimatePresence>
);

const LoadingSpinner = () => (
  <div className="w-6 h-6 border-4 border-white/20 border-t-purple-500 rounded-full animate-spin"></div>
);

const Toast = ({ message, type = "success" }) => (
    <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -20, scale: 0.9 }}
        className={cn(
            "p-4 rounded-xl shadow-lg text-white flex items-center space-x-3 border",
            type === "success" ? "bg-green-500/80 border-green-400/50" : "bg-red-500/80 border-red-400/50",
            "backdrop-blur-md"
        )}
    >
        <span>{message}</span>
    </motion.div>
);

const Input = React.forwardRef(({ className, ...props }, ref) => (
    <input
        ref={ref}
        className={cn(
            "w-full px-4 py-3 bg-slate-700/50 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all duration-300 placeholder:text-gray-400",
            className
        )}
        {...props}
    />
));


// --- AUTHENTICATION COMPONENTS ---

const LoginModal = ({ isOpen, onClose }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
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
        login(data.user, data.access_token);
        showNotification('Login successful!', 'success');
        onClose();
      } else {
        setError(data.detail || 'Login failed. Please check your credentials.');
      }
    } catch (err) {
      setError('Network error. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Welcome Back">
      <form onSubmit={handleLogin} className="space-y-6">
        {error && <div className="text-red-400 text-sm bg-red-500/10 p-3 rounded-lg">{error}</div>}
        <Input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <Input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner /> : 'Login'}
        </Button>
      </form>
    </Modal>
  );
};

const SignupModal = ({ isOpen, onClose }) => {
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
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
        login(data.user, data.access_token);
        showNotification('Account created successfully!', 'success');
        onClose();
      } else {
        setError(data.detail || 'Registration failed. Please try again.');
      }
    } catch (err) {
      setError('Network error. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Your Account">
      <form onSubmit={handleSignup} className="space-y-6">
        {error && <div className="text-red-400 text-sm bg-red-500/10 p-3 rounded-lg">{error}</div>}
        <Input type="text" placeholder="Full Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
        <Input type="email" placeholder="Email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} required />
        <Input type="password" placeholder="Password" value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} required />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner /> : 'Sign Up'}
        </Button>
      </form>
    </Modal>
  );
};


// --- E-COMMERCE COMPONENTS ---

const CartModal = ({ isOpen, onClose }) => {
    const { cart, updateQuantity, cartCount, cartTotal } = useCart();

    if (!isOpen) return null;

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={`Your Cart (${cartCount})`}>
            {cart.length === 0 ? (
                <div className="text-center py-10">
                    <ShoppingCart className="mx-auto h-16 w-16 text-gray-500" />
                    <p className="mt-4 text-gray-400">Your cart is empty.</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {cart.map(item => (
                        <div key={item.id} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                            <div className="flex items-center space-x-4">
                                <img src={item.image} alt={item.name} className="w-16 h-16 rounded-md object-cover" />
                                <div>
                                    <p className="font-semibold">{item.name}</p>
                                    <p className="text-sm text-gray-400">${item.price.toFixed(2)}</p>
                                </div>
                            </div>
                            <div className="flex items-center space-x-3">
                                <button onClick={() => updateQuantity(item.id, item.quantity - 1)} className="p-1 rounded-full bg-slate-600 hover:bg-slate-500 transition-colors"><Minus className="w-4 h-4" /></button>
                                <span>{item.quantity}</span>
                                <button onClick={() => updateQuantity(item.id, item.quantity + 1)} className="p-1 rounded-full bg-slate-600 hover:bg-slate-500 transition-colors"><Plus className="w-4 h-4" /></button>
                            </div>
                        </div>
                    ))}
                    <div className="pt-4 border-t border-white/10">
                        <div className="flex justify-between items-center text-lg font-bold">
                            <span>Total</span>
                            <span>${cartTotal.toFixed(2)}</span>
                        </div>
                        <Button className="w-full mt-4">Proceed to Checkout</Button>
                    </div>
                </div>
            )}
        </Modal>
    );
};


// --- PAGE SECTIONS & LAYOUT COMPONENTS ---

const Header = ({ onLogin, onSignup, onCartClick }) => {
  const { isAuthenticated, user, logout } = useAuth();
  const { cartCount } = useCart();
  const showNotification = useNotification();
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 10);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleLogout = () => {
    logout();
    showNotification('Logged out successfully', 'success');
  };

  return (
    <header className={cn(
      "fixed top-0 left-0 right-0 z-40 transition-all duration-300",
      isScrolled ? "bg-slate-900/50 backdrop-blur-lg border-b border-white/10" : "bg-transparent"
    )}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold tracking-tighter text-white bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">
              GrocerEase
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <button onClick={onCartClick} className="relative text-gray-300 hover:text-white transition-colors">
              <ShoppingCart />
              <SafeAnimatePresence>
                {cartCount > 0 && (
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    exit={{ scale: 0 }}
                    className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-bold"
                  >
                    {cartCount}
                  </motion.span>
                )}
              </SafeAnimatePresence>
            </button>
            {isAuthenticated ? (
              <div className="flex items-center space-x-4">
                <span className="text-gray-300 hidden sm:block">Hi, {(user && typeof user.name === 'string') ? user.name.split(' ')[0] : 'User'}</span>
                <Button variant="outline" onClick={handleLogout} className="px-4 py-2 text-sm">Logout</Button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Button variant="ghost" onClick={onLogin} className="hidden sm:inline-flex">Login</Button>
                <Button onClick={onSignup}>Sign Up</Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

const HeroSection = ({ onSignup }) => {
    const { isAuthenticated } = useAuth();
    const ref = useRef(null);
    const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
    const y = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);

    return (
        <section ref={ref} className="relative h-screen flex items-center justify-center text-white overflow-hidden">
            <motion.div
                style={{ y }}
                className="absolute inset-0 bg-gradient-to-br from-purple-600 via-pink-500 to-red-500 z-0"
            />
            <div className="absolute inset-0 bg-slate-900/60 z-0" />
            <div className="absolute inset-0 bg-gradient-radial from-transparent via-transparent to-slate-900 z-0" />
            
            <div className="relative z-10 text-center p-4">
                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                    className="text-5xl md:text-7xl font-bold tracking-tight mb-6"
                >
                    Grocery Shopping, Reimagined.
                </motion.h1>
                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.4 }}
                    className="max-w-2xl mx-auto text-lg md:text-xl text-gray-300 leading-relaxed mb-10"
                >
                    For busy professionals who value their time. Get fresh groceries delivered precisely when you need them.
                </motion.p>
                {!isAuthenticated && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.6 }}
                    >
                        <Button onClick={onSignup} className="px-8 py-4 text-lg">
                            Start Saving Time Today
                        </Button>
                    </motion.div>
                )}
            </div>
        </section>
    );
};

const features = [
    { icon: <Search />, title: "AI-Powered Smart Search", description: "Find items by dietary needs, recipe, or nutritional content instantly." },
    { icon: <Repeat />, title: "Persistent Cart & 'Buy Again'", description: "Your cart saved across devices, with one-click reordering for your staples." },
    { icon: <Zap />, title: "Recipe-to-Cart", description: "Find a recipe you love? Add all ingredients to your cart in a single click." },
    { icon: <Clock />, title: "Real-Time Delivery Slots", description: "Book a precise 1-hour delivery window that fits your packed schedule." },
];

const FeaturesSection = () => {
    const containerVariants = {
        hidden: {},
        visible: {
            transition: {
                staggerChildren: 0.2,
            },
        },
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 50 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } },
    };

    return (
        <section className="py-24 bg-slate-900 text-white relative">
            <div className="absolute top-0 left-0 w-full h-full bg-grid-white/[0.05]"></div>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                <div className="text-center mb-16">
                    <h2 className="text-4xl font-bold tracking-tight">Your Time is Valuable. We Get It.</h2>
                    <p className="mt-4 text-lg text-gray-400">Features designed to give you back your evenings and weekends.</p>
                </div>
                <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8"
                >
                    {features.map((feature, index) => (
                        <motion.div key={index} variants={itemVariants}>
                            <Card className="p-8 h-full text-center transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:shadow-purple-500/20 ring-1 ring-white/10 hover:ring-purple-500/50">
                                <div className="inline-block p-4 bg-purple-500/10 rounded-full mb-6 text-purple-400">
                                    {React.cloneElement(feature.icon, { className: "w-8 h-8" })}
                                </div>
                                <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                                <p className="text-gray-400 leading-relaxed">{feature.description}</p>
                            </Card>
                        </motion.div>
                    ))}
                </motion.div>
            </div>
        </section>
    );
};

const mockProducts = [
    { id: 1, name: 'Organic Avocados', price: 4.99, image: 'https://images.unsplash.com/photo-1587899798312-bs0a71153b35?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=600' },
    { id: 2, name: 'Artisanal Sourdough', price: 6.50, image: 'https://images.unsplash.com/photo-1589988833803-952b14f8274c?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=600' },
    { id: 3, name: 'Free-Range Eggs', price: 5.25, image: 'https://images.unsplash.com/photo-1598965675343-6b3683837233?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=600' },
    { id: 4, name: 'Oat Milk', price: 3.99, image: 'https://images.unsplash.com/photo-1631140357435-5a0b0a455a1a?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=600' },
];

const ProductShowcase = () => {
    const { isAuthenticated } = useAuth();
    const { addToCart } = useCart();

    if (!isAuthenticated) {
        return (
            <section className="py-24 bg-slate-800 text-center text-white">
                <h3 className="text-2xl font-bold">Login to Start Shopping</h3>
                <p className="text-gray-400 mt-2">Create an account to see our curated selection of fresh products.</p>
            </section>
        );
    }

    return (
        <section className="py-24 bg-slate-900 text-white">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <h2 className="text-4xl font-bold tracking-tight text-center mb-12">Weekly Staples</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                    {mockProducts.map(product => (
                        <Card key={product.id} className="overflow-hidden group transition-transform duration-300 hover:scale-105">
                            <img src={product.image} alt={product.name} className="w-full h-48 object-cover" />
                            <div className="p-6">
                                <h3 className="text-xl font-semibold">{product.name}</h3>
                                <p className="text-lg text-purple-400 font-bold mt-2">${product.price.toFixed(2)}</p>
                                <Button onClick={() => addToCart(product)} className="w-full mt-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                                    Add to Cart
                                </Button>
                            </div>
                        </Card>
                    ))}
                </div>
            </div>
        </section>
    );
};

const Footer = () => (
    <footer className="bg-slate-900 border-t border-white/10 text-gray-400">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8 text-center">
            <p className="text-2xl font-bold tracking-tighter text-white bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400 mb-4">
              GrocerEase
            </p>
            <p>&copy; {new Date().getFullYear()} web-provide-convenient-959883. All rights reserved.</p>
            <p className="mt-2 text-sm">Designed for the modern professional.</p>
        </div>
    </footer>
);


// --- MAIN APP COMPONENT ---

const App = () => {
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [showCart, setShowCart] = useState(false);

  return (
    <NotificationProvider>
      <AuthProvider>
        <CartProviderWrapper>
          <div className="font-sans bg-slate-900">
            <Header
              onLogin={() => setShowLogin(true)}
              onSignup={() => setShowSignup(true)}
              onCartClick={() => setShowCart(true)}
            />
            <main>
              <HeroSection onSignup={() => setShowSignup(true)} />
              <FeaturesSection />
              <ProductShowcase />
            </main>
            <Footer />

            <LoginModal isOpen={showLogin} onClose={() => setShowLogin(false)} />
            <SignupModal isOpen={showSignup} onClose={() => setShowSignup(false)} />
            <CartModal isOpen={showCart} onClose={() => setShowCart(false)} />
          </div>
        </CartProviderWrapper>
      </AuthProvider>
    </NotificationProvider>
  );
};

// Wrapper component to allow CartProvider to use useNotification
const CartProviderWrapper = ({ children }) => {
    return <CartProvider>{children}</CartProvider>;
};

export default App;