import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import ThermalMap from "../components/ThermalMap";
import PriorityWatchlist from "../components/PriorityWatchlist";
import { fetchHotspots, fetchDashboardSummary } from "../api/hotspots";
import { hotspots as mockHotspots } from "../data/hotspots";

export default function Dashboard() {
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [usingMockData, setUsingMockData] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    async function loadData() {
      const liveData = await fetchHotspots();
      if (liveData && liveData.length > 0) {
        setHotspots(liveData);
        setUsingMockData(false);
      } else {
        setHotspots(mockHotspots);
        setUsingMockData(true);
      }

      const liveSummary = await fetchDashboardSummary();
      if (liveSummary && liveSummary.total_events > 0) {
        setSummary(liveSummary);
      }

      setLoading(false);
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-ivory">
        <div className="flex flex-col items-center gap-3">
          <h1 className="font-serif text-4xl text-teal font-extrabold tracking-tight animate-pulse">
            GeoSentinel
          </h1>
          <p className="text-xs text-charcoal/50 tracking-widest uppercase">
            Scanning thermal signatures across India
          </p>
          <div className="flex gap-1.5 mt-2">
            <span className="w-1.5 h-1.5 rounded-full bg-gold animate-bounce" style={{ animationDelay: "0ms" }} />
            <span className="w-1.5 h-1.5 rounded-full bg-gold animate-bounce" style={{ animationDelay: "150ms" }} />
            <span className="w-1.5 h-1.5 rounded-full bg-gold animate-bounce" style={{ animationDelay: "300ms" }} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-ivory overflow-hidden">
      <header className="flex justify-between items-center px-6 py-4 border-b border-charcoal/10 flex-shrink-0">
        <div>
          <h1 className="font-serif text-3xl text-teal font-extrabold tracking-tight">GeoSentinel</h1>
          <p className="text-xs text-gray-500">Industrial Thermal Intelligence - PS 26162</p>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/list" className="text-xs text-gold underline font-sans">
            Priority Rankings
          </Link>
          <span className="text-xs text-charcoal font-mono">
            {summary
              ? `${summary.total_events} events - ${summary.high_risk_events} high risk`
              : `${hotspots.length} sources - updated 2 min ago`}
            {usingMockData && " (demo data)"}
          </span>
        </div>
      </header>
      <div className="flex flex-1 min-h-0">
        <div className="w-[68%] h-full">
          <ThermalMap
            hotspots={hotspots}
            selectedId={selectedId}
            onSelectHotspot={setSelectedId}
          />
        </div>
        <div className="w-[32%] h-full">
          <PriorityWatchlist
            hotspots={hotspots}
            selectedId={selectedId}
            onSelectHotspot={setSelectedId}
          />
        </div>
      </div>
    </div>
  );
}
