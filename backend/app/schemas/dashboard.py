"""
Pydantic models for the dashboard summary endpoint.
Aligned to ML contract — no fake confidence or risk_level fields.
"""

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    """Response for GET /api/v1/dashboard/summary."""

    total_detections: int = Field(0, description="Total raw FIRMS detections processed")
    total_events: int = Field(0, description="Total clustered thermal events")
    industrial_events: int = Field(0, description="Events classified as Industrial by domain rule")
    uncertain_events: int = Field(0, description="Events classified as Uncertain")
    persistent_events: int = Field(0, description="Events with Persistent behavior (KMeans cluster 1)")
    transient_events: int = Field(0, description="Events with Transient behavior (KMeans cluster 0)")
