```typescript
import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import { ShoppingBag, Menu, X } from 'lucide-react';

const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'Shop All', path: '/products' },
    { name: 'New Arrivals', path: '/products?category=new' },
    { name: 'About Us', path: '/about' },
  ];

  return (

              VogueVerse

              {navLinks.map((link) => (
                
                    `text-sm font-medium transition-colors ${
                      isActive ? 'text-brand-primary' : 'text-brand-secondary hover:text-brand-primary'
                    }`
                  }
                >
                  {link.name}
                
              ))}

               setIsMenuOpen(!isMenuOpen)} className="p-2 rounded-md text-brand-secondary hover:bg-gray-100">
                {isMenuOpen ?  : }

      {/* Mobile Menu */}
      {isMenuOpen && (

            {navLinks.map((link) => (
               setIsMenuOpen(false)}
                className={({ isActive }) =>
                  `block px-3 py-2 rounded-md text-base font-medium ${
                    isActive ? 'bg-gray-100 text-brand-primary' : 'text-brand-secondary hover:bg-gray-50'
                  }`
                }
              >
                {link.name}
              
            ))}

      )}
    
  );
};

export default Header;
```