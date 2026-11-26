# Wave 3 — Empirical validation and release readiness

Q17–Q24 are evidence acquisition and validation, not a claim of production readiness. Freeze test/holdout criteria before observing results; never turn synthetic receipts into authenticated release evidence.

| Slice | Objective | Required exit evidence |
|---|---|---|
| Q17 | Stack review and consolidated development candidate | Exact Git input export, complete test discovery, Q16 aggregate CI repair, stack audit, protected files unchanged; independent review still required |
| Q18 | Independent visual benchmark | At least 100 fresh distinct-session screenshots, independent labels, original-image hashes, separate calibration/holdout, frozen thresholds, no tuning on holdout |
| Q19 | Live agent runtime | Real isolated Boundroom/Hermes canary, fresh authenticated workers, restart, timeout and deduplication evidence, independent verifier |
| Q20 | Authoritative roster migration | Actual reign identity and current resource evidence, authenticated approvals, protected keys/checkpoints, restore rehearsal |
| Q21 | Controlled combat experiments | Matched initial troops, gear, talents, formation and enemy; complete round records; controlled comparisons and predeclared hypotheses |
| Q22 | Predictive calibration | Same-mode disjoint training and prospective holdout groups, externally frozen forecasts and baseline, errors and calibrated uncertainty |
| Q23 | Gameplay strategy validation | Resource costs and inventories verified, controlled formation/upgrade outcomes, compare recommendations with existing lineup |
| Q24 | Independent acceptance | All 16 authenticated gates on exact tree, independent reviewer and QA score >=95, no high/critical unresolved, deployment and rollback drill, human authorization |

Q18 requires new source screenshots; do not fabricate them or use the 40 development screenshots as independent holdout. Q19 requires live external infrastructure and permission. Q20–Q23 require game evidence not obtainable from synthetic fixtures. Do not create a long chain of infrastructure-only PRs to conceal these blockers. Keep all drafts intact until authorized; no automatic merge, player writes or resource purchases.
