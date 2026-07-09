"""Shared security dependencies for PlantBrain API routers."""

from fastapi import Header, HTTPException, status

from app.config import settings


async def verify_admin_key(x_admin_key: str = Header(default="")) -> bool:
    """Validate the admin API key and reject insecure production defaults."""

    insecure_default = settings.admin_api_key == "changeme" or not settings.admin_api_key
    if insecure_default:
        if settings.environment != "production":
            return True
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_API_KEY must be configured to a non-default value in production",
        )

    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin API key")
    return True