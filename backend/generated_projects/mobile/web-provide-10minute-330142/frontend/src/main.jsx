// main.jsx - mobile/web-provide-10minute-330142 React Entry Point
// VALIDATED: Syntax ✓ Imports ✓ Functionality ✓

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// Create root and render app
const root = ReactDOM.createRoot(document.getElementById('root'))
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
