# GeoRescue — Complete Model Training Plan
### Live Data · 10-Second Intervals · 4-Hour Collection · Qwen2-VL-7B LoRA Fine-Tuning

---

## Quick Summary

We fine-tune **Qwen2-VL-7B-Instruct** (a vision-language model) to understand flood
disaster imagery from Sentinel-2 satellite photos. The model learns to output structured
JSON containing flood severity, a text description of damage, and polygon coordinates
of affected zones — directly usable as GeoJSON in the live GeoRescue agent.

**Training signal is 100% automatic** — no manual image labelling needed.
Ground truth labels come from Minindu's GIS pipeline:
- Precipitation data from Open-Meteo API → flood polygon
- Road network from OpenStreetMap → flood impact analysis
- These become the "correct answers" the model learns to predict from images

**Collection target:** ~1,440 samples in 4 hours at 10-second intervals.

---

## Who Does What

| Step | Who | Time needed |
|------|-----|-------------|
| Create Sentinel Hub account | **YOU (manual)** | 5 min |
| Create `.env` file with credentials | **YOU (manual)** | 2 min |
| Set up Python virtual environment | **YOU (manual)** | 5 min |
| Install dependencies | Run command | ~5 min |
| Copy Minindu's road network files | Run command (copy) | 30 sec |
| 4-hour live data collection | Run command + leave running | 4 hours |
| Enrich training labels | Run command | ~2 min |
| Start model fine-tuning | Run command + leave running | 2–4 hours |
| Wire fine-tuned adapter into API | **YOU (manual edit)** | 5 min |
| Restart serving API | **YOU (manual)** | 1 min |

---

## File & Folder Map

```
D:\Projects\geo-rescue-omni-GIS-agent\
│
├── TRAINING_PLAN.md                          ← this file
│
├── geo-rescue-omni-GIS-agent-dev-minindu\    ← Minindu's module (source of road data)
│   └── georescue-amd-hackathon\
│       └── data\processed\
│           ├── colombo_road_network.geojson      ← COPY THIS (saves 2 min)
│           └── colombo_road_network_graph.graphml
│
└── ml_serving\
    ├── .env                                  ← YOU CREATE THIS (Sentinel Hub credentials)
    ├── requirements.txt                      ← install with pip
    │
    ├── data_pipeline\                        ← GIS data collection pipeline
    │   ├── config.py                         ← reads .env, sets data paths
    │   ├── live_flood_feed.py                ← Open-Meteo weather → flood polygon
    │   ├── flood_overlay.py                  ← road impact analysis
    │   ├── road_network.py                   ← OSMnx road download
    │   ├── export_geojson.py                 ← GeoJSON I/O utilities
    │   ├── sentinel_downloader.py            ← Sentinel-2 satellite imagery
    │   └── data_collector.py                 ← orchestrator (fast_collect_live)
    │
    ├── training\                             ← model fine-tuning code
    │   ├── dataset.py                        ← PyTorch Dataset for (image, label) pairs
    │   ├── label_generator.py                ← GIS data → Qwen2-VL training format
    │   ├── trainer.py                        ← LoRA fine-tuning loop
    │   └── run_training.py                   ← CLI entry point (run this)
    │
    ├── training_data\                        ← GENERATED during collection
    │   ├── raw\
    │   │   ├── satellite_initial.png         ← first Sentinel-2 download
    │   │   ├── satellite_YYYYMMDD_HHMMSS.png ← refreshed every 30 min
    │   │   └── live_weather_snapshot.json    ← latest weather snapshot
    │   ├── processed\
    │   │   ├── colombo_road_network.geojson  ← PUT MININDU'S FILE HERE
    │   │   ├── colombo_road_nodes.geojson
    │   │   └── colombo_road_network_graph.graphml
    │   ├── samples\                          ← one folder per 10-second sample
    │   │   └── 20260508_120000_000000\
    │   │       ├── label.json                ← severity, metrics, paths
    │   │       ├── live_flood_polygon.geojson
    │   │       └── blocked_roads_flood.geojson
    │   └── dataset_index.json                ← master list of all samples (auto-saved)
    │
    ├── checkpoints\                          ← GENERATED during training
    │   ├── checkpoint-100\                   ← per-epoch saves
    │   ├── checkpoint-200\
    │   └── final\                            ← best model (LoRA adapter weights)
    │       ├── adapter_config.json
    │       ├── adapter_model.safetensors
    │       └── processor files
    │
    ├── api\                                  ← existing FastAPI serving
    │   ├── app.py
    │   └── routes.py
    └── qwen_vl\                              ← existing Qwen2-VL inference
        ├── model_loader.py                   ← EDIT THIS after training (Step 6)
        └── inference.py
```

---

## Phase 0 — Manual Setup (YOU do this)

### 0.1  Create a Sentinel Hub account

**Why:** Sentinel Hub provides Sentinel-2 satellite imagery via API.
The satellite images are needed to pair with flood labels during training.

**Steps (manual):**
1. Go to https://www.sentinel-hub.com/
2. Click **"Get started for free"** → register an account
3. After logging in, go to **Dashboard → User Settings → OAuth clients**
4. Click **"+ Create new"**
5. Give it a name (e.g. `georescue-training`)
6. Copy the **Client ID** and **Client Secret** — you only see the secret once

> **Note:** Free tier includes ~30,000 Processing Units/month.
> One 4096×4096 RGB satellite image ≈ 200 PU.
> 8 refreshes in 4 hours = ~1,600 PU — well within free limits.

---

### 0.2  Create the `.env` file

**Why:** The Sentinel Hub credentials must be kept out of source code.
`data_pipeline/config.py` reads them from this file automatically.

**Location:** `D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\.env`

**Steps (manual):** Create the file with a text editor and paste:

```env
SENTINEL_CLIENT_ID=paste-your-client-id-here
SENTINEL_CLIENT_SECRET=paste-your-client-secret-here
```

> **Important:** Do NOT commit `.env` to git. It already should be in `.gitignore`.
> If not, add it: `echo ".env" >> .gitignore`

---

### 0.3  Set up a Python virtual environment

**Why:** Isolates project dependencies from your system Python.
The GIS libraries (geopandas, rasterio, osmnx) can conflict with other projects.

**Steps (manual — run in PowerShell from the project root):**

```powershell
# Navigate to project root
cd D:\Projects\geo-rescue-omni-GIS-agent

# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Confirm Python path shows .venv
where python
```

> **Windows note:** If you get an execution policy error, run:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

> **Conda alternative (recommended for Windows GIS):**
> ```
> conda create -n georescue python=3.11
> conda activate georescue
> conda install -c conda-forge geopandas rasterio osmnx
> ```
> Then proceed with the pip install below for remaining packages.

---

### 0.4  Install Python dependencies

**Why:** Installs all required ML and GIS libraries.

**Command (run with venv/conda activated):**

```powershell
pip install -r D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\requirements.txt
```

**Expected output:** Long list of package downloads. Takes 3–10 minutes.

**Verify key packages installed:**

```powershell
python -c "import geopandas, osmnx, sentinelhub, torch, transformers, peft; print('All OK')"
```

If this prints `All OK` you are ready.

> **Troubleshooting install issues:**
> - `rasterio` fails on Windows → use: `pip install rasterio --find-links https://girder.github.io/large_image_wheels`
> - `geopandas` geometry errors → install via conda: `conda install -c conda-forge geopandas`
> - `torch` for AMD ROCm → use ROCm wheel: `pip install torch --index-url https://download.pytorch.org/whl/rocm6.0`

---

## Phase 1 — One-Time Road Network Setup (10 min, run once)

**Why:** The flood overlay needs Colombo's road network loaded in memory.
This is a ~13 MB static dataset that does not change. We only need to download it once.

### Option A: Copy from Minindu's pre-computed files (FASTEST — 30 seconds)

Minindu already downloaded and verified this data. Copying it saves ~2 minutes.

**Commands:**

```powershell
# Create target directory
New-Item -ItemType Directory -Force -Path "D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\training_data\processed"

# Copy road network GeoJSON
Copy-Item `
  "D:\Projects\geo-rescue-omni-GIS-agent\geo-rescue-omni-GIS-agent-dev-minindu\geo-rescue-omni-GIS-agent-dev-minindu\georescue-amd-hackathon\data\processed\colombo_road_network.geojson" `
  "D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\training_data\processed\colombo_road_network.geojson"

# Copy GraphML graph (needed for routing)
Copy-Item `
  "D:\Projects\geo-rescue-omni-GIS-agent\geo-rescue-omni-GIS-agent-dev-minindu\geo-rescue-omni-GIS-agent-dev-minindu\georescue-amd-hackathon\data\processed\colombo_road_network_graph.graphml" `
  "D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\training_data\processed\colombo_road_network_graph.graphml"

# Copy node data
Copy-Item `
  "D:\Projects\geo-rescue-omni-GIS-agent\geo-rescue-omni-GIS-agent-dev-minindu\geo-rescue-omni-GIS-agent-dev-minindu\georescue-amd-hackathon\data\processed\colombo_road_nodes.geojson" `
  "D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\training_data\processed\colombo_road_nodes.geojson"
```

**Verify:**

```powershell
Get-Item "D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\training_data\processed\colombo_road_network.geojson"
# Should show file size ~5.7 MB
```

### Option B: Re-download from OpenStreetMap (takes ~2–5 min, needs internet)

Use this only if Option A files are missing or corrupted.

```powershell
cd D:\Projects\geo-rescue-omni-GIS-agent

python -c "
import sys
sys.path.insert(0, 'ml_serving')
from data_pipeline.road_network import download_road_network
download_road_network()
print('Done.')
"
```

**Expected output:**
```
Road network: 18423 edges, 10284 nodes → ml_serving\training_data\processed
Done.
```

---

## Phase 2 — Live Data Collection (4 Hours, ~1,440 Samples)

**What happens during collection:**

Every 10 seconds the collector automatically:
1. Calls Open-Meteo API → gets hourly precipitation for Colombo
2. Converts precipitation to a flood polygon with severity (low/moderate/high/extreme)
3. Overlays flood polygon on the in-memory road network (pre-loaded at start)
4. Records: affected road count, total affected length (meters), severity, timestamp
5. Saves everything to `training_data/samples/<timestamp>/`

Every 30 minutes it also:
6. Downloads a fresh Sentinel-2 satellite image from Sentinel Hub
7. Links all subsequent samples to this new image

**Important notes:**
- Open-Meteo weather data updates hourly — so precipitation values repeat within each hour
- This means flood polygon severity is the same for ~360 consecutive samples per hour
- This is normal and expected — you are capturing state at a high frequency, and the model
  learns from the paired (image + GIS analysis) regardless
- When the weather changes at an hour boundary, severity may jump — capture that transition

### 2.1  Start the collection (leave this running for 4 hours)

Open a **new PowerShell terminal** and run:

```powershell
# Activate your environment first
cd D:\Projects\geo-rescue-omni-GIS-agent
.\.venv\Scripts\Activate.ps1

# Start 4-hour collection at 10-second intervals
python ml_serving\training\run_training.py live-collect `
  --duration-hours 4 `
  --interval 10 `
  --satellite-interval 30
```

**What you will see on screen:**

```
============================================================
  GeoRescue Fast Live Collector
  Duration  : 4.0 h  (14400 s)
  Interval  : 10 s
  Samples   : 1440 planned
  Satellite : refresh every 30 min (180 cycles)
============================================================

Loading road network into memory...
  18423 road segments loaded.

Downloading initial Sentinel-2 image (may take ~30 s)...
  Saved → ml_serving\training_data\raw\satellite_initial.png

[    1/ 1440]   0.1%  ETA 03:59:50  errors=0
[    2/ 1440]   0.1%  ETA 03:59:40  errors=0
...
[  180/ 1440]  12.5%  ETA 03:29:50  errors=0
[info] Refreshing satellite image (cycle 180)...
[info] New satellite image → ...satellite_20260508_140000.png
...
```

**DO NOT close this terminal.** The collection runs for exactly 4 hours.
You can open other terminals for other work while it runs.

### 2.2  Monitor progress mid-collection (optional)

In a separate terminal, check how many samples have been saved:

```powershell
# Count samples saved so far
(Get-ChildItem "D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\training_data\samples" -Directory).Count

# Check latest label
Get-Content (Get-ChildItem "D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\training_data\samples" -Directory | Sort-Object LastWriteTime | Select-Object -Last 1).FullName\label.json
```

Also check the rolling dataset index:

```powershell
# How many samples in the index so far
$idx = Get-Content "D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\training_data\dataset_index.json" | ConvertFrom-Json
$idx.Count
```

### 2.3  If collection is interrupted

If the terminal closes or the process is killed, **restart with `--no-append` omitted**
(the default) — it will append to the existing `dataset_index.json`:

```powershell
python ml_serving\training\run_training.py live-collect `
  --duration-hours 2 `
  --interval 10
# Appending to existing index (720 samples already collected).
```

### 2.4  Expected output after 4 hours

```
D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\training_data\
├── raw\
│   ├── satellite_initial.png              ← ~8 MB Sentinel-2 image
│   ├── satellite_20260508_140000.png
│   ├── satellite_20260508_143000.png
│   ├── ... (8 images total, one every 30 min)
│   └── live_weather_snapshot.json
├── processed\
│   └── colombo_road_network.geojson       ← unchanged
├── samples\
│   ├── 20260508_120000_000000\            ← sample 1
│   │   ├── label.json
│   │   ├── live_flood_polygon.geojson
│   │   └── blocked_roads_flood.geojson
│   ├── ... (1440 sample folders)
│   └── 20260508_160000_000000\            ← sample 1440
└── dataset_index.json                     ← 1440 entries, ~2 MB
```

---

## Phase 3 — Enrich Training Labels (5 minutes)

**What this does:**
The `dataset_index.json` contains raw metrics (numbers). This step converts them into
the exact JSON format the model will learn to output — complete with severity classification,
natural-language findings, and polygon coordinates extracted from the GeoJSON files.

```powershell
cd D:\Projects\geo-rescue-omni-GIS-agent

python ml_serving\training\run_training.py enrich `
  --dataset-index ml_serving\training_data\dataset_index.json
```

**Expected output:**
```
Enriched 1440 samples with training labels → ml_serving\training_data\dataset_index.json
```

**What a training label looks like** (added to each sample in the index):

```json
{
  "training_label": {
    "severity": "moderate",
    "findings": "247 roads affected by flooding (18450m total length). Precipitation: 3.8mm. Flood radius: 2.5km.",
    "affected_zones": [
      [[79.82, 6.91], [79.85, 6.91], [79.85, 6.94], [79.82, 6.91]]
    ]
  }
}
```

---

## Phase 4 — Fine-Tune Qwen2-VL (2–4 Hours)

**What this does:**
We use LoRA (Low-Rank Adaptation) to fine-tune only ~0.3% of Qwen2-VL's parameters.
This adapts the model to understand our specific disaster imagery + GIS output format
without retraining the entire 7B-parameter model from scratch.

The model is shown: `[satellite image] + [prompt asking for flood analysis]`
It learns to produce: `[the JSON label generated by the GIS pipeline]`

### 4.1  Before you start — GPU check (manual)

Open a Python shell and confirm your AMD GPU is visible:

```powershell
python -c "import torch; print('GPU available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

Expected: `GPU available: True` with `AMD Instinct MI300X` or similar.

If GPU is not available, training will run on CPU — extremely slow. Fix ROCm installation before proceeding.

### 4.2  Start fine-tuning

Open a **new terminal** (or wait for collection to finish and reuse that terminal):

```powershell
cd D:\Projects\geo-rescue-omni-GIS-agent
.\.venv\Scripts\Activate.ps1

python ml_serving\training\run_training.py train `
  --dataset-index ml_serving\training_data\dataset_index.json `
  --output-dir ml_serving\checkpoints `
  --epochs 3 `
  --batch-size 4 `
  --lr 2e-4 `
  --enrich-labels
```

**Arguments explained:**
| Argument | Value | Why |
|----------|-------|-----|
| `--epochs 3` | 3 full passes over dataset | Standard for LoRA fine-tuning |
| `--batch-size 4` | 4 samples per GPU step | MI300X has 192 GB — can go higher |
| `--lr 2e-4` | Learning rate | Standard for LoRA adapters |
| `--enrich-labels` | Re-generate labels | Ensures labels are fresh before training |

> **To use more GPU memory** (faster training): increase `--batch-size 8` or `--batch-size 16`

### 4.3  What you see during training

```
trainable params: 20,185,088 || all params: 7,615,616,000 || trainable%: 0.265
***** Running training *****
  Num examples = 1296
  Num Epochs = 3
  Batch size = 4
  Total steps = 972
{'loss': 2.1423, 'learning_rate': 0.0002, 'epoch': 0.12}
{'loss': 1.8341, 'learning_rate': 0.000185, 'epoch': 0.25}
...
```

Loss should decrease each epoch. If it stays flat or increases, reduce `--lr` to `1e-4`.

### 4.4  Expected checkpoints

```
ml_serving\checkpoints\
├── checkpoint-324\      ← saved after epoch 1
├── checkpoint-648\      ← saved after epoch 2
├── checkpoint-972\      ← saved after epoch 3
└── final\               ← best checkpoint (used for inference)
    ├── adapter_config.json
    ├── adapter_model.safetensors
    └── special_tokens_map.json
```

### 4.5  Resume if training is interrupted

```powershell
python ml_serving\training\run_training.py train `
  --dataset-index ml_serving\training_data\dataset_index.json `
  --output-dir ml_serving\checkpoints `
  --resume-from ml_serving\checkpoints\checkpoint-324
```

---

## Phase 5 — Load Fine-Tuned Model into the Serving API

**What this does:** Tells the existing FastAPI server to load the LoRA adapter
on top of the base Qwen2-VL model, so the API now uses the fine-tuned version.

### 5.1  Edit `model_loader.py` (manual)

Open `D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\qwen_vl\model_loader.py`

Find the `get_model()` function and add adapter loading. Change from:

```python
def get_model():
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        "Qwen/Qwen2-VL-7B-Instruct",
        torch_dtype="auto",
        device_map="auto",
    )
    return model
```

To:

```python
import os
from peft import PeftModel

ADAPTER_PATH = os.getenv("QWEN_ADAPTER_PATH", None)

def get_model():
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        "Qwen/Qwen2-VL-7B-Instruct",
        torch_dtype="auto",
        device_map="auto",
    )
    if ADAPTER_PATH and os.path.exists(ADAPTER_PATH):
        model = PeftModel.from_pretrained(model, ADAPTER_PATH)
        print(f"[model] Loaded LoRA adapter from {ADAPTER_PATH}")
    return model
```

> **Why env var?** Lets you switch between base and fine-tuned model without code changes.

### 5.2  Set the adapter path (manual)

Add to `ml_serving\.env`:

```env
QWEN_ADAPTER_PATH=D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\checkpoints\final
```

### 5.3  Restart the API server (manual)

If the FastAPI server is running, stop it (`Ctrl+C`) and restart:

```powershell
cd D:\Projects\geo-rescue-omni-GIS-agent\ml_serving
uvicorn api.app:app --host 0.0.0.0 --port 9000 --reload
```

**Verify the adapter loaded:**
```
INFO:     Started server process
[model] Loaded LoRA adapter from ...\checkpoints\final
INFO:     Application startup complete.
```

---

## Phase 6 — Continuous Improvement Loop (Optional)

After the initial 4-hour collection, you can keep improving the model with fresh data.
Weather conditions change over days and weeks — more diverse data = better model.

**Recommended schedule:**
- Collect 1,440 more samples every day (4 hours at 10s intervals)
- Re-train with the expanded dataset weekly
- Each training run builds on the previous (use `--resume-from`)

**One-liner to run daily collection + training:**

```powershell
# Collect 4 more hours
python ml_serving\training\run_training.py live-collect --duration-hours 4 --interval 10

# Re-train from last checkpoint
python ml_serving\training\run_training.py train `
  --dataset-index ml_serving\training_data\dataset_index.json `
  --output-dir ml_serving\checkpoints `
  --enrich-labels `
  --resume-from ml_serving\checkpoints\final
```

---

## Troubleshooting

### "Road network not found"
```
FileNotFoundError: Road network not found at ml_serving\training_data\processed\colombo_road_network.geojson
```
**Fix:** Run Phase 1 (copy Minindu's files or download via OSMnx).

---

### "SENTINEL_CLIENT_ID and SENTINEL_CLIENT_SECRET must be set"
```
ValueError: SENTINEL_CLIENT_ID and SENTINEL_CLIENT_SECRET must be set in .env
```
**Fix:** Create `.env` file as described in Phase 0.2. The collector will still work
without satellite credentials — satellite images just won't be saved. Weather + GIS labels
are still collected (Open-Meteo requires no credentials).

---

### Open-Meteo API errors / timeouts
```
requests.exceptions.ConnectionError: ...
```
**Why:** Temporary internet issue or Open-Meteo rate limit (unlikely at 10s intervals).
**Fix:** The collector catches errors per-sample and continues. Check `errors=N` in the
progress display — a few errors are normal. If errors are continuous, check your internet.

---

### CUDA / ROCm not available
```
GPU available: False
```
**Fix for AMD ROCm on Windows:**
```powershell
pip install torch --index-url https://download.pytorch.org/whl/rocm6.0
```
Confirm ROCm is installed: `rocm-smi` should show your GPU.

---

### Training loss not decreasing
- Reduce learning rate: `--lr 1e-4`
- Check labels look correct: inspect a `label.json` and its `training_label` field
- Ensure at least 50+ samples are in the dataset index

---

### `geopandas` `union_all()` AttributeError
```
AttributeError: 'GeoSeries' object has no attribute 'union_all'
```
**Fix:** Your geopandas version is < 0.14. Update: `pip install geopandas --upgrade`

---

## Timeline Summary

| Time | What to do |
|------|-----------|
| T+0:00 | Complete Phase 0 (manual setup, .env, venv, pip install) |
| T+0:15 | Complete Phase 1 (copy road network files) |
| T+0:20 | **Start live collection** (Phase 2) — leave running |
| T+4:20 | Collection finishes — ~1,440 samples in `dataset_index.json` |
| T+4:25 | Run label enrichment (Phase 3) — ~5 min |
| T+4:30 | **Start model training** (Phase 4) — leave running |
| T+8:30 | Training finishes — adapter weights in `checkpoints/final/` |
| T+8:35 | Edit `model_loader.py` + update `.env` (Phase 5) — 5 min |
| T+8:40 | Restart API server — fine-tuned model is live |

**Total hands-on time:** ~25 minutes of manual work.
**Total wall-clock time:** ~8.5–9 hours (mostly waiting).

---

## Dataset Statistics (Expected After 4-Hour Collection)

| Metric | Expected value |
|--------|---------------|
| Total samples | ~1,440 |
| Sample rate | 1 per 10 seconds |
| Satellite images | 8–9 (one initial + refresh every 30 min) |
| Severity distribution | Reflects actual weather (likely mostly "low" in dry weather) |
| Disk usage (samples/) | ~200–500 MB (GeoJSON per sample) |
| Disk usage (raw/) | ~70–90 MB (PNG satellite images) |
| `dataset_index.json` size | ~2–3 MB |

> **To get diverse severity levels:** Run collection over multiple days or in different
> weather conditions. Severity level "extreme" only appears during heavy rainfall (>30mm/hr).
