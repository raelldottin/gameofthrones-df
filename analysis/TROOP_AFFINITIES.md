# Dragon Troop Affinities

This document summarizes the troop affinities for various dragons in Game of Thrones: Dragon Fire, as determined through Dragon Pit screenshots and battle report analysis.

## How Troop Affinities Work

- When a dragon's troop affinity matches the enemy troop type deployed, the dragon receives a **+20% to Dragon Stats** bonus (ATK, HP, DEF, SPD)
- This bonus is visible in post-battle reports (e.g., `IMG_3256.PNG`)
- Troop type advantages/disadvantages (±7% damage) are separate from affinity bonuses
- To determine a dragon's affinity: deploy it with a specific troop type and check if it shows "+20% to Dragon Stats" in the battle report

## Affinity Table

| Dragon | Class | Positive Affinity (Dragon Pit) | Negative Affinity | Best Troop(s) for +20% Dragon Stats |
|--------|-------|--------------------------------|-------------------|-------------------------------------|
| **Syrax** | Sentinel | Spearmen (Infantry‑type) **and** Archer | Siege | Spearmen **or** Archer |
| **Tashix** | Hunter | Archer (unlocked) | Siege | Archer |
| **Antares** | Hunter | Archer | Siege | Archer |
| **Bevlorin** | Warrior | Spearmen | — | Spearmen |
| **Malachite** | Sentinel | Cavalry **and** Shieldbearer | Spearmen, Siege | Cavalry **or** Shieldbearer |
| **Vaeldra** | Warrior | Spearmen | — | Spearmen |
| **Daemoros** | Warrior | Archer | — | Archer |
| **Shadowsong** | (likely Sentinel/Hunter/Warrior) | Cavalry | — | Cavalry |
| **Zivern** | (unknown) | Archer **and** Siege | — | Archer **or** Siege |
| **Shadowrend** | Warrior | Shieldbearer **and** Siege | — | Shieldbearer **or** Siege |
| **Thunderstrike** | (unknown) | Cavalry | — | Cavalry |
| **Feskar** | Champion | Spearmen **and** Archer **and** Siege | — | Spearmen **or** Archer **or** Siege |
| **Jagadrix** | Warrior | **Spearmen** | — | **Spearmen** |
| **Vesper** | Sentinel | Shieldbearer | Siege | Shieldbearer |
| **Seasmoke** | (unknown) | Cavalry **and** Archer | Siege | Cavalry **or** Archer |
| **Dawnseeker** | Sentinel | Spearmen | Siege | Spearmen |
| **Vhagar** | Warrior | Shieldbearer **and** Archer **and** Siege | — | Shieldbearer **or** Archer **or** Siege |
| **Arrax** | (unknown) | Shieldbearer **and** Archer | — | Shieldbearer **or** Archer |
| **Solstryker** | Champion | Archer | — | Archer |
| **Shimmer** | Champion | Cavalry **and** Siege | — | Cavalry **or** Siege |
| **Velar** | (likely Warrior) | Shieldbearer | — | Shieldbearer |
| **Arulix** | Champion | Cavalry | — | Cavalry |
| **Nyrena** | Hunter | Shieldbearer **and** Siege | — | Shieldbearer **or** Siege |
| **Rhysarion** | Champion | Spearmen **and** Shieldbearer **and** Siege | — | Spearmen **or** Shieldbearer **or** Siege |

## Notes

1. **Class Information**: Some dragon classes are marked as "(unknown)" or "(likely ...)" - these should be verified by checking the dragon's detail screen in-game or consulting the `dragons.json` file in this repository.

2. **Negative Affinities**: Only explicitly stated negative affinities are shown in the table. Absence of a negative affinity does not necessarily mean the dragon has no negative affinities - it may simply not have been tested or reported.

3. **Multiple Affinities**: Dragons can have multiple positive affinities (e.g., Feskar has affinity with Spearmen, Archer, AND Siege).

4. **Usage Recommendation**: 
   - For army optimization, match troop types to dragon affinities to maximize the +20% stat boost
   - Consider which dragons in your army you want to strengthen most when selecting troop types
   - Rotate troop types to cover multiple dragons in multi-dragon armies

## Sources

Data compiled from:
- Dragon Pit screenshots (IMG_3257.PNG, IMG_3258.PNG, IMG_3259.PNG, etc.)
- Battle report analysis (IMG_3256.PNG and others)
- User-provided affinity information throughout the discovery process
- Repository references: `dragons.json`, `armies.json`, and various mechanics documents

## Last Updated

June 23, 2026