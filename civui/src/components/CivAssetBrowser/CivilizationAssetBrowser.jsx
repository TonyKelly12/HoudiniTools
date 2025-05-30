import React, { useState, useEffect } from 'react';
import Title from '../TitleComponent/TitleComponent';
import List from '../ListComponent/ListComponent';
import ListItem from '../ListItemComponent/ListItemComponent';
import AssetCard from '../AssetCardComponent/AssetCardComponent';
import CivilizationAssetCategoryList from '../CivilizationAssetListComponent/CivilizationAssetListComponent';
import './CivilizationAssetBrowser.css';

const CivilizationAssetBrowser = () => {
    const [selectedCivilization, setSelectedCivilization] = useState('Kingdom1');
    const [selectedAsset, setSelectedAsset] = useState(null);
    const [showAssetCard, setShowAssetCard] = useState(false);
  
    // Sample data - replace with your API calls
    const civilizations = [
      { id: 'Kingdom1', name: 'Kingdom1' },
      { id: 'Kingdom2', name: 'Kingdom2' },
      { id: 'Kingdom3', name: 'Kingdom3' }
    ];
  
    const assetCategories = [
      {
        id: 'iconography',
        title: 'Iconography',
        assets: [
          { id: 1, name: 'Icon Set 1', thumbnail: '/mock-api/placeholders/iconographyThumbs/iconography1.png', type: 'Icons', format: 'SVG', size: '2MB' },
          { id: 2, name: 'Icon Set 2', thumbnail: '/mock-api/placeholders/iconographyThumbs/iconography2.png', type: 'Icons', format: 'SVG', size: '1.5MB' },
          { id: 3, name: 'Icon Set 3', thumbnail: '/mock-api/placeholders/iconographyThumbs/iconography3.png', type: 'Icons', format: 'SVG', size: '3MB' },
          { id: 4, name: 'Icon Set 4', thumbnail: '/mock-api/placeholders/iconographyThumbs/iconography4.png', type: 'Icons', format: 'SVG', size: '2.2MB' }
        ]
      },
      {
        id: 'buildings',
        title: 'Buildings',
        assets: [
          { id: 5, name: 'Medieval Castle', thumbnail: '/mock-api/placeholders/buildingThumbs/building1.jpg', type: '3D Model', format: 'FBX', size: '25MB' },
          { id: 6, name: 'Town House', thumbnail: '/mock-api/placeholders/buildingThumbs/building2.jpg', type: '3D Model', format: 'FBX', size: '15MB' },
          { id: 7, name: 'Watchtower', thumbnail: '/mock-api/placeholders/buildingThumbs/building3.jpg', type: '3D Model', format: 'FBX', size: '18MB' },
          { id: 8, name: 'Market Stall', thumbnail: '/mock-api/placeholders/buildingThumbs/building4.jpg', type: '3D Model', format: 'FBX', size: '12MB' }
        ]
      },
      {
        id: 'weapons',
        title: 'Weapons',
        assets: [
          { id: 9, name: 'Medieval Mace', thumbnail: '/mock-api/placeholders/weaponThumbs/weapon1.jpg', type: '3D Model', format: 'FBX', size: '8MB' },
          { id: 10, name: 'Battle Axe', thumbnail: '/mock-api/placeholders/weaponThumbs/weapon2.jpg', type: '3D Model', format: 'FBX', size: '10MB' },
          { id: 11, name: 'Long Sword', thumbnail: '/mock-api/placeholders/weaponThumbs/weapon3.jpg', type: '3D Model', format: 'FBX', size: '7MB' },
          { id: 12, name: 'War Hammer', thumbnail: '/mock-api/placeholders/weaponThumbs/weapon4.jpg', type: '3D Model', format: 'FBX', size: '9MB' }
        ]
      },
      {
        id: 'materials',
        title: 'Materials',
        assets: [
          { id: 13, name: 'Stone Texture', thumbnail: '/mock-api/placeholders/materialThumbs/material1.jpg', type: 'Material', format: 'PNG', size: '4MB' },
          { id: 14, name: 'Wood Grain', thumbnail: '/mock-api/placeholders/materialThumbs/material2.jpg', type: 'Material', format: 'PNG', size: '5MB' },
          { id: 15, name: 'Metal Surface', thumbnail: '/mock-api/placeholders/materialThumbs/material3.jpg', type: 'Material', format: 'PNG', size: '3MB' },
          { id: 16, name: 'Fabric Pattern', thumbnail: '/mock-api/placeholders/materialThumbs/material4.jpg', type: 'Material', format: 'PNG', size: '2MB' }
        ]
      }
    ];
  
    const handleAssetClick = (asset) => {
      setSelectedAsset(asset);
      setShowAssetCard(true);
    };
  
    const handleAssetDownload = (asset) => {
      // Implement download logic
      console.log('Downloading asset:', asset);
      alert(`Downloading ${asset.name}...`);
    };
  
    return (
      <div className="civilization-asset-browser">
        {/* Left Sidebar */}
        <div className="sidebar">
          <Title level={1} underline={true}>Civilizations</Title>
          <List direction="vertical" className="civilization-list">
            {civilizations.map(civ => (
              <ListItem
                key={civ.id}
                isActive={selectedCivilization === civ.id}
                onClick={() => setSelectedCivilization(civ.id)}
              >
                {civ.name}
              </ListItem>
            ))}
          </List>
        </div>
  
        {/* Main Content */}
        <div className="main-content">
          <Title level={1} underline={true} className="civilization-title">
            {selectedCivilization}
          </Title>
          
          <CivilizationAssetCategoryList
            categories={assetCategories}
            onAssetClick={handleAssetClick}
          />
        </div>
  
        {/* Asset Card Modal */}
        <AssetCard
          asset={selectedAsset}
          isVisible={showAssetCard}
          onClose={() => setShowAssetCard(false)}
          onDownload={handleAssetDownload}
        />
      </div>
    );
  };
  
  export default CivilizationAssetBrowser;