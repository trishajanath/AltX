```javascript
import React from 'react';
import { Star } from 'lucide-react';
import { Link } from 'react-router-dom';

const ProductCard = ({ product }) => {
  if (!product) return null;

  const renderStars = (rating) => {
    const stars = [];
    for (let i = 0; i 
      );
    }
    return stars;
  };

  const discountPrice = (product.price * (1 - product.discountPercentage / 100)).toFixed(2);

  return (

          {Math.round(product.discountPercentage)}% OFF

          {product.title}

          ${discountPrice}
          ${product.price.toFixed(2)}

            {renderStars(product.rating)}
          
          ({product.stock} sold)

  );
};

export default ProductCard;
```