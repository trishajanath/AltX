```javascript
import React, { useState, useEffect } from 'react';
import { Home, ShoppingCart, UtensilsCrossed, Package, ChevronsRight, Search, MapPin } from 'lucide-react';

// Mock Data
const mockCategories = [
  { id: 'fruits-veg', name: 'Fruits & Vegetables', icon: '🍎' },
  { id: 'dairy-bread', name: 'Dairy & Bread', icon: '🍞' },
  { id: 'snacks', name: 'Snacks & Munchies', icon: '🍿' },
  { id: 'meat-fish', name: 'Meat & Fish', icon: '🍗' },
  { id: 'beverages', name: 'Cold Drinks', icon: '🥤' },
  { id: 'cleaning', name: 'Cleaning Essentials', icon: '🧽' },
];

const mockProducts = {
  'fruits-veg': [
    { id: 1, name: 'Fresh Banana', price: 0.5, image: 'https://via.placeholder.com/150/FDE047/000000?text=Banana' },
    { id: 2, name: 'Organic Apples', price: 1.2, image: 'https://via.placeholder.com/150/F87171/000000?text=Apple' },
    { id: 3, name: 'Spinach Bunch', price: 2.0, image: 'https://via.placeholder.com/150/86EFAC/000000?text=Spinach' },
  ],
  'dairy-bread': [
    { id: 4, name: 'Whole Milk', price: 3.5, image: 'https://via.placeholder.com/150/E0F2FE/000000?text=Milk' },
    { id: 5, name: 'Brown Bread', price: 2.8, image: 'https://via.placeholder.com/150/D2B48C/000000?text=Bread' },
  ],
  // Add more mock products for other categories...
};

// Mock API functions
const fetchCategories = () => new Promise(resolve => setTimeout(() => resolve(mockCategories), 500));
const fetchProducts = (categoryId) => new Promise((resolve, reject) => {
  setTimeout(() => {
    if (mockProducts[categoryId]) {
      resolve(mockProducts[categoryId]);
    } else {
      resolve([]); // Return empty for categories with no items yet
    }
  }, 800);
});

// Components

const LoadingSpinner = () => (

);

const ErrorMessage = ({ message }) => (
  
    Oops! 
    {message}
  
);

const Header = ({ cartItemCount, onCartClick }) => (

        Quickly

        Deliver to New York, 10001

          Search

          {cartItemCount > 0 && (
            
              {cartItemCount}
            
          )}

);

const CategoryCard = ({ category, onSelectCategory }) => (
   onSelectCategory(category.id)} className="text-center p-4 bg-surface-200 rounded-lg cursor-pointer hover:bg-primary/10 transition-colors">
    {category.icon}
    {category.name}
  
);

const ProductCard = ({ product, onAddToCart }) => (

      {product.name}
      ${product.price.toFixed(2)}
       onAddToCart(product)} className="btn-primary w-full">
        Add to Cart

);

const HomePage = ({ onSelectCategory }) => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCategories()
      .then(data => setCategories(data))
      .catch(() => setError('Failed to load categories.'))
      .finally(() => setLoading(false));
  }, []);

  return (

        Groceries delivered in 10 mins
        Get your daily essentials faster than ever.
      
      Shop by Category
      {loading && }
      {error && }
      {!loading && !error && (
        
          {categories.map(cat => (
            
          ))}
        
      )}
    
  );
};

const ProductListPage = ({ categoryId, onAddToCart, onBack }) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const categoryName = mockCategories.find(c => c.id === categoryId)?.name || 'Products';

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchProducts(categoryId)
      .then(data => setProducts(data))
      .catch(() => setError('Failed to load products for this category.'))
      .finally(() => setLoading(false));
  }, [categoryId]);

  return (

        &larr; Back to Categories
      
      {categoryName}
      {loading && }
      {error && }
      {!loading && !error && products.length > 0 && (
        
          {products.map(prod => (
            
          ))}
        
      )}
      {!loading && !error && products.length === 0 && (

          No products found in this category yet.
        
      )}
    
  );
};

const CartView = ({ cart, onUpdateCart, onCloseCart }) => {
  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

  const handleQuantityChange = (product, quantity) => {
    onUpdateCart(product, quantity);
  };
  
  return (
    
       e.stopPropagation()}>
        
          Your Cart

        {cart.length === 0 ? (

            Your cart is empty
            Add items to get started!
          
        ) : (
          <>
            
              {cart.map(item => (

                    {item.name}
                    ${item.price.toFixed(2)}

                     handleQuantityChange(item, item.quantity - 1)} className="px-2 py-1">-
                    {item.quantity}
                     handleQuantityChange(item, item.quantity + 1)} className="px-2 py-1">+
                  
                  ${(item.price * item.quantity).toFixed(2)}
                
              ))}

                Subtotal
                ${total.toFixed(2)}

                Proceed to Checkout

        )}

  );
};

function App() {
  const [view, setView] = useState({ page: 'home', categoryId: null });
  const [cart, setCart] = useState([]);
  const [isCartOpen, setIsCartOpen] = useState(false);

  const handleSelectCategory = (categoryId) => {
    setView({ page: 'products', categoryId });
  };

  const handleBackToHome = () => {
    setView({ page: 'home', categoryId: null });
  };
  
  const handleAddToCart = (product) => {
    setCart(prevCart => {
      const existingItem = prevCart.find(item => item.id === product.id);
      if (existingItem) {
        return prevCart.map(item =>
          item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        );
      }
      return [...prevCart, { ...product, quantity: 1 }];
    });
  };

  const handleUpdateCart = (product, quantity) => {
    if (quantity  prevCart.filter(item => item.id !== product.id));
    } else {
      setCart(prevCart => prevCart.map(item =>
        item.id === product.id ? { ...item, quantity } : item
      ));
    }
  };

  const cartItemCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  return (
    
       setIsCartOpen(true)} />

        {view.page === 'home' && }
        {view.page === 'products' && (
          
        )}

      {isCartOpen &&  setIsCartOpen(false)} />}

          &copy; {new Date().getFullYear()} Quickly. All rights reserved.
          Your groceries, delivered in minutes.

  );
}

export default App;
```