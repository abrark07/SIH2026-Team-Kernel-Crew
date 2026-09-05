"""
Business logic for the dashboard summary endpoint.
"""

from app.repositories.event_repository import EventRepository
from app.schemas.dashboard import DashboardSummary


class DashboardService:
    """Aggregates event data into dashboard statistics."""

    def __init__(self, event_repo: EventRepository) -> None:
        self._repo = event_repo

    async def get_summary(self) -> DashboardSummary:
        """
        Return current summary statistics aggregated from ML pipeline output.
        All values sourced from db.json — no invented figures.
        """
        stats = await self._repo.get_summary_stats()
        return DashboardSummary(**stats)
