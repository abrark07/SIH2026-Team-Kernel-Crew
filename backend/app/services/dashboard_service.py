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
        Return current summary statistics.

        Values come from the repository (currently all zeros because
        there is no database).  Once the DB and ML pipeline are
        integrated, this will return real aggregate data.
        """
        stats = await self._repo.get_summary_stats()
        return DashboardSummary(**stats)
