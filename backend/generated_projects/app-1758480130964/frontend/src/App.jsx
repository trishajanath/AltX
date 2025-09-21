import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import Home from './pages/Home.jsx';
import Header from './components/Header.jsx';

function App() {
  return (
    <div className="App min-h-screen bg-gray-50">
      <Router>
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
          </Routes>
        </main>
      </Router>
    </div>
  );
}

export default App;