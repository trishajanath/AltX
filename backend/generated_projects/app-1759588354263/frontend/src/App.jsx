import React, { useState } from 'react';

// Import icons safely with try/catch fallbacks
let Star, Users, Package, MapPin, Zap, Clock, ShoppingCart, Repeat, Twitter, Facebook, Instagram;
try {
  const icons = require('lucide-react');
  Star = icons.Star;
  Users = icons.Users;
  Package = icons.Package;
  MapPin = icons.MapPin;
  Zap = icons.Zap;
  Clock = icons.Clock;
  ShoppingCart = icons.ShoppingCart;
  Repeat = icons.Repeat;
  Twitter = icons.Twitter;
  Facebook = icons.Facebook;
  Instagram = icons.Instagram;
} catch (error) {
  // Fallback icons if lucide-react fails to load
  const FallbackIcon = ({ className }) => <span className={className}>⚡</span>;
  Star = FallbackIcon;
  Users = FallbackIcon;
  Package = FallbackIcon;
  MapPin = FallbackIcon;
  Zap = FallbackIcon;
  Clock = FallbackIcon;
  ShoppingCart = FallbackIcon;
  Repeat = FallbackIcon;
  Twitter = FallbackIcon;
  Facebook = FallbackIcon;
  Instagram = FallbackIcon;
}

// Inline Button component with blue styling, as requested.
const Button = ({ children, className = '', ...props }) => {
  return (
    <button
      className={`bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 ease-in-out transform hover:scale-105 shadow-lg hover:shadow-blue-500/50 ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

// The main component for app-1759588354263 (Quick Commerce Application)
export default function App() {
  // Using useState hook to manage a simple cart count
  const [cartCount, setCartCount] = useState(0);

  const handleAddToCart = () => {
    setCartCount(prevCount => prevCount + 1);
  };

  // Data for the features grid, based on the prompt
  const features = [
    {
      icon: <Package className="h-10 w-10 text-blue-400" />,
      name: 'Real-Time Inventory',
      description: "See live stock from your nearest dark store. No more out-of-stock surprises or cancellations.",
    },
    {
      icon: <MapPin className="h-10 w-10 text-blue-400" />,
      name: 'Live Rider Tracking',
      description: "Watch your delivery arrive in real-time on an interactive map with an accurate ETA.",
    },
    {
      icon: <Zap className="h-10 w-10 text-blue-400" />,
      name: 'Dynamic Flash Deals',
      description: "Grab time-sensitive discounts and curated bundles, like our 'Movie Night Pack'.",
    },
    {
      icon: <Clock className="h-10 w-10 text-blue-400" />,
      name: 'Delivery in Minutes',
      description: "Get your groceries, snacks, and essentials delivered to your door in as fast as 15 minutes.",
    },
    {
      icon: <ShoppingCart className="h-10 w-10 text-blue-400" />,
      name: 'Curated Selection',
      description: "We stock thousands of your favorite local and national brands for every occasion.",
    },
    {
      icon: <Repeat className="h-10 w-10 text-blue-400" />,
      name: 'Effortless Reordering',
      description: "Your past orders are saved, making it simple to restock your essentials with a single tap.",
    },
  ];

  // Data for the main content product grid
  const products = [
    { id: 1, name: "Ben & Jerry's Cookie Dough", price: 7.99, imageTopic: 'ice%20cream' },
    { id: 2, name: 'Organic Avocados (2-pack)', price: 4.50, imageTopic: 'avocado' },
    { id: 3, name: 'La Croix Sparkling Water', price: 5.25, imageTopic: 'soda%20can' },
    { id: 4, name: 'Fresh Bananas (Bunch)', price: 2.99, imageTopic: 'banana' },
    { id: 5, name: 'Kettle Cooked Potato Chips', price: 3.79, imageTopic: 'chips' },
    { id: 6, name: 'Artisan Sourdough Bread', price: 6.49, imageTopic: 'bread' },
    { id: 7, name: 'Free-Range Eggs (Dozen)', price: 5.99, imageTopic: 'eggs' },
    { id: 8, name: 'Cold Brew Coffee Concentrate', price: 8.99, imageTopic: 'coffee' },
  ];

  return (
    <div className="bg-slate-900 text-white font-sans">
      {/* Header */}
      <header className="container mx-auto px-6 py-4 flex justify-between items-center sticky top-0 z-50 bg-slate-900/80 backdrop-blur-sm border-b border-slate-800">
        <div className="text-2xl font-bold text-white">
          <Zap className="inline-block h-6 w-6 text-blue-400 mr-2" />
          Swiftly
        </div>
        <nav className="hidden md:flex items-center space-x-6">
          <a href="#features" className="hover:text-blue-400 transition-colors">Features</a>
          <a href="#products" className="hover:text-blue-400 transition-colors">Shop</a>
          <a href="#" className="hover:text-blue-400 transition-colors">Deals</a>
        </nav>
        <Button className="flex items-center gap-2 py-2 px-4 text-sm">
          <ShoppingCart className="h-5 w-5" />
          <span>Cart ({cartCount})</span>
        </Button>
      </header>

      <main>
        {/* Hero Section */}
        <section className="relative text-center py-20 md:py-32 px-6 bg-gradient-to-b from-slate-900 to-slate-800">
          <div className="absolute inset-0 bg-[url('/grid.svg')] bg-repeat [mask-image:linear-gradient(to_bottom,white_20%,transparent_100%)] opacity-10"></div>
          <div className="relative z-10 container mx-auto">
            <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight mb-4">
              Groceries & More, Delivered in <span className="text-blue-400">Minutes</span>.
            </h1>
            <p className="text-lg md:text-xl text-slate-300 max-w-3xl mx-auto mb-8">
              Your favorite local store, now online. Get fresh produce, snacks, and household essentials delivered faster than you can decide what to watch.
            </p>
            <div className="flex justify-center">
              <Button className="text-lg">
                Enter Your Address to Start
              </Button>
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section id="features" className="py-20 bg-slate-800">
          <div className="container mx-auto px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold">Why You'll Love Swiftly</h2>
              <p className="text-slate-400 mt-2">The quick commerce experience, perfected.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <div key={index} className="bg-slate-900 p-8 rounded-xl shadow-lg flex flex-col items-center text-center transform hover:-translate-y-2 transition-transform duration-300">
                  <div className="mb-4">{feature.icon}</div>
                  <h3 className="text-xl font-semibold mb-2">{feature.name}</h3>
                  <p className="text-slate-400 leading-relaxed">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-20 bg-slate-900">
          <div className="container mx-auto px-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
              <div className="p-4">
                <p className="text-5xl font-bold text-blue-400">15 min</p>
                <p className="text-slate-300 mt-2 text-lg">Average Delivery Time</p>
              </div>
              <div className="p-4">
                <p className="text-5xl font-bold text-blue-400 flex items-center justify-center">
                  4.9 <Star className="h-8 w-8 ml-2 text-yellow-400" fill="currentColor" />
                </p>
                <p className="text-slate-300 mt-2 text-lg">Customer Rating</p>
              </div>
              <div className="p-4">
                <p className="text-5xl font-bold text-blue-400 flex items-center justify-center">
                  1M+ <Users className="h-8 w-8 ml-2" />
                </p>
                <p className="text-slate-300 mt-2 text-lg">Happy Customers Served</p>
              </div>
            </div>
          </div>
        </section>

        {/* Main Content Area - Product Grid */}
        <section id="products" className="py-20 bg-slate-800">
          <div className="container mx-auto px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold">Popular Near You</h2>
              <p className="text-slate-400 mt-2">Based on your location in Downtown</p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {products.map((product) => (
                <div key={product.id} className="bg-slate-900 rounded-lg overflow-hidden shadow-lg group flex flex-col">
                  <div className="relative">
                    <img
                      src={`https://source.unsplash.com/300x200/?${product.imageTopic},${product.name}`}
                      alt={product.name}
                      className="w-full h-40 object-cover group-hover:opacity-80 transition-opacity"
                    />
                  </div>
                  <div className="p-4 flex flex-col flex-grow">
                    <h3 className="font-semibold truncate flex-grow">{product.name}</h3>
                    <p className="text-slate-400 text-lg font-bold mt-1">${product.price.toFixed(2)}</p>
                    <button 
                      onClick={handleAddToCart}
                      className="w-full mt-4 bg-blue-600/20 text-blue-300 hover:bg-blue-600 hover:text-white font-semibold py-2 px-4 rounded-lg transition-all duration-300"
                    >
                      Add to Cart
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800">
        <div className="container mx-auto px-6 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div>
              <h4 className="font-semibold mb-4">Swiftly</h4>
              <ul>
                <li className="mt-2"><a href="#" className="text-slate-400 hover:text-white">About Us</a></li>
                <li className="mt-2"><a href="#" className="text-slate-400 hover:text-white">Careers</a></li>
                <li className="mt-2"><a href="#" className="text-slate-400 hover:text-white">Press</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Partnerships</h4>
              <ul>
                <li className="mt-2"><a href="#" className="text-slate-400 hover:text-white">Become a Rider</a></li>
                <li className="mt-2"><a href="#" className="text-slate-400 hover:text-white">List Your Store</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Support</h4>
              <ul>
                <li className="mt-2"><a href="#" className="text-slate-400 hover:text-white">Help Center</a></li>
                <li className="mt-2"><a href="#" className="text-slate-400 hover:text-white">Contact Us</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul>
                <li className="mt-2"><a href="#" className="text-slate-400 hover:text-white">Terms of Service</a></li>
                <li className="mt-2"><a href="#" className="text-slate-400 hover:text-white">Privacy Policy</a></li>
              </ul>
            </div>
          </div>
          <div className="mt-12 pt-8 border-t border-slate-800 flex flex-col md:flex-row justify-between items-center">
            <p className="text-slate-500">&copy; {new Date().getFullYear()} Swiftly Inc. All rights reserved.</p>
            <div className="flex space-x-4 mt-4 md:mt-0">
              <a href="#" className="text-slate-400 hover:text-white"><Twitter /></a>
              <a href="#" className="text-slate-400 hover:text-white"><Facebook /></a>
              <a href="#" className="text-slate-400 hover:text-white"><Instagram /></a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}