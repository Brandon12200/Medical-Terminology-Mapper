"""
Embedded database manager for terminology mapping.

This module handles the storage, retrieval, and management of embedded
terminology databases for offline mapping of medical terms.
Adapted from the Clinical Protocol Extractor project with terminology-specific enhancements.
"""

import os
import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Union

# Configure logging
logger = logging.getLogger(__name__)

class EmbeddedDatabaseManager:
    """
    Manages embedded terminology databases for offline mapping.
    
    This class provides a lightweight, file-based database system for
    mapping medical terms to standardized terminologies without requiring
    external services.
    
    Attributes:
        data_dir: Directory containing the terminology databases
        connections: Dictionary of database connections
        custom_mappings: User-defined custom mappings
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the database manager.
        
        Args:
            data_dir: Optional path to data directory. If not provided,
                     defaults to the standard data/terminology directory.
        """
        # Default to standard data directory
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))))), 
            'data', 'terminology'
        )
        
        # Initialize database connections
        self.connections = {}
        self.custom_mappings = {}
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
    
    def connect(self) -> bool:
        """
        Connect to the embedded databases.
        
        Returns:
            bool: True if connections were successful
        """
        try:
            # Define the database files to connect to
            databases = {
                "snomed": os.path.join(self.data_dir, "snomed_core.sqlite"),
                "loinc": os.path.join(self.data_dir, "loinc_core.sqlite"),
                "rxnorm": os.path.join(self.data_dir, "rxnorm_core.sqlite")
            }
            
            # Connect to each database if it exists
            for db_name, db_path in databases.items():
                if os.path.exists(db_path):
                    logger.info(f"Connecting to {db_name} database at {db_path}")
                    self.connections[db_name] = sqlite3.connect(db_path)
                    # Enable foreign keys
                    self.connections[db_name].execute("PRAGMA foreign_keys = ON")
                else:
                    # If database doesn't exist, create a minimal schema
                    logger.warning(f"{db_name} database not found at {db_path}, creating empty database")
                    self._create_empty_database(db_name, db_path)
                    
            # Load custom mappings if available
            custom_path = os.path.join(self.data_dir, "custom_mappings.json")
            if os.path.exists(custom_path):
                with open(custom_path, 'r') as f:
                    self.custom_mappings = json.load(f)
                logger.info(f"Loaded {sum(len(mappings) for mappings in self.custom_mappings.values())} custom mappings")
            else:
                # Create empty custom mappings file
                self.custom_mappings = {"snomed": {}, "loinc": {}, "rxnorm": {}}
                with open(custom_path, 'w') as f:
                    json.dump(self.custom_mappings, f, indent=2)
                logger.info(f"Created empty custom mappings file at {custom_path}")
            
            return True
        except Exception as e:
            logger.error(f"Error connecting to databases: {e}")
            return False
    
    def _create_empty_database(self, db_name: str, db_path: str) -> None:
        """
        Create an empty database with the required schema.
        
        Args:
            db_name: Name of the database (snomed, loinc, rxnorm)
            db_path: Path to the database file
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create tables based on database type
            if db_name == "snomed":
                # Main concepts table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS snomed_concepts (
                    id INTEGER PRIMARY KEY,
                    code TEXT NOT NULL,
                    term TEXT NOT NULL,
                    display TEXT NOT NULL,
                    concept_type TEXT,
                    is_active INTEGER DEFAULT 1
                )
                ''')
                # Create index for faster lookups
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_snomed_term ON snomed_concepts(term)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_snomed_code ON snomed_concepts(code)')
                
                # Relationships table for hierarchy and other relationships
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS snomed_relationships (
                    id INTEGER PRIMARY KEY,
                    source_code TEXT NOT NULL,
                    destination_code TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (source_code) REFERENCES snomed_concepts(code),
                    FOREIGN KEY (destination_code) REFERENCES snomed_concepts(code)
                )
                ''')
                # Create index for relationship lookups
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_snomed_rel_source ON snomed_relationships(source_code)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_snomed_rel_dest ON snomed_relationships(destination_code)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_snomed_rel_type ON snomed_relationships(relationship_type)')
                
                # Common relationship types in SNOMED CT:
                # - 116680003: Is-a (subtype) relationship
                # - 363698007: Finding site
                # - 246454002: Occurs after
                # - 255234002: After
                # - 288556008: Before
                # - 42752001: Due to
                # - 47429007: Associated with
                
            elif db_name == "loinc":
                # Main LOINC concepts table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS loinc_concepts (
                    id INTEGER PRIMARY KEY,
                    code TEXT NOT NULL,
                    term TEXT NOT NULL,
                    display TEXT NOT NULL,
                    component TEXT,
                    property TEXT,
                    time TEXT,
                    system TEXT,
                    scale TEXT,
                    method TEXT,
                    long_common_name TEXT,
                    class TEXT,
                    version_last_changed TEXT,
                    status TEXT DEFAULT 'ACTIVE',
                    consumer_name TEXT,
                    classtype INTEGER,
                    order_obs TEXT
                )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_term ON loinc_concepts(term)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_code ON loinc_concepts(code)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_component ON loinc_concepts(component)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_system ON loinc_concepts(system)')
                
                # Commit the concepts table creation
                conn.commit()
                
                # LOINC Part table for the multiaxial hierarchy
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS loinc_parts (
                    id INTEGER PRIMARY KEY,
                    part_number TEXT NOT NULL,
                    part_name TEXT NOT NULL,
                    part_display_name TEXT NOT NULL,
                    part_type TEXT NOT NULL,
                    status TEXT DEFAULT 'ACTIVE'
                )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_part_number ON loinc_parts(part_number)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_part_type ON loinc_parts(part_type)')
                
                # LOINC concept to part mapping
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS loinc_concept_parts (
                    id INTEGER PRIMARY KEY,
                    loinc_code TEXT NOT NULL,
                    part_number TEXT NOT NULL,
                    part_type TEXT NOT NULL,
                    FOREIGN KEY (loinc_code) REFERENCES loinc_concepts(code),
                    FOREIGN KEY (part_number) REFERENCES loinc_parts(part_number)
                )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_concept_parts_code ON loinc_concept_parts(loinc_code)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_concept_parts_part ON loinc_concept_parts(part_number)')
                
                # LOINC hierarchical relationships (parent-child or group relationships)
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS loinc_hierarchy (
                    id INTEGER PRIMARY KEY,
                    parent_code TEXT NOT NULL,
                    child_code TEXT NOT NULL,
                    hierarchy_type TEXT NOT NULL,
                    FOREIGN KEY (parent_code) REFERENCES loinc_concepts(code),
                    FOREIGN KEY (child_code) REFERENCES loinc_concepts(code)
                )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_hierarchy_parent ON loinc_hierarchy(parent_code)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_hierarchy_child ON loinc_hierarchy(child_code)')
                
            elif db_name == "rxnorm":
                # Create the main concepts table first, commit, then create relationships table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS rxnorm_concepts (
                    id INTEGER PRIMARY KEY,
                    code TEXT NOT NULL,
                    term TEXT NOT NULL,
                    display TEXT NOT NULL,
                    tty TEXT, /* Term Type */
                    brand_name TEXT,
                    ingredient TEXT,
                    strength TEXT,
                    dose_form TEXT,
                    route TEXT,
                    ndc TEXT, /* National Drug Code */
                    atc TEXT, /* Anatomical Therapeutic Chemical Classification */
                    is_active INTEGER DEFAULT 1
                )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_term ON rxnorm_concepts(term)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_code ON rxnorm_concepts(code)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_ingredient ON rxnorm_concepts(ingredient)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_brand ON rxnorm_concepts(brand_name)')
                
                # Commit the concepts table creation
                conn.commit()
                
                # Now create the relationships table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS rxnorm_relationships (
                    id INTEGER PRIMARY KEY,
                    source_code TEXT NOT NULL,
                    destination_code TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (source_code) REFERENCES rxnorm_concepts(code),
                    FOREIGN KEY (destination_code) REFERENCES rxnorm_concepts(code)
                )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_rel_source ON rxnorm_relationships(source_code)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_rel_dest ON rxnorm_relationships(destination_code)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_rel_type ON rxnorm_relationships(relationship_type)')
                
                # Common relationship types in RxNorm:
                # - "has_ingredient": Relates a clinical drug to its ingredients
                # - "ingredient_of": Inverse of has_ingredient
                # - "has_form": Relates a clinical drug to its dose form
                # - "has_brand_name": Relates a clinical drug to its brand name
                # - "has_precise_ingredient": More specific ingredient relationship
            
            # Commit changes and add to connections
            conn.commit()
            self.connections[db_name] = conn
            logger.info(f"Created empty {db_name} database at {db_path}")
        except Exception as e:
            logger.error(f"Error creating {db_name} database: {e}")
    
    def lookup_snomed(self, term: str, include_hierarchy: bool = False) -> Optional[Dict[str, Any]]:
        """
        Look up a term in the SNOMED CT database.
        
        Args:
            term: The term to look up
            include_hierarchy: Whether to include hierarchical information
            
        Returns:
            Dictionary with mapping information or None if not found
        """
        # Check custom mappings first
        if term in self.custom_mappings.get("snomed", {}):
            result = dict(self.custom_mappings["snomed"][term])
            
            # Add hierarchy information if requested
            if include_hierarchy and "code" in result:
                self._add_snomed_hierarchy_info(result)
                
            return result
            
        # Then check the database
        if "snomed" in self.connections:
            try:
                conn = self.connections["snomed"]
                cursor = conn.cursor()
                
                # Look for exact match first
                cursor.execute(
                    "SELECT code, display, concept_type FROM snomed_concepts WHERE LOWER(term) = ? AND is_active = 1", 
                    (term.lower(),)
                )
                result = cursor.fetchone()
                
                if result:
                    mapping = {
                        "code": result[0],
                        "display": result[1],
                        "concept_type": result[2] if result[2] else "unknown",
                        "system": "http://snomed.info/sct",
                        "found": True
                    }
                    
                    # Add hierarchy information if requested
                    if include_hierarchy:
                        self._add_snomed_hierarchy_info(mapping)
                        
                    return mapping
                
                # If no exact match, try additional query approaches
                # First try case-insensitive "contains" match
                cursor.execute(
                    "SELECT code, display, concept_type FROM snomed_concepts WHERE LOWER(term) LIKE ? AND is_active = 1 LIMIT 1", 
                    (f"%{term.lower()}%",)
                )
                result = cursor.fetchone()
                
                if result:
                    mapping = {
                        "code": result[0],
                        "display": result[1],
                        "concept_type": result[2] if result[2] else "unknown",
                        "system": "http://snomed.info/sct",
                        "found": True,
                        "confidence": 0.8  # Lower confidence for partial match
                    }
                    
                    # Add hierarchy information if requested
                    if include_hierarchy:
                        self._add_snomed_hierarchy_info(mapping)
                        
                    return mapping
                
            except Exception as e:
                logger.error(f"Error looking up SNOMED term '{term}': {e}")
        
        return None
        
    def get_snomed_concept(self, code: str, include_hierarchy: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get a SNOMED CT concept by its code.
        
        Args:
            code: The SNOMED CT code
            include_hierarchy: Whether to include hierarchical information
            
        Returns:
            Dictionary with concept information or None if not found
        """
        if "snomed" in self.connections:
            try:
                conn = self.connections["snomed"]
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT code, term, display, concept_type FROM snomed_concepts WHERE code = ? AND is_active = 1", 
                    (code,)
                )
                result = cursor.fetchone()
                
                if result:
                    concept = {
                        "code": result[0],
                        "term": result[1],
                        "display": result[2],
                        "concept_type": result[3] if result[3] else "unknown",
                        "system": "http://snomed.info/sct"
                    }
                    
                    # Add hierarchy information if requested
                    if include_hierarchy:
                        self._add_snomed_hierarchy_info(concept)
                        
                    return concept
                    
            except Exception as e:
                logger.error(f"Error getting SNOMED concept '{code}': {e}")
                
        return None
        
    def _add_snomed_hierarchy_info(self, concept: Dict[str, Any]) -> None:
        """
        Add hierarchical information to a SNOMED CT concept.
        
        Args:
            concept: The concept dictionary to augment with hierarchy info
        """
        if "snomed" not in self.connections or "code" not in concept:
            return
            
        code = concept["code"]
        conn = self.connections["snomed"]
        cursor = conn.cursor()
        
        try:
            # Get parent concepts (is-a relationships)
            cursor.execute("""
                SELECT c.code, c.display, c.concept_type
                FROM snomed_relationships r
                JOIN snomed_concepts c ON r.destination_code = c.code
                WHERE r.source_code = ? AND r.relationship_type = '116680003' AND r.is_active = 1
            """, (code,))
            
            parents = [{"code": row[0], "display": row[1], "concept_type": row[2] if row[2] else "unknown"} 
                      for row in cursor.fetchall()]
            
            if parents:
                concept["parents"] = parents
                
            # Get child concepts (inverse is-a relationships)
            cursor.execute("""
                SELECT c.code, c.display, c.concept_type
                FROM snomed_relationships r
                JOIN snomed_concepts c ON r.source_code = c.code
                WHERE r.destination_code = ? AND r.relationship_type = '116680003' AND r.is_active = 1
            """, (code,))
            
            children = [{"code": row[0], "display": row[1], "concept_type": row[2] if row[2] else "unknown"} 
                       for row in cursor.fetchall()]
            
            if children:
                concept["children"] = children
                
            # Get other relationships
            cursor.execute("""
                SELECT r.relationship_type, c.code, c.display, c.concept_type
                FROM snomed_relationships r
                JOIN snomed_concepts c ON r.destination_code = c.code
                WHERE r.source_code = ? AND r.relationship_type != '116680003' AND r.is_active = 1
            """, (code,))
            
            relationships = {}
            for row in cursor.fetchall():
                rel_type = row[0]
                if rel_type not in relationships:
                    relationships[rel_type] = []
                    
                relationships[rel_type].append({
                    "code": row[1], 
                    "display": row[2], 
                    "concept_type": row[3] if row[3] else "unknown"
                })
            
            if relationships:
                concept["relationships"] = relationships
                
        except Exception as e:
            logger.error(f"Error adding hierarchy info for '{code}': {e}")
            
    def get_snomed_ancestors(self, code: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """
        Get all ancestors (parents and their parents) of a SNOMED CT concept.
        
        Args:
            code: The SNOMED CT code
            max_depth: Maximum depth to search in the hierarchy
            
        Returns:
            List of ancestor concepts
        """
        if "snomed" not in self.connections:
            return []
            
        conn = self.connections["snomed"]
        cursor = conn.cursor()
        
        ancestors = []
        visited = set()
        current_level = [code]
        
        try:
            for _ in range(max_depth):
                if not current_level:
                    break
                    
                next_level = []
                for c in current_level:
                    if c in visited:
                        continue
                        
                    visited.add(c)
                    
                    # Get parent concepts (is-a relationships)
                    cursor.execute("""
                        SELECT c.code, c.term, c.display, c.concept_type
                        FROM snomed_relationships r
                        JOIN snomed_concepts c ON r.destination_code = c.code
                        WHERE r.source_code = ? AND r.relationship_type = '116680003' AND r.is_active = 1
                    """, (c,))
                    
                    for row in cursor.fetchall():
                        parent_code = row[0]
                        if parent_code not in visited:
                            next_level.append(parent_code)
                            ancestors.append({
                                "code": parent_code,
                                "term": row[1],
                                "display": row[2],
                                "concept_type": row[3] if row[3] else "unknown",
                                "distance": len(visited)
                            })
                
                current_level = next_level
                
            return ancestors
        except Exception as e:
            logger.error(f"Error getting ancestors for '{code}': {e}")
            return []
            
    def get_snomed_descendants(self, code: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """
        Get all descendants (children and their children) of a SNOMED CT concept.
        
        Args:
            code: The SNOMED CT code
            max_depth: Maximum depth to search in the hierarchy
            
        Returns:
            List of descendant concepts
        """
        if "snomed" not in self.connections:
            return []
            
        conn = self.connections["snomed"]
        cursor = conn.cursor()
        
        descendants = []
        visited = set()
        current_level = [code]
        
        try:
            for _ in range(max_depth):
                if not current_level:
                    break
                    
                next_level = []
                for c in current_level:
                    if c in visited:
                        continue
                        
                    visited.add(c)
                    
                    # Get child concepts (inverse is-a relationships)
                    cursor.execute("""
                        SELECT c.code, c.term, c.display, c.concept_type
                        FROM snomed_relationships r
                        JOIN snomed_concepts c ON r.source_code = c.code
                        WHERE r.destination_code = ? AND r.relationship_type = '116680003' AND r.is_active = 1
                    """, (c,))
                    
                    for row in cursor.fetchall():
                        child_code = row[0]
                        if child_code not in visited:
                            next_level.append(child_code)
                            descendants.append({
                                "code": child_code,
                                "term": row[1],
                                "display": row[2],
                                "concept_type": row[3] if row[3] else "unknown",
                                "distance": len(visited)
                            })
                
                current_level = next_level
                
            return descendants
        except Exception as e:
            logger.error(f"Error getting descendants for '{code}': {e}")
            return []
            
    def get_snomed_related_concepts(self, code: str, relationship_type: str) -> List[Dict[str, Any]]:
        """
        Get concepts related to a SNOMED CT concept by a specific relationship type.
        
        Args:
            code: The SNOMED CT code
            relationship_type: The relationship type code
            
        Returns:
            List of related concepts
        """
        if "snomed" not in self.connections:
            return []
            
        conn = self.connections["snomed"]
        cursor = conn.cursor()
        
        related = []
        
        try:
            # Get related concepts (target of relationship)
            cursor.execute("""
                SELECT c.code, c.term, c.display, c.concept_type
                FROM snomed_relationships r
                JOIN snomed_concepts c ON r.destination_code = c.code
                WHERE r.source_code = ? AND r.relationship_type = ? AND r.is_active = 1
            """, (code, relationship_type))
            
            for row in cursor.fetchall():
                related.append({
                    "code": row[0],
                    "term": row[1],
                    "display": row[2],
                    "concept_type": row[3] if row[3] else "unknown",
                    "direction": "outgoing"
                })
                
            # Get concepts that relate to this one (source of relationship)
            cursor.execute("""
                SELECT c.code, c.term, c.display, c.concept_type
                FROM snomed_relationships r
                JOIN snomed_concepts c ON r.source_code = c.code
                WHERE r.destination_code = ? AND r.relationship_type = ? AND r.is_active = 1
            """, (code, relationship_type))
            
            for row in cursor.fetchall():
                related.append({
                    "code": row[0],
                    "term": row[1],
                    "display": row[2],
                    "concept_type": row[3] if row[3] else "unknown",
                    "direction": "incoming"
                })
                
            return related
        except Exception as e:
            logger.error(f"Error getting related concepts for '{code}': {e}")
            return []
    
    def lookup_loinc(self, term: str, include_details: bool = False) -> Optional[Dict[str, Any]]:
        """
        Look up a term in the LOINC database with enhanced laboratory test matching.
        
        Args:
            term: The term to look up
            include_details: Whether to include detailed LOINC information
            
        Returns:
            Dictionary with mapping information or None if not found
        """
        # Check custom mappings first
        if term in self.custom_mappings.get("loinc", {}):
            result = dict(self.custom_mappings["loinc"][term])
            
            # Add detailed information if requested
            if include_details and "code" in result:
                self._add_loinc_details(result)
                
            return result
            
        # Normalize the laboratory test name
        normalized_term = self._normalize_lab_term(term)
        
        # Then check the database
        if "loinc" in self.connections:
            try:
                conn = self.connections["loinc"]
                cursor = conn.cursor()
                
                # Look for exact match on term
                cursor.execute(
                    """SELECT code, display, component, property, time, system, scale, method, long_common_name 
                       FROM loinc_concepts 
                       WHERE LOWER(term) = ?""", 
                    (term.lower(),)
                )
                result = cursor.fetchone()
                
                if result:
                    mapping = {
                        "code": result[0],
                        "display": result[1],
                        "component": result[2],
                        "property": result[3],
                        "time": result[4],
                        "system": "http://loinc.org",
                        "specimen": result[5],
                        "scale": result[6],
                        "method": result[7],
                        "long_common_name": result[8] if result[8] else result[1],
                        "found": True,
                        "match_type": "exact",
                        "confidence": 1.0
                    }
                    if include_details:
                        self._add_loinc_details(mapping)
                    return mapping
                
                # Try with normalized term if different from original
                if normalized_term != term.lower():
                    cursor.execute(
                        """SELECT code, display, component, property, time, system, scale, method, long_common_name 
                           FROM loinc_concepts 
                           WHERE LOWER(term) = ?""", 
                        (normalized_term,)
                    )
                    result = cursor.fetchone()
                    if result:
                        mapping = {
                            "code": result[0],
                            "display": result[1],
                            "component": result[2],
                            "property": result[3],
                            "time": result[4],
                            "system": "http://loinc.org",
                            "specimen": result[5],
                            "scale": result[6],
                            "method": result[7],
                            "long_common_name": result[8] if result[8] else result[1],
                            "found": True,
                            "match_type": "normalized",
                            "confidence": 0.95
                        }
                        if include_details:
                            self._add_loinc_details(mapping)
                        return mapping
                
                # Try component match (for lab tests)
                cursor.execute(
                    """SELECT code, display, component, property, time, system, scale, method, long_common_name 
                       FROM loinc_concepts 
                       WHERE LOWER(component) = ?""", 
                    (normalized_term,)
                )
                result = cursor.fetchone()
                
                if result:
                    mapping = {
                        "code": result[0],
                        "display": result[1],
                        "component": result[2],
                        "property": result[3],
                        "time": result[4],
                        "system": "http://loinc.org",
                        "specimen": result[5],
                        "scale": result[6],
                        "method": result[7],
                        "long_common_name": result[8] if result[8] else result[1],
                        "found": True,
                        "match_type": "component",
                        "confidence": 0.9
                    }
                    if include_details:
                        self._add_loinc_details(mapping)
                    return mapping
                
                # Try consumer name match
                cursor.execute(
                    """SELECT code, display, component, property, time, system, scale, method, long_common_name, consumer_name 
                       FROM loinc_concepts 
                       WHERE LOWER(consumer_name) LIKE ? LIMIT 1""", 
                    (f"%{normalized_term}%",)
                )
                result = cursor.fetchone()
                
                if result:
                    mapping = {
                        "code": result[0],
                        "display": result[1],
                        "component": result[2],
                        "property": result[3],
                        "time": result[4],
                        "system": "http://loinc.org",
                        "specimen": result[5],
                        "scale": result[6],
                        "method": result[7],
                        "long_common_name": result[8] if result[8] else result[1],
                        "consumer_name": result[9],
                        "found": True,
                        "match_type": "consumer_name",
                        "confidence": 0.85
                    }
                    if include_details:
                        self._add_loinc_details(mapping)
                    return mapping
                
                # Try partial component or display match
                cursor.execute(
                    """SELECT code, display, component, property, time, system, scale, method, long_common_name 
                       FROM loinc_concepts 
                       WHERE LOWER(component) LIKE ? OR LOWER(display) LIKE ? LIMIT 1""", 
                    (f"%{normalized_term}%", f"%{normalized_term}%")
                )
                result = cursor.fetchone()
                
                if result:
                    mapping = {
                        "code": result[0],
                        "display": result[1],
                        "component": result[2],
                        "property": result[3],
                        "time": result[4],
                        "system": "http://loinc.org",
                        "specimen": result[5],
                        "scale": result[6],
                        "method": result[7],
                        "long_common_name": result[8] if result[8] else result[1],
                        "found": True,
                        "match_type": "partial",
                        "confidence": 0.7
                    }
                    if include_details:
                        self._add_loinc_details(mapping)
                    return mapping
                
                # Try advanced pattern matching for common lab tests
                lab_test_match = self._try_common_lab_patterns(cursor, normalized_term)
                if lab_test_match:
                    if include_details:
                        self._add_loinc_details(lab_test_match)
                    return lab_test_match
                
            except Exception as e:
                logger.error(f"Error looking up LOINC term '{term}': {e}")
        
        return None
    
    def _try_common_lab_patterns(self, cursor, term: str) -> Optional[Dict[str, Any]]:
        """
        Try common laboratory test patterns for enhanced LOINC matching.
        
        Args:
            cursor: Database cursor for LOINC database
            term: The term to match
            
        Returns:
            Dictionary with mapping information or None if not found
        """
        term_lower = term.lower().strip()
        
        # Pattern 1: "component in specimen" pattern (e.g., "glucose in blood")
        if " in " in term_lower:
            parts = term_lower.split(" in ")
            if len(parts) == 2:
                component = parts[0].strip()
                specimen = parts[1].strip()
                
                # Try to find matches with this pattern
                cursor.execute("""
                    SELECT code, display, component, property, time, system, scale, method, long_common_name
                    FROM loinc_concepts 
                    WHERE LOWER(component) LIKE ? AND LOWER(system) LIKE ?
                    LIMIT 1
                """, (f"%{component}%", f"%{specimen}%"))
                
                result = cursor.fetchone()
                if result:
                    return {
                        "code": result[0],
                        "display": result[1],
                        "component": result[2],
                        "property": result[3],
                        "time": result[4],
                        "system": "http://loinc.org",
                        "specimen": result[5],
                        "scale": result[6],
                        "method": result[7],
                        "long_common_name": result[8] if result[8] else result[1],
                        "found": True,
                        "match_type": "specimen_pattern",
                        "confidence": 0.85
                    }
        
        # Pattern 2: Common component matching (e.g., "cholesterol" -> cholesterol tests)
        common_components = {
            "cholesterol": "2093-3",  # Cholesterol [Mass/volume] in Serum or Plasma
            "glucose": "2339-0",      # Glucose [Mass/volume] in Blood
            "potassium": "2823-3",    # Potassium [Moles/volume] in Serum or Plasma
            "sodium": "2951-2",       # Sodium [Moles/volume] in Serum or Plasma
            "hemoglobin": "718-7",    # Hemoglobin [Mass/volume] in Blood
            "hematocrit": "4544-3",   # Hematocrit [Volume Fraction] of Blood
            "creatinine": "2160-0"    # Creatinine [Mass/volume] in Serum or Plasma
        }
        
        if term_lower in common_components:
            code = common_components[term_lower]
            cursor.execute("""
                SELECT code, display, component, property, time, system, scale, method, long_common_name
                FROM loinc_concepts 
                WHERE code = ?
            """, (code,))
            
            result = cursor.fetchone()
            if result:
                return {
                    "code": result[0],
                    "display": result[1],
                    "component": result[2],
                    "property": result[3],
                    "time": result[4],
                    "system": "http://loinc.org",
                    "specimen": result[5],
                    "scale": result[6],
                    "method": result[7],
                    "long_common_name": result[8] if result[8] else result[1],
                    "found": True,
                    "match_type": "common_component",
                    "confidence": 0.9
                }
        
        return None
    
    def _normalize_lab_term(self, term: str) -> str:
        """
        Normalize a laboratory test name for better matching.
        
        Args:
            term: The test name to normalize
            
        Returns:
            Normalized lab test name
        """
        normalized = term.lower()
        
        # Remove common prefixes
        prefixes = ["test", "lab test", "laboratory test", "analysis", "measurement", "level", "serum", "plasma"]
        for prefix in prefixes:
            if normalized.startswith(prefix + " "):
                normalized = normalized[len(prefix) + 1:]
                
        # Remove common suffixes
        suffixes = ["test", "level", "count", "measurement", "analysis", "panel", "assay"]
        for suffix in suffixes:
            if normalized.endswith(" " + suffix):
                normalized = normalized[:-len(suffix) - 1]
        
        # Handle common abbreviations and synonyms
        replacements = {
            "hgb": "hemoglobin",
            "hct": "hematocrit",
            "wbc": "leukocyte count",
            "rbc": "erythrocyte count",
            "plt": "platelet count",
            "gluc": "glucose",
            "chol": "cholesterol",
            "creat": "creatinine",
            "bili": "bilirubin",
            "trig": "triglycerides",
            "bun": "urea nitrogen",
            "uric acid": "urate",
            "potassium": "potassium",
            "sodium": "sodium",
            "chloride": "chloride",
            "k": "potassium",
            "na": "sodium",
            "cl": "chloride",
            "hba1c": "hemoglobin a1c",
            "a1c": "hemoglobin a1c"
        }
        
        # Replace the term if it's an exact match for a common abbreviation
        if normalized in replacements:
            normalized = replacements[normalized]
            
        # Clean up whitespace
        import re
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _try_common_lab_patterns(self, cursor, term: str) -> Optional[Dict[str, Any]]:
        """
        Try matching common laboratory test patterns.
        
        Args:
            cursor: Database cursor
            term: The normalized lab test name
            
        Returns:
            Match result or None
        """
        # Common lab test patterns
        common_components = [
            "glucose", "hemoglobin", "creatinine", "potassium", "sodium",
            "calcium", "chloride", "cholesterol", "triglycerides", "protein",
            "albumin", "bilirubin", "alk phos", "alt", "ast", "ldh", "ggt", 
            "tsh", "t3", "t4", "wbc", "rbc", "platelet", "hematocrit"
        ]
        
        # Try matching exact common components
        if term in common_components:
            cursor.execute(
                """SELECT code, display, component, property, time, system, scale, method, long_common_name 
                   FROM loinc_concepts 
                   WHERE LOWER(component) = ? AND (method IS NULL OR method = '') LIMIT 1""",
                (term,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    "code": result[0],
                    "display": result[1],
                    "component": result[2],
                    "property": result[3],
                    "time": result[4],
                    "system": "http://loinc.org",
                    "specimen": result[5],
                    "scale": result[6],
                    "method": result[7],
                    "long_common_name": result[8] if result[8] else result[1],
                    "found": True,
                    "match_type": "common_component",
                    "confidence": 0.85
                }
        
        # Try specific specimen pattern (e.g., "glucose in blood")
        import re
        specimen_match = re.search(r'([\w\s]+) in ([\w\s]+)', term)
        if specimen_match:
            component = specimen_match.group(1).strip()
            specimen = specimen_match.group(2).strip()
            
            cursor.execute(
                """SELECT code, display, component, property, time, system, scale, method, long_common_name 
                   FROM loinc_concepts 
                   WHERE LOWER(component) LIKE ? AND LOWER(system) LIKE ? LIMIT 1""",
                (f"%{component}%", f"%{specimen}%")
            )
            result = cursor.fetchone()
            if result:
                return {
                    "code": result[0],
                    "display": result[1],
                    "component": result[2],
                    "property": result[3],
                    "time": result[4],
                    "system": "http://loinc.org",
                    "specimen": result[5],
                    "scale": result[6],
                    "method": result[7],
                    "long_common_name": result[8] if result[8] else result[1],
                    "found": True,
                    "match_type": "specimen_pattern",
                    "confidence": 0.8
                }
                
        return None
    
    def _add_loinc_details(self, loinc_data: Dict[str, Any]) -> None:
        """
        Add detailed LOINC information to a result.
        
        Args:
            loinc_data: The LOINC data dictionary to augment
        """
        if "loinc" not in self.connections or "code" not in loinc_data:
            return
            
        code = loinc_data["code"]
        conn = self.connections["loinc"]
        cursor = conn.cursor()
        
        try:
            # Get complete concept information if not already present
            if "component" not in loinc_data or "property" not in loinc_data:
                cursor.execute(
                    """SELECT component, property, time, system, scale, method, long_common_name, class, status 
                       FROM loinc_concepts 
                       WHERE code = ?""", 
                    (code,)
                )
                result = cursor.fetchone()
                
                if result:
                    # Add LOINC structural information
                    if result[0]: loinc_data["component"] = result[0]
                    if result[1]: loinc_data["property"] = result[1]
                    if result[2]: loinc_data["time"] = result[2]
                    if result[3]: loinc_data["specimen"] = result[3]
                    if result[4]: loinc_data["scale"] = result[4]
                    if result[5]: loinc_data["method"] = result[5]
                    if result[6]: loinc_data["long_common_name"] = result[6]
                    if result[7]: loinc_data["class"] = result[7]
                    if result[8]: loinc_data["status"] = result[8]
            
            # Get LOINC part information for the multiaxial structure
            cursor.execute("""
                SELECT p.part_number, p.part_name, p.part_display_name, cp.part_type
                FROM loinc_concept_parts cp
                JOIN loinc_parts p ON cp.part_number = p.part_number
                WHERE cp.loinc_code = ?
            """, (code,))
            parts = cursor.fetchall()
            
            if parts:
                loinc_data["parts"] = []
                for part in parts:
                    loinc_data["parts"].append({
                        "part_number": part[0],
                        "part_name": part[1],
                        "part_display_name": part[2],
                        "part_type": part[3]
                    })
            
            # Get parent groups this concept belongs to
            cursor.execute("""
                SELECT c.code, c.display, c.long_common_name, h.hierarchy_type
                FROM loinc_hierarchy h
                JOIN loinc_concepts c ON h.parent_code = c.code
                WHERE h.child_code = ?
            """, (code,))
            parents = cursor.fetchall()
            
            if parents:
                loinc_data["parent_groups"] = []
                for parent in parents:
                    loinc_data["parent_groups"].append({
                        "code": parent[0],
                        "display": parent[1],
                        "long_common_name": parent[2] if parent[2] else parent[1],
                        "hierarchy_type": parent[3]
                    })
            
            # Get child concepts if this is a panel/group
            cursor.execute("""
                SELECT c.code, c.display, c.long_common_name, h.hierarchy_type
                FROM loinc_hierarchy h
                JOIN loinc_concepts c ON h.child_code = c.code
                WHERE h.parent_code = ?
            """, (code,))
            children = cursor.fetchall()
            
            if children:
                loinc_data["child_items"] = []
                for child in children:
                    loinc_data["child_items"].append({
                        "code": child[0],
                        "display": child[1],
                        "long_common_name": child[2] if child[2] else child[1],
                        "hierarchy_type": child[3]
                    })
                    
        except Exception as e:
            logger.error(f"Error adding LOINC details for '{code}': {e}")
            
    def get_loinc_concept(self, code: str, include_details: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get a LOINC concept by its code.
        
        Args:
            code: The LOINC code
            include_details: Whether to include detailed information
            
        Returns:
            Dictionary with concept information or None if not found
        """
        if "loinc" in self.connections:
            try:
                conn = self.connections["loinc"]
                cursor = conn.cursor()
                
                cursor.execute(
                    """SELECT code, term, display, component, property, time, system, scale, method, long_common_name, class 
                       FROM loinc_concepts 
                       WHERE code = ?""", 
                    (code,)
                )
                result = cursor.fetchone()
                
                if result:
                    concept = {
                        "code": result[0],
                        "term": result[1],
                        "display": result[2],
                        "component": result[3],
                        "property": result[4],
                        "time": result[5],
                        "specimen": result[6],
                        "scale": result[7],
                        "method": result[8],
                        "long_common_name": result[9] if result[9] else result[2],
                        "class": result[10],
                        "system": "http://loinc.org"
                    }
                    
                    # Add detailed information if requested
                    if include_details:
                        self._add_loinc_details(concept)
                        
                    return concept
                    
            except Exception as e:
                logger.error(f"Error getting LOINC concept '{code}': {e}")
                
        return None
                
    def get_loinc_hierarchy(self, code: str, relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get parent and child concepts in the LOINC hierarchy.
        
        Args:
            code: The LOINC code
            relationship_type: Optional specific hierarchy relationship type
            
        Returns:
            Dictionary with parent and child concepts
        """
        if "loinc" not in self.connections:
            return []
            
        conn = self.connections["loinc"]
        cursor = conn.cursor()
        hierarchy = []
        
        try:
            # Build the query based on whether a relationship type is specified
            params = [code]
            rel_type_clause = ""
            if relationship_type:
                rel_type_clause = "AND h.hierarchy_type = ?"
                params.append(relationship_type)
                
            # Get parent groups
            cursor.execute(f"""
                SELECT c.code, c.display, c.long_common_name, h.hierarchy_type
                FROM loinc_hierarchy h
                JOIN loinc_concepts c ON h.parent_code = c.code
                WHERE h.child_code = ? {rel_type_clause}
            """, params)
            
            parents = cursor.fetchall()
            for parent in parents:
                hierarchy.append({
                    "code": parent[0],
                    "display": parent[1],
                    "long_common_name": parent[2] if parent[2] else parent[1],
                    "hierarchy_type": parent[3],
                    "relationship": "parent"
                })
                
            # Get child concepts
            cursor.execute(f"""
                SELECT c.code, c.display, c.long_common_name, h.hierarchy_type
                FROM loinc_hierarchy h
                JOIN loinc_concepts c ON h.child_code = c.code
                WHERE h.parent_code = ? {rel_type_clause}
            """, params)
            
            children = cursor.fetchall()
            for child in children:
                hierarchy.append({
                    "code": child[0],
                    "display": child[1],
                    "long_common_name": child[2] if child[2] else child[1],
                    "hierarchy_type": child[3],
                    "relationship": "child"
                })
                
            return hierarchy
                
        except Exception as e:
            logger.error(f"Error getting LOINC hierarchy for '{code}': {e}")
            return []
            
    def get_loinc_by_part(self, part_number: str, part_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get LOINC concepts that contain a specific part.
        
        Args:
            part_number: The LOINC part number
            part_type: Optional specific part type
            
        Returns:
            List of LOINC concepts that contain the specified part
        """
        if "loinc" not in self.connections:
            return []
            
        conn = self.connections["loinc"]
        cursor = conn.cursor()
        concepts = []
        
        try:
            # Build the query based on whether a part type is specified
            params = [part_number]
            part_type_clause = ""
            if part_type:
                part_type_clause = "AND cp.part_type = ?"
                params.append(part_type)
                
            cursor.execute(f"""
                SELECT c.code, c.display, c.component, c.long_common_name, cp.part_type
                FROM loinc_concept_parts cp
                JOIN loinc_concepts c ON cp.loinc_code = c.code
                WHERE cp.part_number = ? {part_type_clause}
            """, params)
            
            results = cursor.fetchall()
            for result in results:
                concepts.append({
                    "code": result[0],
                    "display": result[1],
                    "component": result[2],
                    "long_common_name": result[3] if result[3] else result[1],
                    "part_type": result[4],
                    "system": "http://loinc.org"
                })
                
            return concepts
                
        except Exception as e:
            logger.error(f"Error getting LOINC concepts for part '{part_number}': {e}")
            return []
    
    def lookup_rxnorm(self, term: str, include_details: bool = False) -> Optional[Dict[str, Any]]:
        """
        Look up a term in the RxNorm database with enhanced medication matching.
        
        Args:
            term: The term to look up
            include_details: Whether to include detailed medication information
            
        Returns:
            Dictionary with mapping information or None if not found
        """
        # Check custom mappings first
        if term in self.custom_mappings.get("rxnorm", {}):
            result = dict(self.custom_mappings["rxnorm"][term])
            
            # Add detailed information if requested
            if include_details and "code" in result:
                self._add_rxnorm_details(result)
                
            return result
            
        # Normalize the drug name
        normalized_term = self._normalize_drug_name(term)
        
        # Then check the database
        if "rxnorm" in self.connections:
            try:
                conn = self.connections["rxnorm"]
                cursor = conn.cursor()
                
                # Look for exact match on original term
                result = self._exact_rxnorm_match(cursor, term)
                if result:
                    if include_details:
                        self._add_rxnorm_details(result)
                    return result
                
                # Try with normalized term if different from original
                if normalized_term != term.lower():
                    result = self._exact_rxnorm_match(cursor, normalized_term)
                    if result:
                        result["confidence"] = 0.95  # Slightly lower confidence for normalized match
                        if include_details:
                            self._add_rxnorm_details(result)
                        return result
                
                # Try ingredient match (for generic drugs)
                cursor.execute(
                    """SELECT code, display, tty, ingredient, brand_name, strength, dose_form 
                       FROM rxnorm_concepts 
                       WHERE LOWER(ingredient) = ? AND is_active = 1 
                       LIMIT 1""", 
                    (normalized_term,)
                )
                result = cursor.fetchone()
                if result:
                    mapping = {
                        "code": result[0],
                        "display": result[1],
                        "term_type": result[2] if result[2] else "SCD",  # Default to standard clinical drug
                        "ingredient": result[3],
                        "brand_name": result[4],
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "found": True,
                        "confidence": 0.9,  # Good confidence for ingredient match
                        "match_type": "ingredient"
                    }
                    if include_details:
                        self._add_rxnorm_details(mapping)
                    return mapping
                
                # Try brand name match
                cursor.execute(
                    """SELECT code, display, tty, ingredient, brand_name, strength, dose_form 
                       FROM rxnorm_concepts 
                       WHERE LOWER(brand_name) = ? AND is_active = 1 
                       LIMIT 1""", 
                    (normalized_term,)
                )
                result = cursor.fetchone()
                if result:
                    mapping = {
                        "code": result[0],
                        "display": result[1],
                        "term_type": result[2] if result[2] else "BN",  # Brand name
                        "ingredient": result[3],
                        "brand_name": result[4],
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "found": True,
                        "confidence": 0.9,  # Good confidence for brand match
                        "match_type": "brand"
                    }
                    if include_details:
                        self._add_rxnorm_details(mapping)
                    return mapping
                
                # Try partial match using term with pattern matching for drug naming conventions
                pattern_matches = self._try_medication_patterns(cursor, normalized_term)
                if pattern_matches:
                    mapping = pattern_matches
                    if include_details:
                        self._add_rxnorm_details(mapping)
                    return mapping
                
                # Fallback to simple partial match
                cursor.execute(
                    """SELECT code, display, tty, ingredient, brand_name, strength, dose_form
                       FROM rxnorm_concepts 
                       WHERE (LOWER(term) LIKE ? OR LOWER(ingredient) LIKE ? OR LOWER(brand_name) LIKE ?) 
                       AND is_active = 1 
                       LIMIT 1""", 
                    (f"%{normalized_term}%", f"%{normalized_term}%", f"%{normalized_term}%")
                )
                result = cursor.fetchone()
                if result:
                    mapping = {
                        "code": result[0],
                        "display": result[1],
                        "term_type": result[2] if result[2] else "unknown",
                        "ingredient": result[3],
                        "brand_name": result[4],
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "found": True,
                        "confidence": 0.7,  # Lower confidence for partial match
                        "match_type": "partial"
                    }
                    if include_details:
                        self._add_rxnorm_details(mapping)
                    return mapping
                
            except Exception as e:
                logger.error(f"Error looking up RxNorm term '{term}': {e}")
        
        return None
        
    def _exact_rxnorm_match(self, cursor, term: str) -> Optional[Dict[str, Any]]:
        """Helper method for exact RxNorm term matching."""
        cursor.execute(
            """SELECT code, display, tty, ingredient, brand_name, strength, dose_form 
               FROM rxnorm_concepts 
               WHERE LOWER(term) = ? AND is_active = 1""", 
            (term.lower(),)
        )
        result = cursor.fetchone()
        
        if result:
            return {
                "code": result[0],
                "display": result[1],
                "term_type": result[2] if result[2] else "unknown",
                "ingredient": result[3],
                "brand_name": result[4],
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "found": True,
                "confidence": 1.0,  # Full confidence for exact match
                "match_type": "exact"
            }
        return None
        
    def _normalize_drug_name(self, term: str) -> str:
        """
        Normalize a drug name by removing common dosage forms and strengths.
        
        Args:
            term: The drug name to normalize
            
        Returns:
            Normalized drug name
        """
        normalized = term.lower()
        
        # Remove common strength patterns (e.g., 10mg, 100mcg)
        import re
        normalized = re.sub(r'\b\d+\s*(?:mg|g|mcg|ml|mEq)\b', '', normalized)
        
        # Remove common dosage forms
        dosage_forms = [
            'tablet', 'capsule', 'solution', 'suspension', 'injection', 
            'syrup', 'cream', 'ointment', 'gel', 'lotion', 'patch', 
            'extended release', 'er', 'xr', 'oral', 'topical', 'film'
        ]
        
        for form in dosage_forms:
            normalized = normalized.replace(form, '')
        
        # Remove parenthetical information like (hydrochloride)
        normalized = re.sub(r'\([^)]*\)', '', normalized)
        
        # Remove common brand suffixes
        suffixes = ['-hct', '-xr', '-cr', '-sr', '-ir']
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
        
        # Clean up whitespace and punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
        
    def _try_medication_patterns(self, cursor, term: str) -> Optional[Dict[str, Any]]:
        """
        Try matching medication-specific patterns.
        
        Args:
            cursor: Database cursor
            term: The normalized drug name
            
        Returns:
            Match result or None
        """
        # Try strength + ingredient pattern (e.g., "10 mg lisinopril" -> "lisinopril")
        import re
        ingredient_match = re.search(r'(\d+\s*(?:mg|g|mcg|ml))\s+(\w+)', term)
        if ingredient_match:
            potential_ingredient = ingredient_match.group(2)
            cursor.execute(
                """SELECT code, display, tty, ingredient, brand_name, strength, dose_form 
                   FROM rxnorm_concepts 
                   WHERE LOWER(ingredient) = ? AND is_active = 1 
                   LIMIT 1""", 
                (potential_ingredient,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    "code": result[0],
                    "display": result[1],
                    "term_type": result[2] if result[2] else "IN",  # Ingredient 
                    "ingredient": result[3],
                    "brand_name": result[4],
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "found": True,
                    "confidence": 0.85,
                    "match_type": "pattern_strength_ingredient"
                }
        
        # Try combination drugs (e.g., "lisinopril-hctz" -> "lisinopril" and "hydrochlorothiazide")
        if '-' in term or '/' in term:
            parts = re.split(r'[-/]', term)
            if len(parts) >= 2:
                # Try matching the first component
                cursor.execute(
                    """SELECT code, display, tty, ingredient, brand_name, strength, dose_form 
                       FROM rxnorm_concepts 
                       WHERE LOWER(ingredient) LIKE ? AND is_active = 1 
                       LIMIT 1""", 
                    (f"%{parts[0].strip()}%",)
                )
                result = cursor.fetchone()
                if result:
                    return {
                        "code": result[0],
                        "display": result[1],
                        "term_type": result[2] if result[2] else "SCDC",  # Standard clinical drug component
                        "ingredient": result[3],
                        "brand_name": result[4],
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "found": True,
                        "confidence": 0.75,
                        "match_type": "pattern_combination",
                        "note": "Matched first component of combination drug"
                    }
                    
        return None
        
    def _add_rxnorm_details(self, rxnorm_data: Dict[str, Any]) -> None:
        """
        Add detailed RxNorm information to a result.
        
        Args:
            rxnorm_data: The RxNorm data dictionary to augment
        """
        if "rxnorm" not in self.connections or "code" not in rxnorm_data:
            return
            
        code = rxnorm_data["code"]
        conn = self.connections["rxnorm"]
        cursor = conn.cursor()
        
        try:
            # Get complete concept information
            cursor.execute(
                """SELECT term, display, tty, ingredient, brand_name, strength, dose_form, route, ndc, atc
                   FROM rxnorm_concepts 
                   WHERE code = ? AND is_active = 1""", 
                (code,)
            )
            result = cursor.fetchone()
            
            if result:
                # Add detailed fields if available
                if result[0]:  # term
                    rxnorm_data["term"] = result[0]
                if result[2]:  # tty
                    rxnorm_data["term_type"] = result[2]
                if result[3]:  # ingredient
                    rxnorm_data["ingredient"] = result[3]
                if result[4]:  # brand_name
                    rxnorm_data["brand_name"] = result[4]
                if result[5]:  # strength
                    rxnorm_data["strength"] = result[5]
                if result[6]:  # dose_form
                    rxnorm_data["dose_form"] = result[6]
                if result[7]:  # route
                    rxnorm_data["route"] = result[7]
                if result[8]:  # ndc
                    rxnorm_data["ndc"] = result[8]
                if result[9]:  # atc
                    rxnorm_data["atc"] = result[9]
                    
            # Get related ingredients if this is a clinical drug
            cursor.execute(
                """SELECT c.code, c.term, c.display
                   FROM rxnorm_relationships r
                   JOIN rxnorm_concepts c ON r.destination_code = c.code
                   WHERE r.source_code = ? AND r.relationship_type = 'has_ingredient' AND r.is_active = 1""", 
                (code,)
            )
            ingredients = cursor.fetchall()
            
            if ingredients:
                rxnorm_data["ingredients"] = [
                    {"code": row[0], "term": row[1], "display": row[2]}
                    for row in ingredients
                ]
                
            # Get related brand names if this is a generic
            cursor.execute(
                """SELECT c.code, c.term, c.display, c.brand_name
                   FROM rxnorm_relationships r
                   JOIN rxnorm_concepts c ON r.source_code = c.code
                   WHERE r.destination_code = ? AND r.relationship_type = 'has_ingredient' AND r.is_active = 1
                   AND c.brand_name IS NOT NULL""", 
                (code,)
            )
            brands = cursor.fetchall()
            
            if brands:
                rxnorm_data["brand_alternatives"] = [
                    {"code": row[0], "term": row[1], "display": row[2], "brand_name": row[3]}
                    for row in brands
                ]
                
        except Exception as e:
            logger.error(f"Error adding RxNorm details for '{code}': {e}")
    
    def add_mapping(self, system: str, term: str, mapping: Dict[str, Any]) -> bool:
        """
        Add a mapping to the custom mappings.
        
        Args:
            system: The terminology system (snomed, loinc, rxnorm)
            term: The term to map
            mapping: The mapping information
            
        Returns:
            bool: True if the mapping was added successfully
        """
        try:
            # Ensure the system exists in custom mappings
            if system not in self.custom_mappings:
                self.custom_mappings[system] = {}
            
            # Add the mapping
            self.custom_mappings[system][term] = mapping
            
            # Save to file
            custom_path = os.path.join(self.data_dir, "custom_mappings.json")
            with open(custom_path, 'w') as f:
                json.dump(self.custom_mappings, f, indent=2)
            
            logger.info(f"Added custom {system} mapping for '{term}': {mapping['code']}")
            return True
        except Exception as e:
            logger.error(f"Error adding custom mapping for '{term}': {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the databases.
        
        Returns:
            Dictionary with statistics about the databases
        """
        stats = {
            "snomed": {"count": 0, "database_size": 0},
            "loinc": {"count": 0, "database_size": 0},
            "rxnorm": {"count": 0, "database_size": 0},
            "custom": {
                "snomed": len(self.custom_mappings.get("snomed", {})),
                "loinc": len(self.custom_mappings.get("loinc", {})),
                "rxnorm": len(self.custom_mappings.get("rxnorm", {}))
            }
        }
        
        # Get statistics for each database
        for system in ["snomed", "loinc", "rxnorm"]:
            if system in self.connections:
                try:
                    conn = self.connections[system]
                    cursor = conn.cursor()
                    
                    # Get row count
                    table_name = f"{system}_concepts"
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    stats[system]["count"] = cursor.fetchone()[0]
                    
                    # Get database file size
                    db_path = os.path.join(self.data_dir, f"{system}_core.sqlite")
                    if os.path.exists(db_path):
                        stats[system]["database_size"] = os.path.getsize(db_path)
                except Exception as e:
                    logger.error(f"Error getting statistics for {system}: {e}")
        
        return stats
    
    def close(self):
        """Close all database connections."""
        for conn in self.connections.values():
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
        
        self.connections = {}