import React, { useState } from 'react';

const WishList = () => {
  const [wishlistItems, setWishlistItems] = useState([
    { id: 1, name: 'Product A', price: 29.99, image: '/placeholder-image.jpg' },
    { id: 2, name: 'Product B', price: 49.99, image: '/placeholder-image.jpg' }
  ]);

  const removeFromWishlist = (id) => {
    setWishlistItems(wishlistItems.filter(item => item.id !== id));
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">My Wishlist</h2>
      {wishlistItems.length === 0 ? (
        <p className="text-gray-500">Your wishlist is empty.</p>
      ) : (
        <div className="grid gap-4">
          {wishlistItems.map(item => (
            <div key={item.id} className="border rounded-lg p-4 flex items-center gap-4">
              <img src={item.image} alt={item.name} className="w-16 h-16 object-cover rounded" />
              <div className="flex-1">
                <h3 className="font-semibold">{item.name}</h3>
                <p className="text-green-600 font-bold">${item.price}</p>
              </div>
              <button
                onClick={() => removeFromWishlist(item.id)}
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default WishList;