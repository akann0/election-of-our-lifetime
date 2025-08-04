import React, { useState } from 'react';
import USMap from './USMap';
import ComparisonForm from './ComparisonForm';
import './App.css';

function App() {
  const [currentComparison, setCurrentComparison] = useState({ choice1: '', choice2: '' });
  const [isLoading, setIsLoading] = useState(false);

  const handleCompare = (choice1, choice2) => {
    setCurrentComparison({ choice1, choice2 });
    setIsLoading(true);
    
    // The actual API call will be handled by USMap component
    // We just need to pass the loading state down
  };

  const handleComparisonComplete = () => {
    setIsLoading(false);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Google Trends Electoral Map</h1>
        <p>Compare search trends across US states using Google Trends data</p>
      </header>
      
      <main className="App-main">
        <ComparisonForm 
          onCompare={handleCompare} 
          isLoading={isLoading}
        />
        
        <USMap 
          choice1={currentComparison.choice1}
          choice2={currentComparison.choice2}
          onComparisonComplete={handleComparisonComplete}
          isLoading={isLoading}
        />
      </main>
    </div>
  );
}

export default App;
