# Q3 — Visual recognition development checkpoint

## Design and observed results
The Q2 reader emitted 524 correct, 3 wrong and 73 unknown values. This slice uses field-specific crops and character whitelists for levels, color-preserving name crops, and five star-slot color signatures (gold=1, red=2, outlined empty=0). Reject ambiguous slots and invalid rank sequences. Preserve supported whole-panel numeric values; use secondary crops only on missing stats. This precedence avoids known secondary OCR errors but is not an independently calibrated fusion rule. Never infer star rank from relic balance or dragon identity. Candidate-only output is read-only and not linked to canonical storage.

Measured against the same 40 original 1536x709 screenshots and 15 existing manually transcribed fields: 599/600 correct (99.83%), zero wrong, one unknown (Seasmoke star icons). This is development calibration, not generalization. No image bytes were uploaded. Habit recognition is not part of these 15 fields; it remains unsupported. Fixed geometry and color signatures may fail on other layouts, displays, accessibility settings or animated backgrounds. Whitelisting may hide bad characters and therefore still requires review.

## Reproduce
`python quality/evaluate_visual.py --images /path/to/original/screenshots` with Tesseract 5.5.0 and local image manifest. Local measurements used cached Q2 full-panel OCR plus five new field batches and the visual module. Integrated script needs independent replay. `python -m scripts.dragon_analyzer.visual_reader IMAGE --catalog quality/fixtures/panel-name-catalog.json` returns unverified fields only.

## Holdout protocol (freeze before capture)
- Distinct capture session/reign; no same-image or same-session duplicates across development/holdout. At least 100 legible supported profiles across rarities and ranks, more if needed for a meaningful uncertainty bound. Include negative/unreadable or unsupported-screen cases separately.
- Independent two-pass manual labels; resolve disagreement without inspecting predictions. Record per-image source hash, capture session, geometry, labels and missing fields. Do not upload original images without permission.
- Acceptance: >=99% exact field accuracy including abstentions on supported legible fields, zero wrong critical attributes (identity, stars, level, relics), report critical-field coverage, confidence intervals and negative cases. Critical unknowns must block promotion. Measure runtime and resource use. Report habits separately when supported; no overall complete-reader claim without their evaluation.
- Freeze algorithm, fixture hash, score and thresholds before holdout run; no tuning on holdout. A failed holdout is retained as a benchmark result; repairs require fresh holdout.
- Independent stage identities/reviewer not available in current session; no 95/100 release score or acceptance. Q1/Q2 remain draft dependencies.
