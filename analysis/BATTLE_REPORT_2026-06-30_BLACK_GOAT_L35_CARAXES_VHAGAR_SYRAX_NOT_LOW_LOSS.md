# Battle Report — Black Goat Level 35, Caraxes / Vhagar / Syrax

Source: report screenshot supplied June 30, 2026.

## Summary

- **Report:** Victory Black Goat, Level 35.
- **Location:** Haystack Hall (1774, 846).
- **Time:** 2026-06-30 06:55:22 UTC.
- **Result:** Victory.
- **Displayed difficulty:** Easy.
- **Player side:** jadakiss [WILDFIREE], Archers.
- **Enemy side:** Black Goat, Level 35, Shieldbearers.

This was a bad matchup for low-loss testing:

- Player Archers had **Disadvantage (-7% DMG)**.
- Enemy Shieldbearers had **Advantage (+7% DMG)**.
- Only **2/3 dragon affinity** was active.
- Caraxes showed **No Bonus**.

The tested army was:

**Caraxes left / Vhagar vanguard / Syrax right**

The player started at **21,377** troops and ended at **16,124**. The enemy started at **19,500** and was fully defeated.

## Formation

| Side | Lane | Dragon | Level | End / Start troops | Losses | Affinity |
|---|---|---:|---:|---:|---|
| Player | Left | Caraxes | 35 | 4,744 / 6,551 | 1,807 | No Bonus |
| Player | Vanguard | Vhagar | 44 | 5,346 / 7,464 | 2,118 | +20% Dragon Stats |
| Player | Right | Syrax | 43 | 6,034 / 7,362 | 1,328 | +20% Dragon Stats |
| Enemy | Left | Black Goat | 35 | 0 / 6,500 | 6,500 | No Bonus |
| Enemy | Vanguard | Black Goat | 35 | 0 / 6,500 | 6,500 | No Bonus |
| Enemy | Right | Black Goat | 35 | 0 / 6,500 | 6,500 | No Bonus |

## Derived Result

| Metric | Value |
|---|---:|
| Player troops lost | 5,253 |
| Enemy troops removed | 19,500 |
| Player retention | 75.43% |
| Enemy removed | 100% |
| Enemy removed per player troop lost | 3.71x |
| Total affinity | 2/3 Archers |
| Low-loss classification | **Not low loss** |

This army won, but it is **not** a low-loss army.

## Why This Is Not Low Loss

The army had two problems at once:

1. **Bad troop matchup:** Archers were disadvantaged into Shieldbearers.
2. **Incomplete affinity:** Caraxes had **No Bonus**, so this was only a 2/3 Archer shell.

The loss pattern confirms the problem:

- **Vhagar lost 2,118** troops.
- **Caraxes lost 1,807** troops.
- **Syrax lost 1,328** troops.

Vhagar still did the center job, but the army paid too much to clear the fight. Losing **5,253** in an Easy report is not acceptable for the no-loss / little-loss goal.

## What This Proves

### 1. Caraxes should not be used in Archer planning

Caraxes showed **No Bonus** in an Archer formation. This supports the existing correction that Caraxes belongs in Spearmen/Cavalry planning, not Archer gold-standard planning.

### 2. Vhagar and Syrax are valid Archer-affinity pieces

Both Vhagar and Syrax showed **+20% to Dragon Stats**. They can remain in Archer planning.

### 3. Bad troop matchups destroy low-loss goals

Even with Vhagar center and an Easy label, the army lost over 5,000 troops because the troop-type matchup was bad and the affinity was incomplete.

## Recommendation

Do not use:

**Caraxes / Vhagar / Syrax — Archers**

as a low-loss army.

Correct the Archer slot to:

**Tashix left / Vhagar vanguard / Syrax right**

Reason:

1. Tashix has confirmed Archer affinity.
2. Vhagar has confirmed Archer affinity.
3. Syrax has confirmed Archer affinity.
4. Caraxes should be reserved for Spearmen or Cavalry tests.

But even with the corrected Archer army, do **not** send Archers into Shieldbearers when the goal is low losses.

## Strategic Takeaway

This report is useful because it gives a hard rule for the five-army low-loss plan:

**Low-loss farming requires both matchup discipline and 3/3 affinity.**

This army had neither. It cleared, but it should be removed from low-loss planning.

## Linked Data

- `battle-logs/2026-06-30-victory-black-goat-level-35-haystack-caraxes-vhagar-syrax-archers.json`
- `dragons/caraxes.json`
- `dragons/vhagar.json`
- `dragons/syrax.json`
