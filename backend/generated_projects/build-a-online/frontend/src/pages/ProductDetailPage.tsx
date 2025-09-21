```typescript
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchProductById } from '../api/products';
import { Product } from '../types';
import Spinner from '../components/ui/Spinner';
import ErrorMessage from '../components/ui/ErrorMessage';
import { Star, ChevronLeft } from 'lucide-react';

const ProductDetailPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const getProduct = async () => {
      if (!id) return;
      try {
        setLoading(true);
        const productId = parseInt(id, 10);
        const data = await fetchProductById(productId);
        if (data) {
          setProduct(data);
          setError(null);
        } else {
          setError('Product not found.');
        }
      } catch (err) {
        setError('Failed to fetch product details. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    getProduct();
  }, [id]);

  if (loading) return ;
  if (error) return ;
  if (!product) return ;

  return (
    
       navigate(-1)} 
        className="flex items-center text-sm font-medium text-brand-secondary hover:text-brand-primary mb-8"
      >
        
        Back to Products

        {/* Product Image */}

        {/* Product Info */}
        
          {product.name}
          {product.category}

              {[...Array(5)].map((_, i) => (
                
              ))}

              {product.rating.rate} stars ({product.rating.count} reviews)

          ${product.price.toFixed(2)}

            {product.description}

              Add to Cart

  );
};

export default ProductDetailPage;
```