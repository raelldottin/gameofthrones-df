# Battle Report — Black Goat Level 35 Affinity Corrections

Source: report screenshots supplied June 30, 2026.

## Summary

Two Black Goat Level 35 report cards were captured:

1. **Stalemate:** Crimson / Seasmoke / Feskar as Cavalry into Spearmen.
2. **Victory:** Tashix / Vaeldra / Zivern as Spearmen into Cavalry.

The main value of these reports is not just the outcome. They correct two affinity assumptions:

- **Crimson is not confirmed Cavalry.** In a Cavalry formation, Crimson showed **No Bonus** while Seasmoke and Feskar showed **+20% to Dragon Stats**.
- **Zivern is not confirmed Spearmen.** In a Spearmen formation, Zivern showed **No Bonus** while Vaeldra showed **+20% to Dragon Stats**.

## Report 1 — Crimson / Seasmoke / Feskar

- **Report:** Stalemate Black Goat, Level 35.
- **Time:** 2026-06-30 06:00:05 UTC.
- **Location:** Evenfall Hall (1934, 786).
- **Player troop type:** Cavalry, **Disadvantage (-7% DMG)**.
- **Enemy troop type:** Spearmen, **Advantage (+7% DMG)**.
- **Result:** Stalemate.

Formation:

| Lane | Dragon | Level | End / Start troops | Affinity |
|---|---|---:|---:|---|
| Left | Crimson | 40 | 4,856 / 7,058 | No Bonus |
| Vanguard | Seasmoke | 44 | 5,877 / 7,464 | +20% Dragon Stats |
| Right | Feskar | 40 | 4,577 / 7,058 | +20% Dragon Stats |

Totals:

| Side | Start | End | Losses | Removed % |
|---|---:|---:|---:|---:|
| Player | 21,580 | 15,310 | 6,270 | 29.05% lost |
| Enemy | 19,500 | 4,897 | 14,603 | 74.89% removed |

This army removed a lot of enemy troops, but it did not finish the encounter. It is not a Cavalry gold-standard army because it had only **2/3 affinity coverage**.

## Report 2 — Tashix / Vaeldra / Zivern

- **Report:** Victory Black Goat, Level 35.
- **Time:** 2026-06-30 05:59:09 UTC.
- **Location:** Evenfall Hall (1947, 706).
- **Player troop type:** Spearmen, **Advantage (+7% DMG)**.
- **Enemy troop type:** Cavalry, **Disadvantage (-7% DMG)**.
- **Result:** Victory.

Formation:

| Lane | Dragon | Level | End / Start troops | Affinity |
|---|---|---:|---:|---|
| Left | Tashix | 45 | 5,876 / 7,565 | No Bonus |
| Vanguard | Vaeldra | 36 | 5,948 / 7,192 | +20% Dragon Stats |
| Right | Zivern | 35 | 5,458 / 6,551 | No Bonus |

Totals:

| Side | Start | End | Losses | Removed % |
|---|---:|---:|---:|---:|
| Player | 21,308 | 17,282 | 4,026 | 18.89% lost |
| Enemy | 19,500 | 0 | 19,500 | 100% removed |

This won because the matchup was easy and the player had troop-type advantage. It should not be treated as a gold-standard Spearmen army because it had only **1/3 affinity coverage**.

## What Changed

### 1. Crimson is removed from Cavalry planning

Do not use **Crimson / Seasmoke / Feskar** as a Cavalry gold-standard shell. Crimson received **No Bonus** in the Cavalry report.

Corrected Cavalry direction:

- **Caraxes / Seasmoke / Feskar** if Caraxes is available.
- **Shadowsong / Seasmoke / Feskar** if Caraxes is reserved for Spearmen.

The preferred vanguard remains **Seasmoke** because the army needs center control and survivability.

### 2. Zivern is removed from Spearmen planning

Do not use **Tashix / Vaeldra / Zivern** as a Spearmen gold-standard shell. Only Vaeldra received the +20% dragon-stat bonus.

Corrected Spearmen direction:

- **Syrax / Vaeldra / Caraxes** for the no-blue Spearmen test.
- **Syrax / Vaeldra / Shadowrend** only if the no-blue rule is relaxed.

Vaeldra remains the best center candidate in this shell because she is the only confirmed Spearmen affinity piece in the report and brings Taunt/self-survival value.

### 3. Troop-type advantage is not the same as dragon affinity

The Spearmen report won with **1/3 affinity** because Spearmen had advantage into Cavalry. That is useful for farming, but it does not make the army a complete engine.

The Cavalry report lost the matchup because Cavalry went into Spearmen disadvantage and the army also lacked complete affinity.

## How To Improve

### Cavalry improvement

Stop using Crimson in Cavalry.

Use this order:

1. **Caraxes / Seasmoke / Feskar** — best no-blue Cavalry correction if Caraxes is free.
2. **Shadowsong / Seasmoke / Feskar** — acceptable no-blue reserve if Caraxes is needed elsewhere.
3. Do not send Cavalry into Spearmen unless you are testing limits.

### Spearmen improvement

Stop using Tashix and Zivern in Spearmen unless the goal is only a disposable/farming test.

Use this order:

1. **Syrax / Vaeldra / Caraxes** — best no-blue Spearmen correction.
2. **Rhysarion / Vaeldra / Caraxes** — stronger if no-duplicate planning allows Rhysarion to leave the Shieldbearer army.
3. **Syrax / Vaeldra / Shadowrend** — useful only if blue dragons are allowed.

### Resource priority

Do not spend premium resources trying to force incomplete-affinity armies. Build the dragons that turn these into real engines:

- **Caraxes** for Cavalry/Spearmen flexibility.
- **Vaeldra** because she is close to 3★ and can anchor Spearmen tests.
- **Seasmoke** because it remains the best no-blue Cavalry center.
- **Syrax** to unlock the future Archer/Spearmen support engine.

## Strategic Takeaway

These reports are good because they corrected bad assumptions.

The winning Spearmen report is not proof that Tashix / Vaeldra / Zivern is gold standard. The losing Cavalry report is not proof that Seasmoke / Feskar are weak. The real lesson is simpler:

**Do not build gold-standard armies from unverified affinity icons. Report-card bonuses are the stronger evidence.**

## Linked Data

- `battle-logs/2026-06-30-black-goat-level-35-affinity-correction-reports.json`
- `dragons/crimson.json`
- `dragons/zivern.json`
