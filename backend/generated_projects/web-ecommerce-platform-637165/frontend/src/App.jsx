import React, { useState, useEffect } from 'react'; // Removed 'Component' from named import

// UTILITY: Class Name Merger (emulates clsx/tailwind-merge)
const cn = (...classes) => classes.filter(Boolean).join(' ');

// SHADCN/UI STYLE DEFINITIONS
const buttonVariants = {
  default: "bg-green-600 text-white hover:bg-green-700",
  destructive: "bg-red-500 text-white hover:bg-red-600",
  outline: "border border-gray-200 bg-transparent hover:bg-gray-100 hover:text-gray-900",
  secondary: "bg-gray-100 text-gray-900 hover:bg-gray-200",
  ghost: "hover:bg-gray-100 hover:text-gray-900",
  link: "text-green-600 underline-offset-4 hover:underline",
};

const cardVariants = {
  default: "bg-white rounded-xl border border-gray-200 shadow-sm",
  interactive: "bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300 cursor-pointer",
};

// ERROR BOUNDARY COMPONENT
class ErrorBoundary extends React.Component { // Changed to React.Component
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-red-50 text-red-800">
          <h1 className="text-4xl font-bold mb-4">Oops! Something went wrong.</h1>
          <p>We're sorry for the inconvenience. Please try refreshing the page.</p>
        </div>
      );
    }
    return this.props.children;
  }
}

// ICON COMPONENTS
const ShoppingCart = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle>
    <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
  </svg>
);
const Search = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>
  </svg>
);
const Truck = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="1" y="3" width="15" height="13"></rect><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon>
    <circle cx="5.5" cy="18.5" r="2.5"></circle><circle cx="18.5" cy="18.5" r="2.5"></circle>
  </svg>
);
const Calendar = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line>
    <line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line>
  </svg>
);
const RefreshCw = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline>
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
  </svg>
);
const Zap = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
  </svg>
);
const Star = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
  </svg>
);
const Users = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
    <circle cx="9" cy="7" r="4"></circle>
    <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
  </svg>
);
const ChevronRight = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polyline points="9 18 15 12 9 6"></polyline>
  </svg>
);

const X = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M18 6 6 18"></path>
    <path d="M6 6l12 12"></path>
  </svg>
);

// REUSABLE UI COMPONENTS
const Button = ({ children, variant = "default", className = "", ...props }) => (
  <button
    className={cn(
      "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-400 disabled:opacity-50 disabled:pointer-events-none",
      buttonVariants[variant],
      className
    )}
    {...props}
  >
    {children}
  </button>
);

const Card = ({ children, className = "", variant = "default" }) => (
  <div className={cn(cardVariants[variant], className)}>
    {children}
  </div>
);

// APP-SPECIFIC COMPONENTS
const Header = ({ user, cart, onLoginClick, onSignupClick, onCartClick, onLogout }) => (
  <header className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white/80 backdrop-blur-md">
    <div className="container mx-auto flex h-16 items-center justify-between px-4 md:px-6">
      <a href="#" className="flex items-center gap-2">
        <ShoppingCart className="h-6 w-6 text-green-600" />
        <span className="font-bold text-xl text-gray-800">FreshCart</span>
      </a>
      <nav className="hidden md:flex gap-6 text-sm font-medium text-gray-600">
        <a href="#features" className="hover:text-green-600 transition-colors">Features</a>
        <a href="#aisles" className="hover:text-green-600 transition-colors">Shop Aisles</a>
        <a href="#delivery" className="hover:text-green-600 transition-colors">Delivery</a>
        <a href="#" className="hover:text-green-600 transition-colors">My Orders</a>
      </nav>
      <div className="flex items-center gap-4">
        {user ? (
          <>
            <button
              onClick={onCartClick}
              className="relative p-2 text-gray-600 hover:text-green-600 transition-colors"
            >
              <ShoppingCart className="h-5 w-5" />
              {cart.item_count > 0 && (
                <span className="absolute -top-1 -right-1 bg-green-600 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                  {cart.item_count}
                </span>
              )}
            </button>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Hello, {user.full_name || user.email}</span>
              <Button variant="ghost" onClick={onLogout}>Log Out</Button>
            </div>
          </>
        ) : (
          <>
            <Button variant="ghost" onClick={onLoginClick}>Log In</Button>
            <Button onClick={onSignupClick}>Sign Up</Button>
          </>
        )}
      </div>
    </div>
  </header>
);

const Hero = () => (
  <section className="relative w-full py-20 md:py-32 lg:py-40 bg-gradient-to-br from-green-50 to-emerald-100">
    <div className="container mx-auto px-4 md:px-6 text-center">
      <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight text-gray-900">
        Groceries, Delivered Fresh to Your Doorstep.
      </h1>
      <p className="mt-6 max-w-2xl mx-auto text-lg md:text-xl text-gray-600">
        Skip the lines and get your favorite groceries delivered on your schedule. Fresh produce, pantry staples, and more, all just a click away.
      </p>
      <div className="mt-8 flex justify-center gap-4">
        <Button className="px-8 py-3 text-lg">
          Start Shopping Now
        </Button>
        <Button variant="outline" className="px-8 py-3 text-lg bg-white">
          Learn More
        </Button>
      </div>
    </div>
  </section>
);

const Features = () => {
  const features = [
    {
      icon: <Zap className="h-8 w-8 text-green-600" />,
      title: "Real-time Inventory Updates",
      description: "See 'Low Stock' or 'Out of Stock' badges live as you shop. No more checkout surprises.",
    },
    {
      icon: <ShoppingCart className="h-8 w-8 text-green-600" />,
      title: "Aisle-Based Navigation",
      description: "Browse intuitively through categories like 'Produce' and 'Dairy', just like in a real store.",
    },
    {
      icon: <Search className="h-8 w-8 text-green-600" />,
      title: "Smart Search & Filtering",
      description: "Find exactly what you need with instant suggestions and filters for diet, brand, and price.",
    },
    {
      icon: <RefreshCw className="h-8 w-8 text-green-600" />,
      title: "One-Click Re-order",
      description: "Instantly add all items from a past purchase to your cart for quick weekly shopping.",
    },
    {
      icon: <Calendar className="h-8 w-8 text-green-600" />,
      title: "Scheduled Delivery Slots",
      description: "Pick a delivery window that fits your life. No more waiting around for your order.",
    },
    {
      icon: <Truck className="h-8 w-8 text-green-600" />,
      title: "Live Order Status Tracking",
      description: "Follow your order from our store to your door with real-time updates from packing to delivery.",
    },
  ];

  return (
    <section id="features" className="py-16 md:py-24 bg-white">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900">A Better Way to Grocery Shop</h2>
          <p className="mt-4 max-w-2xl mx-auto text-lg text-gray-600">
            We've built a platform with features designed to make your life easier.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <Card key={index} className="p-6 flex flex-col items-start text-left">
              <div className="bg-green-100 p-3 rounded-full mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">{feature.title}</h3>
              <p className="text-gray-600">{feature.description}</p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

const AisleNavigation = ({ products, onAddToCart }) => {
  const [selectedCategory, setSelectedCategory] = useState('all');
  
  const categories = [
    { id: 'all', name: "All Products", icon: "🛒" },
    { id: 'electronics', name: "Electronics", icon: "📱" },
    { id: 'apparel', name: "Apparel", icon: "👕" },
    { id: 'footwear', name: "Footwear", icon: "👟" },
    { id: 'home_goods', name: "Home Goods", icon: "🏠" },
  ];

  const filteredProducts = selectedCategory === 'all' 
    ? products 
    : products.filter(p => p.category === selectedCategory);

  return (
    <section id="aisles" className="py-16 md:py-24 bg-gray-50">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900">Shop by Category</h2>
          <p className="mt-4 max-w-2xl mx-auto text-lg text-gray-600">
            Browse our curated selection of products across different categories.
          </p>
        </div>
        
        {/* Category Filters */}
        <div className="flex flex-wrap justify-center gap-4 mb-12">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category.id)}
              className={`px-6 py-3 rounded-full flex items-center gap-2 transition-colors ${
                selectedCategory === category.id
                  ? 'bg-green-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-100'
              }`}
            >
              <span>{category.icon}</span>
              <span className="font-medium">{category.name}</span>
            </button>
          ))}
        </div>
        
        {/* Products Grid */}
        {filteredProducts.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredProducts.map((product) => (
              <Card key={product.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                <div className="p-4">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs text-gray-500 uppercase tracking-wide">{product.category}</span>
                  </div>
                  <h3 className="font-semibold text-gray-800 mb-2">{product.name}</h3>
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">{product.description}</p>
                  <div className="flex justify-between items-center">
                    <p className="text-xl font-bold text-green-600">${product.price.toFixed(2)}</p>
                    <Button 
                      onClick={() => onAddToCart(product.id)}
                      className="bg-green-600 hover:bg-green-700 text-white px-4 py-2"
                    >
                      Add to Cart
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-500">No products available in this category.</p>
          </div>
        )}
      </div>
    </section>
  );
};

const SearchDemo = () => {
  const products = [
    { name: "Organic Sourdough Bread", brand: "Artisan Bakers", price: "5.99", image: "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=400&fit=max", tag: "Organic" },
    { name: "Gluten-Free Whole Wheat", brand: "Healthy Harvest", price: "6.49", image: "https://images.unsplash.com/photo-1598373182133-52452f7691ef?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=400&fit=max", tag: "Gluten-Free" },
    { name: "Classic White Bread", brand: "Wonder Bread", price: "3.29", image: "https://images.unsplash.com/photo-1534620808146-d33874f62d35?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=400&fit=max", stock: "Low Stock" },
  ];

  return (
    <section className="py-16 md:py-24 bg-white">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900">Find Exactly What You Need</h2>
          <p className="mt-4 max-w-2xl mx-auto text-lg text-gray-600">
            Our smart search helps you find items instantly. Try typing "bread" and see what happens.
          </p>
        </div>
        <div className="max-w-3xl mx-auto">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search for 'organic avocados'..."
              defaultValue="bread"
              className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-full text-lg focus:ring-2 focus:ring-green-400 focus:border-green-400"
            />
          </div>
          <div className="flex flex-wrap justify-center gap-2 mt-4">
            <Button variant="secondary" className="rounded-full">Brand: All</Button>
            <Button variant="secondary" className="rounded-full bg-green-100 text-green-800">Dietary: Gluten-Free</Button>
            <Button variant="secondary" className="rounded-full">Price: Any</Button>
            <Button variant="secondary" className="rounded-full">On Sale</Button>
          </div>
        </div>
        <div className="mt-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {products.map((product) => (
            <Card key={product.name} className="overflow-hidden">
              <div className="relative">
                <img src={product.image} alt={product.name} className="w-full h-48 object-cover" />
                {product.stock && (
                  <span className="absolute top-2 right-2 bg-yellow-400 text-yellow-900 text-xs font-bold px-2 py-1 rounded-full">{product.stock}</span>
                )}
                {product.tag && (
                  <span className="absolute top-2 left-2 bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded-full">{product.tag}</span>
                )}
              </div>
              <div className="p-4">
                <p className="text-sm text-gray-500">{product.brand}</p>
                <h3 className="font-semibold text-gray-800 mt-1">{product.name}</h3>
                <div className="flex justify-between items-center mt-4">
                  <p className="text-lg font-bold text-gray-900">${product.price}</p>
                  <Button>Add to Cart</Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

const DeliveryScheduler = () => {
  const [selectedDay, setSelectedDay] = useState('Wed');
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
  const slots = ['9am - 11am', '1pm - 3pm', '5pm - 7pm', '7pm - 9pm'];

  return (
    <section id="delivery" className="py-16 md:py-24 bg-gray-50">
      <div className="container mx-auto px-4 md:px-6">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900">Delivery That Works for You</h2>
            <p className="mt-4 text-lg text-gray-600">
              Never miss a delivery again. Choose a 2-hour window that fits your schedule during checkout. We'll handle the rest.
            </p>
            <ul className="mt-6 space-y-4">
              <li className="flex items-start">
                <ChevronRight className="h-6 w-6 text-green-500 mr-2 mt-1 flex-shrink-0" />
                <span>Select your preferred day and time at checkout.</span>
              </li>
              <li className="flex items-start">
                <ChevronRight className="h-6 w-6 text-green-500 mr-2 mt-1 flex-shrink-0" />
                <span>Get real-time notifications when your order is on its way.</span>
              </li>
              <li className="flex items-start">
                <ChevronRight className="h-6 w-6 text-green-500 mr-2 mt-1 flex-shrink-0" />
                <span>Contactless delivery options available for your safety.</span>
              </li>
            </ul>
          </div>
          <Card className="p-6">
            <h3 className="font-bold text-lg mb-4">Choose your delivery slot</h3>
            <div className="flex justify-between border-b pb-2 mb-4">
              {days.map(day => (
                <button
                  key={day}
                  onClick={() => setSelectedDay(day)}
                  className={cn(
                    "px-3 py-2 rounded-md text-sm font-medium",
                    selectedDay === day ? "bg-green-600 text-white" : "hover:bg-gray-100"
                  )}
                >
                  {day}
                </button>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-3">
              {slots.map(slot => (
                <button
                  key={slot}
                  className="w-full text-center p-3 border rounded-md hover:border-green-500 hover:bg-green-50 transition-colors focus:outline-none focus:ring-2 focus:ring-green-400"
                >
                  {slot}
                </button>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
};

const Testimonials = () => {
  const testimonials = [
    {
      name: "Sarah L.",
      quote: "FreshCart is a lifesaver! The one-click re-order for my weekly groceries saves me so much time. The produce is always incredibly fresh.",
      avatar: "https://i.pravatar.cc/150?u=a042581f4e29026704d"
    },
    {
      name: "Michael B.",
      quote: "The live inventory is a game-changer. I used to get so frustrated with other apps when items were out of stock at checkout. Not anymore!",
      avatar: "https://i.pravatar.cc/150?u=a042581f4e29026704e"
    },
    {
      name: "Jessica P.",
      quote: "I love being able to schedule my delivery for after I get home from work. The drivers are always on time and so friendly. Highly recommend!",
      avatar: "https://i.pravatar.cc/150?u=a042581f4e29026704f"
    }
  ];

  return (
    <section className="py-16 md:py-24 bg-white">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900">Loved by Shoppers Like You</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <Card key={index} className="p-6 flex flex-col">
              <div className="flex items-center mb-4">
                <img src={testimonial.avatar} alt={testimonial.name} className="w-12 h-12 rounded-full mr-4" />
                <div>
                  <p className="font-semibold text-gray-800">{testimonial.name}</p>
                  <div className="flex text-yellow-400">
                    <Star className="h-5 w-5" /><Star className="h-5 w-5" /><Star className="h-5 w-5" /><Star className="h-5 w-5" /><Star className="h-5 w-5" />
                  </div>
                </div>
              </div>
              <p className="text-gray-600">"{testimonial.quote}"</p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

const Footer = () => (
  <footer className="bg-gray-800 text-white">
    <div className="container mx-auto px-4 md:px-6 py-12">
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8">
        <div className="col-span-2 lg:col-span-1">
          <a href="#" className="flex items-center gap-2">
            <ShoppingCart className="h-6 w-6 text-green-400" />
            <span className="font-bold text-xl">FreshCart</span>
          </a>
          <p className="mt-4 text-gray-400 text-sm">Your daily groceries, delivered.</p>
        </div>
        <div>
          <h4 className="font-semibold mb-4">Company</h4>
          <ul className="space-y-2 text-sm text-gray-400">
            <li><a href="#" className="hover:text-white">About Us</a></li>
            <li><a href="#" className="hover:text-white">Careers</a></li>
            <li><a href="#" className="hover:text-white">Press</a></li>
          </ul>
        </div>
        <div>
          <h4 className="font-semibold mb-4">Help</h4>
          <ul className="space-y-2 text-sm text-gray-400">
            <li><a href="#" className="hover:text-white">Contact Us</a></li>
            <li><a href="#" className="hover:text-white">FAQ</a></li>
            <li><a href="#" className="hover:text-white">Shipping</a></li>
          </ul>
        </div>
        <div>
          <h4 className="font-semibold mb-4">Legal</h4>
          <ul className="space-y-2 text-sm text-gray-400">
            <li><a href="#" className="hover:text-white">Terms of Service</a></li>
            <li><a href="#" className="hover:text-white">Privacy Policy</a></li>
          </ul>
        </div>
      </div>
      <div className="mt-12 border-t border-gray-700 pt-8 text-center text-sm text-gray-400">
        <p>&copy; {new Date().getFullYear()} FreshCart, Inc. All rights reserved.</p>
      </div>
    </div>
  </footer>
);

// MAIN APP COMPONENT
const App = () => {
  // Authentication state
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  
  // Cart state
  const [cart, setCart] = useState({ items: [], total: 0, item_count: 0 });
  
  // Products state
  const [products, setProducts] = useState([]);
  
  // UI state
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [showCart, setShowCart] = useState(false);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  // API Base URL
  const API_BASE = 'http://localhost:8001/api/v1'; // Backend runs on port 8001

  // Helper function to show notifications
  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  // Authentication functions
  const login = async (email, password) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
      });
      
      if (response.ok) {
        const data = await response.json();
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        await loadUser();
        setShowLogin(false);
        showNotification('Login successful!');
      } else {
        showNotification('Invalid credentials', 'error');
      }
    } catch (error) {
      showNotification('Login failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const signup = async (email, password, fullName) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName })
      });
      
      if (response.ok) {
        showNotification('Account created! Please login.');
        setShowSignup(false);
        setShowLogin(true);
      } else {
        const error = await response.json();
        showNotification(error.detail || 'Signup failed', 'error');
      }
    } catch (error) {
      showNotification('Signup failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    setCart({ items: [], total: 0, item_count: 0 });
    localStorage.removeItem('token');
    showNotification('Logged out successfully');
  };

  const loadUser = async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_BASE}/users/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        await loadCart();
      } else {
        logout();
      }
    } catch (error) {
      console.error('Failed to load user:', error);
    }
  };

  // Cart functions
  const loadCart = async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_BASE}/cart`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const cartData = await response.json();
        setCart(cartData);
      }
    } catch (error) {
      console.error('Failed to load cart:', error);
    }
  };

  const addToCart = async (productId, quantity = 1) => {
    if (!token) {
      showNotification('Please login to add items to cart', 'error');
      setShowLogin(true);
      return;
    }
    
    try {
      const response = await fetch(`${API_BASE}/cart/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ product_id: productId, quantity })
      });
      
      if (response.ok) {
        const result = await response.json();
        showNotification(result.message);
        await loadCart();
      } else {
        showNotification('Failed to add to cart', 'error');
      }
    } catch (error) {
      showNotification('Failed to add to cart', 'error');
    }
  };

  // Load products
  const loadProducts = async () => {
    try {
      const response = await fetch(`${API_BASE}/products`);
      if (response.ok) {
        const productsData = await response.json();
        setProducts(productsData);
      }
    } catch (error) {
      console.error('Failed to load products:', error);
    }
  };

  // Load user and products on app start
  useEffect(() => {
    if (token) {
      loadUser();
    }
    loadProducts();
  }, [token]);

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-white text-gray-800 antialiased">
        {/* Notification */}
        {notification && (
          <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg ${
            notification.type === 'error' ? 'bg-red-500 text-white' : 'bg-green-500 text-white'
          }`}>
            {notification.message}
          </div>
        )}
        
        <Header 
          user={user}
          cart={cart}
          onLoginClick={() => setShowLogin(true)}
          onSignupClick={() => setShowSignup(true)}
          onCartClick={() => setShowCart(true)}
          onLogout={logout}
        />
        
        <main>
          <Hero />
          <Features />
          <AisleNavigation products={products} onAddToCart={addToCart} />
          <SearchDemo />
          <DeliveryScheduler />
          <Testimonials />
        </main>
        
        <Footer />
        
        {/* Login Modal */}
        {showLogin && (
          <LoginModal
            onClose={() => setShowLogin(false)}
            onLogin={login}
            onSwitchToSignup={() => {
              setShowLogin(false);
              setShowSignup(true);
            }}
            loading={loading}
          />
        )}
        
        {/* Signup Modal */}
        {showSignup && (
          <SignupModal
            onClose={() => setShowSignup(false)}
            onSignup={signup}
            onSwitchToLogin={() => {
              setShowSignup(false);
              setShowLogin(true);
            }}
            loading={loading}
          />
        )}
        
        {/* Cart Modal */}
        {showCart && (
          <CartModal
            cart={cart}
            onClose={() => setShowCart(false)}
            token={token}
            apiBase={API_BASE}
            onCartUpdate={loadCart}
            showNotification={showNotification}
          />
        )}
      </div>
    </ErrorBoundary>
  );
};

// Login Modal Component
const LoginModal = ({ onClose, onLogin, onSwitchToSignup, loading }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onLogin(email, password);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Login</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="user1@example.com"
            />
          </div>
          
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="password123"
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        
        <div className="mt-4 text-center">
          <p className="text-sm text-gray-600">
            Don't have an account?{' '}
            <button onClick={onSwitchToSignup} className="text-green-600 hover:underline">
              Sign up
            </button>
          </p>
          <p className="text-xs text-gray-500 mt-2">
            Demo: user1@example.com / password123
          </p>
        </div>
      </div>
    </div>
  );
};

// Signup Modal Component
const SignupModal = ({ onClose, onSignup, onSwitchToLogin, loading }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSignup(email, password, fullName);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Sign Up</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="John Doe"
            />
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="john@example.com"
            />
          </div>
          
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Enter password"
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? 'Creating Account...' : 'Sign Up'}
          </button>
        </form>
        
        <div className="mt-4 text-center">
          <p className="text-sm text-gray-600">
            Already have an account?{' '}
            <button onClick={onSwitchToLogin} className="text-green-600 hover:underline">
              Login
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

// Cart Modal Component
const CartModal = ({ cart, onClose, token, apiBase, onCartUpdate, showNotification }) => {
  const [loading, setLoading] = useState(false);

  const removeFromCart = async (productId) => {
    try {
      const response = await fetch(`${apiBase}/cart/item/${productId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        showNotification('Item removed from cart');
        onCartUpdate();
      }
    } catch (error) {
      showNotification('Failed to remove item', 'error');
    }
  };

  const processPayment = async () => {
    if (cart.total === 0) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${apiBase}/payment/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          cart_total: cart.total,
          payment_method: 'stripe',
          payment_details: {}
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        showNotification(`Payment successful! Order ID: ${result.order_id}`);
        onCartUpdate();
        onClose();
      } else {
        showNotification('Payment failed', 'error');
      }
    } catch (error) {
      showNotification('Payment failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[80vh] overflow-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Shopping Cart</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {cart.items.length === 0 ? (
          <div className="text-center py-8">
            <ShoppingCart className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">Your cart is empty</p>
          </div>
        ) : (
          <>
            <div className="space-y-4 mb-6">
              {cart.items.map((item) => (
                <div key={item.product.id} className="flex items-center justify-between border-b pb-4">
                  <div className="flex-1">
                    <h3 className="font-medium">{item.product.name}</h3>
                    <p className="text-sm text-gray-500">Quantity: {item.quantity}</p>
                    <p className="text-sm font-medium">${item.item_total.toFixed(2)}</p>
                  </div>
                  <button
                    onClick={() => removeFromCart(item.product.id)}
                    className="text-red-500 hover:text-red-700 ml-4"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
            
            <div className="border-t pt-4">
              <div className="flex justify-between items-center mb-4">
                <span className="text-lg font-bold">Total: ${cart.total.toFixed(2)}</span>
              </div>
              
              <button
                onClick={processPayment}
                disabled={loading}
                className="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Processing...' : 'Checkout'}
              </button>
              
              <p className="text-xs text-gray-500 mt-2 text-center">
                Demo payment - no real charges will be made
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default App;