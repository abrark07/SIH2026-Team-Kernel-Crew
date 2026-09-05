/**
 * ThermalMap — MapLibre GL map with WebGL circle layers.
 *
 * Performance: All events are rendered as WebGL data-driven circle
 * layers via GeoJSON Source + Layer — no React DOM <Marker> loop.
 * This supports 5,000+ events without lag.
 *
 * Data: Consumed from the real ML pipeline output via props.
 *   classification: "Industrial" | "Uncertain"
 *   behaviorType:   "Persistent" | "Transient"
 *   thermal fields: meanFrp, maxFrp, meanBrightness
 *   spatial:        spatialDiameterKm, activeDays
 */

import { useRef, useEffect, useState, useMemo, useCallback } from "react";
import { Link } from "react-router-dom";
import Map, { Popup, Source, Layer } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import { classStyle } from "../data/classificationStyle";
import { behaviorStyle } from "../data/behaviorStyle";

// ── Color constants from classificationStyle ───────────────────────
const CLASS_COLORS = {
  Industrial: "#0F6B6E",
  Uncertain:  "#D9A521",
};

// ── GeoJSON builder ────────────────────────────────────────────────
function buildGeoJSON(hotspots, activeFilters) {
  return {
    type: "FeatureCollection",
    features: hotspots
      .filter((h) => activeFilters[h.classification])
      .map((h) => ({
        type: "Feature",
        id: h.id,
        geometry: { type: "Point", coordinates: [h.lng, h.lat] },
        properties: {
          id:             h.id,
          classification: h.classification,
          behaviorType:   h.behaviorType,
          meanFrp:        h.meanFrp ?? 0,
          maxFrp:         h.maxFrp ?? 0,
          activeDays:     h.activeDays ?? 0,
          detectionCount: h.detectionCount ?? 0,
          // Encode color as property for data-driven style
          color: CLASS_COLORS[h.classification] ?? "#888",
        },
      })),
  };
}

// ── Popup content from real ML fields ─────────────────────────────
function MLPopup({ hotspot, onClose }) {
  const cs = classStyle[hotspot.classification] || {};
  const bs = behaviorStyle[hotspot.behaviorType] || {};

  return (
    <Popup
      longitude={hotspot.lng}
      latitude={hotspot.lat}
      onClose={onClose}
      closeOnClick={false}
      maxWidth="280px"
    >
      <div className="font-sans text-charcoal p-1">
        <div className="font-serif font-bold text-sm mb-1">Event {hotspot.id}</div>

        {/* Classification badge */}
        <span
          className="inline-block text-xs text-white px-2 py-0.5 rounded"
          style={{ background: cs.color || "#888" }}
        >
          {cs.label || hotspot.classification}
        </span>

        {/* Behavior badge */}
        {hotspot.behaviorType && (
          <span
            className="inline-block text-xs text-white px-2 py-0.5 rounded ml-1"
            style={{ background: bs.color || "#888" }}
          >
            {hotspot.behaviorType}
          </span>
        )}

        {/* Real thermal metrics */}
        <div className="text-xs mt-2 text-gray-600 space-y-0.5">
          {hotspot.meanFrp != null && (
            <div>FRP: <strong>{hotspot.meanFrp.toFixed(2)} MW</strong> mean / {hotspot.maxFrp?.toFixed(2)} MW max</div>
          )}
          {hotspot.meanBrightness != null && (
            <div>Brightness (Ti4): <strong>{hotspot.meanBrightness.toFixed(1)} K</strong></div>
          )}
          {hotspot.activeDays != null && (
            <div>Active: <strong>{hotspot.activeDays}</strong> of {hotspot.durationDays} days</div>
          )}
          {hotspot.detectionCount != null && (
            <div>Detections: <strong>{hotspot.detectionCount}</strong></div>
          )}
          {hotspot.spatialDiameterKm != null && (
            <div>Spatial extent: <strong>{hotspot.spatialDiameterKm.toFixed(2)} km</strong></div>
          )}
        </div>

        {/* OSM context */}
        {hotspot.osmEvidence != null && (
          <div className="text-[11px] mt-2 text-gray-500 italic border-t border-charcoal/10 pt-2">
            {hotspot.osmEvidence
              ? "OSM industrial facility within 5 km"
              : "No OSM industrial facility within 5 km"}
          </div>
        )}
        {hotspot.nearestFactoryKm != null && (
          <div className="text-[11px] text-gray-500">
            Nearest factory: {hotspot.nearestFactoryKm.toFixed(1)} km
          </div>
        )}

        <Link
          to={`/facility/${hotspot.id}`}
          className="text-xs text-gold underline mt-2 block"
        >
          View Full Details →
        </Link>
      </div>
    </Popup>
  );
}

// ── Main Component ─────────────────────────────────────────────────
export default function ThermalMap({ hotspots, selectedId, onSelectHotspot, onBoundsChange, onFilterChange }) {
  const mapRef = useRef(null);

  const [activeFilters, setActiveFilters] = useState({
    Industrial: true,
    Uncertain: true,
  });
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [popupHotspot, setPopupHotspot] = useState(null);

  useEffect(() => {
    if (onFilterChange) onFilterChange(activeFilters);
  }, [activeFilters, onFilterChange]);

  const handleMoveEnd = useCallback((e) => {
    if (onBoundsChange && e.target) {
      const bounds = e.target.getBounds();
      onBoundsChange([
        bounds.getWest(),
        bounds.getSouth(),
        bounds.getEast(),
        bounds.getNorth(),
      ]);
    }
  }, [onBoundsChange]);

  // Build GeoJSON for the WebGL layer
  const geojsonData = useMemo(
    () => buildGeoJSON(hotspots, activeFilters),
    [hotspots, activeFilters]
  );

  // Fly to selected event
  useEffect(() => {
    if (!selectedId || !mapRef.current) return;
    const h = hotspots.find((h) => h.id === selectedId);
    if (h) {
      mapRef.current.flyTo({
        center: [h.lng, h.lat],
        zoom: 9,
        pitch: 45,
        duration: 1200,
      });
      setPopupHotspot(h);
    }
  }, [selectedId]);

  function toggleFilter(key) {
    setActiveFilters((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  // Click handler on circle layer
  const handleMapClick = useCallback(
    (e) => {
      const features = e.features;
      if (!features || features.length === 0) {
        setPopupHotspot(null);
        onSelectHotspot(null);
        return;
      }
      const clicked = features[0];
      const id = clicked.properties?.id;
      const h = hotspots.find((h) => h.id === id);
      if (h) {
        setPopupHotspot(h);
        onSelectHotspot(h.id);
      }
    },
    [hotspots, onSelectHotspot]
  );

  // Cursor style
  const [cursor, setCursor] = useState("grab");

  // Count stats from the full hotspot list
  const industrialCount = hotspots.filter((h) => h.classification === "Industrial").length;
  const uncertainCount = hotspots.filter((h) => h.classification === "Uncertain").length;
  const persistentCount = hotspots.filter((h) => h.behaviorType === "Persistent").length;

  // ── MapLibre Layer definitions ─────────────────────────────────
  const circleLayer = {
    id: "events-circle",
    type: "circle",
    source: "events",
    paint: {
      "circle-radius": [
        "interpolate", ["linear"], ["zoom"],
        4, 3,
        8, 5,
        12, 8,
      ],
      "circle-color": ["get", "color"],
      "circle-opacity": 0.85,
      "circle-stroke-width": [
        "case",
        ["==", ["get", "id"], selectedId ?? ""],
        3,
        1,
      ],
      "circle-stroke-color": [
        "case",
        ["==", ["get", "id"], selectedId ?? ""],
        "#B8923A",
        "rgba(255,255,255,0.6)",
      ],
    },
  };

  const heatmapLayer = {
    id: "events-heatmap",
    type: "heatmap",
    source: "events",
    paint: {
      "heatmap-weight": ["interpolate", ["linear"], ["get", "maxFrp"], 0, 0.3, 50, 1.5],
      "heatmap-intensity": 2.0,
      "heatmap-radius": 50,
      "heatmap-opacity": 0.9,
      "heatmap-color": [
        "interpolate", ["linear"], ["heatmap-density"],
        0,   "rgba(0,0,0,0)",
        0.1, "#3D1F5C",
        0.3, "#7A2F8F",
        0.5, "#D9A521",
        0.7, "#E8621F",
        1,   "#B31217",
      ],
    },
  };

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Map
        ref={mapRef}
        initialViewState={{ longitude: 83.5, latitude: 23.0, zoom: 5.5, pitch: 20 }}
        style={{ width: "100%", height: "100%", position: "absolute", inset: 0 }}
        mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
        cursor={cursor}
        interactiveLayerIds={["events-circle"]}
        onClick={handleMapClick}
        onMouseEnter={() => setCursor("pointer")}
        onMouseLeave={() => setCursor("grab")}
        onMoveEnd={handleMoveEnd}
        onLoad={handleMoveEnd}
      >
        <Source id="events" type="geojson" data={geojsonData}>
          {showHeatmap ? (
            <Layer {...heatmapLayer} />
          ) : (
            <Layer {...circleLayer} />
          )}
        </Source>

        {popupHotspot && !showHeatmap && (
          <MLPopup
            hotspot={popupHotspot}
            onClose={() => { setPopupHotspot(null); onSelectHotspot(null); }}
          />
        )}
      </Map>

      {/* ── Filter Panel ───────────────────────────────────────── */}
      <div className="absolute top-4 left-4 bg-ivory/95 border border-charcoal/20 rounded-lg px-4 py-3 shadow-md">
        <div className="text-xs font-serif font-bold text-charcoal mb-2">Classify & Filter</div>
        {Object.keys(activeFilters).map((key) => (
          <label key={key} className="flex items-center gap-2 mb-1.5 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={activeFilters[key]}
              onChange={() => toggleFilter(key)}
              className="accent-teal w-3.5 h-3.5"
            />
            <span
              className="w-3 h-3 rounded-full"
              style={{ background: CLASS_COLORS[key] || "#888" }}
            />
            <span className="text-xs text-charcoal">{classStyle[key]?.label || key}</span>
            <span className="text-xs text-gray-400 ml-auto">
              ({hotspots.filter((h) => h.classification === key).length})
            </span>
          </label>
        ))}
        <div className="border-t border-charcoal/10 mt-2 pt-2">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={showHeatmap}
              onChange={() => setShowHeatmap((v) => !v)}
              className="accent-gold w-3.5 h-3.5"
            />
            <span className="text-xs text-charcoal">Show Density Heatmap</span>
          </label>
        </div>
      </div>

      {/* ── Legend ─────────────────────────────────────────────── */}
      <div className="absolute top-4 right-4 bg-ivory/95 border border-charcoal/20 rounded-lg px-4 py-3 shadow-md text-xs">
        <div className="font-serif font-bold text-charcoal mb-2">Legend</div>
        {Object.entries(CLASS_COLORS).map(([key, color]) => (
          <div key={key} className="flex items-center gap-2 mb-1.5">
            <span className="w-3 h-3 rounded-full" style={{ background: color }} />
            <span className="text-charcoal">{classStyle[key]?.label || key}</span>
          </div>
        ))}
        <div className="border-t border-charcoal/10 pt-2 mt-2">
          <div className="font-semibold text-gray-500 mb-1">Behaviour</div>
          {Object.entries(behaviorStyle).map(([key, style]) => (
            <div key={key} className="flex items-center gap-1.5 mb-1">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: style.color }} />
              {key}
            </div>
          ))}
        </div>
      </div>

      {/* ── Status bar ─────────────────────────────────────────── */}
      <div className="absolute bottom-4 left-4 bg-ivory/95 border border-charcoal/20 rounded-lg px-4 py-2 shadow-md">
        <span className="text-xs font-serif font-bold text-charcoal">
          {geojsonData.features.length} of {hotspots.length} events shown
          {" · "}{industrialCount} Industrial · {uncertainCount} Uncertain
          {" · "}{persistentCount} Persistent
        </span>
      </div>
    </div>
  );
}
