import { behaviorStyle } from "../data/behaviorStyle";

export default function PriorityWatchlist({ hotspots, selectedId, onSelectHotspot }) {
  const ranked = [...hotspots].sort((a, b) => b.priorityScore - a.priorityScore);

  return (
    <div className="w-full h-full bg-ivory border-l border-charcoal/20 p-4 overflow-y-auto">
      <h2 className="font-serif text-lg text-teal font-bold">Priority Watchlist</h2>
      <p className="text-xs text-gray-500 mb-3">Ranked by population impact and behavioural deviation</p>

      {ranked.map((h, i) => (
        <div
          key={h.id}
          onClick={() => onSelectHotspot(h.id)}
          className={`py-3 border-b border-charcoal/10 cursor-pointer hover:bg-gold/5 transition-colors ${
            selectedId === h.id ? "bg-gold/20 border-l-4 border-gold pl-2" : i === 0 ? "bg-gold/10 border-l-4 border-gold pl-2" : ""
          }`}
        >
          <div className="flex justify-between items-start">
            <span className="font-serif font-bold text-gold text-sm">
              {String(i + 1).padStart(2, "0")}
            </span>
            {h.behaviorStatus && (
              <span
                className="text-[10px] text-white px-1.5 py-0.5 rounded"
                style={{ background: behaviorStyle[h.behaviorStatus].color }}
              >
                {h.behaviorStatus}
              </span>
            )}
          </div>
          <div className="font-serif text-sm text-charcoal">{h.name}</div>
          <div className="text-xs text-gray-500">
            Priority {h.priorityScore} - {h.population.toLocaleString()} people nearby
            {h.deviationScore !== undefined && ` - Deviation ${h.deviationScore}%`}
          </div>
          <div className="w-full bg-gray-200 h-1 rounded mt-1">
            <div
              className="bg-gold h-1 rounded"
              style={{ width: `${h.priorityScore * 10}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
