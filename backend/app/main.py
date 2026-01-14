import time
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.logging_config import setup_logging, get_logger
from app.metrics import (
    metrics_endpoint, 
    REQUEST_COUNT, 
    REQUEST_LATENCY,
    WEBSOCKET_CONNECTIONS,
    set_model_loaded
)
from app.api.websocket import router as ws_router
from app.api.routes import router as api_router
from app.api.hud_routes import router as hud_router
from app.api.training_routes import router as training_router
from app.db.charts import get_chart_stats


settings = get_settings()

# Setup structured logging
setup_logging(debug=settings.debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    logger.info(
        "application_startup",
        app_name=settings.app_name,
        debug=settings.debug,
    )
    
    # Check chart data
    chart_stats = get_chart_stats()
    logger.info(
        "charts_loaded",
        charts=chart_stats.get("charts_loaded", []),
        total_ranges=chart_stats.get("total_ranges", 0),
    )
    
    # Set model status (not loaded initially)
    set_model_loaded("cards_yolo", False)
    
    yield
    
    # Shutdown
    logger.info("application_shutdown", app_name=settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description="Real-time poker table analyzer with GTO recommendations",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)


# Request timing middleware
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    """Track request timing and log requests."""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    duration_ms = duration * 1000
    
    # Record metrics
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(duration)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
    ).inc()
    
    # Log request (skip health checks and metrics to reduce noise)
    if request.url.path not in ["/health", "/metrics"]:
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
    
    return response


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
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
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "1.0.0",
    }


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    return await metrics_endpoint()


@app.get("/status")
async def status_page():
    """Detailed status page for monitoring."""
    chart_stats = get_chart_stats()
    
    return {
        "status": "healthy",
        "app": {
            "name": settings.app_name,
            "version": "1.0.0",
            "debug": settings.debug,
        },
        "charts": {
            "loaded": chart_stats.get("charts_loaded", []),
            "total_ranges": chart_stats.get("total_ranges", 0),
        },
        "connections": {
            "websocket": 0,  # Will be updated by WebSocket handler
        },
        "model": {
            "loaded": False,  # Will be updated when model loads
            "path": settings.yolo_model_path,
        },
    }
