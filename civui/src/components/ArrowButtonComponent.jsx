const ArrowButton = ({ 
  direction = 'left', 
  onClick, 
  disabled = false,
  className = ''
}) => {
  return (
    <button 
      className={`arrow-button ${direction} ${disabled ? 'disabled' : ''} ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {direction === 'left' ? '◀' : '▶'}
    </button>
  );
};
export default ArrowButton;