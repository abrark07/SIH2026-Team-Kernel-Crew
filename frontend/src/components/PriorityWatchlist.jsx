/**
 * PriorityWatchlist — sidebar ranking driven by real ML fields.
 *
 * Removed fake fields: population, deviationScore, priorityScore (invented).
 * Now uses: classification, behaviorType, meanFrp, activeDays, detectionCount.
 *
 * Sorted by detection_count (proxy for event significance from ML data).
 * Pagination: shows PAGE_SIZE items at a time to avoid rendering all 4893 rows.
 */

import { useState } from "react";
import { classStyle } from "../data/classificationStyle";
import { behaviorStyle } from "../data/behaviorStyle";

const PAGE_SIZE = 50;

export default function PriorityWatchlist({ hotspots, selectedId, onSelectHotspot }) {
  const [page, setPage] = useState(0);

  // Sort by detection count descending — real ML metric
  const ranked = [...hotspots].sort(
    (a, b) => (b.detectionCount || 0) - (a.detectionCount || 0)
  );

  const totalPages = Math.ceil(ranked.length / PAGE_SIZE);
  const pageItems = ranked.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="w-full h-full bg-ivory border-l border-charcoal/20 flex flex-col">
      <div className="p-4 border-b border-charcoal/10">
        <h2 className="font-serif text-lg text-teal font-bold">Priority Watchlist</h2>
        <p className="text-xs text-gray-500 mt-0.5">
          {ranked.length} events · ranked by detection count
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {pageItems.map((h, i) => {
          const rank = page * PAGE_SIZE + i + 1;
          const cs = classStyle[h.classification] || {};
          const bs = behaviorStyle[h.behaviorType] || {};
          const isSelected = selectedId === h.id;

          return (
            <div
              key={h.id}
              onClick={() => onSelectHotspot(h.id)}
              className={`py-2.5 px-2 border-b border-charcoal/10 cursor-pointer hover:bg-gold/5 transition-colors rounded ${
                isSelected ? "bg-gold/20 border-l-4 border-gold" :
                rank === 1 ? "bg-gold/10 border-l-4 border-gold" : ""
              }`}
            >
              <div className="flex justify-between items-center">
                <span className="font-serif font-bold text-gold text-sm">
                  {String(rank).padStart(2, "0")}
                </span>
                <div className="flex gap-1">
                  {h.classification && (
                    <span
                      className="text-[10px] text-white px-1.5 py-0.5 rounded"
                      style={{ background: cs.color || "#888" }}
                    >
                      {cs.label || h.classification}
                    </span>
                  )}
                  {h.behaviorType && (
                    <span
                      className="text-[10px] text-white px-1.5 py-0.5 rounded"
                      style={{ background: bs.color || "#888" }}
                    >
                      {h.behaviorType}
                    </span>
                  )}
                </div>
              </div>

              <div className="font-serif text-sm text-charcoal mt-0.5">Event {h.id}</div>

              <div className="text-xs text-gray-500 mt-0.5 space-y-0.5">
                {h.detectionCount != null && (
                  <div>{h.detectionCount} detections · {h.activeDays ?? "?"} active days</div>
                )}
                {h.meanFrp != null && (
                  <div>FRP {h.meanFrp.toFixed(1)} MW mean / {h.maxFrp?.toFixed(1)} MW max</div>
                )}
                {h.osmEvidence != null && (
                  <div className="italic">{h.osmEvidence ? "✓ OSM industrial evidence" : "No OSM evidence"}</div>
                )}
              </div>

              {/* Detection count bar */}
              <div className="w-full bg-gray-200 h-1 rounded mt-1.5">
                <div
                  className="bg-gold h-1 rounded"
                  style={{
                    width: `${Math.min(100, ((h.detectionCount || 0) / (ranked[0]?.detectionCount || 1)) * 100)}%`
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-2 border-t border-charcoal/10 text-xs text-gray-500">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-2 py-1 rounded hover:bg-gray-100 disabled:opacity-30"
          >
            ← Prev
          </button>
          <span>Page {page + 1} / {totalPages}</span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page === totalPages - 1}
            className="px-2 py-1 rounded hover:bg-gray-100 disabled:opacity-30"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
