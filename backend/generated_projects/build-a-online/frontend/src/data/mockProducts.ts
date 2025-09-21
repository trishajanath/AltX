```typescript
import { Product } from '../types';

export const mockProducts: Product[] = [
  {
    id: 1,
    name: 'Classic Denim Jacket',
    price: 79.99,
    imageUrl: 'https://images.unsplash.com/photo-1543087902-61678a294438?q=80&w=800',
    category: "Jackets",
    description: 'A timeless denim jacket that fits any style. Made with 100% premium cotton for ultimate comfort and durability. Features classic button closure and two chest pockets.',
    rating: { rate: 4.5, count: 150 },
  },
  {
    id: 2,
    name: 'Organic Cotton T-Shirt',
    price: 24.99,
    imageUrl: 'https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?q=80&w=800',
    category: "T-Shirts",
    description: 'Soft, breathable, and eco-friendly. This t-shirt is made from 100% organic cotton and is a perfect staple for any wardrobe.',
    rating: { rate: 4.8, count: 450 },
  },
  {
    id: 3,
    name: 'Slim Fit Chinos',
    price: 59.99,
    imageUrl: 'https://images.unsplash.com/photo-1604176354204-9268737828e4?q=80&w=800',
    category: "Pants",
    description: 'Modern and versatile, these slim-fit chinos are perfect for both casual and semi-formal occasions. Crafted with a slight stretch for added comfort.',
    rating: { rate: 4.3, count: 220 },
  },
  {
    id: 4,
    name: 'Leather Ankle Boots',
    price: 129.99,
    imageUrl: 'https://images.unsplash.com/photo-1608256247963-33e4b787595b?q=80&w=800',
    category: "Shoes",
    description: 'Handcrafted from genuine leather, these ankle boots offer both style and durability. A must-have for the fashion-forward individual.',
    rating: { rate: 4.6, count: 180 },
  },
  {
    id: 5,
    name: 'Wool Winter Scarf',
    price: 34.99,
    imageUrl: 'https://images.unsplash.com/photo-1542489441-338a0a863654?q=80&w=800',
    category: "Accessories",
    description: 'Stay warm and stylish with this soft wool scarf. Its classic design makes it a versatile accessory for the colder months.',
    rating: { rate: 4.9, count: 310 },
  },
  {
    id: 6,
    name: 'Graphic Print Hoodie',
    price: 64.99,
    imageUrl: 'https://images.unsplash.com/photo-1556821840-3b41595ea936?q=80&w=800',
    category: "Hoodies",
    description: 'A comfortable fleece hoodie featuring a unique graphic print. Perfect for a relaxed, urban look.',
    rating: { rate: 4.2, count: 95 },
  },
  {
    id: 7,
    name: 'Linen Summer Shirt',
    price: 49.99,
    imageUrl: 'https://images.unsplash.com/photo-1621072156002-e2fccdc0b176?q=80&w=800',
    category: "Shirts",
    description: 'Lightweight and breathable, this linen shirt is ideal for warm weather. Its relaxed fit ensures comfort all day long.',
    rating: { rate: 4.7, count: 130 },
  },
  {
    id: 8,
    name: 'Performance Running Shorts',
    price: 39.99,
    imageUrl: 'https://images.unsplash.com/photo-1591195853828-11db59a44f6b?q=80&w=800',
    category: "Sportswear",
    description: 'Engineered for athletes, these running shorts feature moisture-wicking fabric and a comfortable, ergonomic design.',
    rating: { rate: 4.8, count: 205 },
  }
];
```