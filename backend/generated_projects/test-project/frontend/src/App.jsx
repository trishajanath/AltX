import React from 'react';

function App() {
  return (
    <div className="App">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-lg shadow-lg mb-6">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center">
              <span className="text-2xl font-bold text-blue-600">NP</span>
            </div>
            <div>
              <h2 className="text-2xl font-bold">Neelesh Padmanabh</h2>
              <p className="text-blue-100">MBA Graduate</p>
              <p className="text-sm text-blue-200">Business Strategy & Innovation</p>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-white/10 rounded p-3">
              <h3 className="font-semibold">Education</h3>
              <p>MBA Graduate</p>
            </div>
            <div className="bg-white/10 rounded p-3">
              <h3 className="font-semibold">Expertise</h3>
              <p>Strategic Planning</p>
            </div>
            <div className="bg-white/10 rounded p-3">
              <h3 className="font-semibold">Focus</h3>
              <p>Business Innovation</p>
            </div>
          </div>
        </div>
      <header className="App-header">
        <h1 className="text-4xl font-bold mb-4">Welcome to Student Helper</h1>
        <p>This is a test application.</p>
      </header>
    </div>
  );
}

export default App;
