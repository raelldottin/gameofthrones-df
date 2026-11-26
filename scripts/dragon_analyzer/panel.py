"""Conservative Dragon Pit text candidate extraction; never canonical state."""
import re

CLASSES = ('Sentinel', 'Warrior', 'Hunter', 'Champion')
TRAITS = ('Stalwart', 'Ruthless', 'Willful', 'Nimble', 'Dominant', 'Cunning', 'Relentless', 'Volatile')
SPEEDS = ('Very Fast', 'Very Slow', 'Average', 'Fast', 'Slow')
STAGES = ('Hatchling', 'Whelp', 'Juvenile', 'Adult')
NUMBER = r'(?:\d{1,3}(?:,\d{3})+|\d+)'
FIELDS = ('name', 'dragon_class', 'temperament', 'speed', 'stage', 'level', 'xp_current', 'xp_required_display', 'power', 'capacity', 'energy_current', 'energy_maximum', 'relic_current', 'relic_required', 'stars')


def number(value):
    return int(value.replace(',', ''))


def choice(line, values):
    found = [v for v in values if re.search(r'(?<![A-Za-z])' + re.escape(v) + r'(?![A-Za-z])', line, re.I)]
    # Longer speed labels supersede their contained short labels.
    found = [v for v in found if not any(v != w and v in w for w in found)]
    return found[0] if len(found) == 1 else None


def unsigned_match(pattern, line):
    match = re.fullmatch(pattern, line)
    if match and re.search(r"[-−]\s*$", line[:match.start(1)]):
        return None
    return match


def parse_panel(text, known_names):
    out = dict.fromkeys(FIELDS)
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    if not lines:
        return out
    names = {n.casefold(): n for n in known_names}
    out['name'] = names.get(lines[0].casefold())
    type_rows = [i for i, x in enumerate(lines[:4]) if choice(x, CLASSES) and choice(x, TRAITS)]
    if len(type_rows) != 1:
        return out
    start = type_rows[0]
    out['dragon_class'] = choice(lines[start], CLASSES)
    out['temperament'] = choice(lines[start], TRAITS)
    stages = [(i, choice(x, STAGES)) for i, x in enumerate(lines) if choice(x, STAGES)]
    if len(stages) != 1:
        return out
    end, out['stage'] = stages[0]
    if end <= start:
        return out
    # Recognize the fixed contiguous five-row stats block immediately above stage.
    block = lines[end-5:end] if end-start >= 6 else []
    if len(block) == 5:
        xp = re.fullmatch(r'(\d{1,3})\s+(' + NUMBER + r')\s*/\s*(\d+(?:\.\d+)?[KkMm]?)', block[0])
        if xp and 1 <= int(xp[1]) <= 999:
            out['level'], out['xp_current'], out['xp_required_display'] = int(xp[1]), number(xp[2]), xp[3].upper()
        power = unsigned_match(r'[^\d]*(' + NUMBER + r')', block[1])
        capacity = unsigned_match(r'[^\d]*(' + NUMBER + r')\.0', block[2])
        energy = unsigned_match(r'[^\d]*(' + NUMBER + r')\s*/\s*(' + NUMBER + r')', block[3])
        if power:
            out['power'] = number(power[1])
        if capacity:
            out['capacity'] = number(capacity[1])
        if energy and number(energy[2]) > 0:
            out['energy_current'], out['energy_maximum'] = number(energy[1]), number(energy[2])
        out['speed'] = choice(block[4], SPEEDS)
    relics = [m for line in lines[end+1:] if (m := unsigned_match(r'[^\d]*(' + NUMBER + r')\s*/\s*(' + NUMBER + r')', line))]
    if len(relics) == 1 and 0 <= number(relics[0][1]) < number(relics[0][2]):
        out['relic_current'], out['relic_required'] = number(relics[0][1]), number(relics[0][2])
    # Star icons and habits are deliberately not inferred from relic thresholds.
    return out
