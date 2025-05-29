import './ListComponent.css';
const ListComponent = ({ children, className = '', direction = 'vertical' }) => {
    return (
      <div className={`list ${direction} ${className}`}>
        {children}
      </div>
    );
  };
  export default ListComponent;