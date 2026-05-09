# GeoRescue — Omni GIS Agent

> AI-powered disaster response platform for the **AMD Developer Hackathon**.  
> Real-time flood analysis · Satellite damage detection · Safe evacuation routing

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     STREAMLIT UI  (app.py :8501)                        │
│   Mission prompt · Satellite upload · Folium map · Live agent panel     │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │  run_pipeline_with_status()
┌────────────────────────────▼─────────────────────────────────────────────┐
│               CREWAI AGENT PIPELINE  (agents/)                           │
│                  LLM: Ollama  llama3.2  (local inference)               │
│                                                                          │
│  1. Vision Analyst      POST /analyze-image    Qwen2-VL-7B damage detect│
│  2. Data Scout          POST /gis/run-cycle    Open-Meteo live weather   │
│  3. Spatial Navigator   GET  /gis/flood-polygon                          │
│                         GET  /gis/blocked-roads                          │
│                         GET  /gis/safe-route                            │
│  4. Reporting Coord.    Ollama synthesises Markdown incident report      │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │  HTTP REST  (localhost:9000)
┌────────────────────────────▼─────────────────────────────────────────────┐
│          FASTAPI GIS & VISION SERVER  (ml_serving/ :9000)               │
│                                                                          │
│  Vision   Qwen2-VL-7B + LoRA (final3/)   AMD Instinct MI300X / ROCm    │
│  GIS      Open-Meteo → flood polygon → road network overlay              │
│           OSMnx + NetworkX → safe route planning                         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Team

| # | Member | Role | Key Technologies |
|---|--------|------|-----------------|
| 1 | **Imansha** *(Team Lead)* | AI Orchestrator | CrewAI, Ollama Llama 3.2, Python |
| 2 | **Minindu** | GIS & Data Engineer | GeoPandas, OSMnx, Open-Meteo API |
| 3 | **Supun** | ML / Hardware | AMD MI300X, Qwen2-VL, FastAPI, ROCm |
| 4 | **Ramitha** | UI & Deployment | Streamlit, Folium, Hugging Face Spaces |

---

## Project Structure

```
georescue/
├── agents/                   # AI Orchestration — Member 1
│   ├── __init__.py           #   Public API: run_pipeline_with_status()
│   ├── tools.py              #   CrewAI @tool wrappers (one per API endpoint)
│   ├── crew.py               #   Agent + Task definitions, Ollama LLM config
│   └── pipeline.py           #   Generator pipeline (AgentUpdate, PipelineResult)
│
├── georescue/                # UI utility package — Members 1 + 4
│   ├── config.py             #   Pydantic-settings config (reads .env)
│   ├── state.py              #   Streamlit session-state management
│   ├── map_layers.py         #   Folium builders: flood, blocked, route, markers
│   ├── routing.py            #   OSMnx cached graph + NetworkX safe-route
│   ├── geojson_utils.py      #   GeoJSON export helpers
│   └── logging_setup.py      #   Centralised logging
│
├── ml_serving/               # GIS + Vision API server — Member 3
│   ├── api/                  #   FastAPI routes + schemas
│   ├── gis_pipeline/         #   Flood cycle: weather → polygon → roads → route
│   ├── qwen_vl/              #   Qwen2-VL-7B inference + GeoJSON generator
│   ├── llama_server/         #   vLLM Llama server config (AMD MI300X)
│   ├── training/             #   LoRA fine-tuning scripts
│   ├── data_pipeline/        #   Satellite data collection
│   ├── benchmarks/           #   GPU throughput tests
│   ├── data/processed/       #   Runtime GeoJSON + GraphML (gitignored)
│   ├── final3/               #   Qwen2-VL LoRA adapter weights (gitignored)
│   └── requirements.txt      #   ML-specific dependencies
│
├── app.py                    # Streamlit entry point
├── requirements.txt          # Core dependencies (UI + agents, no GPU required)
├── Makefile                  # Dev shortcuts: make install / api / app / all
├── .env                      # Local config — gitignored, never commit
├── .env.example              # Shareable template — commit this
├── .gitignore
└── README.md
```

---

## Quick Start

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime |
| Ollama | latest | Local LLM for agent reasoning |
| ROCm / CUDA | optional | GPU acceleration for Qwen-VL |

```bash
# Install Ollama (https://ollama.com/download), then:
ollama pull llama3.2
```

### 1. Clone and configure

```bash
git clone <repo-url>
cd georescue

# Create your local .env from the template
cp .env.example .env
# Defaults work for local development — edit only if your ports differ
```

### 2. Install dependencies

```bash
# UI + agent framework  (no GPU required)
pip install -r requirements.txt

# ML serving  (AMD ROCm or CUDA required)
cd ml_serving && pip install -r requirements.txt && cd ..
```

Or with Make:

```bash
make install      # UI + agents
make install-ml   # ML serving
```

### 3. Start services

**Terminal 1 — GIS & Vision API:**
```bash
cd ml_serving
uvicorn api.app:app --host 0.0.0.0 --port 9000 --reload
```

**Terminal 2 — Streamlit UI:**
```bash
streamlit run app.py
```

Or start both at once (requires `make`):
```bash
make all
```

Open **http://localhost:8501**

> **Offline mode:** The app works without the API server.  
> It falls back to local OSMnx routing and a template report.

---

## Agent Pipeline

Clicking **▶ Run Agent Pipeline** executes four agents sequentially, with
live progress shown inside the `st.status()` panel in real time:

| Step | Agent | Tool calls | Requires |
|------|-------|-----------|---------|
| 1 | **Vision Analyst** | `POST /analyze-image` | Image upload + API |
| 2 | **Data Scout** | `POST /gis/run-cycle` | API server |
| 3 | **Spatial Navigator** | `GET /gis/flood-polygon`<br>`GET /gis/blocked-roads`<br>`GET /gis/safe-route` | API server |
| 4 | **Reporting Coordinator** | *(Ollama reasoning only)* | Ollama |

---

## Degradation Matrix

| GIS API | Ollama | Behaviour |
|---------|--------|-----------|
| Online | Online | Full pipeline: live flood layers + AI-generated report |
| Online | Offline | Live GIS data on map + structured template report |
| Offline | Online | Local OSMnx routing + AI-generated report |
| Offline | Offline | Local OSMnx routing + template report |

---

## API Reference

The GIS & Vision server exposes these endpoints (docs at `:9000/docs`):

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health (LLM, Qwen-VL, GPU status) |
| `POST` | `/analyze-image` | Satellite image → severity + GeoJSON zones |
| `POST` | `/gis/run-cycle` | Trigger live flood analysis cycle |
| `GET` | `/gis/status` | Latest flood cycle status |
| `GET` | `/gis/flood-polygon` | Current flood zone GeoJSON |
| `GET` | `/gis/blocked-roads` | Flood-blocked road segments GeoJSON |
| `GET` | `/gis/safe-route` | Computed safe route GeoJSON |

---

## Environment Variables

See [`.env.example`](.env.example) for the full annotated list.  
Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `GIS_API_URL` | `http://localhost:9000` | FastAPI server URL |
| `ADAPTER_PATH` | `final3` | LoRA adapter path (relative to `ml_serving/`) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server |
| `OLLAMA_MODEL` | `llama3.2` | Model name (`llama3.2` / `llama3.1:8b`) |
| `LLM_TEMPERATURE` | `0.1` | Sampling temperature |
| `MAP_CENTER_LAT/LON` | `6.9271 / 79.8612` | Default map centre (Colombo Fort) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
