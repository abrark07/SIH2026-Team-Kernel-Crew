import { Link } from "react-router-dom";
import { hotspots } from "../data/hotspots";
import { classStyle } from "../data/classificationStyle";
import { behaviorStyle } from "../data/behaviorStyle";

export default function ListView() {
  const ranked = [...hotspots].sort((a, b) => b.priorityScore - a.priorityScore);
  const industrialCount = hotspots.filter((h) => h.classification === "Industrial Source").length;
  const wildfireCount = hotspots.filter((h) => h.classification === "Wildfire").length;
  const anomalyCount = hotspots.filter((h) => h.classification === "Anomaly").length;
  const abnormalCount = hotspots.filter((h) => h.behaviorStatus === "Abnormal").length;

  return (
    <div className="min-h-screen bg-ivory p-8">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h1 className="font-serif text-3xl text-teal font-bold">Priority Rankings</h1>
          <p className="text-sm italic text-gray-500 mt-1">
            Segregated by classification, ranked by population impact and behavioural deviation
          </p>
        </div>
        <Link to="/" className="text-gold underline font-sans text-sm">
          Map - List
        </Link>
      </div>

      <p className="text-xs text-charcoal mb-6">
        {industrialCount} Industrial Sources - {wildfireCount} Wildfires - {anomalyCount} Anomalies -{" "}
        <span className="font-semibold" style={{ color: behaviorStyle.Abnormal.color }}>
          {abnormalCount} Abnormal Behaviour Flagged
        </span>
      </p>

      <div className="flex gap-8">
        <div className="w-40 flex-shrink-0">
          <div className="text-xs font-sans text-charcoal space-y-2">
            <div className="text-gold underline cursor-pointer">All</div>
            <div className="hover:text-gold cursor-pointer">Industrial Source</div>
            <div className="hover:text-gold cursor-pointer">Wildfire</div>
            <div className="hover:text-gold cursor-pointer">Anomaly</div>
            <div className="border-t border-charcoal/10 pt-2 mt-2 text-[11px] text-gray-400 uppercase tracking-wide">
              Behaviour
            </div>
            <div className="hover:text-gold cursor-pointer">Abnormal</div>
            <div className="hover:text-gold cursor-pointer">Elevated</div>
            <div className="hover:text-gold cursor-pointer">Normal</div>
          </div>
        </div>

        <table className="flex-1 border-collapse">
          <thead>
            <tr className="text-xs uppercase tracking-wider text-gray-500 border-b border-charcoal/20">
              <th className="text-left py-2 font-sans font-normal">Rank</th>
              <th className="text-left py-2 font-sans font-normal">Location</th>
              <th className="text-left py-2 font-sans font-normal">Class</th>
              <th className="text-left py-2 font-sans font-normal">Behaviour</th>
              <th className="text-left py-2 font-sans font-normal">Priority Score</th>
              <th className="text-left py-2 font-sans font-normal">Population Nearby</th>
              <th className="text-left py-2 font-sans font-normal">FRP / Brightness</th>
              <th className="text-left py-2 font-sans font-normal">Trend</th>
            </tr>
          </thead>
          <tbody>
            {ranked.map((h, i) => (
              <tr
                key={h.id}
                className={`border-b border-charcoal/10 hover:bg-gold/5 ${
                  i === 0 ? "bg-gold/10 border-l-4 border-gold" : ""
                }`}
              >
                <td className="py-3 font-serif font-bold text-gold">
                  {String(i + 1).padStart(2, "0")}
                </td>
                <td className="py-3">
                  <Link to={`/facility/${h.id}`} className="font-serif text-sm hover:underline">
                    {h.name}, {h.state}
                  </Link>
                </td>
                <td className="py-3">
                  <span
                    className="inline-block w-2 h-2 rounded-full mr-2"
                    style={{ background: classStyle[h.classification]?.color }}
                  />
                  <span className="text-xs">{h.classification}</span>
                </td>
                <td className="py-3">
                  {h.behaviorStatus ? (
                    <span
                      className="text-[10px] text-white px-2 py-0.5 rounded"
                      style={{ background: behaviorStyle[h.behaviorStatus].color }}
                    >
                      {h.behaviorStatus} ({h.deviationScore}%)
                    </span>
                  ) : (
                    <span className="text-[10px] text-gray-400">-</span>
                  )}
                </td>
                <td className="py-3">
                  <div className="flex items-center gap-2">
                    <span className="font-serif font-bold text-sm">{h.priorityScore}</span>
                    <div className="w-16 bg-gray-200 h-1.5 rounded">
                      <div
                        className="bg-gold h-1.5 rounded"
                        style={{ width: `${h.priorityScore * 10}%` }}
                      />
                    </div>
                  </div>
                </td>
                <td className="py-3 text-sm">{h.population.toLocaleString()}</td>
                <td className="py-3 text-xs text-gray-500">
                  {h.frp} MW / {h.brightness}K
                </td>
                <td className="py-3 text-xs">
                  {h.trend === "rising" && "up rising"}
                  {h.trend === "stable" && "stable"}
                  {h.trend === "declining" && "down declining"}
                  {h.trend === "seasonal" && "up seasonal"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
