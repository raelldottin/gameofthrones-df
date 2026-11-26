# Q1 implementation evidence

Status: draft; independent review and CI required. No full release score claimed.

Research: inspected legacy model, analyzer, OCR, configuration, CLI, packaging and smoke tests at 381883c. No validated selected-profile reader exists; the original analyzer called four absent methods and invented default stars, level, class and confidence.

Plan: behavioral tests committed first (cc045f4 and 6e521db); separate legacy observation from canonical state. Preserve every existing roster and battle record. Keep public legacy model names; change unsupported calls from silent success/None to typed failures. Use injectable reader and content-addressed immutable evidence. Actual image decoding, calibrated OCR, source labels and persistent/seasonal reconciliation remain Q2/Q3/Q4.

Implementation: 0–10 legacy star range (0 supports egg records), positive strict reign level, unknown confidence by default; coordinate and order fixes; OCR failures visible; portable env-based defaults; explicit CLI status and validation; nonempty batch; no fabricated army export; safe single filenames; atomic observation writes and conflict rejection. Existing historical data is untouched. CLI output is a directory for analyze/batch; validate accepts legacy DragonData or ArmyComposition, not all repository schemas.

Test effectiveness: named behavioral tests plus eleven real source mutations in isolated temporary copies. The mutation runner accepts only the expected test failure, not import errors or arbitrary infrastructure failures. CI on Python 3.11/3.12 includes package install and CLI entry point.

Limitations: default extraction deliberately raises; injected adapter tests are not real-image accuracy. Batch fail-fast preserves earlier successfully recorded observations (not a transactional batch). Content hash plus before/after read guards common source changes but is not a hostile filesystem sandbox. Existing OCR parsing beyond identified defects remains unvalidated. Legacy model is not the canonical persistent/seasonal schema. No separate agent identities available in this session; independent review and QA remain mandatory. Do not merge before evidence is checked.

The initial red CI failed at TOML parsing (`Cannot overwrite a value`, line 48), before collecting tests. This is a packaging defect, not behavioral red evidence. `quality/replay_legacy_red.py` now copies pinned pre-fix sources into an isolated temporary directory with a minimal pytest config and requires six named behavioral tests to fail, without collection errors. The green CI verifies this replay and the mutation gate separately.
