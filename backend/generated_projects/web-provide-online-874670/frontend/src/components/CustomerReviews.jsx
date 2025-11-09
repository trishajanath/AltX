import React, { useState } from 'react';

const CustomerReviews = () => {
  const [reviews, setReviews] = useState([
    { id: 1, name: 'John Doe', rating: 5, comment: 'Excellent service!' },
    { id: 2, name: 'Jane Smith', rating: 4, comment: 'Very satisfied with my purchase.' }
  ]);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">Customer Reviews</h2>
      <div className="space-y-4">
        {reviews.map(review => (
          <div key={review.id} className="border rounded-lg p-4 shadow-sm">
            <div className="flex items-center mb-2">
              <h3 className="font-semibold text-lg">{review.name}</h3>
              <div className="ml-auto flex">
                {[...Array(review.rating)].map((_, i) => (
                  <span key={i} className="text-yellow-500">⭐</span>
                ))}
              </div>
            </div>
            <p className="text-gray-700">{review.comment}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CustomerReviews;