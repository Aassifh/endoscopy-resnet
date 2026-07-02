# ML Benchmark Results

**Run date:** 2026-06-13  
**Hardware:** Apple MPS (AMD Radeon Pro 5300M)  
**Primary dataset:** Kvasir v1 (real endoscopy images, Simula) — `data/kvasir/` via `scripts/download_and_prepare_kvasir.py`  
**Smoke-test dataset:** Synthetic Kvasir-proxy — `scripts/prepare_benchmark_data.py` (pipeline validation only)

## Kvasir v1 — Summary table (real data)

| Run ID | Checkpoint | Split | Accuracy | Macro-F1 | Weighted-F1 | Polyp recall | Ulcer recall |
|--------|------------|-------|----------|----------|-------------|--------------|--------------|
| B0-val | checkpoints/kvasir_baseline.pt | val | 0.737 | 0.724 | 0.724 | 0.493 | 0.587 |
| B0-test | checkpoints/kvasir_baseline.pt | test | 0.703 | 0.689 | 0.689 | 0.413 | 0.587 |
| B1-val | checkpoints/kvasir_optuna.pt | val | 0.793 | 0.789 | 0.789 | 0.587 | 0.760 |
| B1-test | checkpoints/kvasir_optuna.pt | test | 0.760 | 0.749 | 0.749 | 0.480 | 0.720 |

**Dataset:** 1 400 train / 300 val / 300 test images (350/75/75 per class). Stratified random split (seed 42).  
**Training:** B0 — 15 epochs, default hparams (AdamW, lr=1e-3, img=224). B1 — 8 Optuna trials × 8 epochs/trial; best trial 1 retrained **15 epochs** with tuned hparams (MPS-corrupted auto-export replaced by explicit retrain).

## Kvasir v1 — Optuna search (validation macro-F1 during HPO)

| Trial | Macro-F1 | Optimizer | Scheduler | img_size | Batch | Status |
|-------|----------|-----------|-----------|----------|-------|--------|
| 0 | 0.585 | SGD | cosine | 224 | 32 | complete |
| **1** | **0.724** | **AdamW** | **none** | **224** | **16** | **best (HPO phase)** |
| 2 | 0.250 | AdamW | step | 256 | 32 | complete |
| 3 | 0.250 | AdamW | cosine | 224 | 32 | pruned |
| 4 | 0.250 | SGD | none | 224 | 16 | pruned |
| 5 | 0.250 | AdamW | cosine | 256 | 32 | pruned |
| 6 | 0.250 | SGD | cosine | 256 | 8 | pruned |
| 7 | 0.250 | SGD | cosine | 256 | 16 | pruned |

Best HPO params (trial 1): `lr=3.997×10⁻⁴`, `weight_decay=3.94×10⁻⁵`, `batch_size=16`, `label_smoothing=0.095`, `img_size=224`, AdamW, no scheduler.

After 15-epoch retrain with best params: **val macro-F1 0.789**, **test macro-F1 0.749** (+6.0 pp vs B0 on test).

## Kvasir v1 — Test confusion matrices

**B0 baseline** (rows=true, cols=pred: cecum, polyp, pylorus, ulcer):

```
cecum   [64, 10,  0,  1]
polyp   [ 9, 31, 13, 22]
pylorus [ 0,  0, 72,  3]
ulcer   [11, 13,  7, 44]
```

**B1 Optuna** (15-epoch retrain):

```
cecum   [66,  8,  0,  1]
polyp   [12, 36,  7, 20]
pylorus [ 0,  0, 72,  3]
ulcer   [12,  4,  5, 54]
```

Main confusions: **polyp ↔ ulcer** (20 B1 errors each direction on test), **polyp → pylorus** (7).

## Key takeaways (real Kvasir)

1. **Realistic performance** — scratch ResNet-50 reaches ~70–76% accuracy; far from synthetic 100% saturation.
2. **Optuna helps** — B1 improves test macro-F1 by **+6.0 pp** (0.689 → 0.749) and ulcer recall by **+13 pp** (0.59 → 0.72); polyp recall +7 pp (0.41 → 0.48) but remains the weakest class.
3. **Pylorus easiest** — 96% test recall for both models; cecum ~85–88%.
4. **Clinical gap** — polyp recall ~48% on held-out test is insufficient for screening; focal loss, pretraining (B2), and patient-level splits are priorities.
5. **HPO discriminates** — SGD/cosine trials plateaued at 0.25 macro-F1 (MPS instability + bad configs); AdamW + moderate lr converged best.

JSON reports: `kvasir_baseline_val.json`, `kvasir_baseline_test.json`, `kvasir_optuna_val.json`, `kvasir_optuna_test.json`


## HyperKvasir (23 classes) — B2–B6

**Run date:** 2026-06-17  
**Dataset:** `data/hyperkvasir/` — 7 484 train / 1 589 val / 1 589 test (stratified, seed 42).  
**Training:** 15 epochs, batch 16, AdamW lr=1e-3 (scratch) or 1e-4 (ImageNet), img=224.  
**Selection:** checkpoint with best validation macro-F1.

| Run | Model | Pretrain | Split | Accuracy | Macro-F1 | Weighted-F1 |
|-----|-------|----------|-------|----------|----------|-------------|
| B2 | ResNet-50 | ImageNet | val | 0.896 | 0.591 | 0.890 |
| B2 | ResNet-50 | ImageNet | test | 0.879 | 0.585 | 0.874 |
| B3 | SE-ResNet-50 | none | val | 0.730 | 0.439 | 0.705 |
| B3 | SE-ResNet-50 | none | test | 0.725 | 0.439 | 0.700 |
| B4 | SE-ResNet-50 | ImageNet | val | 0.889 | 0.596 | 0.878 |
| B4 | SE-ResNet-50 | ImageNet | test | 0.882 | 0.577 | 0.870 |
| B5 | Dual-stream | none | val | 0.782 | 0.472 | 0.755 |
| B5 | Dual-stream | none | test | 0.755 | 0.448 | 0.726 |
| B6 | Dual-stream | ImageNet (RGB) | val | 0.901 | 0.596 | 0.894 |
| B6 | Dual-stream | ImageNet (RGB) | test | 0.888 | 0.586 | 0.881 |

### Key takeaways (HyperKvasir)

1. **Best test macro-F1:** B6 (Dual-stream, ImageNet (RGB)) — **0.586** (acc 0.888).
2. **Class imbalance** — accuracy can exceed macro-F1 substantially; macro-F1 remains the primary metric.
3. JSON reports: `hyperkvasir_b2_*` … `hyperkvasir_b6_*` in `benchmarks/ml/results/`.

---

## Appendix — Synthetic proxy (smoke test, 2026-06-11)

| Run ID | Split | Accuracy | Macro-F1 | Polyp recall | Ulcer recall |
|--------|-------|----------|----------|--------------|--------------|
| B0 | val/test | 1.000 | 1.000 | 1.000 | 1.000 |
| B1 | val/test | 1.000 | 1.000 | 1.000 | 1.000 |

320 procedural images (80/class). Perfect scores confirm pipeline correctness only — **not** clinical efficacy.

Legacy JSON: `baseline_val.json`, `baseline_test.json`, `optuna_val.json`, `optuna_test.json`
