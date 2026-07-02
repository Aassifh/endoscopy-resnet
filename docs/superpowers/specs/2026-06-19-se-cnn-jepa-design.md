# Design: SE-ResNet-50 + CNN-JEPA for Colonoscopy (Article C0–C10)

**Date:** 2026-06-19  
**Status:** Approved for implementation  
**Repo:** `endoscopy-resnet`

## Scientific objective

**Central question (H1):** Does domain **CNN-JEPA** pretraining on mask-aware SE-ResNet-50 improve **inter-center generalization** and **label efficiency** for 3-class colonoscopy frame classification vs ImageNet and scratch?

| ID | Hypothesis | Comparison | Metric |
|----|------------|------------|--------|
| H1 | Domain CNN-JEPA (C4) beats ImageNet (C1) under low labels | C4 vs C1, C7–C9 | macro-F1 LOO + polyp recall |
| H2 | Mask-aware SE (C4) beats standard SE under JEPA masking (C3) | C4 vs C3 | latent val loss + fine-tune macro-F1 |
| H3 | CNN-JEPA adds value beyond frozen endoscopy teacher (C5) | C4 vs C5 | macro-F1 @ 25% labels |

C6 (ViT foundation) is a **reference ceiling** for discussion, not the primary claim.

## Task: 3-class fine-tune

| Class | Definition |
|-------|------------|
| `landmark` | Anatomical landmarks (cecum, pylorus, z-line, ileum, retroflexions) |
| `normal_mucosa` | Non-lesion mucosa / prep quality frames (BBPS) |
| `polyp` | Polyps and dyed-lifted polyps |

**Primary metrics:** macro-F1, polyp recall. **Protocol:** leave-one-center-out (public Simula + private centers).

## Architecture

- **Not** ViT I-JEPA (patch masking + ViT).
- **CNN-JEPA:** block masking + SE-ResNet-50 context encoder + conv predictor + EMA target encoder.
- **Mask-aware SE:** channel recalibration uses GAP over **visible positions only** when a spatial mask is provided.

## Early stopping (compute budget)

| Phase | Metric | max_epochs | patience | min_epochs |
|-------|--------|------------|----------|------------|
| CNN-JEPA pretrain | val latent loss ↓ | 80 | 10 | 20 |
| Fine-tune | val macro-F1 ↑ | 30 | 5 | 5 |
| Linear probe | val macro-F1 ↑ | 15 | 3 | 3 |

Always restore best checkpoint. Skip run if final JSON exists.

## Benchmark matrix (C0–C10)

| ID | Method | Pretrain |
|----|--------|----------|
| C0 | SE-ResNet-50 scratch | none |
| C1 | SE-ResNet-50 | ImageNet |
| C2 | ResNet-50 | CNN-JEPA |
| C3 | SE-ResNet-50 | CNN-JEPA + SE standard |
| C4 | SE-ResNet-50 | CNN-JEPA + SE mask-aware |
| C5 | SE-ResNet-50 | frozen endoscopy teacher |
| C6 | ViT foundation | frozen linear probe |
| C7–C9 | C4 | label fractions 10/25/50% |
| C10 | C4 | LOO held-out center |

## Artifacts

- `data/colonoscopy_3class/` — ImageFolder + `centers.json`
- `data/unlabeled_frames/` — JEPA pretrain pool
- `checkpoints/jepa/` — shared pretrain + per-run fine-tune
- `benchmarks/ml/results/jepa_*.json` — evaluation reports
- `benchmarks/ml/results/jepa_campaign_state.json` — loop queue

## Manuscript

Draft: `docs/manuscript_se_cnn_jepa.md` — outline aligned with Frontiers/IEEE JBHI structure.

**LaTeX preprints (EN + FR):** compile with `make -C docs/paper all` → `docs/paper/en/main.pdf`, `docs/paper/fr/main.pdf`.
