import { useState } from 'react';
import { Star, Users, Zap, MapPin, Clock, Package, ShoppingCart, Heart, ArrowRight, CheckCircle, Twitter, Facebook, Instagram } from 'lucide-react';

// Helper Components (defined within the same file for simplicity)

const Button = ({ children, className = '', icon: Icon, ...props }) => {
  return (
    <button
      className={`inline-flex items-center justify-center px-6 py-3 font-semibold text-white bg-blue-600 rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-300 ${className}`}
      {...props}
    >
      {children}
      {Icon && <Icon className="w-5 h-5 ml-2" />}
    </button>
  );
};

const FeatureCard = ({ icon: Icon, title, description }) => (
  <div className="p-6 bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 flex flex-col items-center text-center">
    <div className="flex items-center justify-center w-16 h-16 mb-4 text-blue-600 bg-blue-100 rounded-full">
      <Icon className="w-8 h-8" />
    </div>
    <h3 className="mb-2 text-xl font-bold text-gray-800">{title}</h3>
    <p className="text-gray-600">{description}</p>
  </div>
);

const StatItem = ({ icon: Icon, value, label }) => (
  <div className="text-center">
    <Icon className="w-12 h-12 mx-auto mb-2 text-blue-500" />
    <p className="text-4xl font-extrabold text-gray-800">{value}</p>
    <p className="text-lg text-gray-600">{label}</p>
  </div>
);

const ProductCard = ({ name, price, imageTopic, stock }) => (
  <div className="overflow-hidden bg-white border border-gray-200 rounded-lg shadow-md group">
    <div className="relative">
      <img src={`https://images.unsplash.com/photo-1576186737225-475c5116de25?q=80&w=300&h=200&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D/300x200/?${imageTopic}`} alt={name} className="object-cover w-full h-48 transition-transform duration-300 group-hover:scale-105" />
      {stock > 0 && stock <= 5 && (
        <span className="absolute top-2 left-2 px-2 py-1 text-xs font-bold text-white bg-red-500 rounded-full">Only {stock} left!</span>
      )}
      {stock === 0 && (
        <span className="absolute top-2 left-2 px-2 py-1 text-xs font-bold text-white bg-gray-700 rounded-full">Out of Stock</span>
      )}
    </div>
    <div className="p-4">
      <h3 className="text-lg font-semibold text-gray-800 truncate">{name}</h3>
      <p className="mt-1 text-xl font-bold text-blue-600">${price.toFixed(2)}</p>
      <div className="mt-4">
        {stock > 0 ? (
          <Button className="w-full text-sm">
            <ShoppingCart className="w-4 h-4 mr-2" />
            Add to Cart
          </Button>
        ) : (
          <button className="w-full px-6 py-3 text-sm font-semibold text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors duration-300">
            Notify Me
          </button>
        )}
      </div>
    </div>
  </div>
);


// Main App Component
export default function App() {
  const [searchTerm, setSearchTerm] = useState('');

  const features = [
    {
      icon: Zap,
      title: 'Dynamic Search & Filtering',
      description: "Instantly find 'organic avocados' and filter by category, diet, or price to get exactly what you need, fast."
    },
    {
      icon: Clock,
      title: 'Scheduled Delivery Slots',
      description: "Pick a delivery window that fits your life. No more waiting around or missed groceries."
    },
    {
      icon: Package,
      title: 'Real-Time Inventory',
      description: "See live stock levels as you shop. Subscribe to 'Back in Stock' alerts for your favorite items."
    },
    {
      icon: Heart,
      title: 'Personalized Recommendations',
      description: "Discover new products you'll love based on your shopping habits and preferences."
    },
    {
      icon: MapPin,
      title: 'Locally Sourced Options',
      description: "Support local farms and artisans by easily finding fresh, seasonal produce from your community."
    },
    {
      icon: CheckCircle,
      title: 'Quality Guarantee',
      description: "We stand by our freshness. If you're not happy with an item, we'll make it right, guaranteed."
    }
  ];

  const products = [
    { id: 1, name: 'Organic Hass Avocados', price: 2.50, imageTopic: 'avocado', stock: 15, category: 'Produce' },
    { id: 2, name: 'Artisanal Sourdough Bread', price: 5.99, imageTopic: 'bread', stock: 3, category: 'Bakery' },
    { id: 3, name: 'Free-Range Organic Eggs', price: 6.20, imageTopic: 'eggs', stock: 25, category: 'Dairy' },
    { id: 4, name: 'Cold Brew Coffee Concentrate', price: 8.00, imageTopic: 'coffee', stock: 0, category: 'Beverages' },
    { id: 5, name: 'Fresh Atlantic Salmon Fillet', price: 12.49, imageTopic: 'salmon', stock: 8, category: 'Meat & Seafood' },
    { id: 6, name: 'Gala Apples (3lb Bag)', price: 4.50, imageTopic: 'apples', stock: 50, category: 'Produce' },
    { id: 7, name: 'Greek Yogurt, Plain', price: 3.75, imageTopic: 'yogurt', stock: 0, category: 'Dairy' },
    { id: 8, name: 'Gluten-Free Pasta', price: 4.99, imageTopic: 'pasta', stock: 12, category: 'Pantry' },
    { id: 9, name: 'Organic Baby Spinach', price: 3.29, imageTopic: 'spinach', stock: 5, category: 'Produce' },
    { id: 10, name: 'Kombucha, Ginger Flavor', price: 3.99, imageTopic: 'kombucha', stock: 22, category: 'Beverages' },
  ];

  const stats = [
    { icon: Users, value: '150k+', label: 'Happy Customers' },
    { icon: Star, value: '4.9/5', label: 'Average Rating' },
    { icon: Package, value: '2M+', label: 'Groceries Delivered' },
  ];

  return (
    <div className="bg-gray-50 text-gray-800">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg shadow-sm">
        <nav className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <ShoppingCart className="w-8 h-8 text-blue-600" />
            <span className="text-2xl font-bold text-gray-800">FreshCart</span>
          </div>
          <div className="hidden md:flex items-center space-x-6">
            <a href="#" className="text-gray-600 hover:text-blue-600">Shop</a>
            <a href="#" className="text-gray-600 hover:text-blue-600">Deals</a>
            <a href="#" className="text-gray-600 hover:text-blue-600">About</a>
          </div>
          <div className="flex items-center space-x-4">
            <a href="#" className="text-gray-600 hover:text-blue-600">Log In</a>
            <Button className="hidden sm:inline-flex">Sign Up</Button>
          </div>
        </nav>
      </header>

      <main>
        {/* Hero Section */}
        <section className="relative text-white py-20 md:py-32 bg-gradient-to-r from-blue-600 to-green-400">
          <div className="container mx-auto px-6 text-center">
            <h1 className="text-4xl md:text-6xl font-extrabold leading-tight mb-4">
              Your Groceries, Delivered Fresh.
            </h1>
            <p className="text-lg md:text-xl mb-8 max-w-3xl mx-auto text-blue-100">
              Shop from the best local stores and get your favorite items delivered to your door in as fast as an hour.
            </p>
            <div className="max-w-2xl mx-auto">
              <div className="relative">
                <input
                  type="search"
                  placeholder="Search for 'organic avocados'..."
                  className="w-full p-4 pr-32 text-gray-900 rounded-lg shadow-lg focus:outline-none focus:ring-4 focus:ring-blue-300"
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                <Button className="absolute top-1/2 right-2 transform -translate-y-1/2" icon={ArrowRight}>
                  Search
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-16 sm:py-24 bg-white">
          <div className="container mx-auto px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900">Everything You Need, and More</h2>
              <p className="mt-4 text-lg text-gray-600 max-w-2xl mx-auto">
                We've built a platform designed for convenience, quality, and speed.
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <FeatureCard key={index} icon={feature.icon} title={feature.title} description={feature.description} />
              ))}
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-16 sm:py-20 bg-blue-50">
          <div className="container mx-auto px-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
              {stats.map((stat, index) => (
                <StatItem key={index} icon={stat.icon} value={stat.value} label={stat.label} />
              ))}
            </div>
          </div>
        </section>

        {/* Main Content Area - Products */}
        <section className="py-16 sm:py-24">
          <div className="container mx-auto px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900">Fresh Picks For You</h2>
              <p className="mt-4 text-lg text-gray-600">Browse our curated selection of high-quality groceries.</p>
            </div>
            
            {/* Filter Controls */}
            <div className="flex flex-wrap justify-center gap-2 mb-8">
              <button className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-full shadow-sm">All</button>
              <button className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-full hover:bg-gray-300">Produce</button>
              <button className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-full hover:bg-gray-300">Dairy</button>
              <button className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-full hover:bg-gray-300">Bakery</button>
              <button className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-full hover:bg-gray-300">Pantry</button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              {products.map(product => (
                <ProductCard key={product.id} {...product} />
              ))}
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white">
        <div className="container mx-auto px-6 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8">
            <div className="col-span-2 lg:col-span-1">
              <div className="flex items-center space-x-2 mb-4">
                <ShoppingCart className="w-8 h-8 text-blue-400" />
                <span className="text-2xl font-bold">FreshCart</span>
              </div>
              <p className="text-gray-400">Your daily dose of fresh, delivered.</p>
            </div>
            <div>
              <h3 className="font-bold tracking-wider uppercase mb-4">Shop</h3>
              <ul className="space-y-2">
                <li><a href="#" className="text-gray-400 hover:text-white">All Products</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">Fresh Produce</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">Dairy & Eggs</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">Meat & Seafood</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold tracking-wider uppercase mb-4">About Us</h3>
              <ul className="space-y-2">
                <li><a href="#" className="text-gray-400 hover:text-white">Our Story</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">Careers</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">Press</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold tracking-wider uppercase mb-4">Support</h3>
              <ul className="space-y-2">
                <li><a href="#" className="text-gray-400 hover:text-white">Help Center</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">Contact Us</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">FAQs</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold tracking-wider uppercase mb-4">Legal</h3>
              <ul className="space-y-2">
                <li><a href="#" className="text-gray-400 hover:text-white">Terms of Service</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white">Privacy Policy</a></li>
              </ul>
            </div>
          </div>
          <div className="mt-12 pt-8 border-t border-gray-700 flex flex-col sm:flex-row justify-between items-center">
            <p className="text-gray-400 text-sm">&copy; {new Date().getFullYear()} FreshCart, Inc. All rights reserved.</p>
            <div className="flex space-x-4 mt-4 sm:mt-0">
              <a href="#" className="text-gray-400 hover:text-white"><Twitter className="w-6 h-6" /></a>
              <a href="#" className="text-gray-400 hover:text-white"><Facebook className="w-6 h-6" /></a>
              <a href="#" className="text-gray-400 hover:text-white"><Instagram className="w-6 h-6" /></a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}