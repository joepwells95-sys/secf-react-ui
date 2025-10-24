from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json, os, tempfile
from datetime import datetime

app = FastAPI()

origins = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OVERRIDE_PATH = os.getenv("OVERRIDE_PATH", "override.json")

class ZoneOverrides(BaseModel):
    force_off: bool
    expiresAt: Optional[datetime | None]

class Zone(BaseModel):
    enabled: bool
    overrides: ZoneOverrides

class OverridePayload(BaseModel):
    zoneA: Zone
    zoneB: Zone


def atomic_write_json(path, data):
    temp_fd, temp_path = tempfile.mkstemp()
    with os.fdopen(temp_fd, 'w') as tmp:
        json.dump(data, tmp, indent=2, default=str)
    os.replace(temp_path, path)

@app.get("/api/override")
async def get_override():
    try:
        if not os.path.exists(OVERRIDE_PATH):
            return {"status": "ok", "payload": {
                "zoneA": {"enabled": False, "overrides": {"force_off": False, "expiresAt": None}},
                "zoneB": {"enabled": False, "overrides": {"force_off": False, "expiresAt": None}},
            }}
        with open(OVERRIDE_PATH) as f:
            return {"status": "ok", "payload": json.load(f)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/override")
async def patch_override(payload: OverridePayload):
    try:
        atomic_write_json(OVERRIDE_PATH, payload.dict())
        return {"status": "ok", "payload": payload.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
