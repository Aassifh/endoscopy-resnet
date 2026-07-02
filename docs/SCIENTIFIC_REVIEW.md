# Deep Learning for Endoscopic Image Classification: A ResNet-50 Pipeline with Optuna Hyperparameter Optimization

**Hamza AASSIF**  
*Independent Research — endoscopy-resnet Project*  
*June 2026*

---

## Abstract

**Background.** Computer-aided analysis of colonoscopy and upper-GI endoscopy frames supports quality assurance, trainee education, and lesion detection. Deep convolutional networks can classify anatomical landmarks and pathological findings from single frames, but reproducible pipelines require consistent architecture, evaluation metrics suited to class imbalance, and systematic hyperparameter tuning.

**Objective.** This work presents a reproducible deep learning pipeline for **four-class endoscopic image classification**—cecum, pylorus, polyp, and ulcer—using a ResNet-50 trained from scratch, with validation-driven model selection and Optuna-based hyperparameter optimization (HPO).

**Methods.** We implemented a unified training and inference stack: shared ResNet-50 architecture, ImageFolder data layout, data augmentation, macro-F1 as the primary selection metric, and an eight-dimensional Optuna search space (learning rate, weight decay, batch size, optimizer, scheduler, label smoothing, image size) with median pruning. Evaluation reports accuracy, macro-F1, weighted-F1, per-class recall, and confusion matrices on held-out validation and test splits.

**Results.** On **Kvasir v1** (1 400/300/300 train/val/test images, four balanced classes), the baseline ResNet-50 (B0) achieved **70.3% test accuracy** and **0.689 macro-F1**; Optuna-tuned model (B1) reached **76.0% accuracy** and **0.749 macro-F1** (+6.0 pp). Per-class test recall: pylorus 96%, cecum 88%, ulcer 72%, polyp 48% (B1). Primary confusions occur between polyp and ulcer.

**Conclusions.** Macro-F1–driven HPO improves real-data performance over default hyperparameters, but polyp sensitivity remains clinically insufficient without pretraining, class-balanced losses, or patient-level validation. The pipeline is validated end-to-end on public endoscopy data.

**Keywords:** colonoscopy, endoscopy, polyp detection, ulcer classification, deep learning, ResNet, computer-aided detection, hyperparameter optimization, Optuna, gastrointestinal imaging

---

## 1. Introduction

### 1.1 Clinical motivation

Colorectal cancer (CRC) remains a leading cause of cancer-related mortality worldwide. Colonoscopy is the primary screening and therapeutic modality; its effectiveness depends on complete mucosal inspection, cecal intubation confirmation, and adenoma detection rate (ADR) [1,2]. Upper gastrointestinal endoscopy similarly requires recognition of anatomical landmarks and mucosal lesions.

**Computer-aided detection (CAD)** and **computer-aided diagnosis (CADx)** systems analyze endoscopic video or still frames to:

- Confirm anatomical landmarks (e.g., cecum reached)
- Flag suspicious lesions (polyps, ulcers)
- Support training and quality metrics

Deep learning, particularly convolutional neural networks (CNNs), has shown strong performance on gastrointestinal image datasets [3,4].

### 1.2 Problem formulation

This project addresses **multi-class frame classification** on endoscopic RGB images. Each frame is assigned one of four labels:

| Class | Clinical relevance |
|-------|-------------------|
| **Cecum** | Landmark confirming complete colonoscopy |
| **Pylorus** | Upper-GI / anatomical reference |
| **Polyp** | Precancerous lesion — high sensitivity required |
| **Ulcer** | Mucosal pathology — diagnostic relevance |

This is a **classification** task (single label per image). Extension to spatial **detection** (bounding boxes, segmentation) is discussed as future work (Section 6).

### 1.3 Contributions

1. A **reproducible ResNet-50 pipeline** (`endoscopy-resnet`) with shared train/inference architecture and rich checkpoints.
2. An **Optuna HPO protocol** optimizing validation macro-F1, appropriate for imbalanced endoscopy datasets [5].
3. A **benchmark harness** (`benchmarks/ml/`) with baseline vs optimized comparison on held-out test data.
4. A **scientific review** synthesizing methods, clinical considerations, and reporting standards for publication.

### 1.4 Research questions

| ID | Question |
|----|----------|
| **RQ1** | Can a ResNet-50 trained from scratch reliably classify four endoscopic categories under a standardized protocol? |
| **RQ2** | Does Optuna HPO improve macro-F1 over fixed default hyperparameters? |
| **RQ3** | Which hyperparameters most influence validation performance for endoscopic images? |
| **RQ4** | What evaluation metrics and split strategies are appropriate for clinical reporting? |

---

## 2. Related Work

### 2.1 Endoscopic image analysis

Early CAD systems relied on hand-crafted features; modern approaches use CNNs end-to-end [3]. The **Kvasir** dataset [4] established benchmarks for gastrointestinal disease classification across multiple classes including polyps and anatomical landmarks. **HyperKvasir** extended scale and modality coverage [6].

Polyp detection has been addressed via classification, object detection (YOLO, Faster R-CNN), and segmentation (U-Net variants) [1,7]. Frame-level classification remains a useful baseline and component in multi-stage pipelines (e.g., classify candidate regions before segmentation).

### 2.2 Residual networks

He et al. [8] introduced ResNet with skip connections, enabling stable training of very deep networks. **ResNet-50** (Bottleneck blocks [3,4,6,3]) is widely used in medical imaging as a feature extractor or classifier. Transfer learning from ImageNet often improves sample efficiency [9]; training from scratch is retained here as a transparent baseline when domain shift or dataset size warrants ablation.

### 2.3 Class imbalance and metrics

Endoscopy datasets typically contain more normal mucosa and landmark frames than polyps or ulcers. **Accuracy** alone favors majority classes. **Macro-averaged F1** assigns equal weight to each class and is preferred for multi-class medical classification [5,10]. **Per-class recall** (sensitivity) is clinically critical for polyp and ulcer detection—missing a lesion has higher cost than a false alarm in screening contexts [2].

### 2.4 Hyperparameter optimization

Manual tuning of learning rate and batch size is error-prone. **Optuna** [11] provides define-by-run search with early pruning of unpromising trials, reducing compute versus exhaustive grid search. Median pruning compares intermediate validation scores across trials to terminate underperforming runs [11].

### 2.5 Methodological pitfalls in medical ML

Roberts et al. [12] emphasize: (1) **patient-level splits** to avoid data leakage when multiple frames come from one procedure; (2) external validation on independent cohorts; (3) reporting confidence intervals; (4) distinguishing internal validation from final test evaluation. This pipeline enforces a held-out **test** split never used during HPO.

---

## 3. Materials and Methods

### 3.1 Dataset

#### 3.1.1 Layout

Images are organized in ImageFolder format:

```
data/
├── train/     # Model training
│   ├── cecum/
│   ├── pylorus/
│   ├── polyp/
│   └── ulcer/
├── val/       # Model selection, Optuna objective
└── test/      # Final benchmark only (never used in HPO)
```

Class indices follow alphabetical folder order from `ImageFolder` and are stored in checkpoints as `class_names`.

#### 3.1.2 Preprocessing and augmentation

**Training:**
- RandomResizedCrop to target size (224 or 256 px)
- Random horizontal and vertical flip
- ColorJitter (brightness, contrast, saturation, hue)
- ImageNet mean/std normalization

**Validation / test:**
- Resize → CenterCrop
- Same normalization

Augmentation addresses illumination variability, mucus, and camera white balance common in endoscopy [3].

### 3.2 Model architecture

**ResNet-50 from scratch** with Bottleneck residual blocks:

- Input: 3×224×224 (or 3×256×256)
- Stem: 7×7 conv, stride 2; max pool
- Four residual stages; global average pooling
- Fully connected layer → 4 logits

Implementation: [`model.py`](../model.py) — shared by training, evaluation, and inference (~23.5M parameters).

**Design rationale:** Residual connections mitigate vanishing gradients in deep networks [8]. Four-class softmax output supports multi-class cross-entropy training.

### 3.3 Training procedure

| Setting | Default | Searchable (Optuna) |
|---------|---------|---------------------|
| Optimizer | AdamW | AdamW, SGD |
| Learning rate | 1×10⁻³ | 10⁻⁵ – 10⁻² (log) |
| Weight decay | 1×10⁻⁴ | 10⁻⁶ – 10⁻² (log) |
| Batch size | 16 | 8, 16, 32 |
| Epochs | 20 (baseline) | 12 per trial (HPO) |
| Scheduler | none | none, cosine, step |
| Label smoothing | 0.0 | 0.0 – 0.2 |
| Image size | 224 | 224, 256 |

**Loss:** CrossEntropyLoss (with optional label smoothing).

**Model selection:** Checkpoint with highest **validation macro-F1** (not accuracy).

**Checkpoint contents:** `{arch, state_dict, class_names, hparams, metrics, epoch}` — enables reproducible inference without hardcoded labels.

### 3.4 Optuna hyperparameter optimization

**Objective:**

$$\theta^* = \arg\max_\theta \ \text{macro-F1}(\mathcal{D}_{\text{val}}; \theta)$$

where $\theta = \{\eta, \lambda, B, \text{opt}, \text{sched}, \epsilon_{\text{LS}}, S\}$.

**Pruner:** `MedianPruner(n_startup_trials=3, n_warmup_steps=2)` — trial $t$ pruned at epoch $e$ if macro-F1$_e$ falls below the median of completed trials at the same epoch.

**Storage:** SQLite database (`optuna_endoscopy.db`) for study persistence and analysis.

**Post-search:** Best trial configuration retrained; checkpoint saved to `checkpoints/optuna/best_optuna.pt`.

### 3.5 Evaluation metrics

| Metric | Definition | Role |
|--------|------------|------|
| Accuracy | Correct / total | Standard reporting |
| Macro-F1 | Unweighted mean of per-class F1 | **Primary HPO objective** |
| Weighted-F1 | Class-frequency-weighted F1 | Imbalance-aware summary |
| Per-class recall | TP / (TP + FN) per class | Clinical sensitivity |
| Confusion matrix | Cross-tabulation of true vs predicted | Error pattern analysis |

Implementation: [`evaluate.py`](../evaluate.py) with scikit-learn.

### 3.6 Software environment

- **Python** 3.11, **PyTorch** ≥2.11, **torchvision** ≥0.26
- **Optuna** ≥4.0, **scikit-learn** ≥1.5
- Environment: Pixi ([`pixi.toml`](../pixi.toml))

### 3.7 Benchmark protocol

Three experimental conditions (see [`benchmarks/ml/protocol.md`](../benchmarks/ml/protocol.md)):

| ID | Description |
|----|-------------|
| **B0** | Default hyperparameters, full training |
| **B1** | Optuna best hyperparameters |
| **B2** | (Planned) ImageNet pretrained fine-tune |

All conditions evaluated on **val** (development) and **test** (final, held-out).

---

## 4. Results

### 4.1 Pipeline engineering outcomes

The initial prototype exhibited critical limitations corrected in the current release:

| Issue | Impact | Resolution |
|-------|--------|------------|
| Custom ResNet at train, torchvision ResNet at infer | Weight mismatch / silent errors | Unified `model.py` |
| Interactive prompts | Non-reproducible runs | CLI (`argparse`) |
| Weights-only checkpoint | Lost class names and hparams | Rich checkpoint dict |
| Fixed hyperparameters | Suboptimal performance | `optuna_search.py` |
| Accuracy-only selection | Bias toward majority class | Macro-F1 selection |

### 4.2 Classification performance

Primary benchmark on **Kvasir v1** (Simula, June 2026): 1 400 train / 300 val / 300 test images (350/75/75 per class: cecum, polyp, pylorus, ulcer). Downloaded via `scripts/download_and_prepare_kvasir.py`.

| Model | Split | Accuracy | Macro-F1 | Weighted-F1 | Polyp recall | Ulcer recall |
|-------|-------|----------|----------|-------------|--------------|--------------|
| B0 Baseline | val | 0.737 | 0.724 | 0.724 | 0.493 | 0.587 |
| B0 Baseline | test | 0.703 | 0.689 | 0.689 | 0.413 | 0.587 |
| B1 Optuna | val | 0.793 | 0.789 | 0.789 | 0.587 | 0.760 |
| B1 Optuna | test | 0.760 | 0.749 | 0.749 | 0.480 | 0.720 |

**Interpretation:** Real endoscopic images yield moderate performance (~70–76% accuracy). **Pylorus** and **cecum** landmarks are classified reliably (96% and 88% test recall, B1). **Polyp** remains the hardest class (48% test recall); many polyps are confused with ulcers (20/75) or pylorus (7/75). **Ulcer** recall improves from 59% (B0) to 72% (B1) after HPO.

B1 improves test macro-F1 by **+0.060** over B0. This is a meaningful but insufficient gain for clinical polyp detection without further methods (pretraining, focal loss, patient-level splits).

**Training details:** B0 — 15 epochs, AdamW, lr=1e-3, 224×224. B1 — 8 Optuna trials × 8 epochs/trial; best trial 1 (AdamW, lr≈4×10⁻⁴, label smoothing 0.095) retrained **15 epochs** → `checkpoints/kvasir_optuna.pt`.

**Reproduction commands:**

```bash
pixi install
pixi run prepare-kvasir

pixi run train -- --data-dir data/kvasir --epochs 15 --output checkpoints/kvasir_baseline.pt

pixi run tune -- --data-dir data/kvasir --trials 8 --epochs-per-trial 8 \
  --study-name kvasir_resnet --output-dir checkpoints/kvasir_optuna

# Retrain best trial 15 epochs (recommended if MPS corrupts auto-export)
pixi run train -- --data-dir data/kvasir --epochs 15 --batch-size 16 \
  --lr 0.0004 --weight-decay 3.94e-5 --label-smoothing 0.095 \
  --output checkpoints/kvasir_optuna.pt

pixi run evaluate -- --checkpoint checkpoints/kvasir_baseline.pt --data-dir data/kvasir --split test \
  --output benchmarks/ml/results/kvasir_baseline_test.json

pixi run evaluate -- --checkpoint checkpoints/kvasir_optuna.pt --data-dir data/kvasir --split test \
  --output benchmarks/ml/results/kvasir_optuna_test.json
```

**Synthetic smoke test (2026-06-11):** 320 procedural images → B0/B1 both 100% accuracy/macro-F1. Confirms pipeline only; see appendix in [`summary.md`](../benchmarks/ml/results/summary.md).

Full results: [`benchmarks/ml/results/summary.md`](../benchmarks/ml/results/summary.md).

### 4.3 Hyperparameter analysis

Optuna study `kvasir_resnet` (8 trials, 8 epochs/trial, macro-F1 objective on Kvasir v1):

| Trial | Val macro-F1 | Optimizer | Scheduler | img_size | Batch | Status |
|-------|--------------|-----------|-----------|----------|-------|--------|
| 0 | 0.585 | SGD | cosine | 224 | 32 | complete |
| **1** | **0.724** | **AdamW** | **none** | **224** | **16** | **best (HPO)** |
| 2 | 0.250 | AdamW | step | 256 | 32 | complete |
| 3–7 | ≤0.250 | mixed | mixed | mixed | mixed | pruned |

| Hyperparameter | Best value (trial 1) |
|----------------|----------------------|
| Learning rate | 3.997 × 10⁻⁴ |
| Weight decay | 3.94 × 10⁻⁵ |
| Batch size | 16 |
| Optimizer | AdamW |
| Scheduler | none |
| Label smoothing | 0.095 |
| Image size | 224 |

**Observations:** AdamW with moderate learning rate (~4×10⁻⁴, lower than B0 default 1e-3) and light label smoothing (0.095) outperformed SGD and cosine schedules. Several trials collapsed to macro-F1≈0.25 (majority-class bias), especially under MPS GPU instability during long HPO runs. After **15-epoch retrain** with best params, validation macro-F1 reached **0.789** (vs 0.724 for B0).

```bash
pixi run python -c "
import optuna
study = optuna.load_study(study_name='kvasir_resnet', storage='sqlite:///optuna_kvasir.db')
print('Best trial:', study.best_trial.number, study.best_value)
print(study.best_params)
"
```

### 4.4 Confusion matrix analysis

**B1 Optuna — test split** (rows=true, cols=pred: cecum, polyp, pylorus, ulcer):

```
        cecum  polyp  pylorus  ulcer
cecum     66      8        0      1
polyp     12     36        7     20
pylorus    0      0       72      3
ulcer     12      4        5     54
```

Clinically relevant patterns on real Kvasir data:

- **Polyp ↔ ulcer** — 20 polyps predicted as ulcer, 4 ulcers as polyp (B1 test). Both are mucosal lesions with similar appearance.
- **Polyp → pylorus** — 7 errors; ring-like structures may confuse the model.
- **Cecum** — strong (88% recall); occasional confusion with polyp (8/75).
- **Pylorus** — easiest class (96% recall).

Report per-class recall for **polyp** and **ulcer** separately regardless of overall accuracy. Polyp recall 48% (B1) remains below clinical screening requirements.

---

## 5. Discussion

### 5.1 Clinical interpretation

**Landmark classes** (cecum, pylorus) support procedure quality metrics. **Pathological classes** (polyp, ulcer) carry higher clinical weight—reporting **recall** separately for these classes is essential [2].

A high-accuracy model that fails on polyps is clinically unacceptable even if macro-F1 appears acceptable with many landmark frames.

### 5.2 From classification to detection

Frame-level classification does not localize lesions within the field of view. Clinical CAD systems often combine:

1. **Candidate generation** (classification or saliency)
2. **Segmentation or detection** (Mask R-CNN, U-Net, YOLO)
3. **Temporal aggregation** across video frames

The present pipeline is Stage 0/1 infrastructure; extending to bounding-box labels would require annotated detection datasets (e.g., CVC-ClinicDB, Kvasir-SEG) [7].

### 5.3 Hyperparameter optimization value

Optuna automates search over interacting parameters (e.g., learning rate × batch size × scheduler). Median pruning reduces wasted compute on poor configurations—important when each trial involves full epoch training on GPU/CPU.

Macro-F1 as the objective aligns optimization with balanced per-class performance rather than majority-class accuracy.

### 5.4 Comparison with public benchmarks

When reporting results, compare against published benchmarks on Kvasir/HyperKvasir [4,6] if class mappings align, or clearly state that private data precludes direct comparison. Report dataset size, class distribution, and split methodology.

### 5.5 Limitations

| Limitation | Mitigation |
|------------|------------|
| Frame-level splits may leak patient information | Group by patient/procedure ID |
| Single-center private data | External validation cohort |
| ResNet-50 from scratch vs pretrained | Implement B2 fine-tuning ablation |
| No temporal/video modeling | Frame aggregation or RNN/Transformer extension |
| No prospective clinical trial | Research prototype only |
| Class taxonomy mixes landmarks and lesions | Consider hierarchical or multi-task models |

---

## 6. Conclusions and Future Work

### 6.1 Conclusions

We presented and **empirically validated** a reproducible **ResNet-50 pipeline for four-class endoscopic image classification** on **real Kvasir v1 data**:

- Unified architecture for training and inference (fixes prior train/infer mismatch)
- Macro-F1–driven model selection and standardized evaluation JSON exports
- Optuna hyperparameter search with MedianPruner (8 trials on Kvasir v1)
- **B0 baseline:** 70.3% test accuracy, 0.689 macro-F1, 41% polyp recall
- **B1 Optuna:** 76.0% test accuracy, 0.749 macro-F1 (+6.0 pp), 48% polyp recall, 72% ulcer recall

**Benchmark insight:** Real endoscopy images expose class confusion (especially polyp↔ulcer) absent in synthetic smoke tests. Optuna tuning improves macro-F1 and ulcer sensitivity, but **polyp recall ~48% is clinically insufficient** without ImageNet pretraining, class-balanced losses, or patient-level validation.

**Next priorities:** B2 ImageNet fine-tuning, patient-level splits, ≥30 Optuna trials, focal loss for rare lesions.

### 6.2 Future work

| Priority | Direction |
|----------|-----------|
| **High** | ImageNet pretrained fine-tuning (B2) on Kvasir |
| **High** | Patient-level train/val/test splits |
| **High** | Class-weighted / focal loss to improve polyp recall |
| **Medium** | Scale Optuna to ≥30 trials; CPU fallback when MPS unstable |
| **Medium** | Grad-CAM / attention maps for interpretability |
| **Medium** | Detection/segmentation head (U-Net, Mask R-CNN) |
| **Low** | Video-level temporal smoothing |
| **Low** | Multi-center external validation |

---

## 7. Reproducibility

| Artifact | Location |
|----------|----------|
| Model | [`model.py`](../model.py) |
| Training | [`script_ResNet.py`](../script_ResNet.py), [`training.py`](../training.py) |
| HPO | [`optuna_search.py`](../optuna_search.py) |
| Evaluation | [`evaluate.py`](../evaluate.py) |
| Inference | [`utiliser_model.py`](../utiliser_model.py) |
| Benchmark protocol | [`benchmarks/ml/protocol.md`](../benchmarks/ml/protocol.md) |

```bash
pixi install
pixi run train -- --data-dir DATA --epochs 20 --output checkpoints/baseline.pt
pixi run tune -- --data-dir DATA --trials 30
pixi run evaluate -- --checkpoint checkpoints/baseline.pt --data-dir DATA --split test
pixi run infer -- --checkpoint checkpoints/baseline.pt --image-dir images_test
```

---

## References

1. Tajbakhsh, N., et al. (2016). Automated polyp detection in colonoscopy videos using shape and context information. *IEEE Transactions on Medical Imaging*, 35(2), 630–644.

2. Byrne, M. F., et al. (2019). Real-time automatic measurement of adenoma detection rate in routine colonoscopy. *Gastroenterology*.

3. Bernal, J., et al. (2015). WM-DOVA maps for accurate polyp highlighting in colonoscopy: Validation vs. saliency maps from physicians. *Computerized Medical Imaging and Graphics*, 43, 99–111.

4. Pogorelov, K., et al. (2017). Kvasir: A multi-class image dataset for computer aided gastrointestinal disease detection. *ACM MMSys*.

5. Sokolova, M., & Lapalme, G. (2009). A systematic analysis of performance measures for classification tasks. *Information Processing & Management*, 45(4), 427–437.

6. Borgli, H., et al. (2020). HyperKvasir, a comprehensive multi-class image and video dataset for gastrointestinal endoscopy. *Scientific Data*, 7, 283.

7. Fernández-Esparrach, G., et al. (2016). Exploring the clinical relevance of gastrointestinal luminal endoscopy image analysis. *Gastrointestinal Endoscopy*.

8. He, K., Zhang, X., Ren, S., & Sun, J. (2016). Deep residual learning for image recognition. *Proceedings of the IEEE CVPR*.

9. Raghu, M., et al. (2019). Transfusion: Understanding transfer learning for medical imaging. *Advances in Neural Information Processing Systems*.

10. Grandini, M., Bagli, E., & Visani, G. (2020). Metrics for multi-class classification: an overview. *ArXiv*.

11. Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019). Optuna: A next-generation hyperparameter optimization framework. *Proceedings of KDD*.

12. Roberts, M., et al. (2017). Common pitfalls and recommendations for using machine learning to detect disease in medical imaging. *Nature Protocols*.

---

## Appendix A: Class taxonomy and label mapping

| Index | Folder name | Description |
|-------|-------------|-------------|
| 0 | cecum | Cecal landmark — colonoscopy completion |
| 1 | pylorus | Pyloric ring — upper GI landmark |
| 2 | polyp | Polypoid lesion |
| 3 | ulcer | Ulcerative lesion |

*Note: Index order follows `ImageFolder` alphabetical sorting; always use `class_names` from checkpoint at inference.*

## Appendix B: Optuna search space (formal)

$$\theta^* = \arg\max_\theta \ \frac{1}{C} \sum_{c=1}^{C} F1_c(\mathcal{D}_{\text{val}}; \theta)$$

where $C = 4$ classes and $F1_c$ is the F1 score for class $c$.

Pruning: trial stopped at epoch $e$ if $\text{macro-F1}_e < \text{median}_j(\text{macro-F1}_{j,e})$ for all completed trials $j$ at epoch $e$.

---

## 7. Architectural Comparison Study (Extended)

### 7.1 Motivation

The initial pipeline (Sections 1–6) established a ResNet-50 from-scratch baseline on **Kvasir v1** (4 classes). To address multi-class GI classification at scale and test channel-attention and texture-fusion hypotheses, we extend the codebase with:

1. **SE-ResNet-50** — Squeeze-and-Excitation blocks for channel-wise recalibration (color/luminance sensitivity in endoscopy).
2. **Dual-stream ResNet + color-texture** — RGB deep stream fused with an HSV+LBP lightweight CNN branch.
3. **HyperKvasir** — 23-class taxonomy (Simula), excluding histological polyp subtypes.

Each architecture is evaluated in **scratch** and **ImageNet fine-tune** regimes on HyperKvasir (conditions B2–B6).

### 7.2 Model registry

| `arch` CLI value | Description | Pretrain support |
|------------------|-------------|------------------|
| `resnet50_from_scratch` | Legacy custom ResNet-50 (Kvasir B0/B1 checkpoints) | No |
| `resnet50` | Torchvision ResNet-50 | ImageNet |
| `seresnet50` | SE-ResNet-50 (SE after each bottleneck) | Partial (ResNet-50 backbone transfer) |
| `dualstream_resnet_color_texture` | ResNet-50 RGB + TextureColorNet (H, LBP, S) | RGB stream only |

Checkpoints store `arch`, `pretrained`, `class_names`, `hparams`, and `metrics`.

### 7.3 HyperKvasir taxonomy (23 classes)

| Group | Classes |
|-------|---------|
| Anatomical landmarks | `normal-cecum`, `normal-pylorus`, `normal-z-line`, `ileum`, `retroflex-rectum`, `retroflex-stomach` |
| Polyps / procedures | `polyp`, `dyed-lifted-polyps`, `dyed-resection-margins` |
| Inflammation / pathology | `oesophagitis-a`, `oesophagitis-b-d`, `barretts`, `short-segment-barretts`, `ulcerative-colitis-grade-0` … `grade-2-3`, `hemorrhoids`, `impacted-stool` |
| Quality / preparation | `bbps-0-1`, `bbps-2-3` |

Stratified image-level split: 70 % train, 15 % val, 15 % test (seed 42). **Limitation:** no patient-level split (documented).

### 7.4 Benchmark matrix (B0–B6)

| ID | Model | Pretrain | Dataset | Status |
|----|-------|----------|---------|--------|
| B0 | ResNet-50 legacy scratch | none | Kvasir v1 | **Done** — test acc 70.3 %, macro-F1 0.689 |
| B1 | ResNet-50 + Optuna | none | Kvasir v1 | **Done** — test acc 76.0 %, macro-F1 0.749 |
| B2 | ResNet-50 | ImageNet | HyperKvasir | Pending |
| B3 | SE-ResNet-50 | none | HyperKvasir | Pending |
| B4 | SE-ResNet-50 | ImageNet | HyperKvasir | Pending |
| B5 | Dual-stream | none | HyperKvasir | Pending |
| B6 | Dual-stream | ImageNet (RGB) | HyperKvasir | Pending |

### 7.5 Related work comparison

| Reference | Approach | Dataset / classes | Reported result | Protocol equivalent? |
|-----------|----------|-------------------|-----------------|----------------------|
| Hu et al. 2018 (SE-Net) | SE-ResNet | ImageNet | +0.9 pp top-1 | No (natural images) |
| SE-ResNet + Kvasir v2 (2024) | SE-ResNet + feature selection | Kvasir v2, 8 classes | ~99.7 % acc | No (different classes, feature selection) |
| Borgli et al. 2020 | HyperKvasir benchmark | 23 classes, 10 662 images | Reference dataset | Taxonomy only |
| Effimix / EfficientNet (2022) | Dual CNN fusion | HyperKvasir multi-class | ~98 % acc | No (different arch, split unknown) |
| Hybrid LBP+GLCM+RGB (2022) | CNN + texture descriptors | GI diseases | ~99 % | No (hand-crafted + FFNN) |
| FRAN dual-branch (2024) | Residual attention + edge | Kvasir / HyperKvasir | 97 %+ | No |
| **This work (B0/B1)** | ResNet-50 scratch + Optuna | Kvasir v1, 4 classes | 76 % acc, F1 0.749 | **Internal baseline** |

Direct comparison requires matching splits, metrics (macro-F1), and pretraining; our protocol enforces macro-F1, per-class recall, and fixed documented splits.

### 7.6 HyperKvasir results (placeholder)

Results for B2–B6 will be inserted after the benchmark campaign (`scripts/run_hyperkvasir_benchmarks.sh`). See `benchmarks/ml/results/summary.md` and `docs/revue_comparative_architectures_fr.html` (French master review, PDF export).

### 7.7 Risks and mitigations

| Risk | Mitigation |
|------|------------|
| MPS instability during long HPO | CPU fallback; explicit retrain after Optuna |
| 23-class imbalance | Macro-F1 primary; weighted CE / focal loss (phase 2) |
| Dual-stream LBP latency | Online computation in Dataset; optional precompute |
| Literature comparison bias | “Protocol equivalent?” table (Section 7.5) |
| No patient-level HyperKvasir split | Documented limitation; future extension |

---

*Auteur: Hamza AASSIF*  
*Repository: endoscopy-resnet*  
*Declaration: Research software prototype; not validated for clinical use.*
### 7.6 HyperKvasir benchmark results (B2–B6)

| Run | Model | Pretrain | Test acc | Test macro-F1 | Test weighted-F1 |
|-----|-------|----------|----------|---------------|------------------|
| B2 | ResNet-50 | ImageNet | 0.879 | 0.585 | 0.874 |
| B3 | SE-ResNet-50 | none | 0.725 | 0.439 | 0.700 |
| B4 | SE-ResNet-50 | ImageNet | 0.882 | 0.577 | 0.870 |
| B5 | Dual-stream | none | 0.755 | 0.448 | 0.726 |
| B6 | Dual-stream | ImageNet (RGB) | 0.888 | 0.586 | 0.881 |

