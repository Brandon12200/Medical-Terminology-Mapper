import asyncio
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import aiokafka
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError
import hl7
from hl7.mllp import open_hl7_connection
import redis.asyncio as redis
from dataclasses import dataclass, asdict
import uuid
from enum import Enum
import logging
from app.utils.logger import get_logger
from app.models.ai_models import AdvancedMedicalAI, ProcessingMode
from app.standards.terminology.mapper import TerminologyMapper

logger = get_logger(__name__)


class MessageType(Enum):
    """Healthcare message types"""
    HL7_V2 = "hl7_v2"
    HL7_V3 = "hl7_v3"
    FHIR = "fhir"
    DICOM = "dicom"
    X12 = "x12"
    CUSTOM = "custom"
    CDA = "cda"
    CCDA = "ccda"


class ProcessingStatus(Enum):
    """Message processing status"""
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class HealthcareMessage:
    """Unified healthcare message format"""
    id: str
    type: MessageType
    source_system: str
    timestamp: datetime
    patient_id: Optional[str]
    encounter_id: Optional[str]
    content: Any
    metadata: Dict[str, Any]
    status: ProcessingStatus
    processed_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0


@dataclass
class StreamConfig:
    """Streaming configuration"""
    kafka_brokers: List[str]
    redis_url: str
    input_topics: List[str]
    output_topics: Dict[str, str]
    consumer_group: str
    batch_size: int = 100
    batch_timeout_ms: int = 5000
    max_retries: int = 3
    enable_deduplication: bool = True
    enable_ordering: bool = True
    checkpoint_interval_ms: int = 60000


class HealthcareStreamProcessor:
    """Production-grade healthcare data stream processor with AI capabilities"""
    
    def __init__(self, config: StreamConfig, ai_model: AdvancedMedicalAI, terminology_mapper: TerminologyMapper):
        self.config = config
        self.ai_model = ai_model
        self.terminology_mapper = terminology_mapper
        
        # Kafka components
        self.consumer = None
        self.producer = None
        
        # Redis for caching and deduplication
        self.redis_client = None
        
        # Processing metrics
        self.metrics = {
            "messages_processed": 0,
            "messages_failed": 0,
            "avg_latency_ms": 0,
            "throughput_per_sec": 0
        }
        
        # Message handlers
        self.handlers: Dict[MessageType, Callable] = {
            MessageType.HL7_V2: self._process_hl7_v2,
            MessageType.FHIR: self._process_fhir,
            MessageType.CDA: self._process_cda,
            MessageType.CUSTOM: self._process_custom
        }
        
        # Processing pipeline stages
        self.pipeline_stages = [
            self._validate_message,
            self._deduplicate_message,
            self._parse_message,
            self._extract_clinical_data,
            self._apply_ai_processing,
            self._map_terminologies,
            self._apply_business_rules,
            self._transform_output
        ]
        
    async def initialize(self):
        """Initialize streaming components"""
        try:
            # Initialize Kafka consumer
            self.consumer = AIOKafkaConsumer(
                *self.config.input_topics,
                bootstrap_servers=','.join(self.config.kafka_brokers),
                group_id=self.config.consumer_group,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                enable_auto_commit=False,
                auto_offset_reset='earliest',
                max_poll_records=self.config.batch_size
            )
            
            # Initialize Kafka producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=','.join(self.config.kafka_brokers),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                compression_type='gzip',
                acks='all',
                retries=3
            )
            
            # Initialize Redis
            self.redis_client = await redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Start consumer and producer
            await self.consumer.start()
            await self.producer.start()
            
            logger.info("Healthcare stream processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize stream processor: {e}")
            raise
    
    async def start_processing(self):
        """Start processing healthcare data streams"""
        logger.info("Starting healthcare stream processing...")
        
        checkpoint_task = asyncio.create_task(self._periodic_checkpoint())
        metrics_task = asyncio.create_task(self._update_metrics())
        
        try:
            while True:
                # Fetch batch of messages
                batch = await self._fetch_batch()
                
                if batch:
                    # Process batch in parallel
                    await self._process_batch(batch)
                    
                    # Commit offsets after successful processing
                    await self.consumer.commit()
                    
        except asyncio.CancelledError:
            logger.info("Stream processing cancelled")
        except Exception as e:
            logger.error(f"Stream processing error: {e}")
            raise
        finally:
            checkpoint_task.cancel()
            metrics_task.cancel()
            await self.shutdown()
    
    async def _fetch_batch(self) -> List[HealthcareMessage]:
        """Fetch batch of messages from Kafka"""
        messages = []
        
        try:
            # Poll for messages with timeout
            records = await self.consumer.getmany(
                timeout_ms=self.config.batch_timeout_ms,
                max_records=self.config.batch_size
            )
            
            for topic_partition, record_list in records.items():
                for record in record_list:
                    try:
                        # Convert Kafka record to HealthcareMessage
                        message = self._kafka_record_to_message(record)
                        messages.append(message)
                    except Exception as e:
                        logger.error(f"Failed to parse message: {e}")
                        self.metrics["messages_failed"] += 1
            
        except KafkaError as e:
            logger.error(f"Kafka fetch error: {e}")
        
        return messages
    
    async def _process_batch(self, messages: List[HealthcareMessage]):
        """Process batch of messages through the pipeline"""
        
        # Group messages by type for optimized processing
        grouped = self._group_messages_by_type(messages)
        
        # Process each group in parallel
        tasks = []
        for msg_type, group_messages in grouped.items():
            if msg_type in self.handlers:
                task = asyncio.create_task(
                    self._process_message_group(msg_type, group_messages)
                )
                tasks.append(task)
        
        # Wait for all groups to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch processing error: {result}")
    
    async def _process_message_group(self, msg_type: MessageType, messages: List[HealthcareMessage]):
        """Process group of messages of the same type"""
        
        handler = self.handlers[msg_type]
        
        # Process messages through pipeline
        for message in messages:
            try:
                # Update status
                message.status = ProcessingStatus.PROCESSING
                
                # Run through pipeline stages
                for stage in self.pipeline_stages:
                    message = await stage(message)
                    if message is None:
                        break
                
                if message:
                    # Type-specific processing
                    message = await handler(message)
                    
                    # Send to output topic
                    await self._send_to_output(message)
                    
                    # Update metrics
                    self.metrics["messages_processed"] += 1
                    message.status = ProcessingStatus.COMPLETED
                    
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                message.status = ProcessingStatus.FAILED
                message.error = str(e)
                
                # Handle retry logic
                if message.retry_count < self.config.max_retries:
                    await self._retry_message(message)
                else:
                    await self._send_to_dlq(message)
    
    async def _validate_message(self, message: HealthcareMessage) -> Optional[HealthcareMessage]:
        """Validate message structure and content"""
        
        # Basic validation
        if not message.content:
            message.error = "Empty message content"
            return None
        
        # Type-specific validation
        if message.type == MessageType.HL7_V2:
            if not self._validate_hl7_v2(message.content):
                message.error = "Invalid HL7 v2 message"
                return None
        
        elif message.type == MessageType.FHIR:
            if not self._validate_fhir(message.content):
                message.error = "Invalid FHIR resource"
                return None
        
        return message
    
    async def _deduplicate_message(self, message: HealthcareMessage) -> Optional[HealthcareMessage]:
        """Deduplicate messages using Redis"""
        
        if not self.config.enable_deduplication:
            return message
        
        # Create deduplication key
        dedup_key = f"dedup:{message.source_system}:{message.id}"
        
        # Check if message was already processed
        if await self.redis_client.exists(dedup_key):
            logger.debug(f"Duplicate message detected: {message.id}")
            return None
        
        # Mark message as processed (with TTL)
        await self.redis_client.setex(dedup_key, 86400, "1")  # 24 hour TTL
        
        return message
    
    async def _parse_message(self, message: HealthcareMessage) -> HealthcareMessage:
        """Parse message content based on type"""
        
        if message.type == MessageType.HL7_V2:
            parsed = hl7.parse(message.content)
            message.metadata["parsed_hl7"] = self._hl7_to_dict(parsed)
            
            # Extract patient and encounter IDs
            try:
                message.patient_id = str(parsed.segment('PID')[3][0])
                if 'PV1' in str(parsed):
                    message.encounter_id = str(parsed.segment('PV1')[19])
            except:
                pass
        
        elif message.type == MessageType.FHIR:
            # FHIR is already JSON
            if isinstance(message.content, str):
                message.content = json.loads(message.content)
            
            # Extract identifiers
            if message.content.get('resourceType') == 'Patient':
                message.patient_id = message.content.get('id')
        
        return message
    
    async def _extract_clinical_data(self, message: HealthcareMessage) -> HealthcareMessage:
        """Extract clinical data from parsed message"""
        
        clinical_data = {
            "conditions": [],
            "medications": [],
            "procedures": [],
            "observations": [],
            "lab_results": []
        }
        
        if message.type == MessageType.HL7_V2:
            # Extract from HL7 segments
            parsed_hl7 = message.metadata.get("parsed_hl7", {})
            
            # Extract diagnoses from DG1 segments
            if "DG1" in parsed_hl7:
                for diag in parsed_hl7["DG1"]:
                    clinical_data["conditions"].append({
                        "code": diag.get("diagnosis_code"),
                        "text": diag.get("diagnosis_description"),
                        "type": diag.get("diagnosis_type")
                    })
            
            # Extract observations from OBX segments
            if "OBX" in parsed_hl7:
                for obs in parsed_hl7["OBX"]:
                    clinical_data["observations"].append({
                        "code": obs.get("observation_identifier"),
                        "value": obs.get("observation_value"),
                        "units": obs.get("units"),
                        "status": obs.get("observation_result_status")
                    })
        
        elif message.type == MessageType.FHIR:
            # Extract from FHIR resources
            resource = message.content
            resource_type = resource.get('resourceType')
            
            if resource_type == 'Condition':
                clinical_data["conditions"].append({
                    "code": resource.get('code', {}).get('coding', [{}])[0].get('code'),
                    "text": resource.get('code', {}).get('text'),
                    "status": resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code')
                })
            
            elif resource_type == 'MedicationRequest':
                clinical_data["medications"].append({
                    "code": resource.get('medicationCodeableConcept', {}).get('coding', [{}])[0].get('code'),
                    "text": resource.get('medicationCodeableConcept', {}).get('text'),
                    "dosage": resource.get('dosageInstruction', [{}])[0].get('text')
                })
        
        message.metadata["clinical_data"] = clinical_data
        return message
    
    async def _apply_ai_processing(self, message: HealthcareMessage) -> HealthcareMessage:
        """Apply AI processing to extract additional insights"""
        
        # Extract narrative text for AI processing
        narrative_text = self._extract_narrative_text(message)
        
        if narrative_text:
            # Process with AI model
            clinical_doc = await self.ai_model.process_clinical_document(
                text=narrative_text,
                metadata=message.metadata,
                mode=ProcessingMode.STREAMING
            )
            
            # Merge AI-extracted entities with structured data
            clinical_data = message.metadata.get("clinical_data", {})
            
            for entity in clinical_doc.entities:
                if entity.type == "CONDITION" and entity.confidence > 0.8:
                    clinical_data["conditions"].append({
                        "text": entity.text,
                        "ai_extracted": True,
                        "confidence": entity.confidence,
                        "negated": entity.negated
                    })
                elif entity.type == "MEDICATION" and entity.confidence > 0.8:
                    clinical_data["medications"].append({
                        "text": entity.text,
                        "ai_extracted": True,
                        "confidence": entity.confidence,
                        "attributes": entity.attributes
                    })
            
            # Add AI insights
            message.metadata["ai_insights"] = {
                "summary": clinical_doc.summary,
                "risk_factors": clinical_doc.risk_factors,
                "recommendations": clinical_doc.recommendations,
                "relationships": clinical_doc.relationships
            }
        
        return message
    
    async def _map_terminologies(self, message: HealthcareMessage) -> HealthcareMessage:
        """Map clinical terms to standard terminologies"""
        
        clinical_data = message.metadata.get("clinical_data", {})
        terminology_mappings = {}
        
        # Map conditions
        for condition in clinical_data.get("conditions", []):
            if condition.get("text"):
                mapping_result = await self.terminology_mapper.map_term(
                    term=condition["text"],
                    context="condition",
                    target_systems=["snomed", "icd10"]
                )
                
                if mapping_result.mappings:
                    condition["mappings"] = {
                        system: [{
                            "code": m.code,
                            "display": m.display,
                            "confidence": m.confidence
                        } for m in mappings]
                        for system, mappings in mapping_result.mappings.items()
                    }
        
        # Map medications
        for medication in clinical_data.get("medications", []):
            if medication.get("text"):
                mapping_result = await self.terminology_mapper.map_term(
                    term=medication["text"],
                    context="medication",
                    target_systems=["rxnorm", "ndc"]
                )
                
                if mapping_result.mappings:
                    medication["mappings"] = {
                        system: [{
                            "code": m.code,
                            "display": m.display,
                            "confidence": m.confidence
                        } for m in mappings]
                        for system, mappings in mapping_result.mappings.items()
                    }
        
        message.metadata["terminology_mappings"] = terminology_mappings
        return message
    
    async def _apply_business_rules(self, message: HealthcareMessage) -> HealthcareMessage:
        """Apply healthcare business rules and clinical decision support"""
        
        alerts = []
        clinical_data = message.metadata.get("clinical_data", {})
        ai_insights = message.metadata.get("ai_insights", {})
        
        # Check for critical conditions
        for condition in clinical_data.get("conditions", []):
            if self._is_critical_condition(condition):
                alerts.append({
                    "type": "critical_condition",
                    "severity": "high",
                    "message": f"Critical condition detected: {condition.get('text')}",
                    "action_required": True
                })
        
        # Check for drug interactions
        medications = clinical_data.get("medications", [])
        if len(medications) > 1:
            interactions = await self._check_drug_interactions(medications)
            alerts.extend(interactions)
        
        # Check AI-identified risk factors
        for risk in ai_insights.get("risk_factors", []):
            if risk.get("score", 0) > 0.8:
                alerts.append({
                    "type": "ai_risk_factor",
                    "severity": "medium",
                    "message": f"High risk factor: {risk.get('factor')}",
                    "score": risk.get("score")
                })
        
        # Apply routing rules based on alerts
        if alerts:
            message.metadata["alerts"] = alerts
            message.metadata["priority"] = "high" if any(a["severity"] == "high" for a in alerts) else "medium"
        
        return message
    
    async def _transform_output(self, message: HealthcareMessage) -> HealthcareMessage:
        """Transform message to output format"""
        
        # Create processed data structure
        message.processed_data = {
            "id": message.id,
            "timestamp": message.timestamp.isoformat(),
            "source_system": message.source_system,
            "patient_id": message.patient_id,
            "encounter_id": message.encounter_id,
            "clinical_data": message.metadata.get("clinical_data", {}),
            "ai_insights": message.metadata.get("ai_insights", {}),
            "alerts": message.metadata.get("alerts", []),
            "processing_time_ms": self._calculate_processing_time(message)
        }
        
        return message
    
    async def _process_hl7_v2(self, message: HealthcareMessage) -> HealthcareMessage:
        """Process HL7 v2 messages"""
        # HL7 v2 specific processing
        return message
    
    async def _process_fhir(self, message: HealthcareMessage) -> HealthcareMessage:
        """Process FHIR resources"""
        # FHIR specific processing
        return message
    
    async def _process_cda(self, message: HealthcareMessage) -> HealthcareMessage:
        """Process CDA documents"""
        # CDA specific processing
        return message
    
    async def _process_custom(self, message: HealthcareMessage) -> HealthcareMessage:
        """Process custom message formats"""
        # Custom format processing
        return message
    
    async def _send_to_output(self, message: HealthcareMessage):
        """Send processed message to output topic"""
        
        output_topic = self.config.output_topics.get(
            message.type.value,
            self.config.output_topics.get("default")
        )
        
        if output_topic:
            await self.producer.send(
                output_topic,
                value=asdict(message),
                key=message.id.encode('utf-8')
            )
    
    async def _retry_message(self, message: HealthcareMessage):
        """Retry failed message"""
        message.retry_count += 1
        message.status = ProcessingStatus.RETRYING
        
        # Send to retry topic with delay
        retry_topic = self.config.output_topics.get("retry")
        if retry_topic:
            await self.producer.send(
                retry_topic,
                value=asdict(message),
                key=message.id.encode('utf-8')
            )
    
    async def _send_to_dlq(self, message: HealthcareMessage):
        """Send message to dead letter queue"""
        dlq_topic = self.config.output_topics.get("dlq")
        if dlq_topic:
            await self.producer.send(
                dlq_topic,
                value=asdict(message),
                key=message.id.encode('utf-8')
            )
    
    async def _periodic_checkpoint(self):
        """Periodically checkpoint processing state"""
        while True:
            try:
                await asyncio.sleep(self.config.checkpoint_interval_ms / 1000)
                
                # Save processing state to Redis
                checkpoint = {
                    "timestamp": datetime.now().isoformat(),
                    "metrics": self.metrics,
                    "consumer_position": await self._get_consumer_position()
                }
                
                await self.redis_client.set(
                    f"checkpoint:{self.config.consumer_group}",
                    json.dumps(checkpoint)
                )
                
            except Exception as e:
                logger.error(f"Checkpoint error: {e}")
    
    async def _update_metrics(self):
        """Update processing metrics"""
        while True:
            try:
                await asyncio.sleep(10)  # Update every 10 seconds
                
                # Calculate throughput
                current_time = datetime.now()
                # Implementation would calculate actual throughput
                
                # Publish metrics
                await self._publish_metrics()
                
            except Exception as e:
                logger.error(f"Metrics update error: {e}")
    
    def _kafka_record_to_message(self, record) -> HealthcareMessage:
        """Convert Kafka record to HealthcareMessage"""
        
        data = record.value
        
        return HealthcareMessage(
            id=data.get("id", str(uuid.uuid4())),
            type=MessageType(data.get("type", "custom")),
            source_system=data.get("source_system", "unknown"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            patient_id=data.get("patient_id"),
            encounter_id=data.get("encounter_id"),
            content=data.get("content"),
            metadata=data.get("metadata", {}),
            status=ProcessingStatus.RECEIVED
        )
    
    def _group_messages_by_type(self, messages: List[HealthcareMessage]) -> Dict[MessageType, List[HealthcareMessage]]:
        """Group messages by type for batch processing"""
        grouped = {}
        for message in messages:
            if message.type not in grouped:
                grouped[message.type] = []
            grouped[message.type].append(message)
        return grouped
    
    def _validate_hl7_v2(self, content: str) -> bool:
        """Validate HL7 v2 message structure"""
        try:
            parsed = hl7.parse(content)
            return 'MSH' in str(parsed)
        except:
            return False
    
    def _validate_fhir(self, content: Any) -> bool:
        """Validate FHIR resource structure"""
        if isinstance(content, dict):
            return 'resourceType' in content
        return False
    
    def _hl7_to_dict(self, parsed_hl7) -> Dict[str, Any]:
        """Convert parsed HL7 message to dictionary"""
        result = {}
        
        for segment in parsed_hl7:
            segment_name = str(segment[0])
            if segment_name not in result:
                result[segment_name] = []
            
            segment_dict = {}
            for i, field in enumerate(segment[1:]):
                if field:
                    segment_dict[f"field_{i+1}"] = str(field)
            
            result[segment_name].append(segment_dict)
        
        return result
    
    def _extract_narrative_text(self, message: HealthcareMessage) -> Optional[str]:
        """Extract narrative text from message for AI processing"""
        
        if message.type == MessageType.HL7_V2:
            # Extract from NTE segments
            parsed = message.metadata.get("parsed_hl7", {})
            notes = []
            
            if "NTE" in parsed:
                for nte in parsed["NTE"]:
                    if "field_3" in nte:  # Comment field
                        notes.append(nte["field_3"])
            
            return " ".join(notes) if notes else None
        
        elif message.type == MessageType.FHIR:
            # Extract from narrative or text fields
            if isinstance(message.content, dict):
                return message.content.get("text", {}).get("div")
        
        return None
    
    def _is_critical_condition(self, condition: Dict[str, Any]) -> bool:
        """Check if condition is critical"""
        critical_codes = {
            "I21",  # Acute myocardial infarction
            "I63",  # Cerebral infarction
            "J96",  # Respiratory failure
            "R57",  # Shock
            "N17"   # Acute kidney failure
        }
        
        code = condition.get("code", "")
        return any(code.startswith(critical) for critical in critical_codes)
    
    async def _check_drug_interactions(self, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for drug-drug interactions"""
        # This would integrate with a drug interaction database
        # For now, return empty list
        return []
    
    def _calculate_processing_time(self, message: HealthcareMessage) -> float:
        """Calculate message processing time"""
        return (datetime.now() - message.timestamp).total_seconds() * 1000
    
    async def _get_consumer_position(self) -> Dict[str, int]:
        """Get current consumer position for all partitions"""
        positions = {}
        for tp in self.consumer.assignment():
            positions[f"{tp.topic}:{tp.partition}"] = self.consumer.position(tp)
        return positions
    
    async def _publish_metrics(self):
        """Publish metrics to monitoring system"""
        # This would integrate with Prometheus/Grafana
        pass
    
    async def shutdown(self):
        """Gracefully shutdown stream processor"""
        logger.info("Shutting down healthcare stream processor...")
        
        if self.consumer:
            await self.consumer.stop()
        
        if self.producer:
            await self.producer.stop()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Healthcare stream processor shutdown complete")
