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

## Cursor Cloud specific instructions

The Cloud VM is **Linux/CPU**, not a Mac — so the pixi workflow above does **not** apply here.

- **Do NOT run `pixi`.** `pixi.toml` pins `platforms = ["osx-64"]`, so `pixi install` fails on Linux. The startup update script instead installs `requirements-ci.txt` + `pytest` into the system Python 3.12 with `pip` (the CI-proven Linux path, mirroring `.github/workflows/ci.yml`). Just use `python3` / `pip` directly.
- **Run from the repo root.** There is no `pyproject.toml`/`setup.py`; modules are imported flatly (e.g. `from models... import ...`), so commands must run with CWD = `/workspace`.
- **CI gates to keep green** (see `.github/workflows/ci.yml`): `python3 -m pytest tests/`; the JEPA+SE-ResNet import forward-pass smoke; and `python3 scripts/generate_paper_tables.py` followed by `git diff --exit-code docs/paper/shared/tables/results.tex` (regenerated tables must match committed `results.tex`).
- **No linter is configured** (no ruff/flake8/black config; CI has no lint step). Use `python3 -m compileall` for a quick syntax check.
- **Data & checkpoints are not in git** and the real prepare scripts download large external datasets. For a CPU smoke/hello-world, generate a tiny ImageFolder dataset (`<root>/{train,val}/<class>/*.jpg`) and train with `python3 script_ResNet.py --data-dir <root> --arch seresnet50 --mask-aware-se --num-classes 3 --epochs 2 --batch-size 8 --img-size 64 --device cpu --output /tmp/out.pt`. Keep synthetic data and checkpoints outside the repo (e.g. `/tmp`); `data/train|val|test/` and `checkpoints/` are gitignored.
- **`make -C docs/paper all` needs `tectonic`, which is not installed** in the Cloud VM; the committed `docs/paper/**/main.pdf` is the reference. Only the table-regeneration gate above runs in cloud.
- **GPU/MPS training and the full `run_*.sh` benchmark campaigns are meant for the developer's Mac** ("My Machines"), not this CPU VM.
