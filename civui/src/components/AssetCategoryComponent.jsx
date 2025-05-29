import Title from './titleComponent';
import Gallery from './GalleryComponent';

const AssetCategoryItem = ({ 
    title, 
    assets = [], 
    onAssetClick,
    className = '' 
  }) => {
    return (
      <div className={`asset-category-item ${className}`}>
        <Title level={2} underline={true}>
          {title}
        </Title>
        <Gallery 
          items={assets}
          onItemClick={onAssetClick}
          itemsPerView={3}
        />
      </div>
    );
  };
export default AssetCategoryItem;