# Q8 — Release acceptance and integration benchmark (draft)

Release status: **BLOCKED**. This is a read-only release assessment layer, not a deployment mechanism. All 16 required gates are explicit in release.py. Each authenticated receipt must bind the exact candidate Git tree, versioned policy, issuer, gate, outcome and artifact hash. Duplicate, missing, failed, stale or untrusted receipts block. Independent review/evaluation issuer identities must differ from each other and other gate issuers. QA scores require evidence references to admitted receipts, cap each dimension, and require >=95. Even a perfect trusted synthetic package only returns eligible_for_human_review, never authorization.

The trusted digest set is an external security boundary: only an independent authenticated verifier may populate it after checking real artifacts and role identities. Hashes are not signatures; this module does not verify identity, inspect semantic evidence, or establish CI provenance by itself. No production trusted receipt provider is implemented. No self-issued receipt or synthetic test score counts as actual product evaluation.

## Run locally
- python -m scripts.dragon_analyzer.release : historical inventory; always blocked, no automatic promotion.
- python -m pytest -o addopts='' -q scripts/test_release.py : release and cross-module contracts.
- python -m quality.measure_release : five timed runs after warmup for allocation, historical audit and migration staging; input/output digests and platform recorded. This establishes a development measurement, not a regression budget. Freeze baseline on dedicated comparable hardware before asserting performance non-regression. Actual OCR runtime, memory, worker timeout and end-to-end deployment budgets remain open.
- python quality/check_release_mutations.py : targeted source faults with named failing tests.

## Operational procedure
Keep PRs 4–11 draft. Obtain independent review per slice; check CI against each exact head; resolve stack dependency conflicts and rerun complete gates on the final candidate tree. Preserve main and all player-state files. Before any authorized deployment, record previous accepted commit and artifacts, verify backup restore and read-only migration dry run, verify actual worker isolation and signed/authenticated receipts, then perform a rollback drill in a disposable environment. No deployment or destructive rollback has been executed. The pure replay rollback test verifies historical observation-time behavior only.

## Remaining product work
Q3 independent image holdout, habit detection and end-to-end OCR; Q4 authenticated durable authority, correction/revocation policy and actual reign metadata; Q5 verified ability/talent-aware tactical engine; Q6 prospective matched battle evidence and calibration; Q7 authenticated fresh-agent dispatcher, durable content-addressed artifacts, process limits and recovery; Q8 independent reviewer/evaluator and measured performance budgets. Historical development benchmarks are not production scores. No separate agents available in this session. No release or merge.
