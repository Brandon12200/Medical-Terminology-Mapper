# Medical Terminology Mapper

A comprehensive platform that maps medical terminology across healthcare standards including SNOMED CT, ICD-10, RxNorm, and LOINC.

## Overview

Medical Terminology Mapper addresses the critical healthcare interoperability challenge of inconsistent terminology usage across different systems and standards. The platform intelligently identifies medical terms and maps them to standardized terminologies while providing a robust API for seamless integration.

## Key Features

- **Comprehensive Terminology Support**: Maps between SNOMED CT, ICD-10, LOINC, and RxNorm
- **Relationship Awareness**: Understands relationships between terms (equivalent, broader, narrower)
- **Confidence Scoring**: Provides match confidence metrics for all mappings
- **Robust API**: Well-documented REST API for integration into clinical workflows
- **Comprehensive Audit Trail**: Tracks all mapping decisions and changes

## Technical Stack

- **Backend**: Node.js with Express framework
- **Database**: Not yet implemented (will use MongoDB or PostgreSQL)
- **TypeScript**: For type safety and better code organization
- **Jest**: For comprehensive testing
- **Winston**: For structured logging

## Project Structure

```
medical-terminology-mapper/
├── src/                      # Source code
│   ├── api/                  # API routes and controllers
│   ├── services/             # Business logic and services
│   ├── models/               # Data models
│   ├── utils/                # Utility functions
│   └── index.ts              # Application entry point
├── tests/                    # Test files
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── dist/                     # Compiled JavaScript files
├── .gitignore                # Git ignore file
├── package.json              # Node.js package file
├── tsconfig.json             # TypeScript configuration
└── jest.config.js            # Jest configuration
```

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/medical-terminology-mapper.git
cd medical-terminology-mapper

# Install dependencies
npm install

# Run in development mode
npm run dev

# Build the project
npm run build

# Start the production server
npm start
```

## Testing

```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

## API Usage

### Get all terminology systems

```
GET /api/v1/terminology
```

### Get term details

```
GET /api/v1/terminology/:system/code/:code
```

### Map a term from one system to another

```
POST /api/v1/mapping/translate
{
  "sourceSystem": "snomed",
  "sourceCode": "73211009",
  "targetSystem": "icd10"
}
```

### Get relationship between terms

```
GET /api/v1/mapping/relationship?sourceSystem=snomed&sourceCode=73211009&targetSystem=icd10&targetCode=E11
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
