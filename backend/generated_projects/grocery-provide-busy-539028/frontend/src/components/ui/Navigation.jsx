import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Menu, X } from 'lucide-react';

export const NavBar = ({ children, className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className={`bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {children}
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </div>
      
      {/* Mobile menu */}
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{
          opacity: isOpen ? 1 : 0,
          height: isOpen ? 'auto' : 0
        }}
        className="md:hidden bg-white border-t border-gray-200"
      >
        <div className="px-2 pt-2 pb-3 space-y-1">
          {children}
        </div>
      </motion.div>
    </nav>
  );
};

export const NavLink = ({ children, active = false, className = '', ...props }) => (
  <motion.a
    whileHover={{ y: -2 }}
    className={`px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
      active
        ? 'text-blue-600 bg-blue-50'
        : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
    } ${className}`}
    {...props}
  >
    {children}
  </motion.a>
);

export const FloatingTabs = ({ tabs, activeTab, onTabChange, className = '' }) => (
  <div className={`flex bg-gray-100 p-1 rounded-lg ${className}`}>
    {tabs.map((tab) => (
      <motion.button
        key={tab.id}
        onClick={() => onTabChange(tab.id)}
        className={`relative px-6 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
          activeTab === tab.id
            ? 'text-blue-600'
            : 'text-gray-600 hover:text-gray-900'
        }`}
        whileHover={{ y: -1 }}
        whileTap={{ y: 0 }}
      >
        {activeTab === tab.id && (
          <motion.div
            layoutId="activeTab"
            className="absolute inset-0 bg-white rounded-md shadow-sm"
            transition={{ type: "spring", duration: 0.3 }}
          />
        )}
        <span className="relative z-10">{tab.label}</span>
      </motion.button>
    ))}
  </div>
);