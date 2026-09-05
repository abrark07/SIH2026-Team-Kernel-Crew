import asyncio
import pytest
from datetime import date
from app.repositories.analysis_repository import AnalysisRepository
from app.services.firms_service import FirmsService
from app.services.analysis_service import AnalysisService
from app.schemas.analysis import AnalysisRequest

@pytest.mark.asyncio
async def test_ml_pipeline():
    repo = AnalysisRepository()
    firms = FirmsService()
    
    # In demo mode, AnalysisService bypasses FirmsService and loads the local dataset.
    
    service = AnalysisService(repo, firms)
    
    request = AnalysisRequest(
        bbox=[86.0, 23.0, 87.0, 24.0],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31)
    )

    res = await service.start_analysis(request)
    run = await repo.get_run(res.run_id)
    
    assert run["status"] == "completed", f"ML pipeline failed: {run.get('error')}"
    events = run["result"]["events"]
    
    assert len(events) == 164
    persistent = sum(1 for e in events if e["behavior_type"] == "Persistent")
    transient = sum(1 for e in events if e["behavior_type"] == "Transient")
    industrial = sum(1 for e in events if e["final_prediction"] == "Industrial")
    uncertain = sum(1 for e in events if e["final_prediction"] == "Uncertain")
    
    assert persistent == 27
    assert transient == 137
    assert industrial == 31
    assert uncertain == 133

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ml_pipeline())
