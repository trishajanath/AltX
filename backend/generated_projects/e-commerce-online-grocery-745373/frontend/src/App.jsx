An award-winning React App.jsx for an Online Grocery E-commerce Platform, designed with a unique Bauhaus Geometric layout and adhering to all specified technical and design constraints.

```jsx
import React, { useState, useEffect, useRef } from 'react';

// SAFE FRAMER-MOTION FALLBACKS (CRITICAL FOR BROWSER COMPATIBILITY):
const createMotionFallback = (element) => {
  const FallbackComponent = ({ children, className, style, onClick, id, ...props }) => {
    // Filter out framer-motion specific props to avoid React warnings
    const validProps = { className, style, onClick, id };
    return React.createElement(element, validProps, children);
  };
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
  nav: createMotionFallback('nav'),
};

const AnimatePresence = ({ children }) => <>{children}</>;

// --- CONTEXT DEFINITIONS ---
const AuthContext = React.createContext(null);
const useAuth = () => React.useContext(AuthContext);

const CartContext = React.createContext(null);
const useCart = () => React.useContext(CartContext);

const NotificationContext = React.createContext(null);
const useNotification = () => React.useContext(NotificationContext);

// --- MOCK DATA ---
const mockProducts = [
  { id: 1, name: 'Organic Hass Avocado', price: 2.50, image: '/avocado.png', category: 'Produce' },
  { id: 2, name: 'Artisanal Sourdough Loaf', price: 5.99, image: '/bread.png', category: 'Bakery' },
  { id: 3, name: 'Free-Range Eggs (Dozen)', price: 4.20, image: '/eggs.png', category: 'Dairy & Eggs' },
  { id: 4, name: 'Organic Whole Milk', price: 3.80, image: '/milk.png', category: 'Dairy & Eggs' },
  { id: 5, name: 'Fresh Strawberries (1lb)', price: 4.50, image: '/strawberries.png', category: 'Produce', onSale: true },
  { id: 6, name: 'Gourmet Ground Coffee', price: 12.99, image: '/coffee.png', category: 'Pantry' },
];

const mockPromotions = [
    { id: 1, title: "50% Off All Berries", description: "Stock up on fresh, juicy berries this week only!", productIds: [5] },
    { id: 2, title: "BOGO Bakery", description: "Buy one artisanal bread, get one 50% off.", productIds: [2] },
    { id: 3, title: "Dairy Delights", description: "Save 15% on all milk and eggs.", productIds: [3, 4] },
];


// --- HELPER FUNCTIONS ---
const cn = (...classes) => classes.filter(Boolean).join(' ');

// --- ICON COMPONENTS ---
const User = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>;
const ShoppingCart = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="8" cy="21" r="1"></circle><circle cx="19" cy="21" r="1"></circle><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57L23 6H6"></path></svg>;
const X = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>;
const Plus = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"></path><path d="M12 5v14"></path></svg>;
const Minus = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"></path></svg>;
const Search = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>;
const ArrowRight = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>;


// --- UI COMPONENTS (SHADCN STYLE) ---
const Button = ({ children, className = "", onClick, disabled, ...props }) => (
  <button
    className={cn(
      "inline-flex items-center justify-center rounded-none px-6 py-3 text-sm font-bold uppercase tracking-widest transition-all duration-300 ease-in-out focus-visible:outline-none disabled:opacity-50 disabled:cursor-not-allowed",
      "bg-white text-black hover:bg-red-500 hover:text-white",
      "hover:scale-105 hover:-translate-y-1 transform",
      className
    )}
    onClick={onClick}
    disabled={disabled}
    {...props}
  >
    {children}
  </button>
);

const Modal = ({ isOpen, onClose, children, title }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 font-sans">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="bg-zinc-900 text-white border-2 border-white/20 rounded-none max-w-md w-full max-h-[90vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between p-4 border-b border-white/20">
          <h2 className="text-lg font-bold uppercase tracking-widest">{title}</h2>
          <button onClick={onClose} className="text-white/50 hover:text-white transition-colors">
            <X />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </motion.div>
    </div>
  );
};

const LoadingSpinner = () => <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>;

const Toast = ({ message, type = "success", onClose }) => (
  <motion.div
    initial={{ opacity: 0, y: 50 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: 20 }}
    className={cn(
      "fixed bottom-4 right-4 p-4 rounded-none shadow-lg z-[100] font-sans border-2",
      type === "success" ? "bg-green-500 border-white text-black" : "bg-red-500 border-white text-white"
    )}
  >
    <div className="flex items-center justify-between">
      <span className="font-bold uppercase tracking-wider">{message}</span>
      <button onClick={onClose} className="ml-4 hover:opacity-75">
        <X />
      </button>
    </div>
  </motion.div>
);

// --- AUTHENTICATION COMPONENTS ---
const AuthFormInput = (props) => (
    <input
        {...props}
        className="w-full px-3 py-2 bg-zinc-800 border-2 border-zinc-700 text-white placeholder-zinc-500 focus:outline-none focus:border-red-500 transition-colors rounded-none"
    />
);

const LoginModal = ({ isOpen, onClose, onSwitch, onSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const API_URL = 'http://localhost:8001/api/v1';

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: email, password })
      });
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem('token', data.access_token);
        // Assuming the user object is returned directly or within a 'user' key
        const userPayload = data.user || { email, name: email.split('@')[0] };
        localStorage.setItem('user', JSON.stringify(userPayload));
        onSuccess(userPayload);
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
    <Modal isOpen={isOpen} onClose={onClose} title="Login">
      <form onSubmit={handleLogin} className="space-y-4">
        {error && <div className="text-red-500 text-sm font-bold">{error}</div>}
        <AuthFormInput type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <AuthFormInput type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <Button type="submit" className="w-full bg-red-500 text-white hover:bg-red-600" disabled={loading}>
          {loading ? <LoadingSpinner /> : 'Login'}
        </Button>
        <p className="text-center text-sm text-zinc-400">
          No account? <button type="button" onClick={onSwitch} className="font-bold text-white underline hover:text-red-500">Sign up</button>
        </p>
      </form>
    </Modal>
  );
};

const SignupModal = ({ isOpen, onClose, onSwitch, onSuccess }) => {
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const API_URL = 'http://localhost:8001/api/v1';

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
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Sign Up">
      <form onSubmit={handleSignup} className="space-y-4">
        {error && <div className="text-red-500 text-sm font-bold">{error}</div>}
        <AuthFormInput type="text" placeholder="Full Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
        <AuthFormInput type="email" placeholder="Email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} required />
        <AuthFormInput type="password" placeholder="Password" value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} required />
        <Button type="submit" className="w-full bg-red-500 text-white hover:bg-red-600" disabled={loading}>
          {loading ? <LoadingSpinner /> : 'Create Account'}
        </Button>
        <p className="text-center text-sm text-zinc-400">
          Already have an account? <button type="button" onClick={onSwitch} className="font-bold text-white underline hover:text-red-500">Log in</button>
        </p>
      </form>
    </Modal>
  );
};

// --- E-COMMERCE COMPONENTS ---
const CartModal = ({ isOpen, onClose }) => {
    const { cart, updateQuantity, removeFromCart, clearCart } = useCart();
    const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Shopping Cart">
            {cart.length === 0 ? (
                <p className="text-zinc-400">Your cart is empty.</p>
            ) : (
                <div className="space-y-4">
                    {cart.map(item => (
                        <div key={item.id} className="flex items-center justify-between border-b border-zinc-700 pb-2">
                            <div>
                                <p className="font-bold">{item.name}</p>
                                <p className="text-sm text-zinc-400">${item.price.toFixed(2)}</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <button onClick={() => updateQuantity(item.id, item.quantity - 1)} className="p-1 border border-zinc-600 hover:bg-zinc-700"><Minus /></button>
                                <span>{item.quantity}</span>
                                <button onClick={() => updateQuantity(item.id, item.quantity + 1)} className="p-1 border border-zinc-600 hover:bg-zinc-700"><Plus /></button>
                                <button onClick={() => removeFromCart(item.id)} className="ml-2 text-red-500 hover:text-red-400"><X /></button>
                            </div>
                        </div>
                    ))}
                    <div className="pt-4 text-right">
                        <p className="text-lg font-bold">Subtotal: ${subtotal.toFixed(2)}</p>
                        <p className="text-sm text-zinc-500">Delivery fee calculated at checkout.</p>
                    </div>
                    <div className="flex gap-4 pt-4">
                        <Button onClick={clearCart} className="w-full bg-zinc-700 text-white hover:bg-zinc-600">Clear Cart</Button>
                        <Button className="w-full bg-red-500 text-white hover:bg-red-600">Checkout</Button>
                    </div>
                </div>
            )}
        </Modal>
    );
};

const ProductCard = ({ product }) => {
    const { addToCart } = useCart();
    return (
        <motion.div 
            className="bg-black/50 backdrop-blur-md p-4 flex flex-col justify-between border-2 border-white/10 group"
            whileHover={{ y: -8, scale: 1.02 }}
            transition={{ type: 'spring', stiffness: 300 }}
        >
            <div>
                <div className="aspect-square bg-zinc-800 mb-4 flex items-center justify-center">
                    {/* Placeholder for image */}
                    <span className="text-zinc-500 text-sm">Image</span>
                </div>
                <h3 className="font-bold uppercase tracking-wider text-white">{product.name}</h3>
                <p className="text-red-400 font-bold">${product.price.toFixed(2)}</p>
            </div>
            <Button onClick={() => addToCart(product)} className="w-full mt-4">Add to Cart</Button>
        </motion.div>
    );
};

// --- LAYOUT & PAGE COMPONENTS ---
const GeometricHeader = ({ onLogin, onSignup, onLogout, onCartClick }) => {
    const { user } = useAuth();
    const { cartCount } = useCart();

    return (
        <motion.header
            className="col-span-6 row-span-1 bg-black flex items-center justify-between p-6 border-b-2 border-white"
            initial={{ y: -100 }}
            animate={{ y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
        >
            <h1 className="text-2xl font-black uppercase tracking-widest text-white">
                Grocer<span className="text-red-500">.io</span>
            </h1>
            <nav className="flex items-center gap-4">
                <button onClick={onCartClick} className="relative text-white hover:text-red-500 transition-colors duration-300">
                    <ShoppingCart />
                    {cartCount > 0 && (
                        <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-bold">
                            {cartCount}
                        </span>
                    )}
                </button>
                {user ? (
                    <div className="flex items-center gap-4">
                        <span className="text-white hidden sm:block">Hi, {user.name}</span>
                        <button onClick={onLogout} className="text-white uppercase font-bold tracking-wider hover:text-red-500 transition-colors">Logout</button>
                    </div>
                ) : (
                    <div className="flex items-center gap-2">
                        <button onClick={onLogin} className="text-white uppercase font-bold tracking-wider hover:text-red-500 transition-colors">Login</button>
                        <Button onClick={onSignup} className="hidden sm:inline-flex">Sign Up</Button>
                    </div>
                )}
            </nav>
        </motion.header>
    );
};

const HeroBlock = ({ onSignup }) => (
    <motion.div 
        className="col-span-6 md:col-span-4 row-span-2 bg-gradient-to-br from-red-500 via-pink-500 to-rose-400 flex flex-col justify-center items-start p-8 md:p-12"
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.7, delay: 0.2, ease: 'easeOut' }}
    >
        <h2 className="font-black text-5xl md:text-7xl text-white uppercase tracking-tighter leading-none mb-4">
            Fresh Groceries.
            <br />
            Delivered Fast.
        </h2>
        <p className="text-white/80 max-w-md mb-8 text-lg">
            Experience the future of grocery shopping. Quality produce, pantry staples, and more, right to your doorstep.
        </p>
        <Button onClick={onSignup} className="bg-black text-white hover:bg-white hover:text-black">
            Start Shopping <ArrowRight className="ml-2" />
        </Button>
    </motion.div>
);

const SearchBlock = () => (
    <motion.div 
        className="col-span-6 md:col-span-2 row-span-1 bg-[#f59e0b] p-8 flex flex-col justify-center"
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.4, ease: 'easeOut' }}
    >
        <h3 className="text-2xl font-bold uppercase text-black tracking-wider mb-4">Find Anything</h3>
        <div className="relative">
            <input 
                type="text" 
                placeholder="Search for 'avocado'..."
                className="w-full bg-white/50 text-black placeholder-black/60 p-4 pl-12 rounded-none border-2 border-black focus:outline-none focus:bg-white"
            />
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-black" />
        </div>
    </motion.div>
);

const PromotionsBlock = () => (
    <motion.div 
        className="col-span-6 md:col-span-2 row-span-1 bg-red-500 p-8 flex flex-col justify-center"
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.6, ease: 'easeOut' }}
    >
        <h3 className="text-3xl font-bold uppercase text-white tracking-wider mb-2">Weekly Deals</h3>
        <div className="space-y-2">
            {mockPromotions.slice(0, 2).map(promo => (
                <div key={promo.id} className="bg-black/20 p-3 text-white">
                    <p className="font-bold">{promo.title}</p>
                    <p className="text-sm opacity-80">{promo.description}</p>
                </div>
            ))}
        </div>
    </motion.div>
);

const FeaturedProductsBlock = ({ products }) => (
    <motion.div 
        className="col-span-6 md:col-span-4 row-span-2 bg-zinc-800 p-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.7, delay: 0.8, ease: 'easeOut' }}
    >
        <h3 className="text-3xl font-bold uppercase text-white tracking-wider mb-6">Featured Products</h3>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            {products.slice(0, 3).map(p => <ProductCard key={p.id} product={p} />)}
        </div>
    </motion.div>
);

// --- PROVIDER COMPONENTS ---
const AppProviders = ({ children }) => {
    const [user, setUser] = useState(null);
    const [cart, setCart] = useState([]);
    const [notifications, setNotifications] = useState([]);

    useEffect(() => {
        const token = localStorage.getItem('token');
        const savedUser = localStorage.getItem('user');
        if (token && savedUser && savedUser !== 'undefined') {
            try {
                setUser(JSON.parse(savedUser));
            } catch (e) {
                console.error("Failed to parse user from localStorage", e);
                localStorage.clear();
            }
        }
    }, []);

    const showNotification = (message, type = 'success') => {
        const id = Date.now();
        setNotifications(prev => [...prev, { id, message, type }]);
        setTimeout(() => {
            setNotifications(prev => prev.filter(n => n.id !== id));
        }, 3000);
    };

    const authContextValue = {
        user,
        setUser,
        login: (userData) => {
            setUser(userData);
            showNotification('Login successful!', 'success');
        },
        logout: () => {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            setUser(null);
            setCart([]);
            showNotification('Logged out successfully', 'success');
        }
    };

    const cartContextValue = {
        cart,
        addToCart: (product) => {
            setCart(prev => {
                const existing = prev.find(item => item.id === product.id);
                if (existing) {
                    return prev.map(item => item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item);
                }
                return [...prev, { ...product, quantity: 1 }];
            });
            showNotification(`${product.name} added to cart!`, 'success');
        },
        updateQuantity: (productId, quantity) => {
            if (quantity < 1) {
                setCart(prev => prev.filter(item => item.id !== productId));
            } else {
                setCart(prev => prev.map(item => item.id === productId ? { ...item, quantity } : item));
            }
        },
        removeFromCart: (productId) => {
            setCart(prev => prev.filter(item => item.id !== productId));
        },
        clearCart: () => setCart([]),
        cartCount: cart.reduce((sum, item) => sum + item.quantity, 0),
    };

    return (
        <AuthContext.Provider value={authContextValue}>
            <CartContext.Provider value={cartContextValue}>
                <NotificationContext.Provider value={showNotification}>
                    {children}
                    <div className="fixed bottom-0 right-0 m-4 z-[100]">
                        <AnimatePresence>
                            {notifications.map(n => (
                                <Toast key={n.id} message={n.message} type={n.type} onClose={() => setNotifications(p => p.filter(item => item.id !== n.id))} />
                            ))}
                        </AnimatePresence>
                    </div>
                </NotificationContext.Provider>
            </CartContext.Provider>
        </AuthContext.Provider>
    );
};

// --- MAIN APP COMPONENT ---
const App = () => {
    const [showLogin, setShowLogin] = useState(false);
    const [showSignup, setShowSignup] = useState(false);
    const [showCart, setShowCart] = useState(false);
    const [products, setProducts] = useState([]);

    useEffect(() => {
        // Simulate API call for products
        setProducts(mockProducts);
    }, []);

    return (
        <AppProviders>
            <BauhausGroceryApp
                products={products}
                onLogin={() => setShowLogin(true)}
                onSignup={() => setShowSignup(true)}
                onCartClick={() => setShowCart(true)}
            />
            <AuthModals
                showLogin={showLogin}
                setShowLogin={setShowLogin}
                showSignup={showSignup}
                setShowSignup={setShowSignup}
            />
            <CartModal isOpen={showCart} onClose={() => setShowCart(false)} />
        </AppProviders>
    );
};

const BauhausGroceryApp = ({ products, onLogin, onSignup, onCartClick }) => {
    const { logout } = useAuth();
    return (
        <div className="bg-zinc-900 min-h-screen font-sans text-white antialiased">
            <div className="p-2 md:p-4">
                <div className="grid grid-cols-6 grid-rows-[auto_repeat(4,_minmax(0,_1fr))] md:grid-rows-4 gap-2 h-[calc(100vh-1rem)] md:h-[calc(100vh-2rem)]">
                    <GeometricHeader onLogin={onLogin} onSignup={onSignup} onLogout={logout} onCartClick={onCartClick} />
                    <HeroBlock onSignup={onSignup} />
                    <SearchBlock />
                    <PromotionsBlock />
                    <FeaturedProductsBlock products={products} />
                </div>
            </div>
        </div>
    );
};

const AuthModals = ({ showLogin, setShowLogin, showSignup, setShowSignup }) => {
    const { login } = useAuth();
    return (
        <>
            <AnimatePresence>
                {showLogin && (
                    <LoginModal
                        isOpen={showLogin}
                        onClose={() => setShowLogin(false)}
                        onSuccess={login}
                        onSwitch={() => { setShowLogin(false); setShowSignup(true); }}
                    />
                )}
            </AnimatePresence>
            <AnimatePresence>
                {showSignup && (
                    <SignupModal
                        isOpen={showSignup}
                        onClose={() => setShowSignup(false)}
                        onSuccess={login}
                        onSwitch={() => { setShowSignup(false); setShowLogin(true); }}
                    />
                )}
            </AnimatePresence>
        </>
    );
};

export default App;