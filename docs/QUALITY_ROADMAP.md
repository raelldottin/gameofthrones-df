# Quality-first product roadmap

| Slice | Goal | Exit criteria |
|---|---|---|
| Q0 | Dated roster gate | 38 profiles, 40 screenshots, all 21 targeted input faults rejected, negative control and CI |
| Q1 | Repair legacy contracts | red/green tests for 7–10 stars, coordinate parsing, missing OCR interfaces, portable temp paths, CLI failures, clean packaging |
| Q2 | Rewrite analyzer boundary | typed persistent/seasonal observations, image decoder and injected OCR adapter, explicit unknown/abstain, deterministic normalization, atomic storage and migration |
| Q3 | Real image evaluation | independently labeled fixtures, split by screenshot session, target ≥99% exact name/star/relic accuracy on legible supported holdout, zero critical hallucinations; report coverage and abstention |
| Q4 | Reconciliation | provenance, idempotence, duplicate/conflict quarantine, reign transitions, schema migration, rollback, mutation and property tests |
| Q5 | Formation solver | independently verified affinity and ability catalog; uniqueness, active-star gates, deterministic ranking; exhaustive small-fixture oracle; no unsupported win rates |
| Q6 | Battle calibration | matchup-stratified held-out data; compare losses, outcomes and calibration to baseline; uncertainty reported |
| Q7 | Dynamic agent supervisor | distinct identity each stage/retry; artifact hashes and immutable handoffs; gate manifest validator; bounded loop, blocked status, rejection of reused agents/stale benchmarks/false success |
| Q8 | Release readiness | independent review and evaluator, source mutation testing, measured performance budgets, regression history, ≥95/100 and all hard gates |

## Audit findings at Q0 (Q1 draft remediation in progress)
- Critical: model restricts stars to 5; analyzer calls missing extract_dragon_name, extract_level, extract_stats, extract_ability_info.
- High: battle header location converts regex group 1 (name) to int instead of coordinate groups 2 and 3; analyze/batch/validate CLI placeholders; broad OCR exception handling; absolute personal Mac paths; three shallow smoke tests.
- Legacy OCR and CLI remain incomplete. A green roster gate does not fix these. Evaluate rewrite instead of preserving fake defaults. Add red tests before repairs.

See [Q1 implementation evidence](Q1_IMPLEMENTATION.md) for the draft fixes and limitations. Do not mark Q1 accepted before independent review, clean install, behavioral tests and source mutation gate pass.

Proposed thresholds are targets, not measured results. Do not publish personal screenshots without approval. Use versioned benchmark hashes and regression history. No global release score until independent evidence exists.

Q2 stacked draft: [candidate extraction and measured development baseline](Q2_CANDIDATE_EXTRACTION.md). Real-image acceptance remains blocked.

Q3 draft: [visual recognition and frozen holdout protocol](Q3_VISUAL_RECOGNITION.md). 599/600 development fields correct; holdout and independent acceptance blocked.

Q4 stacked draft: [reconciliation contract](Q4_RECONCILIATION.md); pure replay, staged migration, approval boundary and explicit reign transitions. Durable authority and independent acceptance pending.

Q5 draft: [exact additive formation allocation](Q5_FORMATION_SOLVER.md). Tactical synergy and independent acceptance remain open.

Q6 draft: [battle replay and illustrative attrition model](Q6_BATTLE_EVALUATION.md). Calibration and full combat mechanics remain blocked on evidence.

Q7 draft: [bounded workflow supervisor contract](Q7_SUPERVISOR.md); simulated dispatch only, authenticated runtime integration and independent acceptance pending.

Q8 draft: [release assessment and operational gates](Q8_RELEASE_ACCEPTANCE.md). Production blocked; no independent score or release authorization.
