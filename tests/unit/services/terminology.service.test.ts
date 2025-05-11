import { TerminologyService } from '../../../src/services/terminology.service';

describe('TerminologyService', () => {
  let service: TerminologyService;

  beforeEach(() => {
    service = new TerminologyService();
  });

  describe('getAllSystems', () => {
    it('should return a list of terminology systems', async () => {
      const systems = await service.getAllSystems();
      
      expect(systems).toBeDefined();
      expect(Array.isArray(systems)).toBe(true);
      expect(systems.length).toBeGreaterThan(0);
      
      // Check that systems have the expected structure
      const system = systems[0];
      expect(system).toHaveProperty('id');
      expect(system).toHaveProperty('name');
      expect(system).toHaveProperty('version');
    });
  });

  describe('getTermByCode', () => {
    it('should return a term when it exists', async () => {
      const term = await service.getTermByCode('snomed', '73211009');
      
      expect(term).toBeDefined();
      expect(term?.code).toBe('73211009');
      expect(term?.display).toBe('Diabetes mellitus');
      expect(term?.system).toBe('snomed');
    });

    it('should return null when term does not exist', async () => {
      const term = await service.getTermByCode('snomed', 'non-existent-code');
      expect(term).toBeNull();
    });
  });

  describe('searchTerms', () => {
    it('should return matching terms when query matches', async () => {
      const terms = await service.searchTerms('snomed', 'diabetes');
      
      expect(terms).toBeDefined();
      expect(Array.isArray(terms)).toBe(true);
      expect(terms.length).toBeGreaterThan(0);
      
      // Check that returned terms include 'diabetes' in their display
      for (const term of terms) {
        expect(term.display.toLowerCase()).toContain('diabetes');
      }
    });

    it('should return empty array when no matches found', async () => {
      const terms = await service.searchTerms('snomed', 'xyz123nonexistent');
      
      expect(terms).toBeDefined();
      expect(Array.isArray(terms)).toBe(true);
      expect(terms.length).toBe(0);
    });
  });
});