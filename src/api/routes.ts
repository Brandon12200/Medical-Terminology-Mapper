import { Express } from 'express';
import { terminologyRoutes } from './terminology';
import { mappingRoutes } from './mapping';

export function setupRoutes(app: Express): void {
  // Health check endpoint
  app.get('/health', (req, res) => {
    res.status(200).json({ status: 'ok' });
  });
  
  // API routes
  app.use('/api/v1/terminology', terminologyRoutes);
  app.use('/api/v1/mapping', mappingRoutes);
}