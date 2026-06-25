# Vermax — Spreading Blaze

Source: Dragon Pit screenshots supplied June 25, 2026.

## Discovery State

- **Dragon:** Vermax
- **Rarity:** Epic
- **Class:** Warrior
- **Discovery:** Not discovered
- **Relics shown:** 0
- **Command:** Spreading Blaze
- **Command progress:** 0 / 110
- **Speed:** Average
- **Energy:** 0
- **Displayed troop capacity:** 2,351.0
- **Displayed power:** 0

## Base Attributes Shown

| Attribute | Value |
|---|---:|
| Strength | 69.6 |
| Instinct | 52.2 |
| Intelligence | 49.9 |
| Initiative | 67.3 |

Strength is Vermax's highest damage-scaling attribute. Initiative is his second-highest displayed attribute.

## Active Command — Spreading Blaze

After each Basic Attack:

1. Deal **Physical Damage** to 1 enemy in the same lane at a **+50% Damage Rate**.
2. Make a **20% chance** roll to grant 1 stack of **Spreading Blaze** to 1 ally that deals Tactical Damage until the end of combat.
3. Repeat the Spreading Blaze chance if an enemy deals Fire Damage.

### Physical Damage

- Damage Rate: **+50%**.
- Increased by Vermax's **Strength**.
- Mitigated by the target's **Instinct**.

### Spreading Blaze Buff

- Each stack increases the target's **Tactical Damage Dealt by +2.5%**.
- Maximum: **10 stacks**.
- Maximum Tactical Damage increase: **+25%**.
- The command therefore benefits from a protected Tactical-damage ally that remains alive long enough to accumulate stacks.

## Habit Progression

All listed habits are currently locked because Vermax is not discovered and has 0 stars.

### 2★ — Trial by Flame

Reduces Fire Damage received as Vermax's troop capacity falls.

| Habit level | Below 75% capacity | Below 50% capacity | Below 25% capacity | Power |
|---:|---:|---:|---:|---:|
| 1 | -5% | -10% | -15% | 340 |
| 2 | -6% | -12% | -18% | 740 |
| 3 | -7% | -14% | -21% | 1,200 |
| 4 | -8.5% | -17% | -25.5% | 1,800 |
| 5 | -10% | -20% | -30% | 2,500 |

### 4★ — Reactive Instincts

At the start of combat, increase the Instinct and Initiative of the ally with the highest Instinct until the end of combat. Both effects are enhanced by Vermax's Strength.

| Habit level | Instinct | Initiative | Power |
|---:|---:|---:|---:|
| 1 | +18% | +9% | 340 |
| 2 | +21.6% | +10.8% | 740 |
| 3 | +25.2% | +12.6% | 1,200 |
| 4 | +30.6% | +15.3% | 1,800 |
| 5 | +36% | +18% | 2,500 |

### 6★ — Rallying Flame

At the start of combat:

- Chance to grant Vermax 1 stack of **Rallying Flame**, up to 4 stacks. Repeat the chance for each enemy that deals Fire Damage.
- Each Rallying Flame stack increases Vermax's **Physical Damage Dealt by +5%**, for a maximum of **+20%**.
- Chance to grant 1 stack of **Spreading Blaze** to 1 Tactical-damage ally, up to 10 stacks. Repeat the chance for each enemy that deals Fire Damage.
- Each Spreading Blaze stack increases the target's **Tactical Damage Dealt by +2.5%**, for a maximum of **+25%**.

| Habit level | Rallying Flame chance | Spreading Blaze chance | Power |
|---:|---:|---:|---:|
| 1 | 50% | 50% | 340 |
| 2 | 60% | 60% | 740 |
| 3 | 70% | 70% | 1,200 |
| 4 | 85% | 85% | 1,800 |
| 5 | 100% | 100% | 2,500 |

### 8★ — Dragon's Valor

At the start of combat, reduce Vermax's Damage Received and increase his Strength until the end of combat.

| Habit level | Damage Received | Strength | Power |
|---:|---:|---:|---:|
| 1 | -5% | +8.5% | 340 |
| 2 | -6% | +10.2% | 740 |
| 3 | -7% | +11.9% | 1,200 |
| 4 | -8.5% | +14.45% | 1,800 |
| 5 | -10% | +17% | 2,500 |

### 10★ — Unyielding Resolve

At the start of each round, Vermax has a chance to grant himself **Advantage (+15% Damage Dealt)** for 2 rounds.

- If Vermax is afflicted with **Weakened**, the chance is multiplied by 1.5.
- A successful activation while Weakened also removes Weakened.

| Habit level | Base Advantage chance | Chance while Weakened | Power |
|---:|---:|---:|---:|
| 1 | 20% | 30% | 340 |
| 2 | 26% | 39% | 790 |
| 3 | 32% | 48% | 1,400 |
| 4 | 40% | 60% | 2,100 |
| 5 | 50% | 75% | 3,100 |

## Development Breakpoints

- **Discovery:** unlocks Spreading Blaze and its repeatable Physical hit/Tactical buff loop.
- **2★:** adds conditional Fire mitigation.
- **4★:** adds a major Instinct and Initiative buff for the ally with the highest Instinct.
- **6★:** is the primary offensive breakpoint; Fire-dealing enemies can accelerate both Vermax's Physical scaling and his Tactical ally's Spreading Blaze stacks.
- **8★:** improves personal durability and Strength scaling.
- **10★:** adds recurring Advantage and a conditional Weakened cleanse.

## Composition Implication

Vermax is best treated as a protected flank support-damage hybrid rather than a vanguard. His current command rewards repeated Basic Attacks, survival, and pairing with a Tactical-damage ally. The planned Army 2 structure is:

- **Left flank:** Nyrena
- **Vanguard:** Velar
- **Right flank:** Vermax
- **Troop type:** Shieldbearers

In this structure, Nyrena is the intended Spreading Blaze recipient, Velar protects the formation, and Vermax replaces Arrax once discovered and sufficiently developed. The +25% Tactical ceiling is a maximum reached only at 10 stacks; it should not be treated as an immediate start-of-combat bonus.