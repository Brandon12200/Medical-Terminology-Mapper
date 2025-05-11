import express, { Request, Response } from 'express';
import { TerminologyService } from '../services/terminology.service';
import { logger } from '../utils/logger';

const router = express.Router();
const terminologyService = new TerminologyService();

// Get all terminology systems
router.get('/', async (req: Request, res: Response) => {
  try {
    const systems = await terminologyService.getAllSystems();
    res.json(systems);
  } catch (error) {
    logger.error(`Error getting terminology systems: ${error}`);
    res.status(500).json({ error: 'Failed to retrieve terminology systems' });
  }
});

// Get specific term by code from a terminology system
router.get('/:system/code/:code', async (req: Request, res: Response) => {
  try {
    const { system, code } = req.params;
    const term = await terminologyService.getTermByCode(system, code);
    
    if (!term) {
      return res.status(404).json({ error: 'Term not found' });
    }
    
    res.json(term);
  } catch (error) {
    logger.error(`Error getting term: ${error}`);
    res.status(500).json({ error: 'Failed to retrieve term' });
  }
});

export const terminologyRoutes = router;