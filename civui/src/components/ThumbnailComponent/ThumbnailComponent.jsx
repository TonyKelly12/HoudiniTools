import './ThumbnailComponent.css';
const ThumbnailComponent = ({ 
    src, 
    alt, 
    onClick, 
    className = '',
    type = 'image' 
  }) => {
    return (
      <div 
        className={`thumbnail ${type} ${className}`}
        onClick={onClick}
      >
        <img src={src} alt={alt} />
        <div className="thumbnail-overlay">
          <span>Click to view</span>
        </div>
      </div>
    );
  };
export default ThumbnailComponent;