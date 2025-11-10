import React, { useState } from 'react';
import { motion } from 'framer-motion';

export const Input = ({ 
  label, 
  error, 
  className = '',
  type = 'text',
  ...props 
}) => {
  const [focused, setFocused] = useState(false);
  const [hasValue, setHasValue] = useState(props.value || props.defaultValue);

  return (
    <div className={`relative ${className}`}>
      <input
        type={type}
        className={`peer w-full px-4 py-3 border-2 rounded-lg bg-white transition-all duration-200 placeholder-transparent focus:outline-none ${
          error 
            ? 'border-red-300 focus:border-red-500' 
            : 'border-gray-200 focus:border-blue-500'
        }`}
        placeholder=" "
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onChange={(e) => {
          setHasValue(e.target.value);
          props.onChange?.(e);
        }}
        {...props}
      />
      {label && (
        <motion.label
          className={`absolute left-4 transition-all duration-200 pointer-events-none ${
            focused || hasValue
              ? '-top-2 text-xs bg-white px-2 text-blue-600'
              : 'top-3 text-gray-500'
          }`}
          animate={{
            y: focused || hasValue ? -8 : 0,
            scale: focused || hasValue ? 0.85 : 1,
          }}
        >
          {label}
        </motion.label>
      )}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-1 text-sm text-red-500"
        >
          {error}
        </motion.div>
      )}
    </div>
  );
};

export const TextArea = ({ label, error, rows = 4, className = '', ...props }) => {
  const [focused, setFocused] = useState(false);
  const [hasValue, setHasValue] = useState(props.value || props.defaultValue);

  return (
    <div className={`relative ${className}`}>
      <textarea
        rows={rows}
        className={`peer w-full px-4 py-3 border-2 rounded-lg bg-white transition-all duration-200 placeholder-transparent focus:outline-none resize-none ${
          error 
            ? 'border-red-300 focus:border-red-500' 
            : 'border-gray-200 focus:border-blue-500'
        }`}
        placeholder=" "
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onChange={(e) => {
          setHasValue(e.target.value);
          props.onChange?.(e);
        }}
        {...props}
      />
      {label && (
        <motion.label
          className={`absolute left-4 transition-all duration-200 pointer-events-none ${
            focused || hasValue
              ? '-top-2 text-xs bg-white px-2 text-blue-600'
              : 'top-3 text-gray-500'
          }`}
          animate={{
            y: focused || hasValue ? -8 : 0,
            scale: focused || hasValue ? 0.85 : 1,
          }}
        >
          {label}
        </motion.label>
      )}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-1 text-sm text-red-500"
        >
          {error}
        </motion.div>
      )}
    </div>
  );
};