import React from 'react';

function DebugApp() {
  console.log('DebugApp component rendering');
  
  try {
    // Try to import and use react-router-dom
    const { BrowserRouter, Routes, Route } = require('react-router-dom');
    console.log('React Router imported successfully');
    
    return (
      <BrowserRouter>
        <div style={{ padding: '20px' }}>
          <h1>Debug: React Router Works</h1>
          <Routes>
            <Route path="/" element={<div>Home Route</div>} />
          </Routes>
        </div>
      </BrowserRouter>
    );
  } catch (error) {
    console.error('Error in DebugApp:', error);
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        <h1>Error Loading App</h1>
        <pre>{String(error)}</pre>
      </div>
    );
  }
}

export default DebugApp;