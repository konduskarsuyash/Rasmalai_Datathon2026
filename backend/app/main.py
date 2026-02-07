"""
Financial Network Game-Theoretic Backend API.
MVP: Network & Clearing Core, Contagion Engine, Equilibrium Engine.
"""
from pathlib import Path
import sys

# Allow importing core_implementation from project root when running from backend/
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import networks, contagion, equilibrium

app = FastAPI(
    title="Financial Network Systemic Risk API",
    description="Network-based game-theoretic model: banks, exchanges, clearing houses.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(networks.router, prefix="/api/networks", tags=["networks"])
app.include_router(contagion.router, prefix="/api/contagion", tags=["contagion"])
app.include_router(equilibrium.router, prefix="/api/equilibrium", tags=["equilibrium"])


@app.get("/")
async def root():
    return {"service": "financial-network-api", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
