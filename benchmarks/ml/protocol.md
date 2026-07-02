# ML Benchmark Protocol — Endoscopy Classification

## Dataset layouts

### Kvasir v1 (4 classes) — B0 / B1

```
data/kvasir/
├── train/          # cecum, pylorus, polyp, ulcer
├── val/
└── test/
```

Prepare: `pixi run prepare-kvasir -- --output data/kvasir`

### HyperKvasir (23 classes) — B2–B6

```
data/hyperkvasir/
├── train/          # 23 official Simula class folders
├── val/
└── test/
```

Prepare: `pixi run prepare-hyperkvasir -- --output data/hyperkvasir`

Stratified split per class: 70 % train, 15 % val, 15 % test (seed 42).

## Metrics

| Metric | Role |
|--------|------|
| **Macro-F1** | Primary model selection and reporting |
| **Weighted-F1** | Secondary — class frequency |
| **Accuracy** | Comparison with prior work |
| **Per-class recall** | Clinical (polyp, ulcer, rare classes) |
| **Confusion matrix** | 4×4 (Kvasir) or 23×23 (HyperKvasir) |
| **Grouped macro-recall** | Landmarks / pathologies / dyed procedures / quality (HyperKvasir) |

## Benchmark matrix

| ID | Architecture | Pretrain | Dataset | Description |
|----|--------------|----------|---------|-------------|
| B0 | `resnet50_from_scratch` (legacy) | none | Kvasir v1 | Baseline scratch |
| B1 | `resnet50_from_scratch` + Optuna | none | Kvasir v1 | HPO baseline |
| B2 | `resnet50` | ImageNet | HyperKvasir | Fine-tune transfer |
| B3 | `seresnet50` | none | HyperKvasir | SE channel recalibration scratch |
| B4 | `seresnet50` | ImageNet | HyperKvasir | SE + transfer |
| B5 | `dualstream_resnet_color_texture` | none | HyperKvasir | RGB + HSV/LBP fusion |
| B6 | `dualstream_resnet_color_texture` | ImageNet (RGB) | HyperKvasir | Dual-stream, RGB pretrained |

## Training defaults

| Regime | Epochs | LR | Batch | Optimizer |
|--------|--------|-----|-------|-----------|
| Scratch (B0, B3, B5) | 15–20 | 1e-3 | 16 | AdamW |
| ImageNet fine-tune (B2, B4, B6) | 15–20 | 1e-4 | 16 | AdamW |

Selection criterion: **best validation macro-F1**.

## CLI — architecture registry

```bash
# ResNet-50 scratch (torchvision backbone)
pixi run train -- --data-dir data/hyperkvasir --arch resnet50 --epochs 15 \
  --output checkpoints/hyperkvasir/b3_resnet50_scratch.pt

# ResNet-50 ImageNet (B2)
pixi run train -- --data-dir data/hyperkvasir --arch resnet50 --pretrained --epochs 15 \
  --output checkpoints/hyperkvasir/b2_resnet50_imagenet.pt

# SE-ResNet-50 scratch (B3)
pixi run train -- --data-dir data/hyperkvasir --arch seresnet50 --epochs 15 \
  --output checkpoints/hyperkvasir/b3_seresnet50_scratch.pt

# SE-ResNet-50 ImageNet (B4)
pixi run train -- --data-dir data/hyperkvasir --arch seresnet50 --pretrained --epochs 15 \
  --output checkpoints/hyperkvasir/b4_seresnet50_imagenet.pt

# Dual-stream scratch (B5)
pixi run train -- --data-dir data/hyperkvasir --arch dualstream_resnet_color_texture --epochs 15 \
  --output checkpoints/hyperkvasir/b5_dualstream_scratch.pt

# Dual-stream ImageNet RGB (B6)
pixi run train -- --data-dir data/hyperkvasir --arch dualstream_resnet_color_texture --pretrained --epochs 15 \
  --output checkpoints/hyperkvasir/b6_dualstream_imagenet.pt
```

## Evaluation

```bash
pixi run evaluate -- --checkpoint checkpoints/hyperkvasir/b2_resnet50_imagenet.pt \
  --data-dir data/hyperkvasir --split test \
  --output benchmarks/ml/results/hyperkvasir_b2_test.json
```

## Full HyperKvasir campaign

```bash
bash scripts/run_hyperkvasir_benchmarks.sh
```

Environment overrides: `EPOCHS=15`, `DEVICE=auto|cpu|mps`, `DATA_DIR=data/hyperkvasir`.

## Optuna search space (Kvasir B1)

| Hyperparameter | Range |
|----------------|-------|
| `lr` | log-uniform [1e-5, 1e-2] |
| `weight_decay` | log-uniform [1e-6, 1e-2] |
| `batch_size` | {8, 16, 32} |
| `optimizer` | {adamw, sgd} |
| `scheduler` | {none, cosine, step} |
| `label_smoothing` | [0.0, 0.2] |
| `img_size` | {224, 256} |

## HyperKvasir results template

Fill `benchmarks/ml/results/summary.md` after B2–B6:

| Run ID | Arch | Pretrain | Split | Accuracy | Macro-F1 | Weighted-F1 |
|--------|------|----------|-------|----------|----------|-------------|
| B2 | resnet50 | ImageNet | test | — | — | — |
| B3 | seresnet50 | none | test | — | — | — |
| B4 | seresnet50 | ImageNet | test | — | — | — |
| B5 | dualstream | none | test | — | — | — |
| B6 | dualstream | ImageNet | test | — | — | — |

## Reproducibility

- Checkpoints include `arch`, `pretrained`, `class_names`, `hparams`, `metrics`
- Fixed seed: 42 (training), stratified split seed 42 (data prep)
- MPS fallback: `--device cpu` if GPU unstable

---

## CNN-JEPA article protocol — colonoscopy 3-class (C0–C10)

### Dataset

```
data/colonoscopy_3class/
├── manifest.json
├── all/train|val|test/     # landmark, normal_mucosa, polyp
└── folds/fold_{center_id}/train|val|test/
```

Prepare:

```bash
pixi run prepare-colonoscopy-3class
pixi run extract-video-frames -- --hyperkvasir-video data/raw/hyper-kvasir-videos
```

| Class | Definition |
|-------|------------|
| `landmark` | Cecum, pylorus, z-line, ileum, retroflexions |
| `normal_mucosa` | BBPS scores, hemorrhoids, impacted stool |
| `polyp` | Polyps, dyed-lifted polyps |

**Primary metrics:** macro-F1 (model selection), polyp recall (clinical).

### Early stopping (article defaults)

| Phase | Monitor | Mode | Patience | min_epochs | max_epochs |
|-------|---------|------|----------|------------|------------|
| CNN-JEPA pretrain | `val_latent_loss` | min | 10 | 20 | 80 |
| Fine-tune | `val_macro_f1` | max | 5 | 5 | 30 |
| Linear probe (C6) | `val_macro_f1` | max | 3 | 3 | 15 |

Each run writes `{checkpoint}.early_stop.json`. Skip re-run if `benchmarks/ml/results/{run_id}_test.json` exists.

### Benchmark matrix C0–C10

| ID | Method | Pretrain | Labels | Role |
|----|--------|----------|--------|------|
| C0 | SE-ResNet-50 | none | 100 % | Scratch baseline |
| C1 | SE-ResNet-50 | ImageNet | 100 % | Transfer baseline (H1) |
| C2 | ResNet-50 | CNN-JEPA | 100 % | JEPA without SE |
| C3 | SE-ResNet-50 | CNN-JEPA + SE standard | 100 % | Ablation H2 |
| C4 | SE-ResNet-50 | CNN-JEPA + SE mask-aware | 100 % | **Proposed (H1)** |
| C5 | SE-ResNet-50 | Frozen endoscopy teacher | 100 % | Ablation H3 |
| C6 | ViT foundation | linear probe | 100 % | Reference ceiling |
| C7–C9 | C4 | CNN-JEPA | 10 / 25 / 50 % | Label efficiency |
| C10 | C4 | CNN-JEPA | LOO held-out center | Main table |

### CLI examples

```bash
# Shared JEPA pretrain (once)
pixi run pretrain-jepa -- --frames-dir data/jepa_frames --backbone seresnet50 \
  --mask-aware-se --output checkpoints/jepa/c4_mask_aware_shared.pt

# Fine-tune C4 on one LOO fold
bash scripts/run_loo_benchmark.sh C4 fold_simula

# Full campaign (one job per invocation)
bash scripts/run_article_campaign_loop.sh
bash scripts/run_article_campaign_loop.sh --smoke
```

Campaign state: `benchmarks/ml/results/jepa_campaign_state.json`

### Hypotheses

- **H1:** C4 > C1 in LOO macro-F1 at ≥25 % labels (C8) or +5 pp polyp recall
- **H2:** C4 > C3 (mask-aware SE under JEPA masking)
- **H3:** C4 ≥ C5 at 25 % labels (CNN-JEPA vs frozen teacher)
