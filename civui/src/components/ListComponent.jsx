import './listComponent.css';

const List = ({ children, className = '', direction = 'vertical' }) => {
    return (
      <div className={`list ${direction} ${className}`}>
        {children}
      </div>
    );
  };
  export default List;