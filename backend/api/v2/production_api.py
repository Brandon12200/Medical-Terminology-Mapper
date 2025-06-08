from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from sqlalchemy.orm import Session
import redis.asyncio as redis
from prometheus_fastapi_instrumentator import Instrumentator
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.models.ai_models import AdvancedMedicalAI, ProcessingMode, ClinicalDocument
from app.streaming.healthcare_stream_processor import (
    HealthcareStreamProcessor,
    StreamConfig,
    HealthcareMessage,
    MessageType
)
from app.security.hipaa_security import (
    HIPAASecurityManager,
    SecurityConfig,
    get_current_user,
    require_role,
    require_access_level,
    UserRole,
    AccessLevel,
    TokenData
)
from app.standards.terminology.enhanced_mapper import EnhancedTerminologyMapper
from app.utils.logger import get_logger
from .routers import (
    auth_router,
    terminology_router,
    clinical_router,
    streaming_router,
    admin_router,
    audit_router
)

logger = get_logger(__name__)

# Production configuration
class ProductionConfig:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/medical_db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Kafka
    KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")
    
    # Security
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://your-domain.com").split(",")
    TRUSTED_HOSTS = os.getenv("TRUSTED_HOSTS", "your-domain.com").split(",")
    
    # AI Models
    ENABLE_AI = os.getenv("ENABLE_AI", "true").lower() == "true"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # Monitoring
    SENTRY_DSN = os.getenv("SENTRY_DSN")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))


# Global instances
ai_model: Optional[AdvancedMedicalAI] = None
stream_processor: Optional[HealthcareStreamProcessor] = None
security_manager: Optional[HIPAASecurityManager] = None
terminology_mapper: Optional[EnhancedTerminologyMapper] = None
redis_client: Optional[redis.Redis] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global ai_model, stream_processor, security_manager, terminology_mapper, redis_client
    
    logger.info("Starting Medical Terminology Mapper Production API...")
    
    try:
        # Initialize Redis
        redis_client = await redis.from_url(
            ProductionConfig.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Initialize database
        from app.database import init_db, get_db
        await init_db(ProductionConfig.DATABASE_URL)
        
        # Initialize security manager
        security_config = SecurityConfig(
            jwt_secret_key=ProductionConfig.JWT_SECRET_KEY,
            allowed_origins=ProductionConfig.ALLOWED_ORIGINS,
            rate_limit_requests=ProductionConfig.RATE_LIMIT_REQUESTS,
            rate_limit_window_seconds=ProductionConfig.RATE_LIMIT_WINDOW
        )
        
        # Get database session
        db = next(get_db())
        
        security_manager = HIPAASecurityManager(
            config=security_config,
            db_session=db,
            redis_client=redis_client
        )
        
        # Initialize terminology mapper
        terminology_mapper = EnhancedTerminologyMapper()
        await terminology_mapper.initialize()
        
        # Initialize AI model if enabled
        if ProductionConfig.ENABLE_AI:
            ai_config = {
                "enable_clinical_bert": True,
                "enable_scispacy": True,
                "enable_embeddings": True,
                "enable_llm": bool(ProductionConfig.OPENAI_API_KEY or ProductionConfig.ANTHROPIC_API_KEY),
                "openai_api_key": ProductionConfig.OPENAI_API_KEY,
                "anthropic_api_key": ProductionConfig.ANTHROPIC_API_KEY,
                "max_workers": 4
            }
            
            ai_model = AdvancedMedicalAI(ai_config)
            logger.info("AI models initialized successfully")
        
        # Initialize stream processor
        stream_config = StreamConfig(
            kafka_brokers=ProductionConfig.KAFKA_BROKERS,
            redis_url=ProductionConfig.REDIS_URL,
            input_topics=["hl7-messages", "fhir-resources", "clinical-documents"],
            output_topics={
                "default": "processed-messages",
                "alerts": "clinical-alerts",
                "retry": "retry-queue",
                "dlq": "dead-letter-queue"
            },
            consumer_group="medical-processor-group",
            batch_size=100,
            batch_timeout_ms=5000
        )
        
        stream_processor = HealthcareStreamProcessor(
            config=stream_config,
            ai_model=ai_model,
            terminology_mapper=terminology_mapper
        )
        
        await stream_processor.initialize()
        
        # Start background stream processing
        asyncio.create_task(stream_processor.start_processing())
        
        logger.info("All services initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    finally:
        # Cleanup
        logger.info("Shutting down services...")
        
        if stream_processor:
            await stream_processor.shutdown()
        
        if redis_client:
            await redis_client.close()
        
        logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Medical Terminology Mapper API",
    description="Production-ready healthcare data processing API with AI capabilities",
    version="2.0.0",
    docs_url="/api/v2/docs",
    redoc_url="/api/v2/redoc",
    openapi_url="/api/v2/openapi.json",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ProductionConfig.TRUSTED_HOSTS
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ProductionConfig.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"]
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response

# Process time middleware
@app.middleware("http")
async def add_process_time(request: Request, call_next):
    import time
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )

# Initialize monitoring
if ProductionConfig.SENTRY_DSN:
    sentry_sdk.init(
        dsn=ProductionConfig.SENTRY_DSN,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration()
        ],
        traces_sample_rate=0.1,
        environment=os.getenv("ENVIRONMENT", "production")
    )

# Prometheus metrics
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app, endpoint="/metrics")

# Health check endpoints
@app.get("/health", tags=["health"])
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/health/detailed", tags=["health"])
async def detailed_health_check(
    current_user: TokenData = Depends(require_role([UserRole.SYSTEM_ADMIN]))
):
    """Detailed health check for monitoring"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {}
    }
    
    # Check Redis
    try:
        await redis_client.ping()
        health_status["services"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Check AI models
    if ai_model:
        health_status["services"]["ai_models"] = {
            "status": "healthy",
            "models_loaded": list(ai_model.models.keys())
        }
    
    # Check stream processor
    if stream_processor:
        health_status["services"]["stream_processor"] = {
            "status": "healthy",
            "metrics": stream_processor.metrics
        }
    
    return health_status

# API Routes

@app.post("/api/v2/process/document", tags=["clinical"])
async def process_clinical_document(
    document: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(require_access_level(AccessLevel.PHI_LIMITED))
):
    """Process clinical document with AI enhancement"""
    
    if not ai_model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI processing not available"
        )
    
    try:
        # Extract text and metadata
        text = document.get("text", "")
        metadata = document.get("metadata", {})
        
        # Add user context to metadata
        metadata["processed_by"] = current_user.username
        metadata["process_time"] = datetime.utcnow().isoformat()
        
        # Process document
        clinical_doc = await ai_model.process_clinical_document(
            text=text,
            metadata=metadata,
            mode=ProcessingMode.INTERACTIVE
        )
        
        # Log PHI access
        await security_manager._audit_log(
            event_type="DATA_VIEW",
            user_id=current_user.user_id,
            username=current_user.username,
            resource_type="clinical_document",
            patient_id=metadata.get("patient_id"),
            action="process_document"
        )
        
        # Background task for additional processing
        background_tasks.add_task(
            store_processed_document,
            clinical_doc,
            current_user
        )
        
        return {
            "status": "success",
            "document": {
                "entities": [
                    {
                        "text": e.text,
                        "type": e.type,
                        "confidence": e.confidence,
                        "negated": e.negated,
                        "terminology_codes": e.terminology_codes
                    }
                    for e in clinical_doc.entities
                ],
                "summary": clinical_doc.summary,
                "risk_factors": clinical_doc.risk_factors,
                "recommendations": clinical_doc.recommendations
            }
        }
        
    except Exception as e:
        logger.error(f"Document processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document"
        )


@app.post("/api/v2/stream/message", tags=["streaming"])
async def submit_healthcare_message(
    message: Dict[str, Any],
    current_user: TokenData = Depends(require_access_level(AccessLevel.PHI_FULL))
):
    """Submit healthcare message for stream processing"""
    
    if not stream_processor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stream processing not available"
        )
    
    try:
        # Create healthcare message
        healthcare_msg = HealthcareMessage(
            id=message.get("id", str(uuid.uuid4())),
            type=MessageType(message.get("type", "custom")),
            source_system=message.get("source_system", "api"),
            timestamp=datetime.utcnow(),
            patient_id=message.get("patient_id"),
            encounter_id=message.get("encounter_id"),
            content=message.get("content"),
            metadata={
                "submitted_by": current_user.username,
                "api_version": "v2"
            },
            status="received"
        )
        
        # Send to Kafka
        await stream_processor.producer.send(
            "healthcare-messages",
            value=healthcare_msg.dict()
        )
        
        return {
            "status": "accepted",
            "message_id": healthcare_msg.id,
            "timestamp": healthcare_msg.timestamp
        }
        
    except Exception as e:
        logger.error(f"Stream submission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit message"
        )


@app.post("/api/v2/terminology/map/batch", tags=["terminology"])
async def batch_terminology_mapping(
    terms: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_user)
):
    """Batch terminology mapping with AI enhancement"""
    
    if not terminology_mapper:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Terminology mapping not available"
        )
    
    # Validate batch size
    if len(terms) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size exceeds maximum of 1000 terms"
        )
    
    # Create batch job
    job_id = str(uuid.uuid4())
    
    # Submit to background processing
    background_tasks.add_task(
        process_terminology_batch,
        job_id,
        terms,
        current_user
    )
    
    return {
        "status": "accepted",
        "job_id": job_id,
        "term_count": len(terms),
        "estimated_time_seconds": len(terms) * 0.5
    }


# Background tasks
async def store_processed_document(doc: ClinicalDocument, user: TokenData):
    """Store processed document in database"""
    # Implementation would store in database
    pass


async def process_terminology_batch(job_id: str, terms: List[Dict], user: TokenData):
    """Process terminology mapping batch"""
    
    try:
        results = []
        
        for term_data in terms:
            result = await terminology_mapper.map_term(
                term=term_data["term"],
                context=term_data.get("context"),
                target_systems=term_data.get("systems", ["snomed", "loinc", "rxnorm"])
            )
            results.append(result)
        
        # Store results in Redis with TTL
        await redis_client.setex(
            f"batch_result:{job_id}",
            3600,  # 1 hour TTL
            json.dumps({
                "status": "completed",
                "results": [r.dict() for r in results],
                "completed_at": datetime.utcnow().isoformat()
            })
        )
        
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        
        await redis_client.setex(
            f"batch_result:{job_id}",
            3600,
            json.dumps({
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            })
        )


# Mount routers
app.include_router(auth_router, prefix="/api/v2/auth", tags=["authentication"])
app.include_router(terminology_router, prefix="/api/v2/terminology", tags=["terminology"])
app.include_router(clinical_router, prefix="/api/v2/clinical", tags=["clinical"])
app.include_router(streaming_router, prefix="/api/v2/streaming", tags=["streaming"])
app.include_router(admin_router, prefix="/api/v2/admin", tags=["admin"])
app.include_router(audit_router, prefix="/api/v2/audit", tags=["audit"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.v2.production_api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=4,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    )
