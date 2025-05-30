# Medical Terminology Mapper - Frontend

A modern React application for mapping medical terms to standardized terminologies.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at http://localhost:5173

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── common/       # Generic components (buttons, alerts, etc.)
│   │   ├── Layout/       # App layout components
│   │   ├── TermMapper/   # Single term mapping components
│   │   └── BatchProcessor/ # Batch processing components
│   ├── pages/            # Route page components
│   ├── services/         # API service layer
│   ├── types/            # TypeScript type definitions
│   ├── utils/            # Utility functions
│   └── App.tsx           # Main application component
├── public/               # Static assets
└── tests/               # Test files
```

## 🎯 Features

### Single Term Mapping
- Real-time medical term search
- Support for multiple terminology systems (SNOMED CT, LOINC, RxNorm)
- Clinical context enhancement
- Adjustable fuzzy matching threshold
- Visual confidence scores with progress bars
- Export results as CSV or JSON

### Batch Processing
- CSV file upload for bulk term processing
- Real-time processing status updates
- Progress tracking with visual indicators
- Download results in multiple formats
- Support for large datasets

### User Experience
- Clean, modern interface with Tailwind CSS
- Responsive design for all screen sizes
- Loading states and error handling
- Intuitive navigation
- Professional data visualization

## 🛠️ Development

### Available Scripts

```bash
# Development server with hot reload
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Run tests with UI
npm run test:ui

# Generate test coverage
npm run test:coverage

# Lint code
npm run lint

# Preview production build
npm run preview
```

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

### Testing

The project uses Vitest for unit testing:

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run specific test file
npm test SingleTermForm.test.tsx
```

Test files are located alongside components with `.test.tsx` extension.

## 🔧 Configuration

### API Integration

The frontend communicates with the backend through a service layer:

```typescript
// src/services/mappingService.ts
- mapTerm(): Map a single medical term
- getSystems(): Get available terminology systems
- processBatch(): Process multiple terms
- uploadFile(): Upload CSV for batch processing
```

### Type Safety

All API responses and component props are fully typed:

```typescript
// src/types/index.ts
- MappingRequest: API request structure
- MappingResponse: API response structure
- BatchJobStatus: Batch processing status
- SystemInfo: Terminology system information
```

## 📦 Dependencies

### Core
- **React 19**: UI library
- **TypeScript**: Type safety
- **Vite**: Build tool and dev server
- **React Router**: Client-side routing

### UI & Styling
- **Tailwind CSS**: Utility-first CSS framework
- **PostCSS**: CSS processing

### Data Management
- **TanStack Query**: Server state management
- **Axios**: HTTP client

### Testing
- **Vitest**: Test runner
- **Testing Library**: Component testing utilities

## 🚢 Deployment

### Docker

Build and run with Docker:

```bash
# Development
docker build -f Dockerfile -t medical-mapper-frontend .
docker run -p 3000:3000 medical-mapper-frontend

# Production
docker build -f Dockerfile.prod -t medical-mapper-frontend:prod .
docker run -p 80:80 medical-mapper-frontend:prod
```

### Static Hosting

Build for production:

```bash
npm run build
```

The `dist/` directory can be served by any static hosting service (Nginx, Apache, Netlify, Vercel).

## 🐛 Troubleshooting

### Common Issues

1. **API Connection Error**
   - Ensure backend is running on http://localhost:8000
   - Check CORS configuration in backend
   - Verify `.env` file exists with correct API URL

2. **Build Errors**
   - Clear node_modules: `rm -rf node_modules && npm install`
   - Clear Vite cache: `rm -rf node_modules/.vite`
   - Ensure Node.js version is 18+

3. **Test Failures**
   - Update test snapshots: `npm test -- -u`
   - Check for async operations in tests
   - Ensure all mocks are properly configured

## 📚 Additional Resources

- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [TanStack Query Docs](https://tanstack.com/query/latest)
- [Vite Guide](https://vitejs.dev/guide/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add your feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Submit a pull request

## 📄 License

This project is part of the Medical Terminology Mapper system.