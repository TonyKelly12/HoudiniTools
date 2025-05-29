import React, { useState } from 'react';
import Thumbnail from '../ThumbnailComponent/ThumbnailComponent';
import ArrowButton from '../ArrowButtonComponent/ArrowButtonComponent';
import './GalleryComponent.css';
const Gallery = ({ 
    items = [], 
    onItemClick, 
    className = '',
    itemsPerView = 3 
  }) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const maxIndex = Math.max(0, items.length - itemsPerView);
  
    const handlePrevious = () => {
      setCurrentIndex(prev => Math.max(0, prev - 1));
    };
  
    const handleNext = () => {
      setCurrentIndex(prev => Math.min(maxIndex, prev + 1));
    };
  
    return (
      <div className={`gallery ${className}`}>
        <ArrowButton 
          direction="left" 
          onClick={handlePrevious}
          disabled={currentIndex === 0}
        />
        
        <div className="gallery-container">
          <div 
            className="gallery-track"
            style={{
              transform: `translateX(-${currentIndex * (100 / itemsPerView)}%)`
            }}
          >
            {items.map((item, index) => (
              <Thumbnail
                key={item.id || index}
                src={item.thumbnail || item.src}
                alt={item.name || item.alt}
                onClick={() => onItemClick && onItemClick(item)}
                className="gallery-item"
              />
            ))}
          </div>
        </div>
        
        <ArrowButton 
          direction="right" 
          onClick={handleNext}
          disabled={currentIndex >= maxIndex}
        />
      </div>
    );
  };
  export default Gallery;