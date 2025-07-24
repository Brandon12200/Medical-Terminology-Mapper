#!/usr/bin/env python3
"""
Medical Terminology Mapper - Usage Examples

This script demonstrates how to use the Medical Terminology Mapper API
for various medical document processing and entity extraction tasks.
"""

import requests
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
DEMO_DOCS_PATH = Path(__file__).parent / "sample_documents"

class MedicalTerminologyMapperClient:
    """Simple client for the Medical Terminology Mapper API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
        
    def health_check(self) -> Dict[str, Any]:
        """Check if the API is healthy"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
        
    def upload_document(self, file_path: Path) -> Dict[str, Any]:
        """Upload a single document for processing"""
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'text/plain')}
            response = requests.post(
                f"{self.base_url}/api/v1/documents/upload",
                files=files
            )
        response.raise_for_status()
        return response.json()
        
    def upload_batch_documents(self, file_paths: List[Path]) -> Dict[str, Any]:
        """Upload multiple documents for batch processing"""
        files = []
        file_handles = []
        
        try:
            for file_path in file_paths:
                f = open(file_path, 'rb')
                file_handles.append(f)
                files.append(('files', (file_path.name, f, 'text/plain')))
            
            response = requests.post(
                f"{self.base_url}/api/v1/documents/batch/upload",
                files=files
            )
            response.raise_for_status()
            return response.json()
            
        finally:
            # Close all file handles
            for f in file_handles:
                f.close()
                
    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """Get the processing status of a document"""
        response = requests.get(
            f"{self.base_url}/api/v1/documents/{document_id}/status"
        )
        response.raise_for_status()
        return response.json()
        
    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """Get the processing status of a batch"""
        response = requests.get(
            f"{self.base_url}/api/v1/documents/batch/{batch_id}/status"
        )
        response.raise_for_status()
        return response.json()
        
    def extract_entities(self, document_id: str, 
                        include_terminology: bool = True) -> Dict[str, Any]:
        """Extract entities from a processed document"""
        params = {'include_terminology_mappings': include_terminology}
        response = requests.post(
            f"{self.base_url}/api/v1/documents/{document_id}/extract-entities",
            params=params
        )
        response.raise_for_status()
        return response.json()
        
    def get_batch_results(self, batch_id: str, 
                         include_text: bool = False) -> Dict[str, Any]:
        """Get results from a completed batch"""
        params = {'include_raw_text': include_text}
        response = requests.get(
            f"{self.base_url}/api/v1/documents/batch/{batch_id}/results",
            params=params
        )
        response.raise_for_status()
        return response.json()
        
    def export_batch_results(self, batch_id: str, format: str = 'json') -> bytes:
        """Export batch results in specified format"""
        response = requests.get(
            f"{self.base_url}/api/v1/documents/batch/{batch_id}/export/{format}"
        )
        response.raise_for_status()
        return response.content
        
    def map_term(self, term: str, context: str = "", 
                 systems: List[str] = None) -> Dict[str, Any]:
        """Map a single medical term to standard terminologies"""
        if systems is None:
            systems = ["snomed", "loinc", "rxnorm"]
            
        data = {
            "term": term,
            "context": context,
            "target_systems": systems
        }
        response = requests.post(
            f"{self.base_url}/api/v1/terminology/map",
            json=data
        )
        response.raise_for_status()
        return response.json()

def wait_for_completion(client: MedicalTerminologyMapperClient, 
                       batch_id: str, timeout: int = 300) -> Dict[str, Any]:
    """Wait for batch processing to complete"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status = client.get_batch_status(batch_id)
        print(f"Progress: {status['progress_percentage']:.1f}% "
              f"({status['processed_documents']}/{status['total_documents']})")
        
        if status['status'] in ['completed', 'failed']:
            return status
            
        time.sleep(5)
    
    raise TimeoutError("Batch processing timed out")

def example_1_health_check():
    """Example 1: Basic health check"""
    print("=== Example 1: Health Check ===")
    
    client = MedicalTerminologyMapperClient()
    
    try:
        health = client.health_check()
        print(f"✅ API is healthy: {health}")
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False
    
    return True

def example_2_single_document_processing():
    """Example 2: Process a single medical document"""
    print("\n=== Example 2: Single Document Processing ===")
    
    client = MedicalTerminologyMapperClient()
    doc_path = DEMO_DOCS_PATH / "clinical_note_example.txt"
    
    if not doc_path.exists():
        print(f"❌ Demo document not found: {doc_path}")
        return
    
    try:
        # Upload document
        print(f"📄 Uploading document: {doc_path.name}")
        upload_result = client.upload_document(doc_path)
        document_id = upload_result['document_id']
        print(f"✅ Document uploaded with ID: {document_id}")
        
        # Wait for processing (in real implementation, would poll status)
        print("⏳ Waiting for processing...")
        time.sleep(2)  # Simulate processing time
        
        # Extract entities
        print("🔍 Extracting entities...")
        entities_result = client.extract_entities(document_id)
        
        print(f"📊 Found {len(entities_result.get('entities', []))} entities")
        
        # Display sample entities
        for entity in entities_result.get('entities', [])[:5]:  # First 5 entities
            print(f"  • {entity['text']} ({entity['label']}) - "
                  f"Confidence: {entity.get('confidence', 0):.2f}")
                  
        # Display terminology mappings
        mappings = entities_result.get('terminology_mappings', {})
        for system, maps in mappings.items():
            if maps:
                print(f"🏥 {system.upper()} mappings: {len(maps)}")
                for mapping in maps[:3]:  # First 3 mappings
                    code = mapping.get('code') or mapping.get('rxcui')
                    display = mapping.get('display') or mapping.get('name')
                    print(f"  • {mapping['original_text']} → {code}: {display}")
        
    except Exception as e:
        print(f"❌ Single document processing failed: {e}")

def example_3_batch_processing():
    """Example 3: Batch processing of multiple documents"""
    print("\n=== Example 3: Batch Document Processing ===")
    
    client = MedicalTerminologyMapperClient()
    
    # Collect all demo documents
    demo_files = list(DEMO_DOCS_PATH.glob("*.txt"))
    if not demo_files:
        print("❌ No demo documents found")
        return
    
    try:
        # Upload batch
        print(f"📄 Uploading {len(demo_files)} documents for batch processing...")
        batch_result = client.upload_batch_documents(demo_files)
        batch_id = batch_result['batch_id']
        print(f"✅ Batch uploaded with ID: {batch_id}")
        
        # Monitor progress
        print("⏳ Monitoring batch processing...")
        final_status = wait_for_completion(client, batch_id, timeout=120)
        
        if final_status['status'] == 'completed':
            print("✅ Batch processing completed successfully!")
            
            # Get results
            print("📊 Retrieving batch results...")
            results = client.get_batch_results(batch_id)
            
            # Display summary
            stats = results.get('batch_statistics', {})
            print(f"📈 Batch Statistics:")
            print(f"  • Total documents: {stats.get('total_documents', 0)}")
            print(f"  • Success rate: {stats.get('success_rate', 0):.1f}%")
            print(f"  • Total entities extracted: {stats.get('total_entities_extracted', 0)}")
            print(f"  • Average confidence: {stats.get('average_confidence', 0):.2f}")
            
            # Export results
            print("💾 Exporting results...")
            json_export = client.export_batch_results(batch_id, 'json')
            
            export_path = Path('batch_results.json')
            with open(export_path, 'wb') as f:
                f.write(json_export)
            print(f"✅ Results exported to {export_path}")
            
        else:
            print(f"❌ Batch processing failed: {final_status}")
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")

def example_4_terminology_mapping():
    """Example 4: Direct terminology mapping"""
    print("\n=== Example 4: Direct Terminology Mapping ===")
    
    client = MedicalTerminologyMapperClient()
    
    # Sample medical terms to map
    terms = [
        ("diabetes", "diagnosis"),
        ("metformin", "medication"),
        ("blood glucose", "lab test"),
        ("hypertension", "condition"),
        ("chest pain", "symptom")
    ]
    
    try:
        for term, context in terms:
            print(f"\n🔍 Mapping term: '{term}' (context: {context})")
            
            mapping_result = client.map_term(term, context)
            mappings = mapping_result.get('mappings', [])
            
            if mappings:
                for mapping in mappings:
                    system = mapping['system'].upper()
                    code = mapping['code']
                    display = mapping['display']
                    confidence = mapping['confidence']
                    print(f"  • {system}: {code} - {display} (confidence: {confidence:.2f})")
            else:
                print("  • No mappings found")
                
    except Exception as e:
        print(f"❌ Terminology mapping failed: {e}")

def example_5_entity_analysis():
    """Example 5: Analyze entity extraction results"""
    print("\n=== Example 5: Entity Analysis ===")
    
    # This would typically use results from previous examples
    # For demo purposes, we'll show how to analyze entity data
    
    sample_entities = [
        {"text": "diabetes mellitus", "label": "CONDITION", "confidence": 0.95},
        {"text": "metformin", "label": "DRUG", "confidence": 0.88},
        {"text": "blood pressure", "label": "OBSERVATION", "confidence": 0.92},
        {"text": "chest X-ray", "label": "TEST", "confidence": 0.87},
        {"text": "heart", "label": "ANATOMY", "confidence": 0.94},
    ]
    
    print("📊 Entity Analysis:")
    
    # Group by entity type
    entity_types = {}
    total_confidence = 0
    
    for entity in sample_entities:
        entity_type = entity['label']
        if entity_type not in entity_types:
            entity_types[entity_type] = []
        entity_types[entity_type].append(entity)
        total_confidence += entity['confidence']
    
    # Display analysis
    print(f"📈 Summary:")
    print(f"  • Total entities: {len(sample_entities)}")
    print(f"  • Average confidence: {total_confidence / len(sample_entities):.2f}")
    print(f"  • Entity types: {len(entity_types)}")
    
    print("\n🏷️ Entities by type:")
    for entity_type, entities in entity_types.items():
        print(f"  • {entity_type}: {len(entities)} entities")
        for entity in entities:
            print(f"    - {entity['text']} (confidence: {entity['confidence']:.2f})")

def main():
    """Run all examples"""
    print("🏥 Medical Terminology Mapper - Usage Examples")
    print("=" * 50)
    
    # Check if API is available
    if not example_1_health_check():
        print("\n❌ API is not available. Please start the service first:")
        print("   docker-compose up -d")
        print("   # or")
        print("   cd backend && python -m uvicorn api.main:app --reload")
        return
    
    # Run examples
    example_2_single_document_processing()
    example_3_batch_processing()
    example_4_terminology_mapping()
    example_5_entity_analysis()
    
    print("\n✅ All examples completed!")
    print("\n📚 Next steps:")
    print("  • Explore the interactive API docs: http://localhost:8000/docs")
    print("  • Try the web interface: http://localhost:3000")
    print("  • Review the exported results files")

if __name__ == "__main__":
    main()