import { Term } from './terminology.model';

/**
 * Represents a mapped term between two terminology systems
 */
export interface MappedTerm {
  sourceTerm: Term;
  targetTerm: Term;
  relationship: MappingRelationshipType;
  source: string;
  lastUpdated: string;
}

/**
 * Represents the relationship between two terms in different terminology systems
 */
export interface MappingRelationship {
  sourceSystem: string;
  sourceCode: string;
  targetSystem: string;
  targetCode: string;
  relationship: MappingRelationshipType;
  confidence: number;
  source: string;
  lastUpdated: string;
}

/**
 * Types of relationships between mapped terms
 */
export type MappingRelationshipType = 
  | 'equivalent'    // Terms are equivalent
  | 'broader'       // Source term is broader than target term
  | 'narrower'      // Source term is narrower than target term
  | 'related'       // Terms are related but not equivalent
  | 'not-related';  // Terms are not related