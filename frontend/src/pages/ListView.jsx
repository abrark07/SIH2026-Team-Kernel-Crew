/**
 * ListView — paginated tabular ranking of ML events.
 *
 * Removed invented fields: population, trend, deviationScore, behaviorStatus,
 *   priorityScore, frp (old alias), brightness (old alias).
 *
 * Now shows real ML fields:
 *   classification    "Industrial" | "Uncertain"
 *   behaviorType      "Persistent" | "Transient"
 *   meanFrp           MW
 *   maxFrp            MW
 *   meanBrightness    K (Ti4)
 *   activeDays        int
 *   durationDays      int
 *   detectionCount    int
 *   activityFrequency float
 *   osmEvidence       bool
 *
 * Pagination: PAGE_SIZE rows per page to avoid rendering all 4893 at once.
 */

import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { fetchHotspots } from "../api/hotspots";
import { classStyle } from "../data/classificationStyle";
import { behaviorStyle } from "../data/behaviorStyle";

const PAGE_SIZE = 100;

export default function ListView() {
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [filterClass, setFilterClass] = useState("All");
  const [filterBehavior, setFilterBehavior] = useState("All");

  useEffect(() => {
    async function load() {
      const data = await fetchHotspots();
      setHotspots(data || []);
      setLoading(false);
    }
    load();
  }, []);

  // Apply filters
  const filtered = hotspots.filter((h) => {
    if (filterClass !== "All" && h.classification !== filterClass) return false;
    if (filterBehavior !== "All" && h.behaviorType !== filterBehavior) return false;
    return true;
  });

  // Sort by detectionCount descending
  const sorted = [...filtered].sort((a, b) => (b.detectionCount || 0) - (a.detectionCount || 0));
  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);
  const pageItems = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  // Summary counts (full dataset, not page)
  const industrialCount = hotspots.filter((h) => h.classification === "Industrial").length;
  const uncertainCount = hotspots.filter((h) => h.classification === "Uncertain").length;
  const persistentCount = hotspots.filter((h) => h.behaviorType === "Persistent").length;
  const transientCount = hotspots.filter((h) => h.behaviorType === "Transient").length;

  if (loading) {
    return <div className="min-h-screen bg-ivory p-8 font-serif text-teal">Loading events…</div>;
  }

  return (
    <div className="min-h-screen bg-ivory p-8">
      {/* Header */}
      <div className="flex justify-between items-start mb-2">
        <div>
          <h1 className="font-serif text-3xl text-teal font-bold">Event Rankings</h1>
          <p className="text-sm italic text-gray-500 mt-1">
            {hotspots.length} events · ranked by detection count · Jan 2024 VIIRS SNPP nighttime
          </p>
        </div>
        <Link to="/" className="text-gold underline font-sans text-sm">← Map</Link>
      </div>

      {/* Summary strip */}
      <p className="text-xs text-charcoal mb-4">
        {industrialCount} Industrial · {uncertainCount} Uncertain ·{" "}
        {persistentCount} Persistent · {transientCount} Transient
      </p>

      <div className="flex gap-8">
        {/* Filter sidebar */}
        <div className="w-40 flex-shrink-0">
          <div className="text-xs font-sans text-charcoal space-y-2">
            <div className="text-[11px] text-gray-400 uppercase tracking-wide">Classification</div>
            {["All", "Industrial", "Uncertain"].map((c) => (
              <div
                key={c}
                onClick={() => { setFilterClass(c); setPage(0); }}
                className={`cursor-pointer hover:text-gold ${filterClass === c ? "text-gold underline" : ""}`}
              >
                {c}
              </div>
            ))}
            <div className="border-t border-charcoal/10 pt-2 text-[11px] text-gray-400 uppercase tracking-wide">
              Behaviour
            </div>
            {["All", "Persistent", "Transient"].map((b) => (
              <div
                key={b}
                onClick={() => { setFilterBehavior(b); setPage(0); }}
                className={`cursor-pointer hover:text-gold ${filterBehavior === b ? "text-gold underline" : ""}`}
              >
                {b}
              </div>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="text-xs uppercase tracking-wider text-gray-500 border-b border-charcoal/20">
                <th className="text-left py-2 font-sans font-normal">Rank</th>
                <th className="text-left py-2 font-sans font-normal">Event ID</th>
                <th className="text-left py-2 font-sans font-normal">Classification</th>
                <th className="text-left py-2 font-sans font-normal">Behaviour</th>
                <th className="text-left py-2 font-sans font-normal">Detections</th>
                <th className="text-left py-2 font-sans font-normal">Active Days</th>
                <th className="text-left py-2 font-sans font-normal">FRP (mean / max)</th>
                <th className="text-left py-2 font-sans font-normal">Brightness Ti4</th>
                <th className="text-left py-2 font-sans font-normal">OSM Evidence</th>
              </tr>
            </thead>
            <tbody>
              {pageItems.map((h, i) => {
                const rank = page * PAGE_SIZE + i + 1;
                const cs = classStyle[h.classification] || {};
                const bs = behaviorStyle[h.behaviorType] || {};
                return (
                  <tr
                    key={h.id}
                    className={`border-b border-charcoal/10 hover:bg-gold/5 ${rank === 1 ? "bg-gold/10" : ""}`}
                  >
                    <td className="py-3 font-serif font-bold text-gold">
                      {String(rank).padStart(2, "0")}
                    </td>
                    <td className="py-3">
                      <Link to={`/facility/${h.id}`} className="font-serif text-sm hover:underline">
                        {h.id}
                      </Link>
                    </td>
                    <td className="py-3">
                      <span
                        className="inline-block text-xs text-white px-2 py-0.5 rounded"
                        style={{ background: cs.color || "#888" }}
                      >
                        {cs.label || h.classification}
                      </span>
                    </td>
                    <td className="py-3">
                      {h.behaviorType ? (
                        <span
                          className="text-[10px] text-white px-2 py-0.5 rounded"
                          style={{ background: bs.color || "#888" }}
                        >
                          {h.behaviorType}
                        </span>
                      ) : <span className="text-xs text-gray-400">—</span>}
                    </td>
                    <td className="py-3 text-sm font-semibold">{h.detectionCount ?? "—"}</td>
                    <td className="py-3 text-sm">
                      {h.activeDays != null ? `${h.activeDays} / ${h.durationDays ?? "?"}d` : "—"}
                    </td>
                    <td className="py-3 text-xs text-gray-600">
                      {h.meanFrp != null ? `${h.meanFrp.toFixed(1)} / ${h.maxFrp?.toFixed(1)} MW` : "—"}
                    </td>
                    <td className="py-3 text-xs text-gray-600">
                      {h.meanBrightness != null ? `${h.meanBrightness.toFixed(1)} K` : "—"}
                    </td>
                    <td className="py-3 text-xs">
                      {h.osmEvidence == null ? "—" : h.osmEvidence ? "✓ Yes" : "No"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 text-xs text-gray-500">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-3 py-1 border rounded hover:bg-gray-100 disabled:opacity-30"
              >
                ← Previous
              </button>
              <span>
                Page {page + 1} of {totalPages} — showing {pageItems.length} of {sorted.length} filtered events
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page === totalPages - 1}
                className="px-3 py-1 border rounded hover:bg-gray-100 disabled:opacity-30"
              >
                Next →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
