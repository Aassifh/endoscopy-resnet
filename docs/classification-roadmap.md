# Classification roadmap — endoscopy-resnet

**Goal:** Unified frame-level **multi-class** classification benchmarks across every architecture in `models/registry.py`, on tasks that go beyond binary polyp detection and collapsed 3-class screening.

**Status:** 2026-07-02 — roadmap + dataset survey; first new task = HyperKvasir pathology (11 classes).

---

## 1. Current state (gap analysis)

The repo runs **two disconnected benchmark tracks**:

| Track | Tasks | Architectures | JEPA (C0–C10) | Results |
|-------|-------|---------------|---------------|---------|
| **B0–B6** | Kvasir 4-class, HyperKvasir **23-class** | ResNet-50, SE-ResNet-50, dual-stream | No | `benchmarks/ml/results/summary.md` |
| **C0–C10** | Colonoscopy **3-class** (collapsed) + LOO | SE-ResNet-50, ResNet-50 (+ JEPA variants) | Yes | `benchmarks/ml/results/jepa_summary.md` |

**Gaps:**

1. **No unified matrix** — C2–C5 / dual-stream / JEPA never run on HyperKvasir-23; B5–B6 never run on colonoscopy 3-class or pathology.
2. **Information loss** — `prepare_colonoscopy_3class.py` maps 23 HyperKvasir labels → 3 classes and **drops 11 pathology classes** (Barrett's, esophagitis, UC grades, resection margins).
3. **No histology** — polyp subtypes (tubular, serrated, adenocarcinoma…) require external datasets (ERCPMP, PIBAdb, VIM-Polyp).
4. **Detection-only data** — LDPolypVideo, Kvasir-Sessile are bbox/segmentation; need crop/extract scripts for classification.

**Baselines (Simula single fold, 3-class):**

| Run | Macro-F1 | Polyp recall |
|-----|----------|--------------|
| C1 ImageNet | 0.989 | 0.971 |
| C4 JEPA | 0.910 | 0.829 |

**Baselines (HyperKvasir 23-class, test):**

| Run | Macro-F1 | Accuracy |
|-----|----------|----------|
| B6 dual-stream ImageNet | **0.586** | 0.888 |
| B2 ResNet ImageNet | 0.585 | 0.879 |
| B4 SE-ResNet ImageNet | 0.577 | 0.882 |

Macro-F1 ≪ accuracy on 23-class confirms that **fine-grained tasks** are the right stress test for architectures and pretraining.

---

## 2. Task taxonomy

| Task ID | Name | Classes | Source | Center metadata | Primary clinical recall |
|---------|------|---------|--------|-----------------|-------------------------|
| **T0** | Kvasir v1 | 4 | Simula Kvasir | No | polyp, ulcer |
| **T1** | HyperKvasir full | 23 | Simula labeled images | No | polyps, rare pathologies |
| **T2** | HyperKvasir pathology | 11 | Subset of T1 (excluded from 3-class) | No | esophagitis, UC, Barrett's |
| **T3** | Colonoscopy screening | 3 | Kvasir + HyperKvasir + private | Yes (LOO) | polyp |
| **T4** | Polyp histology | 7–8 | ERCPMP-v5 (new) | Patient | adenocarcinoma, serrated |
| **T5** | Polyp histology (multi) | 5–6 | PIBAdb (new, access) | Polyp-level | SSA, TSA, invasive |
| **T6** | Kvasir extended | 8+ | Full Kvasir zip (new) | No | esophagitis, UC, Barrett's |

**Grouped HyperKvasir (T1) reporting** (per `protocol.md`):

- Landmarks: cecum, pylorus, z-line, ileum, retroflex-*
- Polyps / procedures: polyps, dyed-lifted-polyps, dyed-resection-margins
- Quality: bbps-*, hemorrhoids, impacted-stool
- Pathology: Barrett's, esophagitis, UC grades

---

## 3. Architecture × task matrix

Rows = `models/registry.py` entries; columns = tasks. Cell = benchmark run ID pattern.

| Architecture | Pretrain options | T0 Kvasir | T1 HK-23 | T2 HK-path | T3 3-class | T4 ERCPMP | T5 PIBAdb |
|--------------|------------------|-----------|----------|------------|------------|-----------|-----------|
| `resnet50` | scratch, ImageNet, CNN-JEPA | B0/B2 | B2, **H2** | **P2** | C2 | **E2** | **I2** |
| `seresnet50` | scratch, ImageNet | B3/B4 | B3/B4, **H3/H4** | **P3/P4** | C0/C1 | **E3/E4** | **I3/I4** |
| `seresnet50` + mask-aware SE | CNN-JEPA (C3–C5) | — | **H4m** | **P4m** | C4 | **E4m** | **I4m** |
| `dualstream_resnet_color_texture` | scratch, ImageNet RGB | — | B5/B6, **H5/H6** | **P5/P6** | **D4** | **E5/E6** | **I5/I6** |

**Legend:** Bold = not yet run. **H\*** = HyperKvasir JEPA extension; **P\*** = pathology task; **E\***/**I\*** = future external datasets.

**C6** (ViT linear probe) and **C7–C9** (label fractions) apply to T3 and optionally T2/T4 after core matrix is filled.

---

## 4. Dataset survey

Frame-level or easily convertible to ImageFolder classification. Sorted by **integration effort** (low → high).

| Dataset | Modality | #Classes / labels | Label type | License / access | Download size | Pipeline fit | Notes |
|---------|----------|-------------------|------------|------------------|---------------|--------------|-------|
| **HyperKvasir** (in repo) | WLI colon/GI stills | 23 anatomy + pathology + quality | Folder name | CC BY 4.0, Simula | ~1.1 GB zip | **Ready** — `pixi run prepare-hyperkvasir` | 10 662 images; pathology subset = T2 |
| **Kvasir v1** (in repo) | WLI stills | 4 (cecum, pylorus, polyp, ulcer) | Folder | CC BY 4.0 | ~50 MB | **Ready** — `prepare-kvasir` | Full Kvasir has 8+ classes (T6) |
| **ERCPMP-v5** | WLI colon stills + video | 7 pathology + morphology in filename | Filename + Excel | Mendeley Data (open) | ~430 images + videos (RAR) | **Good** — parse filenames → ImageFolder | Tubular, villous, hyperplastic, serrated, adenocarcinoma…; 368×256 JPG |
| **PIBAdb** | WLI/NBI stills + video | 6 histology (+ bbox) | CSV + bbox crop | Biobank **request** | ~31k images | **Medium** — crop + polyp-level split | Adenoma, hyperplastic, SSA, TSA, non-epithelial, invasive |
| **VIM-Polyp** | Video + histology WSIs | Video: polyp ID; patho: subtype | Multimodal IDs | Zenodo CC | 202 videos, 1903 WSIs | **Low for frames** — video extract + histology is separate modality | Best for cross-modal, not pure colonoscopy frames |
| **LDPolypVideo** | Video | Detection only (bbox) | Per-frame bbox | GitHub / MICCAI | 160 videos, 40k frames | **Low** — detection; needs crop script | No class labels beyond polyp presence |
| **Kvasir-Sessile** | WLI stills | 1 (sessile polyp) | Subset of Kvasir-SEG | CC BY 4.0 | ~14 MB | **Low** — 196 images, segmentation masks | Test-set for small polyp generalization, not multi-class |
| **Kvasir-SEG** | WLI stills | Polyp vs background | Segmentation mask | CC BY 4.0 | ~44 MB | **Low** — binary detection/seg | Crop polyp patches → weak single-class |

### Recommended integration order

1. **T2 HyperKvasir pathology** — zero new download; unlocks 11-class fine-grained GI pathology (this PR).
2. **T1 + JEPA (H-series)** — same `data/hyperkvasir/`; extend campaign shell to run C0–C4 + B5–B6 on 23 classes.
3. **T4 ERCPMP-v5** — first true **polyp histology** task; Mendeley download + filename parser.
4. **T5 PIBAdb** — richest histology taxonomy; requires access request + bbox crop pipeline.
5. **T6 Full Kvasir** — extend `download_and_prepare_kvasir.py` to all Simula classes.

---

## 5. Smallest integration (recommended)

### Phase A — HyperKvasir pathology (T2) ← **start here**

**Why:** Classes are already downloaded and labeled; they are explicitly excluded from the article 3-class task; 11 classes is genuinely multi-class and clinically distinct (esophagitis vs UC vs Barrett's).

**Prep:**

```bash
pixi run prepare-hyperkvasir          # if not done
pixi run prepare-hyperkvasir-pathology -- --output data/hyperkvasir_pathology
```

**Output layout:** `data/hyperkvasir_pathology/{train,val,test}/{class}/` (ImageFolder, seed 42, 70/15/15 stratified).

**Class inventory** (from local `data/hyperkvasir/class_counts.json`):

| Class | Total images | Note |
|-------|-------------|------|
| dyed-resection-margins | 989 | Largest; procedure-related |
| ulcerative-colitis-grade-2 | 443 | |
| esophagitis-a | 403 | |
| esophagitis-b-d | 260 | |
| ulcerative-colitis-grade-1 | 201 | |
| ulcerative-colitis-grade-3 | 133 | |
| barretts-short-segment | 53 | |
| barretts | 41 | |
| ulcerative-colitis-grade-0-1 | 35 | |
| ulcerative-colitis-grade-2-3 | 28 | |
| ulcerative-colitis-grade-1-2 | 11 | **Very small** — report per-class recall with caution |

**Benchmark:** `bash scripts/run_hyperkvasir_pathology_benchmarks.sh` — mirrors B2–B6 on `DATA_DIR=data/hyperkvasir_pathology`; results → `benchmarks/ml/results/hyperkvasir_pathology_*_test.json`.

**Metrics:** macro-F1 (primary); per-class recall for esophagitis-a, UC-grade-2, barretts; grouped macro-recall (Barrett's / esophagitis / UC / procedure).

### Phase B — Unified HyperKvasir-23 + JEPA (T1 H-series)

Extend `run_hyperkvasir_benchmarks.sh` with JEPA fine-tunes (C0–C4 pattern) on `data/hyperkvasir`. Reuse shared JEPA checkpoints from colonoscopy pretrain (`checkpoints/jepa/c4_mask_aware_shared.pt`). Adds **H0–H6** run IDs to the same results folder.

### Phase C — ERCPMP polyp histology (T4)

New script `scripts/download_and_prepare_ercpmp.py`:

- Download Mendeley `10.17632/7grhw5tv7n`
- Parse image filenames → pathology class folders
- Optional: morphology-only auxiliary task (Paris, JNET) as multi-label later

---

## 6. Unified campaign design (target)

Single queue file `benchmarks/ml/results/classification_campaign_state.json` with jobs:

```
{T}_{arch}_{pretrain}_{fold?}
```

Example queue slice:

1. `T2_B2_imagenet` … `T2_B6_imagenet` (pathology, existing archs)
2. `T1_H4_jepa` … (23-class JEPA)
3. `T3_C0_scratch_fold_simula` … (existing C-series, keep separate state file for article)
4. `T4_E4_imagenet` (after ERCPMP prep)

**Skip-if-done:** `{run_id}_test.json` exists (same pattern as `run_article_campaign_loop.sh`).

**Primary metric:** macro-F1 on val (checkpoint selection), test (reporting).  
**Clinical:** per-class recall for polyp/pathology classes listed per task.

---

## 7. Commands cheat sheet

```bash
# Data (My Machine)
pixi install
pixi run prepare-kvasir
pixi run prepare-hyperkvasir
pixi run prepare-hyperkvasir-pathology
pixi run prepare-colonoscopy-3class

# Benchmarks
bash scripts/run_hyperkvasir_benchmarks.sh              # T1 B2–B6 (done)
bash scripts/run_hyperkvasir_pathology_benchmarks.sh    # T2 B2–B6 (new)
bash scripts/run_article_campaign_loop.sh               # T3 C0–C10
# bash scripts/run_hyperkvasir_jepa_benchmarks.sh         # T1 H-series (planned)

# Summaries
python scripts/generate_paper_tables.py
```

---

## 8. Open questions

1. **UC grade merging** — collapse 6 UC grades → 3 tiers for stability, or keep fine-grained?
2. **Private centers** — extend T2/T4 with private pathology labels when available?
3. **JEPA pretrain pool** — domain JEPA on HyperKvasir video frames (`extract-video-frames`) vs labeled stills only?
4. **Polyp histology priority** — ERCPMP (open, smaller) vs PIBAdb (richer, gated access)?

---

## 9. Next steps (implementation order)

| Step | Deliverable | Effort |
|------|-------------|--------|
| 1 | This roadmap | Done |
| 2 | `prepare_hyperkvasir_pathology.py` + pixi task | Small |
| 3 | `run_hyperkvasir_pathology_benchmarks.sh` | Small |
| 4 | Run T2 B2–B6 on My Machine; update `summary.md` | GPU |
| 5 | `run_hyperkvasir_jepa_benchmarks.sh` (H-series) | Medium |
| 6 | `download_and_prepare_ercpmp.py` | Medium |
| 7 | Merge queues → unified classification campaign | Medium |
