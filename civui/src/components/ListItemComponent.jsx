import './listItemComponent.css';

const ListItem = ({ 
    children, 
    isActive = false, 
    onClick, 
    className = '' 
  }) => {
    return (
      <div 
        className={`list-item ${isActive ? 'active' : ''} ${className}`}
        onClick={onClick}
      >
        {children}
      </div>
    );
  };
  export default ListItem;