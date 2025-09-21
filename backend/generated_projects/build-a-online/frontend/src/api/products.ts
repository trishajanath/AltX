```typescript
import { mockProducts } from '../data/mockProducts';
import { Product } from '../types';

// Simulate an API call with a delay to demonstrate loading states
export const fetchAllProducts = (): Promise => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockProducts);
    }, 1000); // 1-second delay
  });
};

export const fetchProductById = (id: number): Promise => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const product = mockProducts.find((p) => p.id === id);
      if (product) {
        resolve(product);
      } else {
        reject(new Error('Product not found'));
      }
    }, 800); // 0.8-second delay
  });
};
```