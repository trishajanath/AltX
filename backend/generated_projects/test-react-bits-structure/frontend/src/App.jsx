import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Welcome to Test React Bits Structure</h1>
        <p className="text-gray-300 mb-4">Your application is ready!</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-md mx-auto">
          <div className="bg-gray-800 p-4 rounded-lg">
            <h3 className="font-semibold mb-2">Frontend</h3>
            <p className="text-sm text-gray-400">React + Vite + Tailwind CSS</p>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg">
            <h3 className="font-semibold mb-2">Backend</h3>
            <p className="text-sm text-gray-400">FastAPI + Python</p>
          </div>
        </div>
        <div className="mt-8">
          <p className="text-blue-400 text-sm">Ready for development!</p>
        </div>
      </div>
    </div>
  );
}

export default App;