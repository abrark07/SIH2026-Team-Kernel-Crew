import asyncio
from datetime import date
from app.repositories.analysis_repository import AnalysisRepository
from app.services.firms_service import FirmsService
from app.services.analysis_service import AnalysisService
from app.schemas.analysis import AnalysisRequest

async def test():
    repo = AnalysisRepository()
    firms = FirmsService()
    
    # We don't have FIRMS_MAP_KEY set, so FirmsService will throw.
    # We will mock FirmsService.fetch_firms_data
    
    # Let's mock a few detections that look like the ones in viirs_v11_final_event_dataset.csv
    mock_detections = [
        {"latitude": 19.5, "longitude": 83.5, "acq_date": "2024-01-01", "daynight": "N", "frp": 10.5, "bright_ti4": 305.1, "bright_ti5": 280.0},
        {"latitude": 19.5, "longitude": 83.5, "acq_date": "2024-01-03", "daynight": "N", "frp": 11.0, "bright_ti4": 310.0, "bright_ti5": 281.0},
        {"latitude": 19.5, "longitude": 83.5, "acq_date": "2024-01-05", "daynight": "N", "frp": 12.0, "bright_ti4": 308.0, "bright_ti5": 282.0},
        {"latitude": 19.5, "longitude": 83.5, "acq_date": "2024-01-07", "daynight": "N", "frp": 10.8, "bright_ti4": 304.0, "bright_ti5": 279.0},
        {"latitude": 19.5, "longitude": 83.5, "acq_date": "2024-01-09", "daynight": "N", "frp": 11.5, "bright_ti4": 309.0, "bright_ti5": 280.0},
        # Need many more days to be Persistent (e.g. >10 days)
        {"latitude": 19.5, "longitude": 83.5, "acq_date": "2024-01-11", "daynight": "N", "frp": 11.0, "bright_ti4": 305.1, "bright_ti5": 280.0},
        {"latitude": 19.5, "longitude": 83.5, "acq_date": "2024-01-13", "daynight": "N", "frp": 11.0, "bright_ti4": 305.1, "bright_ti5": 280.0},
        {"latitude": 19.5, "longitude": 83.5, "acq_date": "2024-01-15", "daynight": "N", "frp": 11.0, "bright_ti4": 305.1, "bright_ti5": 280.0},
        {"latitude": 19.5, "longitude": 83.5, "acq_date": "2024-01-17", "daynight": "N", "frp": 11.0, "bright_ti4": 305.1, "bright_ti5": 280.0},
        {"latitude": 19.5, "longitude": 83.5, "acq_date": "2024-01-19", "daynight": "N", "frp": 11.0, "bright_ti4": 305.1, "bright_ti5": 280.0},
        {"latitude": 19.5, "longitude": 83.5, "acq_date": "2024-01-21", "daynight": "N", "frp": 11.0, "bright_ti4": 305.1, "bright_ti5": 280.0},
        {"latitude": 19.5, "longitude": 83.5, "acq_date": "2024-01-23", "daynight": "N", "frp": 11.0, "bright_ti4": 305.1, "bright_ti5": 280.0},
        {"latitude": 19.5, "longitude": 83.5, "acq_date": "2024-01-25", "daynight": "N", "frp": 11.0, "bright_ti4": 305.1, "bright_ti5": 280.0},
        {"latitude": 19.5, "longitude": 83.5, "acq_date": "2024-01-27", "daynight": "N", "frp": 11.0, "bright_ti4": 305.1, "bright_ti5": 280.0},
        {"latitude": 19.5, "longitude": 83.5, "acq_date": "2024-01-29", "daynight": "N", "frp": 11.0, "bright_ti4": 305.1, "bright_ti5": 280.0},
        # Transient event with nearby OSM
        {"latitude": 20.0, "longitude": 84.0, "acq_date": "2024-01-01", "daynight": "N", "frp": 5.0, "bright_ti4": 300.0, "bright_ti5": 290.0},
        # Transient event without OSM nearby
        {"latitude": 21.0, "longitude": 85.0, "acq_date": "2024-01-01", "daynight": "N", "frp": 5.0, "bright_ti4": 300.0, "bright_ti5": 290.0},
    ]
    
    async def mock_fetch(*args, **kwargs):
        return mock_detections
        
    firms.fetch_firms_data = mock_fetch
    
    service = AnalysisService(repo, firms)
    
    request = AnalysisRequest(
        bbox=[83.0, 19.0, 84.5, 20.5],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 10)
    )
    
    # Create temporary mock OSM file to test integration
    import os
    from pathlib import Path
    data_dir = Path(__file__).parent / "temp_test_data"
    data_dir.mkdir(exist_ok=True)
    temp_osm = data_dir / "osm_points.csv"
    with open(temp_osm, "w") as f:
        f.write("latitude,longitude,industrial,landuse,power,man_made,building,product,plant_source,plant_method,resource,description\n")
        f.write("20.01,84.01,factory,,,,,,,,,\n")
        f.write("19.0,83.0,mine,,,,,,,,,\n")
        
    try:
        # Override the path that AnalysisService looks for just for this test
        AnalysisService._test_osm_file_override = temp_osm
        
        res = await service.start_analysis(request)
        print("Start result:", res)
        
        # Since start_analysis is async and awaits _run_ml_pipeline, it should have updated the repo
        run = await repo.get_run(res.run_id)
        print("Final status:", run["status"])
        if "result" in run:
            import json
            print(json.dumps(run["result"]["events"], indent=2))
    finally:
        # Cleanup mock file
        if temp_osm.exists():
            os.remove(temp_osm)
        if data_dir.exists():
            os.rmdir(data_dir)
        if hasattr(AnalysisService, "_test_osm_file_override"):
            delattr(AnalysisService, "_test_osm_file_override")

if __name__ == "__main__":
    asyncio.run(test())
