# What's in this directory

This is the **serving copy** of the `Qwen/Qwen2-VL-7B-Instruct` LoRA adapter — the version the
ML serving code loads at inference time. It mirrors `georescue/colab/adapter/` (same files, same
content) but lives under `ml_serving/final3` so the serving pipeline has its own stable path to
load from.

## `tokenizer.json` (~12 MB)

The serialized Hugging Face **fast tokenizer** for `Qwen2Tokenizer` — vocabulary, BPE merge
rules, and pre/post-processing steps. It's what `AutoTokenizer.from_pretrained(...)` loads to
encode/decode text for the model.

**This file is generated from the base Qwen2-VL model, not from this project's training or
serving code.** It is byte-identical to `georescue/colab/adapter/tokenizer.json`. Nothing in the
serving pipeline writes or modifies it.

**You do not need to re-pull, re-import, or diff this file when reviewing serving changes.** Its
size (~12 MB, versus a few KB for the rest of this directory) comes entirely from the base
model's vocabulary — it carries no adapter-specific or serving-specific information.

## The other files here

| File | Purpose |
|---|---|
| `adapter_config.json` | LoRA hyperparameters (rank 16, alpha 32, dropout 0.05) and which attention projections were fine-tuned — the config that actually reflects training. |
| `tokenizer_config.json` | Special tokens (`<\|im_start\|>`, `<\|vision_start\|>`, image/video pad tokens, etc.), max sequence length (32768), padding side — used alongside `tokenizer.json`. |
| `processor_config.json` | Vision-tower preprocessing config (image/video normalization stats, patch size, resize bounds) since Qwen2-VL is multimodal. |
| `chat_template.jinja` | Jinja2 template that formats a chat conversation into the raw prompt string the model expects. |
| `README.md` | Auto-generated Hugging Face model card (mostly boilerplate placeholders). |

## Practical note

If you're only touching serving logic (not the model/adapter itself), you can safely ignore
`tokenizer.json` when pulling or reviewing diffs in this directory — it never changes as part of
normal serving work. If you want to stop tracking its changes in git going forward (e.g. via
`.gitattributes` filters or moving it out of version control into object storage), that's a
separate change — let me know if you'd like that set up.
