import React, { useState } from 'react';
import FeedbackButton from './components/FeedbackButton';
import CustomerReviews from './components/CustomerReviews';
import WishList from './components/WishList';

function App() {
  const [activeTab, setActiveTab] = useState('home');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Navigation Header */}
      <nav className="bg-white shadow-lg">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-800">Online Store</h1>
            <div className="flex space-x-6">
              <button
                onClick={() => setActiveTab('home')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'home' ? 'bg-blue-500 text-white' : 'text-gray-600 hover:text-blue-500'
                }`}
              >
                Home
              </button>
              <button
                onClick={() => setActiveTab('wishlist')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'wishlist' ? 'bg-blue-500 text-white' : 'text-gray-600 hover:text-blue-500'
                }`}
              >
                Wishlist
              </button>
              <button
                onClick={() => setActiveTab('reviews')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'reviews' ? 'bg-blue-500 text-white' : 'text-gray-600 hover:text-blue-500'
                }`}
              >
                Reviews
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {activeTab === 'home' && (
          <div className="text-center">
            <h2 className="text-4xl font-bold mb-6 text-gray-800">Welcome to Our Online Store</h2>
            <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
              Discover amazing products, save your favorites to your wishlist, and read what our customers have to say.
            </p>
            <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-8">
              <div className="bg-white p-6 rounded-lg shadow-md">
                <h3 className="text-xl font-semibold mb-3 text-gray-800">Quality Products</h3>
                <p className="text-gray-600">Carefully curated selection of high-quality items.</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-md">
                <h3 className="text-xl font-semibold mb-3 text-gray-800">Fast Shipping</h3>
                <p className="text-gray-600">Quick and reliable delivery to your doorstep.</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-md">
                <h3 className="text-xl font-semibold mb-3 text-gray-800">Customer Support</h3>
                <p className="text-gray-600">Dedicated support team ready to help you.</p>
              </div>
            </div>
            <FeedbackButton />
          </div>
        )}
        
        {activeTab === 'wishlist' && <WishList />}
        {activeTab === 'reviews' && <CustomerReviews />}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-8 mt-16">
        <div className="container mx-auto px-4 text-center">
          <p>&copy; 2025 Online Store. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;