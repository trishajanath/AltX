```javascript
import React from 'react';
import { Facebook, Twitter, Instagram, Youtube } from 'lucide-react';

const Footer = () => {
  return (

          {/* Column 1 */}
          
            Customer Care
            
              Help Center
              Track Your Order
              Returns & Refunds
              Contact Us

          {/* Column 2 */}
          
            About DealDash
            
              About Us
              Careers
              Press
              Affiliate Program

          {/* Column 3 */}
          
            Payment Methods

          {/* Column 4 */}
          
            Follow Us

          {/* Column 5 */}
          
            Download Our App
            Get exclusive deals and manage orders on the go.

          &copy; {new Date().getFullYear()} DealDash. All rights reserved.
          Privacy Policy | Terms of Service

  );
};

export default Footer;
```