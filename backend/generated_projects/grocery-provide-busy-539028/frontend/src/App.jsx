import React, 'useState', 'useEffect', 'useRef', 'useCallback';

// UTILITY: Class Name Merger
const cn = (...classes) => classes.filter(Boolean).join(' ');

// SAFE FRAMER-MOTION FALLBACKS (CRITICAL FOR BROWSER COMPATIBILITY):
const createMotionFallback = (element) => {
  const FallbackComponent = React.forwardRef(({ children, className, style, onClick, id, initial, animate, exit, whileHover, whileTap, whileInView, transition, variants, ...validProps }, ref) => 
    React.createElement(element, { ref, className, style, onClick, id, ...validProps }, children)
  );
  FallbackComponent.displayName = `motion.${element}`;
  return FallbackComponent;
};

const motion = {
  div: createMotionFallback('div'),
  span: createMotionFallback('span'), 
  section: createMotionFallback('section'),
  h1: createMotionFallback('h1'),
  h2: createMotionFallback('h2'),
  button: createMotionFallback('button'),
  p: createMotionFallback('p'),
  header: createMotionFallback('header'),
  aside: createMotionFallback('aside'),
};

const AnimatePresence = ({ children }) => <>{children}</>;
const useInView = () => [React.useRef(null), true];
const useScroll = () => ({ scrollYProgress: { get: () => 0, onChange: () => {}, set: () => {}, stop: () => {}, destroy: () => {} } });

// API URL
const API_URL = 'http://localhost:8001/api/v1';

// CONTEXT DEFINITIONS
const AuthContext = React.createContext(null);
const useAuth = () => React.useContext(AuthContext);

const CartContext = React.createContext(null);
const useCart = () => React.useContext(CartContext);

const NotificationContext = React.createContext(null);
const useNotification = () => React.useContext(NotificationContext);

// ICON COMPONENTS
const UserIcon = () => <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>;
const ShoppingCartIcon = () => <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" /></svg>;
const XIcon = () => <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>;
const PlusIcon = () => <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 6v12m6-6H6" /></svg>;
const MinusIcon = () => <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M18 12H6" /></svg>;
const SearchIcon = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>;
const ArrowRightIcon = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>;
const UploadIcon = () => <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>;
const StarIcon = ({ filled }) => <svg className={cn("w-5 h-5", filled ? "text-[#ec4899]" : "text-white/50")} fill={filled ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.196-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.783-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>;

// BRUTALIST UI COMPONENTS
const Button = ({ children, variant = "primary", className = "", ...props }) => {
  const baseClasses = "font-mono uppercase tracking-wider text-sm px-6 py-3 border-2 border-black transition-all duration-200 flex items-center justify-center gap-2";
  const variants = {
    primary: "bg-[#ec4899] text-black hover:bg-black hover:text-[#ec4899] shadow-[4px_4px_0_#000] hover:shadow-[4px_4px_0_#ec4899]",
    secondary: "bg-white text-black hover:bg-black hover:text-white shadow-[4px_4px_0_#000] hover:shadow-[4px_4px_0_#fff]",
    ghost: "bg-transparent text-white border-white hover:bg-white hover:text-black",
  };
  return <button className={cn(baseClasses, variants[variant], className)} {...props}>{children}</button>;
};

const Input = React.forwardRef(({ className, ...props }, ref) => {
  return <input ref={ref} className={cn("w-full bg-white text-black p-3 border-2 border-black focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#ec4899] font-mono", className)} {...props} />;
});
Input.displayName = 'Input';

const Modal = ({ isOpen, onClose, children, title }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <motion.div 
        className="bg-white text-black w-full max-w-md border-4 border-black shadow-[8px_8px_0_#ec4899]"
        onClick={(e) => e.stopPropagation()}
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
      >
        <div className="flex items-center justify-between p-4 border-b-4 border-black">
          <h2 className="font-mono text-xl uppercase font-bold">{title}</h2>
          <button onClick={onClose} className="p-1 border-2 border-transparent hover:border-black"><XIcon /></button>
        </div>
        <div className="p-6">{children}</div>
      </motion.div>
    </div>
  );
};

const Toast = ({ message, type = "success", onClose }) => (
  <motion.div
    className={cn(
      "fixed bottom-5 right-5 p-4 border-4 border-black shadow-[5px_5px_0_#000] z-[100] font-mono uppercase text-sm",
      type === "success" ? "bg-[#ec4899] text-black" : "bg-red-500 text-white"
    )}
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: 20 }}
  >
    <div className="flex items-center justify-between gap-4">
      <span>{message}</span>
      <button onClick={onClose} className="p-1 border-2 border-transparent hover:border-black"><XIcon /></button>
    </div>
  </motion.div>
);

const LoadingSpinner = () => <div className="w-6 h-6 border-4 border-black border-t-[#ec4899] rounded-full animate-spin"></div>;

// AUTHENTICATION COMPONENTS
const AuthForm = ({ onSubmit, loading, error, children, buttonText }) => (
  <form onSubmit={onSubmit} className="space-y-4">
    {error && <div className="bg-red-500/20 text-red-700 p-3 border-2 border-red-700 font-mono text-sm">{error}</div>}
    {children}
    <Button type="submit" className="w-full" disabled={loading}>
      {loading ? <LoadingSpinner /> : buttonText}
    </Button>
  </form>
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
    <Modal isOpen={isOpen} onClose={onClose} title="Login">
      <AuthForm onSubmit={handleLogin} loading={loading} error={error} buttonText="Log In">
        <Input type="email" placeholder="EMAIL" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <Input type="password" placeholder="PASSWORD" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </AuthForm>
      <p className="text-center mt-4 font-mono text-sm">
        NO ACCOUNT? <button onClick={onSwitch} className="underline hover:text-[#ec4899]">SIGN UP</button>
      </p>
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
      if (!response.ok) throw new Error(data.detail || 'Signup failed');
      login(data.user, data.access_token);
      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Sign Up">
      <AuthForm onSubmit={handleSignup} loading={loading} error={error} buttonText="Create Account">
        <Input type="text" placeholder="FULL NAME" value={name} onChange={(e) => setName(e.target.value)} required />
        <Input type="email" placeholder="EMAIL" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <Input type="password" placeholder="PASSWORD" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </AuthForm>
      <p className="text-center mt-4 font-mono text-sm">
        HAVE AN ACCOUNT? <button onClick={onSwitch} className="underline hover:text-[#ec4899]">LOG IN</button>
      </p>
    </Modal>
  );
};

// E-COMMERCE COMPONENTS
const mockProducts = [
  { id: 1, name: 'Organic Chicken Breast', price: 9.99, category: 'Meat', tags: ['Organic'], image: '/images/chicken.png' },
  { id: 2, name: 'Gluten-Free Bread', price: 5.49, category: 'Bakery', tags: ['Gluten-Free'], image: '/images/bread.png' },
  { id: 3, name: 'Artisanal Chickpeas', price: 3.29, category: 'Pantry', tags: ['Organic'], image: '/images/chickpeas.png' },
  { id: 4, name: 'Greek Yogurt', price: 4.99, category: 'Dairy', tags: [], image: '/images/yogurt.png' },
  { id: 5, name: 'Avocado', price: 1.99, category: 'Produce', tags: ['Organic'], image: '/images/avocado.png' },
  { id: 6, name: 'Kombucha', price: 3.99, category: 'Drinks', tags: ['Organic'], image: '/images/kombucha.png' },
  { id: 7, name: 'Almond Milk', price: 4.50, category: 'Dairy', tags: ['Gluten-Free'], image: '/images/almond-milk.png' },
  { id: 8, name: 'Quinoa', price: 6.79, category: 'Pantry', tags: ['Organic', 'Gluten-Free'], image: '/images/quinoa.png' },
];

const ProductCard = ({ product }) => {
  const { addToCart } = useCart();
  return (
    <div className="bg-white text-black border-4 border-black p-4 flex flex-col justify-between group">
      <div className="aspect-square bg-gray-100 border-2 border-black mb-4 flex items-center justify-center">
        <p className="font-mono text-xs">IMG_PLACEHOLDER</p>
      </div>
      <div>
        <h3 className="font-mono uppercase font-bold truncate">{product.name}</h3>
        <div className="flex justify-between items-center mt-2">
          <p className="font-mono text-lg">${product.price.toFixed(2)}</p>
          <button 
            onClick={() => addToCart(product)}
            className="w-10 h-10 bg-black text-white border-2 border-black flex items-center justify-center transition-all duration-200 group-hover:bg-[#ec4899] group-hover:text-black"
          >
            <PlusIcon />
          </button>
        </div>
      </div>
    </div>
  );
};

const CartSidebar = ({ isOpen, onClose }) => {
  const { cart, updateQuantity, removeFromCart, subtotal } = useCart();

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={onClose}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />
          <motion.aside
            className="fixed top-0 right-0 h-full w-full max-w-md bg-white text-black border-l-4 border-black z-50 flex flex-col"
            initial={{ x: '100%' }}
            animate={{ x: '0%' }}
            exit={{ x: '100%' }}
            transition={{ type: 'tween', duration: 0.3 }}
          >
            <div className="flex items-center justify-between p-4 border-b-4 border-black">
              <h2 className="font-mono text-xl uppercase font-bold">Your Cart</h2>
              <button onClick={onClose} className="p-1 border-2 border-transparent hover:border-black"><XIcon /></button>
            </div>
            {cart.length === 0 ? (
              <div className="flex-grow flex items-center justify-center">
                <p className="font-mono uppercase">Your cart is empty.</p>
              </div>
            ) : (
              <div className="flex-grow overflow-y-auto p-4 space-y-4">
                {cart.map(item => (
                  <div key={item.id} className="flex items-center gap-4 border-2 border-black p-2">
                    <div className="w-16 h-16 bg-gray-100 border-2 border-black flex-shrink-0"></div>
                    <div className="flex-grow">
                      <h3 className="font-mono uppercase text-sm font-bold">{item.name}</h3>
                      <p className="font-mono text-xs">${item.price.toFixed(2)}</p>
                    </div>
                    <div className="flex items-center gap-2 border-2 border-black">
                      <button onClick={() => updateQuantity(item.id, item.quantity - 1)} className="w-8 h-8 flex items-center justify-center hover:bg-gray-200"><MinusIcon /></button>
                      <span className="font-mono w-6 text-center">{item.quantity}</span>
                      <button onClick={() => updateQuantity(item.id, item.quantity + 1)} className="w-8 h-8 flex items-center justify-center hover:bg-gray-200"><PlusIcon /></button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="p-4 border-t-4 border-black space-y-4">
              <div className="flex justify-between font-mono uppercase font-bold text-lg">
                <span>Subtotal</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              <Button className="w-full">Checkout</Button>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
};

// LAYOUT COMPONENTS
const Header = () => {
  const { user, logout } = useAuth();
  const { cartCount, toggleCart } = useCart();
  const { showNotification } = useNotification();
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);

  const handleLogout = () => {
    logout();
    showNotification('LOGGED OUT', 'success');
  };

  return (
    <>
      <motion.header className="bg-white text-black border-b-4 border-black p-4 sticky top-0 z-30">
        <div className="container mx-auto flex justify-between items-center">
          <a href="#" className="font-mono font-bold uppercase tracking-wider text-xl">GROCERY-PROVIDE</a>
          <nav className="flex items-center gap-4">
            {user ? (
              <>
                <span className="font-mono uppercase text-sm hidden md:block">HI, {user.name.split(' ')[0]}</span>
                <button onClick={handleLogout} className="font-mono uppercase text-sm hover:text-[#ec4899]">LOGOUT</button>
              </>
            ) : (
              <>
                <button onClick={() => setShowLogin(true)} className="font-mono uppercase text-sm hover:text-[#ec4899]">LOGIN</button>
                <button onClick={() => setShowSignup(true)} className="font-mono uppercase text-sm bg-black text-white px-4 py-2 hover:bg-[#ec4899] hover:text-black transition-colors duration-200">SIGN UP</button>
              </>
            )}
            <button onClick={toggleCart} className="relative p-2 border-2 border-transparent hover:border-black">
              <ShoppingCartIcon />
              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-[#ec4899] text-black font-mono text-xs rounded-full h-5 w-5 flex items-center justify-center border-2 border-black">
                  {cartCount}
                </span>
              )}
            </button>
          </nav>
        </div>
      </motion.header>
      <LoginModal 
        isOpen={showLogin} 
        onClose={() => setShowLogin(false)} 
        onSwitch={() => { setShowLogin(false); setShowSignup(true); }}
        onSuccess={() => { setShowLogin(false); showNotification('LOGIN SUCCESSFUL', 'success'); }}
      />
      <SignupModal 
        isOpen={showSignup} 
        onClose={() => setShowSignup(false)} 
        onSwitch={() => { setShowSignup(false); setShowLogin(true); }}
        onSuccess={() => { setShowSignup(false); showNotification('WELCOME!', 'success'); }}
      />
    </>
  );
};

const Footer = () => {
  const [feedback, setFeedback] = useState('');
  const { showNotification } = useNotification();

  const handleFeedbackSubmit = (e) => {
    e.preventDefault();
    if (feedback.trim()) {
      console.log('Feedback submitted:', feedback);
      showNotification('FEEDBACK SENT. THANKS!', 'success');
      setFeedback('');
    }
  };

  return (
    <footer className="bg-black text-white p-8 md:p-16 border-t-4 border-white">
      <div className="container mx-auto grid md:grid-cols-3 gap-8">
        <div className="md:col-span-1">
          <h3 className="font-mono uppercase font-bold text-xl mb-4">GROCERY-PROVIDE</h3>
          <p className="font-mono text-sm text-white/70">EFFICIENCY FOR THE BUSY. QUALITY FOR THE CONSCIOUS.</p>
        </div>
        <div className="md:col-span-2">
          <h3 className="font-mono uppercase font-bold mb-4">ANONYMOUS FEEDBACK</h3>
          <form onSubmit={handleFeedbackSubmit} className="flex flex-col md:flex-row gap-2">
            <Input 
              type="text" 
              placeholder="SUGGESTIONS? ISSUES? LET US KNOW." 
              className="bg-black text-white border-white focus:ring-offset-black"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
            />
            <Button type="submit" variant="ghost" className="px-4">SUBMIT</Button>
          </form>
        </div>
      </div>
      <div className="container mx-auto mt-8 pt-8 border-t-2 border-white/20 text-center">
        <p className="font-mono text-xs text-white/50">© 2024 grocery-provide-busy-539028. ALL RIGHTS RESERVED.</p>
      </div>
    </footer>
  );
};

// PROVIDER COMPONENTS
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

  const value = { user, token, login, logout };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

const CartProvider = ({ children }) => {
  const [cart, setCart] = useState([]);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const { showNotification } = useNotification();

  const addToCart = (product) => {
    setCart(prev => {
      const existing = prev.find(item => item.id === product.id);
      if (existing) {
        return prev.map(item => item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item);
      }
      return [...prev, { ...product, quantity: 1 }];
    });
    showNotification(`${product.name} ADDED`, 'success');
  };

  const removeFromCart = (productId) => {
    setCart(prev => prev.filter(item => item.id !== productId));
  };

  const updateQuantity = (productId, quantity) => {
    if (quantity < 1) {
      removeFromCart(productId);
    } else {
      setCart(prev => prev.map(item => item.id === productId ? { ...item, quantity } : item));
    }
  };

  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);
  const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const toggleCart = () => setIsCartOpen(prev => !prev);

  const value = { cart, addToCart, removeFromCart, updateQuantity, cartCount, subtotal, isCartOpen, toggleCart };
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};

const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);

  const showNotification = (message, type = 'success') => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 3000);
  };

  return (
    <NotificationContext.Provider value={{ showNotification }}>
      {children}
      <div className="fixed bottom-0 right-0 p-4 space-y-2 z-[100]">
        <AnimatePresence>
          {notifications.map(n => (
            <Toast key={n.id} message={n.message} type={n.type} onClose={() => setNotifications(prev => prev.filter(item => item.id !== n.id))} />
          ))}
        </AnimatePresence>
      </div>
    </NotificationContext.Provider>
  );
};

// MAIN APP COMPONENT
const App = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({ Organic: false, 'Gluten-Free': false });

  const handleFilterToggle = (filter) => {
    setFilters(prev => ({ ...prev, [filter]: !prev[filter] }));
  };

  const filteredProducts = mockProducts.filter(p => {
    const activeFilters = Object.keys(filters).filter(key => filters[key]);
    const searchMatch = p.name.toLowerCase().includes(searchTerm.toLowerCase());
    const filterMatch = activeFilters.length === 0 || activeFilters.every(f => p.tags.includes(f));
    return searchMatch && filterMatch;
  });

  return (
    <NotificationProvider>
      <AuthProvider>
        <CartProvider>
          <div className="bg-white text-black min-h-screen font-sans antialiased">
            <Header />
            <CartSidebar isOpen={useCart().isCartOpen} onClose={useCart().toggleCart} />
            
            <main>
              {/* Hero Section: geometric_blocks */}
              <section className="bg-black text-white p-8 md:p-16 border-b-4 border-white">
                <div className="container mx-auto text-center">
                  <motion.h1 
                    className="font-mono font-bold uppercase text-4xl md:text-7xl tracking-tighter"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                  >
                    FAST GROCERIES.
                  </motion.h1>
                  <motion.h1 
                    className="font-mono font-bold uppercase text-4xl md:text-7xl tracking-tighter text-[#ec4899]"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                  >
                    ZERO HASSLE.
                  </motion.h1>
                  <motion.p 
                    className="max-w-2xl mx-auto mt-6 font-mono text-white/80"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.5, delay: 0.4 }}
                  >
                    A seamless online grocery experience for busy professionals and families. Minimalist design, maximum efficiency.
                  </motion.p>
                </div>
              </section>

              {/* Predictive Search Section */}
              <section className="p-8 md:p-16 bg-white border-b-4 border-black sticky top-[73px] z-20">
                <div className="container mx-auto">
                  <div className="relative mb-4">
                    <Input 
                      type="text" 
                      placeholder="SEARCH 'CHICKEN', 'BREAD', 'AVOCADO'..." 
                      className="pl-12 text-lg"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-black/50">
                      <SearchIcon />
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {Object.keys(filters).map(filter => (
                      <button 
                        key={filter}
                        onClick={() => handleFilterToggle(filter)}
                        className={cn(
                          "font-mono uppercase text-xs px-3 py-1 border-2 border-black transition-colors duration-200",
                          filters[filter] ? "bg-black text-white" : "bg-white text-black"
                        )}
                      >
                        {filter}
                      </button>
                    ))}
                  </div>
                </div>
              </section>

              {/* Product Grid Section: card_grid_system */}
              <section className="bg-gray-100 p-8 md:p-16">
                <div className="container mx-auto">
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {filteredProducts.map(product => (
                      <ProductCard key={product.id} product={product} />
                    ))}
                  </div>
                  {filteredProducts.length === 0 && (
                    <div className="text-center py-16 border-4 border-dashed border-black">
                      <p className="font-mono uppercase">NO PRODUCTS FOUND.</p>
                      <p className="font-mono text-sm text-black/60">Try adjusting your search or filters.</p>
                    </div>
                  )}
                </div>
              </section>

              {/* Features Section: Brutalist Cards */}
              <section className="bg-black text-white p-8 md:p-16">
                <div className="container mx-auto">
                  <h2 className="font-mono font-bold uppercase text-3xl md:text-5xl tracking-tighter text-center mb-12">
                    BUILT FOR <span className="text-[#ec4899]">SPEED</span>
                  </h2>
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-0 border-t-4 border-l-4 border-white">
                    {[
                      { title: "USER REVIEWS", desc: "See what others think. Leave ratings and upload photos to build community trust." },
                      { title: "ORDER HISTORY", desc: "View past orders and reorder your weekly staples with a single click. Shopping done in seconds." },
                      { title: "QUICK ADD", desc: "No need to visit product pages. Add items directly from the grid and watch your cart update instantly." },
                    ].map(feature => (
                      <div key={feature.title} className="p-8 border-b-4 border-r-4 border-white aspect-square flex flex-col justify-end">
                        <h3 className="font-mono uppercase font-bold text-2xl mb-2">{feature.title}</h3>
                        <p className="font-mono text-white/70">{feature.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            </main>

            <Footer />
          </div>
        </CartProvider>
      </AuthProvider>
    </NotificationProvider>
  );
};

export default App;