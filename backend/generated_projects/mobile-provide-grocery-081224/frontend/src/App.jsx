import React, { useState, useEffect, useRef } from 'react';

// UTILITY FOR COMBINING CLASSNAMES (like Shadcn/ui)
const cn = (...inputs) => {
  return inputs.filter(Boolean).join(' ');
};

// SAFE FRAMER-MOTION FALLBACKS (CRITICAL FOR BROWSER COMPATIBILITY):
const createMotionFallback = (element) => {
  const Component = ({ children, className, style, onClick, id, ...props }) => {
    // Filter out framer-motion specific props
    const validProps = Object.keys(props).reduce((acc, key) => {
      if (
!['initial', 'animate', 'exit', 'whileHover', 'whileTap', 'whileInView', 'transition', 'variants', 'viewport'].includes(key)
) {
        acc[key] = props[key];
      }
      return acc;
    }, {});
    return React.createElement(element, { className, style, onClick, id, ...validProps }, children);
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
  img: createMotionFallback('img'),
};

const AnimatePresence = ({ children }) => <>{children}</>;
const useInView = (ref, options) => {
  const [isInView, setIsInView] = useState(false);
  useEffect(() => {
    // Simple fallback: assume it's in view after a short delay to mimic animation trigger
    const timer = setTimeout(() => setIsInView(true), 100);
    return () => clearTimeout(timer);
  }, []);
  return [ref, isInView];
};

// CONTEXT DEFINITIONS
const AuthContext = React.createContext(null);
const useAuth = () => React.useContext(AuthContext);

const CartContext = React.createContext(null);
const useCart = () => React.useContext(CartContext);

const NotificationContext = React.createContext(null);
const useNotification = () => React.useContext(NotificationContext);

// API URL
const API_URL = 'http://localhost:8001/api/v1';

// MOCK DATA (for demonstration purposes)
const MOCK_MEAL_KITS = [
    { id: 1, name: '30-Min Tuscan Chicken', price: 24.99, image: 'https://images.unsplash.com/photo-1604382354936-07c5d9983d34?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=800&q=60', category: 'Meal Kit' },
    { id: 2, name: 'Vegan Chili Night', price: 19.99, image: 'https://images.unsplash.com/photo-1556742122-a2b95b0d6a2e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=800&q=60', category: 'Meal Kit' },
    { id: 3, name: 'Spicy Taco Tuesday Kit', price: 21.50, image: 'https://images.unsplash.com/photo-1552332386-f8dd00dc2f85?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=800&q=60', category: 'Meal Kit' },
    { id: 4, name: 'Fresh Pasta Carbonara', price: 28.00, image: 'https://images.unsplash.com/photo-1621996346565-e326b20f5413?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=800&q=60', category: 'Meal Kit' },
];

// ICON COMPONENTS
const UserIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>;
const ShoppingCartIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>;
const XIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>;
const PlusIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>;
const MinusIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line></svg>;
const ChevronRightIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>;

// UI COMPONENTS (SHADCN STYLE)
const Button = ({ children, variant = "default", className = "", ...props }) => {
    const baseClasses = "inline-flex items-center justify-center rounded-full text-sm font-bold ring-offset-background transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50";
    const variants = {
        default: "bg-white text-slate-900 hover:bg-gray-200 px-8 py-3",
        primary: "bg-white text-slate-900 hover:bg-gray-200 px-8 py-3",
        outline: "bg-white text-slate-900 hover:bg-gray-200 px-8 py-3",
        ghost: "hover:bg-gray-200 text-slate-900",
        link: "text-primary underline-offset-4 hover:underline",
    };
    return <button className={cn(baseClasses, variants[variant], className)} {...props}>{children}</button>;
};

const Modal = ({ isOpen, onClose, children, title }) => {
    if (!isOpen) return null;
    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={onClose}>
            <motion.div
                className="relative bg-black/80 backdrop-blur-lg border border-white/10 rounded-2xl max-w-md w-full max-h-[90vh] overflow-y-auto shadow-2xl shadow-purple-500/20"
                onClick={(e) => e.stopPropagation()}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
            >
                <div className="flex items-center justify-between p-6 border-b border-white/10">
                    <h2 className="text-xl font-bold text-white tracking-tight">{title}</h2>
                    <button onClick={onClose} className="text-white/50 hover:text-white transition-colors"><XIcon /></button>
                </div>
                <div className="p-6">{children}</div>
            </motion.div>
        </div>
    );
};

const LoadingSpinner = () => <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>;

const Toast = ({ message, type = "success", onClose }) => (
    <motion.div
        initial={{ opacity: 0, y: -20, x: '-50%' }}
        animate={{ opacity: 1, y: 0, x: '-50%' }}
        exit={{ opacity: 0, y: -20, x: '-50%' }}
        className={cn(
            "fixed top-20 left-1/2 p-4 rounded-xl shadow-2xl z-[100] text-white font-semibold text-sm border",
            type === "success" ? "bg-green-500/80 backdrop-blur-md border-green-400/50" : "bg-red-500/80 backdrop-blur-md border-red-400/50"
        )}
    >
        <div className="flex items-center justify-between">
            <span>{message}</span>
            <button onClick={onClose} className="ml-4 text-white/70 hover:text-white"><XIcon /></button>
        </div>
    </motion.div>
);

// AUTHENTICATION COMPONENTS
const AuthInput = (props) => (
    <input
        className="w-full px-4 py-3 bg-slate-950/50 border border-white/10 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
        {...props}
    />
);

const LoginModal = ({ isOpen, onClose, onSwitch, onSuccess }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { login } = useAuth();

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Login failed');
            login(data.user, data.access_token);
            onSuccess();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Welcome Back">
            <form onSubmit={handleLogin} className="space-y-4">
                {error && <div className="text-red-400 text-sm bg-red-500/10 p-3 rounded-md">{error}</div>}
                <AuthInput type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                <AuthInput type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                <Button type="submit" variant="primary" className="w-full" disabled={loading}>
                    {loading ? <LoadingSpinner /> : 'Login'}
                </Button>
                <p className="text-center text-sm text-white/50">
                    Don't have an account?{' '}
                    <button type="button" onClick={onSwitch} className="font-semibold text-purple-400 hover:underline">Sign Up</button>
                </p>
            </form>
        </Modal>
    );
};

const SignupModal = ({ isOpen, onClose, onSwitch, onSuccess }) => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { login } = useAuth();

    const handleSignup = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Registration failed');
            login(data.user, data.access_token);
            onSuccess();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Create Your Account">
            <form onSubmit={handleSignup} className="space-y-4">
                {error && <div className="text-red-400 text-sm bg-red-500/10 p-3 rounded-md">{error}</div>}
                <AuthInput type="text" placeholder="Full Name" value={name} onChange={(e) => setName(e.target.value)} required />
                <AuthInput type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                <AuthInput type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                <Button type="submit" variant="primary" className="w-full" disabled={loading}>
                    {loading ? <LoadingSpinner /> : 'Create Account'}
                </Button>
                <p className="text-center text-sm text-white/50">
                    Already have an account?{' '}
                    <button type="button" onClick={onSwitch} className="font-semibold text-purple-400 hover:underline">Login</button>
                </p>
            </form>
        </Modal>
    );
};

// E-COMMERCE COMPONENTS
const CartModal = ({ isOpen, onClose }) => {
    const { cart, updateQuantity, removeFromCart, clearCart, cartTotal } = useCart();

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Your Cart">
            {cart.length === 0 ? (
                <p className="text-white/60 text-center py-8">Your cart is empty.</p>
            ) : (
                <div className="space-y-4">
                    {cart.map(item => (
                        <div key={item.id} className="flex items-center justify-between text-white">
                            <img src={item.image} alt={item.name} className="w-16 h-16 rounded-md object-cover" />
                            <div className="flex-1 ml-4">
                                <p className="font-semibold">{item.name}</p>
                                <p className="text-sm text-white/60">${item.price.toFixed(2)}</p>
                            </div>
                            <div className="flex items-center space-x-2 bg-slate-950/50 border border-white/10 rounded-full p-1">
                                <button onClick={() => updateQuantity(item.id, item.quantity - 1)} className="p-1 rounded-full hover:bg-white/10"><MinusIcon /></button>
                                <span className="w-6 text-center">{item.quantity}</span>
                                <button onClick={() => updateQuantity(item.id, item.quantity + 1)} className="p-1 rounded-full hover:bg-white/10"><PlusIcon /></button>
                            </div>
                            <button onClick={() => removeFromCart(item.id)} className="ml-4 text-red-400 hover:text-red-300"><XIcon /></button>
                        </div>
                    ))}
                    <div className="border-t border-white/10 pt-4 mt-4 flex justify-between items-center">
                        <p className="text-lg font-bold text-white">Total: ${cartTotal.toFixed(2)}</p>
                        <Button variant="primary">Checkout</Button>
                    </div>
                    <button onClick={clearCart} className="w-full text-center text-sm text-white/50 hover:text-white mt-2">Clear Cart</button>
                </div>
            )}
        </Modal>
    );
};

// LAYOUT & PAGE COMPONENTS
const Header = () => {
    const { user, logout } = useAuth();
    const { cartCount } = useCart();
    const { showLogin, showSignup, showCart } = useAuth();

    return (
        <header className="fixed top-0 left-0 right-0 z-40 p-4">
            <div className="container mx-auto flex justify-between items-center p-3 rounded-2xl bg-black/20 backdrop-blur-lg border border-white/10 ring-1 ring-white/10">
                <a href="#" className="text-2xl font-bold tracking-tighter text-white bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                    Grocerly
                </a>
                <nav className="flex items-center space-x-4">
                    {user ? (
                        <>
                            <span className="text-white/80 text-sm hidden md:block">Hi, {user.name.split(' ')[0]}</span>
                            <button onClick={logout} className="text-white/60 hover:text-white transition-colors text-sm">Logout</button>
                        </>
                    ) : (
                        <>
                            <Button variant="ghost" onClick={showLogin}>Login</Button>
                            <Button variant="default" onClick={showSignup}>Sign Up</Button>
                        </>
                    )}
                    <button onClick={showCart} className="relative text-white hover:scale-110 transition-transform">
                        <ShoppingCartIcon />
                        {cartCount > 0 && (
                            <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-bold shadow-lg">
                                {cartCount}
                            </span>
                        )}
                    </button>
                </nav>
            </div>
        </header>
    );
};

const HeroSection = () => {
    const { showSignup } = useAuth();
    return (
        <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-black text-white">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-600 to-purple-700 clip-path-diagonal z-0"></div>
            <div className="absolute inset-0 bg-gradient-radial from-purple-400/10 via-pink-300/0 to-red-400/0"></div>
            
            <div className="relative z-10 container mx-auto grid md:grid-cols-2 gap-8 items-center px-6">
                <motion.div 
                    className="text-center md:text-left"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                >
                    <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white leading-tight contrast_pairing">
                        Groceries, <br />
                        <span className="bg-gradient-to-br from-purple-400 via-pink-400 to-red-400 bg-clip-text text-transparent">Reimagined.</span>
                    </h1>
                    <p className="mt-6 text-lg md:text-xl text-white/70 max-w-lg leading-relaxed">
                        Curated meal kits and pantry staples delivered on your schedule. Spend less time shopping, more time living.
                    </p>
                    <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center md:justify-start">
                        <Button variant="primary" onClick={showSignup}>
                            Start Your First Order
                        </Button>
                        <Button variant="outline">
                            Explore Meal Kits
                        </Button>
                    </div>
                </motion.div>
                <motion.div 
                    className="relative hidden md:block"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
                >
                    <img src="https://images.unsplash.com/photo-1542838132-92c53300491e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=800&q=80" alt="Fresh Groceries" className="rounded-3xl shadow-2xl shadow-purple-500/20 transform -rotate-3 hover:rotate-0 transition-transform duration-500" />
                    <div className="absolute -bottom-8 -left-8 w-48 h-48 bg-white/10 backdrop-blur-md rounded-2xl p-4 transform rotate-6 hover:rotate-0 transition-transform duration-500">
                        <h3 className="font-bold text-white">Weekly Restock</h3>
                        <p className="text-sm text-white/60 mt-1">Re-order your essentials with one tap.</p>
                    </div>
                </motion.div>
            </div>
        </section>
    );
};

const FeatureSection = ({ title, description, useCase, imageUrl, reverse = false }) => {
    const ref = useRef(null);
    const [inViewRef, isInView] = useInView(ref, { once: true, amount: 0.3 });

    return (
        <section ref={inViewRef} className="relative py-20 md:py-32 overflow-hidden bg-black">
            <div className={cn("absolute inset-0", reverse ? "diagonal-section-even bg-gradient-to-bl from-slate-950 to-black" : "diagonal-section bg-gradient-to-br from-black to-slate-950")}></div>
            <div className="container mx-auto grid md:grid-cols-2 gap-12 items-center relative z-10 px-6">
                <motion.div 
                    className={cn("relative", reverse && "md:order-2")}
                    initial={{ opacity: 0, y: 50 }}
                    animate={isInView ? { opacity: 1, y: 0 } : {}}
                    transition={{ duration: 0.7, ease: 'easeOut' }}
                >
                    <div className="relative aspect-square">
                        <div className={cn("absolute inset-0 rounded-3xl bg-gradient-to-br from-indigo-600 to-purple-700 transform", reverse ? "skew-y-3" : "-skew-y-3")}></div>
                        <img src={imageUrl} alt={title} className="relative w-full h-full object-cover rounded-3xl shadow-2xl shadow-purple-900/30 transform hover:scale-105 transition-transform duration-500" />
                    </div>
                </motion.div>
                <motion.div 
                    className={cn(reverse && "md:order-1")}
                    initial={{ opacity: 0, y: 50 }}
                    animate={isInView ? { opacity: 1, y: 0 } : {}}
                    transition={{ duration: 0.7, delay: 0.2, ease: 'easeOut' }}
                >
                    <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white contrast_pairing">{title}</h2>
                    <p className="mt-4 text-lg text-white/60 leading-relaxed">{description}</p>
                    <div className="mt-6 p-6 rounded-2xl bg-black/20 border border-white/10 backdrop-blur-sm">
                        <p className="font-mono text-sm text-purple-400">Use Case:</p>
                        <p className="mt-2 text-white/80">{useCase}</p>
                    </div>
                </motion.div>
            </div>
        </section>
    );
};

const MealKitsSection = () => {
    const { addToCart } = useCart();
    const ref = useRef(null);
    const [inViewRef, isInView] = useInView(ref, { once: true, amount: 0.2 });

    return (
        <section ref={inViewRef} className="py-20 md:py-32 bg-black text-white">
            <div className="container mx-auto px-6 text-center">
                <motion.h2 
                    className="text-4xl md:text-5xl font-bold tracking-tight"
                    initial={{ opacity: 0, y: 20 }}
                    animate={isInView ? { opacity: 1, y: 0 } : {}}
                    transition={{ duration: 0.5 }}
                >
                    Chef-Designed Meal Kits
                </motion.h2>
                <motion.p 
                    className="mt-4 max-w-2xl mx-auto text-lg text-white/60"
                    initial={{ opacity: 0, y: 20 }}
                    animate={isInView ? { opacity: 1, y: 0 } : {}}
                    transition={{ duration: 0.5, delay: 0.1 }}
                >
                    Everything you need for a delicious meal, delivered to your door.
                </motion.p>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 mt-12">
                    {MOCK_MEAL_KITS.map((kit, index) => (
                        <motion.div
                            key={kit.id}
                            className="bg-slate-900/50 rounded-2xl overflow-hidden group border border-white/10 transform transition-all duration-300 hover:!opacity-100 hover:scale-105 hover:shadow-2xl hover:shadow-purple-500/20"
                            initial={{ opacity: 0, y: 50 }}
                            animate={isInView ? { opacity: 1, y: 0 } : {}}
                            transition={{ duration: 0.5, delay: 0.1 * index }}
                        >
                            <img src={kit.image} alt={kit.name} className="w-full h-48 object-cover" />
                            <div className="p-6 text-left">
                                <h3 className="font-bold text-lg text-white">{kit.name}</h3>
                                <p className="text-white/50 text-sm mt-1">{kit.category}</p>
                                <div className="flex justify-between items-center mt-4">
                                    <p className="text-xl font-bold text-purple-400">${kit.price.toFixed(2)}</p>
                                    <Button onClick={() => addToCart(kit)} variant="primary" className="px-4 py-2 text-xs">Add to Cart</Button>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
};

const Footer = () => (
    <footer className="bg-black border-t border-white/10 text-white/50 py-12">
        <div className="container mx-auto px-6 text-center">
            <p>&copy; {new Date().getFullYear()} Grocerly. All rights reserved.</p>
            <p className="text-sm mt-2">Awwwards-Inspired Design for Busy Professionals.</p>
        </div>
    </footer>
);

// PROVIDER COMPONENTS
const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);
    const [showLoginModal, setShowLoginModal] = useState(false);
    const [showSignupModal, setShowSignupModal] = useState(false);
    const { showNotification } = useNotification();

    useEffect(() => {
        const storedToken = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');
        if (storedToken && storedUser) {
            setToken(storedToken);
            setUser(JSON.parse(storedUser));
        }
    }, []);

    const login = (userData, userToken) => {
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.setItem('token', userToken);
        setUser(userData);
        setToken(userToken);
    };

    const logout = () => {
        localStorage.removeItem('user');
        localStorage.removeItem('token');
        setUser(null);
        setToken(null);
        showNotification('Logged out successfully.', 'success');
    };

    const value = {
        user,
        token,
        login,
        logout,
        showLogin: () => setShowLoginModal(true),
        showSignup: () => setShowSignupModal(true),
        closeAuthModals: () => {
            setShowLoginModal(false);
            setShowSignupModal(false);
        },
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
            <AnimatePresence>
                {showLoginModal && (
                    <LoginModal
                        isOpen={showLoginModal}
                        onClose={() => setShowLoginModal(false)}
                        onSwitch={() => { setShowLoginModal(false); setShowSignupModal(true); }}
                        onSuccess={() => {
                            setShowLoginModal(false);
                            showNotification('Login successful!', 'success');
                        }}
                    />
                )}
                {showSignupModal && (
                    <SignupModal
                        isOpen={showSignupModal}
                        onClose={() => setShowSignupModal(false)}
                        onSwitch={() => { setShowSignupModal(false); setShowLoginModal(true); }}
                        onSuccess={() => {
                            setShowSignupModal(false);
                            showNotification('Account created successfully!', 'success');
                        }}
                    />
                )}
            </AnimatePresence>
        </AuthContext.Provider>
    );
};

const CartProvider = ({ children }) => {
    const [cart, setCart] = useState([]);
    const [showCartModal, setShowCartModal] = useState(false);
    const { showNotification } = useNotification();

    const addToCart = (product) => {
        setCart(prev => {
            const existing = prev.find(item => item.id === product.id);
            if (existing) {
                return prev.map(item => item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item);
            }
            return [...prev, { ...product, quantity: 1 }];
        });
        showNotification(`${product.name} added to cart!`, 'success');
    };

    const removeFromCart = (productId) => {
        setCart(prev => prev.filter(item => item.id !== productId));
    };


    const updateQuantity = (productId, quantity) => {
        if (quantity < 1) {
            removeFromCart(productId);
            return;
        }
        setCart(prev => prev.map(item => item.id === productId ? { ...item, quantity } : item));
    };

    const clearCart = () => setCart([]);

    const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);
    const cartTotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

    const value = {
        cart,
        addToCart,
        removeFromCart,
        updateQuantity,
        clearCart,
        cartCount,
        cartTotal,
        showCart: () => setShowCartModal(true),
    };

    return (
        <CartContext.Provider value={value}>
            {children}
            <AnimatePresence>
                {showCartModal && <CartModal isOpen={showCartModal} onClose={() => setShowCartModal(false)} />}
            </AnimatePresence>
        </CartContext.Provider>
    );
};

const NotificationProvider = ({ children }) => {
    const [notifications, setNotifications] = useState([]);

    const showNotification = (message, type = 'success') => {
        const id = Date.now();
        setNotifications([{ id, message, type }]); // Only show one at a time
        setTimeout(() => {
            setNotifications(prev => prev.filter(n => n.id !== id));
        }, 3000);
    };

    return (
        <NotificationContext.Provider value={{ showNotification }}>
            {children}
            <AnimatePresence>
                {notifications.map(n => (
                    <Toast key={n.id} message={n.message} type={n.type} onClose={() => setNotifications([])} />
                ))}
            </AnimatePresence>
        </NotificationContext.Provider>
    );
};

// MAIN APP COMPONENT
const App = () => {
    const features = [
        { name: 'Meal Kit Bundles', description: "Pre-packaged ingredient bundles for specific recipes, like '30-Minute Tuscan Chicken' or 'Vegan Chili'. This eliminates meal planning and ingredient hunting.", use_case: "A user selects the 'Taco Tuesday Kit' and the app adds ground beef, tortillas, cheese, and salsa to their cart in one click.", imageUrl: 'https://images.unsplash.com/photo-1627907222143-453c76959345?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=800&q=60' },
        { name: "Subscription 'Pantry Staples'", description: "Automated, recurring orders for essentials like milk, eggs, and coffee. This 'set it and forget it' feature ensures you never run out of daily necessities.", use_case: 'A user subscribes to receive 1 gallon of milk and a loaf of sourdough bread every Monday morning.', imageUrl: 'https://images.unsplash.com/photo-1584543622519-9a8646f58145?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=800&q=60' },
        { name: 'Express Delivery Slots', description: 'Book precise 1-hour delivery windows, including same-day express slots. This caters to the unpredictable schedules of working professionals.', use_case: 'A user finishing work at 6 PM books a delivery slot between 7 PM and 8 PM the same evening.', imageUrl: 'https://images.unsplash.com/photo-1580913428023-02c695666d61?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=800&q=60' },
    ];

    return (
        <NotificationProvider>
            <AuthProvider>
                <CartProvider>
                    <div className="bg-black font-sans antialiased">
                        <Header />
                        <main>
                            <HeroSection />
                            {features.map((feature, index) => (
                                <FeatureSection
                                    key={feature.name}
                                    title={feature.name}
                                    description={feature.description}
                                    useCase={feature.use_case}
                                    imageUrl={feature.imageUrl}
                                    reverse={index % 2 !== 0}
                                />
                            ))}
                            <MealKitsSection />
                        </main>
                        <Footer />
                    </div>
                </CartProvider>
            </AuthProvider>
        </NotificationProvider>
    );
};

export default App;