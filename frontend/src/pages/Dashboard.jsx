import { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import ThermalMap from "../components/ThermalMap";
import PriorityWatchlist from "../components/PriorityWatchlist";
import { fetchHotspots, fetchDashboardSummary, triggerAnalysis } from "../api/hotspots";

export default function Dashboard() {
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [summary, setSummary] = useState(null);
  const [viewportBounds, setViewportBounds] = useState(null);
  const [mapFilters, setMapFilters] = useState({ Industrial: true, Uncertain: true });

  const loadData = async () => {
    const [liveData, liveSummary] = await Promise.all([
      fetchHotspots(),
      fetchDashboardSummary(),
    ]);
    if (liveData) setHotspots(liveData);
    if (liveSummary) setSummary(liveSummary);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const runDemoAnalysis = async () => {
    setAnalyzing(true);
    try {
      await triggerAnalysis([86.0, 23.0, 87.0, 24.0], "2024-01-01", "2024-01-31");
      // Wait a moment to ensure db.json is picked up, though the backend writes it synchronously
      await loadData();
    } catch (err) {
      alert("Analysis failed: " + err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const visibleHotspots = useMemo(() => {
    let filtered = hotspots;
    if (viewportBounds) {
      const [w, s, e, n] = viewportBounds;
      filtered = filtered.filter((h) => 
        h.lng >= w && h.lng <= e && h.lat >= s && h.lat <= n
      );
    }
    return filtered.filter((h) => mapFilters[h.classification]);
  }, [hotspots, viewportBounds, mapFilters]);

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-ivory">
        <div className="flex flex-col items-center gap-3">
          <h1 className="font-serif text-4xl text-teal font-extrabold tracking-tight animate-pulse">
            GeoSentinel
          </h1>
          <p className="text-xs text-charcoal/50 tracking-widest uppercase">
            Loading ML pipeline data…
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-ivory overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-charcoal/10 bg-ivory z-10 flex-shrink-0">
        <div>
          <h1 className="font-serif text-xl text-teal font-bold leading-tight">GeoSentinel</h1>
          <p className="text-[10px] text-charcoal/40 tracking-wider uppercase">
            Industrial Thermal Intelligence · Jan 2024 VIIRS SNPP
          </p>
        </div>

        {/* Summary stats from real ML output */}
        {summary && (
          <div className="flex gap-6 text-xs text-charcoal font-sans">
            <div><span className="font-bold text-teal">{summary.total_events.toLocaleString()}</span> events</div>
            <div><span className="font-bold" style={{ color: "#0F6B6E" }}>{summary.industrial_events.toLocaleString()}</span> Industrial</div>
            <div><span className="font-bold" style={{ color: "#D9A521" }}>{summary.uncertain_events.toLocaleString()}</span> Uncertain</div>
            <div><span className="font-bold">{summary.persistent_events.toLocaleString()}</span> Persistent</div>
            <div><span className="font-bold">{summary.transient_events.toLocaleString()}</span> Transient</div>
            <div className="text-gray-400">{summary.total_detections.toLocaleString()} raw detections</div>
          </div>
        )}

        <div className="flex items-center gap-4">
          <button
            onClick={runDemoAnalysis}
            disabled={analyzing}
            className="text-xs bg-teal text-white px-3 py-1.5 rounded disabled:opacity-50 font-sans"
          >
            {analyzing ? "Analyzing..." : "Run SIH Demo Analysis"}
          </button>
          <Link to="/list" className="text-gold underline font-sans text-sm">
            Priority Rankings →
          </Link>
        </div>
      </header>

      {/* Main: map + watchlist */}
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 relative">
          <ThermalMap
            hotspots={hotspots}
            selectedId={selectedId}
            onSelectHotspot={setSelectedId}
            onBoundsChange={setViewportBounds}
            onFilterChange={setMapFilters}
          />
        </div>
        <div className="w-72 flex-shrink-0">
          <PriorityWatchlist
            hotspots={visibleHotspots}
            selectedId={selectedId}
            onSelectHotspot={setSelectedId}
          />
        </div>
      </div>
    </div>
  );
}
