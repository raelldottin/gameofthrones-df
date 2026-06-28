# Army 1 Battle Validation — Shieldbearers vs Jauss Cavalry

Date: 2026-06-28  
Source: 9 player-provided battle report screenshots  
Target: Stalemate Lv. 6 Food, Pinkmaiden (1010, 1332)  
Opponent: [GodOfWar] Jauss  
Opponent army: Feskar / Caraxes / Shadowsong with Cavalry  
Attacking army: Rhysarion / Vhagar / Malachite with Shieldbearers  
Result sequence: Stalemate, Stalemate, Stalemate, moving from Evenly Matched to Favorable

## Executive read

Army 1 is validated as a real attrition anchor. It fought through a bad troop matchup — Shieldbearers into Cavalry, shown as Disadvantage (-7% DMG) for the attacker and Advantage (+7% DMG) for the defender — and still pushed the report state from Evenly Matched to Favorable.

The stalemates do not mean the army is weak. The pattern says the army was winning the attrition race but lacked enough tempo to finish the Cavalry target inside the 10-round cap.

## Report snapshots

| UTC time | Rating | Attacker troops | Defender troops | Notes |
|---|---:|---:|---:|---|
| 07:16:14 | Evenly matched | 11,012 / 22,173 | 10,415 / 21,848 | Both sides still had full dragon output. |
| 07:17:14 | Evenly matched | 5,858 / 22,173 | 4,324 / 21,848 | Vhagar and Shadowsong dropped to 0. Malachite and Rhysarion kept output going. |
| 07:18:14 | Favorable | 4,702 / 22,173 | 417 / 21,848 | Defender was nearly cleared, but the 10-round limit still caused stalemate. |

## Dragon performance

### Rhysarion

Rhysarion was consistent. Dawnsong cast 6 times in all three visible reports.

- 07:16:14: 4,009 total kills, 1,632 command kills, 2,377 basic attack kills
- 07:17:14: 2,682 total kills, 1,084 command kills, 1,598 basic attack kills
- 07:18:14: 1,413 total kills, 523 command kills, 890 basic attack kills

Decision: keep Rhysarion locked in Army 1. He is not a flex piece for a Vaeldra army.

### Vhagar

Vhagar was powerful when alive but became the volatility point.

- 07:16:14: 3,256 total kills, 5 Fiery Bonds casts
- 07:17:14: 283 total kills, 2 Fiery Bonds casts, finished at 0 HP
- 07:18:14: 0 total kills, 0 Fiery Bonds casts, finished at 0 HP

Decision: Vhagar still belongs in the double-legendary anchor shell, but survivability is the issue to watch. Do not judge him only by the later depleted reports; the first report shows real contribution when he survives long enough to cast.

### Malachite

Malachite was the most important proof point in these reports. Warden's Rally cast 6 times in every visible 10-round report and supplied both damage and healing.

- 07:16:14: 4,168 total kills, 1,282 command kills, 2,886 basic attack kills, 1,403 healing
- 07:17:14: 3,126 total kills, 899 command kills, 2,227 basic attack kills, 1,102 healing
- 07:18:14: 2,494 total kills, 749 command kills, 1,745 basic attack kills, 804 healing

Decision: Malachite is not just filler. He is the stabilizer and should stay locked with Rhysarion and Vhagar.

## Enemy threat read

Caraxes was the main burst threat.

- 07:16:14: 5,827 total kills, including 3,421 from Infernal Burst
- 07:17:14: 3,486 total kills, including 2,073 from Infernal Burst
- 07:18:14: 748 total kills, including 369 from Infernal Burst

Feskar remained active deep into the final report, but Caraxes created the damage pressure that made Vhagar collapse.

## Strategic conclusions

1. Army 1 should stay locked as Rhysarion / Vhagar / Malachite.
2. The double-legendary anchor theory is supported here: Vhagar plus Malachite gives the army enough ceiling and sustain to fight uphill through a troop disadvantage.
3. Rhysarion is the glue dragon, not the spare dragon. Pulling him for Vaeldra would break the army's consistency.
4. Vaeldra should not replace any Army 1 piece based on these reports.
5. This army should avoid Cavalry when a Spearmen counter is available. Its better use is into Archers/Siege or as a defensive attrition anchor.
6. The next improvement is not composition churn. It is matchup selection, Vhagar survivability, and more tempo so the army can finish before round 10.

## Repo implications

- Mark Army 1 as battle-validated against a bad troop matchup.
- Preserve Army 1 as the strongest locked shell.
- Treat Vaeldra as a lower-army control/depth candidate, not an Army 1 replacement.
- Add future test cases against Archers and Siege to confirm how Army 1 performs when troop matchup is favorable.
