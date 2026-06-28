# Spearmen Position Tests — June 28, 2026

Source: battle report screenshots supplied June 28, 2026.

## Purpose

Test the Spearmen gold-standard army positions while keeping the safe vanguard rule intact.

The center should not move first. These reports keep **Dawnseeker vanguard** and compare flank behavior around it.

## Test 1 — Crimson / Dawnseeker / Jagadrix

- **Result:** Victory.
- **Enemy:** Aurochs, Level 30.
- **Location:** Stone Hedge (1258, 1458).
- **Time:** 2026-06-28 01:05:48 UTC.
- **Matchup:** Spearmen advantage into Cavalry, **+7% damage**.
- **Affinity:** 3/3, +20% to dragon stats.
- **Final troops:** 21,228 / 21,770.
- **Troop losses:** 542.
- **Enemy troops removed:** 8,700.
- **Efficiency:** 16.05 enemy troops removed per player troop lost.

| Lane | Dragon | Level | End troops | Losses | Total kills | Command | Command kills | Recovery | Basic kills |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| Left | Crimson | 39 | 6,418 / 6,700 | 282 | 3,942 | Bloodscale Terror x2 | 1,418 | 0 | 2,524 |
| Vanguard | Dawnseeker | 43 | 6,920 / 7,105 | 185 | 2,235 | Radiant Wings x5 | 660 | 288 | 1,575 |
| Right | Jagadrix | 43 | 7,890 / 7,965 | 75 | 2,523 | Cunning Whispers x3 | 661 | 0 | 1,862 |

## Test 2 — Jagadrix / Dawnseeker / Crimson

- **Result:** Victory.
- **Enemy:** Outlaws, Level 30.
- **Location:** Acorn Hall (1174, 1410).
- **Time:** 2026-06-28 00:15:13 UTC.
- **Matchup:** Spearmen disadvantage into Archers, **-7% damage**.
- **Affinity:** 3/3, +20% to dragon stats.
- **Final troops:** 20,740 / 21,668.
- **Troop losses:** 928.
- **Enemy troops removed:** 8,700.
- **Efficiency:** 9.38 enemy troops removed per player troop lost.

| Lane | Dragon | Level | End troops | Losses | Total kills | Command | Command kills | Recovery | Basic kills |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| Left | Jagadrix | 43 | 7,774 / 7,965 | 191 | 2,954 | Cunning Whispers x5 | 947 | 0 | 2,007 |
| Vanguard | Dawnseeker | 42 | 6,877 / 7,003 | 126 | 2,219 | Radiant Wings x6 | 715 | 298 | 1,504 |
| Right | Crimson | 39 | 6,089 / 6,700 | 611 | 3,527 | Bloodscale Terror x2 | 1,167 | 0 | 2,360 |

## Comparison

These two reports are useful, but they are **not a clean A/B test**. Test 1 had troop advantage into Cavalry. Test 2 had troop disadvantage into Archers. The enemy type and matchup changed, so position alone does not explain the difference.

| Formation | Matchup | Player losses | Enemy removed | Efficiency | Main signal |
|---|---|---:|---:|---:|---|
| Crimson / Dawnseeker / Jagadrix | Advantage | 542 | 8,700 | 16.05 | Cleaner farming result |
| Jagadrix / Dawnseeker / Crimson | Disadvantage | 928 | 8,700 | 9.38 | Still won, but Crimson took heavy right-flank losses |

## Swap Analysis

### Dawnseeker stays vanguard

Dawnseeker was safe in both reports. It lost **185** troops in the advantage fight and **126** troops in the disadvantage fight while producing recovery through Radiant Wings in both cases. Do not move Dawnseeker out of center yet.

### Crimson is the primary finisher

Crimson led total kills in both reports:

- **3,942 kills** from the left flank in the advantage test.
- **3,527 kills** from the right flank in the disadvantage test.

This confirms Crimson is the Spearmen engine's primary finisher. The question is not whether Crimson belongs in the army; it is which flank keeps Crimson productive without creating unnecessary losses.

### Jagadrix is safer as the right-side partner in the favorable test

In the favorable matchup, Jagadrix on the right lost only **75** troops while still contributing **2,523 kills**. That is a strong support-finisher profile.

In the disadvantage test, Jagadrix on the left produced **2,954 kills** and lost **191** troops. That is still solid, but not enough to prove left is better because the matchup was worse.

### Crimson right can be expensive into bad matchups

In the disadvantage test, Crimson right produced **3,527 kills**, but lost **611** troops. That does not mean Crimson-right is bad in all cases, but it does show that Crimson can become the damage sponge when Spearmen are sent into Archers.

## Current Position Recommendation

For the Spearmen gold-standard army, the best current farming orientation to retest is:

**Crimson left / Dawnseeker vanguard / Jagadrix right**

Reasons:

1. Crimson led kills from the left flank.
2. Dawnseeker stayed safe in center.
3. Jagadrix stayed very safe on the right while still contributing damage.
4. The total-loss result was much cleaner in the favorable matchup.

However, because the matchups were different, this should be treated as a **current preference**, not a final proof.

## Next Clean Test

Run both formations against the same enemy type and level:

1. **Crimson / Dawnseeker / Jagadrix**
2. **Jagadrix / Dawnseeker / Crimson**

Use the same enemy troop type if possible. Compare:

- total player losses;
- Crimson losses;
- Jagadrix losses;
- command kills;
- basic attack kills;
- recovery from Dawnseeker;
- whether one flank consistently draws more enemy pressure.

## Linked Data

- `battle-logs/2026-06-28-spearmen-position-tests-level-30.json`
- `analysis/GOLD_STANDARD_ARMY_CANDIDATES_2026-06-27.md`
