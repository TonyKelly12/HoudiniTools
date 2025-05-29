import Title from '../TitleComponent/TitleComponent';

const AssetCardComponent = ({ 
    asset, 
    isVisible = false, 
    onClose, 
    onDownload,
    className = '' 
  }) => {
    if (!isVisible || !asset) return null;
  
    return (
      <div className={`asset-card-backdrop ${className}`} onClick={onClose}>
        <div className="asset-card" onClick={e => e.stopPropagation()}>
          <button className="close-button" onClick={onClose}>×</button>
          
          <div className="asset-card-content">
            <div className="asset-preview">
              <img src={asset.thumbnail || asset.src} alt={asset.name} />
            </div>
            
            <div className="asset-details">
              <Title level={2}>{asset.name}</Title>
              <p className="asset-description">{asset.description}</p>
              
              <div className="asset-metadata">
                <div className="metadata-item">
                  <strong>Type:</strong> {asset.type}
                </div>
                <div className="metadata-item">
                  <strong>Format:</strong> {asset.format}
                </div>
                <div className="metadata-item">
                  <strong>Size:</strong> {asset.size}
                </div>
                {asset.tags && (
                  <div className="metadata-item">
                    <strong>Tags:</strong> {asset.tags.join(', ')}
                  </div>
                )}
              </div>
              
              <div className="asset-actions">
                <button 
                  className="download-button primary"
                  onClick={() => onDownload && onDownload(asset)}
                >
                  Download Asset
                </button>
                <button 
                  className="preview-button secondary"
                  onClick={() => console.log('Preview asset:', asset)}
                >
                  Preview
                </button>
                <button 
                  className="info-button secondary"
                  onClick={() => console.log('More info:', asset)}
                >
                  More Info
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };
export default AssetCardComponent;