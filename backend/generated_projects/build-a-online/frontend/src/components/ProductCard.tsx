```typescript
import React from 'react';
import { Link } from 'react-router-dom';
import { Product } from '../types';
import { Star } from 'lucide-react';

interface ProductCardProps {
  product: Product;
}

const ProductCard: React.FC = ({ product }) => {
  return (

          {product.name}
          
            {product.category}

              {product.rating.rate} ({product.rating.count})

          ${product.price.toFixed(2)}

  );
};

export default ProductCard;
```