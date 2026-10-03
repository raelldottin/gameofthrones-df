# Game of Thrones: Dragon Fire Screenshot Analyzer

Automated analysis of dragon screenshots from Game of Thrones: Dragon Fire mobile game.

## Features

- **OCR Extraction**: Extract dragon stats, abilities, and levels from screenshots
- **Data Models**: Structured Pydantic models for dragons, abilities, habits, and armies
- **Batch Processing**: Analyze multiple screenshots at once
- **Data Export**: Export to JSON for further analysis
- **Army Composition**: Track and validate army compositions

## Current Dragon Roster and Strategy

- [Latest progression overlay — October 3, 2026](player-state/dragon-update-2026-10-03.json) — four observed Hatchery reward groups record **154 persistent relics across 22 already-owned dragons**. **Tashix 4★** is the only directly verified October 3 star-up and is shown at **0/300** toward the next star. Exact counters directly shown after the latest single opens are **Arrax 143/500, Tairax 67/100, Shimmer 429/800, Shadowsong 59/300, and Nyrena 53/500**. No ownership or habit change is inferred.
- [October 3 Hatchery reward log](player-state/hatchery-experiment-2026-10-03.json) — two overlapping 70-relic ten-pull results plus two 7-relic single-open results, for **154 visible relics across 22 unique dragons**. The latest supplied screen shows **1 Dragonbone Key, 0 Dragonglass Keys, 0 Dragonfire Keys, and 304 gold**. Currency and key counts remain dated operational history.
- [Latest progression overlay — September 29, 2026](player-state/dragon-update-2026-09-29.json) — five observed Hatchery reward groups now record **232 persistent relics across 25 already-owned dragons**. **Crimson 2★** remains the only directly verified September 29 star-up. Latest exact counters include **Rhysarion 63/300, Antares 144/300, Dawnseeker 186/300, Zivern 324/800, Vesper 208/300, Vaeldra 45/300, Jagadrix 524/800, Thunderstrike 256/300, Arulix 43/500, Arrax 105/500, and Bevlorin 84/500**. No ownership or habit change is inferred.
- [September 29 Hatchery reward log](player-state/hatchery-experiment-2026-09-29.json) — **232 visible relics across 25 unique dragons over five observed reward groups**. IMG_5278–IMG_5280 add a 70-relic / 12-dragon batch; the re-uploaded IMG_5276(1) and IMG_5277(1) are byte-identical duplicates of already-recorded screenshots and are not counted twice. Latest dated screen state shows **0 Dragonbone Keys, 3 Dragonglass Keys, 0 Dragonfire Keys, and 124 gold**; currencies and keys remain operational history rather than persistent dragon attributes.
- [Latest progression overlay — September 28, 2026](player-state/dragon-update-2026-09-28.json) — three observed Hatchery reward groups record **84 persistent relics across 17 already-owned dragons**. The two later single-open screens directly verify exact current counters for **Rhysarion 57/300, Antares 140/300, Arrax 83/500, Zivern 319/800, Vesper 194/300, and Dawnseeker 166/300**. No **Star Up!** or **Hatched!** label is visible, so no star-rank, ownership, or habit change is inferred.
- [September 28 Hatchery reward log](player-state/hatchery-experiment-2026-09-28.json) — **84 visible relics across 17 unique dragons over three observed reward groups**. The first group is the overlapping IMG_5245–5248 result; IMG_5252 and IMG_5253 are later single opens with exact post-award relic counters. Latest dated state shown is **3 Dragonbone Keys, 1 Dragonglass Key, 0 Dragonfire Keys, and 409 gold**; currencies and keys remain operational history rather than persistent dragon attributes.
- [September 27 verified habit snapshot](player-state/habit-update-2026-09-27.json) — detailed Dragon Pit screens directly verify **Headlong Into Danger 3 (Arrax), Fearsome Reach 2 (Zivern), Whispering Sabotage 5/max (Jagadrix), Dragon's Valor 3 (Vaeldra), Hypnotic Helix 4 (Arulix), and Dragon's Might 2 (Thunderstrike)**, including the displayed level curves and next-upgrade costs where applicable.
- [Latest progression overlay — September 27, 2026](player-state/dragon-update-2026-09-27.json) — two Standard Hatchery batches directly verify **Nyrena 5★, Starshower 2★, Seasmoke 2★, and Kalspire 2★**; later Dragon Pit screens on the same date directly verify the six habit levels linked above. Habit changes are never inferred from star rank alone, and exact post-star relic carryover remains unverified unless directly shown.
- [September 27 Hatchery reward log](player-state/hatchery-experiment-2026-09-27.json) — **418 visible relics across 27 unique dragons over five observed reward groups**. Directly verified star-ups include **Nyrena 5★, Starshower 2★, Seasmoke 2★, Kalspire 2★, and Caraxes 2★**; the final group includes an **Elite Drop of Shadowrend x100**. Currencies and keys remain dated operational observations.
- [Latest progression overlay — September 26, 2026](player-state/dragon-update-2026-09-26.json) — Standard Hatchery ten-pull directly verifies **Arulix 5★**, **Syrax 2★**, and **Smoketail hatched/owned at 2★**. Smoketail raises the verified owned roster to **37 dragons**. Exact post-up relic carryover and newly available habits are left unverified until detailed Dragon Pit profiles are captured.
- [September 26 Hatchery ten-pull](player-state/hatchery-experiment-2026-09-26.json) — **5 Dragonbone Keys + 500 gold** produced **165 visible relics across 17 dragons**, including Arulix and Syrax star-ups plus the Smoketail hatch. Post-pull pity counters are not inferred because no counter screen was supplied.
- [Latest progression overlay — September 25, 2026](player-state/dragon-update-2026-09-25.json) — September 25 Hatchery rewards merged conservatively. Exact current totals are **Shimmer 373/800, Arrax 255/300, Jagadrix 449/800**; other visible awards are stored as minimum progression when no exact post-reward number is shown. **Smoketail x5** is recorded as a relic target only; ownership is not inferred.
- [September 25 Hatchery result log](player-state/hatchery-experiment-2026-09-25.json) — Syrax & Vaeldra event result plus the overlapping standard-batch reward screens. The standard batch shows **74 relics across 14 unique dragons**; dated pity counters and currencies are kept out of the persistent roster.
- [Latest progression overlay — September 24, 2026](player-state/dragon-update-2026-09-24.json) — **Solstryker 5★ (9/500), Bevlorin 5★ (5/500), and Venator 2★ (10/100)** verified from detailed Dragon Pit profiles. Solstryker retains Steady Erosion 1 + Energy Drain 1; Bevlorin retains Fire Ward 1 + Dragon's Fury 1; Venator's newly unlocked first habit is **Hunter's Bane 1**, matched to the repository's previously captured Venator ability reference.
- [Latest progression overlay — September 22, 2026](player-state/dragon-update-2026-09-22.json) — apply **15 dragons' Hatchery relic updates** and the separately verified **Arulix 4★, 289/300 relics** profile over the September 20 complete roster. No unverified star or habit changes are inferred.
- [September 22 Hatchery experiment](player-state/hatchery-experiment-2026-09-22.json) — ten standard chest openings for 900 gold, 78 relics across 15 dragons, and 499 gold shown afterward. Gold and chest counters are dated experiment observations, **not persistent dragon attributes**. The ten-pull yielded no Arulix relics; a subsequent detailed profile independently shows 289/300.
- [Complete reign-persistent dragon roster — September 20, 2026](player-state/dragon-roster-2026-09-20.json) — all 36 owned dragons verified from detailed Dragon Pit screenshots. Star ranks, unlocked habit names and levels, relic progress, class and command names recorded. Tairax's first habit is verified as **Whisper of Ash 1**, with full command and five-habit reference in [dragons/tairax.json](dragons/tairax.json).
- [Current 10-march plan — September 20](player-state/army-composition.md) — ten unique, all-positive-affinity trios computed using September 20 stars and unlocked habits; qualitative deployment priorities, **not measured win rates**. **Stale for optimization:** not recalculated for the September 22/25/26/27 relic updates, September 24 star upgrades, the September 26 Arulix/Syrax star-ups and Smoketail hatch, the September 27 Nyrena/Starshower/Seasmoke/Kalspire star increases, or the October 3 Tashix 4★ star-up and newer relic progression.
- [Current 10-march JSON — September 20](armies/current-ten-marches-2026-09-20.json) — machine-readable formations, bench, constraints and evidence status.
- [September 20 formation analysis](analysis/CURRENT_TEN_MARCHES_ROSTER_OPTIMIZED_2026-09-20.md) — ability and lane synergy, September event context, explicit limits and battle-validation plan.
- [Previous roster — September 3, 2026](player-state/dragon-roster-2026-09-03.json) and [September 3 marches](armies/current-ten-marches-2026-09-03.json) — historical snapshots, **superseded for current deployment**.
- [August 14 Wyrmtable comparison](analysis/CURRENT_TEN_MARCHES_WYRMTABLE_2026-08-14.md) — historical max-level comparison only.

For the latest persistent progression, start with the September 20 complete roster, apply the September 22 overlay by dragon name, then the September 24 overlay, then the September 25 overlay, then the September 26 overlay, then the September 27 overlay, then the September 28 overlay, then the September 29 overlay, then the October 3 overlay; use the September 27 verified habit snapshot for the latest directly observed habit levels and upgrade costs. Record only persistent ownership, star ranks, unlocked habit upgrades, relic progress, class and command identities in the roster/overlay; reign levels, level-dependent combat stats, XP, energy, troop counts, seasonal resources and power are excluded. Older `dragons/` profiles and `dragons.json` include dated reign-specific captures and **must not override** newer star, habit, or relic-progress observations. Dated battle reports are historical evidence, not measurements of the updated roster. The game supports up to **five simultaneous dragon-led armies**; ten marches here are preset candidates and rotation options, not ten simultaneous deployments.

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
