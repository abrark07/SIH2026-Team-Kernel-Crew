"""
Data-access abstraction for analysis runs.

Uses an in-memory dict for the POC so the backend can track runs
without a database.  Replace with a real DB when available.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class AnalysisRepository:
    """
    Stores analysis run metadata.

    POC implementation: in-memory dictionary.
    Production: replace with PostgreSQL / equivalent.
    """

    def __init__(self) -> None:
        self._runs: Dict[str, Dict[str, Any]] = {}
        self._counter: int = 0

    async def create_run(
        self,
        bbox: List[float],
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Create a new analysis run record and return its metadata."""
        self._counter += 1
        run_id = f"RUN-{self._counter:04d}"
        record = {
            "run_id": run_id,
            "bbox": bbox,
            "start_date": start_date,
            "end_date": end_date,
            "status": "started",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "result": None,
        }
        self._runs[run_id] = record
        return record

    async def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Return run metadata or None."""
        return self._runs.get(run_id)

    async def update_run(self, run_id: str, updates: Dict[str, Any]) -> None:
        """Merge *updates* into an existing run record."""
        if run_id in self._runs:
            self._runs[run_id].update(updates)

    async def list_runs(self) -> List[Dict[str, Any]]:
        """Return all runs (most recent first)."""
        return list(reversed(self._runs.values()))
