import React, { useState, useEffect, useRef } from 'react';

// UTILITY FOR CLASSNAMES (SHADCN/UI PATTERN)
const cn = (...inputs) => {
  return inputs.filter(Boolean).join(' ');
};

// AUTHENTICATION CONTEXT (MANDATORY)
const AuthContext = React.createContext(null);
const useAuth = () => React.useContext(AuthContext);

// CART CONTEXT (E-COMMERCE)
const CartContext = React.createContext(null);
const useCart = () => React.useContext(CartContext);

// NOTIFICATION CONTEXT (MANDATORY)
const NotificationContext = React.createContext(null);
const useNotification = () => React.useContext(NotificationContext);

// --- MOCK DATA ---
const mockProducts = [
  { id: 1, name: 'Organic Avocado', price: 2.50, image: '🥑', category: 'Produce' },
  { id: 2, name: 'Artisanal Sourdough', price: 5.00, image: '🍞', category: 'Bakery' },
  { id: 3, name: 'Pasture-Raised Eggs', price: 6.00, image: '🥚', category: 'Dairy & Eggs' },
  { id: 4, name: 'Oat Milk', price: 4.50, image: '🥛', category: 'Dairy & Eggs' },
  { id: 5, name: 'Free-Range Chicken Breast', price: 9.99, image: '🍗', category: 'Meat' },
  { id: 6, name: 'Bell Peppers (3-pack)', price: 3.50, image: '🫑', category: 'Produce' },
  { id: 7, name: 'Soy Sauce', price: 3.00, image: '🍶', category: 'Pantry' },
  { id: 8, name: 'Jasmine Rice (1kg)', price: 4.00, image: '🍚', category: 'Pantry' },
];

const mockMealKits = [
    { id: 1, name: '15-Min Pesto Pasta', description: 'A classic Italian dish, ready in a flash.', image: '🍝', ingredients: [2, 4] },
    { id: 2, name: 'Quick Chicken Stir-fry', description: 'Healthy, flavorful, and faster than takeout.', image: '🍜', ingredients: [5, 6, 7, 8] },
    { id: 3, name: 'Avocado Toast Deluxe', description: 'The perfect breakfast or lunch to fuel your day.', image: '🥑', ingredients: [1, 2, 3] },
];

const features = [
    { name: "One-Click Re-order", description: "Instantly add all items from a past purchase to your cart.", icon: '🔄' },
    { name: "Curated Meal Kits", description: "Solve the 'what to cook' problem with delicious, quick recipes.", icon: '🍲' },
    { name: "Real-Time Delivery", description: "Pick a 1-hour delivery window that fits your busy schedule.", icon: '🚚' },
    { name: "Smart Subscriptions", description: "Auto-reorder staples like milk and eggs so you never run out.", icon: '🔁' },
];


// --- ICON COMPONENTS ---
const UserIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>;
const ShoppingCartIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="8" cy="21" r="1"></circle><circle cx="19" cy="21" r="1"></circle><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57L23 6H6"></path></svg>;
const XIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>;
const PlusIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"></path><path d="M12 5v14"></path></svg>;
const MinusIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"></path></svg>;
const SearchIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>;
const ZapIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>;

// --- UI COMPONENTS (SHADCN STYLE) ---
const Button = ({ children, variant = "default", className = "", ...props }) => {
  const baseStyles = "inline-flex items-center justify-center whitespace-nowrap rounded-full text-sm font-bold ring-offset-background transition-transform-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:-translate-y-1 active:scale-95 duration-300";
  const variants = {
    default: "bg-white text-slate-900 hover:bg-white/90 shadow-lg shadow-white/10",
    primary: "bg-gradient-to-br from-purple-600 via-pink-500 to-red-500 text-white shadow-lg shadow-pink-500/30",
    outline: "border border-white/20 bg-transparent text-white hover:bg-white/10",
    ghost: "hover:bg-white/10 hover:text-slate-100 text-slate-300",
  };
  return <button className={cn(baseStyles, variants[variant], "px-6 py-3", className)} {...props}>{children}</button>;
};

const Card = ({ children, className = "", ...props }) => (
  <div className={cn("backdrop-blur-md bg-slate-800/50 border border-white/10 rounded-2xl shadow-2xl shadow-black/20", className)} {...props}>
    {children}
  </div>
);

const Modal = ({ isOpen, onClose, children, title }) => {
  useEffect(() => {
    const handleEsc = (event) => {
      if (event.keyCode === 27) onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-slate-900 text-white border border-white/10 rounded-2xl max-w-md w-full max-h-[90vh] overflow-y-auto shadow-2xl shadow-purple-500/20" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <h2 className="text-xl font-bold tracking-tight">{title}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors rounded-full p-1 hover:bg-white/10">
            <XIcon />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};

const LoadingSpinner = () => <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>;

const Toast = ({ message, type, onDismiss }) => {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 5000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  const baseStyle = "fixed bottom-5 right-5 p-4 rounded-xl shadow-2xl z-[100] text-white flex items-center gap-3 transition-all duration-300";
  const typeStyles = {
    success: "bg-gradient-to-br from-blue-600 to-cyan-500 shadow-cyan-500/30",
    error: "bg-gradient-to-br from-red-600 to-pink-500 shadow-pink-500/30",
  };

  return (
    <div className={cn(baseStyle, typeStyles[type])}>
      <span>{message}</span>
      <button onClick={onDismiss} className="p-1 rounded-full hover:bg-white/20"><XIcon /></button>
    </div>
  );
};

// --- AUTHENTICATION COMPONENTS ---
const AuthFormInput = (props) => (
    <input {...props} className="w-full px-4 py-3 bg-slate-800/50 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all" />
);

const LoginModal = ({ isOpen, onClose, onSwitchToSignup }) => {
  const { login } = useAuth();
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
      if (!response.ok) throw new Error(data.detail || 'Login failed');
      
      login(data.user, data.access_token);
      showNotification('Login successful!', 'success');
      onClose();
    } catch (err) {
      setError(err.message);
      showNotification(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Welcome Back">
      <form onSubmit={handleLogin} className="space-y-4">
        {error && <div className="text-red-400 text-sm p-3 bg-red-500/10 rounded-md">{error}</div>}
        <AuthFormInput type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <AuthFormInput type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <Button type="submit" variant="primary" className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner /> : 'Login'}
        </Button>
        <p className="text-center text-sm text-slate-400">
          Don't have an account?{' '}
          <button type="button" onClick={onSwitchToSignup} className="font-semibold text-purple-400 hover:underline">Sign Up</button>
        </p>
      </form>
    </Modal>
  );
};

const SignupModal = ({ isOpen, onClose, onSwitchToLogin }) => {
  const { login } = useAuth();
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const showNotification = useNotification();

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

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
      if (!response.ok) throw new Error(data.detail || 'Registration failed');
      
      login(data.user, data.access_token);
      showNotification('Account created successfully!', 'success');
      onClose();
    } catch (err) {
      setError(err.message);
      showNotification(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Your Account">
      <form onSubmit={handleSignup} className="space-y-4">
        {error && <div className="text-red-400 text-sm p-3 bg-red-500/10 rounded-md">{error}</div>}
        <AuthFormInput type="text" name="name" placeholder="Full Name" onChange={handleChange} required />
        <AuthFormInput type="email" name="email" placeholder="Email" onChange={handleChange} required />
        <AuthFormInput type="password" name="password" placeholder="Password" onChange={handleChange} required />
        <Button type="submit" variant="primary" className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner /> : 'Create Account'}
        </Button>
        <p className="text-center text-sm text-slate-400">
          Already have an account?{' '}
          <button type="button" onClick={onSwitchToLogin} className="font-semibold text-purple-400 hover:underline">Login</button>
        </p>
      </form>
    </Modal>
  );
};

// --- E-COMMERCE COMPONENTS ---
const ProductCard = ({ product }) => {
    const { addToCart } = useCart();
    return (
        <Card className="p-4 flex flex-col items-center text-center group transition-transform duration-300 hover:-translate-y-2 hover:shadow-purple-500/20">
            <div className="text-6xl mb-4 transition-transform duration-300 group-hover:scale-110">{product.image}</div>
            <h3 className="font-bold tracking-tight text-lg">{product.name}</h3>
            <p className="text-slate-400 text-sm mb-4">${product.price.toFixed(2)}</p>
            <Button variant="primary" className="w-full" onClick={() => addToCart(product)}>Add to Cart</Button>
        </Card>
    );
};

const CartModal = ({ isOpen, onClose }) => {
    const { cart, updateQuantity, removeFromCart, cartTotal } = useCart();

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Your Cart">
            {cart.length === 0 ? (
                <p className="text-slate-400 text-center py-8">Your cart is empty.</p>
            ) : (
                <div className="space-y-4">
                    {cart.map(item => (
                        <div key={item.id} className="flex items-center justify-between gap-4 p-2 rounded-lg bg-slate-800/50">
                            <span className="text-3xl">{item.image}</span>
                            <div className="flex-grow">
                                <p className="font-semibold">{item.name}</p>
                                <p className="text-sm text-slate-400">${item.price.toFixed(2)}</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <button onClick={() => updateQuantity(item.id, item.quantity - 1)} className="p-1 rounded-full bg-slate-700 hover:bg-slate-600"><MinusIcon /></button>
                                <span>{item.quantity}</span>
                                <button onClick={() => updateQuantity(item.id, item.quantity + 1)} className="p-1 rounded-full bg-slate-700 hover:bg-slate-600"><PlusIcon /></button>
                            </div>
                            <button onClick={() => removeFromCart(item.id)} className="text-red-400 hover:text-red-300"><XIcon /></button>
                        </div>
                    ))}
                    <div className="pt-4 border-t border-white/10 flex justify-between items-center">
                        <p className="text-lg font-bold">Total:</p>
                        <p className="text-lg font-bold">${cartTotal.toFixed(2)}</p>
                    </div>
                    <Button variant="primary" className="w-full">Proceed to Checkout</Button>
                </div>
            )}
        </Modal>
    );
};

// --- PAGE SECTIONS & LAYOUT ---
const Header = ({ onLogin, onSignup, onCartClick }) => {
    const { user, logout } = useAuth();
    const { cartCount } = useCart();
    const [isScrolled, setIsScrolled] = useState(false);

    useEffect(() => {
        const handleScroll = () => setIsScrolled(window.scrollY > 10);
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <header className={cn(
            "fixed top-0 left-0 right-0 z-40 transition-all duration-300",
            isScrolled ? "mt-4 mx-4 rounded-2xl backdrop-blur-xl bg-slate-900/50 border border-white/10 shadow-2xl shadow-black/30" : "p-4"
        )}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    <div className="flex items-center gap-2 text-2xl font-bold tracking-tighter bg-clip-text text-transparent bg-gradient-to-br from-purple-400 to-pink-400">
                        <ZapIcon /> Grocerly
                    </div>
                    <div className="flex items-center space-x-4">
                        <button onClick={onCartClick} className="relative text-slate-300 hover:text-white transition-colors">
                            <ShoppingCartIcon />
                            {cartCount > 0 && (
                                <span className="absolute -top-2 -right-2 bg-gradient-to-br from-pink-500 to-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-bold animate-pulse">
                                    {cartCount}
                                </span>
                            )}
                        </button>
                        {user ? (
                            <div className="flex items-center space-x-4">
                                <span className="text-slate-300 hidden sm:block">Hi, {user.name.split(' ')[0]}</span>
                                <Button variant="outline" onClick={logout}>Logout</Button>
                            </div>
                        ) : (
                            <div className="flex items-center space-x-2">
                                <Button variant="ghost" onClick={onLogin} className="hidden sm:inline-flex">Login</Button>
                                <Button variant="default" onClick={onSignup}>Sign Up</Button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
};

const HeroSection = ({ onSignup }) => (
    <section className="relative min-h-screen flex items-center justify-center text-white overflow-hidden bg-slate-900">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-600 via-pink-500 to-red-500 opacity-30 [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]"></div>
        <div className="absolute top-0 left-0 w-96 h-96 bg-blue-500/20 rounded-full filter blur-3xl animate-blob"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-purple-500/20 rounded-full filter blur-3xl animate-blob animation-delay-4000"></div>
        
        <div className="relative z-10 text-center p-4">
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
                Grocery shopping, <br />
                <span className="bg-clip-text text-transparent bg-gradient-to-br from-purple-400 via-pink-400 to-red-400">
                    reimagined for speed.
                </span>
            </h1>
            <p className="max-w-2xl mx-auto text-lg text-slate-300 leading-relaxed mb-8">
                Spend less time shopping and more time living. Get fresh groceries delivered in minutes with our AI-powered platform.
            </p>
            <div className="relative max-w-xl mx-auto">
                <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input 
                    type="text"
                    placeholder="Search for 'lactose-free snacks' or 'quick dinner'"
                    className="w-full pl-12 pr-4 py-4 rounded-full backdrop-blur-md bg-white/10 border border-white/20 focus:ring-2 focus:ring-purple-500 focus:outline-none shadow-lg"
                />
            </div>
             <Button variant="primary" className="mt-8" onClick={onSignup}>
                Start Shopping Now
            </Button>
        </div>
    </section>
);

const FeaturesSection = () => (
    <section className="py-20 sm:py-32 bg-slate-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
                <h2 className="text-4xl font-bold tracking-tight">Your Personal Grocery Assistant</h2>
                <p className="mt-4 text-lg text-slate-400">Features designed to give you back your time.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                {features.map((feature, index) => (
                    <Card key={feature.name} className="p-8 text-center transition-transform duration-300 hover:-translate-y-2 hover:shadow-purple-500/20" style={{ animationDelay: `${index * 100}ms` }}>
                        <div className="text-5xl mb-4">{feature.icon}</div>
                        <h3 className="text-xl font-bold mb-2">{feature.name}</h3>
                        <p className="text-slate-400 leading-relaxed">{feature.description}</p>
                    </Card>
                ))}
            </div>
        </div>
    </section>
);

const ProductsSection = () => (
    <div className="relative bg-slate-900 text-white py-20 sm:py-32 overflow-hidden">
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-gradient-radial from-purple-400/20 via-pink-300/10 to-red-400/5 rounded-full filter blur-3xl"></div>
        <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-gradient-radial from-blue-400/20 via-cyan-300/10 to-teal-400/5 rounded-full filter blur-3xl"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
                <h2 className="text-4xl font-bold tracking-tight">Personalized Quick Add</h2>
                <p className="mt-4 text-lg text-slate-400">Your favorite items, ready when you are.</p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {mockProducts.slice(0, 4).map(p => <ProductCard key={p.id} product={p} />)}
            </div>
        </div>
    </div>
);

const MealKitsSection = () => {
    const { addMealKitToCart } = useCart();
    return (
        <section className="py-20 sm:py-32 bg-slate-900 text-white">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-12">
                    <h2 className="text-4xl font-bold tracking-tight">Dinner, Solved.</h2>
                    <p className="mt-4 text-lg text-slate-400">One-click meal kits for delicious, stress-free evenings.</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {mockMealKits.map(kit => (
                        <Card key={kit.id} className="p-6 flex flex-col group transition-all duration-300 hover:border-purple-500/50 hover:-translate-y-2">
                            <div className="text-6xl mb-4 transition-transform duration-300 group-hover:rotate-3 group-hover:scale-110">{kit.image}</div>
                            <h3 className="text-2xl font-bold tracking-tight">{kit.name}</h3>
                            <p className="text-slate-400 flex-grow mb-6">{kit.description}</p>
                            <Button variant="primary" onClick={() => addMealKitToCart(kit)}>Add All Ingredients</Button>
                        </Card>
                    ))}
                </div>
            </div>
        </section>
    );
};

const Footer = () => (
    <footer className="bg-slate-900 border-t border-white/10 text-white">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8 text-center">
            <p className="text-slate-400">&copy; {new Date().getFullYear()} Grocerly. All rights reserved.</p>
            <p className="text-sm text-slate-500 mt-2">Awwwards Site of the Day Submission</p>
        </div>
    </footer>
);

// --- PROVIDER COMPONENTS ---
const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);

    useEffect(() => {
        const storedToken = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');
        if (storedToken && storedUser) {
            setToken(storedToken);
            setUser(JSON.parse(storedUser));
        }
    }, []);

    const login = (userData, accessToken) => {
        setUser(userData);
        setToken(accessToken);
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.setItem('token', accessToken);
    };

    const logout = () => {
        setUser(null);
        setToken(null);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
    };

    const value = { user, token, login, logout };
    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

const CartProvider = ({ children }) => {
    const [cart, setCart] = useState([]);
    const showNotification = useNotification();

    const addToCart = (product, quantity = 1) => {
        setCart(prev => {
            const existing = prev.find(item => item.id === product.id);
            if (existing) {
                return prev.map(item => item.id === product.id ? { ...item, quantity: item.quantity + quantity } : item);
            }
            return [...prev, { ...product, quantity }];
        });
        showNotification(`${product.name} added to cart!`, 'success');
    };
    
    const addMealKitToCart = (mealKit) => {
        mealKit.ingredients.forEach(ingredientId => {
            const product = mockProducts.find(p => p.id === ingredientId);
            if (product) {
                addToCart(product, 1);
            }
        });
        showNotification(`${mealKit.name} ingredients added!`, 'success');
    };

    const updateQuantity = (productId, quantity) => {
        if (quantity <= 0) {
            removeFromCart(productId);
        } else {
            setCart(prev => prev.map(item => item.id === productId ? { ...item, quantity } : item));
        }
    };

    const removeFromCart = (productId) => {
        setCart(prev => prev.filter(item => item.id !== productId));
    };

    const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);
    const cartTotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

    const value = { cart, addToCart, addMealKitToCart, updateQuantity, removeFromCart, cartCount, cartTotal };
    return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};

const NotificationProvider = ({ children }) => {
    const [notifications, setNotifications] = useState([]);

    const showNotification = (message, type = 'success') => {
        const id = Date.now();
        setNotifications(prev => [...prev, { id, message, type }]);
    };

    const dismissNotification = (id) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    };

    return (
        <NotificationContext.Provider value={showNotification}>
            {children}
            <div className="fixed bottom-5 right-5 z-[100] space-y-2">
                {notifications.map(n => (
                    <Toast key={n.id} message={n.message} type={n.type} onDismiss={() => dismissNotification(n.id)} />
                ))}
            </div>
        </NotificationContext.Provider>
    );
};

// --- MAIN APP COMPONENT ---
const App = () => {
    const [showLogin, setShowLogin] = useState(false);
    const [showSignup, setShowSignup] = useState(false);
    const [showCart, setShowCart] = useState(false);

    return (
        <AuthProvider>
            <NotificationProvider>
                <CartProvider>
                    <div className="min-h-screen bg-slate-900 font-sans text-white antialiased">
                        <Header
                            onLogin={() => setShowLogin(true)}
                            onSignup={() => setShowSignup(true)}
                            onCartClick={() => setShowCart(true)}
                        />
                        <main>
                            <HeroSection onSignup={() => setShowSignup(true)} />
                            <FeaturesSection />
                            <ProductsSection />
                            <MealKitsSection />
                        </main>
                        <Footer />

                        <LoginModal
                            isOpen={showLogin}
                            onClose={() => setShowLogin(false)}
                            onSwitchToSignup={() => { setShowLogin(false); setShowSignup(true); }}
                        />
                        <SignupModal
                            isOpen={showSignup}
                            onClose={() => setShowSignup(false)}
                            onSwitchToLogin={() => { setShowSignup(false); setShowLogin(true); }}
                        />
                        <CartModal
                            isOpen={showCart}
                            onClose={() => setShowCart(false)}
                        />
                    </div>
                </CartProvider>
            </NotificationProvider>
        </AuthProvider>
    );
};

export default App;