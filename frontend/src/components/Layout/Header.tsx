import { Link, useLocation, useNavigate } from 'react-router-dom';

export const Header = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const handleBatchClick = (e: React.MouseEvent) => {
    e.preventDefault();
    // Force a page reload to ensure state reset
    window.location.href = '/batch';
  };
  
  return (
    <header className="app-header">
      <div className="header-content">
        <Link to="/" className="app-title">
          Medical Terminology Mapper
        </Link>
        <nav className="nav-links">
          <Link to="/single">
            Single Term
          </Link>
          <a href="#" onClick={handleBatchClick}>
            Batch Processing
          </a>
        </nav>
      </div>
    </header>
  );
};