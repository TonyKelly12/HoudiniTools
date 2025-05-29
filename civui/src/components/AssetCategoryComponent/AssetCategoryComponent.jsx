import Title from '../TitleComponent/TitleComponent';
import Gallery from '../GalleryComponent/GalleryComponent';

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