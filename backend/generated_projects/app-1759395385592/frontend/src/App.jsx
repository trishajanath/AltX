import React, { useState, useEffect, useCallback } from 'react';

// Import all React Bits components with comprehensive fallbacks
let Button, Card, CardHeader, CardBody;
try {
  const ButtonModule = require('./components/ui/Button');
  Button = ButtonModule.Button;
} catch (error) {
  // Fallback Button
  Button = ({ children, variant = 'primary', size = 'md', className = '', ...props }) => {
    const variants = {
      primary: 'bg-blue-600 hover:bg-blue-700 text-white',
      secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
      outline: 'border border-gray-300 hover:bg-gray-50 text-gray-700'
    };
    const sizes = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base', 
      lg: 'px-6 py-3 text-lg'
    };
    return (
      <button 
        className={`inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${variants[variant]} ${sizes[size]} ${className}`}
        {...(props || {})}
      >
        {children}
      </button>
    );
  };
}

try {
  const CardModule = require('./components/ui/Card');
  Card = CardModule.Card;
  CardHeader = CardModule.CardHeader;
  CardBody = CardModule.CardBody;
} catch (error) {
  // Fallback Card components
  Card = ({ children, className = '' }) => (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      {children}
    </div>
  );
  CardHeader = ({ children, className = '' }) => (
    <div className={`px-6 py-4 border-b border-gray-200 ${className}`}>
      {children}
    </div>
  );
  CardBody = ({ children, className = '' }) => (
    <div className={`px-6 py-4 ${className}`}>
      {children}
    </div>
  );
}

// Import AnimatedText with fallback for reliability
let SplitText, GradientText;
try {
  const AnimatedTextModule = require('./components/ui/AnimatedText');
  SplitText = AnimatedTextModule.SplitText;
  GradientText = AnimatedTextModule.GradientText;
} catch (error) {
  // Fallback SplitText
  SplitText = ({ text, className = '' }) => (
    <span className={`inline-block ${className}`}>{text}</span>
  );
  // Fallback GradientText  
  GradientText = ({ text, className = '' }) => (
    <span className={`bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent ${className}`}>
      {text}
    </span>
  );
}

// Import Navigation with fallback for reliability
let NavBar, NavLink;
try {
  const NavigationModule = require('./components/ui/Navigation');
  NavBar = NavigationModule.NavBar;
  NavLink = NavigationModule.NavLink;
} catch (error) {
  // Fallback NavBar
  NavBar = ({ children, className = '' }) => (
    <nav className={`bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">{children}</div>
      </div>
    </nav>
  );
  NavLink = ({ href, children, isActive, className = '' }) => (
    <a href={href} className={`inline-flex items-center px-1 pt-1 text-sm font-medium transition-colors ${isActive ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'} ${className}`}>
      {children}
    </a>
  );
}

// Import Lucide React icons with fallbacks
let Download, Github, ExternalLink, X, ShoppingCart, User, Menu, Plus, Minus;
try {
  const LucideModule = require('lucide-react');
  Download = LucideModule.Download;
  Github = LucideModule.Github;
  ExternalLink = LucideModule.ExternalLink;
  X = LucideModule.X;
  ShoppingCart = LucideModule.ShoppingCart;
  User = LucideModule.User;
  Menu = LucideModule.Menu;
  Plus = LucideModule.Plus;
  Minus = LucideModule.Minus;
} catch (error) {
  // Fallback icon components using Unicode symbols
  Download = ({ className = '', ...props }) => <span className={`inline-block ${className}`} {...props}>⬇</span>;
  Github = ({ className = '', ...props }) => <span className={`inline-block ${className}`} {...props}>⚡</span>;
  ExternalLink = ({ className = '', ...props }) => <span className={`inline-block ${className}`} {...props}>↗</span>;
  X = ({ className = '', ...props }) => <span className={`inline-block ${className}`} {...props}>✕</span>;
  ShoppingCart = ({ className = '', ...props }) => <span className={`inline-block ${className}`} {...props}>🛒</span>;
  User = ({ className = '', ...props }) => <span className={`inline-block ${className}`} {...props}>👤</span>;
  Menu = ({ className = '', ...props }) => <span className={`inline-block ${className}`} {...props}>☰</span>;
  Plus = ({ className = '', ...props }) => <span className={`inline-block ${className}`} {...props}>+</span>;
  Minus = ({ className = '', ...props }) => <span className={`inline-block ${className}`} {...props}>-</span>;
}

// Include inline SpinnerLoader to avoid import issues
const SpinnerLoader = ({ size = 'md', className = '' }) => {
  const sizes = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' };
  return <div className={`${sizes[size]} border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin ${className}`} />;
};

const API_BASE_URL = 'http://localhost:8000/api/v1';

// --- Inline Components ---

const GlobalHeader = ({ onCartClick }) => {
  const [cartItemCount, setCartItemCount] = useState(0);

  useEffect(() => {
    const updateCartCount = () => {
      try {
        const cartData = localStorage.getItem('app-1759395385592-cart');
        const cart = cartData ? JSON.parse(cartData) : [];
        setCartItemCount(Array.isArray(cart) ? cart.reduce((sum, item) => sum + item.quantity, 0) : 0);
      } catch (error) {
        console.error("Failed to parse cart from localStorage", error);
        setCartItemCount(0);
      }
    };
    
    updateCartCount();
    window.addEventListener('storage', updateCartCount);
    window.addEventListener('cartUpdated', updateCartCount);

    return () => {
      window.removeEventListener('storage', updateCartCount);
      window.removeEventListener('cartUpdated', updateCartCount);
    };
  }, []);

  return (
    <NavBar>
      <div className="flex items-center">
        <GradientText text="AURA" className="text-2xl font-bold" />
      </div>
      <div className="hidden sm:flex items-center space-x-8">
        <NavLink href="#store" isActive>Store</NavLink>
        <NavLink href="#products">Products</NavLink>
        <NavLink href="#about">About</NavLink>
      </div>
      <div className="flex items-center space-x-4">
        <button className="text-gray-500 hover:text-gray-800 transition-colors">
          <User className="w-5 h-5" />
        </button>
        <button onClick={onCartClick} className="relative text-gray-500 hover:text-gray-800 transition-colors">
          <ShoppingCart className="w-5 h-5" />
          {cartItemCount > 0 && (
            <span className="absolute -top-2 -right-2 flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-blue-600 rounded-full">
              {cartItemCount}
            </span>
          )}
        </button>
      </div>
    </NavBar>
  );
};

const HeroSection = ({ product }) => {
  if (!product) return <div className="h-screen bg-gray-900 flex items-center justify-center"><SpinnerLoader size="lg" /></div>;

  return (
    <div className="relative h-screen w-full overflow-hidden bg-gray-900 text-white">
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-30"
        style={{ backgroundImage: `url(${product.imageUrl || 'https://images.unsplash.com/photo-1507564911639-635d235b8729?q=80&w=2940&auto=format&fit=crop'})` }}
      />
      <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-transparent to-gray-900/50" />
      <div className="relative z-10 flex flex-col items-center justify-center h-full text-center px-4">
        <div className="animate-fade-in-up" style={{ animationDelay: '200ms' }}>
          <SplitText text={product.name} className="text-5xl md:text-7xl lg:text-8xl font-extrabold tracking-tighter" />
        </div>
        <div className="animate-fade-in-up" style={{ animationDelay: '400ms' }}>
          <GradientText text={product.tagline} className="mt-4 text-xl md:text-2xl font-medium" />
        </div>
        <div className="mt-8 animate-fade-in-up" style={{ animationDelay: '600ms' }}>
          <Button size="lg" onClick={() => document.getElementById('products-section')?.scrollIntoView({ behavior: 'smooth' })}>
            Explore Products
          </Button>
        </div>
      </div>
    </div>
  );
};

const ProductCard = ({ product, onAddToCart, onViewDetails }) => (
  <Card className="group overflow-hidden transition-all duration-300 hover:shadow-2xl hover:-translate-y-2 bg-gray-800 border-gray-700 text-white">
    <div className="relative">
      <img src={product.imageUrl || 'https://images.unsplash.com/photo-1521478313203-d188ab1a9504?q=80&w=2000&auto=format&fit=crop'} alt={product.name} className="w-full h-64 object-cover transition-transform duration-500 group-hover:scale-110" />
      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent" />
    </div>
    <CardBody>
      <h3 className="text-xl font-bold">{product.name}</h3>
      <p className="text-gray-400 mt-1 text-sm">{product.tagline}</p>
      <div className="flex justify-between items-center mt-4">
        <p className="text-2xl font-semibold">
          ${new Intl.NumberFormat().format(product.price)}
        </p>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm" onClick={() => onViewDetails(product)} className="border-gray-500 text-gray-300 hover:bg-gray-700">Details</Button>
          <Button size="sm" onClick={() => onAddToCart(product)}>Add to Cart</Button>
        </div>
      </div>
    </CardBody>
  </Card>
);

const ProductDetailModal = ({ product, onClose, onAddToCart }) => {
  if (!product) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
      <Card className="relative w-full max-w-4xl max-h-[90vh] flex flex-col md:flex-row bg-gray-900 border-gray-700 text-white animate-slide-in-up">
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors z-10">
          <X className="w-6 h-6" />
        </button>
        <div className="md:w-1/2">
          <img src={product.imageUrl || 'https://images.unsplash.com/photo-1521478313203-d188ab1a9504?q=80&w=2000&auto=format&fit=crop'} alt={product.name} className="w-full h-64 md:h-full object-cover rounded-t-lg md:rounded-l-lg md:rounded-t-none" />
        </div>
        <div className="md:w-1/2 p-8 flex flex-col overflow-y-auto">
          <h2 className="text-3xl font-bold mb-2">{product.name}</h2>
          <GradientText text={product.tagline} className="text-lg font-medium mb-4" />
          <p className="text-gray-300 mb-6 flex-grow">{product.description}</p>
          
          <div className="mb-6">
            <h4 className="font-semibold text-lg mb-2 border-b border-gray-700 pb-2">Specifications</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              {product.specifications && Object.entries(product.specifications).map(([key, value]) => (
                <li key={key} className="flex justify-between">
                  <span>{key}:</span>
                  <span className="font-medium text-gray-200">{value}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-auto pt-6 border-t border-gray-700 flex items-center justify-between">
            <p className="text-3xl font-bold">${new Intl.NumberFormat().format(product.price)}</p>
            <Button size="lg" onClick={() => onAddToCart(product)}>Add to Cart</Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

const CartSidebar = ({ isOpen, onClose, cart, onUpdateCart, onRemoveFromCart }) => {
  const subtotal = Array.isArray(cart) ? cart.reduce((sum, item) => sum + item.price * item.quantity, 0) : 0;

  return (
    <>
      <div 
        className={`fixed inset-0 bg-black/60 z-50 transition-opacity duration-300 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={onClose}
      />
      <div className={`fixed top-0 right-0 h-full w-full max-w-md bg-gray-900 text-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <h2 className="text-2xl font-bold">Your Cart</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
              <X className="w-6 h-6" />
            </button>
          </div>
          
          {Array.isArray(cart) && cart.length > 0 ? (
            <div className="flex-grow overflow-y-auto p-6 space-y-4">
              {cart.map(item => (
                <div key={item.id} className="flex items-center space-x-4">
                  <img src={item.imageUrl} alt={item.name} className="w-20 h-20 object-cover rounded-md" />
                  <div className="flex-grow">
                    <h4 className="font-semibold">{item.name}</h4>
                    <p className="text-sm text-gray-400">${item.price.toFixed(2)}</p>
                  </div>
                  <div className="flex items-center space-x-2 border border-gray-600 rounded-md p-1">
                    <button onClick={() => onUpdateCart(item.id, item.quantity - 1)} className="text-gray-400 hover:text-white"><Minus size={16} /></button>
                    <span className="w-6 text-center">{item.quantity}</span>
                    <button onClick={() => onUpdateCart(item.id, item.quantity + 1)} className="text-gray-400 hover:text-white"><Plus size={16} /></button>
                  </div>
                  <button onClick={() => onRemoveFromCart(item.id)} className="text-red-500 hover:text-red-400"><X size={18} /></button>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex-grow flex items-center justify-center">
              <p className="text-gray-400">Your cart is empty.</p>
            </div>
          )}

          <div className="p-6 border-t border-gray-700 mt-auto">
            <div className="flex justify-between items-center mb-4">
              <span className="text-lg text-gray-300">Subtotal</span>
              <span className="text-2xl font-bold">${subtotal.toFixed(2)}</span>
            </div>
            <Button size="lg" className="w-full">Proceed to Checkout</Button>
          </div>
        </div>
      </div>
    </>
  );
};


// --- Main App Component ---

export default function App() {
  const [products, setProducts] = useState([]);
  const [featuredProduct, setFeaturedProduct] = useState(null);
  const [cart, setCart] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const dispatchCartUpdate = () => {
    window.dispatchEvent(new Event('cartUpdated'));
  };

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/products`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        // Handle both array and object responses
        let productsArray = [];
        if (Array.isArray(data)) {
          productsArray = data;
        } else if (data && Array.isArray(data.products)) {
          productsArray = data.products;
        } else if (data && Array.isArray(data.data)) {
          productsArray = data.data;
        } else {
          // If API returns unexpected format, fall back to mock data
          console.warn("API returned unexpected format, using fallback data");
          productsArray = [
            { id: 1, name: "Sample Product 1", price: 99.99, description: "A great product" },
            { id: 2, name: "Sample Product 2", price: 149.99, description: "Another great product" },
            { id: 3, name: "Sample Product 3", price: 199.99, description: "The best product" }
          ];
        }

        // Enhance products with missing fields
        const enhancedProducts = productsArray.map(product => ({
          ...product,
          tagline: product.tagline || `Premium ${product.name}`,
          imageUrl: product.imageUrl || `https://images.unsplash.com/photo-1521478313203-d188ab1a9504?q=80&w=2000&auto=format&fit=crop&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D`,
          category: product.category || 'Technology'
        }));

        setProducts(enhancedProducts);
        setFeaturedProduct(enhancedProducts[0] || null);
      } catch (err) {
        console.error("Failed to fetch products:", err);
        // Fallback to mock data on error
        const fallbackProducts = [
          {
            id: 1,
            name: "Premium Laptop",
            price: 1299.99,
            description: "High-performance laptop for professionals",
            tagline: "Power meets elegance",
            imageUrl: "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?q=80&w=2000&auto=format&fit=crop",
            category: "Technology"
          },
          {
            id: 2,
            name: "Wireless Headphones",
            price: 299.99,
            description: "Crystal clear audio with noise cancellation",
            tagline: "Immerse yourself in sound",
            imageUrl: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=2000&auto=format&fit=crop",
            category: "Audio"
          },
          {
            id: 3,
            name: "Smart Watch",
            price: 399.99,
            description: "Stay connected and track your health",
            tagline: "Your health, on your wrist",
            imageUrl: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?q=80&w=2000&auto=format&fit=crop",
            category: "Wearables"
          }
        ];
        setProducts(fallbackProducts);
        setFeaturedProduct(fallbackProducts[0]);
        setError("Using sample data. Backend may not be running.");
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  useEffect(() => {
    try {
      const savedCart = localStorage.getItem('app-1759395385592-cart');
      if (savedCart) {
        const parsedCart = JSON.parse(savedCart);
        if (Array.isArray(parsedCart)) {
          setCart(parsedCart);
        }
      }
    } catch (err) {
      console.error("Failed to load cart from localStorage:", err);
      setCart([]);
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem('app-1759395385592-cart', JSON.stringify(cart));
      dispatchCartUpdate();
    } catch (err) {
      console.error("Failed to save cart to localStorage:", err);
    }
  }, [cart]);

  const handleAddToCart = useCallback((productToAdd) => {
    setCart(prevCart => {
      const existingItem = prevCart.find(item => item.id === productToAdd.id);
      if (existingItem) {
        return prevCart.map(item =>
          item.id === productToAdd.id ? { ...item, quantity: item.quantity + 1 } : item
        );
      }
      return [...prevCart, { ...productToAdd, quantity: 1 }];
    });
    // Optionally close detail modal and open cart
    setSelectedProduct(null);
    setIsCartOpen(true);
  }, []);

  const handleUpdateCart = useCallback((productId, quantity) => {
    if (quantity < 1) {
      handleRemoveFromCart(productId);
      return;
    }
    setCart(prevCart =>
      prevCart.map(item =>
        item.id === productId ? { ...item, quantity } : item
      )
    );
  }, []);

  const handleRemoveFromCart = useCallback((productId) => {
    setCart(prevCart => prevCart.filter(item => item.id !== productId));
  }, []);

  return (
    <div className="bg-gray-900 min-h-screen font-sans">
      <GlobalHeader onCartClick={() => setIsCartOpen(true)} />
      
      <main>
        <HeroSection product={featuredProduct} />

        <section id="products-section" className="py-20 sm:py-24">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-4xl font-extrabold text-white sm:text-5xl">Our Collection</h2>
              <p className="mt-4 text-lg text-gray-400">Discover the future of technology, crafted with precision and passion.</p>
            </div>

            {loading && (
              <div className="flex justify-center">
                <SpinnerLoader size="lg" />
              </div>
            )}

            {error && (
              <div className="text-center text-red-400 bg-red-900/50 p-4 rounded-lg">
                <p>{error}</p>
              </div>
            )}

            {!loading && !error && Array.isArray(products) && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {products.map(product => (
                  <ProductCard 
                    key={product.id} 
                    product={product} 
                    onAddToCart={handleAddToCart}
                    onViewDetails={setSelectedProduct}
                  />
                ))}
              </div>
            )}
          </div>
        </section>
      </main>

      <ProductDetailModal 
        product={selectedProduct} 
        onClose={() => setSelectedProduct(null)}
        onAddToCart={handleAddToCart}
      />

      <CartSidebar 
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
        cart={cart}
        onUpdateCart={handleUpdateCart}
        onRemoveFromCart={handleRemoveFromCart}
      />
    </div>
  );
}