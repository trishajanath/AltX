import React from 'react';
import './App.css';

function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Test App
          </h1>
          <p className="text-gray-600 mt-2">test app</p>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Welcome to your new app!</h2>
          <p className="text-gray-600">
            This is a full-stack application generated based on your idea.
            The backend API is ready and the frontend is set up with TailwindCSS.
          </p>
          
          <div className="mt-6 space-y-4">
            <button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
              Get Started
            </button>
            
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;