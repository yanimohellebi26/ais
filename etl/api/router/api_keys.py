from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.security_api import verify_api_key, create_api_key, delete_api_key, get_api_keys

router = APIRouter()

class APIKeyCreateRequest(BaseModel):
    name: str

@router.post("/")
async def api_create(payload: APIKeyCreateRequest, auth=Depends(verify_api_key)):
    if not auth.get("superuser"):
        raise HTTPException(status_code=403, detail="Forbidden")
    key = create_api_key(payload.name)
    return {"api_key": key, "name": payload.name}

@router.delete("/{key}")
async def api_delete(key: str, auth=Depends(verify_api_key)):
    if not auth.get("superuser"):
        raise HTTPException(status_code=403, detail="Forbidden")
    success = delete_api_key(key)
    return {"deleted": success}

@router.get("/")
async def api_get(auth=Depends(verify_api_key)):
    if not auth.get("superuser"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"api_keys": get_api_keys()}