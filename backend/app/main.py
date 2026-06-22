import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api import health, query, documents

# Setup structured logging format
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format=log_format,
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("plantbrain.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan handler that validates config on startup.
    Since config is instantiated in config.py, if we reach here, it's valid.
    The get_settings() factory ensures the app exits on missing required vars.
    """
    logger.info("Initializing PlantBrain application lifespan...")
    
    # Validate essential config explicitly here as an extra safety measure
    if not settings.ANTHROPIC_API_KEY:
        logger.critical("ANTHROPIC_API_KEY is not set.")
        raise ValueError("ANTHROPIC_API_KEY must be provided")
        
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.critical("SUPABASE_URL or SUPABASE_KEY is not set.")
        raise ValueError("Supabase configuration must be provided")
        
    logger.info(f"Allowed CORS origins: {settings.ALLOWED_ORIGINS}")
    logger.info(f"Max Document Size: {settings.MAX_DOCUMENT_SIZE_MB}MB")
    logger.info("Configuration validated successfully.")
    
    # Required log message
    logger.info("PlantBrain backend ready")
    
    yield
    
    logger.info("PlantBrain backend shutting down. Cleaning up resources...")

app = FastAPI(
    title="PlantBrain API",
    description="Backend API for PlantBrain - Industrial Knowledge Intelligence",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
    expose_headers=["Content-Length"]
)

@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """
    Request logging middleware.
    Logs HTTP method, path, and response time in milliseconds.
    """
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"Method: {request.method} Path: {request.url.path} "
            f"Status: {response.status_code} Time: {process_time_ms:.2f}ms"
        )
        return response
    except Exception as exc:
        process_time_ms = (time.time() - start_time) * 1000
        logger.error(
            f"Method: {request.method} Path: {request.url.path} "
            f"Status: 500 Time: {process_time_ms:.2f}ms - Exception: {str(exc)}"
        )
        raise

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that returns structured JSON errors
    instead of raw stack traces for unhandled exceptions.
    """
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing your request.",
            "detail": str(exc),
            "path": request.url.path,
            "method": request.method
        }
    )

# Include routers for the API endpoints
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
