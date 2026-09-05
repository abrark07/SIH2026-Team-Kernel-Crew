# GeoSentinel

**AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources**
Smart India Hackathon 2026 | PS 26162 | Organization: National Technical Research Organisation (NTRO)

---

## Overview

GeoSentinel is a GIS-based intelligence platform that automatically detects, classifies, and monitors industrial thermal sources using NASA VIIRS satellite data and OpenStreetMap infrastructure context.

Raw satellite fire-detection systems like NASA FIRMS can tell you that heat exists somewhere on Earth, but not what kind of heat it is. GeoSentinel closes that gap: it distinguishes persistent industrial thermal activity from transient events such as wildfires or agricultural burning, ranks flagged sources by real-world risk, and flags abnormal behavior against each source's own historical baseline, giving regulators an evidence-based, auditable way to prioritize what needs attention first.

---

## The Problem

Industrial facilities such as oil refineries, petrochemical complexes, thermal power plants, steel industries, mining areas, and LNG terminals generate thermal signatures observable from space. Current satellite-based fire monitoring systems such as NASA FIRMS provide thermal anomaly detections but do not distinguish between industrial fires, gas flares, agricultural burning, mining activity, and wildfires. This creates false alarms for disaster management systems and leaves unregistered or abnormal industrial activity undetected.

## The Solution

GeoSentinel classifies every detected thermal event using a behavior-first, evidence-based pipeline, never guessing where evidence is insufficient, and presents the results on a live, interactive 3D map dashboard.


| Stage | What Happens |
|---|---|
| 1. Ingestion | Nighttime VIIRS detections for the target region and date range (lat/lon, FRP, brightness temperature bands TI4/TI5) |
| 2. Daily Spatial Objects | Agglomerative Clustering (complete linkage, 375m distance threshold) groups same-day detections into coherent spatial objects, avoiding arbitrary grid cells |
| 3. Temporal Event Linking | BallTree nearest-neighbor search links daily objects across consecutive days (max 3-day gap) via Union-Find into full events |
| 4. Feature Engineering | 11 behavioral features per event: mean/max FRP, mean/max brightness (TI4, TI5), active days, duration, activity frequency, detections per active day, spatial diameter |
| 5. Scaling | RobustScaler (median/IQR-based), resistant to the extreme outliers common in thermal satellite data |
| 6. Behavior Clustering | K-Means (K=2, unsupervised) groups events purely by behavior into Persistent or Transient, with no location data used at this stage |
| 7. Contextual Evidence | Independent check against OpenStreetMap industrial infrastructure (factories, mines, power plants, brick kilns) within 5km |
| 8. Final Decision | Deterministic rule: Persistent maps to Industrial. Transient plus OSM evidence maps to Industrial. Otherwise, Uncertain. The system never emits a false Non-Industrial claim |

### Why This Design

- Event-based, not grid-based: avoids treating an arbitrary spatial box as the definition of an event
- Behavior and context kept separate: tested combined clustering scored worse (silhouette 0.8427) than behavior-only (0.8461), since mixing them let geography quietly define behavior
- Conservative by design: the system abstains as Uncertain rather than emitting a false negative when evidence is insufficient
- Fully deterministic final decision: no hidden weights or hand-tuned scores, the final rule is simple and auditable

### Validation Results

| Metric | Result |
|---|---|
| Labelled events evaluated | 55 |
| Confidently classified | 24 (43.64% coverage) |
| Left as Uncertain | 31 |
| Industrial precision (confident cases) | 95.83% |
| Industrial recall (confident cases) | 100% |

Low coverage is intentional. The system is designed to be right when it commits to an answer, rather than forcing a guess on every case.

### What Is Not In the Deployed Path

For transparency: WorldCover land-cover data and Isolation Forest anomaly detection were explored during development but are not part of the final frozen decision pipeline. The earlier weighted-scoring approach (72.73% validation accuracy) was superseded by the current deterministic rule-based decision layer.

---

## Key Innovations Beyond the Core Requirement

**Priority Score**
Ranks every flagged source by real-world risk, combining population proximity and behavioral trend, so regulators know what to investigate first rather than just what exists.

**Abnormality Detection**
Compares a source's current thermal behavior (FRP, event duration, detection frequency) against its own historical baseline, flagging deviations as Normal, Elevated, or Abnormal, turning detection into a behavioral audit trail.

---

## Tech Stack

**Data Sources**
- NASA FIRMS / VIIRS (thermal detections, historical archive)
- OpenStreetMap (industrial infrastructure context)
- Population density data (Priority Score input)

**ML and Data Processing**
- Python, Pandas, NumPy
- scikit-learn (Agglomerative Clustering, K-Means, RobustScaler)
- BallTree spatial indexing (haversine distance)

**Geospatial**
- PostGIS (spatial database, spatial joins, indexing)
- GeoPandas

**Backend**
- FastAPI
- TimescaleDB (time-series storage)
- Twilio (WhatsApp/SMS alerts)

**Frontend**
- React + Vite
- MapLibre GL JS (3D terrain, satellite/hybrid basemap via MapTiler)
- Recharts (behavioral timeline visualization)
- Tailwind CSS

**Infrastructure**
- Docker
- GitHub Actions (CI)
- Render / Railway (deployment)

---

## Frontend Features

- Live 3D map with tilted terrain view, satellite and label overlay, color-coded classification markers with confidence-based opacity
- Classification filter toggles to show or hide Industrial, Wildfire, and Anomaly layers interactively
- Density heatmap view toggling between individual markers and a risk-weighted density overlay
- Priority Watchlist ranking sources by population impact and behavioral deviation, with click-to-fly-to-location
- Facility Detail view showing full behavioral timeline per source, baseline-vs-current comparison, and monsoon-visibility-aware persistence calculation
- Explainable classifications, with every popup stating why a source was classified the way it was

---

## Project Structure


---

## Running Locally

```bash
npm install
npm run dev
```

Requires a `.env` file in the project root with:
---

## ML Pipeline Architecture

The classification pipeline is intentionally modular, separating how a thermal source behaves from where it is located, so geography never silently defines behavioral patterns.


---

## Problem Statement Deliverables Addressed

1. Classification and segregation of industrial fires from forest fires and other natural fires
2. GIS-based solution for data storage and visualization of the output as an overlay over maps

Both are satisfied by the live 3D classified map view, with Priority Score and Abnormality Detection layered on top as additional innovation beyond the core requirement.

---

## Team

Kernel Crew - Smart India Hackathon 2026, PS 26162
