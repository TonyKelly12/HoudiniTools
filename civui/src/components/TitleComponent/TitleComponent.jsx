import './TitleComponent.css';
const TitleComponent = ({ 
  children, 
  level = 1, 
  className = '',
  underline = false 
}) => {
  const Tag = `h${level}`;
  return (
    <Tag className={`title ${underline ? 'underlined' : ''} ${className}`}>
      {children}
    </Tag>
  );
};
export default TitleComponent;