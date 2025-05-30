import { MappingService } from '../../../src/services/mapping.service';

describe('MappingService', () => {
  let service: MappingService;

  beforeEach(() => {
    service = new MappingService();
  });

  describe('mapTerm', () => {
    it('should return a mapped term when mapping exists', async () => {
      const mappedTerm = await service.mapTerm('snomed', '73211009', 'icd10');
      
      expect(mappedTerm).toBeDefined();
      expect(mappedTerm?.sourceTerm.code).toBe('73211009');
      expect(mappedTerm?.sourceTerm.system).toBe('snomed');
      expect(mappedTerm?.targetTerm.system).toBe('icd10');
      expect(mappedTerm?.relationship).toBeDefined();
    });

    it('should return null when no mapping exists', async () => {
      const mappedTerm = await service.mapTerm('snomed', 'non-existent-code', 'icd10');
      expect(mappedTerm).toBeNull();
    });
  });

  describe('getRelationship', () => {
    it('should return relationship when it exists', async () => {
      const relationship = await service.getRelationship(
        'snomed', 
        '73211009', 
        'icd10', 
        'E11'
      );
      
      expect(relationship).toBeDefined();
      expect(relationship?.sourceSystem).toBe('snomed');
      expect(relationship?.sourceCode).toBe('73211009');
      expect(relationship?.targetSystem).toBe('icd10');
      expect(relationship?.targetCode).toBe('E11');
      expect(relationship?.relationship).toBeDefined();
      expect(relationship?.confidence).toBeGreaterThan(0);
    });

    it('should return null when relationship does not exist', async () => {
      const relationship = await service.getRelationship(
        'snomed', 
        'non-existent-code', 
        'icd10', 
        'non-existent-code'
      );
      
      expect(relationship).toBeNull();
    });
  });
});