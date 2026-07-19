# GeoRescue — Implementation Guide: 10 Highly Feasible Features

These are the 10 features added to `Abstract_V1.md`, with concrete implementation steps mapped to the existing codebase.

---

## 1. Early Flood Warning Notifications

**What:** Auto-detect when flood severity escalates and alert the user in real time.

**How to implement:**

1. **New file** — `georescue/ml_serving/gis_pipeline/alert_monitor.py`
   - Store last-known severity in `data/processed/severity_history.json`
   - Function `check_escalation(current, previous)` returns an alert if severity increased

2. **Modify** — `georescue/ml_serving/gis_pipeline/pipeline.py` → `run_cycle()`
   - After computing severity, call `check_escalation()`
   - Append result to `latest_status.json` with an `"alert"` field

3. **Modify** — `georescue/georescue/state.py`
   - Add `_default("active_alerts", [])` and `_default("last_known_severity", "")`

4. **Modify** — `georescue/app.py`
   - After pipeline completes, compare `gis_severity` to `last_known_severity`
   - If escalated → `st.toast("⚠️ Severity escalated to HIGH!", icon="🚨")`
   - Show persistent `st.warning()` banner at page top

**Key code pattern:**
```python
# In app.py, after pipeline results are applied:
prev = st.session_state.last_known_severity
curr = st.session_state.gis_severity
if curr and prev and ["low","moderate","high","extreme"].index(curr) > ["low","moderate","high","extreme"].index(prev):
    st.toast(f"⚠️ Flood severity escalated: {prev.upper()} → {curr.upper()}", icon="🚨")
st.session_state.last_known_severity = curr
```

---

## 2. Nearby Shelter Locator

**What:** Query OpenStreetMap for schools, hospitals, community centres and display them on the map.

**How to implement:**

1. **New file** — `georescue/georescue/pois.py`
   ```python
   import requests
   import streamlit as st

   SHELTER_TAGS = [
       'amenity=school', 'amenity=hospital',
       'amenity=community_centre', 'amenity=place_of_worship',
   ]

   @st.cache_data(ttl=3600, show_spinner="Fetching shelters…")
   def fetch_shelters(center_lat, center_lon, radius_m=10000):
       tag_filter = "".join(f'node[{t}](around:{radius_m},{center_lat},{center_lon});' for t in SHELTER_TAGS)
       query = f"[out:json][timeout:25];({tag_filter});out body;"
       resp = requests.get("https://overpass-api.de/api/interpreter", params={"data": query}, timeout=30)
       resp.raise_for_status()
       elements = resp.json().get("elements", [])
       return [
           {
               "name": e.get("tags", {}).get("name", "Unnamed Shelter"),
               "type": e.get("tags", {}).get("amenity", "shelter"),
               "lat": e["lat"], "lon": e["lon"],
           }
           for e in elements if "lat" in e and "lon" in e
       ]
   ```

2. **Modify** — `georescue/georescue/map_layers.py`
   ```python
   def render_shelters(m, shelters, visible=True):
       if not shelters or not visible:
           return
       fg = folium.FeatureGroup(name="Emergency Shelters")
       icon_map = {"hospital": "plus-sign", "school": "education", "community_centre": "home"}
       for s in shelters:
           folium.Marker(
               [s["lat"], s["lon"]],
               popup=f"<b>{s['name']}</b><br>{s['type']}",
               icon=folium.Icon(color="purple", icon=icon_map.get(s["type"], "home"), prefix="glyphicon"),
           ).add_to(fg)
       fg.add_to(m)
   ```

3. **Modify** — `georescue/app.py`
   - Sidebar: `show_shelters = st.checkbox("Emergency shelters", value=False)`
   - Map section: call `render_shelters(base_map, fetch_shelters(center_lat, center_lon), show_shelters)`

---

## 3. Emergency SOS Button

**What:** One-click distress signal with geolocation, severity context, and emergency contacts.

**How to implement:**

1. **New file** — `georescue/georescue/sos.py`
   ```python
   import json
   from datetime import datetime, timezone

   def build_sos_payload(lat, lon, severity, contacts=None):
       return {
           "type": "SOS_DISTRESS",
           "timestamp_utc": datetime.now(timezone.utc).isoformat(),
           "location": {"lat": lat, "lon": lon},
           "google_maps_url": f"https://www.google.com/maps?q={lat},{lon}",
           "flood_severity": severity or "unknown",
           "emergency_contacts": contacts or [],
           "message": f"EMERGENCY: Person at ({lat}, {lon}) requesting immediate assistance. Flood severity: {severity}.",
       }

   def sos_to_text(payload):
       contacts = "\n".join(f"  - {c['name']}: {c['phone']}" for c in payload.get("emergency_contacts", []))
       return (
           f"🆘 SOS DISTRESS SIGNAL\n"
           f"Time: {payload['timestamp_utc']}\n"
           f"Location: {payload['location']['lat']}, {payload['location']['lon']}\n"
           f"Map: {payload['google_maps_url']}\n"
           f"Severity: {payload['flood_severity']}\n"
           f"Contacts:\n{contacts or '  None registered'}\n"
       )
   ```

2. **Modify** — `georescue/app.py` (in left_col, after Actions section)
   ```python
   st.divider()
   if st.button("🆘 EMERGENCY SOS", type="primary", use_container_width=True):
       from georescue.sos import build_sos_payload, sos_to_text
       payload = build_sos_payload(
           st.session_state.start_lat, st.session_state.start_lon,
           st.session_state.gis_severity,
           st.session_state.get("emergency_contacts", []),
       )
       st.error(sos_to_text(payload))
       st.download_button("📥 Download SOS", json.dumps(payload, indent=2),
                          file_name="sos_distress.json", mime="application/json")
   ```

---

## 4. Crowd-Sourced Flood Reporting

**What:** Users submit geotagged flood observations that appear on the map.

**How to implement:**

1. **New file** — `georescue/ml_serving/api/report_routes.py`
   ```python
   import json, uuid
   from datetime import datetime, timezone
   from pathlib import Path
   from fastapi import APIRouter, HTTPException
   from pydantic import BaseModel
   from typing import Optional

   router = APIRouter(prefix="/reports", tags=["Reports"])
   REPORTS_FILE = Path(__file__).parent.parent / "data" / "processed" / "flood_reports.json"

   class FloodReport(BaseModel):
       lat: float
       lon: float
       severity: str  # low / moderate / high / extreme
       description: str
       reporter_name: Optional[str] = "Anonymous"

   def _load():
       if REPORTS_FILE.exists():
           return json.loads(REPORTS_FILE.read_text())
       return []

   def _save(reports):
       REPORTS_FILE.parent.mkdir(parents=True, exist_ok=True)
       REPORTS_FILE.write_text(json.dumps(reports, indent=2))

   @router.post("/flood")
   async def submit_report(report: FloodReport):
       reports = _load()
       entry = report.dict()
       entry["id"] = str(uuid.uuid4())[:8]
       entry["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
       reports.append(entry)
       _save(reports)
       return {"status": "ok", "id": entry["id"]}

   @router.get("/flood")
   async def get_reports():
       return _load()
   ```

2. **Modify** — `georescue/ml_serving/api/app.py`
   ```python
   from api.report_routes import router as report_router
   app.include_router(report_router)
   ```

3. **Modify** — `georescue/georescue/map_layers.py` — add `render_crowd_reports(m, reports, visible)`
   - Display as orange circle markers with popup showing description + timestamp

4. **Modify** — `georescue/app.py` sidebar
   - Add an expander with `st.text_input` for description, `st.selectbox` for severity, submit button

---

## 5. Offline Emergency Maps

**What:** Download the current map + road graph for use without internet.

**How to implement:**

1. **Modify** — `georescue/app.py` (in the Export expander)
   ```python
   import io, tempfile

   # Save map as standalone HTML
   map_html = base_map._repr_html_()
   st.download_button(
       "🗺️ Download Offline Map (HTML)",
       data=map_html,
       file_name="georescue_offline_map.html",
       mime="text/html",
       use_container_width=True,
   )
   ```

2. **Modify** — `georescue/georescue/routing.py` — add disk caching
   ```python
   GRAPH_CACHE = Path(__file__).parent.parent / "data" / "cached_graph.graphml"

   def save_graph_to_disk(graph):
       GRAPH_CACHE.parent.mkdir(parents=True, exist_ok=True)
       ox.save_graphml(graph, GRAPH_CACHE)

   def load_graph_from_disk():
       if GRAPH_CACHE.exists():
           return ox.load_graphml(GRAPH_CACHE)
       return None
   ```

3. **Modify** — `fetch_road_graph()` to try disk cache before network download.

---

## 6. Emergency Contact Sharing

**What:** Store and share emergency contacts; auto-include in SOS and reports.

**How to implement:**

1. **Modify** — `georescue/georescue/state.py`
   ```python
   _default("emergency_contacts", [])  # List of {"name": str, "phone": str, "relationship": str}
   ```

2. **Modify** — `georescue/app.py` sidebar
   ```python
   with st.sidebar.expander("📞 Emergency Contacts"):
       name = st.text_input("Name", key="ec_name")
       phone = st.text_input("Phone", key="ec_phone")
       rel = st.text_input("Relationship", key="ec_rel")
       if st.button("Add Contact"):
           st.session_state.emergency_contacts.append({"name": name, "phone": phone, "relationship": rel})
           st.rerun()
       for i, c in enumerate(st.session_state.emergency_contacts):
           st.caption(f"{c['name']} — {c['phone']} ({c['relationship']})")
   ```

3. **Modify** — `georescue/agents/pipeline.py` → `_build_template_report()`
   - Add a "### 6. EMERGENCY CONTACTS" section listing all registered contacts.

---

## 7. Safe Zone Recommendations

**What:** Identify and display areas outside the flood polygon that are road-accessible.

**How to implement:**

1. **New file** — `georescue/georescue/safe_zones.py`
   ```python
   from shapely.geometry import box, mapping
   from shapely.ops import unary_union

   def compute_safe_zones(flood_geojson, center_lat, center_lon, radius_km=5):
       if not flood_geojson or not flood_geojson.get("features"):
           return None
       from shapely.geometry import shape
       flood_polys = [shape(f["geometry"]) for f in flood_geojson["features"]]
       flood_union = unary_union(flood_polys)
       r = radius_km / 111.0
       bounds = box(center_lon - r, center_lat - r, center_lon + r, center_lat + r)
       safe = bounds.difference(flood_union)
       if safe.is_empty:
           return None
       return {
           "type": "FeatureCollection",
           "features": [{
               "type": "Feature",
               "properties": {"name": "Recommended Safe Zone"},
               "geometry": mapping(safe),
           }],
       }
   ```

2. **Modify** — `georescue/georescue/map_layers.py`
   ```python
   def render_safe_zones(m, safe_geojson, visible=True):
       if not safe_geojson or not visible:
           return
       folium.GeoJson(
           safe_geojson, name="Safe Zones",
           style_function=lambda _: {"fillColor": "#4caf50", "color": "#2e7d32",
                                     "weight": 2, "fillOpacity": 0.2},
       ).add_to(m)
   ```

3. **Modify** — `georescue/app.py`
   - Sidebar: `show_safe_zones = st.checkbox("Safe zone recommendations", value=False)`
   - After flood layer: compute and render safe zones

---

## 8. Flood Prediction Using AI

**What:** Extend the weather query to 7 days; display a precipitation trend chart with projected severity.

**How to implement:**

1. **Modify** — `georescue/ml_serving/gis_pipeline/live_flood_feed.py` → `fetch_live_precipitation()`
   ```python
   params = {
       "latitude": lat, "longitude": lon,
       "hourly": "precipitation,precipitation_probability",
       "past_hours": 24,
       "forecast_hours": 72,   # ← extended from 3 to 72
       "timezone": "UTC",
   }
   ```

2. **New file** — `georescue/ml_serving/gis_pipeline/flood_predictor.py`
   ```python
   import numpy as np

   def predict_severity_trend(precip_values, window=6):
       """Classify each 6-hour window into a severity level."""
       trend = []
       for i in range(0, len(precip_values), window):
           chunk = precip_values[i:i+window]
           mm = sum(v for v in chunk if v is not None)
           if mm < 5: level = "low"
           elif mm < 20: level = "moderate"
           elif mm < 40: level = "high"
           else: level = "extreme"
           trend.append({"hour_offset": i, "precip_mm_6h": round(mm, 1), "severity": level})
       return trend
   ```

3. **Modify** — `georescue/app.py` — add a chart panel below the report
   ```python
   import pandas as pd
   # After pipeline, if weather data available:
   st.subheader("📈 Flood Severity Forecast")
   st.line_chart(pd.DataFrame(trend_data).set_index("hour_offset")["precip_mm_6h"])
   ```

---

## 9. Emergency Supply Location Finder

**What:** Locate pharmacies, fuel stations, supermarkets, police, fire stations on the map.

**How to implement:**

Uses the **same pattern as Feature 2 (Shelter Locator)** — extend `georescue/georescue/pois.py`:

```python
SUPPLY_TAGS = [
    'amenity=pharmacy', 'amenity=fuel', 'shop=supermarket',
    'amenity=police', 'amenity=fire_station',
]

@st.cache_data(ttl=3600, show_spinner="Fetching supply points…")
def fetch_supply_points(center_lat, center_lon, radius_m=10000):
    # Same Overpass query pattern as fetch_shelters()
    tag_filter = "".join(f'node[{t}](around:{radius_m},{center_lat},{center_lon});' for t in SUPPLY_TAGS)
    query = f"[out:json][timeout:25];({tag_filter});out body;"
    resp = requests.get("https://overpass-api.de/api/interpreter", params={"data": query}, timeout=30)
    resp.raise_for_status()
    elements = resp.json().get("elements", [])
    return [
        {"name": e.get("tags",{}).get("name","Unnamed"), "type": e.get("tags",{}).get("amenity") or e.get("tags",{}).get("shop","supply"),
         "lat": e["lat"], "lon": e["lon"]}
        for e in elements if "lat" in e
    ]
```

- Render with `render_supply_points()` using category-specific icons (💊🏪⛽🚒🚓)
- Add sidebar toggle: `show_supplies = st.checkbox("Emergency supplies", value=False)`

---

## 10. Missing Person Reporting

**What:** Register missing persons with last-known location; display on map for SAR coordination.

**How to implement:**

1. **Extend** — `georescue/ml_serving/api/report_routes.py` (shares backend with crowd reports)
   ```python
   class MissingPerson(BaseModel):
       name: str
       age: Optional[int] = None
       last_seen_lat: float
       last_seen_lon: float
       description: str
       contact_phone: str

   MISSING_FILE = Path(__file__).parent.parent / "data" / "processed" / "missing_persons.json"

   @router.post("/missing")
   async def report_missing(person: MissingPerson):
       # Same _load/_save pattern as flood reports
       ...

   @router.get("/missing")
   async def get_missing():
       ...
   ```

2. **Modify** — `georescue/georescue/map_layers.py`
   ```python
   def render_missing_persons(m, persons, visible=True):
       if not persons or not visible:
           return
       fg = folium.FeatureGroup(name="Missing Persons")
       for p in persons:
           folium.Marker(
               [p["last_seen_lat"], p["last_seen_lon"]],
               popup=f"<b>{p['name']}</b> (age {p.get('age','?')})<br>{p['description']}<br>Contact: {p['contact_phone']}",
               icon=folium.Icon(color="orange", icon="user", prefix="fa"),
           ).add_to(fg)
       fg.add_to(m)
   ```

3. **Modify** — `georescue/app.py` — add a "Report Missing Person" expander in left_col with input fields + submit button

---

## File Impact Summary

| File | Features touching it |
|------|---------------------|
| `georescue/app.py` | All 10 |
| `georescue/georescue/state.py` | 1, 6 |
| `georescue/georescue/map_layers.py` | 2, 4, 7, 9, 10 |
| `georescue/agents/pipeline.py` | 1, 6 |
| `georescue/ml_serving/gis_pipeline/live_flood_feed.py` | 8 |
| `georescue/ml_serving/gis_pipeline/pipeline.py` | 1 |
| `georescue/ml_serving/api/app.py` | 4, 10 |
| **New:** `georescue/georescue/pois.py` | 2, 9 |
| **New:** `georescue/georescue/sos.py` | 3 |
| **New:** `georescue/georescue/safe_zones.py` | 7 |
| **New:** `georescue/ml_serving/gis_pipeline/flood_predictor.py` | 8 |
| **New:** `georescue/ml_serving/gis_pipeline/alert_monitor.py` | 1 |
| **New:** `georescue/ml_serving/api/report_routes.py` | 4, 10 |
