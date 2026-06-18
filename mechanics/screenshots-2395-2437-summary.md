# Game Mechanics Update — Screenhots 2395–2437

This file summarizes mechanics newly confirmed or clarified from screenshots `IMG_2395.PNG` through `IMG_2437.PNG`.

## Sources
- `IMG_2395.PNG` – Info Guide: Maps
- `IMG_2396.PNG` – Info Guide: Stronghold
- `IMG_2397.PNG` – Info Guide: Resources
- `IMG_2398.PNG` – Info Guide: Social (Alliances)
- `IMG_2399.PNG` – Info Guide: Army Actions (Marching)
- `IMG_2400.PNG` – Info Guide: Army Actions (Combat Outcomes / Reinforcement)
- `IMG_2401.PNG` – Info Guide: Army Actions (Reinforcement / Recall)
- `IMG_2402.PNG` – Info Guide: Garrisons
- `IMG_2403.PNG` – Info Guide: Garrisons (Slots & Ownership)
- `IMG_2413.PNG` – Info Guide: Army Builder
- `IMG_2414.PNG` – Army Builder UI (Shadowrend / Left Flank)
- `IMG_2426.PNG`/`2427.PNG` – Tile map gameplay (Coldwater, combat prep)
- `IMG_2431.PNG`–`2437.PNG` – Stronghold / Infrastructure / War Tactics / Dragon Care

## 1. Map & Territory System (confirmed)
- **Dual map system**: World Map (high-level strategy / navigation) + Tile Map (tactical combat)
- **Territory capture**: send armies to occupy adjacent tiles
- **POIs (Points of Interest)**: special locations; Alliance PvP variants exist
- **Key locations**: Crossings, Towns, Castles — **only Alliances can hold** these
- **Victory condition**: dominate the Seven Kingdoms and claim King's Landing
- **Factions**: server-wide groups; **Alliances**: player-created sub-groups within Factions
- **Alliance persistence**: Alliances continue across Reigns

## 2. Resources & Reign System (confirmed)
- **Basic Resources** expire at the end of each Reign: Food, Wood, Stone, Iron
- **Non-expiring / persistent**: Gold, Dragon collection, Star Rank, Heirlooms
- **Special currencies**: Meat, Stamina, Resolve, Territory Influence
- **Economy panel**: track production rates and storage caps

## 3. Stronghold & Infrastructure (confirmed)
- **Tier 8** Stronghold (player current state)
- **1/2 builders** available
- **Buildings** use Roman numerals (I, II, III…) with cumulative level counts (e.g. 6/15)
  - Granary II 6/15 (Food)
  - Lumber Mill II 6/15 (Wood)
  - Quarry II 5/15 (Stone)
  - Foundry II 5/15 (Metal/Iron)
  - Storehouse II 0/15 (storage)
- **Building progression**: Stronghold Tier unlocks higher tiers; lower-tier buildings can still be upgraded within limits

## 4. Army Builder & Composition (confirmed)
- **Army structure**: 1–3 dragons **required** to form an army; single troop type per army
- **Troop source**: Barracks
- **Editing constraint**: can only modify army composition when army is at a **Stronghold** or **Garrison**
- **Formations**: Left/Right/Center flanks; placement matters for bonuses
- **Dragon classes** (from Dragon Care tree):
  - Champion
  - Warrior
  - Sentinel
  - Hunter
- **Dragon roles** (shown in UI):
  - Vanguard slot required for deployment
  - Left Flank / Right Flank slots

## 5. March & Combat Rules (confirmed)
- **Stamina** consumed per action; dragons regain 1 Stamina every 4m 30s
- **March speed** = speed of the **slowest dragon** in the army
- **Combat**: win battle + break **Durability** (castle icon) to capture tile
- **Combat resolution**:
  - Win & break Durability → capture tile
  - Win but fail to break Durability → army returns to origin
  - Lose → army sent all the way back to Stronghold
  - Stalemate after 10 rounds → both armies remain on tile, attacker regroups after cooldown
- **Terrain Advantage**: shown in combat preview as "No Advantage" or similar
- **Combat preview**: shows Player Strength vs Defender Strength with FAVORABLE/UNFAVORABLE verdict
- **March cost example**: 10 Stamina, ~2 minutes travel time for adjacent tile

## 6. Garrisons (confirmed)
- **Purpose**: forward operating bases on Ruins, Towns, Castles
- **Benefits**:
  - Faster marches *to* the garrison
  - Quicker reinforcements *to* armies stationed there
  - Recall point (defeated/recalled armies return here instead of Stronghold)
  - Can refill troops, adjust lanes, swap troop types at garrison
- **In-field limitation**: armies deep in the field can only refill troops; cannot change dragons or troop types
- **Slots & Ownership**:
  - Garrisons have limited army slots
  - **Towns**: Alliance-owned; all alliance members can garrison there (shared slots)
  - **Castles**: Faction-owned; only Faction members can garrison, march through, or conquer adjacent tiles
  - **Ruins**: slots unlocked via "Ruins Reinforcement" upgrade
