# GeoRescue — Google Colab Training Guide
### Train Qwen2-VL-7B on your 1,404 GIS samples using Colab GPU, then bring the model back

---

## Overview

Your local machine may not have a compatible GPU for training. Google Colab gives you
free access to NVIDIA T4 (16 GB) or A100 (40 GB on Pro). This guide walks you through:

1. Packing your local data for upload
2. Running training on Colab step by step
3. Downloading the fine-tuned model adapter
4. Plugging it back into your local `ml_serving` API

**Total hands-on time:** ~30 minutes of setup + 2–5 hours of Colab training (unattended).

---

## What GPU You Get on Colab

| Colab tier | GPU | VRAM | Recommended batch size | Training time |
|------------|-----|------|----------------------|---------------|
| Free | NVIDIA T4 | 16 GB | 1 | ~5–7 hours |
| Colab Pro | NVIDIA A100 | 40 GB | 4 | ~2–3 hours |
| Colab Pro+ | NVIDIA A100 | 80 GB | 8 | ~1–2 hours |

> **Free tier is enough.** Qwen2-VL-7B in fp16 uses ~14 GB. T4 has 16 GB — tight but works
> with batch_size=1 and gradient checkpointing enabled.

---

## Part 1 — Prepare Files on Your Local Machine

### 1.1 Files you need to pack (DO THIS BEFORE GOING TO COLAB)

You need to zip two things:

**A) The training data folder**
Location: `D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\training_data\`
Contains: 1,404 sample folders + satellite images + dataset_index.json

**B) The training code folder**
Location: `D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\training\`
Contains: dataset.py, label_generator.py, trainer.py, run_training.py

### 1.2 Create the zip files (run in your PowerShell)

```powershell
# Zip training data (~150-300 MB zipped)
Compress-Archive `
  -Path "D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\training_data" `
  -DestinationPath "D:\Projects\geo-rescue-omni-GIS-agent\training_data_upload.zip" `
  -Force

# Zip training code (~small, a few KB)
Compress-Archive `
  -Path "D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\training" `
  -DestinationPath "D:\Projects\geo-rescue-omni-GIS-agent\training_code_upload.zip" `
  -Force

Write-Host "Done. Check sizes:"
Get-Item "D:\Projects\geo-rescue-omni-GIS-agent\training_data_upload.zip" | Select-Object Name, @{n='Size_MB';e={[math]::Round($_.Length/1MB,1)}}
Get-Item "D:\Projects\geo-rescue-omni-GIS-agent\training_code_upload.zip" | Select-Object Name, @{n='Size_MB';e={[math]::Round($_.Length/1MB,1)}}
```

### 1.3 Files you will upload to Colab

| File | Location after zip | Approx size | What it contains |
|------|--------------------|-------------|-----------------|
| `training_data_upload.zip` | Project root | ~150–300 MB | 1,404 samples, GeoJSON labels, satellite PNGs, dataset_index.json |
| `training_code_upload.zip` | Project root | < 1 MB | dataset.py, label_generator.py, trainer.py |

---

## Part 2 — Google Colab Setup

### 2.1 Open a new Colab notebook

1. Go to https://colab.research.google.com/
2. Click **"New notebook"**
3. Go to **Runtime → Change runtime type**
4. Select **GPU** → choose **T4** (free) or **A100** (Pro)
5. Click **Save**

### 2.2 Upload your files to Colab

In the left sidebar click the **folder icon** → then the **upload icon** (arrow pointing up).

Upload both files:
- `training_data_upload.zip`
- `training_code_upload.zip`

> **Alternative — Google Drive (recommended for large files):**
> Upload both zips to your Google Drive, then mount Drive in Colab (Cell 2 shows how).
> This is faster for large files and survives session disconnects.

---

## Part 3 — Colab Notebook Cells (copy-paste each cell)

Create a new code cell for each section below. Run them **in order**.

---

### CELL 1 — Check GPU

```python
# Verify GPU is assigned before doing anything else
!nvidia-smi

import torch
print("\nPyTorch CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU device:", torch.cuda.get_device_name(0))
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"VRAM: {vram:.1f} GB")
    if vram < 15:
        print("WARNING: Less than 15 GB VRAM — use batch_size=1 in Cell 7")
else:
    print("ERROR: No GPU found. Go to Runtime → Change runtime type → GPU")
```

**Expected output:**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI ...   Driver Version: ...   CUDA Version: ...                    |
+-------------+---+
| Tesla T4    |...|
+-------------+---+

PyTorch CUDA available: True
GPU device: Tesla T4
VRAM: 15.8 GB
```

If you see `No GPU found`, stop and change the runtime type first.

---

### CELL 2 — (Optional) Mount Google Drive

Only needed if you uploaded your zips to Google Drive instead of directly to Colab.

```python
# SKIP THIS CELL if you uploaded files directly to Colab (not Google Drive)
from google.colab import drive
drive.mount('/content/drive')

# After mounting, find your files:
import os
# Change this path to wherever you put the zips in your Drive
DRIVE_PATH = "/content/drive/MyDrive/"
print("Files in Drive root:")
print([f for f in os.listdir(DRIVE_PATH) if f.endswith('.zip')])
```

---

### CELL 3 — Install packages

```python
# DO NOT install torch/torchvision/torchaudio here.
# Colab pre-installs matched versions. Installing them via pip upgrades torch
# to a newer CUDA build but leaves torchvision on the old one, causing:
#   RuntimeError: PyTorch CUDA=13.0 but torchvision CUDA=12.8

!pip install -q \
    transformers==4.45.0 \
    accelerate \
    "peft==0.12.0" \
    qwen-vl-utils \
    geopandas \
    shapely \
    pillow \
    sentinelhub \
    python-dotenv \
    requests

# peft==0.12.0 is pinned — newer peft versions require torchao>=0.16.0
# but Colab's system torchao (0.10.0) re-asserts itself after every restart.

print("All packages installed.")

import torch, transformers, peft
print(f"transformers : {transformers.__version__}")
print(f"peft         : {peft.__version__}")   # must show 0.12.0
print(f"torch        : {torch.__version__}")
print(f"CUDA         : {torch.cuda.is_available()}")
print(f"torch CUDA   : {torch.version.cuda}")
```

---

### CELL 4 — Upload and extract files

> **Note:** Windows `Compress-Archive` stores paths with backslashes inside the zip.
> Linux treats backslashes as part of the filename instead of path separators, so a
> plain `extractall()` produces broken flat files. This cell converts backslashes to
> forward slashes during extraction.

```python
import zipfile, os
from pathlib import Path

# -----------------------------------------------------------------------
# If you uploaded directly to Colab (files are in /content/):
DATA_ZIP = "/content/training_data_upload.zip"
CODE_ZIP = "/content/training_code_upload.zip"

# If you used Google Drive (uncomment and adjust path):
# DATA_ZIP = "/content/drive/MyDrive/training_data_upload.zip"
# CODE_ZIP = "/content/drive/MyDrive/training_code_upload.zip"
# -----------------------------------------------------------------------

def extract_windows_zip(zip_path, extract_to):
    """Extract a zip created on Windows, converting backslash paths to forward slashes."""
    extract_to = Path(extract_to)
    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.infolist():
            clean_name = member.filename.replace("\\", "/")
            target = extract_to / clean_name
            if clean_name.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(member) as src, open(target, "wb") as dst:
                dst.write(src.read())
    print(f"  Done → {extract_to}")

print("Extracting training data...")
extract_windows_zip(DATA_ZIP, "/content/")

print("Extracting training code...")
extract_windows_zip(CODE_ZIP, "/content/")

# ── Verify ───────────────────────────────────────────────────────────────────
data_dir = Path("/content/training_data")
code_dir = Path("/content/training")

index_ok  = (data_dir / "dataset_index.json").exists()
samples_n = len(list((data_dir / "samples").iterdir())) if (data_dir / "samples").exists() else 0
sat_n     = len(list((data_dir / "raw").glob("*.png")))  if (data_dir / "raw").exists() else 0
trainer_ok = (code_dir / "trainer.py").exists()

print(f"\nDataset index  : {'OK' if index_ok else 'MISSING'}")
print(f"Samples        : {samples_n}")
print(f"Satellite PNGs : {sat_n}")
print(f"trainer.py     : {'OK' if trainer_ok else 'MISSING'}")
```

**Expected output:**
```
Extracting training data...
  Done → /content
Extracting training code...
  Done → /content

Dataset index  : OK
Samples        : 1452
Satellite PNGs : 7
trainer.py     : OK
```

---

### CELL 5 — Load the dataset and inspect

```python
import sys, json
sys.path.insert(0, "/content")

from training.label_generator import enrich_dataset_labels
from training.dataset import FloodAnalysisDataset

INDEX_PATH = "/content/training_data/dataset_index.json"

# Re-enrich labels with Colab paths (local Windows paths won't work here)
print("Re-enriching labels with Colab paths...")
samples = json.loads(open(INDEX_PATH).read())

for s in samples:
    # Fix Windows paths → Colab paths for satellite images
    sat = s.get("satellite_image_path")
    if sat:
        fname = Path(sat).name
        colab_sat = f"/content/training_data/raw/{fname}"
        s["satellite_image_path"] = colab_sat if Path(colab_sat).exists() else None

    # Fix flood polygon paths
    fp = s.get("flood_polygon_path")
    if fp:
        sid = s["sample_id"]
        s["flood_polygon_path"] = f"/content/training_data/samples/{sid}/live_flood_polygon.geojson"

    # Fix blocked roads paths
    bp = s.get("blocked_roads_path")
    if bp:
        sid = s["sample_id"]
        s["blocked_roads_path"] = f"/content/training_data/samples/{sid}/blocked_roads_flood.geojson"

    # Rebuild training label with Colab paths
    from training.label_generator import build_training_label
    s["training_label"] = build_training_label(s)

open(INDEX_PATH, "w").write(json.dumps(samples, indent=2))
print(f"Re-enriched {len(samples)} samples.")

# Load dataset and print a sample
dataset = FloodAnalysisDataset(INDEX_PATH, require_image=False)
print(f"\nDataset size: {len(dataset)}")
sample = dataset[0]
print(f"Sample keys: {list(sample.keys())}")
print(f"Prompt: {sample['prompt'][:80]}...")
print(f"Expected output: {sample['expected_output'][:120]}...")
print(f"Has image: {'image' in sample}")
```

---

### CELL 6 — Configure training for your GPU

```python
import torch

# Auto-detect GPU and set batch size accordingly
vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9 if torch.cuda.is_available() else 0

if vram_gb >= 35:      # A100 40GB or better
    BATCH_SIZE = 4
    USE_GRAD_CKPT = False
    print(f"A100 detected ({vram_gb:.0f} GB) → batch_size=4")
elif vram_gb >= 15:    # T4 16GB
    BATCH_SIZE = 1
    USE_GRAD_CKPT = True
    print(f"T4 detected ({vram_gb:.0f} GB) → batch_size=1 + gradient checkpointing")
else:
    BATCH_SIZE = 1
    USE_GRAD_CKPT = True
    print(f"Unknown GPU ({vram_gb:.0f} GB) → batch_size=1 (conservative)")

EPOCHS      = 3
LR          = 2e-4
OUTPUT_DIR  = "/content/checkpoints"
INDEX_PATH  = "/content/training_data/dataset_index.json"

print(f"\nTraining config:")
print(f"  Dataset    : {INDEX_PATH}")
print(f"  Output     : {OUTPUT_DIR}")
print(f"  Epochs     : {EPOCHS}")
print(f"  Batch size : {BATCH_SIZE}")
print(f"  LR         : {LR}")
print(f"  Grad ckpt  : {USE_GRAD_CKPT}")
```

---

### CELL 7 — Run training

```python
# This cell will run for 2-7 hours depending on your GPU
# DO NOT close the browser tab — Colab disconnects if idle
# Tip: keep the tab open and check back periodically

import sys
sys.path.insert(0, "/content")

import torch
from pathlib import Path
from peft import LoraConfig, TaskType, get_peft_model
from transformers import (
    AutoProcessor,
    Qwen2VLForConditionalGeneration,
    Trainer,
    TrainingArguments,
)
from training.dataset import FloodAnalysisDataset

# ── Self-contained config (safe to run without Cell 6) ──────────────────────
vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9 if torch.cuda.is_available() else 0
try:
    _ = BATCH_SIZE  # use Cell 6 values if already set
except NameError:
    BATCH_SIZE    = 4 if vram_gb >= 35 else 1
    USE_GRAD_CKPT = vram_gb < 35
    EPOCHS        = 3
    LR            = 2e-4
    OUTPUT_DIR    = "/content/checkpoints"
    INDEX_PATH    = "/content/training_data/dataset_index.json"
    print(f"[config] batch={BATCH_SIZE}  grad_ckpt={USE_GRAD_CKPT}  epochs={EPOCHS}  lr={LR}")

MODEL_ID = "Qwen/Qwen2-VL-7B-Instruct"

LORA_CONFIG = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
)

# ── Load model ──────────────────────────────────────────────────────────────
print("Loading processor...")
processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)

print("Loading model (16.6 GB download + load — takes 5-10 min first time)...")
model = Qwen2VLForConditionalGeneration.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
)

if USE_GRAD_CKPT:
    model.gradient_checkpointing_enable()
    print("Gradient checkpointing enabled (saves VRAM on T4)")

model = get_peft_model(model, LORA_CONFIG)
model.print_trainable_parameters()

# ── Dataset split ───────────────────────────────────────────────────────────
full_dataset = FloodAnalysisDataset(INDEX_PATH, require_image=False)
n_eval  = max(1, int(len(full_dataset) * 0.1))
n_train = len(full_dataset) - n_eval
train_set, eval_set = torch.utils.data.random_split(full_dataset, [n_train, n_eval])
print(f"\nTrain: {n_train}  Eval: {n_eval}")

# ── Collate function ────────────────────────────────────────────────────────
def collate(batch):
    texts, images = [], []
    for item in batch:
        has_img = "image" in item
        content = []
        if has_img:
            content.append({"type": "image", "image": item["image"]})
            images.append(item["image"])
        content.append({"type": "text", "text": item["prompt"]})
        conversation = [
            {"role": "user",      "content": content},
            {"role": "assistant", "content": [{"type": "text", "text": item["expected_output"]}]},
        ]
        texts.append(
            processor.apply_chat_template(conversation, tokenize=False, add_generation_prompt=False)
        )
    inputs = processor(
        text=texts,
        images=images or None,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=2048,
    )
    inputs["labels"] = inputs["input_ids"].clone()
    return inputs

# ── Training arguments ──────────────────────────────────────────────────────
args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    learning_rate=LR,
    warmup_ratio=0.05,
    lr_scheduler_type="cosine",
    fp16=True,
    logging_steps=20,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    report_to="none",
    remove_unused_columns=False,
    dataloader_num_workers=2,
    gradient_checkpointing=USE_GRAD_CKPT,
)

# ── Train ───────────────────────────────────────────────────────────────────
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_set,
    eval_dataset=eval_set,
    data_collator=collate,
)

print("\nStarting training...")
trainer.train()

# ── Save final adapter ──────────────────────────────────────────────────────
final_path = Path(OUTPUT_DIR) / "final"
trainer.save_model(str(final_path))
processor.save_pretrained(str(final_path))
print(f"\nModel adapter saved to {final_path}")
print("Contents:", list(final_path.iterdir()))
```

**What you will see during training:**
```
trainable params: 20,185,088 || all params: 7,615,616,000 || trainable%: 0.265
Train: 1263  Eval: 141

Starting training...
{'loss': 2.14, 'learning_rate': 0.0002, 'epoch': 0.12}
{'loss': 1.89, 'learning_rate': 0.000185, 'epoch': 0.25}
...
{'eval_loss': 1.72, 'epoch': 1.0}   ← checkpoint saved
...
{'eval_loss': 1.58, 'epoch': 2.0}   ← checkpoint saved
...
{'eval_loss': 1.51, 'epoch': 3.0}   ← checkpoint saved (best)

Model adapter saved to /content/checkpoints/final
```

Loss should decrease each epoch. If loss stays above 2.5 after epoch 1, stop and reduce `LR` to `1e-4`.

---

### CELL 8 — Save checkpoints to Google Drive (IMPORTANT — do this before session ends)

Colab deletes `/content/` when the session ends. Save your work to Drive first.

```python
# Mount Drive if not already mounted
from google.colab import drive
import shutil, os
from pathlib import Path

drive.mount('/content/drive', force_remount=False)

# Create destination folder in Drive
drive_dest = "/content/drive/MyDrive/georescue_checkpoints"
os.makedirs(drive_dest, exist_ok=True)

# Copy checkpoints to Drive
print("Copying checkpoints to Google Drive...")
shutil.copytree(
    "/content/checkpoints",
    f"{drive_dest}/checkpoints",
    dirs_exist_ok=True
)
print(f"Saved to {drive_dest}/checkpoints")
print("Contents:")
for f in Path(f"{drive_dest}/checkpoints/final").iterdir():
    size = f.stat().st_size / 1e6
    print(f"  {f.name:40s}  {size:.1f} MB")
```

---

### CELL 9 — Download the adapter to your computer

The fine-tuned model is just a small adapter (not the full 16 GB model).
Typical size: **40–80 MB** total.

```python
# Zip the final adapter folder for download
import shutil
shutil.make_archive(
    "/content/georescue_adapter",   # output zip name
    "zip",
    "/content/checkpoints/final"    # folder to zip
)

# Download it to your computer
from google.colab import files
files.download("/content/georescue_adapter.zip")

print("Download started. Check your browser's download folder.")
print("\nFile sizes in adapter:")
for f in Path("/content/checkpoints/final").iterdir():
    print(f"  {f.name}: {f.stat().st_size / 1e6:.1f} MB")
```

**Files that will be in the zip (total ~40–80 MB):**
```
adapter_config.json          ← LoRA config (tiny)
adapter_model.safetensors    ← trained weights (~40-80 MB)
special_tokens_map.json      ← tokenizer metadata
tokenizer.json
tokenizer_config.json
preprocessor_config.json
```

---

## Part 4 — Bring the Model Back to Your Local Setup

### 4.1 Extract the downloaded zip

After downloading `georescue_adapter.zip`, extract it:

```powershell
Expand-Archive `
  -Path "$env:USERPROFILE\Downloads\georescue_adapter.zip" `
  -DestinationPath "D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\checkpoints\final" `
  -Force

# Verify
Get-ChildItem "D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\checkpoints\final"
```

Expected output:
```
adapter_config.json
adapter_model.safetensors    (~40-80 MB)
tokenizer.json
tokenizer_config.json
...
```

### 4.2 Add adapter path to `.env`

Open `D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\.env` and add:

```env
QWEN_ADAPTER_PATH=D:\Projects\geo-rescue-omni-GIS-agent\ml_serving\checkpoints\final
```

### 4.3 Edit `model_loader.py` to load the adapter (manual)

Open [ml_serving/qwen_vl/model_loader.py](ml_serving/qwen_vl/model_loader.py)

Find the function that loads the model and update it to:

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
        print(f"[model] LoRA adapter loaded from {ADAPTER_PATH}")
    return model
```

### 4.4 Restart the serving API

```powershell
cd D:\Projects\geo-rescue-omni-GIS-agent\ml_serving
uvicorn api.app:app --host 0.0.0.0 --port 9000 --reload
```

You should see:
```
[model] LoRA adapter loaded from ...\checkpoints\final
INFO:     Application startup complete.
```

---

## Tips for Long Colab Sessions

### Prevent disconnection (Colab disconnects after ~90 min idle)

Paste this in your browser console (F12 → Console) to keep the session alive:

```javascript
// Paste in browser console to click "Reconnect" automatically
setInterval(() => {
  document.querySelector('#connect')?.click();
}, 60000);
```

### If your session disconnects mid-training

The checkpoints are saved per epoch. If you saved to Drive (Cell 8), you can resume:

1. Start a new Colab session
2. Re-run Cell 1, 2, 3, 4 (setup)
3. Find your last checkpoint in Drive (e.g. `checkpoint-400`)
4. In Cell 7, change the `trainer.train()` line to:

```python
trainer.train(resume_from_checkpoint="/content/drive/MyDrive/georescue_checkpoints/checkpoints/checkpoint-400")
```

### Save checkpoints to Drive after each epoch

Add this callback before `trainer.train()` in Cell 7:

```python
from transformers import TrainerCallback
import shutil

class SaveToDriveCallback(TrainerCallback):
    def on_epoch_end(self, args, state, control, **kwargs):
        epoch = int(state.epoch)
        src = f"{OUTPUT_DIR}/checkpoint-{state.global_step}"
        dst = f"/content/drive/MyDrive/georescue_checkpoints/epoch_{epoch}"
        if Path(src).exists():
            shutil.copytree(src, dst, dirs_exist_ok=True)
            print(f"\n[drive] Epoch {epoch} checkpoint saved to Drive → {dst}")

trainer = Trainer(
    ...
    callbacks=[SaveToDriveCallback()],
)
```

---

## Summary Checklist

### Before opening Colab
- [ ] Run the PowerShell zip commands (Section 1.2)
- [ ] Confirm `training_data_upload.zip` is ~150–300 MB
- [ ] Confirm `training_code_upload.zip` is < 1 MB

### In Colab
- [ ] Cell 1: GPU confirmed (T4 or better)
- [ ] Cell 2: Drive mounted (if using Drive)
- [ ] Cell 3: Packages installed, all imports OK
- [ ] Cell 4: Files extracted, 1404 samples confirmed
- [ ] Cell 5: Labels re-enriched with Colab paths
- [ ] Cell 6: Batch size set for your GPU
- [ ] Cell 7: Training running, loss decreasing
- [ ] Cell 8: Checkpoints saved to Drive before session ends
- [ ] Cell 9: `georescue_adapter.zip` downloaded to your computer

### Back on your local machine
- [ ] Extracted adapter to `ml_serving\checkpoints\final\`
- [ ] Added `QWEN_ADAPTER_PATH` to `.env`
- [ ] Edited `qwen_vl\model_loader.py` to load adapter
- [ ] Restarted serving API, confirmed adapter loaded in logs
