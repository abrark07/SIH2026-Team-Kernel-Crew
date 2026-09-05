/**
 * Frontend API adapter for the GeoSentinel backend.
 *
 * Aligned to the frozen ML contract. NO values are invented here:
 *   - classification comes from ML final_prediction: "Industrial" | "Uncertain"
 *   - behaviorType comes from frozen KMeans: "Persistent" | "Transient"
 *   - thermal fields are real VIIRS metrics (mean_frp, max_frp, mean_bright_ti4)
 *   - OSM distances are real nearest entity distances in km
 *
 * Removed invented fields: confidence, population, trend, deviationScore,
 *   priorityScore, risk_level, behaviorStatus (Normal/Abnormal).
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Maps a GeoJSON Feature from the API into the hotspot object
 * consumed by UI components.
 *
 * Field mapping from ML → UI:
 *   classification       "Industrial" | "Uncertain"    → classification
 *   behavior_type        "Persistent" | "Transient"    → behaviorType
 *   behavior_cluster     0 | 1                         → behaviorCluster
 *   mean_frp             MW float                      → meanFrp
 *   max_frp              MW float                      → maxFrp
 *   mean_bright_ti4      K float                       → meanBrightness
 *   active_days          int                           → activeDays
 *   duration_days        int                           → durationDays
 *   detection_count      int                           → detectionCount
 *   activity_frequency   float 0-1                     → activityFrequency
 *   spatial_diameter_km  float                         → spatialDiameterKm
 *   nearest_factory_km   float | null                  → nearestFactoryKm
 *   nearest_power_km     float | null                  → nearestPowerKm
 *   osm_industrial_evidence bool                       → osmEvidence
 */
function adaptFeatureToHotspot(feature) {
  const p = feature.properties;
  const [lng, lat] = feature.geometry.coordinates;

  return {
    id: p.event_id,
    lat,
    lng,

    // ML classification — "Industrial" or "Uncertain"
    classification: p.classification || "Uncertain",

    // Behavior from frozen KMeans
    behaviorType: p.behavior_type || null,     // "Persistent" | "Transient"
    behaviorCluster: p.behavior_cluster,

    // Temporal (real feature engineering output)
    activeDays: p.active_days ?? null,
    durationDays: p.duration_days ?? null,
    detectionCount: p.detection_count ?? null,
    activityFrequency: p.activity_frequency ?? null,

    // Thermal (real VIIRS values)
    meanFrp: p.mean_frp ?? null,
    maxFrp: p.max_frp ?? null,
    meanBrightness: p.mean_bright_ti4 ?? null,
    maxBrightness: p.max_bright_ti4 ?? null,

    // Spatial
    spatialDiameterKm: p.spatial_diameter_km ?? null,

    // OSM context
    osmEvidence: p.osm_industrial_evidence ?? null,
    nearestFactoryKm: p.nearest_factory_km ?? null,
    nearestPowerKm: p.nearest_power_km ?? null,
    nearestMineKm: p.nearest_mine_km ?? null,
    nearestIndustrialZoneKm: p.nearest_industrial_zone_km ?? null,
  };
}

/** Fetch all events as adapted hotspot objects. */
export async function fetchHotspots() {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/events`);
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    const geojson = await res.json();
    if (!geojson.features) return [];
    return geojson.features.map(adaptFeatureToHotspot);
  } catch (err) {
    console.warn("[fetchHotspots] Failed:", err.message);
    return [];
  }
}

/** Fetch the raw GeoJSON FeatureCollection (for WebGL layers). */
export async function fetchHotspotsGeoJSON() {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/events`);
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("[fetchHotspotsGeoJSON] Failed:", err.message);
    return { type: "FeatureCollection", features: [] };
  }
}

/** Fetch event detail for the FacilityDetail page. */
export async function fetchEventDetail(eventId) {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/events/${eventId}`);
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.warn("[fetchEventDetail] Failed:", err.message);
    return null;
  }
}

/** Fetch dashboard summary statistics. */
export async function fetchDashboardSummary() {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/dashboard/summary`);
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.warn("[fetchDashboardSummary] Failed:", err.message);
    return null;
  }
}

/** Trigger the ML pipeline on a specific region. */
export async function triggerAnalysis(bbox, startDate, endDate) {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/analysis/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        bbox: bbox,
        start_date: startDate,
        end_date: endDate
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Analysis failed");
    }
    return await res.json();
  } catch (err) {
    console.error("[triggerAnalysis] Failed:", err.message);
    throw err;
  }
}
