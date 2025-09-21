```javascript
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Star, ShieldCheck, Truck } from 'lucide-react';

const ProductDetailPage = () => {
  const { productId } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [mainImage, setMainImage] = useState('');

  useEffect(() => {
    const fetchProduct = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`https://dummyjson.com/products/${productId}`);
        if (!response.ok) {
          throw new Error('Product not found.');
        }
        const data = await response.json();
        setProduct(data);
        setMainImage(data.thumbnail);
      } catch (e) {
        setError(e.message);
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchProduct();
  }, [productId]);

  if (loading) {
    return ;
  }

  if (error) {
    return (
      
        {error}
        Go back to homepage
      
    );
  }

  if (!product) return null;
  
  const discountPrice = (product.price * (1 - product.discountPercentage / 100)).toFixed(2);

  return (

        {/* Image Gallery */}

            {product.images.map((img, index) => (
               setMainImage(img)}
              />
            ))}

        {/* Product Details */}
        
          {product.title}
          {product.brand}

              {[...Array(Math.floor(product.rating))].map((_, i) => )}
              {[...Array(5 - Math.floor(product.rating))].map((_, i) => )}
            
            {product.rating.toFixed(1)} ({product.stock} reviews)

            ${discountPrice}
            ${product.price.toFixed(2)}
            {Math.round(product.discountPercentage)}% OFF

          {product.description}

            Quantity:
             setQuantity(q => Math.max(1, q-1))} className="border px-3 py-1 rounded-l-md">-
            {quantity}
             setQuantity(q => q+1)} className="border px-3 py-1 rounded-r-md">+
            {product.stock} pieces available

            Add to Cart
            Buy Now

              Buyer Protection: Get a refund if the item is not as described.

              Free Shipping & Free Returns

  );
};

export default ProductDetailPage;
```