```javascript
import React, { useState, useEffect, Suspense } from 'react';
import { Routes, Route, Link, useParams, useNavigate } from 'react-router-dom';
import { Search, Star, Clock, ChefHat, ShoppingCart, ArrowLeft, AlertTriangle } from 'lucide-react';

//  Mock API 
// In a real app, this would be in a separate file (e.g., src/api.js)
// and would use fetch() or axios to call a real backend.
const mockRestaurants = [
  { id: 1, name: 'Meghana Foods', cuisine: 'Biryani, North Indian', rating: 4.5, deliveryTime: 30, imageUrl: 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?q=80&w=800' },
  { id: 2, name: 'KFC', cuisine: 'Burgers, Fast Food', rating: 4.1, deliveryTime: 25, imageUrl: 'https://images.unsplash.com/photo-1562967914-608f82629710?q=80&w=800' },
  { id: 3, name: 'Pizza Hut', cuisine: 'Pizzas, Italian', rating: 3.9, deliveryTime: 45, imageUrl: 'https://images.unsplash.com/photo-1513104890138-7c749659a591?q=80&w=800' },
  { id: 4, name: 'Subway', cuisine: 'Salads, Sandwiches', rating: 4.3, deliveryTime: 20, imageUrl: 'https://images.unsplash.com/photo-1553909489-cd47e0907910?q=80&w=800' },
  { id: 5, name: 'Burger King', cuisine: 'Burgers, American', rating: 4.2, deliveryTime: 35, imageUrl: 'https://images.unsplash.com/photo-1571091718767-18b5b1457add?q=80&w=800' },
  { id: 6, name: 'Taco Bell', cuisine: 'Mexican, Fast Food', rating: 4.0, deliveryTime: 40, imageUrl: 'https://images.unsplash.com/photo-1552332386-f8dd00dc2f85?q=80&w=800' },
  { id: 7, name: "Domino's Pizza", cuisine: 'Pizzas, Italian', rating: 4.4, deliveryTime: 30, imageUrl: 'https://images.unsplash.com/photo-1594007654729-407eedc4be65?q=80&w=800' },
  { id: 8, name: 'Wow! Momo', cuisine: 'Chinese, Tibetan', rating: 4.6, deliveryTime: 28, imageUrl: 'https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?q=80&w=800' },
];

const mockMenu = {
  1: { name: 'Meghana Foods', items: [{ name: 'Chicken Biryani', price: 320 }, { name: 'Mutton Biryani', price: 450 }, { name: 'Paneer Butter Masala', price: 280 }] },
  2: { name: 'KFC', items: [{ name: 'Zinger Burger', price: 199 }, { name: 'Hot Wings (6pc)', price: 250 }, { name: 'Large Fries', price: 120 }] },
  3: { name: 'Pizza Hut', items: [{ name: 'Margherita Pizza', price: 299 }, { name: 'Pepperoni Pizza', price: 450 }, { name: 'Garlic Bread', price: 150 }] },
  4: { name: 'Subway', items: [{ name: 'Veggie Delite Salad', price: 220 }, { name: 'Chicken Teriyaki Sub', price: 300 }, { name: 'Cookie', price: 50 }] },
  // ... more menus
};

const mockApi = {
  fetchRestaurants: () => new Promise(resolve => setTimeout(() => resolve(mockRestaurants), 1000)),
  fetchRestaurantMenu: (id) => new Promise((resolve, reject) => {
    setTimeout(() => {
      const menuData = mockMenu[id];
      const restaurantInfo = mockRestaurants.find(r => r.id === parseInt(id));
      if (menuData && restaurantInfo) {
        resolve({ ...restaurantInfo, ...menuData });
      } else {
        reject(new Error('Restaurant not found'));
      }
    }, 1000);
  }),
};

//  Helper & Utility Components 

const ShimmerCard = () => (

);

const ShimmerMenu = () => (

        {[...Array(5)].map((_, i) => (

        ))}
    
);

const ErrorComponent = ({ message }) => (

    Oops! Something went wrong.
    {message || "We couldn't load the data. Please try again later."}
  
);

//  Page & Layout Components 

const Header = () => (

        DishDash

        Offers
        Help

          Cart

);

const Footer = () => (

      &copy; {new Date().getFullYear()} DishDash. All Rights Reserved.
      A project built by GitHub Copilot.

);

const RestaurantCard = ({ restaurant }) => (

      {restaurant.name}
      {restaurant.cuisine}

           {restaurant.rating}

             {restaurant.deliveryTime} MINS

);

const HomePage = () => {
  const [restaurants, setRestaurants] = useState([]);
  const [filteredRestaurants, setFilteredRestaurants] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const getRestaurants = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await mockApi.fetchRestaurants();
        setRestaurants(data);
        setFilteredRestaurants(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    getRestaurants();
  }, []);
  
  useEffect(() => {
    const results = restaurants.filter(res =>
      res.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      res.cuisine.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredRestaurants(results);
  }, [searchTerm, restaurants]);

  return (

           setSearchTerm(e.target.value)}
            className="w-full p-4 pl-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />

      Restaurants near you
      
      {loading && (
        
          {[...Array(8)].map((_, i) => )}
        
      )}

      {error && }

      {!loading && !error && filteredRestaurants.length > 0 && (
        
          {filteredRestaurants.map(restaurant => (
            
          ))}
        
      )}

      {!loading && !error && filteredRestaurants.length === 0 && (
        
            No restaurants found matching your search.
        
      )}
    
  );
};

const RestaurantMenuPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [restaurant, setRestaurant] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const getMenu = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await mockApi.fetchRestaurantMenu(id);
                setRestaurant(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        getMenu();
    }, [id]);

    if (loading) return ;
    if (error) return ;
    if (!restaurant) return ;

    return (
        
              navigate(-1)} className="flex items-center gap-2 mb-6 text-gray-600 hover:text-primary">
                 Back to restaurants

                    {restaurant.name}
                    {restaurant.cuisine}

                             {restaurant.rating}

                             {restaurant.deliveryTime} MINS

            Menu
            
                {restaurant.items.map(item => (

                            {item.name}
                            ₹{item.price}

                            ADD

                ))}

    );
};

//  Main App Component 

function App() {
  return (

          } />
          } />

  );
}

export default App;
```