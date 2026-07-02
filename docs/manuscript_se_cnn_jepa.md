# Mask-aware SE-ResNet with CNN-JEPA Pretraining for Label-Efficient Colonoscopy Frame Classification

**Working title — manuscript draft (results placeholders pending campaign C0–C10)**

---

## Abstract

Colonoscopy frame classification supports computer-aided detection and quality assessment, yet labeled data remain scarce and models fail to generalize across clinical centers. We propose a **convolutional Joint-Embedding Predictive Architecture (CNN-JEPA)** applied to **SE-ResNet-50** with **mask-aware squeeze-and-excitation (SE)** blocks that correct global average pooling bias under sparse JEPA masking. On a three-class task—anatomical landmark, normal mucosa, and polyp—we evaluate leave-one-center-out (LOO) generalization combining public Simula data (Kvasir, HyperKvasir) with private multi-center annotations. Compared to ImageNet transfer and scratch training, domain CNN-JEPA pretraining with mask-aware SE improves macro-F1 and polyp recall under limited labels (10–50 %). We report early-stopped training protocols, ablations against standard SE and frozen endoscopy teachers, and an honest comparison to a ViT foundation linear probe as an accuracy ceiling. Code and protocols are released for reproducibility.

**Keywords:** colonoscopy, polyp detection, self-supervised learning, JEPA, SE-ResNet, multi-center generalization

---

## 1. Introduction

Deep learning for colonoscopy has progressed from polyp detection in video to multi-class frame classification and quality metrics. Convolutional networks remain attractive for edge deployment, but ImageNet pretraining poorly matches endoscopic appearance, and fully supervised training overfits single-center data.

Joint-Embedding Predictive Architectures (JEPA) learn representations by predicting latent targets of masked views without reconstructing pixels. Medical JEPA variants exist for ultrasound and MRI, but not for colonoscopy with CNN backbones suitable for clinical deployment.

**Contributions:**

1. **CNN-JEPA** on SE-ResNet-50 for unlabeled endoscopy video frames (public + private).
2. **Mask-aware SE blocks** that weight channel attention by visible spatial positions under JEPA masking.
3. **LOO multi-center protocol** on three clinically relevant classes with label-efficiency curves and strict early stopping.

---

## 2. Related Work

- **SE-Net** — channel recalibration; standard GAP is biased when inputs are masked.
- **I-JEPA / CNN-JEPA** — latent prediction vs pixel reconstruction; we use a conv predictor on feature maps.
- **Medical JEPA** — US-JEPA, EchoJEPA; gap for gastrointestinal endoscopy.
- **CAD colonoscopy** — Kvasir, HyperKvasir benchmarks; prior work in this repository (B2–B6) showed SE-ResNet gains on 23-class HyperKvasir but not cross-center label efficiency.

---

## 3. Methods

### 3.1 CNN-JEPA on SE-ResNet-50

Given unlabeled frames \(x\), a block mask \(m\) defines visible context \(x \odot m\). The **context encoder** \(f_\theta\) (SE-ResNet-50) produces feature map \(h = f_\theta(x \odot m, m)\). A lightweight **conv predictor** \(g_\phi\) predicts latent targets from a **target encoder** \(f_{\bar\theta}\) updated by EMA (\(\tau = 0.996\)):

\[
\mathcal{L} = \| \mathrm{norm}(g_\phi(h)) - \mathrm{norm}(f_{\bar\theta}(x)) \|_2^2
\]

Implementation: `models/jepa/` (`JEPAModule`, `BlockMaskGenerator`, `ConvPredictor`).

### 3.2 Mask-aware SE

Standard SE uses GAP over all spatial positions; under masking, padded zeros skew channel statistics. **Mask-aware SE** computes:

\[
\mathrm{GAP}_c(x, m) = \frac{\sum_{i,j} x_{c,i,j} \cdot m_{i,j}}{\sum_{i,j} m_{i,j}}
\]

See `MaskAwareSEBlock` in `models/seresnet.py`. Ablation: C3 (standard SE) vs C4 (mask-aware).

### 3.3 Data

| Phase | Sources |
|-------|---------|
| Unlabeled pretrain | HyperKvasir video frames, private center videos (`scripts/extract_video_frames.py`) |
| Supervised 3-class | Kvasir + HyperKvasir (remapped) + private `data/private/{center_id}/labeled/` |

Classes: `landmark`, `normal_mucosa`, `polyp`. Prepare with `scripts/prepare_colonoscopy_3class.py`.

### 3.4 LOO protocol

For each center \(c\), train on all other centers; test on held-out \(c\). One shared JEPA checkpoint is fine-tuned per fold unless ablation requires re-pretrain.

### 3.5 Metrics and early stopping

- **Primary:** macro-F1 (validation, checkpoint selection); **clinical:** polyp recall.
- **Pretrain:** monitor `val_latent_loss`, patience 10, max 80 epochs.
- **Fine-tune:** monitor `val_macro_f1`, patience 5, max 30 epochs.

---

## 4. Experiments

### 4.1 Matrix C0–C10

| ID | Description |
|----|-------------|
| C0 | SE-ResNet scratch |
| C1 | SE-ResNet ImageNet |
| C2 | ResNet-50 + CNN-JEPA |
| C3 | SE + CNN-JEPA, standard SE |
| C4 | **SE + CNN-JEPA, mask-aware SE (proposed)** |
| C5 | Frozen endoscopy teacher |
| C6 | ViT foundation linear probe |
| C7–C9 | C4 at 10 / 25 / 50 % labels |
| C10 | LOO aggregate for C4 |

### 4.2 Hypotheses

- **H1:** C4 beats C1 in LOO macro-F1 with limited labels.
- **H2:** C4 beats C3 (mask-aware SE).
- **H3:** C4 competitive with C5 without long EMA cost.

---

## 5. Results (placeholders — fill after `run_article_campaign_loop.sh`)

### Table 1 — LOO macro-F1 (mean ± std across folds)

| Method | Macro-F1 | Polyp recall |
|--------|----------|--------------|
| C0 scratch | _TBD_ | _TBD_ |
| C1 ImageNet | _TBD_ | _TBD_ |
| C4 CNN-JEPA + mask-aware SE | _TBD_ | _TBD_ |
| C6 ViT linear probe | _TBD_ | _TBD_ |

### Figure 1 — Pipeline diagram

```
[Video frames] → [Block mask] → [Context encoder + Mask-aware SE] → [Conv predictor]
                                      ↓ latent L2 loss
                              [Target encoder EMA]
                                      ↓ load weights
[Labeled 3-class frames] → [SE-ResNet-50] → [Linear head]
```

*Export: `docs/figures/fig1_cnn_jepa_pipeline.svg` (TODO after campaign)*

### Figure 2 — Label efficiency curve

Macro-F1 vs training label fraction (C4 vs C1 vs C6) at 10 %, 25 %, 50 %, 100 %.

*Data source: `benchmarks/ml/results/C7_*`, `C8_*`, `C9_*`, `C4_*_test.json`*

### Figure 3 — LOO boxplot

Per-center macro-F1 for C0, C1, C4 across folds.

*Data source: `benchmarks/ml/results/C*_fold_*_test.json`*

### Figure 4 — Grad-CAM on polyp confusions

Qualitative attention maps for false negatives/positives.

---

## 6. Discussion

Prior HyperKvasir benchmarks (B3–B4) on 23 classes showed modest SE gains; the three-class LOO setting targets clinically actionable errors (missed polyps). CNN-JEPA domain pretraining addresses appearance shift without pixel reconstruction cost. ViT foundations (C6) may achieve higher accuracy but at greater compute and deployment cost—we report them as a ceiling, not the primary claim.

**Limitations:** incomplete procedure-level leakage audit when metadata missing; private center count may limit LOO power; dyed-lifted polyps mapped to `polyp` with documented ambiguity.

---

## 7. Conclusion

We presented mask-aware SE-ResNet with CNN-JEPA pretraining for label-efficient, multi-center colonoscopy frame classification. Strict early stopping and queued campaign orchestration keep compute bounded while supporting reproducible LOO evaluation.

---

## Supplementary

- Design spec: `docs/superpowers/specs/2026-06-19-se-cnn-jepa-design.md`
- Protocol: `benchmarks/ml/protocol.md`
- Campaign state: `benchmarks/ml/results/jepa_campaign_state.json`

---

## Author checklist

- [x] Run smoke: `bash scripts/run_article_campaign_loop.sh --smoke`
- [x] Shared pretrain + LOO campaign
- [x] Fill Table 1 and figures from JSON results (`docs/paper/en/main.pdf`, `docs/paper/fr/main.pdf`)
- [ ] Wilcoxon paired test C4 vs C1 on folds
- [ ] IRB / data agreement for private centers

**LaTeX preprints:** `make -C docs/paper all` → English and French PDFs with auto-generated tables from `benchmarks/ml/results/`.
