# AGENTS.md — context for Cursor Cloud Agents (desktop + iOS)

This file helps Cursor agents work on **endoscopy-resnet** from any device, including the **Cursor iOS app**.

## Project

Colonoscopy frame classification: ResNet / SE-ResNet-50, **CNN-JEPA** self-supervised pretraining, supervised **3-class** fine-tune (`landmark`, `normal_mucosa`, `polyp`).

## Repo layout

| Path | Purpose |
|------|---------|
| `models/jepa/` | CNN-JEPA (encoder, masking, predictor, loss) |
| `models/seresnet.py` | SE-ResNet-50 + **MaskAwareSEBlock** |
| `scripts/prepare_colonoscopy_3class.py` | 3-class dataset + LOO folds |
| `scripts/pretrain_cnn_jepa.py` | Phase-1 JEPA pretrain |
| `scripts/run_article_campaign_loop.sh` | One benchmark job per invocation (C0–C10) |
| `scripts/run_full_jepa_benchmarks.sh` | Full campaign loop |
| `benchmarks/ml/results/` | JSON test metrics (`C*_fold_simula_test.json`) |
| `docs/paper/en/` / `docs/paper/fr/` | LaTeX arXiv manuscripts |
| `benchmarks/ml/protocol.md` | C0–C10 protocol |

## Commands (Mac, via pixi)

```bash
pixi install
pixi run prepare-colonoscopy-3class
pixi run run-jepa-campaign              # one job
bash scripts/run_full_jepa_benchmarks.sh  # full queue
python scripts/generate_paper_tables.py
make -C docs/paper all                    # needs tectonic
python -m pytest tests/
```

## Benchmark matrix (article)

- **C0** scratch, **C1** ImageNet, **C2** ResNet+JEPA, **C3/C4/C5** SE+JEPA ablations, **C7–C9** label fractions, **C10** LOO summary.
- Latest results: `benchmarks/ml/results/jepa_summary.md`
- **Honest finding:** C1 > C4 on public Simula single fold; H1 not confirmed yet.

## Data not in git

- `data/kvasir/`, `data/hyperkvasir/`, `data/colonoscopy_3class/` — download via pixi prepare scripts on Mac.
- `checkpoints/` — training outputs, gitignored.

## Mobile / iOS

See **docs/setup-cursor-ios.md**. Use **Cloud** worker for code/docs; **My Machines** for GPU/MPS training on the developer’s Mac.

## Conventions

- Primary metric: **macro-F1** (val for checkpoint selection); clinical: **polyp recall**.
- Early stopping: pretrain monitors `val_latent_loss`; fine-tune monitors `val_macro_f1`.
- Do not edit `.cursor/plans/` plan files unless asked.
- Only commit when the user explicitly requests it.
