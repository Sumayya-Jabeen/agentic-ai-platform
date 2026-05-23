from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from config import config


# Tells FastAPI to look for "X-API-Key" in the request headers
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """
    Dependency that protects any route it is attached to.

    How it works:
    - FastAPI reads the "X-API-Key" header from the incoming request
    - Compares it against API_SECRET_KEY from your .env file
    - If it matches  → request is allowed through
    - If it is wrong or missing → 401 Unauthorized is returned immediately

    Usage: add `Depends(verify_api_key)` to any route you want to protect.
    Routes without it (like /health) remain publicly accessible.
    """
    if not api_key or api_key != config.api_secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Include 'X-API-Key' in your request headers."
        )
