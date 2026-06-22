import time
from fastapi import APIRouter, Response
from app.models.schemas import HealthResponse, HealthChecks
from app.core.config import settings
from app.core.document_store import supabase

router = APIRouter()
START_TIME = time.time()

@router.get("/health", response_model=HealthResponse)
async def health_check(response: Response):
    """
    Health check endpoint. Validates core services.
    """
    uptime = int(time.time() - START_TIME)
    
    # Check Supabase
    supabase_status = "ok"
    if supabase:
        try:
            supabase.table("documents").select("id").limit(1).execute()
        except Exception as e:
            supabase_status = f"down: {str(e)}"
    else:
        supabase_status = "down: client not initialized"
        
    # Check Claude Key
    claude_status = "ok" if settings.ANTHROPIC_API_KEY and len(settings.ANTHROPIC_API_KEY) > 5 else "missing_key"
    
    # Check Gemini Key
    gemini_status = "ok" if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY) > 5 else "missing_key"
    
    # Determine HTTP status code
    if "down" in supabase_status:
        response.status_code = 503
        overall_status = "degraded"
    else:
        response.status_code = 200
        overall_status = "ok"
        
    if claude_status != "ok" or gemini_status != "ok":
        overall_status = "degraded"
        
    return HealthResponse(
        status=overall_status,
        version="1.0.0-phase1",
        uptime_seconds=uptime,
        checks=HealthChecks(
            supabase=supabase_status,
            claude=claude_status,
            gemini=gemini_status
        )
    )
