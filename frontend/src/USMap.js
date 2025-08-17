import React, { useState, useRef, useEffect } from 'react';
import { ReactComponent as USMapSVG } from './us-map.svg';
import ElectionService from './ElectionService';
import './USMap.css';

const ElectoralCollege = new Map([
  ['AL', 9], ['AK', 3], ['AZ', 11], ['AR', 6], ['CA', 54],
  ['CO', 10], ['CT', 7], ['DE', 3], ['FL', 30], ['GA', 16],
  ['HI', 4], ['ID', 4], ['IL', 19], ['IN', 11], ['IA', 6],
  ['KS', 6], ['KY', 8], ['LA', 8], ['ME', 4], ['MD', 10],
  ['MA', 11], ['MI', 15], ['MN', 10], ['MS', 6], ['MO', 10],
  ['MT', 4], ['NE', 5], ['NV', 6], ['NH', 4], ['NJ', 14],
  ['NM', 5], ['NY', 28], ['NC', 16], ['ND', 3], ['OH', 17],
  ['OK', 7], ['OR', 8], ['PA', 19], ['RI', 4], ['SC', 9],
  ['SD', 3], ['TN', 11], ['TX', 40], ['UT', 6], ['VA', 13],
  ['VT', 3], ['WA', 12], ['WI', 10], ['WV', 4], ['WY', 3],
  ['DC', 3]
]);

// Helper to convert -1 to 1 sentiment to 0-100% (50% = neutral)
function sentimentToPercent(score) {
  return (score + 1) * 50;
}

const loadingMessages = [
  'Counting ballots in swing states...',
  'Choosing a vice president...',
  'Doing debate prep...',
  'Shaking hands with voters...',
  'Polling the Electoral College...',
  'Running negative ads...',
  'Consulting the pundits...',
  'Making last-minute campaign stops...',
  'Checking the exit polls...',
  'Calling the networks...'
];

const USMap = ({ choice1, choice2, onComparisonComplete, isLoading: parentIsLoading }) => {
  const [scoreboard, setScoreboard] = useState([0, 0]); // [Red, Blue]
  const [stateColors, setStateColors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [currentComparison, setCurrentComparison] = useState('');
  const [loadingMsgIdx, setLoadingMsgIdx] = useState(0);
  const svgRef = useRef(null);
  // Add state to hold the breakdown display
  const [showFurtherBreakdown, setShowFurtherBreakdown] = useState(false);
  const [nationalDemographicData, setNationalDemographicData] = useState({});
  const [analysisData, setAnalysisData] = useState({});

  // Function to update state colors - this will be used for electoral coloring
  const updateStateColor = (stateId, color) => {
    setStateColors(prev => ({
      ...prev,
      [stateId]: color
    }));
  };

  // Get color for a state, default to light gray if not set
  const getStateColor = (stateId) => {
    return stateColors[stateId] || '#e0e0e0';
  };

  const updateScoreboard = (colors) => {
    let redTotal = 0;
    let blueTotal = 0;

    Object.entries(colors).forEach(([stateId, color]) => {
      const electoralVotes = ElectoralCollege.get(stateId);
      if (electoralVotes) {
        if (color === '#F44336') { // Red
          redTotal += electoralVotes;
        } else if (color === '#2196F3') { // Blue
          blueTotal += electoralVotes;
        }
      }
    });

    setScoreboard([redTotal, blueTotal]);
  };

  // Apply fills whenever colors change
  useEffect(() => {
    if (!svgRef.current) return;
    console.log("Applying colors to SVG paths");
    const paths = svgRef.current.querySelectorAll("path[id]");
    paths.forEach((p) => {
      const id = p.id.toUpperCase();
      console.log(`Setting color for ${id}: ${getStateColor(id)}`);
      if (stateColors[id]) {
        p.setAttribute("style", `fill: ${stateColors[id]}; stroke: black; stroke-width: 1.5px`);
      } else {
        console.log(`No color set for ${id}, defaulting to light gray`);
        p.setAttribute("style", "fill: rgb(249,249,249); stroke: black; stroke-width: 1.5px");
      }
    });
    // Update scoreboard based on current state colors
    updateScoreboard(stateColors);
  }, [stateColors]);

  // Handle comparison when choice1 and choice2 change
  useEffect(() => {
    if (choice1 && choice2 && choice1 !== choice2) {
      const comparison = `${choice1} vs ${choice2}`;
      if (comparison !== currentComparison) {
        setCurrentComparison(comparison);
        handleRunComparison(choice1, choice2);
      }
    }
  }, [choice1, choice2]);

  const isCurrentlyLoading = isLoading || parentIsLoading;

  // Rotate loading messages while loading
  useEffect(() => {
    if (isCurrentlyLoading) {
      setLoadingMsgIdx(0);
      const interval = setInterval(() => {
        setLoadingMsgIdx(idx => (idx + 1) % loadingMessages.length);
      }, 1200);
      return () => clearInterval(interval);
    }
  }, [isCurrentlyLoading]);

  const handleStateClick = (stateId) => {
    // Cycle through colors: gray -> red -> blue -> gray
    console.log(`State clicked: ${stateId}`);
    console.log(`Current color: ${getStateColor(stateId)}`);
    const currentColor = getStateColor(stateId);
    let newColor;
    if (currentColor === '#e0e0e0') {
      newColor = '#F44336'; // Red
    } else if (currentColor === '#F44336') {
      newColor = '#2196F3'; // Blue
    } else {
      newColor = '#e0e0e0'; // Gray
    }
    updateStateColor(stateId, newColor);
  };

  // Handle running the comparison with user-provided choices
  const handleRunComparison = async (choice1, choice2) => {
    setIsLoading(true);
    try {
      console.log(`Comparing ${choice1} vs ${choice2} with combined analysis...`);
      const comparisonResults = await ElectionService.compareChoices(choice1, choice2);
      console.log('Received comparison results:', comparisonResults);
      setStateColors(comparisonResults.state_colors);
      
      // Extract US national demographic data directly from the response
      const nationalData = comparisonResults.national_demographic_vote_splits?.US || 
                          comparisonResults.demographic_vote_splits?.US || {};
      
      console.log('National demographic data:', nationalData);
      console.log('Full comparison results:', comparisonResults);
      
      setNationalDemographicData(nationalData);
      setAnalysisData(comparisonResults);
      
      // You can also access the detailed analysis data if needed:
      // console.log('Trends data:', comparisonResults.trends_data);
      // console.log('Sentiment data:', comparisonResults.sentiment_data);
      // console.log('Analysis summary:', comparisonResults.analysis_summary);
      
    } catch (error) {
      console.error('Error comparing choices:', error);
    } finally {
      setIsLoading(false);
      if (onComparisonComplete) {
        onComparisonComplete();
      }
    }
  };

  // Legacy function for random colors (kept for backward compatibility)
  const handleRunRandomColors = async () => {
    setIsLoading(true);
    try {
      console.log('Generating random colors from backend...');
      const randomColors = await ElectionService.generateRandomColors();
      console.log('Received random colors:', randomColors);
      setStateColors(randomColors);
    } catch (error) {
      console.error('Error generating random colors:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Order demographics: conservative, center-right, moderate, center-left, liberal
  const demographicOrder = [
    'conservative',
    'moderate',
    'liberal'
  ];

  return (
    <div className="us-map-container">
      <div className="us-map-header">
        <h1>Electoral Map</h1>
        {currentComparison && (
          <div className="current-comparison">
            <h2>Comparing: {currentComparison}</h2>
            <div className="comparison-legend">
              <span className="legend-item">
                <span className="legend-color red"></span>
                {choice1}
              </span>
              <span className="legend-item">
                <span className="legend-color blue"></span>
                {choice2}
              </span>
            </div>
          </div>
        )}
      </div>
      
      <div className="us-map-scoreboard">
        <div className="scoreboard-header">
          <h2>Electoral Votes</h2>
          <div className="scoreboard-controls">
            <div className="scoreboard-totals">
              <span className="red-total">{choice1 || 'Red'}: {scoreboard[0]}</span>
              <span className="blue-total">{choice2 || 'Blue'}: {scoreboard[1]}</span>
            </div>
            {!currentComparison && (
              <button 
                className="run-button" 
                onClick={handleRunRandomColors}
                disabled={isCurrentlyLoading}
              >
                {isCurrentlyLoading ? 'Running...' : 'Run Random Colors'}
              </button>
            )}
          </div>
        </div>
        <div className="scoreboard-bar-container">
          <div className="scoreboard-bar">
            <div 
              className="red-bar" 
              style={{ width: `${(scoreboard[0] / 538) * 100}%` }}
            >
              {scoreboard[0] > 0 && <span className="bar-label">{scoreboard[0]}</span>}
            </div>
            <div 
              className="blue-bar" 
              style={{ width: `${(scoreboard[1] / 538) * 100}%` }}
            >
              {scoreboard[1] > 0 && <span className="bar-label">{scoreboard[1]}</span>}
            </div>
            <div className="fifty-percent-line"></div>
          </div>
        </div>
        {/* National Popular Vote */}
        {nationalDemographicData && Object.keys(nationalDemographicData).length > 0 && (
        <div className="demographic-bars">
          <div className="demographic-label">{"National Popular Vote"}</div>
          <div className="demographic-bar-container" style={{ display: 'flex', width: '100%', height: '24px', background: '#eee', borderRadius: '6px', overflow: 'hidden', margin: '6px 0' }}>
            <div className="demographic-bar red" style={{ width: `${nationalDemographicData.overall[choice1]}%`, background: '#F44336', color: nationalDemographicData.overall[choice1] > 15 ? '#fff' : '#000', display: 'flex', alignItems: 'center', justifyContent: nationalDemographicData.overall[choice1] > 15 ? 'center' : 'flex-start', fontWeight: 'bold', fontSize: '0.95em' }}>
              {nationalDemographicData.overall[choice1] >= 10 ? `${nationalDemographicData.overall[choice1].toFixed(1)}%` : ''}
            </div>
            <div className="demographic-bar blue" style={{ width: `${nationalDemographicData.overall[choice2]}%`, background: '#2196F3', color: nationalDemographicData.overall[choice2] > 15 ? '#fff' : '#000', display: 'flex', alignItems: 'center', justifyContent: nationalDemographicData.overall[choice2] > 15 ? 'center' : 'flex-end', fontWeight: 'bold', fontSize: '0.95em' }}>
              {nationalDemographicData.overall[choice2] >= 10 ? `${nationalDemographicData.overall[choice2].toFixed(1)}%` : ''}
            </div>
          </div>
        </div>
        )}
      </div>
      
      {isCurrentlyLoading && (
        <div className="loading-overlay" style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(30, 30, 50, 0.98)',
          zIndex: 10,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: '1.3em',
          fontWeight: 'bold',
          letterSpacing: '0.01em',
          textShadow: '0 2px 8px #000',
        }}>
          <div className="loading-spinner" style={{ marginBottom: 24 }}></div>
          <p style={{ marginBottom: 8 }}>Election in progress...</p>
          <p style={{ fontSize: '1.1em', fontWeight: 400, fontStyle: 'italic' }}>{loadingMessages[loadingMsgIdx]}</p>
        </div>
      )}
      
      <div className="us-map-svg">
        <USMapSVG 
          ref={svgRef}
          style={{ width: '100%', height: 'auto' }}
          onClick={(e) => {
            const stateId = e.target.id;
            if (stateId && stateId.length === 2) {
              handleStateClick(stateId);
            }
          }}
        />
      </div>
      {/* Analysis Breakdown */}
      {nationalDemographicData && Object.keys(nationalDemographicData).length > 0 && (
        <div className="analysis-breakdown">
          <div className="breakdown-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ margin: 0 }}>National Demographic Vote Breakdown</h3>
            <button 
              className="further-breakdown-toggle"
              onClick={() => setShowFurtherBreakdown(!showFurtherBreakdown)}
              style={{
                padding: '8px 16px',
                backgroundColor: showFurtherBreakdown ? '#2196F3' : '#f0f0f0',
                color: showFurtherBreakdown ? 'white' : '#333',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 'bold',
                transition: 'all 0.2s ease'
              }}
            >
              {showFurtherBreakdown ? 'Hide' : 'Show'} Further Breakdown
            </button>
          </div>
          
          {/* Basic Demographic Bars */}
          <div className="demographic-bars">
            {demographicOrder
              .filter(demo => nationalDemographicData[demo])
              .map((demo) => {
                const percent1 = nationalDemographicData[demo][choice1] || 0;
                const percent2 = nationalDemographicData[demo][choice2] || 0;
                
                return (
                  <div className="demographic-bar-row" key={demo}>
                    <div className="demographic-label">{demo.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}</div>
                    <div className="demographic-bar-container" style={{ display: 'flex', width: '100%', height: '24px', background: '#eee', borderRadius: '6px', overflow: 'hidden', margin: '6px 0' }}>
                      <div className="demographic-bar red" style={{ width: `${percent1}%`, background: '#F44336', color: percent1 > 15 ? '#fff' : '#000', display: 'flex', alignItems: 'center', justifyContent: percent1 > 15 ? 'center' : 'flex-start', fontWeight: 'bold', fontSize: '0.95em' }}>
                        {percent1 >= 10 ? `${percent1.toFixed(1)}%` : ''}
                      </div>
                      <div className="demographic-bar blue" style={{ width: `${percent2}%`, background: '#2196F3', color: percent2 > 15 ? '#fff' : '#000', display: 'flex', alignItems: 'center', justifyContent: percent2 > 15 ? 'center' : 'flex-end', fontWeight: 'bold', fontSize: '0.95em' }}>
                        {percent2 >= 10 ? `${percent2.toFixed(1)}%` : ''}
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>

          {/* Further Breakdown Section */}
          {showFurtherBreakdown && analysisData && (
            <div className="further-breakdown" style={{ marginTop: '20px', padding: '16px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <h4 style={{ marginBottom: '16px', color: '#333' }}>Detailed Analysis Components</h4>
              
              {/* Google Trends Data */}
              {analysisData.search_data && (
                <div className="breakdown-section" style={{ marginBottom: '16px' }}>
                  <h5 style={{ color: '#2196F3', marginBottom: '8px' }}>🔍 Google Search Volume</h5>
                  <div style={{ fontSize: '0.9em', color: '#666' }}>
                    <p><strong>Winner:</strong> {analysisData.search_data.winner || 'No clear winner'}</p>
                    <p><strong>Electoral Votes:</strong> {JSON.stringify(analysisData.electoral_tally || {})}</p>
                    
                    {/* US Weighted Average Score */}
                    {analysisData.search_data.state_scores?.US && (
                      <div style={{ marginTop: '12px', padding: '8px', backgroundColor: '#e3f2fd', borderRadius: '4px' }}>
                        <p style={{ margin: '0 0 4px 0', fontWeight: 'bold', color: '#1976d2' }}>US Weighted Average (by Electoral Votes):</p>
                        <div style={{ display: 'flex', gap: '16px', fontSize: '0.85em' }}>
                          <span><strong>{choice1}:</strong> {analysisData.search_data.state_scores.US[choice1]}</span>
                          <span><strong>{choice2}:</strong> {analysisData.search_data.state_scores.US[choice2]}</span>
                          <span style={{ color: '#666' }}>
                            <strong>Margin:</strong> {analysisData.search_data.state_scores.US.margin}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Sentiment Analysis Data */}
              {analysisData.sentiment_summary && (
                <div className="breakdown-section" style={{ marginBottom: '16px' }}>
                  <h5 style={{ color: '#FF9800', marginBottom: '8px' }}>💭 Sentiment Analysis</h5>
                  <div style={{ fontSize: '0.9em', color: '#666' }}>
                    {analysisData.sentiment_summary.sentiment_data?.sentiment_scores && (
                      <div>
                        <p><strong>{choice1}:</strong> {(analysisData.sentiment_summary.sentiment_data.sentiment_scores[choice1] * 100).toFixed(1)}% positive</p>
                        <p><strong>{choice2}:</strong> {(analysisData.sentiment_summary.sentiment_data.sentiment_scores[choice2] * 100).toFixed(1)}% positive</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* DSA Demographic Similarity */}
              {analysisData.dsa_results && (
                <div className="breakdown-section">
                  <h5 style={{ color: '#9C27B0', marginBottom: '8px' }}>🎯 Demographic Similarity Analysis</h5>
                  <div style={{ fontSize: '0.9em', color: '#666' }}>
                    {analysisData.dsa_results.demographic_preferences && (
                      <div>
                        {Object.entries(analysisData.dsa_results.demographic_preferences).map(([demo, pref]) => (
                          <p key={demo}>
                            <strong>{demo}:</strong> Prefers {pref.preferred_choice} 
                            (margin: {(pref.margin * 100).toFixed(1)}%, confidence: {pref.confidence})
                          </p>
                        ))}
                      </div>
                    )}
                    <p style={{ marginTop: '8px', fontStyle: 'italic' }}>
                      Method: {analysisData.dsa_results.embedding_method || 'Unknown'}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default USMap;
