// ArtistInterface/src/components/CivilizationSelector.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';


const CivilizationSelector = () => {
  const [civilizations, setCivilizations] = useState([]);
  const [selectedCiv, setSelectedCiv] = useState(null);
  const [context, setContext] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCivilizations();
  }, []);

  const fetchCivilizations = async () => {
    try {
      const response = await axios.get('http://localhost:8000/civilizations/');
      setCivilizations(response.data.civilizations);
    } catch (error) {
      console.error('Failed to fetch civilizations:', error);
    }
  };

  const selectCivilization = async (civ) => {
    setSelectedCiv(civ);
    setLoading(true);
    
    try {
      const response = await axios.post('http://localhost:8001/context/analyze', {
        civilization_id: civ.id,
        generator_type: 'weapon'
      });
      setContext(response.data);
    } catch (error) {
      console.error('Failed to get context:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateWeapon = async () => {
    if (!selectedCiv) return;
    
    // Send civilization ID to Houdini HDA
    // This could be done via HTTP to a Houdini Web Server
    // or by writing to a shared file/database
    
    alert(`Generating weapon for ${selectedCiv.metadata.name}...`);
  };

  return (
    <div className="civilization-selector">
      <h2>Select Civilization for Asset Generation</h2>
      
      <div className="civilization-grid">
        {civilizations.map(civ => (
          <div 
            key={civ.id} 
            className={`civ-card ${selectedCiv?.id === civ.id ? 'selected' : ''}`}
            onClick={() => selectCivilization(civ)}
          >
            <h3>{civ.metadata.name}</h3>
            <p>{civ.metadata.description}</p>
            <div className="civ-tags">
              <span className="tag gov">{civ.metadata.government_type}</span>
              <span className="tag tech">{civ.metadata.technology_level}</span>
              <span className="tag culture">{civ.metadata.cultural_values}</span>
            </div>
          </div>
        ))}
      </div>

      {loading && <div className="loading">Analyzing civilization...</div>}

      {context && (
        <div className="context-display">
          <h3>Generation Context for {selectedCiv.metadata.name}</h3>
          
          <div className="style-guide">
            <h4>Style Guide</h4>
            <div className="themes">
              <strong>Visual Themes: </strong>
              {context.style_guide.visual_themes.join(', ')}
            </div>
            <div className="materials">
              <strong>Recommended Materials: </strong>
              {context.style_guide.materials.join(', ')}
            </div>
            <div className="colors">
              <strong>Color Palette: </strong>
              <div className="color-swatches">
                {context.style_guide.color_palette.map(color => (
                  <div 
                    key={color} 
                    className="color-swatch" 
                    style={{backgroundColor: color}}
                    title={color}
                  />
                ))}
              </div>
            </div>
          </div>

          <div className="asset-recommendations">
            <h4>Recommended Assets ({context.asset_recommendations.length})</h4>
            <div className="asset-grid">
              {context.asset_recommendations.slice(0, 6).map(asset => (
                <div key={asset.asset_id} className="asset-card">
                  <div className="asset-preview">
                    {/* Asset preview would go here */}
                    <div className="placeholder-preview">Preview</div>
                  </div>
                  <div className="asset-info">
                    <div className="compatibility-score">
                      {Math.round(asset.compatibility_score * 100)}% match
                    </div>
                    <div className="asset-reasons">
                      {asset.reasons.join(', ')}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <button onClick={generateWeapon} className="generate-btn">
            Generate Weapon for {selectedCiv.metadata.name}
          </button>
        </div>
      )}
    </div>
  );
};

export default CivilizationSelector;