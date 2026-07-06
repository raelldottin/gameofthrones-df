# Official Dragon Roster Validation — 2026-07-06

Source: https://gotdragonfire.com/dragons/

Purpose: validate the repository's dragon identity fields against the official public Dragonfire dragon roster.

Scope:
- Validated: `name`, `rarity`, and `class`/official `Breed`.
- Not validated by this source: combat commands, habits, stats, levels, stars, troop affinities, troop capacity, power, relic progress, and in-game ownership state.
- The official public roster/profile pages expose identity/lore data. Gameplay mechanics still require in-game screenshots, official news posts, or battle report evidence.

## Summary

- Official roster count checked from the public Dragons page: 28 dragons.
- Repository coverage after this validation: 28 official roster dragons present under `dragons/`.
- Added missing official roster file: `dragons/vesper.json`.
- Existing identity mismatches found in checked files: none for the official `rarity` and `Breed` fields.
- Out-of-roster preview/news dragon currently in repo: `dragons/tessarion.json`. Tessarion is sourced from the official news post, but is not listed on the public Dragons roster page as of this validation.

## Official roster identity table

| Dragon | Official rarity | Official breed | Repo status | Validation result |
|---|---|---|---|---|
| Syrax | Legendary | Sentinel | Present | Matches |
| Vhagar | Legendary | Warrior | Present | Matches |
| Caraxes | Legendary | Hunter | Present | Matches |
| Seasmoke | Legendary | Champion | Present | Matches |
| Solstryker | Rare | Champion | Present | Matches |
| Crimson | Legendary | Hunter | Present | Matches |
| Kalspire | Legendary | Champion | Present | Matches |
| Malachite | Legendary | Sentinel | Present | Matches |
| Venator | Legendary | Warrior | Present | Matches |
| Daemoros | Epic | Warrior | Present | Matches |
| Feskar | Epic | Champion | Present | Matches |
| Rhysarion | Epic | Champion | Present | Matches |
| Shadowsong | Epic | Hunter | Present | Matches |
| Tashix | Epic | Hunter | Present | Matches |
| Vaeldra | Epic | Warrior | Present | Matches |
| Velar | Epic | Sentinel | Present | Matches |
| Zivern | Epic | Sentinel | Present | Matches |
| Antares | Rare | Hunter | Present | Matches |
| Shimmer | Rare | Sentinel | Present | Matches |
| Jagadrix | Rare | Hunter | Present | Matches |
| Bevlorin | Rare | Champion | Present | Matches |
| Shadowrend | Rare | Warrior | Present | Matches |
| Thunderstrike | Rare | Warrior | Present | Matches |
| Vesper | Rare | Sentinel | Added | Matches official profile |
| Arulix | Rare | Champion | Present | Matches |
| Nyrena | Rare | Champion | Present | Matches |
| Dawnseeker | Rare | Sentinel | Present | Matches |
| Arrax | Rare | Warrior | Present | Matches |

## Validation notes

### Public roster limitations

The official Dragons page confirms each listed dragon's display name, rarity, and Breed. It does not expose the in-game Command text, Habit text, numeric effect values, star thresholds, stats, troop affinities, or ownership-specific data. Those fields remain screenshot- or official-news-derived.

### Vesper

`dragons/vesper.json` was missing before this pass. The official Vesper profile confirms:

- Name: Vesper
- Rarity: Rare
- Breed: Sentinel
- Lore subtitle: The Silent Shadow

The new file intentionally records only official identity/lore fields and leaves gameplay mechanics as unknown until an in-game screenshot or official mechanics source is available.

### Tessarion

`dragons/tessarion.json` exists from the official news post `https://news.gotdragonfire.com/introducing-tessarion/`. Tessarion should remain marked as `official_preview_details_only` unless/until the public Dragons roster page is updated to include her.

## Follow-up checks

1. Capture an in-game Vesper Dragon Pit screenshot to fill command, habits, stats, troop capacity, power, stars, level, and troop affinity data.
2. Re-check the official Dragons page after new releases because the roster page may lag official news posts.
3. Keep identity fields separate from screenshot-derived gameplay fields. Official roster/profile pages validate identity; in-game screenshots validate current player-owned combat data.
