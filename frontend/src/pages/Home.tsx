import { Link } from 'react-router-dom';

export const Home = () => {
  return (
    <div>
      <div className="hero-section">
        <h1 className="hero-title">
          Medical Terminology Mapper
        </h1>
        <p className="hero-subtitle">
          Transform medical terms into standardized terminologies with precision. 
          Supporting SNOMED CT, LOINC, and RxNorm for comprehensive healthcare data mapping.
        </p>
      </div>

      <div className="feature-grid">
        <Link to="/single" className="feature-card">
          <div className="feature-icon">📋</div>
          <h2 className="feature-title">
            Single Term Mapping
          </h2>
          <p className="feature-description">
            Instantly map individual medical terms to standard terminology systems with real-time results.
          </p>
          <span className="feature-link">Get started →</span>
        </Link>

        <Link to="/batch" className="feature-card">
          <div className="feature-icon">📁</div>
          <h2 className="feature-title">
            Batch Processing
          </h2>
          <p className="feature-description">
            Upload CSV files with multiple terms and process them all at once for efficient bulk mapping.
          </p>
          <span className="feature-link">Upload file →</span>
        </Link>
      </div>

      <div className="systems-section">
        <h3 className="systems-title">
          Supported Terminology Systems
        </h3>
        <div className="systems-grid">
          <div className="system-item">
            <h4 className="system-name">SNOMED CT</h4>
            <p className="system-description">Comprehensive clinical terminology for healthcare</p>
          </div>
          <div className="system-item">
            <h4 className="system-name">LOINC</h4>
            <p className="system-description">Universal codes for laboratory and clinical observations</p>
          </div>
          <div className="system-item">
            <h4 className="system-name">RxNorm</h4>
            <p className="system-description">Standardized nomenclature for medications and drugs</p>
          </div>
        </div>
      </div>
    </div>
  );
};