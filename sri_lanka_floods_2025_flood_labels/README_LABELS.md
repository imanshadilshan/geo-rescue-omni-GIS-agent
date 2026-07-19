# Flood ground-truth labels — auto-generated (v1, heuristic)

## What's in this package
- `masks/` — one binary PNG per tile: `<tile_name>_mask.png`
  White (255) = detected standing water, Black (0) = non-water. Same pixel dimensions as the source tile.
- `metadata.csv` — your original metadata with three new columns:
  - `mask_path` — filename of the matching mask in `masks/`
  - `flood_fraction` — fraction of the tile's pixels flagged as water (0–1)
  - `label_method` — `auto_heuristic_hsv_v1` (see below)
- `annotate.py` — the exact script used, so you can re-run it with different thresholds
- `preview/` — 4 sample overlays (mask painted red on the source image) so you can eyeball quality before trusting it for evaluation

## How the labels were made
No manual masks, GeoJSON, or GIS flood boundaries were available for this set, so I generated labels programmatically rather than leaving them blank. The method is classic color-based water segmentation, not a trained flood-detection model:

1. Convert each tile to HSV.
2. Flag **confident open water**: blue/cyan/teal hue, real saturation, mid-range brightness (clear rivers, lakes, sea).
3. Flag **candidate turbid/muddy water**: low-saturation, grayish-brown pixels where blue ≥ red (murky floodwater and waterlogged ground look like this, but so do some roads and rooftops).
4. Grow the confident-water seeds through connected candidate pixels only (morphological reconstruction) — this pulls in turbid floodwater that's physically touching real water, while excluding isolated gray rooftops/roads that just happen to share the same color.
5. Clean up: drop tiny speckles, fill tiny holes, light smoothing.

## Important limitations — please read before trusting metrics
- **This is visible standing water, not flood-specific extent.** With true-color RGB and no pre-flood reference image, there's no way to algorithmically tell "this river is flooded beyond its banks" apart from "this river always looks like this." Coastal tiles in particular (e.g. tile 0000, right at the coastline) will show high `flood_fraction` mostly because of the sea, not flooding.
- **No NIR/SWIR band.** Standard water indices (NDWI, MNDWI) need a near-infrared band. This is a same-band RGB approximation, so it will under-detect very muddy/opaque floodwater and can occasionally mistake shadows or dark asphalt for water.
- **Not human-verified.** Treat this as a first-pass pseudo-label set to unblock your Accuracy/F1/IoU pipeline, not as certified ground truth.

## Suggested next step
Spot-check the `preview/` overlays and a handful of `masks/` files against the source tiles. If accuracy matters for a real evaluation (e.g. a paper, a report, disaster response), the better path is:
1. Use these masks as a starting point / pre-annotation layer.
2. Load tiles + masks into CVAT, Label Studio, or QGIS and correct them by eye — much faster than annotating from scratch.
3. If you can get a pre-flood reference image for the same tiles, subtracting permanent water (rivers/sea/lakes) from the mask would turn this into an actual flood-only layer instead of "all visible water."

If you'd rather I re-run with different sensitivity (e.g. more/less aggressive turbid-water detection), just let me know which tiles are off and in which direction (missing flooded areas vs. over-flagging).
