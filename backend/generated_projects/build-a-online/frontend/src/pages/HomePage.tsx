```typescript
import React from 'react';
import { Link } from 'react-router-dom';
import { useProducts } from '../hooks/useProducts';
import ProductCard from '../components/ProductCard';
import Spinner from '../components/ui/Spinner';
import ErrorMessage from '../components/ui/ErrorMessage';

const HomePage: React.FC = () => {
  const { products, loading, error } = useProducts();

  const featuredProducts = products.slice(0, 4);

  return (
    
      {/* Hero Section */}

            Discover Your Signature Style

            Explore our curated collection of high-quality apparel. From timeless classics to the latest trends.

              Shop Now

      {/* Featured Products Section */}
      
        New Arrivals
        {loading && }
        {error && }
        {!loading && !error && (
          
            {featuredProducts.map((product) => (
              
            ))}
          
        )}

  );
};

export default HomePage;
```