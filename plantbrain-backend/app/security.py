"""Shared security dependencies for PlantBrain API routers."""

from fastapi import Header, HTTPException

from app.config import settings


async def verify_admin_key(x_admin_key: str = Header(default="")) -> bool:
    """Validate the admin API key, skipping only insecure development defaults."""

    if settings.admin_api_key == "changeme" or not settings.admin_api_key:
        if settings.environment != "production":
            return True
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin API key")
    return True
