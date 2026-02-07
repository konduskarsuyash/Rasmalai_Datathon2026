"""
Financial Network Backend API — auth + simulation/config logic.
All logic (config, core, ml, featherless) lives inside backend/app.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend dir is on path so "app" package resolves when running as backend.app.main
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

# Load from backend/.env or project root
_env_backend = _backend_dir / ".env"
_env_root = _backend_dir.parent / ".env"
if _env_backend.exists():
    load_dotenv(_env_backend)
else:
    load_dotenv(_env_root)

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .middleware.auth import get_optional_user
from .routers import simulation, config_router, network

app = FastAPI(
    title="Financial Network API",
    description="Auth + simulation v2 (config, core, ml, featherless).",
    version="0.3.0",
)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,*").split(",")
if "*" in CORS_ORIGINS:
    CORS_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulation.router, prefix="/api/simulation", tags=["simulation"])
app.include_router(config_router.router, prefix="/api/config", tags=["config"])
app.include_router(network.router, prefix="/api/networks", tags=["networks"])


@app.get("/")
async def root():
    return {"service": "financial-network-api", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/me")
async def me(current_user=Depends(get_optional_user)):
    """Current user if authenticated (Clerk)."""
    if not current_user:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "user_id": current_user["user_id"],
        "session_id": current_user.get("session_id"),
    }
