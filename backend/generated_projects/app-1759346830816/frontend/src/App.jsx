import React, { useState, useEffect, useCallback } from 'react';

const API_URL = 'http://localhost:8000/api/v1';

export default function App() {
  // State for navigation, data, and authentication
  const [view, setView] = useState('catalog'); // 'catalog', 'product', 'login', 'signup'
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  
  // State for catalog controls and forms
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [authFormData, setAuthFormData] = useState({ email: '', password: '', username: '' });
  const [error, setError] = useState('');

  // Fetch all products based on search and filter
  const fetchProducts = useCallback(async () => {
    try {
      const query = new URLSearchParams({ search: searchTerm, category: filterCategory }).toString();
      const response = await fetch(`${API_URL}/products?${query}`);
      if (!response.ok) throw new Error('Failed to fetch products');
      const data = await response.json();
      setProducts(Array.isArray(data) ? data : []);
      setError('');
    } catch (err) {
      setError(err.message);
      setProducts([]); // Ensure products is always an array
    }
  }, [searchTerm, filterCategory]);

  // Fetch a single product by its ID
  const fetchProductById = async (id) => {
    try {
      const response = await fetch(`${API_URL}/products/${id}`);
      if (!response.ok) throw new Error('Failed to fetch product details');
      const data = await response.json();
      setSelectedProduct(data);
      setView('product');
      setError('');
    } catch (err) {
      setError(err.message);
    }
  };

  // Effect to check for existing user session on app load
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (token && storedUser && storedUser !== 'undefined') {
      try {
        setUser(JSON.parse(storedUser));
      } catch (err) {
        console.error('Error parsing stored user data:', err);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
        setToken(null);
      }
    }
  }, [token]);

  // Effect to fetch products when the catalog view is active or filters change
  useEffect(() => {
    if (view === 'catalog') {
      fetchProducts();
    }
  }, [view, fetchProducts]);

  // --- Handlers ---

  const handleAuthFormChange = (e) => {
    setAuthFormData({ ...authFormData, [e.target.name]: e.target.value });
  };

  const handleAuthSubmit = async (e, endpoint) => {
    e.preventDefault();
    setError('');
    try {
      const response = await fetch(`${API_URL}/auth/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(authFormData),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || 'Authentication failed');
      
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      setToken(data.token);
      setUser(data.user);
      setView('catalog');
      setAuthFormData({ email: '', password: '', username: '' });
    } catch (err) {
      setError(err.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
    setView('catalog');
  };

  // --- Render Functions for different views ---

  const Header = () => (
    <header className="bg-white shadow-md p-4">
      <nav className="container mx-auto flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800 cursor-pointer" onClick={() => setView('catalog')}>
          SimpleShop
        </h1>
        <div>
          {user ? (
            <div className="flex items-center gap-4">
              <span className="text-gray-700">Hi, {user.username}!</span>
              <button onClick={handleLogout} className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
                Logout
              </button>
            </div>
          ) : (
            <div className="flex gap-2">
              <button onClick={() => setView('login')} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                Login
              </button>
              <button onClick={() => setView('signup')} className="bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300">
                Sign Up
              </button>
            </div>
          )}
        </div>
      </nav>
    </header>
  );

  const AuthForm = ({ isSignUp }) => (
    <div className="max-w-md mx-auto mt-10 p-8 border rounded-lg shadow-lg bg-white">
      <h2 className="text-2xl font-bold mb-6 text-center">{isSignUp ? 'Create Account' : 'Login'}</h2>
      <form onSubmit={(e) => handleAuthSubmit(e, isSignUp ? 'register' : 'login')}>
        {isSignUp && (
          <div className="mb-4">
            <label className="block text-gray-700 mb-2" htmlFor="username">Username</label>
            <input type="text" name="username" value={authFormData.username} onChange={handleAuthFormChange} className="w-full px-3 py-2 border rounded-lg" required />
          </div>
        )}
        <div className="mb-4">
          <label className="block text-gray-700 mb-2" htmlFor="email">Email</label>
          <input type="email" name="email" value={authFormData.email} onChange={handleAuthFormChange} className="w-full px-3 py-2 border rounded-lg" required />
        </div>
        <div className="mb-6">
          <label className="block text-gray-700 mb-2" htmlFor="password">Password</label>
          <input type="password" name="password" value={authFormData.password} onChange={handleAuthFormChange} className="w-full px-3 py-2 border rounded-lg" required />
        </div>
        <button type="submit" className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600">
          {isSignUp ? 'Sign Up' : 'Login'}
        </button>
        <p className="text-center mt-4">
          <span onClick={() => setView(isSignUp ? 'login' : 'signup')} className="text-blue-500 hover:underline cursor-pointer">
            {isSignUp ? 'Already have an account? Login' : "Don't have an account? Sign Up"}
          </span>
        </p>
      </form>
    </div>
  );

  const ProductCatalog = () => (
    <div>
      <div className="my-6 flex flex-col sm:flex-row gap-4">
        <input
          type="text"
          placeholder="Search products..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-grow px-4 py-2 border rounded-lg"
        />
        <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)} className="px-4 py-2 border rounded-lg bg-white">
          <option value="">All Categories</option>
          <option value="electronics">Electronics</option>
          <option value="books">Books</option>
          <option value="clothing">Clothing</option>
        </select>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {products.map(product => (
          <div key={product.id} onClick={() => fetchProductById(product.id)} className="border rounded-lg overflow-hidden shadow-lg hover:shadow-xl transition-shadow cursor-pointer bg-white">
            <img src={product.imageUrl || 'https://via.placeholder.com/300'} alt={product.name} className="w-full h-48 object-cover" />
            <div className="p-4">
              <h3 className="text-lg font-semibold text-gray-800">{product.name}</h3>
              <p className="text-gray-600 mt-2">${product.price}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const ProductDetail = () => (
    <div className="mt-6">
      <button onClick={() => setView('catalog')} className="mb-6 bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300">
        &larr; Back to Catalog
      </button>
      {selectedProduct && (
        <div className="flex flex-col md:flex-row gap-8 bg-white p-8 rounded-lg shadow-lg">
          <img src={selectedProduct.imageUrl || 'https://via.placeholder.com/400'} alt={selectedProduct.name} className="w-full md:w-1/2 rounded-lg object-cover" />
          <div>
            <h2 className="text-3xl font-bold text-gray-900">{selectedProduct.name}</h2>
            <p className="text-2xl text-blue-600 font-semibold my-4">${selectedProduct.price}</p>
            <p className="text-gray-700 leading-relaxed">{selectedProduct.description}</p>
            <button className="mt-6 bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 font-semibold">
              Add to Cart
            </button>
          </div>
        </div>
      )}
    </div>
  );

  // --- Main Component Render ---
  
  return (
    <div className="bg-gray-50 min-h-screen font-sans">
      <Header />
      <main className="container mx-auto p-4">
        {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4" role="alert">{error}</div>}
        
        {view === 'login' && <AuthForm isSignUp={false} />}
        {view === 'signup' && <AuthForm isSignUp={true} />}
        {view === 'catalog' && <ProductCatalog />}
        {view === 'product' && <ProductDetail />}
      </main>
    </div>
  );
}