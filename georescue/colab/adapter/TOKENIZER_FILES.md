# What's in this directory

This is a **PEFT/LoRA adapter export** for `Qwen/Qwen2-VL-7B-Instruct`, produced from a Colab
training run. It is not a full model — it's a small set of trained weight deltas plus the
tokenizer/processor config needed to run them against the base model.

## `tokenizer.json` (~12 MB)

The serialized Hugging Face **fast tokenizer** (from the `tokenizers` Rust library). It contains
the full vocabulary, BPE merge rules, and pre/post-processing steps for `Qwen2Tokenizer`. This is
what lets `AutoTokenizer.from_pretrained(...)` load and encode/decode text instantly, without
re-downloading or rebuilding the tokenizer from the base Qwen2-VL model.

**It is a static, generated artifact of the base model — it is not produced or changed by this
LoRA training run.** The adapter only trains `q_proj`/`k_proj`/`v_proj`/`o_proj` weights (see
`adapter_config.json`); the tokenizer vocabulary is untouched. That means this file is identical
every time this adapter is exported, and identical to the copy in
`georescue/ml_serving/final3/tokenizer.json`.

**You do not need to re-pull, re-diff, or re-import this file when reviewing changes to the
adapter.** If it shows up as changed, that's a strong signal something regenerated it
unnecessarily (e.g. a re-export script), not a real content change worth reviewing.

## The other files here

| File | Purpose |
|---|---|
| `adapter_config.json` | LoRA hyperparameters (rank 16, alpha 32, dropout 0.05) and which attention projections were fine-tuned. This is the actual "what did training change" file. |
| `tokenizer_config.json` | Small config pointing at `tokenizer.json` — special tokens (`<\|im_start\|>`, `<\|vision_start\|>`, image/video pad tokens, etc.), max sequence length (32768), padding side. |
| `processor_config.json` | Image/video preprocessing config for the vision tower (normalization stats, patch size, resize bounds) — needed because Qwen2-VL is multimodal. |
| `chat_template.jinja` | Jinja2 template that formats a chat conversation (system/user/assistant turns, images) into the raw prompt string the model expects. |
| `README.md` | Auto-generated Hugging Face model card (mostly boilerplate placeholders). |

## Practical note

`tokenizer.json` is the only large file in this set (~12 MB vs. a few KB for everything else).
It's boilerplate copied from the base model, not adapter-specific output, so it's safe to skip
when pulling/reviewing/diffing this directory — only `adapter_config.json` (and the actual LoRA
weight file, if present elsewhere) reflect real training changes.
