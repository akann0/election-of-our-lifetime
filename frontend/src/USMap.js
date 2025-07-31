import React, { useState, useRef, useEffect } from 'react';
import { ReactComponent as USMapSVG } from './us-map.svg';
import './USMap.css';

const USMap = () => {
  const [stateColors, setStateColors] = useState({});
  const svgRef = useRef(null);

  // Function to update state colors - this will be used for electoral coloring
  const updateStateColor = (stateId, color) => {
    console.log(`Updating color for ${stateId} to ${color}`);
    setStateColors(prev => ({
      ...prev,
      [stateId]: color
    }));
  };

  // Get color for a state, default to light gray if not set
  const getStateColor = (stateId) => {
    return stateColors[stateId] || '#e0e0e0';
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
  }, [stateColors]);

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

  return (
    <div className="us-map-container">
      <h1>Electoral Map</h1>
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
