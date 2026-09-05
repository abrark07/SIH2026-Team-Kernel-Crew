/**
 * FacilityDetail — full detail view for a single ML thermal event.
 *
 * Removed:
 *   - mockDetectionHistory.js (all imports + usage)
 *   - fabricated time-series charts
 *   - fake fields: population, confidence, priorityScore, deviationScore,
 *     trend, behaviorStatus (Normal/Abnormal)
 *
 * Now displays real ML pipeline fields:
 *   - classification: "Industrial" | "Uncertain"
 *   - behavior_type: "Persistent" | "Transient"
 *   - behavior_cluster: 0 | 1
 *   - temporal: active_days, duration_days, detection_count,
 *               activity_frequency, start_date, end_date
 *   - thermal: mean_frp, max_frp, std_frp, mean_bright_ti4,
 *              max_bright_ti4, mean_bright_ti5, max_bright_ti5,
 *              spatial_diameter_km
 *   - osm_context: osm_industrial_evidence, nearest_*_km distances
 */

import { useParams, Link } from "react-router-dom";
import { useState, useEffect } from "react";
import Map, { Marker } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import { classStyle } from "../data/classificationStyle";
import { behaviorStyle } from "../data/behaviorStyle";
import { fetchEventDetail } from "../api/hotspots";

// ── Stat block component ───────────────────────────────────────────
function StatBlock({ label, value, unit, highlight }) {
  return (
    <div className={`p-3 rounded-lg border ${highlight ? "border-gold/50 bg-gold/5" : "border-charcoal/10 bg-white"}`}>
      <div className="text-[10px] uppercase tracking-wider text-gray-400 mb-1">{label}</div>
      <div className="font-serif font-bold text-lg text-charcoal">
        {value != null ? String(value) : "N/A"}
        {unit && value != null && <span className="text-xs font-normal text-gray-400 ml-1">{unit}</span>}
      </div>
    </div>
  );
}

// ── OSM Evidence row ───────────────────────────────────────────────
function OSMRow({ label, km }) {
  if (km == null) return null;
  const near = km <= 5;
  return (
    <div className={`flex justify-between text-xs py-1 border-b border-charcoal/5 ${near ? "text-teal font-semibold" : "text-gray-500"}`}>
      <span>{label}</span>
      <span>{km.toFixed(2)} km {near && "⚑"}</span>
    </div>
  );
}

export default function FacilityDetail() {
  const { id } = useParams();
  const [event, setEvent] = useState(undefined); // undefined=loading, null=not found

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const data = await fetchEventDetail(id);
      if (!cancelled) setEvent(data || null);
    }
    load();
    return () => { cancelled = true; };
  }, [id]);

  if (event === undefined) {
    return (
      <div className="h-screen flex items-center justify-center font-serif text-teal">
        Loading event {id}…
      </div>
    );
  }

  if (event === null) {
    return (
      <div className="h-screen flex flex-col items-center justify-center font-serif text-charcoal">
        <div className="text-2xl mb-4">Event not found</div>
        <Link to="/" className="text-gold underline">← Back to map</Link>
      </div>
    );
  }

  const cs = classStyle[event.classification] || {};
  const bs = behaviorStyle[event.behavior_type] || {};
  const loc = event.location || {};
  const temporal = event.temporal || {};
  const thermal = event.thermal || {};
  const osm = event.osm_context || {};

  const activityPct =
    temporal.active_days != null && temporal.duration_days != null && temporal.duration_days > 0
      ? Math.round((temporal.active_days / temporal.duration_days) * 100)
      : null;

  return (
    <div className="min-h-screen bg-ivory">
      {/* Header */}
      <div className="border-b border-charcoal/10 px-8 py-4 flex items-center justify-between">
        <div>
          <Link to="/" className="text-xs text-gold underline mr-4">← Map</Link>
          <Link to="/list" className="text-xs text-gold underline">← Rankings</Link>
        </div>
        <div className="flex gap-2">
          {event.classification && (
            <span
              className="text-xs text-white px-3 py-1 rounded-full font-semibold"
              style={{ background: cs.color || "#888" }}
            >
              {cs.label || event.classification}
            </span>
          )}
          {event.behavior_type && (
            <span
              className="text-xs text-white px-3 py-1 rounded-full"
              style={{ background: bs.color || "#888" }}
            >
              {event.behavior_type} (Cluster {event.behavior_cluster})
            </span>
          )}
        </div>
      </div>

      <div className="px-8 py-6 grid grid-cols-3 gap-6">
        {/* Left column: identity + temporal + thermal */}
        <div className="col-span-2 space-y-6">

          {/* Identity */}
          <div>
            <h1 className="font-serif text-3xl text-teal font-bold">Event {event.event_id}</h1>
            {loc.latitude != null && (
              <p className="text-sm text-gray-500 mt-1 font-mono">
                {loc.latitude.toFixed(5)}, {loc.longitude.toFixed(5)}
              </p>
            )}
          </div>

          {/* Temporal stats */}
          <div>
            <h2 className="font-serif text-lg text-charcoal font-bold mb-3">Temporal Activity</h2>
            <div className="grid grid-cols-4 gap-3">
              <StatBlock label="Active Days" value={temporal.active_days} />
              <StatBlock label="Duration" value={temporal.duration_days} unit="days" />
              <StatBlock label="Detections" value={temporal.detection_count} highlight />
              <StatBlock
                label="Activity Rate"
                value={activityPct != null ? `${activityPct}%` : null}
                highlight={activityPct != null && activityPct > 70}
              />
            </div>
            {temporal.start_date && (
              <p className="text-xs text-gray-400 mt-2">
                Period: {String(temporal.start_date)} → {String(temporal.end_date)}
              </p>
            )}
            {temporal.detections_per_active_day != null && (
              <p className="text-xs text-gray-400 mt-1">
                ~{temporal.detections_per_active_day.toFixed(1)} detections per active day
              </p>
            )}
          </div>

          {/* Thermal stats */}
          <div>
            <h2 className="font-serif text-lg text-charcoal font-bold mb-3">VIIRS Thermal Metrics</h2>
            <div className="grid grid-cols-4 gap-3">
              <StatBlock label="Mean FRP" value={thermal.mean_frp?.toFixed(2)} unit="MW" />
              <StatBlock label="Max FRP" value={thermal.max_frp?.toFixed(2)} unit="MW" highlight />
              <StatBlock label="Mean Brightness (Ti4)" value={thermal.mean_bright_ti4?.toFixed(1)} unit="K" />
              <StatBlock label="Max Brightness (Ti4)" value={thermal.max_bright_ti4?.toFixed(1)} unit="K" />
            </div>
            <div className="grid grid-cols-3 gap-3 mt-3">
              <StatBlock label="Mean Brightness (Ti5)" value={thermal.mean_bright_ti5?.toFixed(1)} unit="K" />
              <StatBlock label="FRP Std Dev" value={thermal.std_frp?.toFixed(2)} unit="MW" />
              <StatBlock label="Spatial Diameter" value={thermal.spatial_diameter_km?.toFixed(2)} unit="km" />
            </div>
          </div>

          {/* Decision rationale */}
          <div className="rounded-lg border border-charcoal/10 bg-white p-4">
            <h2 className="font-serif text-base text-charcoal font-bold mb-2">Classification Rationale</h2>
            <p className="text-sm text-gray-600">
              {event.behavior_type === "Persistent"
                ? `Behavior type is Persistent (KMeans Cluster ${event.behavior_cluster}). Domain rule: Persistent → Industrial.`
                : event.behavior_type === "Transient" && osm.osm_industrial_evidence
                  ? `Behavior type is Transient (KMeans Cluster ${event.behavior_cluster}), but OSM industrial evidence found within 5 km. Domain rule: Transient + OSM evidence → Industrial.`
                  : event.behavior_type === "Transient"
                    ? `Behavior type is Transient (KMeans Cluster ${event.behavior_cluster}). No OSM industrial evidence within 5 km. Domain rule: Transient + no OSM evidence → Uncertain.`
                    : "Classification determined by domain decision rules on frozen ML behavior output."}
            </p>
          </div>
        </div>

        {/* Right column: map + OSM context */}
        <div className="space-y-4">
          {/* Mini map */}
          {loc.latitude != null && (
            <div className="rounded-lg overflow-hidden border border-charcoal/10 h-52">
              <Map
                initialViewState={{ longitude: loc.longitude, latitude: loc.latitude, zoom: 10 }}
                style={{ width: "100%", height: "100%" }}
                mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
                interactive={false}
                attributionControl={false}
              >
                <Marker longitude={loc.longitude} latitude={loc.latitude}>
                  <div
                    style={{
                      width: 14, height: 14, borderRadius: "50%",
                      background: cs.color || "#888",
                      border: "2px solid white",
                      boxShadow: "0 2px 6px rgba(0,0,0,0.4)"
                    }}
                  />
                </Marker>
              </Map>
            </div>
          )}

          {/* OSM Context */}
          <div className="rounded-lg border border-charcoal/10 bg-white p-4">
            <h2 className="font-serif text-base text-charcoal font-bold mb-2">OSM Industrial Context</h2>
            {osm.osm_industrial_evidence == null ? (
              <p className="text-xs text-gray-400 italic">OSM data not available for this event</p>
            ) : (
              <>
                <div className={`text-xs font-semibold mb-3 ${osm.osm_industrial_evidence ? "text-teal" : "text-gray-400"}`}>
                  {osm.osm_industrial_evidence ? "✓ Industrial facility within 5 km" : "✗ No mapped industrial evidence within 5 km"}
                </div>
                <div className="space-y-0.5">
                  <OSMRow label="Industrial Zone" km={osm.nearest_industrial_zone_km} />
                  <OSMRow label="Factory" km={osm.nearest_factory_km} />
                  <OSMRow label="Works" km={osm.nearest_works_km} />
                  <OSMRow label="Mine / Quarry" km={osm.nearest_mine_km} />
                  <OSMRow label="Brick / Kiln" km={osm.nearest_brick_km} />
                  <OSMRow label="Depot" km={osm.nearest_depot_km} />
                  <OSMRow label="Power Plant" km={osm.nearest_power_km} />
                  <OSMRow label="Other Industry" km={osm.nearest_other_industry_km} />
                </div>
                <p className="text-[10px] text-gray-300 mt-2 italic">⚑ = within 5 km threshold</p>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
