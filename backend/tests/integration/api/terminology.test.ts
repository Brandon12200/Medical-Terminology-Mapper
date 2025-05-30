import request from 'supertest';
import app from '../../../src/index';

describe('Terminology API', () => {
  describe('GET /api/v1/terminology', () => {
    it('should return a list of terminology systems', async () => {
      const response = await request(app)
        .get('/api/v1/terminology')
        .expect(200);
      
      expect(Array.isArray(response.body)).toBe(true);
      expect(response.body.length).toBeGreaterThan(0);
      
      // Check structure of returned systems
      const system = response.body[0];
      expect(system).toHaveProperty('id');
      expect(system).toHaveProperty('name');
      expect(system).toHaveProperty('version');
    });
  });

  describe('GET /api/v1/terminology/:system/code/:code', () => {
    it('should return a term when it exists', async () => {
      const response = await request(app)
        .get('/api/v1/terminology/snomed/code/73211009')
        .expect(200);
      
      expect(response.body).toHaveProperty('code', '73211009');
      expect(response.body).toHaveProperty('display', 'Diabetes mellitus');
      expect(response.body).toHaveProperty('system', 'snomed');
    });

    it('should return 404 when term does not exist', async () => {
      await request(app)
        .get('/api/v1/terminology/snomed/code/non-existent-code')
        .expect(404);
    });
  });
});