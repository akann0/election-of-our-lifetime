import React, { useState } from 'react';
import USMap from './USMap';
import ComparisonForm from './ComparisonForm';
import './App.css';

function App() {
  const [currentComparison, setCurrentComparison] = useState({ choice1: '', choice2: '' });
  const [isLoading, setIsLoading] = useState(false);
  const [formOpen, setFormOpen] = useState(false);

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
        <h1 className="election-title">The United States of America<br/>2024 National Search Sentiment Election</h1>
        <p className="election-subtitle">Welcome to the most consequential, statistically dubious, and algorithmically determined election in American history.<br/>Cast your queries. The fate of the nation (and your search terms) hangs in the balance.</p>
      </header>
      <main className="App-main">
        <div className={`comparison-form-collapsible${formOpen ? ' open' : ''}`} style={{ width: '100%', maxWidth: '100%', margin: '0 auto', marginBottom: 16 }}>
          <button 
            className="toggle-form-btn ballot-toggle-btn" 
            onClick={() => setFormOpen(open => !open)}
            style={{ width: 'auto', minWidth: 'fit-content', padding: '10px 32px', fontWeight: 'bold', fontSize: '1.1em', borderRadius: 6, marginBottom: 4, display: 'block', marginLeft: 'auto', marginRight: 'auto' }}
          >
            {formOpen ? 'Hide Ballot' : 'Show Ballot'}
          </button>
          {formOpen && (
            <div style={{ transition: 'max-height 0.3s', overflow: 'hidden' }}>
              <ComparisonForm 
                onCompare={handleCompare} 
                isLoading={isLoading}
                small
              />
            </div>
          )}
        </div>
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
