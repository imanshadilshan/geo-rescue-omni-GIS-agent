"""GeoRescue AI API — FastAPI application entry point.

Run with:
    uvicorn api.app:app --host 0.0.0.0 --port 9000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up models at startup to avoid cold-start latency."""
    from qwen_vl.model_loader import load_model
    load_model()
    print("[GeoRescue] All models loaded. API ready.")
    yield
    print("[GeoRescue] Shutting down...")


app = FastAPI(
    title="GeoRescue AI API",
    description="Disaster intelligence powered by Qwen2-VL on AMD MI300X GPU",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow cross-origin requests from the UI (Member 4)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
