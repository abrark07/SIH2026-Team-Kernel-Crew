const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const CLASSIFICATION_MAP = {
  "industrial-like": "Industrial Source",
  "non-industrial": "Wildfire",
  "uncertain": "Anomaly",
};

function adaptFeatureToHotspot(feature) {
  const p = feature.properties;
  const [lng, lat] = feature.geometry.coordinates;

  return {
    id: p.event_id,
    name: p.event_id,
    state: "Unknown region",
    lat,
    lng,
    classification: CLASSIFICATION_MAP[p.classification] || "Anomaly",
    confidence: p.confidence !== null && p.confidence !== undefined ? Math.round(p.confidence * 100) : null,
    brightness: null,
    persistence: null,
    observedDays: p.active_days ?? null,
    priorityScore: p.priority_score ?? null,
    riskLevel: p.risk_level ?? null,
    population: null,
    firstDetected: null,
  };
}

export async function fetchHotspots() {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/events`);
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    const geojson = await res.json();
    if (!geojson.features || geojson.features.length === 0) return null;
    return geojson.features.map(adaptFeatureToHotspot);
  } catch (err) {
    console.warn("fetchHotspots failed, will fall back to mock data:", err.message);
    return null;
  }
}

export async function fetchEventDetail(eventId) {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/events/${eventId}`);
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    const d = await res.json();

    return {
      id: d.event_id,
      name: d.industrial_context?.nearest_facility || d.event_id,
      state: "Unknown region",
      lat: d.location.latitude,
      lng: d.location.longitude,
      classification: CLASSIFICATION_MAP[d.classification] || "Anomaly",
      confidence: d.confidence !== null && d.confidence !== undefined ? Math.round(d.confidence * 100) : null,
      brightness: d.thermal?.mean_brightness ?? null,
      persistence: null,
      observedDays: d.temporal?.active_days ?? null,
      priorityScore: d.priority?.score ?? null,
      riskLevel: d.priority?.risk_level ?? null,
      population: null,
      firstDetected: d.temporal?.first_detected ?? null,
    };
  } catch (err) {
    console.warn("fetchEventDetail failed:", err.message);
    return null;
  }
}

export async function fetchDashboardSummary() {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/dashboard/summary`);
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("fetchDashboardSummary failed:", err.message);
    return null;
  }
}

export async function checkBackendHealth() {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/health`);
    if (!res.ok) return false;
    const data = await res.json();
    return data.status === "ok";
  } catch (err) {
    return false;
  }
}

// India bounding box as a sensible default region for analysis runs.
// Last 30 days as a sensible default date range.
export async function runAnalysis() {
  try {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);

    const res = await fetch(`${BASE_URL}/api/v1/analysis/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        bbox: [68.0, 6.0, 97.5, 37.5],
        start_date: start.toISOString().split("T")[0],
        end_date: end.toISOString().split("T")[0],
      }),
    });
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("runAnalysis failed:", err.message);
    return null;
  }
}
