from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.api.websocket import router as ws_router
from app.api.routes import router as api_router
from app.api.hud_routes import router as hud_router
from app.api.training_routes import router as training_router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    print(f"🚀 Starting {settings.app_name}")
    # TODO: Initialize ML models, database connections
    yield
    # Shutdown
    print(f"👋 Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    description="Real-time poker table analyzer with GTO recommendations",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])
app.include_router(api_router, prefix="/api", tags=["API"])
app.include_router(hud_router, prefix="/api", tags=["HUD & Equity"])
app.include_router(training_router, prefix="/api", tags=["Training"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}
