"""External API services for medical terminology lookup."""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import hashlib
from pathlib import Path
import time
from urllib.parse import quote

logger = logging.getLogger(__name__)


class TerminologyAPIService:
    """Manages connections to external terminology APIs."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize API service with in-memory caching only."""
        # Use in-memory cache instead of file-based cache
        self._memory_cache = {}
        self.session = requests.Session()
        self.session.timeout = 5  # 5 second timeout for API requests
        self.cache_ttl = timedelta(hours=1)  # Cache responses for 1 hour in memory
        
        # API endpoints
        self.apis = {
            'rxnorm': {
                'base_url': 'https://rxnav.nlm.nih.gov/REST',
                'endpoints': {
                    'search': '/drugs.json',
                    'rxcui': '/rxcui.json',
                    'allrelated': '/rxcui/{rxcui}/allrelated.json',
                    'spellingsuggestions': '/spellingsuggestions.json'
                }
            },
            'umls': {
                'base_url': 'https://uts-ws.nlm.nih.gov/rest',
                'endpoints': {
                    'search': '/search/current',
                    'content': '/content/current/CUI/{cui}',
                    'crosswalk': '/crosswalk/current/source/{source}/{id}'
                },
                'requires_auth': True
            },
            'loinc': {
                'base_url': 'https://fhir.loinc.org',
                'endpoints': {
                    'search': '/CodeSystem/$lookup',
                    'valueset': '/ValueSet/$expand'
                }
            },
            'snomed': {
                'base_url': 'https://browser.ihtsdotools.org/snowstorm/snomed-ct/browser/MAIN/2024-10-01',
                'endpoints': {
                    'search': '/descriptions',
                    'concept': '/concepts/{conceptId}',
                    'relationships': '/concepts/{conceptId}/relationships'
                }
            },
            'clinicaltables': {
                'base_url': 'https://clinicaltables.nlm.nih.gov/api',
                'endpoints': {
                    'rxterms': '/rxterms/v3/search',
                    'loinc': '/loinc_items/v3/search',
                    'icd10': '/icd10cm/v3/search',
                    'snomed': '/snomed_ct/v3/search'
                }
            }
        }
    
    def _get_cache_key(self, api: str, endpoint: str, params: Dict) -> str:
        """Generate cache key for API request."""
        param_str = json.dumps(params, sort_keys=True)
        key = f"{api}_{endpoint}_{param_str}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if available and not expired."""
        if cache_key in self._memory_cache:
            try:
                cached = self._memory_cache[cache_key]
                cache_time = datetime.fromisoformat(cached['timestamp'])
                if datetime.now() - cache_time < self.cache_ttl:
                    return cached['data']
                else:
                    # Remove expired cache entry
                    del self._memory_cache[cache_key]
            except Exception as e:
                logger.warning(f"Error reading memory cache: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        """Save response to memory cache."""
        try:
            self._memory_cache[cache_key] = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
        except Exception as e:
            logger.warning(f"Error saving to memory cache: {e}")
    
    def search_rxnorm(self, term: str, max_results: int = 10) -> List[Dict]:
        """Search RxNorm for medications."""
        cache_key = self._get_cache_key('rxnorm', 'search', {'name': term})
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached
        
        try:
            # First try exact search
            response = self.session.get(
                f"{self.apis['rxnorm']['base_url']}/drugs.json",
                params={'name': term}
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            drug_group = data.get('drugGroup', {})
            
            # Process concept groups
            for concept_group in drug_group.get('conceptGroup', []):
                for concept in concept_group.get('conceptProperties', []):
                    results.append({
                        'code': concept.get('rxcui'),
                        'display': concept.get('name'),
                        'system': 'RxNorm',
                        'tty': concept.get('tty'),
                        'synonym': concept.get('synonym', '')
                    })
            
            # If no results, try spelling suggestions
            if not results:
                spell_response = self.session.get(
                    f"{self.apis['rxnorm']['base_url']}/spellingsuggestions.json",
                    params={'name': term}
                )
                if spell_response.status_code == 200:
                    spell_data = spell_response.json()
                    suggestions = spell_data.get('suggestionGroup', {}).get('suggestionList', {}).get('suggestion', [])
                    # Try searching with first suggestion
                    if suggestions:
                        return self.search_rxnorm(suggestions[0], max_results)
            
            # Limit results
            results = results[:max_results]
            self._save_to_cache(cache_key, results)
            return results
            
        except Exception as e:
            logger.error(f"RxNorm API error: {e}")
            return []
    
    def search_clinical_tables(self, term: str, terminology: str = 'rxterms', max_results: int = 10) -> List[Dict]:
        """Search NIH Clinical Tables API (no authentication required)."""
        cache_key = self._get_cache_key('clinicaltables', terminology, {'terms': term})
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached
        
        try:
            endpoint = self.apis['clinicaltables']['endpoints'].get(terminology)
            if not endpoint:
                return []
            
            response = self.session.get(
                f"{self.apis['clinicaltables']['base_url']}{endpoint}",
                params={
                    'terms': term,
                    'maxList': max_results
                }
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            if len(data) >= 4:  # Clinical Tables returns array format
                items = data[3]  # Fourth element contains the actual results
                for item in items[:max_results]:
                    if terminology == 'rxterms':
                        results.append({
                            'code': item[3] if len(item) > 3 else None,  # RxCUI
                            'display': item[0],  # Display name
                            'system': 'RxNorm',
                            'strength': item[1] if len(item) > 1 else None,
                            'form': item[2] if len(item) > 2 else None
                        })
                    elif terminology == 'loinc':
                        results.append({
                            'code': item[0],  # LOINC code
                            'display': item[1] if len(item) > 1 else item[0],
                            'system': 'LOINC',
                            'component': item[2] if len(item) > 2 else None
                        })
                    elif terminology == 'icd10':
                        results.append({
                            'code': item[0],  # ICD-10 code
                            'display': item[1] if len(item) > 1 else item[0],
                            'system': 'ICD-10-CM'
                        })
                    elif terminology == 'snomed':
                        results.append({
                            'code': item[0],  # SNOMED code
                            'display': item[1] if len(item) > 1 else item[0],
                            'system': 'SNOMED CT'
                        })
            
            self._save_to_cache(cache_key, results)
            return results
            
        except Exception as e:
            logger.error(f"Clinical Tables API error: {e}")
            return []
    
    def search_snomed_browser(self, term: str, max_results: int = 10) -> List[Dict]:
        """Search SNOMED CT using the public browser API."""
        cache_key = self._get_cache_key('snomed', 'search', {'term': term})
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached
        
        try:
            response = self.session.get(
                f"{self.apis['snomed']['base_url']}/descriptions",
                params={
                    'term': term,
                    'active': 'true',
                    'limit': max_results,
                    'lang': 'english'
                },
                headers={'Accept': 'application/json'}
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get('items', []):
                concept = item.get('concept', {})
                results.append({
                    'code': concept.get('conceptId'),
                    'display': item.get('term'),
                    'system': 'SNOMED CT',
                    'fsn': concept.get('fsn', {}).get('term'),
                    'active': item.get('active', True)
                })
            
            self._save_to_cache(cache_key, results)
            return results
            
        except Exception as e:
            logger.error(f"SNOMED Browser API error: {e}")
            return []
    
    def search_loinc_fhir(self, term: str, max_results: int = 10) -> List[Dict]:
        """Search LOINC using FHIR API."""
        cache_key = self._get_cache_key('loinc', 'search', {'term': term})
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached
        
        try:
            # FHIR $lookup operation
            response = self.session.post(
                f"{self.apis['loinc']['base_url']}/CodeSystem/$lookup",
                json={
                    'resourceType': 'Parameters',
                    'parameter': [
                        {
                            'name': 'coding',
                            'valueCoding': {
                                'system': 'http://loinc.org',
                                'display': term
                            }
                        }
                    ]
                },
                headers={'Content-Type': 'application/fhir+json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Parse FHIR Parameters response
                for param in data.get('parameter', []):
                    if param.get('name') == 'display':
                        display = param.get('valueString')
                    elif param.get('name') == 'code':
                        code = param.get('valueCode')
                
                if 'code' in locals() and 'display' in locals():
                    results.append({
                        'code': code,
                        'display': display,
                        'system': 'LOINC'
                    })
                
                self._save_to_cache(cache_key, results)
                return results
            
        except Exception as e:
            logger.error(f"LOINC FHIR API error: {e}")
        
        # Fallback to Clinical Tables LOINC search
        return self.search_clinical_tables(term, 'loinc', max_results)
    
    def get_umls_auth_token(self, api_key: str) -> Optional[str]:
        """Get UMLS authentication token (requires API key)."""
        try:
            response = self.session.post(
                'https://utslogin.nlm.nih.gov/cas/v1/api-key',
                data={'apikey': api_key}
            )
            response.raise_for_status()
            # Parse TGT from response
            # Note: Full UMLS auth implementation requires additional steps
            return response.text
        except Exception as e:
            logger.error(f"UMLS auth error: {e}")
            return None
    
    def search_all(self, term: str, systems: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """Search across multiple terminology systems."""
        if systems is None:
            systems = ['rxnorm', 'snomed', 'loinc', 'icd10']
        
        results = {}
        
        # Search each requested system
        if 'rxnorm' in systems:
            # Try both RxNorm API and Clinical Tables
            rxnorm_results = self.search_rxnorm(term)
            if not rxnorm_results:
                rxnorm_results = self.search_clinical_tables(term, 'rxterms')
            results['rxnorm'] = rxnorm_results
        
        if 'snomed' in systems:
            # Try SNOMED browser API
            snomed_results = self.search_snomed_browser(term)
            if not snomed_results:
                snomed_results = self.search_clinical_tables(term, 'snomed')
            results['snomed'] = snomed_results
        
        if 'loinc' in systems:
            # Try LOINC FHIR API
            loinc_results = self.search_loinc_fhir(term)
            if not loinc_results:
                loinc_results = self.search_clinical_tables(term, 'loinc')
            results['loinc'] = loinc_results
        
        if 'icd10' in systems:
            results['icd10'] = self.search_clinical_tables(term, 'icd10')
        
        return results
    
    def get_concept_details(self, code: str, system: str) -> Optional[Dict]:
        """Get detailed information about a specific concept."""
        if system.lower() == 'rxnorm':
            try:
                response = self.session.get(
                    f"{self.apis['rxnorm']['base_url']}/rxcui/{code}/allrelated.json"
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Error getting RxNorm details: {e}")
        
        elif system.lower() in ['snomed', 'snomed ct']:
            try:
                response = self.session.get(
                    f"{self.apis['snomed']['base_url']}/concepts/{code}",
                    headers={'Accept': 'application/json'}
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Error getting SNOMED details: {e}")
        
        return None