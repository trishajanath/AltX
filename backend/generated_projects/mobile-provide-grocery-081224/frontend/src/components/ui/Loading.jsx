import React from 'react';
import { motion } from 'framer-motion';

export const SkeletonLoader = ({ className = '', lines = 3 }) => (
  <div className={`animate-pulse space-y-3 ${className}`}>
    {Array.from({ length: lines }).map((_, i) => (
      <div key={i} className="h-4 bg-gray-200 rounded-md"></div>
    ))}
  </div>
);

export const SpinnerLoader = ({ size = 'md', className = '' }) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8', 
    lg: 'w-12 h-12'
  };

  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
      className={`${sizes[size]} border-2 border-gray-200 border-t-blue-600 rounded-full ${className}`}
    />
  );
};

export const PulseLoader = ({ className = '' }) => (
  <div className={`flex space-x-2 ${className}`}>
    {[0, 1, 2].map(i => (
      <motion.div
        key={i}
        animate={{ scale: [1, 1.2, 1] }}
        transition={{
          duration: 0.8,
          repeat: Infinity,
          delay: i * 0.2 
        }}
        className="w-3 h-3 bg-blue-600 rounded-full"
      />
    ))}
  </div>
);