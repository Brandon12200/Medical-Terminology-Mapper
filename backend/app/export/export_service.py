"""
Enhanced export service for batch processing results with entity data
"""
import json
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from uuid import UUID
import logging

from ..processing.document_processor import DocumentProcessor
from ..ml.medical_entity_extractor import MedicalEntityExtractor

logger = logging.getLogger(__name__)

class EnhancedExportService:
    """Service for exporting batch results with detailed entity extraction data"""
    
    def __init__(self, document_processor: DocumentProcessor = None, 
                 entity_extractor: MedicalEntityExtractor = None):
        self.document_processor = document_processor or DocumentProcessor()
        self.entity_extractor = entity_extractor or MedicalEntityExtractor()
        
    def export_batch_with_entities(self,
                                 batch_id: UUID,
                                 documents: List[Dict[str, Any]],
                                 format: str,
                                 include_entities: bool = True,
                                 include_terminology_mappings: bool = True,
                                 include_raw_text: bool = False,
                                 include_confidence_scores: bool = True) -> Optional[str]:
        """
        Export batch results with entity extraction data
        
        Args:
            batch_id: Batch identifier
            documents: List of document records from database
            format: Export format (json, csv, excel)
            include_entities: Include extracted entities
            include_terminology_mappings: Include SNOMED/LOINC/RxNorm mappings
            include_raw_text: Include extracted text
            include_confidence_scores: Include confidence scores
            
        Returns:
            Path to exported file or None if error
        """
        try:
            # Create export directory
            export_dir = Path("exports") / str(batch_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Process documents to get entity data
            enriched_documents = []
            for doc in documents:
                doc_data = self._enrich_document_data(
                    doc, 
                    include_entities=include_entities,
                    include_terminology_mappings=include_terminology_mappings,
                    include_raw_text=include_raw_text,
                    include_confidence_scores=include_confidence_scores
                )
                enriched_documents.append(doc_data)
            
            # Export based on format
            if format.lower() == 'json':
                return self._export_json(export_dir, timestamp, batch_id, enriched_documents)
            elif format.lower() == 'csv':
                return self._export_csv(export_dir, timestamp, enriched_documents, include_entities)
            elif format.lower() == 'excel':
                return self._export_excel(export_dir, timestamp, enriched_documents, include_entities)
            else:
                logger.error(f"Unsupported format: {format}")
                return None
                
        except Exception as e:
            logger.error(f"Error in enhanced export: {e}")
            return None
    
    def _enrich_document_data(self, doc: Dict[str, Any], **options) -> Dict[str, Any]:
        """Enrich document data with entity extraction results"""
        try:
            doc_data = {
                "document_id": doc['document_id'],
                "filename": doc['filename'],
                "status": doc['status'],
                "document_type": doc['document_type'],
                "file_size": doc['file_size'],
                "upload_timestamp": doc.get('upload_timestamp'),
                "processing_time": self._calculate_processing_time(doc)
            }
            
            # Add raw text if requested
            if options.get('include_raw_text') and doc.get('extracted_text'):
                doc_data['extracted_text'] = doc['extracted_text']
            
            # Add entity extraction results if available and requested
            if options.get('include_entities') and doc['status'] == 'completed':
                entities = self._get_or_extract_entities(doc, options.get('include_confidence_scores', True))
                doc_data['entities'] = entities
                
                # Add terminology mappings if requested
                if options.get('include_terminology_mappings'):
                    doc_data['terminology_mappings'] = self._get_terminology_mappings(entities)
                
                # Add entity statistics
                doc_data['entity_statistics'] = self._calculate_entity_statistics(entities)
            
            return doc_data
            
        except Exception as e:
            logger.error(f"Error enriching document {doc.get('document_id')}: {e}")
            return {
                "document_id": doc['document_id'],
                "filename": doc['filename'],
                "status": "error",
                "error": str(e)
            }
    
    def _get_or_extract_entities(self, doc: Dict[str, Any], include_confidence: bool = True) -> List[Dict[str, Any]]:
        """Get entities from cached results or extract them"""
        try:
            # Check if entities are already stored (in a real implementation)
            # For now, we'll extract them from the text if available
            if not doc.get('extracted_text'):
                return []
            
            # Extract entities using BioBERT
            extraction_result = self.entity_extractor.extract_entities(doc['extracted_text'])
            
            entities = []
            for entity in extraction_result.get('entities', []):
                entity_data = {
                    "text": entity.get('text'),
                    "label": entity.get('label'),
                    "start": entity.get('start'),
                    "end": entity.get('end')
                }
                
                if include_confidence:
                    entity_data["confidence"] = entity.get('confidence', 0.0)
                
                entities.append(entity_data)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def _get_terminology_mappings(self, entities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Get terminology mappings for extracted entities"""
        try:
            mappings = {
                "snomed": [],
                "loinc": [],
                "rxnorm": []
            }
            
            # Group entities by type for appropriate terminology mapping
            for entity in entities:
                label = entity.get('label', '').upper()
                text = entity.get('text', '')
                
                if label in ['CONDITION', 'DISEASE', 'SYMPTOM']:
                    # Map to SNOMED CT
                    snomed_mapping = self._map_to_snomed(text)
                    if snomed_mapping:
                        mappings["snomed"].append({
                            "original_text": text,
                            "entity_type": label,
                            **snomed_mapping
                        })
                
                elif label in ['DRUG', 'MEDICATION']:
                    # Map to RxNorm
                    rxnorm_mapping = self._map_to_rxnorm(text)
                    if rxnorm_mapping:
                        mappings["rxnorm"].append({
                            "original_text": text,
                            "entity_type": label,
                            **rxnorm_mapping
                        })
                
                elif label in ['TEST', 'LAB_TEST', 'OBSERVATION']:
                    # Map to LOINC
                    loinc_mapping = self._map_to_loinc(text)
                    if loinc_mapping:
                        mappings["loinc"].append({
                            "original_text": text,
                            "entity_type": label,
                            **loinc_mapping
                        })
            
            return mappings
            
        except Exception as e:
            logger.error(f"Error getting terminology mappings: {e}")
            return {"snomed": [], "loinc": [], "rxnorm": []}
    
    def _map_to_snomed(self, text: str) -> Optional[Dict[str, Any]]:
        """Map text to SNOMED CT (placeholder implementation)"""
        # This would use the existing terminology mapper
        return {
            "code": "123456789",
            "display": f"SNOMED mapping for: {text}",
            "confidence": 0.85
        }
    
    def _map_to_loinc(self, text: str) -> Optional[Dict[str, Any]]:
        """Map text to LOINC (placeholder implementation)"""
        return {
            "code": "LA12345-6",
            "display": f"LOINC mapping for: {text}",
            "confidence": 0.80
        }
    
    def _map_to_rxnorm(self, text: str) -> Optional[Dict[str, Any]]:
        """Map text to RxNorm (placeholder implementation)"""
        return {
            "rxcui": "123456",
            "name": f"RxNorm mapping for: {text}",
            "confidence": 0.82
        }
    
    def _calculate_entity_statistics(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for extracted entities"""
        if not entities:
            return {}
        
        stats = {
            "total_entities": len(entities),
            "entity_types": {},
            "avg_confidence": 0.0,
            "high_confidence_entities": 0
        }
        
        confidences = []
        for entity in entities:
            # Count by type
            label = entity.get('label', 'UNKNOWN')
            stats["entity_types"][label] = stats["entity_types"].get(label, 0) + 1
            
            # Confidence statistics
            confidence = entity.get('confidence', 0.0)
            confidences.append(confidence)
            if confidence > 0.8:
                stats["high_confidence_entities"] += 1
        
        if confidences:
            stats["avg_confidence"] = sum(confidences) / len(confidences)
        
        return stats
    
    def _calculate_processing_time(self, doc: Dict[str, Any]) -> Optional[float]:
        """Calculate processing time for document"""
        try:
            if doc.get('started_at') and doc.get('completed_at'):
                start = datetime.fromisoformat(doc['started_at'])
                end = datetime.fromisoformat(doc['completed_at'])
                return (end - start).total_seconds()
        except:
            pass
        return None
    
    def _export_json(self, export_dir: Path, timestamp: str, batch_id: UUID, documents: List[Dict]) -> str:
        """Export to JSON format"""
        export_file = export_dir / f"enhanced_batch_export_{timestamp}.json"
        
        export_data = {
            "batch_id": str(batch_id),
            "export_timestamp": datetime.utcnow().isoformat(),
            "export_type": "enhanced_with_entities",
            "total_documents": len(documents),
            "documents": documents,
            "batch_statistics": self._calculate_batch_statistics(documents)
        }
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return str(export_file)
    
    def _export_csv(self, export_dir: Path, timestamp: str, documents: List[Dict], include_entities: bool) -> str:
        """Export to CSV format"""
        if include_entities:
            # Create separate files for documents and entities
            doc_file = export_dir / f"documents_{timestamp}.csv"
            entity_file = export_dir / f"entities_{timestamp}.csv"
            
            # Export documents
            doc_rows = []
            entity_rows = []
            
            for doc in documents:
                doc_row = {
                    'document_id': doc['document_id'],
                    'filename': doc['filename'],
                    'status': doc['status'],
                    'document_type': doc['document_type'],
                    'file_size': doc['file_size'],
                    'processing_time': doc.get('processing_time'),
                    'total_entities': doc.get('entity_statistics', {}).get('total_entities', 0),
                    'avg_confidence': doc.get('entity_statistics', {}).get('avg_confidence', 0.0)
                }
                doc_rows.append(doc_row)
                
                # Add entities to separate rows
                for entity in doc.get('entities', []):
                    entity_row = {
                        'document_id': doc['document_id'],
                        'entity_text': entity.get('text'),
                        'entity_type': entity.get('label'),
                        'start_pos': entity.get('start'),
                        'end_pos': entity.get('end'),
                        'confidence': entity.get('confidence', 0.0)
                    }
                    entity_rows.append(entity_row)
            
            # Write documents CSV
            if doc_rows:
                with open(doc_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=doc_rows[0].keys())
                    writer.writeheader()
                    writer.writerows(doc_rows)
            
            # Write entities CSV
            if entity_rows:
                with open(entity_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=entity_rows[0].keys())
                    writer.writeheader()
                    writer.writerows(entity_rows)
            
            return str(doc_file)  # Return main file
        else:
            # Simple document export
            export_file = export_dir / f"batch_export_{timestamp}.csv"
            rows = []
            for doc in documents:
                row = {
                    'document_id': doc['document_id'],
                    'filename': doc['filename'],
                    'status': doc['status'],
                    'document_type': doc['document_type'],
                    'file_size': doc['file_size'],
                    'processing_time': doc.get('processing_time')
                }
                rows.append(row)
            
            if rows:
                with open(export_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
            
            return str(export_file)
    
    def _export_excel(self, export_dir: Path, timestamp: str, documents: List[Dict], include_entities: bool) -> str:
        """Export to Excel format with multiple sheets"""
        export_file = export_dir / f"enhanced_batch_export_{timestamp}.xlsx"
        
        with pd.ExcelWriter(export_file, engine='openpyxl') as writer:
            # Documents sheet
            doc_data = []
            for doc in documents:
                doc_data.append({
                    'Document ID': doc['document_id'],
                    'Filename': doc['filename'],
                    'Status': doc['status'],
                    'Type': doc['document_type'],
                    'Size (bytes)': doc['file_size'],
                    'Processing Time (s)': doc.get('processing_time'),
                    'Total Entities': doc.get('entity_statistics', {}).get('total_entities', 0),
                    'Avg Confidence': doc.get('entity_statistics', {}).get('avg_confidence', 0.0)
                })
            
            df_docs = pd.DataFrame(doc_data)
            df_docs.to_excel(writer, sheet_name='Documents', index=False)
            
            # Entities sheet (if requested)
            if include_entities:
                entity_data = []
                for doc in documents:
                    for entity in doc.get('entities', []):
                        entity_data.append({
                            'Document ID': doc['document_id'],
                            'Document Name': doc['filename'],
                            'Entity Text': entity.get('text'),
                            'Entity Type': entity.get('label'),
                            'Start Position': entity.get('start'),
                            'End Position': entity.get('end'),
                            'Confidence': entity.get('confidence', 0.0)
                        })
                
                if entity_data:
                    df_entities = pd.DataFrame(entity_data)
                    df_entities.to_excel(writer, sheet_name='Entities', index=False)
                
                # Terminology mappings sheet
                mapping_data = []
                for doc in documents:
                    mappings = doc.get('terminology_mappings', {})
                    for terminology, maps in mappings.items():
                        for mapping in maps:
                            mapping_data.append({
                                'Document ID': doc['document_id'],
                                'Original Text': mapping.get('original_text'),
                                'Entity Type': mapping.get('entity_type'),
                                'Terminology': terminology.upper(),
                                'Code': mapping.get('code') or mapping.get('rxcui'),
                                'Display': mapping.get('display') or mapping.get('name'),
                                'Confidence': mapping.get('confidence', 0.0)
                            })
                
                if mapping_data:
                    df_mappings = pd.DataFrame(mapping_data)
                    df_mappings.to_excel(writer, sheet_name='Terminology Mappings', index=False)
        
        return str(export_file)
    
    def _calculate_batch_statistics(self, documents: List[Dict]) -> Dict[str, Any]:
        """Calculate overall batch statistics"""
        total_docs = len(documents)
        completed_docs = sum(1 for doc in documents if doc['status'] == 'completed')
        failed_docs = sum(1 for doc in documents if doc['status'] == 'failed')
        
        total_entities = sum(doc.get('entity_statistics', {}).get('total_entities', 0) for doc in documents)
        
        # Calculate average confidence
        all_confidences = []
        for doc in documents:
            for entity in doc.get('entities', []):
                confidence = entity.get('confidence')
                if confidence is not None:
                    all_confidences.append(confidence)
        
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        
        return {
            "total_documents": total_docs,
            "completed_documents": completed_docs,
            "failed_documents": failed_docs,
            "success_rate": (completed_docs / total_docs * 100) if total_docs > 0 else 0,
            "total_entities_extracted": total_entities,
            "average_confidence": avg_confidence,
            "entities_per_document": total_entities / completed_docs if completed_docs > 0 else 0
        }