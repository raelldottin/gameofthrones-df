# Q17 — Stack review (draft)

## Observed defects and fixes
1. Q16 run 45868431884: both contract jobs passed 361 tests and 136 targeted mutants; aggregation failed with ModuleNotFoundError: pydantic. Q16 parent repair 83acb90 lazily exports public analyzer symbols and runs certification with python -S. No gate bypass. Await actual aggregate.
2. Q9–Q16 runner copied allowlisted working-directory inputs, including untracked/ignored files. A clean tracked diff did not establish that all benchmark inputs came from the declared tree. Q17 exports regular blobs from the exact Git commit to a private temp directory, rejects symlinks/submodules, and runs the original per-mutant snapshot process on the frozen tree. No external Git archive attribute substitution. Retest with real miniature Git repositories containing dirty, ignored and untracked files. Validate clean checkout at start/end; source_snapshot marker required by certification. This is not a security sandbox; trusted checkout, dependencies and runner environment remain external.
3. CI hardcoded all 16 test files. No omitted current file found, but future test files could silently be missed. Use pytest discovery over scripts and upload behavioral JUnit alongside mutation report. No existing CLI checks or mutation definitions removed. JUnit is development evidence; certification still verifies mutation reports, not independently authenticating every behavioral result.
4. Installed wheel includes dragon_analyzer only, not quality tooling; certification is a checkout-only engineering command, not an installed consumer CLI. Do not pretend installed package exposes all engineering tooling. Package/API cleanup and real end-to-end screenshot workflow still need separate review.

## Stack audit and open risks
PRs #4–19 were open drafts, stacked in order; main remained 381883c. Q17 is draft #20 on the repaired Q16 head, not a merged release. Q16 had 41 protected player-state/armies blobs identical to main. Recheck exact head after Q17. No independent reviewer agent was available. This is an implementation-owner review, not acceptance of every line of 16 PRs.

- Q1–Q3/Q11: fail-closed preview and same-session measurements; no independent holdout or complete ability/commander/gear recognition, integrated original-image replay still outstanding.
- Q4/Q12: signed local journal and replay tests, not authoritative production migration. External key custody, actual reign, authenticated checkpoint and recovery required.
- Q5/Q13/Q15: exact limited optimization and dated inventory strategy; uncalibrated preference objectives, incomplete mechanics and current resources. No recommendation promotion.
- Q6/Q14: historical arithmetic and illustrative simulation; no prospective calibrated probabilities, actual combat coefficients or independent groups.
- Q7/Q10: simulated dispatcher and local receipt bridge, no live execution, trusted verifier service, real isolation or external deduplication.
- Q8/Q16/Q17: structural evidence, not independent acceptance. No trusted receipts or score. Performance ceilings proposed, not verified comparable budgets. No deployment rollback drill.

Q17 adds one targeted certification mutation (137 total) and real snapshot canaries. Test-first checkpoint recorded; red CI not independently observed at commit. The next objective is Q18, independent visual evidence, not another synthetic accuracy claim.
