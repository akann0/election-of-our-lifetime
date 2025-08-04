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

const USMap = ({ choice1, choice2, onComparisonComplete, isLoading: parentIsLoading }) => {
  const [scoreboard, setScoreboard] = useState([0, 0]); // [Red, Blue]
  const [stateColors, setStateColors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [currentComparison, setCurrentComparison] = useState('');
  const svgRef = useRef(null);

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

  const isCurrentlyLoading = isLoading || parentIsLoading;

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
      </div>
      
      {isCurrentlyLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>Loading comparison data...</p>
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
    </div>
  );
};

export default USMap;
