# GeoRescue — Feature Feasibility Analysis

> Full codebase scan completed across **all 30+ source files** spanning `agents/`, `georescue/`, `ml_serving/`, and `UI/`.

---

## Summary Matrix

| # | Feature | Verdict | Effort |
|---|---------|---------|--------|
| 1 | Early flood warning notifications | ✅ Highly Feasible | Medium |
| 2 | AI-based safe evacuation routes | ✅ **Already Implemented** | — |
| 3 | Real-time flood risk map | ✅ **Already Implemented** | — |
| 4 | Nearby shelter locator | ✅ Highly Feasible | Low–Medium |
| 5 | Emergency SOS button | ✅ Highly Feasible | Low |
| 6 | Blocked road detection | ✅ **Already Implemented** | — |
| 7 | Rescue team tracking | ⚠️ Moderately Feasible | Medium–High |
| 8 | Crowd-sourced flood reporting | ✅ Highly Feasible | Medium |
| 9 | Offline emergency maps | ✅ Highly Feasible | Low–Medium |
| 10 | SMS alerts during internet failure | ❌ Not Feasible (needs Twilio/telecom) | High |
| 11 | Emergency contact sharing | ✅ Highly Feasible | Low |
| 12 | Medical emergency prioritization | ⚠️ Moderately Feasible | Medium |
| 13 | Safe zone recommendations | ✅ Highly Feasible | Low–Medium |
| 14 | Flood prediction using AI | ✅ Highly Feasible | Medium |
| 15 | Emergency supply location finder | ✅ Highly Feasible | Low–Medium |
| 16 | Traffic-aware evacuation routing | ⚠️ Moderately Feasible | Medium |
| 17 | Missing person reporting | ✅ Highly Feasible | Low–Medium |
| 18 | Disaster management dashboard | ⚠️ Partially Implemented | Medium |

---

## Detailed Analysis

### ✅ ALREADY IMPLEMENTED (3 features)

---

#### 2. AI-Based Safe Evacuation Routes
**Status: Fully implemented — core feature of the platform.**

Your system already does this at two levels:
- **Server-side:** `georescue/ml_serving/gis_pipeline/routing.py` — `plan_safe_route()` uses NetworkX shortest-path on an OSMnx graph with blocked edges removed
- **Client-side:** `georescue/georescue/routing.py` — `calculate_safe_route()` does the same locally as a fallback
- **AI orchestration:** The Spatial Navigator agent (`georescue/agents/crew.py` L80–100) retrieves and validates the route

> No changes needed. Already a **headline feature**.

---

#### 3. Real-Time Flood Risk Map
**Status: Fully implemented — live weather-driven flood polygon.**

- `georescue/ml_serving/gis_pipeline/live_flood_feed.py` — `fetch_live_precipitation()` pulls real-time hourly rainfall from Open-Meteo → `precipitation_to_radius_km()` maps intensity to severity levels (low/moderate/high/extreme) → generates a geographic flood polygon
- `georescue/georescue/map_layers.py` L108–141 — `render_flood_zone()` renders it as a blue overlay with severity-scaled opacity
- Layer toggle in sidebar: `show_flood_zone` checkbox

> No changes needed. Already works end-to-end.

---

#### 6. Blocked Road Detection
**Status: Fully implemented — spatial intersection analysis.**

- `georescue/ml_serving/gis_pipeline/flood_overlay.py` L152–207 — `identify_blocked_roads()` performs GeoPandas `overlay(how='intersection')` between the flood polygon and the OSM road network
- Returns road names, highway types, affected lengths, and fully/partially blocked status
- `georescue/georescue/map_layers.py` L148–175 — renders as bold red lines with tooltip showing road name + affected length

> No changes needed. Already a core GIS pipeline feature.

---

### ✅ HIGHLY FEASIBLE — Can implement with current architecture (10 features)

---

#### 1. Early Flood Warning Notifications
**Effort: Medium | Where it fits: New agent + pipeline step**

Your system already fetches live precipitation and computes severity in `georescue/ml_serving/gis_pipeline/live_flood_feed.py`. Adding warnings requires:

**Implementation approach:**
- Add a **background polling loop** (e.g. a `schedule` or `APScheduler` task) in the FastAPI server that calls `generate_live_flood_polygon()` every 15–30 minutes
- When severity escalates (e.g. low → moderate → high), trigger a **warning event**
- In the Streamlit UI: use `st.toast()` or a persistent `st.warning()` banner when a new severity level is detected
- Store severity history in `session_state` and compare on each poll

**Touchpoints:**
- New: `ml_serving/gis_pipeline/alert_monitor.py`
- Modify: `georescue/ml_serving/gis_pipeline/pipeline.py` — add `check_escalation()`
- Modify: `georescue/georescue/state.py` — add `severity_history`, `active_alerts`
- Modify: `georescue/app.py` — add alert banner at top of page

---

#### 4. Nearby Shelter Locator
**Effort: Low–Medium | Where it fits: Map layer + OSM query**

You already use OSMnx to fetch road graphs. OSMnx (and Overpass API) can query **points of interest** like schools, hospitals, community centres — which serve as shelters.

**Implementation approach:**
- Query Overpass API for `amenity=school`, `amenity=hospital`, `building=civic`, `amenity=community_centre` within the map radius
- Display as a new Folium marker layer with shelter icons
- Optionally calculate walking/driving distance from the user's start point to each shelter using your existing routing engine
- Add a `show_shelters` checkbox in the sidebar

**Touchpoints:**
- New: `georescue/shelters.py` — Overpass query + caching
- Modify: `georescue/georescue/map_layers.py` — add `render_shelters()` with custom icons
- Modify: `georescue/app.py` sidebar — add toggle
- Modify: `georescue/georescue/state.py` — add `shelters_geojson`

---

#### 5. Emergency SOS Button
**Effort: Low | Where it fits: UI widget**

A simple but impactful UI addition.

**Implementation approach:**
- Add a large red `st.button("🆘 EMERGENCY SOS")` in the left panel
- On click: capture current `start_lat`, `start_lon` (user's location), timestamp, and the current flood severity
- Generate a **formatted SOS message** with coordinates, a Google Maps link, and severity context
- Provide a `st.download_button` for the SOS payload (JSON) and a **copy-to-clipboard** button
- Optionally auto-trigger the pipeline to compute the nearest safe route from the user's position

**Touchpoints:**
- Modify: `georescue/app.py` — add SOS section after Actions
- New: `georescue/sos.py` — SOS message formatter

---

#### 8. Crowd-Sourced Flood Reporting
**Effort: Medium | Where it fits: New API endpoint + UI form**

Allow users to submit flood observations that appear on the map for other users.

**Implementation approach:**
- Add a simple **report form** in the Streamlit sidebar: location (from map click), severity (dropdown), description (text), optional photo
- Store reports in a JSON file on the server (or SQLite for durability)
- New FastAPI endpoints: `POST /reports` and `GET /reports`
- Display crowd reports as a separate Folium marker layer (orange pins with popups)
- The Reporting Coordinator agent can incorporate crowd reports into its summary

**Touchpoints:**
- New: `ml_serving/api/report_routes.py` — CRUD endpoints
- New: `georescue/reporting.py` — UI form component
- Modify: `georescue/georescue/map_layers.py` — add `render_crowd_reports()`
- Modify: `georescue/ml_serving/api/schemas.py` — add `FloodReport` model
- Modify: `georescue/ml_serving/api/app.py` — include new router

---

#### 9. Offline Emergency Maps
**Effort: Low–Medium | Where it fits: Leverages existing architecture**

Your system **already has partial offline capability** via the graceful degradation strategy in `georescue/agents/pipeline.py` L148–170. When the API is offline, it falls back to local OSMnx routing.

**Enhancements to make it more robust:**
- Add a **"Download Map for Offline Use"** button that saves the current Folium map as a static HTML file (`base_map.save("offline_map.html")`)
- Cache the road graph to disk (not just in `st.cache_resource`) so it survives app restarts — save as GraphML using `ox.save_graphml()`
- Pre-download tile layers for the Colombo area using a tile caching proxy or offline tile package

**Touchpoints:**
- Modify: `georescue/georescue/routing.py` — add `save_graph_to_disk()` / `load_graph_from_disk()` with GraphML
- Modify: `georescue/app.py` — add download button for offline HTML map

---

#### 11. Emergency Contact Sharing
**Effort: Low | Where it fits: UI panel + session state**

**Implementation approach:**
- Add an **"Emergency Contacts"** expander in the sidebar
- Allow users to input: name, phone, relationship (stored in `session_state`)
- Include contacts in the SOS message payload and in the incident report
- Add a "Share contacts" button that generates a shareable text block

**Touchpoints:**
- Modify: `georescue/georescue/state.py` — add `emergency_contacts` list
- Modify: `georescue/app.py` sidebar — add contact management UI
- Modify: `georescue/agents/pipeline.py` `_build_template_report()` — include contacts in report

---

#### 13. Safe Zone Recommendations
**Effort: Low–Medium | Where it fits: Inverse of flood polygon**

You already compute flood zones. The **inverse** (areas outside the flood polygon, above a certain elevation, near shelters) are safe zones.

**Implementation approach:**
- Compute safe zone as `map_bounds.difference(flood_polygon)` using Shapely
- Filter to areas that are road-accessible (connected to the unblocked graph)
- Rank zones by: distance from user, number of shelters, road connectivity
- Display as green-shaded areas on the map
- The Reporting Coordinator can include "Top 3 recommended safe zones" in the report

**Touchpoints:**
- New: `georescue/safe_zones.py` — zone computation + ranking
- Modify: `georescue/georescue/map_layers.py` — add `render_safe_zones()`
- Modify: report template in `georescue/agents/pipeline.py` — add safe zone section

---

#### 14. Flood Prediction Using AI
**Effort: Medium | Where it fits: Extends existing weather pipeline**

Your `georescue/ml_serving/gis_pipeline/live_flood_feed.py` already fetches 6h past + 3h forecast from Open-Meteo.

**Implementation approach:**
- Extend the Open-Meteo query to include **7-day forecast** (`forecast_days=7`)
- Add forecast parameters: `precipitation_probability`, `weathercode`, `soil_moisture`
- Implement a simple **time-series prediction** using the precipitation trend:
  - Linear regression or exponential smoothing on the precipitation curve
  - Or use the Llama 3.2 agent to interpret the trend and produce a natural-language prediction
- Display a **flood risk timeline** chart in the UI using `st.line_chart()` or `st.plotly_chart()`
- Include prediction in the incident report: "Flood severity expected to escalate to HIGH in 6 hours based on precipitation trend"

**Touchpoints:**
- Modify: `georescue/ml_serving/gis_pipeline/live_flood_feed.py` — extend API call with forecast params
- New: `ml_serving/gis_pipeline/flood_predictor.py` — trend analysis
- Modify: `georescue/app.py` — add prediction chart panel
- Modify: report template — add "Prediction" section

---

#### 15. Emergency Supply Location Finder
**Effort: Low–Medium | Where it fits: Same pattern as shelter locator**

Same Overpass API approach as shelters, but querying for: `shop=supermarket`, `amenity=pharmacy`, `amenity=hospital`, `amenity=fuel`, `amenity=fire_station`, `amenity=police`.

**Implementation approach:**
- Query OSM for supply-relevant POIs within radius
- Display with category-specific icons (🏥 hospital, ⛽ fuel, 🏪 store, 💊 pharmacy)
- Calculate distance from user's location
- Show as filterable layer with toggle per category

**Touchpoints:**
- Could share `georescue/shelters.py` → rename to `georescue/pois.py` (points of interest)
- Modify: `georescue/georescue/map_layers.py` — add `render_supply_points()`
- Modify: sidebar — add POI category checkboxes

---

#### 17. Missing Person Reporting
**Effort: Low–Medium | Where it fits: Same backend as crowd-sourced reports**

**Implementation approach:**
- Add a "Report Missing Person" form: name, age, last known location (map click), photo (optional), description, contact number
- Store in the same JSON/SQLite backend as crowd reports (`POST /reports/missing`)
- Display on map as special markers (person icon) with popup showing details
- Include in the incident report: "N missing person reports in the affected area"

**Touchpoints:**
- Extend: `ml_serving/api/report_routes.py` (if implementing crowd reports, share the backend)
- Modify: `georescue/georescue/map_layers.py` — add `render_missing_persons()`
- Modify: `georescue/app.py` — add missing person form in expander

---

### ⚠️ MODERATELY FEASIBLE — Possible but requires more work (4 features)

---

#### 7. Rescue Team Tracking
**Effort: Medium–High | Challenge: Requires real-time location streaming**

Your current architecture is **request-response** (pipeline runs on button click). Real-time tracking would need:

**Partial implementation approach (simulated):**
- Add a **"Rescue Teams"** panel where operators can manually log team positions (map click → "Place Team Alpha here")
- Display as moving markers on the map with team name, status (en route / on-site / returning), ETA
- Calculate ETA from team position to incident using your existing routing engine
- For a demo: simulate team movement along the safe route using JavaScript animation in the Folium map

**What would make it real (out of scope for this project):**
- WebSocket server for live GPS data from field devices
- Real-time map updates via `streamlit-autorefresh` or a different framework (React + Socket.IO)

**Touchpoints:**
- New: `georescue/rescue_teams.py` — team state management
- Modify: `georescue/georescue/map_layers.py` — add `render_rescue_teams()`
- Modify: `georescue/georescue/state.py` — add `rescue_teams` list

---

#### 12. Medical Emergency Prioritization
**Effort: Medium | Challenge: Requires a prioritization model**

**Implementation approach:**
- Add a **triage form** where responders can log medical emergencies: location, severity (red/yellow/green), number of patients, type (trauma, drowning, illness)
- Use a **scoring algorithm** to rank emergencies by: proximity to blocked roads, severity level, number of patients, accessibility (is a safe route available?)
- Display a **priority queue** panel sorted by score
- Route the nearest available rescue team to the highest-priority incident
- The Reporting Coordinator agent can produce a **triage summary**

**Touchpoints:**
- New: `georescue/triage.py` — scoring algorithm + priority queue
- Modify: `georescue/app.py` — add triage panel
- Modify: report template — add "Medical Triage Summary" section

---

#### 16. Traffic-Aware Evacuation Routing
**Effort: Medium | Challenge: No live traffic data source**

Your routing uses OSMnx (distance-weighted). Adding traffic awareness would require:

**Partial implementation approach:**
- Use OSMnx's `speed` and `travel_time` edge attributes (estimated from highway type and speed limits) instead of pure `length`
- Apply **penalty weights** to roads near the flood zone boundary (likely congested during evacuation)
- Query **Google Maps Directions API** or **TomTom Traffic API** for real-time traffic data (requires API key)
- Fall back to estimated speeds by road type if no traffic API is available

**Implementation:**
- Modify: `georescue/georescue/routing.py` — change `weight="length"` to `weight="travel_time"` and add congestion penalties
- Modify: `georescue/ml_serving/gis_pipeline/routing.py` — same on server side
- New: optional traffic API integration

---

#### 18. Disaster Management Dashboard
**Effort: Medium | Status: Partially implemented**

Your current UI is already a command center, but it's **mission-focused** (single run → report). A dashboard would aggregate **historical data**.

**What you already have:**
- Real-time map with multiple layers
- Agent activity log
- Route statistics panel
- Emergency response report

**What a dashboard would add:**
- **Summary cards** at the top: total floods analyzed, roads currently blocked, average severity this week
- **Severity trend chart** over time (from stored `latest_status.json` history)
- **Mission history** log: past pipeline runs with timestamps and outcomes
- **Multi-location view**: analyze multiple regions, not just Colombo

**Touchpoints:**
- New: `georescue/dashboard.py` — metrics aggregation
- Modify: `georescue/ml_serving/gis_pipeline/pipeline.py` — append to history file after each cycle
- Modify: `georescue/app.py` — add dashboard section with `st.metric()` cards

---

### ❌ NOT FEASIBLE for this project (1 feature)

---

#### 10. SMS Alerts During Internet Failure
**Effort: High | Why: Requires external telecom infrastructure**

This requires:
- A **Twilio** or **Vonage** account with SMS credits
- A dedicated server with internet (if user's internet is down, the server must be separate)
- Phone number collection and consent
- Sri Lanka-specific SMS routing

> **⚠️ WARNING:** This is fundamentally an infrastructure problem, not a code problem. If the user has no internet, the Streamlit app is inaccessible entirely. SMS requires a separate always-on service with telecom integration. This is **out of scope** for a hackathon project.

**Alternative that IS feasible:** Add a "Download Emergency Info" button that saves a self-contained HTML file with the latest map, route, and contacts that works without internet. This leverages your existing offline map capability.

---

## 🎁 BONUS: Additional Features You Didn't List (but are easy to add)

These leverage your existing architecture with minimal effort:

| Feature | Effort | How |
|---------|--------|-----|
| **Multi-language support** | Low | Use Llama 3.2 to translate the report into Sinhala/Tamil via a prompt suffix |
| **PDF report export** | Low | Use `fpdf2` or `reportlab` to convert the Markdown report to a printable PDF |
| **Elevation-aware routing** | Medium | OSMnx can fetch elevation data via `ox.elevation.add_node_elevations_google()` — route to higher ground |
| **Multiple evacuation routes** | Low | Use `nx.shortest_simple_paths()` instead of `nx.shortest_path()` to show the top 3 alternative routes |
| **Severity heatmap** | Low | Use Folium's `HeatMap` plugin with precipitation data points across the region |
| **Historical flood comparison** | Medium | Store each cycle's flood polygon; display past vs. current overlay to show flood progression |
| **Voice-activated commands** | Low | Use `streamlit-webrtc` or browser's SpeechRecognition API for voice input to the mission prompt |
| **Weather radar overlay** | Low | Add Open-Meteo's precipitation map tile layer as an additional Folium tile source |

---

## Recommended Implementation Priority

If I were to prioritize for maximum impact with minimum effort:

### Phase 1 — Quick Wins (1–2 days each)
1. **Emergency SOS Button** — Immediate user value, ~50 lines of code
2. **Emergency Contact Sharing** — Pairs with SOS, trivial to add
3. **Offline Emergency Maps** — You're 80% there; just add the download button
4. **Safe Zone Recommendations** — Inverse of existing flood polygon computation

### Phase 2 — High Impact (2–4 days each)
5. **Nearby Shelter Locator** — Overpass API query + map layer
6. **Emergency Supply Location Finder** — Same pattern as shelters
7. **Flood Prediction Using AI** — Extend existing Open-Meteo integration
8. **Early Flood Warning Notifications** — Polling + severity comparison

### Phase 3 — Differentiators (3–5 days each)
9. **Crowd-Sourced Flood Reporting** — New API endpoints + form
10. **Missing Person Reporting** — Shares backend with crowd reports
11. **Disaster Management Dashboard** — Aggregation + history
12. **Medical Emergency Prioritization** — Triage system

> **💡 TIP:** Features 1–4 (Phase 1) could all be implemented in a single focused sprint and would immediately make the platform feel much more complete for a hackathon demo.
