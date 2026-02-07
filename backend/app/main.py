"""
Financial Network Game-Theoretic Backend API.
MVP: Network & Clearing Core, Contagion Engine, Equilibrium Engine.
"""
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Allow importing core_implementation from project root when running from backend/
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import networks, contagion, equilibrium, users
from .config.database import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="Financial Network Systemic Risk API",
    description="Network-based game-theoretic model: banks, exchanges, clearing houses.",
    version="0.1.0",
)

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database lifecycle events
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

app.include_router(networks.router, prefix="/api/networks", tags=["networks"])
app.include_router(contagion.router, prefix="/api/contagion", tags=["contagion"])
app.include_router(equilibrium.router, prefix="/api/equilibrium", tags=["equilibrium"])
app.include_router(users.router, prefix="/api/users", tags=["users"])


@app.get("/")
async def root():
    return {"service": "financial-network-api", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "database": "connected"}
