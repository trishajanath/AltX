import React from 'react';

const MatchedPeople = () => {
  // Placeholder data for matched people
  const matchedPeople = [
    { id: 1, name: 'Alice', imageUrl: 'https://example.com/alice.jpg' },
    { id: 2, name: 'Bob', imageUrl: 'https://example.com/bob.jpg' },
    { id: 3, name: 'Charlie', imageUrl: 'https://example.com/charlie.jpg' },
  ];

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Your Matches</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {matchedPeople.map(person => (
          <div key={person.id} className="bg-white rounded-lg shadow-md overflow-hidden">
            <img src={person.imageUrl} alt={person.name} className="w-full h-48 object-cover" />
            <div className="p-4">
              <h2 className="text-lg font-semibold">{person.name}</h2>
              {/* Add more details or actions here */}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MatchedPeople;