import sys
import os
from typing import List, Dict, Optional, Any
import asyncio
import json
import csv
import pandas as pd
from datetime import datetime
import uuid
from fastapi import BackgroundTasks, UploadFile
import aiofiles
import time

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.v1.models.batch import (
    BatchJobRequest, BatchJobStatus, BatchJobResult,
    BatchStatus, FileFormat
)
from api.v1.models.terminology import BatchMappingRequest, BatchMappingResponse, MappingResponse
from api.v1.services.terminology_service import TerminologyService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class BatchService:
    def __init__(self):
        """Initialize the batch service."""
        self.terminology_service = TerminologyService()
        self.jobs: Dict[str, BatchJobStatus] = {}  # In-memory job storage
        self.job_results: Dict[str, Any] = {}  # In-memory results storage
        
        # Create directories for file storage
        self.upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")
        self.results_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "results")
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)

    async def batch_map_terms(self, request: BatchMappingRequest) -> BatchMappingResponse:
        """
        Process batch mapping request synchronously.
        """
        start_time = time.time()
        
        try:
            # Map all terms
            results = await self.terminology_service.batch_map_terms(
                terms=request.terms,
                systems=[s.value for s in request.systems] if request.systems else ["all"],
                context=request.context,
                fuzzy_threshold=request.fuzzy_threshold,
                fuzzy_algorithms=[a.value for a in request.fuzzy_algorithms] if request.fuzzy_algorithms else ["all"],
                max_results_per_term=request.max_results_per_term
            )
            
            # Process results
            mapping_responses = []
            successful = 0
            failed = 0
            
            for result in results:
                term = result["term"]
                term_results = result.get("results", {})
                error = result.get("error")
                
                if error:
                    failed += 1
                else:
                    total_matches = sum(len(mappings) for mappings in term_results.values())
                    if total_matches > 0:
                        successful += 1
                    else:
                        failed += 1
                
                # Create mapping response
                response = MappingResponse(
                    term=term,
                    results=term_results,
                    total_matches=sum(len(mappings) for mappings in term_results.values()),
                    processing_time_ms=0  # Individual times not tracked in batch
                )
                mapping_responses.append(response)
            
            total_time = (time.time() - start_time) * 1000
            
            return BatchMappingResponse(
                results=mapping_responses,
                total_terms=len(request.terms),
                successful_mappings=successful,
                failed_mappings=failed,
                total_processing_time_ms=round(total_time, 2)
            )
            
        except Exception as e:
            logger.error(f"Error in batch mapping: {str(e)}", exc_info=True)
            raise

    async def create_batch_job(
        self,
        request: BatchJobRequest,
        file: UploadFile,
        background_tasks: BackgroundTasks
    ) -> BatchJobStatus:
        """
        Create a new batch processing job.
        """
        try:
            # Save uploaded file
            file_path = os.path.join(self.upload_dir, f"{request.job_id}_{file.filename}")
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Parse file to count terms
            terms = await self._parse_file(file_path, request.file_format, request.column_name)
            
            # Create job status
            job_status = BatchJobStatus(
                job_id=request.job_id,
                status=BatchStatus.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                total_terms=len(terms),
                processed_terms=0,
                successful_mappings=0,
                failed_mappings=0,
                progress_percentage=0.0
            )
            
            # Store job status
            self.jobs[request.job_id] = job_status
            
            # Add background task to process the job
            background_tasks.add_task(
                self._process_batch_job,
                request.job_id,
                terms,
                request
            )
            
            return job_status
            
        except Exception as e:
            logger.error(f"Error creating batch job: {str(e)}", exc_info=True)
            raise

    async def _parse_file(
        self,
        file_path: str,
        file_format: FileFormat,
        column_name: str
    ) -> List[str]:
        """Parse uploaded file and extract terms."""
        try:
            if file_format == FileFormat.CSV:
                df = pd.read_csv(file_path)
                if column_name not in df.columns:
                    raise ValueError(f"Column '{column_name}' not found in CSV file")
                return df[column_name].dropna().tolist()
                
            elif file_format == FileFormat.JSON:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    # Assume list of strings or list of dicts with 'term' key
                    if all(isinstance(item, str) for item in data):
                        return data
                    elif all(isinstance(item, dict) and 'term' in item for item in data):
                        return [item['term'] for item in data]
                    else:
                        raise ValueError("JSON must be a list of strings or objects with 'term' key")
                else:
                    raise ValueError("JSON must be a list")
                    
            elif file_format == FileFormat.EXCEL:
                df = pd.read_excel(file_path)
                if column_name not in df.columns:
                    raise ValueError(f"Column '{column_name}' not found in Excel file")
                return df[column_name].dropna().tolist()
                
            elif file_format == FileFormat.TXT:
                with open(file_path, 'r') as f:
                    return [line.strip() for line in f if line.strip()]
                    
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
                
        except Exception as e:
            logger.error(f"Error parsing file: {str(e)}")
            raise

    async def _process_batch_job(
        self,
        job_id: str,
        terms: List[str],
        request: BatchJobRequest
    ):
        """Process batch job in background."""
        try:
            # Update job status to processing
            job = self.jobs[job_id]
            job.status = BatchStatus.PROCESSING
            job.updated_at = datetime.utcnow()
            
            # Process terms in smaller batches with progress updates
            batch_size = 10  # Process 10 terms at a time for better progress granularity
            all_results = []
            
            for i in range(0, len(terms), batch_size):
                batch_terms = terms[i:i + batch_size]
                
                # Create batch request
                batch_request = BatchMappingRequest(
                    terms=batch_terms,
                    systems=request.systems,
                    context=request.context,
                    fuzzy_threshold=request.fuzzy_threshold,
                    fuzzy_algorithms=request.fuzzy_algorithms,
                    max_results_per_term=request.max_results_per_term
                )
                
                # Process batch
                batch_response = await self.batch_map_terms(batch_request)
                
                # Update progress after each small batch
                job.processed_terms += len(batch_terms)
                job.successful_mappings += batch_response.successful_mappings
                job.failed_mappings += batch_response.failed_mappings
                job.progress_percentage = (job.processed_terms / job.total_terms) * 100
                job.updated_at = datetime.utcnow()
                
                # Store results - convert TermMapping objects to dicts
                for result in batch_response.results:
                    # Convert TermMapping objects to dictionaries for JSON serialization
                    serializable_mappings = {}
                    for system, mappings in result.results.items():
                        serializable_mappings[system] = [
                            mapping.model_dump() if hasattr(mapping, 'model_dump') else mapping
                            for mapping in mappings
                        ]
                    
                    all_results.append({
                        "original_term": result.term,
                        "mappings": serializable_mappings,
                        "total_matches": result.total_matches
                    })
            
            # Save results
            await self._save_results(job_id, all_results)
            
            # Update job status to completed
            job.status = BatchStatus.COMPLETED
            job.updated_at = datetime.utcnow()
            
            # Store results reference
            self.job_results[job_id] = {
                "results": all_results,
                "summary": {
                    "total_terms": job.total_terms,
                    "successful_mappings": job.successful_mappings,
                    "failed_mappings": job.failed_mappings,
                    "processing_time_seconds": (job.updated_at - job.created_at).total_seconds()
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing batch job {job_id}: {str(e)}", exc_info=True)
            job = self.jobs[job_id]
            job.status = BatchStatus.FAILED
            job.error_message = str(e)
            job.updated_at = datetime.utcnow()

    async def _save_results(self, job_id: str, results: List[Dict]):
        """Save results in multiple formats."""
        try:
            # Save as JSON
            json_path = os.path.join(self.results_dir, f"{job_id}.json")
            async with aiofiles.open(json_path, 'w') as f:
                await f.write(json.dumps(results, indent=2))
            
            # Save as CSV
            csv_path = os.path.join(self.results_dir, f"{job_id}.csv")
            
            # Flatten results for CSV
            csv_rows = []
            for result in results:
                term = result["original_term"]
                mappings = result["mappings"]
                
                if not mappings:
                    csv_rows.append({
                        "original_term": term,
                        "system": "",
                        "code": "",
                        "display": "",
                        "confidence": "",
                        "match_type": ""
                    })
                else:
                    for system, system_mappings in mappings.items():
                        for mapping in system_mappings:
                            csv_rows.append({
                                "original_term": term,
                                "system": system,
                                "code": mapping["code"],
                                "display": mapping["display"],
                                "confidence": mapping["confidence"],
                                "match_type": mapping["match_type"]
                            })
            
            # Write CSV
            if csv_rows:
                df = pd.DataFrame(csv_rows)
                df.to_csv(csv_path, index=False)
                
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            raise

    async def get_job_status(self, job_id: str) -> Optional[BatchJobStatus]:
        """Get job status by ID."""
        return self.jobs.get(job_id)

    async def get_job_results(
        self,
        job_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> Optional[BatchJobResult]:
        """Get job results by ID."""
        job = self.jobs.get(job_id)
        if not job or job.status != BatchStatus.COMPLETED:
            return None
        
        results_data = self.job_results.get(job_id)
        if not results_data:
            return None
        
        # Apply pagination
        all_results = results_data["results"]
        paginated_results = all_results[offset:offset + limit]
        
        return BatchJobResult(
            job_id=job_id,
            status=job.status,
            results=paginated_results,
            summary=results_data["summary"],
            download_formats={
                "csv": f"/api/v1/batch/download/{job_id}.csv",
                "json": f"/api/v1/batch/download/{job_id}.json"
            }
        )

    async def get_result_file(self, job_id: str, format: str) -> Optional[str]:
        """Get path to result file."""
        file_path = os.path.join(self.results_dir, f"{job_id}.{format}")
        if os.path.exists(file_path):
            return file_path
        return None