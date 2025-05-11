import express from 'express';
import dotenv from 'dotenv';
import { setupRoutes } from './api/routes';
import { logger } from './utils/logger';

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());

// Setup API routes
setupRoutes(app);

// Start server
app.listen(PORT, () => {
  logger.info(`Server started on port ${PORT}`);
});

export default app;