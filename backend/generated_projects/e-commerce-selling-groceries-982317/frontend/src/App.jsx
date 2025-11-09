import React from 'react';

// --- UTILITY IMPORTS ---
import { cn, twMerge } from './lib/utils.js';

// Make twMerge globally available for inline components
window.twMerge = twMerge;

const buttonVariants = {
  default: "bg-indigo-600 text-white hover:bg-indigo-700",
  destructive: "bg-red-600 text-white hover:bg-red-700",
  outline: "border border-gray-600 bg-transparent hover:bg-gray-800 hover:text-white",
  secondary: "bg-gray-700 text-white hover:bg-gray-600",
  ghost: "hover:bg-gray-800 hover:text-white",
  link: "text-indigo-400 underline-offset-4 hover:underline",
};

const cardVariants = {
  default: "bg-gray-900 border border-gray-700 rounded-lg shadow-md text-white",
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
const Zap = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>;
const Leaf = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 20A7 7 0 0 1 4 13V6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v1a1 1 0 0 0 2 0V6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v7a7 7 0 0 1-7 7z"></path><path d="M9 21c0-3 4-3 4-6"></path></svg>;
const BookOpen = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>;
const MapPin = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>;
const Repeat = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m17 2 4 4-4 4"></path><path d="M3 11v-1a4 4 0 0 1 4-4h14"></path><path d="m7 22-4-4 4-4"></path><path d="M21 13v1a4 4 0 0 1-4 4H3"></path></svg>;
const Columns = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"></rect><line x1="12" x2="12" y1="3" y2="21"></line></svg>;

// --- UI COMPONENTS ---
const Button = React.forwardRef(({ className, variant, size, ...props }, ref) => {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        "px-4 py-2",
        buttonVariants[variant] || buttonVariants.default,
        className
      )}
      ref={ref}
      {...props}
    />
  );
});

const Card = React.forwardRef(({ className, variant, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(cardVariants[variant] || cardVariants.default, className)}
    {...props}
  />
));

const Input = React.forwardRef(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        "flex h-10 w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500",
        className
      )}
      ref={ref}
      {...props}
    />
  );
});

const Select = React.forwardRef(({ className, children, ...props }, ref) => {
  return (
    <select
      className={cn(
        "flex h-10 w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500",
        className
      )}
      ref={ref}
      {...props}
    >
      {children}
    </select>
  );
});

const Modal = ({ isOpen, onClose, children, title }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto text-white shadow-2xl shadow-indigo-500/10">
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-xl font-semibold">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};

const LoadingSpinner = ({ className }) => (
  <div className={cn("animate-spin rounded-full h-6 w-6 border-b-2 border-white", className)}></div>
);

const Toast = ({ message, type, onClose }) => (
  <div className={cn(
    "fixed top-20 right-4 p-4 rounded-md shadow-lg z-[100] transition-all text-white",
    type === "success" ? "bg-green-600" : "bg-red-600"
  )}>
    <div className="flex items-center justify-between">
      <span>{message}</span>
      <button onClick={onClose} className="ml-4 text-white hover:text-gray-200">
        <X />
      </button>
    </div>
  </div>
);

// --- AUTHENTICATION COMPONENTS ---
const LoginModal = ({ isOpen, onClose, onSwitchToSignup }) => {
  const { login } = useAuth();
  const showNotification = useNotification();
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');

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
        {error && <div className="text-red-400 text-sm p-2 bg-red-900/50 rounded">{error}</div>}
        <Input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <Input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner /> : 'Login'}
        </Button>
        <p className="text-center text-sm text-gray-400">
          Don't have an account?{' '}
          <button type="button" onClick={onSwitchToSignup} className="font-medium text-indigo-400 hover:underline">
            Sign up
          </button>
        </p>
      </form>
    </Modal>
  );
};

const SignupModal = ({ isOpen, onClose, onSwitchToLogin }) => {
  const { login } = useAuth();
  const showNotification = useNotification();
  const [formData, setFormData] = React.useState({ name: '', email: '', password: '', confirmPassword: '' });
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

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
        login(data.user, data.access_token);
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
        {error && <div className="text-red-400 text-sm p-2 bg-red-900/50 rounded">{error}</div>}
        <Input name="name" type="text" placeholder="Full Name" value={formData.name} onChange={handleChange} required />
        <Input name="email" type="email" placeholder="Email" value={formData.email} onChange={handleChange} required />
        <Input name="password" type="password" placeholder="Password" value={formData.password} onChange={handleChange} required />
        <Input name="confirmPassword" type="password" placeholder="Confirm Password" value={formData.confirmPassword} onChange={handleChange} required />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner /> : 'Sign Up'}
        </Button>
        <p className="text-center text-sm text-gray-400">
          Already have an account?{' '}
          <button type="button" onClick={onSwitchToLogin} className="font-medium text-indigo-400 hover:underline">
            Login
          </button>
        </p>
      </form>
    </Modal>
  );
};

// --- E-COMMERCE & FEATURE COMPONENTS ---
const CartModal = ({ isOpen, onClose }) => {
    const { cart, updateQuantity, removeFromCart, clearCart, cartTotal, cartCount } = useCart();
    const [deliverySlot, setDeliverySlot] = React.useState('');
    const hasGroceries = cart.some(item => item.category === 'Groceries');

    const handleCheckout = () => {
        alert(`Checkout for ${cartCount} items, total: $${cartTotal.toFixed(2)}. Delivery slot: ${deliverySlot || 'N/A'}`);
        clearCart();
        onClose();
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={`Shopping Cart (${cartCount})`}>
            {cart.length === 0 ? (
                <p className="text-gray-400">Your cart is empty.</p>
            ) : (
                <div className="space-y-4">
                    {(cart || []).map(item => (
                        <div key={item.id} className="flex items-center justify-between p-2 bg-gray-800 rounded">
                            <div className="flex items-center space-x-3">
                                <img src={item.image} alt={item.name} className="w-16 h-16 object-cover rounded" />
                                <div>
                                    <p className="font-semibold">{item.name}</p>
                                    <p className="text-sm text-gray-400">${item.price.toFixed(2)}</p>
                                </div>
                            </div>
                            <div className="flex items-center space-x-2">
                                <Button variant="ghost" size="sm" onClick={() => updateQuantity(item.id, item.quantity - 1)}><Minus className="h-4 w-4" /></Button>
                                <span>{item.quantity}</span>
                                <Button variant="ghost" size="sm" onClick={() => updateQuantity(item.id, item.quantity + 1)}><Plus className="h-4 w-4" /></Button>
                                <Button variant="destructive" size="sm" onClick={() => removeFromCart(item.id)}><X className="h-4 w-4" /></Button>
                            </div>
                        </div>
                    ))}
                    <div className="border-t border-gray-700 pt-4 space-y-4">
                        {hasGroceries && (
                            <div>
                                <label htmlFor="delivery-slot" className="block text-sm font-medium text-gray-300 mb-2">Scheduled Grocery Delivery</label>
                                <Select id="delivery-slot" value={deliverySlot} onChange={(e) => setDeliverySlot(e.target.value)}>
                                    <option value="">Select a time slot</option>
                                    <option value="today-5-7pm">Today, 5 PM - 7 PM</option>
                                    <option value="tomorrow-9-11am">Tomorrow, 9 AM - 11 AM</option>
                                    <option value="tomorrow-5-7pm">Tomorrow, 5 PM - 7 PM</option>
                                </Select>
                            </div>
                        )}
                        <div className="flex justify-between items-center text-lg font-bold">
                            <span>Total:</span>
                            <span>${cartTotal.toFixed(2)}</span>
                        </div>
                        <Button className="w-full" onClick={handleCheckout}>Proceed to Checkout</Button>
                    </div>
                </div>
            )}
        </Modal>
    );
};

const ComparisonModal = ({ isOpen, onClose, items }) => {
    if (!items || items.length === 0) return null;

    const specs = ['brand', 'screen_size', 'ram', 'storage', 'camera'];

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Product Comparison">
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead>
                        <tr className="border-b border-gray-700">
                            <th className="p-2">Specification</th>
                            {(items || []).map(item => <th key={item.id} className="p-2">{item.name}</th>)}
                        </tr>
                    </thead>
                    <tbody>
                        {(specs || []).map(spec => (
                            <tr key={spec} className="border-b border-gray-800">
                                <td className="p-2 font-semibold capitalize">{spec.replace('_', ' ')}</td>
                                {(items || []).map(item => (
                                    <td key={item.id} className="p-2">{item.specs[spec] || 'N/A'}</td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </Modal>
    );
};

const ProductCard = ({ product, onCompareToggle, isComparing }) => {
    const { addToCart } = useCart();
    const showNotification = useNotification();

    const handleAddToCart = () => {
        addToCart(product);
        showNotification(`${product.name} added to cart!`, 'success');
    };

    return (
        <Card className="flex flex-col">
            <img src={product.image} alt={product.name} className="w-full h-48 object-cover rounded-t-lg" />
            <div className="p-4 flex flex-col flex-grow">
                <h3 className="text-lg font-semibold mb-2">{product.name}</h3>
                <p className="text-gray-400 text-sm mb-4 flex-grow">{product.description}</p>
                <div className="flex justify-between items-center mt-auto">
                    <span className="text-xl font-bold text-indigo-400">${product.price.toFixed(2)}</span>
                    <div className="flex items-center space-x-2">
                        {product.category === 'Electronics' && (
                            <Button variant={isComparing ? "secondary" : "outline"} onClick={() => onCompareToggle(product)}>
                                <Columns className="h-4 w-4" />
                            </Button>
                        )}
                        <Button onClick={handleAddToCart}>Add to Cart</Button>
                    </div>
                </div>
            </div>
        </Card>
    );
};

const RecipeCard = ({ recipe }) => {
    const { addMultipleToCart } = useCart();
    const showNotification = useNotification();

    const handleAddIngredients = () => {
        addMultipleToCart(recipe.ingredients);
        showNotification(`Ingredients for ${recipe.name} added to cart!`, 'success');
    };

    return (
        <Card className="flex flex-col">
            <img src={recipe.image} alt={recipe.name} className="w-full h-48 object-cover rounded-t-lg" />
            <div className="p-4 flex flex-col flex-grow">
                <h3 className="text-lg font-semibold mb-2">{recipe.name}</h3>
                <p className="text-gray-400 text-sm mb-2">Ingredients: {(recipe.ingredients || []).map(i => i.name).join(', ')}</p>
                <Button onClick={handleAddIngredients} className="mt-auto">Add Ingredients to Cart</Button>
            </div>
        </Card>
    );
};

// --- LAYOUT COMPONENTS ---
const Header = () => {
  const { user, logout } = useAuth();
  const { cartCount } = useCart();
  const { setShowLogin, setShowSignup, setShowCart } = React.useContext(AppContext);

  return (
    <header className="bg-gray-900/80 backdrop-blur-sm border-b border-gray-700 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <a href="#" className="text-2xl font-bold text-white flex items-center gap-2">
              <Zap className="text-indigo-400"/> GrocerTronics
            </a>
          </div>
          <div className="flex items-center space-x-4">
            <button onClick={() => setShowCart(true)} className="relative text-gray-300 hover:text-white">
              <ShoppingCart />
              {cartCount > 0 && (
                <span className="absolute -top-2 -right-2 bg-indigo-600 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                  {cartCount}
                </span>
              )}
            </button>
            {user ? (
              <div className="flex items-center space-x-4">
                <span className="text-gray-300 hidden sm:block">Welcome, {user.name}</span>
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
  );
};

const Footer = () => (
    <footer className="bg-gray-900 border-t border-gray-700 mt-16">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 text-center text-gray-400">
            <p>&copy; {new Date().getFullYear()} GrocerTronics. All rights reserved.</p>
            <p className="text-sm mt-1">Your one-stop shop for groceries and electronics.</p>
        </div>
    </footer>
);

const AppContext = React.createContext(null);

// --- MAIN APP COMPONENT ---
const App = () => {
  // --- STATE MANAGEMENT ---
  const [user, setUser] = React.useState(null);
  const [cart, setCart] = React.useState([]);
  const [notifications, setNotifications] = React.useState([]);
  const [products, setProducts] = React.useState([]);
  const [recipes, setRecipes] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  
  const [showLogin, setShowLogin] = React.useState(false);
  const [showSignup, setShowSignup] = React.useState(false);
  const [showCart, setShowCart] = React.useState(false);
  const [showComparison, setShowComparison] = React.useState(false);

  const [comparisonList, setComparisonList] = React.useState([]);
  const [activeCategory, setActiveCategory] = React.useState('All');
  const [filters, setFilters] = React.useState({
      groceries: { organic: false, glutenFree: false },
      electronics: { brand: 'All' }
  });

  // --- DATA FETCHING ---
  React.useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('token');
      const savedUser = localStorage.getItem('user');
      if (token && savedUser) {
        setUser(JSON.parse(savedUser));
      }
    };

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        // In a real app, these would be separate API calls.
        // We simulate a single fetch for simplicity.
        const response = await fetch('http://localhost:8001/api/v1/shop/initial-data');
        if (!response.ok) throw new Error('Failed to fetch data');
        const data = await response.json();
        setProducts(data.products);
        setRecipes(data.recipes);
      } catch (err) {
        setError('Could not load shop data. Using mock data instead.');
        // Mock data as a fallback
        setProducts([
            { id: 1, name: 'Organic Bananas', price: 1.99, category: 'Groceries', description: 'A bunch of fresh, organic bananas.', image: 'https://via.placeholder.com/300x200/FFD700/000000?text=Bananas', specs: { organic: true, glutenFree: true } },
            { id: 2, name: 'Whole Wheat Bread', price: 3.49, category: 'Groceries', description: 'A loaf of healthy whole wheat bread.', image: 'https://via.placeholder.com/300x200/8B4513/FFFFFF?text=Bread', specs: { organic: false, glutenFree: false } },
            { id: 3, name: 'Laptop Pro 16"', price: 2399.00, category: 'Electronics', description: 'The latest high-performance laptop.', image: 'https://via.placeholder.com/300x200/333333/FFFFFF?text=Laptop', specs: { brand: 'TechCorp', screen_size: '16 inch', ram: '32GB', storage: '1TB SSD', camera: '1080p' } },
            { id: 4, name: 'Smartphone X', price: 999.00, category: 'Electronics', description: 'A sleek and powerful smartphone.', image: 'https://via.placeholder.com/300x200/1E90FF/FFFFFF?text=Phone', specs: { brand: 'GadgetCo', screen_size: '6.7 inch', ram: '8GB', storage: '256GB', camera: '48MP' } },
            { id: 5, name: 'Gluten-Free Pasta', price: 4.99, category: 'Groceries', description: 'Delicious pasta for a gluten-free diet.', image: 'https://via.placeholder.com/300x200/F0E68C/000000?text=Pasta', specs: { organic: false, glutenFree: true } },
            { id: 6, name: '4K Smart TV 55"', price: 799.00, category: 'Electronics', description: 'Immersive viewing experience.', image: 'https://via.placeholder.com/300x200/00008B/FFFFFF?text=TV', specs: { brand: 'VisionElec', screen_size: '55 inch', ram: 'N/A', storage: 'N/A', camera: 'N/A' } },
        ]);
        setRecipes([
            { id: 1, name: 'Classic Pasta Dish', image: 'https://via.placeholder.com/300x200/FF6347/FFFFFF?text=Pasta+Dish', ingredients: [{ id: 5, name: 'Gluten-Free Pasta', quantity: 1 }, { id: 1, name: 'Organic Bananas', quantity: 1 }] },
            { id: 2, name: 'Simple Sandwich', image: 'https://via.placeholder.com/300x200/4682B4/FFFFFF?text=Sandwich', ingredients: [{ id: 2, name: 'Whole Wheat Bread', quantity: 1 }] },
        ]);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
    fetchData();
  }, []);

  // --- HANDLERS & CONTEXT VALUES ---
  const showNotification = (message, type = 'success') => {
    const id = Date.now();
    setNotifications(prev => [...(prev || []), { id, message, type }]);
    setTimeout(() => {
      setNotifications(prev => (prev || []).filter(n => n.id !== id));
    }, 3000);
  };

  const authContextValue = {
    user,
    login: (userData, token) => {
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
    },
    logout: () => {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setUser(null);
      showNotification('Logged out successfully', 'success');
    },
  };

  const cartContextValue = {
    cart,
    addToCart: (product) => {
      setCart(prev => {
        const existing = (prev || []).find(item => item.id === product.id);
        if (existing) {
          return (prev || []).map(item => item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item);
        }
        return [...(prev || []), { ...product, quantity: 1 }];
      });
    },
    addMultipleToCart: (productsToAdd) => {
        setCart(prevCart => {
            let newCart = [...(prevCart || [])];
            (productsToAdd || []).forEach(productToAdd => {
                const existingIndex = newCart.findIndex(item => item.id === productToAdd.id);
                if (existingIndex > -1) {
                    newCart[existingIndex].quantity += productToAdd.quantity || 1;
                } else {
                    const productDetails = (products || []).find(p => p.id === productToAdd.id);
                    if (productDetails) {
                        newCart.push({ ...productDetails, quantity: productToAdd.quantity || 1 });
                    }
                }
            });
            return newCart;
        });
    },
    removeFromCart: (productId) => setCart(prev => (prev || []).filter(item => item.id !== productId)),
    updateQuantity: (productId, quantity) => {
      if (quantity <= 0) {
        cartContextValue.removeFromCart(productId);
      } else {
        setCart(prev => (prev || []).map(item => item.id === productId ? { ...item, quantity } : item));
      }
    },
    clearCart: () => setCart([]),
    cartCount: (cart || []).reduce((sum, item) => sum + item.quantity, 0),
    cartTotal: (cart || []).reduce((sum, item) => sum + item.price * item.quantity, 0),
  };

  const handleCompareToggle = (product) => {
    setComparisonList(prev => {
        const currentList = prev || [];
        const isPresent = currentList.find(p => p.id === product.id);
        if (isPresent) {
            return currentList.filter(p => p.id !== product.id);
        }
        if (currentList.length < 4) {
            return [...currentList, product];
        }
        showNotification('You can compare up to 4 items.', 'error');
        return currentList;
    });
  };

  const handleFilterChange = (category, filterName, value) => {
      setFilters(prev => ({
          ...prev,
          [category]: { ...prev[category], [filterName]: value }
      }));
  };

  const filteredProducts = (products || []).filter(p => {
      if (activeCategory !== 'All' && p.category !== activeCategory) return false;
      if (p.category === 'Groceries') {
          if (filters.groceries.organic && !p.specs.organic) return false;
          if (filters.groceries.glutenFree && !p.specs.glutenFree) return false;
      }
      if (p.category === 'Electronics') {
          if (filters.electronics.brand !== 'All' && p.specs.brand !== filters.electronics.brand) return false;
      }
      return true;
  });

  const featureList = [
      { icon: <Leaf/>, name: 'Dynamic Filtering', desc: "Filter groceries by 'Organic' or electronics by 'Brand'." },
      { icon: <BookOpen/>, name: 'Recipe-to-Cart', desc: "Add all ingredients for a recipe to your cart with one click." },
      { icon: <Columns/>, name: 'Spec Comparator', desc: "Compare up to 4 electronic devices side-by-side." },
      { icon: <MapPin/>, name: 'Real-Time Tracking', desc: "Track your grocery delivery on a map or get carrier info for electronics." },
      { icon: <Repeat/>, name: 'Grocery Subscriptions', desc: "Automate your essential shopping with recurring deliveries." },
  ];

  // Show loading screen while data is being fetched
  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white font-sans flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-xl">Loading your shopping experience...</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={authContextValue}>
      <CartContext.Provider value={cartContextValue}>
        <NotificationContext.Provider value={showNotification}>
          <AppContext.Provider value={{ setShowLogin, setShowSignup, setShowCart }}>
            <div className="min-h-screen bg-black text-white font-sans">
              <Header />
              
              <main>
                {/* Hero Section */}
                <section className="bg-gray-900 py-20 sm:py-32 text-center relative overflow-hidden">
                    <div className="absolute inset-0 bg-grid-gray-700/[0.2] [mask-image:linear-gradient(to_bottom,white_5%,transparent_90%)]"></div>
                    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative">
                        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-500">
                            Groceries & Gadgets, Delivered.
                        </h1>
                        <p className="mt-6 text-lg text-gray-300 max-w-2xl mx-auto">
                            The ultimate convenience. Your one-stop shop for fresh organic produce and the latest high-tech electronics, all in a seamless, premium experience.
                        </p>
                        <div className="mt-10 flex justify-center gap-4">
                            <Button onClick={() => document.getElementById('products').scrollIntoView({ behavior: 'smooth' })}>Shop Now</Button>
                            <Button variant="outline" onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}>Learn More</Button>
                        </div>
                    </div>
                </section>

                {/* Features Section */}
                <section id="features" className="py-24 sm:py-32">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="text-center">
                            <h2 className="text-3xl font-bold tracking-tight">A Smarter Way to Shop</h2>
                            <p className="mt-4 text-lg text-gray-400">Specialized features for a tailored experience.</p>
                        </div>
                        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {(featureList || []).map(feature => (
                                <div key={feature.name} className="p-6 bg-gray-900 border border-gray-800 rounded-lg">
                                    <div className="text-indigo-400 mb-4">{React.cloneElement(feature.icon, { className: "h-8 w-8" })}</div>
                                    <h3 className="text-lg font-semibold">{feature.name}</h3>
                                    <p className="mt-2 text-gray-400">{feature.desc}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* Products Section */}
                <section id="products" className="py-24 sm:py-32 bg-gray-900/50">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="text-center mb-12">
                            <h2 className="text-3xl font-bold tracking-tight">Our Products</h2>
                            <p className="mt-4 text-lg text-gray-400">Everything you need, from pantry to processor.</p>
                        </div>

                        {/* Filters */}
                        <div className="mb-8 p-4 bg-gray-900 rounded-lg border border-gray-700 flex flex-col md:flex-row gap-4 justify-between items-center">
                            <div className="flex gap-2">
                                {['All', 'Groceries', 'Electronics'].map(cat => (
                                    <Button key={cat} variant={activeCategory === cat ? 'default' : 'secondary'} onClick={() => setActiveCategory(cat)}>{cat}</Button>
                                ))}
                            </div>
                            {activeCategory === 'Groceries' && (
                                <div className="flex items-center gap-4">
                                    <label className="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked={filters.groceries.organic} onChange={e => handleFilterChange('groceries', 'organic', e.target.checked)} className="form-checkbox bg-gray-800 border-gray-600 text-indigo-500" /> Organic</label>
                                    <label className="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked={filters.groceries.glutenFree} onChange={e => handleFilterChange('groceries', 'glutenFree', e.target.checked)} className="form-checkbox bg-gray-800 border-gray-600 text-indigo-500" /> Gluten-Free</label>
                                </div>
                            )}
                            {activeCategory === 'Electronics' && (
                                <div className="flex items-center gap-2">
                                    <label>Brand:</label>
                                    <Select value={filters.electronics.brand} onChange={e => handleFilterChange('electronics', 'brand', e.target.value)}>
                                        <option>All</option>
                                        <option>TechCorp</option>
                                        <option>GadgetCo</option>
                                        <option>VisionElec</option>
                                    </Select>
                                </div>
                            )}
                        </div>

                        {loading ? <div className="flex justify-center"><LoadingSpinner className="h-12 w-12"/></div> : error ? <p className="text-center text-red-400">{error}</p> : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                                {filteredProducts.map(product => (
                                    <ProductCard key={product.id} product={product} onCompareToggle={handleCompareToggle} isComparing={comparisonList.some(p => p.id === product.id)} />
                                ))}
                            </div>
                        )}
                        {comparisonList.length > 0 && (
                            <div className="fixed bottom-4 right-4 z-30">
                                <Button onClick={() => setShowComparison(true)}>Compare ({comparisonList.length})</Button>
                            </div>
                        )}
                    </div>
                </section>

                {/* Recipes Section */}
                <section className="py-24 sm:py-32">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="text-center mb-12">
                            <h2 className="text-3xl font-bold tracking-tight">Meal Inspiration</h2>
                            <p className="mt-4 text-lg text-gray-400">From our kitchen to yours. Add all ingredients with a single click.</p>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {(recipes || []).map(recipe => <RecipeCard key={recipe.id} recipe={recipe} />)}
                        </div>
                    </div>
                </section>
              </main>

              <Footer />

              {/* Modals */}
              <LoginModal isOpen={showLogin} onClose={() => setShowLogin(false)} onSwitchToSignup={() => { setShowLogin(false); setShowSignup(true); }} />
              <SignupModal isOpen={showSignup} onClose={() => setShowSignup(false)} onSwitchToLogin={() => { setShowSignup(false); setShowLogin(true); }} />
              <CartModal isOpen={showCart} onClose={() => setShowCart(false)} />
              <ComparisonModal isOpen={showComparison} onClose={() => setShowComparison(false)} items={comparisonList} />

              {/* Notifications */}
              <div className="fixed top-4 right-4 z-[100] space-y-2">
                {(notifications || []).map(n => (
                  <Toast key={n.id} message={n.message} type={n.type} onClose={() => setNotifications(p => (p || []).filter(item => item.id !== n.id))} />
                ))}
              </div>
            </div>
          </AppContext.Provider>
        </NotificationContext.Provider>
      </CartContext.Provider>
    </AuthContext.Provider>
  );
};

export default App;