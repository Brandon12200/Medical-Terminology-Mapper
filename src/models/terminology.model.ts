/**
 * Represents a medical terminology system
 */
export interface TerminologySystem {
  id: string;
  name: string;
  version: string;
  description?: string;
}

/**
 * Represents a term within a terminology system
 */
export interface Term {
  code: string;
  display: string;
  system: string;
  properties?: Record<string, any>;
  parents?: string[];
  children?: string[];
}