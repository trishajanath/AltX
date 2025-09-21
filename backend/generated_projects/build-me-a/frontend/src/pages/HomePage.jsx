```javascript
import React, { useState, useEffect } from 'react';
import ProductCard from '../components/ProductCard';

const HomePage = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const fetchProducts = async (pageNum) => {
    setLoading(true);
    setError(null);
    try {
      const limit = 20;
      const skip = (pageNum - 1) * limit;
      // Using a free public API for mock data
      const response = await fetch(`https://dummyjson.com/products?limit=${limit}&skip=${skip}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if(data.products.length === 0) {
        setHasMore(false);
      }
      setProducts(prev => [...prev, ...data.products]);
    } catch (e) {
      setError("Failed to fetch products. Please try again later.");
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts(page);
  }, [page]);
  
  const handleLoadMore = () => {
    setPage(prevPage => prevPage + 1);
  };

  return (
    
      Lightning Deals
      
      {error && {error}}

        {products.map(product => (
          
        ))}

        {loading && }
        {!loading && hasMore && (
          
            Load More
          
        )}
        {!hasMore && You've reached the end!}

  );
};

export default HomePage;
```