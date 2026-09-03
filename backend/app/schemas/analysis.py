"""
Pydantic models for the analysis endpoints.

Request validation (bbox bounds, date ordering) and response shapes.
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class AnalysisRequest(BaseModel):
    """Body for POST /api/v1/analysis/run."""

    bbox: List[float] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Bounding box as [west, south, east, north]",
        examples=[[-180.0, -90.0, 180.0, 90.0]],
    )
    start_date: date = Field(
        ...,
        description="Analysis period start (inclusive)",
        examples=["2026-08-01"],
    )
    end_date: date = Field(
        ...,
        description="Analysis period end (inclusive)",
        examples=["2026-08-31"],
    )

    @model_validator(mode="after")
    def validate_bbox_and_dates(self) -> "AnalysisRequest":
        west, south, east, north = self.bbox

        # Longitude: -180 .. 180
        if not (-180 <= west <= 180):
            raise ValueError(f"west longitude must be between -180 and 180, got {west}")
        if not (-180 <= east <= 180):
            raise ValueError(f"east longitude must be between -180 and 180, got {east}")

        # Latitude: -90 .. 90
        if not (-90 <= south <= 90):
            raise ValueError(f"south latitude must be between -90 and 90, got {south}")
        if not (-90 <= north <= 90):
            raise ValueError(f"north latitude must be between -90 and 90, got {north}")

        # Ordering
        if west >= east:
            raise ValueError(
                f"west ({west}) must be less than east ({east})"
            )
        if south >= north:
            raise ValueError(
                f"south ({south}) must be less than north ({north})"
            )

        # Date ordering
        if self.start_date > self.end_date:
            raise ValueError(
                f"start_date ({self.start_date}) must be <= end_date ({self.end_date})"
            )

        return self


class AnalysisResponse(BaseModel):
    """Response for POST /api/v1/analysis/run."""

    run_id: str = Field(..., description="Unique identifier for this analysis run")
    status: str = Field(..., description="Current status of the run")
    message: str = Field(..., description="Human-readable status message")


class AnalysisRunStatus(BaseModel):
    """Response for GET /api/v1/analysis/runs/{run_id}."""

    run_id: str = Field(..., description="Unique identifier for this analysis run")
    status: str = Field(..., description="Current status of the run")
    created_at: Optional[str] = Field(None, description="ISO timestamp of run creation")
    bbox: Optional[List[float]] = Field(None, description="Bounding box used")
    start_date: Optional[str] = Field(None, description="Analysis period start")
    end_date: Optional[str] = Field(None, description="Analysis period end")


class RunNotFoundError(BaseModel):
    """Body returned when a run_id does not exist."""

    detail: str = "Analysis run not found"
