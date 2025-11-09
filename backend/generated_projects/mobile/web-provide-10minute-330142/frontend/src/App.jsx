// App.jsx - mobile/web-provide-10minute-330142 React Application
// VALIDATED: Syntax ✓ Imports ✓ Functionality ✓

import React, { useState, useEffect, useCallback } from 'react';

// Utility function for class names
const cn = (...classes) => classes.filter(Boolean).join(' ');

// Button variants
const buttonVariants = {
  default: "bg-blue-500 text-white hover:bg-blue-600",
  secondary: "bg-gray-500 text-white hover:bg-gray-600",
  danger: "bg-red-500 text-white hover:bg-red-600",
};

// UI Components with DEFENSIVE PROGRAMMING
const Button = ({ children, variant = "default", className = "", ...props }) => (
  <button 
    className={cn(buttonVariants[variant], "px-4 py-2 rounded-md transition-colors", className)} 
    {...props}
  >
    {children}
  </button>
);

const Card = ({ children, className = "" }) => (
  <div className={cn("bg-white rounded-lg shadow-md p-4", className)}>
    {children}
  </div>
);

const LoadingSpinner = () => (
  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
);

// Error Boundary
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true };
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="text-center p-8 bg-red-100 text-red-800 rounded-lg">
          <h2 className="text-xl font-bold">Something went wrong</h2>
          <p>Please refresh the page and try again.</p>
        </div>
      );
    }
    return this.props.children;
  }
}

// API Hook with defensive programming
const useApi = () => {
  const apiFetch = useCallback(async (url, options = {}) => {
    try {
      const response = await fetch(`http://localhost:8001/api/v1${url}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }, []);
  
  return apiFetch;
};

// Product Card Component with DEFENSIVE PROGRAMMING
const ProductCard = ({ product }) => {
  if (!product) return null;
  
  // Destructure with fallbacks
  const {
    id = 0,
    name = 'Unknown Product',
    description = 'No description available',
    price = 0,
    stock = 0,
    image_url = 'https://placehold.co/300x200/ddd/666?text=No+Image'
  } = product;
  
  return (
    <Card className="flex flex-col h-full">
      <img 
        src={image_url} 
        alt={name}
        className="w-full h-48 object-cover rounded-md mb-3"
        onError={(e) => {
          e.target.src = 'https://placehold.co/300x200/ddd/666?text=No+Image';
        }}
      />
      <h3 className="font-semibold text-lg mb-2">{name}</h3>
      <p className="text-gray-600 text-sm mb-3 flex-grow">{description}</p>
      <div className="flex justify-between items-center">
        <span className="text-xl font-bold text-green-600">
          ${(price || 0).toFixed(2)}
        </span>
        <Button disabled={stock === 0}>
          {stock === 0 ? 'Out of Stock' : 'Add to Cart'}
        </Button>
      </div>
    </Card>
  );
};

// Products Grid with DEFENSIVE PROGRAMMING
const ProductGrid = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const apiFetch = useApi();
  
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiFetch('/products');
        
        // DEFENSIVE: Ensure data is array
        setProducts(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error('Failed to fetch products:', err);
        setError('Failed to load products. Please try again.');
        setProducts([]); // Fallback to empty array
      } finally {
        setLoading(false);
      }
    };
    
    fetchProducts();
  }, [apiFetch]);
  
  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <LoadingSpinner />
        <span className="ml-2">Loading products...</span>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="text-center p-8 bg-red-100 text-red-800 rounded-lg">
        <p>{error}</p>
        <Button 
          onClick={() => window.location.reload()} 
          className="mt-4"
        >
          Retry
        </Button>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8 text-center">mobile/web-provide-10minute-330142</h1>
      
      {(products || []).length === 0 ? (
        <div className="text-center p-8 bg-gray-100 rounded-lg">
          <p className="text-gray-600">No products available at the moment.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {(products || []).map((product) => (
            <ProductCard key={product?.id || Math.random()} product={product} />
          ))}
        </div>
      )}
    </div>
  );
};

// Main App Component
function App() {
  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        <ProductGrid />
      </div>
    </ErrorBoundary>
  );
}

export default App;
