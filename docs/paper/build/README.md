# Paper build artifacts

Per-phase PDF snapshots produced by `bash scripts/validate_publication.sh <phase>`.

| Directory | Phase | Contents |
|-----------|-------|----------|
| `phase-00-thesis/` | 0 | Honest benchmark thesis locked (EN+FR) |
| `phase-01-grouped-splits/` | 1.1 | Group-aware split infra validated |
| `phase-05-tables/` | 5 | Unified auto-generated tables |
| `phase-06-limitations/` | 6 | Limitations subsection added |
| `phase-07-reproduce/` | 7 | `make reproduce-paper` path verified |

Latest PDFs (always current): `en/main.pdf`, `fr/main.pdf`.

Regenerate everything:

```bash
bash scripts/validate_publication.sh all
# or
make validate
```
