"""
Pydantic models for the dashboard summary endpoint.
"""

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    """Response for GET /api/v1/dashboard/summary."""

    total_detections: int = Field(0, description="Total raw FIRMS detections")
    total_events: int = Field(0, description="Total clustered thermal events")
    industrial_events: int = Field(0, description="Events classified as industrial-like")
    non_industrial_events: int = Field(0, description="Events classified as non-industrial")
    uncertain_events: int = Field(0, description="Events with uncertain classification")
    high_risk_events: int = Field(0, description="Events flagged as high risk")
    average_confidence: float = Field(0.0, description="Mean classification confidence")
