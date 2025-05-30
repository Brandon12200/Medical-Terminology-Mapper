import { Link } from 'react-router-dom';

export const Header = () => {
  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link to="/" className="text-xl font-semibold text-gray-900">
              Medical Terminology Mapper
            </Link>
          </div>
          <nav className="flex space-x-8">
            <Link 
              to="/single" 
              className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium"
            >
              Single Term
            </Link>
            <Link 
              to="/batch" 
              className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium"
            >
              Batch Processing
            </Link>
            {/* <Link 
              to="/ai-extraction" 
              className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium"
            >
              AI Extraction
            </Link> */}
          </nav>
        </div>
      </div>
    </header>
  );
};