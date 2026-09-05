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

---

## ML Pipeline Architecture

The classification pipeline is intentionally modular, separating how a thermal source behaves from where it is located, so geography never silently defines behavioral patterns.
