# Superpowers Cursor Benchmark Harness

Adapted from `vendor/superpowers/tests/skill-triggering/` for Cursor.

## Commands

```bash
./run-benchmark.sh all       # hook test + analyze + results
./run-benchmark.sh analyze   # CSO analysis only
./run-benchmark.sh results   # regenerate summary tables
./run-benchmark.sh hook-test # verify session-start hook
```

## Python SDK mode (optional)

```bash
pip install cursor-sdk
export CURSOR_API_KEY=...
python run_benchmark.py sdk --condition treatment --runs 3
```

## Contents

- `prompts/` — 6 upstream naive prompts (verbatim)
- `scenarios/` — pressure scenario base prompts
- `rubrics/` — scoring criteria
- `run_benchmark.py` — analysis and result generation

See [docs/superpowers-study/05-cursor-benchmark-protocol.md](../docs/superpowers-study/05-cursor-benchmark-protocol.md).
