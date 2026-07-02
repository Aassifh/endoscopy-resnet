# LaTeX manuscripts — SE-CNN-JEPA colonoscopy

Two arXiv-style preprints (English + French) with shared figures and auto-generated tables.

## Structure

- `en/main.tex` — English article
- `fr/main.tex` — French article
- `shared/` — figures, tables, macros

## Build

Requirements: `tectonic` (recommended) or `pdflatex` + `bibtex`, Python 3.

```bash
cd docs/paper
make tables    # regenerate shared/tables/results.tex from benchmark JSON
make all       # build en/main.pdf and fr/main.pdf (uses tectonic)
make clean     # remove auxiliary files
```

Install Tectonic (macOS): `brew install tectonic`

Or from repo root:

```bash
python scripts/generate_paper_tables.py
make -C docs/paper all
```

## Data source

Tables pull from `benchmarks/ml/results/C*_fold_simula_test.json`.

## Author

Hamza AASSIF — update affiliation in `shared/macros.tex` if needed.
