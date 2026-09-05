import asyncio
import json
import pandas as pd
from datetime import date
from pathlib import Path
from app.repositories.analysis_repository import AnalysisRepository
from app.services.firms_service import FirmsService
from app.services.analysis_service import AnalysisService
from app.schemas.analysis import AnalysisRequest

async def main():
    repo = AnalysisRepository()
    firms = FirmsService()
    
    # Read the new dataset
    csv_path = Path(__file__).parent / "data" / "viirs_jan2024_night.csv"
    print(f"Reading dataset: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Convert to list of dicts to simulate FIRMS API response
    detections = df.to_dict(orient="records")
    print(f"Loaded {len(detections)} raw detections.")
    
    async def mock_fetch(*args, **kwargs):
        return detections
        
    firms.fetch_firms_data = mock_fetch
    
    service = AnalysisService(repo, firms)
    
    request = AnalysisRequest(
        bbox=[68.0, 6.0, 97.5, 37.5], # India bbox
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31)
    )
    
    res = await service.start_analysis(request)
    run = await repo.get_run(res.run_id)
    
    if "result" in run and run["result"]:
        events = run["result"]["events"]
        # Ensure event_id is string
        for e in events:
            e["event_id"] = str(e["event_id"])
            
        out_path = Path(__file__).parent / "data" / "db.json"
        with open(out_path, "w") as f:
            json.dump(events, f, indent=2)
            
        print(f"Successfully processed and saved {len(events)} events to db.json")
    else:
        print("Failed to run pipeline:", run.get("error", "Unknown error"))

if __name__ == "__main__":
    asyncio.run(main())
