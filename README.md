# Game of Thrones: Dragon Fire Screenshot Analyzer

Automated analysis of dragon screenshots from Game of Thrones: Dragon Fire mobile game.

## Features

- **OCR Extraction**: Extract dragon stats, abilities, and levels from screenshots
- **Data Models**: Structured Pydantic models for dragons, abilities, habits, and armies
- **Batch Processing**: Analyze multiple screenshots at once
- **Data Export**: Export to JSON for further analysis
- **Army Composition**: Track and validate army compositions

## Current Dragon Roster and Strategy

- [Latest progression overlay — September 26, 2026](player-state/dragon-update-2026-09-26.json) — Standard Hatchery ten-pull directly verifies **Arulix 5★**, **Syrax 2★**, and **Smoketail hatched/owned at 2★**. Smoketail raises the verified owned roster to **37 dragons**. Exact post-up relic carryover and newly available habits are left unverified until detailed Dragon Pit profiles are captured.
- [September 26 Hatchery ten-pull](player-state/hatchery-experiment-2026-09-26.json) — **5 Dragonbone Keys + 500 gold** produced **165 visible relics across 17 dragons**, including Arulix and Syrax star-ups plus the Smoketail hatch. Post-pull pity counters are not inferred because no counter screen was supplied.
- [Latest progression overlay — September 25, 2026](player-state/dragon-update-2026-09-25.json) — September 25 Hatchery rewards merged conservatively. Exact current totals are **Shimmer 373/800, Arrax 255/300, Jagadrix 449/800**; other visible awards are stored as minimum progression when no exact post-reward number is shown. **Smoketail x5** is recorded as a relic target only; ownership is not inferred.
- [September 25 Hatchery result log](player-state/hatchery-experiment-2026-09-25.json) — Syrax & Vaeldra event result plus the overlapping standard-batch reward screens. The standard batch shows **74 relics across 14 unique dragons**; dated pity counters and currencies are kept out of the persistent roster.
- [Latest progression overlay — September 24, 2026](player-state/dragon-update-2026-09-24.json) — **Solstryker 5★ (9/500), Bevlorin 5★ (5/500), and Venator 2★ (10/100)** verified from detailed Dragon Pit profiles. Solstryker retains Steady Erosion 1 + Energy Drain 1; Bevlorin retains Fire Ward 1 + Dragon's Fury 1; Venator's newly unlocked first habit is **Hunter's Bane 1**, matched to the repository's previously captured Venator ability reference.
- [Latest progression overlay — September 22, 2026](player-state/dragon-update-2026-09-22.json) — apply **15 dragons' Hatchery relic updates** and the separately verified **Arulix 4★, 289/300 relics** profile over the September 20 complete roster. No unverified star or habit changes are inferred.
- [September 22 Hatchery experiment](player-state/hatchery-experiment-2026-09-22.json) — ten standard chest openings for 900 gold, 78 relics across 15 dragons, and 499 gold shown afterward. Gold and chest counters are dated experiment observations, **not persistent dragon attributes**. The ten-pull yielded no Arulix relics; a subsequent detailed profile independently shows 289/300.
- [Complete reign-persistent dragon roster — September 20, 2026](player-state/dragon-roster-2026-09-20.json) — all 36 owned dragons verified from detailed Dragon Pit screenshots. Star ranks, unlocked habit names and levels, relic progress, class and command names recorded. Tairax's first habit is verified as **Whisper of Ash 1**, with full command and five-habit reference in [dragons/tairax.json](dragons/tairax.json).
- [Current 10-march plan — September 20](player-state/army-composition.md) — ten unique, all-positive-affinity trios computed using September 20 stars and unlocked habits; qualitative deployment priorities, **not measured win rates**. **Stale for optimization:** not recalculated for the September 22/25/26 relic updates, September 24 star upgrades, the September 26 Arulix/Syrax star-ups, or newly owned Smoketail.
- [Current 10-march JSON — September 20](armies/current-ten-marches-2026-09-20.json) — machine-readable formations, bench, constraints and evidence status.
- [September 20 formation analysis](analysis/CURRENT_TEN_MARCHES_ROSTER_OPTIMIZED_2026-09-20.md) — ability and lane synergy, September event context, explicit limits and battle-validation plan.
- [Previous roster — September 3, 2026](player-state/dragon-roster-2026-09-03.json) and [September 3 marches](armies/current-ten-marches-2026-09-03.json) — historical snapshots, **superseded for current deployment**.
- [August 14 Wyrmtable comparison](analysis/CURRENT_TEN_MARCHES_WYRMTABLE_2026-08-14.md) — historical max-level comparison only.

For the latest persistent progression, start with the September 20 complete roster, apply the September 22 overlay by dragon name, then the September 24 overlay, then the September 25 overlay, then the September 26 overlay. Record only persistent ownership, star ranks, unlocked habit upgrades, relic progress, class and command identities in the roster/overlay; reign levels, level-dependent combat stats, XP, energy, troop counts, seasonal resources and power are excluded. Older `dragons/` profiles and `dragons.json` include dated reign-specific captures and **must not override** newer star, habit, or relic-progress observations. Dated battle reports are historical evidence, not measurements of the updated roster. The game supports up to **five simultaneous dragon-led armies**; ten marches here are preset candidates and rotation options, not ten simultaneous deployments.

## Installation

```bash
# Using uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"
```

## Dependencies

- Python 3.11+
- OpenCV (cv2) for image processing
- Tesseract OCR for text extraction
- Pillow for image handling
- Pydantic for data validation
- Typer/Rich for CLI

## Quick Start

```bash
# Install dependencies
uv sync

# Run tests
uv run python scripts/test_analyzer.py

# Analyze a screenshot
uv run python -m scripts.dragon_analyzer.cli analyze path/to/screenshot.png

# Batch analyze
uv run python -m scripts.dragon_analyzer.cli batch /path/to/screenshots
```

## Project Structure

```
scripts/
├── dragon_analyzer/
│   ├── __init__.py
│   ├── analyzer.py       # Main analyzer class
│   ├── cli.py            # CLI commands
│   ├── models.py         # Pydantic data models
│   ├── ocr.py           # OCR processing
│   └── config.py
├── test_analyzer.py      # Unit tests
└── test_ocr.py          # OCR tests
```

## Data Models

### Dragon
- name, level, stars, class (Sentinel/Warrior/Hunter/Champion)
- Stats: health, attack, defense, speed, energy

### Ability
- name, type (Command/Habit/Passive), damage_type
- damage_rate, description, cooldown, trigger_condition

### Habit
- name, trigger, effect, stats progression, upgrade cost

### ArmyComposition
- vanguard, left_flank, right_flank
- troop_type, target_type, validation status

## OCR Processing

The analyzer uses Tesseract OCR with custom preprocessing:
- Image resizing and denoising
- Contrast/brightness adjustment
- Thresholding for better text detection
- Region-specific extraction (name, level, stats, abilities)

## Output

Results are saved as JSON files in:
- `dragons/` - Individual dragon data
- `battle-logs/` - Battle reconstruction data
- `analysis/` - Aggregated analysis and army compositions

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Lint
uv run ruff check .

# Type check
uv run ty check

# Format
uv run ruff format .
```
