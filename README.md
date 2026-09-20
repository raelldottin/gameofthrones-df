# Game of Thrones: Dragon Fire Screenshot Analyzer

Automated analysis of dragon screenshots from Game of Thrones: Dragon Fire mobile game.

## Features

- **OCR Extraction**: Extract dragon stats, abilities, and levels from screenshots
- **Data Models**: Structured Pydantic models for dragons, abilities, habits, and armies
- **Batch Processing**: Analyze multiple screenshots at once
- **Data Export**: Export to JSON for further analysis
- **Army Composition**: Track and validate army compositions

## Current Dragon Roster and Strategy

- [Current reign-persistent dragon roster — September 20, 2026](player-state/dragon-roster-2026-09-20.json) — all 36 owned dragons verified from detailed Dragon Pit profile screenshots across four batches. Stars, habit ranks, relic progress, classes, and commands are captured where visible; Tairax's first habit is confirmed at level 1 but its name remains unverified.
- [Previous roster — September 3, 2026](player-state/dragon-roster-2026-09-03.json) — historical snapshot retained for provenance.
- [Last published 10-march plan](player-state/army-composition.md) — composed using the September 3 roster; **not recalculated from the September 20 update**.
- [Machine-readable September 3 marches](armies/current-ten-marches-2026-09-03.json) — previous lineup proposal; not newly validated.
- [August 14 Wyrmtable comparison](analysis/CURRENT_TEN_MARCHES_WYRMTABLE_2026-08-14.md) — historical max-level comparison only.

The current roster tracks only information retained across reigns. Dragon Reign Level, combat stats tied to that level, XP, energy, troop counts, seasonal resources and power are intentionally excluded. Older `dragons/` profiles and `dragons.json` include dated reign-specific captures and **must not override** the more recent star, habit, or relic-progress observations in `player-state/dragon-roster-2026-09-20.json`. Dated battle reports are historical evidence, not measurements of the updated roster.

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
│   ├── ocr.py            # OCR processing
│   └── config.py        # Configuration
├── test_analyzer.py      # Unit tests
└── test_ocr.py           # OCR tests
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
