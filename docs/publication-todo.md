# Publication Readiness TODO

Ordered roadmap to validate the work and make it publishable, given the current
constraints: **single public center (Simula), public Kvasir + HyperKvasir images
only, no video**.

> Key enabler: you do **not** need videos. HyperKvasir ships ~99,000 **unlabeled
> still images** alongside the labeled set — a legitimate large corpus for JEPA
> pretraining. This removes the biggest weakness of the SSL story.

Work top-to-bottom; each phase unblocks the next.

---

## Phase 0 — Decide the paper's honest thesis (do first)

- [x] Pick the framing given the available data. Two viable, honest options:
  - **A. Methods/benchmark paper** — contribution = reproducible unified
    benchmark + mask-aware SE + CNN-JEPA baseline (not "JEPA beats ImageNet").
  - **B. Empirical study** — "When does domain SSL help colonoscopy
    classification?" with an honest, nuanced/negative result.
- [x] Stop claiming JEPA superiority unless Phase 3 proves it.

---

## Phase 1 — Fix validity (blocking; not publishable without this)

- [x] **1.1 Patient/procedure-grouped splits.** Replace per-image
  `stratified_split` in `scripts/prepare_colonoscopy_3class.py` with group-aware
  splitting (`GroupShuffleSplit` / `GroupKFold`) keyed on procedure/patient (or
  at least source video/sequence).
  - _Done when:_ no image from one procedure appears in more than one split.
- [ ] **1.2 Re-run all C0–C5 + B2–B6** on grouped splits. Expect the near-perfect
  C1 (0.989) to drop — that is the honest number.
- [ ] **1.3 Multi-seed.** ≥3 seeds per config; report **mean ± std** and
  bootstrap 95% CIs on macro-F1 and polyp recall.
  - _Done when:_ every table cell is `mean ± std`, not a single number.
  _Infra: `benchmarks/ml/seeds.json`, `run_multi_seed_campaign.sh`, `generate_paper_tables.py` mean±std; re-runs pending._
- [ ] **1.4 Significance tests** for every "X beats Y" claim (paired across
  seeds / bootstrap). Soften or remove within-noise claims (B6 vs B2:
  0.586 vs 0.585; C2 vs C4).

---

## Phase 2 — Make the SSL experiment real (the JEPA story)

- [ ] **2.1 Pretrain JEPA on HyperKvasir's ~99k unlabeled images** (not the ~4k
  labeled subset). Point the prepare/pretrain scripts at the unlabeled folder.
  _Script added: `scripts/download_hyperkvasir_unlabeled.py` + `pixi run prepare-hyperkvasir-unlabeled`; campaign prefers `data/jepa_frames/hyperkvasir_unlabeled` when present._
- [ ] **2.2 Re-run C2–C5** fine-tunes from the new checkpoints, with grouped
  splits + multi-seed.
- [ ] **2.3 Diagnose C3 = C4 = C5** (currently bit-identical: 0.9103 / 0.8285).
  Verify the ablations actually differ (log SE pooling path, confirm distinct
  checkpoints load). Either produce a real difference, or report that mask-aware
  SE has no effect and reframe it as a finding.

---

## Phase 3 — Test the actual hypotheses

- [ ] **3.1 Label-efficiency (C7–C9)** re-run under grouped/multi-seed. Strongest
  likely-positive result: if C4 > C1 at 10–25% labels, that is a publishable
  claim (aligns with H1's intent).
- [ ] **3.2 Cross-dataset external validation** (replaces missing multi-center):
  train on Kvasir → test on HyperKvasir, and reverse. Supports the
  "generalizes across hospitals" motivation without private data.
- [ ] **3.3 Drop or fix "LOO".** With one center, remove the C10 "LOO mean
  (n=1)" table or relabel it plainly as a pooled split.

---

## Phase 4 — Complete or cut the benchmark scope

- [x] **4.1 T2 pathology:** either run the 11-class runs and populate the empty
  `docs/paper/shared/tables/classification_unified.tex` table, or remove T2
  everywhere (abstract/intro/methods/results). An empty table is an auto-reject.
- [x] **4.2 T1 JEPA (H2/H4):** add these rows to the HK-23 table, or delete the
  sentence promising them.
- [ ] **4.3 C6 ViT/DINOv2 linear probe:** run it as the promised "reference
  ceiling," or remove the claim.

---

## Phase 5 — Correctness & literature (cheap, high-value)

- [x] **5.1 Fix the polyp-recall definition** in `methods.tex` (it currently
  describes precision).
- [x] **5.2 Cite CNN-JEPA prior art**; reframe novelty as mask-aware SE +
  benchmark (do not imply you invented convolutional JEPA).
- [x] **5.3 Add a numeric comparison to published HyperKvasir results** so
  readers know whether macro-F1 ≈0.58 is competitive.
- [x] **5.4 Reconcile the two overlapping screening tables**
  (`results.tex` vs `classification_unified.tex`) into one, single rounding
  convention (fix 0.828 vs 0.829 mismatch).

---

## Phase 6 — Clinical framing & completeness

- [ ] **6.1 Report sensitivity at fixed specificity** (and PR/ROC curves) for the
  polyp class — macro-F1 alone under-serves a screening claim.
- [ ] **6.2 Add per-class counts, data-availability statement, ethics note, and a
  consolidated Limitations paragraph** (single center, image counts, compute).
  _Partial: Limitations subsection added (EN+FR); ethics/data statement pending._
- [ ] **6.3 Minor fixes:** hardware line; reconcile `\numsamples` vs T1/T3
  counts; regenerate all figures/tables from final JSON.

---

## Phase 7 — Reproducibility & submission

- [ ] **7.1 Freeze a `make reproduce` path** (prepare → pretrain → campaign →
  tables); verify tables regenerate from committed JSON.
  _Added: root `Makefile` targets `reproduce`, `reproduce-paper`, `validate`._
- [ ] **7.2 Clean runs:** `python -m pytest tests/` and LaTeX build
  (`make -C docs/paper all`) pass for EN + FR.
  _Validated via `bash scripts/validate_publication.sh all`._
- [ ] **7.3 Pick a venue** matching the honest thesis (benchmark/reproducibility
  or medical-imaging workshop track if the result stays "ImageNet ≥ JEPA except
  at low labels").

---

## Priority summary

- **Minimum bar to be publishable at all:** Phase 1 + 4.1 + 5
  (grouped splits + uncertainty + complete/scoped benchmark + correct defs).
- **Turns "honest but weak" into a real contribution:** Phase 2
  (99k-image JEPA pretrain) + Phase 3.1 (label-efficiency win) + Phase 3.2
  (cross-dataset generalization).
