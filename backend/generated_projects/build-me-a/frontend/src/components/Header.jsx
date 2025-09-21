```javascript
import React, { useState } from 'react';
import { Search, User, Heart, ShoppingCart, Menu, X } from 'lucide-react';
import { Link } from 'react-router-dom';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (

        {/* Top Bar */}

            Customer Service
            Download App
            Sell on DealDash

            Register
            Sign In

        {/* Main Header */}

              DealDash

              New Arrivals
              Best Sellers
              Electronics
              Home Goods

              3

              5
            
             setIsMenuOpen(!isMenuOpen)}>
              {isMenuOpen ?  : }

        {/* Mobile Menu & Search */}
        {isMenuOpen && (

              New Arrivals
              Best Sellers
              Electronics
              Home Goods

        )}

  );
};

export default Header;
```