import React, { useState, useEffect } from 'react';

// Helper for combining Tailwind CSS classes
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// --- ICONS (as React Components) ---

const AppleLogo = ({ className }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 20.94c1.5 0 2.75 1.06 4 1.06 3 0 6-8 6-12.22A4.91 4.91 0 0 0 17 5c-2.22 0-4 1.44-5 2-1-.56-2.78-2-5-2a4.9 4.9 0 0 0-5 4.78C2 14 5 22 8 22c1.25 0 2.5-1.06 4-1.06Z"></path>
    <path d="M10 2c1 .5 2 2 2 5"></path>
  </svg>
);

const AndroidLogo = ({ className }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M16 8.81a4 4 0 0 1-8 0"></path>
        <path d="M12 15.5a4 4 0 0 1-4-4h8a4 4 0 0 1-4 4Z"></path>
        <path d="M8 6.38V4.5a2.5 2.5 0 0 1 5 0V6.4"></path>
        <path d="M18.83 7.83a10 10 0 0 1-13.66 0"></path>
        <path d="M5.17 16.17a10 10 0 0 1 13.66 0"></path>
        <path d="M12 18v2"></path>
        <path d="M4.2 19.8 2 22"></path>
        <path d="M22 22l-2.2-2.2"></path>
    </svg>
);

const Star = ({ className = "w-5 h-5" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
  </svg>
);

const PackageCheck = ({ className }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m16 16 2 2 4-4"/><path d="M21 10V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l2-1.14"/><path d="M16.5 9.4 7.55 4.24"/><path d="M3.29 7 12 12l8.71-5"/><path d="M12 22V12"/></svg>
);

const MapPin = ({ className }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
);

const RefreshCw = ({ className }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>
);

const Replace = ({ className }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 4c0-1.1.9-2 2-2s2 .9 2 2"/><path d="M20 10c0-1.1.9-2 2-2s2 .9 2 2"/><path d="m22 14-4-4"/><path d="m18 14 4-4"/><path d="M2 18v-2c0-1.1.9-2 2-2h5.5"/><path d="m10 10-4 4 4 4"/><path d="M6 14h12c1.1 0 2-.9 2-2v-2c0-1.1-.9-2-2-2h-1.5"/><path d="M4 20c0 1.1.9 2 2 2s2-.9 2-2"/><path d="M10 20c0 1.1.9 2 2 2s2-.9 2-2"/></svg>
);

const DollarSign = ({ className }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" x2="12" y1="2" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
);

const MessageSquare = ({ className }) => (
    <svg className={className} xmlns="http://www.w.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
);

const Warehouse = ({ className }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 8.35V20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8.35A2 2 0 0 1 3 6.5l8-4.2a2 2 0 0 1 2 0l8 4.2a2 2 0 0 1 1 1.85Z"/><path d="M22 22V11l-10-5.2L2 11v11"/><path d="M12 22V11"/><path d="M6 12.5 12 9l6 3.5"/><path d="M15 18h-6v-4h6v4Z"/></svg>
);

const Home = ({ className }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
);

// --- SHADCN/UI STYLE COMPONENTS ---

const buttonVariants = {
  default: "bg-white text-black hover:bg-gray-200",
  secondary: "bg-gray-800 text-white hover:bg-gray-700",
  ghost: "hover:bg-gray-800 hover:text-white",
  destructive: "bg-red-500 text-white hover:bg-red-600",
};

const cardVariants = {
  default: "bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-lg",
};

const Button = React.forwardRef(({ className, variant, ...props }, ref) => {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-bold transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 disabled:opacity-50 disabled:pointer-events-none",
        buttonVariants[variant] || buttonVariants.default,
        className
      )}
      ref={ref}
      {...props}
    />
  );
});
Button.displayName = "Button";

const Card = React.forwardRef(({ className, variant, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(cardVariants[variant] || cardVariants.default, className)}
    {...props}
  />
));
Card.displayName = "Card";

// --- ERROR BOUNDARY ---

class ErrorBoundary extends React.Component {
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
        <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center">
          <h1 className="text-3xl font-bold mb-4">Something went wrong.</h1>
          <p className="text-gray-400">Please refresh the page to try again.</p>
        </div>
      );
    }
    return this.props.children;
  }
}

// --- PAGE SECTIONS ---

const Header = () => (
  <header className="sticky top-0 z-50 w-full border-b border-gray-800 bg-black/80 backdrop-blur-lg">
    <div className="container mx-auto flex h-16 items-center justify-between px-4 md:px-6">
      <a href="#" className="flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6 text-white"><path d="m12 3-1.45 4.14L6.34 8.2l4.14 1.45L12 14l1.45-4.14L17.66 8.2l-4.14-1.45L12 3z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></svg>
        <span className="text-xl font-bold text-white">Swiftly</span>
      </a>
      <Button variant="default">Get The App</Button>
    </div>
  </header>
);

const Hero = () => (
  <section className="relative w-full overflow-hidden bg-black pt-20 pb-20 md:pt-32 md:pb-24">
    <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-black to-gray-800 opacity-80"></div>
    <div className="container mx-auto px-4 md:px-6 relative z-10 text-center">
      <h1 className="text-4xl md:text-6xl lg:text-7xl font-extrabold tracking-tighter text-white">
        Groceries in Minutes. Not Hours.
      </h1>
      <p className="mt-6 max-w-2xl mx-auto text-lg md:text-xl text-gray-300">
        Your favorite local products, delivered from our hub to your door in under 10 minutes. Welcome to the future of convenience.
      </p>
      <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
        <Button variant="default" className="flex items-center gap-2">
          <AppleLogo className="w-5 h-5" /> Download for iOS
        </Button>
        <Button variant="secondary" className="flex items-center gap-2">
          <AndroidLogo className="w-5 h-5" /> Download for Android
        </Button>
      </div>
      <div className="mt-16 mx-auto max-w-md">
        <div className="relative mx-auto border-gray-800 bg-gray-800 border-[8px] rounded-t-xl h-[172px] max-w-[301px] md:h-[294px] md:max-w-[512px]">
            <div className="rounded-lg overflow-hidden h-[156px] md:h-[278px] bg-black">
                <img src="https://images.unsplash.com/photo-1601598851547-4302969d0614?q=80&w=800&auto=format&fit=crop" alt="App Screenshot" className="h-full w-full object-cover" />
            </div>
        </div>
        <div className="relative mx-auto bg-gray-900 rounded-b-xl h-[24px] max-w-[301px] md:h-[42px] md:max-w-[512px]"></div>
        <div className="relative mx-auto bg-gray-800 rounded-b-xl h-[55px] max-w-[83px] md:h-[95px] md:max-w-[142px]"></div>
      </div>
    </div>
  </section>
);

const features = [
  {
    icon: <PackageCheck className="w-8 h-8 text-white" />,
    name: 'Live Inventory from Local Hubs',
    description: "Browse a real-time catalog of your nearest micro-fulfillment center. If it's in the app, it's in stock and ready for delivery.",
  },
  {
    icon: <MapPin className="w-8 h-8 text-white" />,
    name: 'Real-Time Rider Tracking',
    description: "Watch your rider's progress on a live map from the moment you order. No more guessing, just accurate ETAs.",
  },
  {
    icon: <RefreshCw className="w-8 h-8 text-white" />,
    name: "One-Tap 'Buy It Again'",
    description: "Restock your weekly essentials in seconds. Your order history lets you re-add entire past orders to your cart with a single tap.",
  },
  {
    icon: <Replace className="w-8 h-8 text-white" />,
    name: 'Smart & Instant Substitutions',
    description: "If an item is unavailable, we'll suggest a similar product for your approval via push notification, ensuring your order is always complete.",
  },
  {
    icon: <DollarSign className="w-8 h-8 text-white" />,
    name: 'Dynamic Delivery Fee Tiers',
    description: "Our delivery fee adjusts based on demand. Order during off-peak hours or over a certain amount to get free delivery.",
  },
  {
    icon: <MessageSquare className="w-8 h-8 text-white" />,
    name: 'In-App Chat with Rider',
    description: "Need to provide a gate code or specific drop-off instructions? Communicate directly with your rider through our secure in-app chat.",
  },
];

const Features = () => (
  <section className="py-20 md:py-28 bg-black">
    <div className="container mx-auto px-4 md:px-6">
      <div className="text-center max-w-3xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-bold text-white">Everything You Need, Faster Than Ever</h2>
        <p className="mt-4 text-lg text-gray-400">
          Swiftly is packed with features designed to save you time and eliminate the hassles of traditional grocery shopping.
        </p>
      </div>
      <div className="mt-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {features.map((feature, index) => (
          <Card key={index} className="flex flex-col items-start text-left hover:border-gray-600 transition-colors duration-300">
            <div className="p-3 bg-gray-800 rounded-lg mb-4">
              {feature.icon}
            </div>
            <h3 className="text-xl font-bold text-white">{feature.name}</h3>
            <p className="mt-2 text-gray-400">{feature.description}</p>
          </Card>
        ))}
      </div>
    </div>
  </section>
);

const RiderTrackingSection = () => {
  return (
    <section className="py-20 md:py-28 bg-gray-950">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-white">Never Lose Sight of Your Order</h2>
          <p className="mt-4 text-lg text-gray-400">
            Our live tracking map gives you peace of mind, showing your delivery's journey from our hub to your home in real-time.
          </p>
        </div>
        <div className="mt-16 max-w-4xl mx-auto">
          <Card className="p-4 md:p-8 bg-black border-gray-800">
            <div className="relative w-full h-64 md:h-96 bg-gray-900 rounded-lg overflow-hidden">
              {/* Map background lines */}
              <div className="absolute top-1/2 left-0 w-full h-px bg-gray-700/50"></div>
              <div className="absolute left-1/2 top-0 h-full w-px bg-gray-700/50"></div>
              <div className="absolute top-0 left-0 w-full h-full" style={{ background: 'radial-gradient(circle, rgba(156, 163, 175, 0.05) 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>
              
              {/* Hub and Home Icons */}
              <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center">
                <Warehouse className="w-10 h-10 text-gray-400" />
                <span className="text-xs font-semibold text-gray-400 mt-1">Local Hub</span>
              </div>
              <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 flex flex-col items-center">
                <Home className="w-10 h-10 text-white" />
                <span className="text-xs font-semibold text-white mt-1">Your Home</span>
              </div>

              {/* Dotted Path */}
              <svg className="absolute top-0 left-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                <path d="M 25 25 L 75 75" stroke="white" strokeWidth="0.5" strokeDasharray="2 2" fill="none" />
              </svg>

              {/* Rider Icon with Animation */}
              <div className="absolute top-1/4 left-1/4 rider-animation">
                <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-2xl shadow-white/50">
                  <MapPin className="w-5 h-5 text-black" />
                </div>
              </div>
              
              {/* ETA Card */}
              <div className="absolute bottom-4 left-4 bg-black/70 backdrop-blur-sm border border-gray-700 rounded-lg p-3 text-white">
                <p className="text-sm font-bold">ETA: 3 minutes</p>
                <p className="text-xs text-gray-300">Rider: David</p>
              </div>
            </div>
          </Card>
        </div>
      </div>
      <style>{`
        @keyframes moveRider {
          0% { transform: translate(0, 0); }
          100% { transform: translate(200%, 200%); }
        }
        .rider-animation {
          animation: moveRider 8s ease-in-out infinite;
        }
        @media (min-width: 768px) {
          @keyframes moveRider {
            0% { transform: translate(0, 0); }
            100% { transform: translate(384%, 384%); }
          }
        }
      `}</style>
    </section>
  );
};

const testimonials = [
    {
        quote: "Swiftly is a lifesaver. I ordered ingredients for dinner during a meeting, and they arrived before I even finished my call. Unbelievably fast!",
        name: "Sarah L.",
        title: "Busy Professional",
    },
    {
        quote: "As a new parent, quick trips to the store are impossible. The 'Buy It Again' feature for diapers and formula has saved me so much time and stress.",
        name: "Mike R.",
        title: "New Dad",
    },
    {
        quote: "The live tracking is my favorite part. I know exactly when to expect my delivery, which is perfect for my packed schedule. The app is so sleek and easy to use.",
        name: "Jessica T.",
        title: "Freelance Designer",
    }
];

const Testimonials = () => (
    <section className="py-20 md:py-28 bg-black">
        <div className="container mx-auto px-4 md:px-6">
            <div className="text-center max-w-3xl mx-auto">
                <h2 className="text-3xl md:text-4xl font-bold text-white">Trusted by People Who Value Time</h2>
                <p className="mt-4 text-lg text-gray-400">
                    See why busy professionals, parents, and convenience-seekers are choosing Swiftly for their daily needs.
                </p>
            </div>
            <div className="mt-16 grid grid-cols-1 lg:grid-cols-3 gap-8">
                {testimonials.map((testimonial, index) => (
                    <Card key={index} className="flex flex-col justify-between">
                        <div>
                            <div className="flex mb-4 text-yellow-400">
                                {[...Array(5)].map((_, i) => <Star key={i} />)}
                            </div>
                            <blockquote className="text-gray-300">"{testimonial.quote}"</blockquote>
                        </div>
                        <footer className="mt-6">
                            <p className="font-bold text-white">{testimonial.name}</p>
                            <p className="text-sm text-gray-500">{testimonial.title}</p>
                        </footer>
                    </Card>
                ))}
            </div>
        </div>
    </section>
);

const CTA = () => (
    <section className="py-20 md:py-28 bg-gray-950">
        <div className="container mx-auto px-4 md:px-6 text-center">
            <h2 className="text-3xl md:text-5xl font-extrabold text-white">Ready for 10-Minute Deliveries?</h2>
            <p className="mt-4 max-w-xl mx-auto text-lg text-gray-400">
                Join thousands of users who have reclaimed their time. Download Swiftly now and get your first delivery on us.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
                <Button variant="default" className="flex items-center gap-2">
                    <AppleLogo className="w-5 h-5" /> Download for iOS
                </Button>
                <Button variant="secondary" className="flex items-center gap-2">
                    <AndroidLogo className="w-5 h-5" /> Download for Android
                </Button>
            </div>
        </div>
    </section>
);

const Footer = () => (
    <footer className="py-8 bg-black border-t border-gray-800">
        <div className="container mx-auto px-4 md:px-6 flex flex-col md:flex-row justify-between items-center">
            <p className="text-sm text-gray-500">&copy; {new Date().getFullYear()} Swiftly Inc. All rights reserved.</p>
            <div className="flex gap-4 mt-4 md:mt-0">
                <a href="#" className="text-sm text-gray-400 hover:text-white transition-colors">Terms of Service</a>
                <a href="#" className="text-sm text-gray-400 hover:text-white transition-colors">Privacy Policy</a>
            </div>
        </div>
    </footer>
);


// --- MAIN APP COMPONENT ---

const App = () => {
  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-black text-white font-sans antialiased">
        <Header />
        <main>
          <Hero />
          <Features />
          <RiderTrackingSection />
          <Testimonials />
          <CTA />
        </main>
        <Footer />
      </div>
    </ErrorBoundary>
  );
};

export default App;