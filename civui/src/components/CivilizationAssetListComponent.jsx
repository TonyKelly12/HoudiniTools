import AssetCategoryItem from './AssetCategoryComponent';

const CivilizationAssetCategoryList = ({ 
    categories = [], 
    onAssetClick,
    className = '' 
  }) => {
    return (
      <div className={`civilization-asset-category-list ${className}`}>
        {categories.map((category, index) => (
          <AssetCategoryItem
            key={category.id || index}
            title={category.title}
            assets={category.assets}
            onAssetClick={onAssetClick}
          />
        ))}
      </div>
    );
  };
export default CivilizationAssetCategoryList;