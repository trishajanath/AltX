```typescript
export interface Product {
  id: number;
  name: string;
  price: number;
  imageUrl: string;
  category: string;
  description: string;
  rating: {
    rate: number;
    count: number;
  };
}
```