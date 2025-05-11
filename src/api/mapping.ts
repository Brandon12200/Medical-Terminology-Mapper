import express, { Request, Response } from 'express';
import { MappingService } from '../services/mapping.service';
import { logger } from '../utils/logger';

const router = express.Router();
const mappingService = new MappingService();

// Map term from source to target terminology
router.post('/translate', async (req: Request, res: Response) => {
  try {
    const { sourceSystem, sourceCode, targetSystem } = req.body;
    
    if (!sourceSystem || !sourceCode || !targetSystem) {
      return res.status(400).json({ 
        error: 'Missing required parameters: sourceSystem, sourceCode, and targetSystem are required'
      });
    }
    
    const mappedTerm = await mappingService.mapTerm(sourceSystem, sourceCode, targetSystem);
    
    if (!mappedTerm) {
      return res.status(404).json({ error: 'No mapping found for this term' });
    }
    
    res.json(mappedTerm);
  } catch (error) {
    logger.error(`Error mapping term: ${error}`);
    res.status(500).json({ error: 'Failed to map terminology' });
  }
});

// Get mapping relationship between terms
router.get('/relationship', async (req: Request, res: Response) => {
  try {
    const { sourceSystem, sourceCode, targetSystem, targetCode } = req.query as Record<string, string>;
    
    if (!sourceSystem || !sourceCode || !targetSystem || !targetCode) {
      return res.status(400).json({ 
        error: 'Missing required parameters: sourceSystem, sourceCode, targetSystem, and targetCode are required'
      });
    }
    
    const relationship = await mappingService.getRelationship(
      sourceSystem, 
      sourceCode, 
      targetSystem, 
      targetCode
    );
    
    if (!relationship) {
      return res.status(404).json({ error: 'No relationship found between these terms' });
    }
    
    res.json(relationship);
  } catch (error) {
    logger.error(`Error getting relationship: ${error}`);
    res.status(500).json({ error: 'Failed to retrieve relationship' });
  }
});

export const mappingRoutes = router;