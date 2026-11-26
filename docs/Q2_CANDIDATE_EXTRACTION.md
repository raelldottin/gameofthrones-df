# Q2 — screenshot candidate extraction (draft)

Q1 CI: 34/34 behavioral tests, 6/6 expected legacy failures, 11/11 source mutants, Python 3.11/3.12; independent review outstanding. This stacked PR does not merge Q1 or Q2.

## Design
Read original bytes once, hash them, decode with Pillow, validate geometry, normalize a right-panel crop, inject OCR text reader, parse bounded patterns with explicit unknowns. Output is an unverified candidate and never writes canonical data. No default integration into Q1's fail-closed analyzer. Stars/habits are icon-only and not inferred. Names require exact catalog match; no fuzzy identity guess. Raw OCR may contain errors even when syntactically valid; all values need verification before reconciliation. Separate Q4 state model will own reign transitions.

## Actual development benchmark
40 local images (38 unique dragons) from one capture session; 15 scored fields each. Labels from November 26 manual transcription; not independent. Tesseract 5.5.0. Correct 524/600 (87.33%), wrong 3/600, abstain 73/600. Precision among emitted values 524/527 (99.43%), coverage 527/600 (87.83%). All three wrong values were level 2 read as 9. Name coverage 28/40; star coverage 0/40. This **fails** acceptance; no held-out accuracy claim. No image bytes uploaded to GitHub. Fixture manifest hashes local files. Reproduce with `python quality/evaluate_panels.py --images /path/to/screenshots` (Tesseract installed). The baseline measurement was made using the same parser and crop in local tools; reproduction runner CI requires separately available original files.

## Next work
Improve color-preserving title segmentation and level icon reading; design icon-based star/habit detector; add independent labels and a distinct capture-session holdout; enforce coverage and exact-field accuracy together; prevent candidate promotion until independently verified. Never tune against holdout. Freeze acceptance metrics before testing. No full release score, no independent agent dispatch in this session. Test-only commit precedes production code; CI verifies synthetic contracts, not real OCR accuracy.

Review repair: a sign adjacent to a numeric token must not be consumed as icon decoration. Added four regression examples and six targeted source mutations for candidate extraction. Rerunning the revised parser against cached real OCR output preserved 524/3/73. CI results pending.
