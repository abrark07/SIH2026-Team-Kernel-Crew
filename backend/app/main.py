"""
FastAPI application entry point.

Creates the app, configures CORS, mounts all routers, and registers
a global exception handler that never leaks sensitive information.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.api.routes import analysis, events, dashboard, health

# Suppress httpx's default request logging — it logs full URLs which
# would expose the FIRMS MAP_KEY embedded in the request path.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# ── Lifespan (startup / shutdown hooks) ─────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    settings = get_settings()
    logger.info(
        "Starting %s v%s", settings.APP_TITLE, settings.APP_VERSION,
    )
    if not settings.FIRMS_MAP_KEY:
        logger.warning(
            "FIRMS_MAP_KEY is not set — FIRMS data fetching will be unavailable."
        )
    
    # Check for OSM data
    import os
    from pathlib import Path
    osm_file = Path(__file__).parent.parent / "data" / "osm_points.csv"
    if not osm_file.exists():
        logger.warning("OSM contextual dataset not found at %s; predictions will run without OSM evidence.", osm_file)
        
    yield
    logger.info("Shutting down.")


# ── App factory ─────────────────────────────────────────────────

settings = get_settings()

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=(
        "Backend API for AI-based detection and classification of "
        "industrial fires and persistent thermal sources using NASA FIRMS, "
        "OSM, and satellite data.  (SIH 2026 — Team Kernel Crew)"
    ),
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(health.router,    prefix=API_PREFIX)
app.include_router(analysis.router,  prefix=API_PREFIX)
app.include_router(events.router,    prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)


# ── Global exception handler ───────────────────────────────────


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for unexpected errors.

    Logs the real traceback server-side but returns a generic message
    to the client so stack traces and secrets are never exposed.
    """
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
    )
