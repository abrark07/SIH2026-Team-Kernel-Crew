"""
GET /api/v1/health

Simple health-check endpoint for development and integration testing.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str = "ok"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns a simple status to confirm the API is running.",
)
async def health_check() -> HealthResponse:
    return HealthResponse()
