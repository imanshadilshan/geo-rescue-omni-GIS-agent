# Real-time Integration — Live Flood Ingest & Auto-Routing

This document describes the near-real-time pipeline added to this repository, how it works, and how to test it locally.

Files added or updated

- `gis_tools/live_flood_feed.py` — fetches precipitation from Open-Meteo and writes a flood polygon.
- `gis_tools/run_live_cycle.py` — one-shot pipeline: fetch weather → flood overlay → reroute → write latest outputs.
- `gis_tools/run_live_monitor.py` — continuous monitor that runs `run_live_cycle` on an interval.
- `gis_tools/flood_overlay.py` — updated to accept an external flood polygon file.
- `gis_tools/routing.py` — routing already present; used by the cycle to compute routes.
- Outputs written to: `data/processed/` and `data/raw/`.

Primary outputs

- `data/processed/live_flood_polygon.geojson` — polygon generated from live weather.
- `data/processed/blocked_roads_flood.geojson` — roads intersecting the flood polygon.
- `data/processed/optimal_route_colombo.geojson` — computed route avoiding blocked roads.
- `data/processed/latest_route.geojson` — rolling latest route written each cycle.
- `data/processed/latest_status.json` — compact status for UI polling (timestamp, severity, counts, route length, paths).
- `data/raw/live_weather_snapshot.json` — raw weather snapshot used to derive the polygon.

Quick setup

1. Activate your venv in `georescue-amd-hackathon`:

```powershell
cd georescue-amd-hackathon
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies (if not already done):

```powershell
pip install -r requirements.txt
```

Run commands

- One-shot live cycle (fetches weather, runs overlay, reroutes, writes outputs):

```powershell
.\.venv\Scripts\python.exe gis_tools\run_live_cycle.py
```

- Continuous near-real-time monitor (default every 300 seconds):

```powershell
.\.venv\Scripts\python.exe gis_tools\run_live_monitor.py --interval-seconds 300
```

How to test (quick checklist)

1. Run the one-shot command above.
2. Confirm these files exist and are recent:
   - `data/processed/live_flood_polygon.geojson`
   - `data/processed/blocked_roads_flood.geojson`
   - `data/processed/optimal_route_colombo.geojson`
   - `data/processed/latest_route.geojson`
   - `data/processed/latest_status.json`
   - `data/raw/live_weather_snapshot.json`

3. Inspect `latest_status.json` — it should contain keys: `timestamp_utc`, `severity`, `affected_roads`, `total_affected_length_m`, `route_length_m`, `route_path`, `latest_route_path`.

```powershell
Get-Content data\processed\latest_status.json -Raw | ConvertFrom-Json
```

4. Visual check: open any generated `.geojson` at https://geojson.io or in QGIS to verify geometry.

Automated smoke test (Python)
Create and run a tiny test script (one-liner) to assert `latest_status.json` contains expected fields:

```powershell
python - <<'PY'
import json, sys
f='georescue-amd-hackathon/data/processed/latest_status.json'
try:
    s=json.load(open(f))
    keys=['timestamp_utc','severity','affected_roads','route_length_m']
    missing=[k for k in keys if k not in s]
    assert not missing, f"missing keys: {missing}"
    print('SMOKE OK', s['severity'], s['affected_roads'])
except Exception as e:
    print('SMOKE FAIL', e); sys.exit(2)
PY
```

Troubleshooting

- If `colombo_road_network.geojson` or GraphML is missing, run:

```powershell
python gis_tools/road_network.py
```

- If Open-Meteo fetch fails, check internet, or inspect `data/raw/live_weather_snapshot.json` for error details.
- If output geometries look wrong, confirm CRS: many operations re-project to `EPSG:32644` (UTM zone) for metric buffers.

Security and production notes

- Open-Meteo is used as a free demo source; replace with authenticated feeds if you have region-specific flood or sensor data.
- For production, consider providing an HTTP endpoint that serves `latest_status.json` and `latest_route.geojson` behind authentication and rate limiting.

Next recommended steps

- Add a tiny HTTP server to serve `latest_status.json` and `latest_route.geojson` for UI polling.
- Add logging rotation and error alerts for the monitor.

If you want, I can add the HTTP endpoint now and wire it into the monitor. Say the word.
