import React from 'react';

const Home = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to app-1758464736392
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          build a simple application to add and remove events at a college 

        </p>
        <div className="space-x-4">
          <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            Get Started
          </button>
          <button className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded">
            Learn More
          </button>
        </div>
      </div>
      
      <div className="grid md:grid-cols-3 gap-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Feature 1</h3>
          <p className="text-gray-600">Description of your first key feature.</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Feature 2</h3>
          <p className="text-gray-600">Description of your second key feature.</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Feature 3</h3>
          <p className="text-gray-600">Description of your third key feature.</p>
        </div>
      </div>
    </div>
  );
};

export default Home;