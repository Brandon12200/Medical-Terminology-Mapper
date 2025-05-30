import { Link } from 'react-router-dom';

export const Home = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Medical Terminology Mapper
        </h1>
        <p className="text-lg text-gray-600">
          Map medical terms to standardized terminologies including SNOMED CT, LOINC, and RxNorm
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        <Link
          to="/single"
          className="bg-white p-8 rounded-lg shadow hover:shadow-lg transition-shadow"
        >
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Single Term Mapping
          </h2>
          <p className="text-gray-600 mb-4">
            Enter a single medical term and get instant mappings to standard terminology systems.
          </p>
          <span className="text-blue-600 font-medium">Get started →</span>
        </Link>

        <Link
          to="/batch"
          className="bg-white p-8 rounded-lg shadow hover:shadow-lg transition-shadow"
        >
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Batch Processing
          </h2>
          <p className="text-gray-600 mb-4">
            Upload a CSV file with multiple terms and process them all at once.
          </p>
          <span className="text-blue-600 font-medium">Upload file →</span>
        </Link>

        {/* <Link
          to="/ai-extraction"
          className="bg-white p-8 rounded-lg shadow hover:shadow-lg transition-shadow border-2 border-purple-100"
        >
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            AI Term Extraction
          </h2>
          <p className="text-gray-600 mb-4">
            Extract medical terms from clinical text using BioBERT AI model.
          </p>
          <span className="text-purple-600 font-medium">Try AI →</span>
        </Link> */}
      </div>

      <div className="mt-12 bg-blue-50 p-6 rounded-lg">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Supported Terminology Systems
        </h3>
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div>
            <h4 className="font-medium text-gray-900">SNOMED CT</h4>
            <p className="text-sm text-gray-600">Clinical terminology</p>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">LOINC</h4>
            <p className="text-sm text-gray-600">Laboratory observations</p>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">RxNorm</h4>
            <p className="text-sm text-gray-600">Medications and drugs</p>
          </div>
        </div>
      </div>
    </div>
  );
};