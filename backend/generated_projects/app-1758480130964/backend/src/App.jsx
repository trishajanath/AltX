import React, { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <header className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              App 1758480130964
            </h1>
            <p className="text-xl text-gray-600">
              Welcome to your new React application!
            </p>
          </header>
          
          <main className="bg-white rounded-lg shadow-lg p-8">
            <div className="text-center">
              <button
                className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                onClick={() => setCount(count + 1)}
              >
                Count is {count}
              </button>
              <p className="mt-4 text-gray-600">
                Click the button to test the React functionality.
              </p>
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}

export default App