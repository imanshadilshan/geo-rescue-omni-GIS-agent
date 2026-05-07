# GIS Tools Setup & Execution Guide

This guide explains how to set up and run the GIS tools for the Geo-Rescue Omni project.

## Prerequisites

### 1. Virtual Environment Activation

Before running any script, activate the Python virtual environment:

```powershell
# Navigate to the georescue-amd-hackathon folder
cd georescue-amd-hackathon

# Activate the virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# You should see (.venv) in your prompt
```

### 2. Dependencies Installation

All required dependencies are listed in `requirements.txt`. Install them with:

```powershell
pip install -r requirements.txt
```

**Key packages:**

- `osmnx==2.1.0` — Download road networks from OpenStreetMap
- `geopandas==1.1.3` — Work with geographic data
- `scikit-learn` — Spatial queries for routing (installed separately if needed)

---

## Running the GIS Scripts

### Script 1: Road Network Downloader (`road_network.py`)

**Purpose:** Downloads the drivable road network for Colombo, Sri Lanka from OpenStreetMap and converts it to GeoJSON and GraphML formats.

**Command:**

```powershell
python gis_tools/road_network.py
```

**What it does:**

- Downloads road network from OpenStreetMap (OSMnx)
- Converts to GeoDataFrames for nodes and edges
- Calculates network statistics
- Saves outputs as GeoJSON and GraphML files

**Output files:**

- `data/processed/colombo_road_network.geojson` — Road segments (edges) ~5.8 MB
- `data/processed/colombo_road_nodes.geojson` — Intersections (nodes) ~1.2 MB
- `data/processed/colombo_road_network_graph.graphml` — Network graph for routing ~5.5 MB

**Runtime:** ~10–20 seconds (depends on network speed to OpenStreetMap)

**Notes:**

- This script should be run **first** as it generates data needed by other scripts
- If OSMnx API is slow or times out, the script will retry automatically

---

### Script 2: Flood Overlay Analysis (`flood_overlay.py`)

**Purpose:** Analyzes flood impact on the road network by identifying blocked or partially blocked roads during a flood event.

**Command:**

```powershell
python gis_tools/flood_overlay.py
```

**What it does:**

- Loads the road network from `colombo_road_network.geojson`
- Creates a sample flood polygon centered near Colombo
- Performs spatial overlay to find intersecting roads
- Calculates affected road lengths and segments

**Output files:**

- `data/processed/blocked_roads_flood.geojson` — Roads affected by flood
- `data/processed/flood_polygon.geojson` — Flood boundary polygon

**Runtime:** ~2–3 seconds

**Notes:**

- Uses a sample flood polygon for demonstration; modify the `location` and `radius` variables in the script to test different flood zones
- Warnings about "geographic CRS" are expected and do not affect results

---

### Script 3: Safe Route Planning (`routing.py`)

**Purpose:** Plans an optimal route between two points while avoiding blocked roads.

**Command:**

```powershell
python gis_tools/routing.py
```

**What it does:**

- Loads the road network graph from `colombo_road_network_graph.graphml`
- Removes blocked roads from the graph
- Finds the shortest path between start and end coordinates
- Converts the route to a GeoDataFrame and saves as GeoJSON

**Output files:**

- `data/processed/optimal_route_colombo.geojson` — Route segments (~2.2 KB)

**Runtime:** ~1–2 seconds

**Notes:**

- Requires `scikit-learn` for spatial queries; automatically installed with dependencies
- Start and end coordinates are hardcoded in the script; modify `start_coords` and `end_coords` to test different routes

---

### Script 4: GeoJSON Export Utilities (`export_geojson.py`)

**Purpose:** Utility module providing reusable functions for exporting GeoDataFrames to GeoJSON format.

**Usage:**
This is a utility library, not a standalone script. Import and use in other Python code:

```python
from gis_tools.export_geojson import save_geojson, load_geojson, save_geojson_batch
import geopandas as gpd

# Load a GeoDataFrame
gdf = gpd.read_file("data/processed/colombo_road_network.geojson")

# Export with validation and error handling
output_path = save_geojson(
    gdf,
    "output/my_export.geojson",
    validate_crs=True,
    auto_convert_crs=True,
    target_crs="EPSG:4326"
)
```

---

## Running All Scripts End-to-End

To run the full workflow in sequence:

```powershell
# Ensure you're in the georescue-amd-hackathon folder with venv activated
python gis_tools/road_network.py
python gis_tools/flood_overlay.py
python gis_tools/routing.py
```

**Expected total runtime:** ~15–30 seconds

**Output structure:**

```
data/processed/
├── colombo_road_network.geojson        (roads)
├── colombo_road_nodes.geojson          (intersections)
├── colombo_road_network_graph.graphml  (graph)
├── blocked_roads_flood.geojson         (flood-affected roads)
├── flood_polygon.geojson               (flood zone)
└── optimal_route_colombo.geojson       (safe route)
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'osmnx'` or `geopandas`

**Cause:** Dependencies not installed or wrong Python environment.

**Fix:**

```powershell
# Ensure venv is activated (you should see (.venv) in prompt)
pip install -r requirements.txt
```

### `TypeError: graph_from_place() got an unexpected keyword argument 'timeout'`

**Cause:** Incompatible OSMnx version.

**Status:** ✓ **Fixed** — The script now automatically retries without the `timeout` parameter if needed.

### `ImportError: scikit-learn must be installed as an optional dependency`

**Cause:** `scikit-learn` not installed; needed for spatial queries in routing.

**Fix:**

```powershell
pip install scikit-learn
```

**Status:** ✓ **Fixed** — Installed in venv during testing.

### `KeyError: 'area'` when downloading road network

**Cause:** Incompatible OSMnx version doesn't include `area` in `basic_stats()`.

**Status:** ✓ **Fixed** — The script now computes approximate area from node convex hull as fallback.

### Script runs but outputs are empty or very small

**Possible cause:** Flood polygon doesn't intersect with roads; sample uses hardcoded coordinates far from Colombo center.

**Fix:** Modify the flood polygon location in `flood_overlay.py` line ~80:

```python
center_lon, center_lat = 80.85, 6.92  # Adjust to your location
```

### `UserWarning: Geometry is in a geographic CRS. Results from 'length' are likely incorrect.`

**Status:** ✓ **Expected** — This is a non-fatal warning. The scripts automatically project to EPSG:3857 (Web Mercator) for accurate measurements before logging results.

---

## Customizing the Scripts

### Change Flood Zone Location

Edit `flood_overlay.py` (~line 80):

```python
center_lon, center_lat = 80.85, 6.92      # Longitude, Latitude
radius_km = 2.0                            # Radius in km
```

### Change Route Start/End Points

Edit `routing.py` (~line 410):

```python
start_coords = (6.9271, 80.7789)  # (latitude, longitude)
end_coords = (6.852, 80.8197)     # (latitude, longitude)
```

### Change Network Type

Edit `road_network.py` (~line 275):

```python
network_type = "drive"  # Options: "drive", "walk", "bike", "all"
```

---

## Performance Notes

| Script           | Time    | Data Size    |
| ---------------- | ------- | ------------ |
| road_network.py  | ~10–20s | ~12 MB total |
| flood_overlay.py | ~2–3s   | ~0.2 MB      |
| routing.py       | ~1–2s   | ~2 KB        |

- First run of `road_network.py` may take longer if OSMnx needs to download from OpenStreetMap API
- Subsequent runs load cached data from GeoJSON/GraphML files (much faster)

---

## File Manifest

| File                          | Purpose                                 |
| ----------------------------- | --------------------------------------- |
| `gis_tools/road_network.py`   | Download and process road network       |
| `gis_tools/flood_overlay.py`  | Analyze flood impact on roads           |
| `gis_tools/routing.py`        | Plan safe routes avoiding blocked roads |
| `gis_tools/export_geojson.py` | Utility module for GeoJSON export       |
| `gis_tools/config.py`         | Configuration settings                  |
| `requirements.txt`            | Python dependencies                     |

---

## Next Steps

1. **Explore outputs:** Open the generated GeoJSON files in QGIS or a web GIS viewer (e.g., geojson.io)
2. **Modify parameters:** Customize flood zones, routes, and network types as needed
3. **Integrate with agent:** Use output data in your Foundry AI agent for decision-making
4. **Add more analysis:** Extend scripts to calculate travel time, accessibility, etc.

---

## Questions or Issues?

Refer to the logs in each script run—they provide detailed information about what was processed and any warnings or errors encountered.
