"""Qwen2-VL model loader with singleton pattern for memory efficiency."""

import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

MODEL_NAME = "Qwen/Qwen2-VL-7B-Instruct"

_model = None
_processor = None


def load_model():
    """Load and cache the Qwen2-VL model and processor.
    
    Uses singleton pattern so the model is loaded once into GPU memory
    and reused across all inference requests.
    """
    global _model, _processor

    if _model is None:
        print(f"[GeoRescue] Loading {MODEL_NAME}...")
        _model = Qwen2VLForConditionalGeneration.from_pretrained(
            MODEL_NAME,
            torch_dtype="auto",
            device_map="auto"
        )
        _processor = AutoProcessor.from_pretrained(MODEL_NAME)
        print(f"[GeoRescue] Model loaded on {_model.device}")

    return _model, _processor


def get_gpu_info():
    """Return current GPU memory usage."""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1e9
        reserved = torch.cuda.memory_reserved() / 1e9
        return {"allocated_gb": round(allocated, 2), "reserved_gb": round(reserved, 2)}
    return {"error": "No GPU available"}
