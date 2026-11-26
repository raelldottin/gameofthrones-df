"""Geometry-specific visual candidate fields; never authoritative observations."""
import re
import numpy as np
from PIL import Image, ImageOps

BOXES = {'name': (1134,52,1420,87), 'level': (1144,195,1171,225),
         'xp': (1177,184,1415,215), 'power': (1180,262,1410,298),
         'relic': (1181,557,1408,594)}
CONFIG = {'name':'--psm 7', 'level':'--psm 7 -c tessedit_char_whitelist=0123456789',
          'xp':'--psm 7', 'power':'--psm 7 -c tessedit_char_whitelist=0123456789,/',
          'relic':'--psm 7 -c tessedit_char_whitelist=0123456789,/'}
NUMBER = r'(?:\d{1,3}(?:,\d{3})+|\d+)'

def normalized(image):
    w,h=image.size
    if w<768 or h<350 or abs(w/h/(1536/709)-1)>.02:
        raise ValueError('Unsupported Dragon Pit screenshot geometry')
    return image.convert('RGB').resize((1536,709))

def crop_field(image, kind):
    a=np.asarray(normalized(image).crop(BOXES[kind]))
    gray=np.max(a,axis=2) if kind=='name' else np.min(a,axis=2)
    mask=Image.fromarray(np.uint8(np.where(gray>(100 if kind=='name' else 150),0,255)))
    return ImageOps.expand(mask.resize((gray.shape[1]*3,gray.shape[0]*3)),border=16,fill=255)

def classify_star(patch):
    r,g,b=np.asarray(patch,dtype=float).transpose(2,0,1)
    gold=((r>130)&(g>75)&(r>b*1.5)&(g>b*1.3)).mean()
    red=((r>150)&(r>g*1.65)&(r>b*1.3)).mean()
    empty=((b>r*1.15)&(b>35)&(g>r*1.05)).mean()
    if red>=.5 and gold>=.2: return 2
    if gold>=.30 and red<.08: return 1
    if gold<.03 and red<.03 and .045<=empty<=.25: return 0
    return None

def rank_from_slots(slots):
    if len(slots)!=5 or any(x not in (0,1,2) for x in slots): return None
    if slots!=sorted(slots,reverse=True) or (2 in slots and 0 in slots): return None
    return sum(slots) or None

def read_stars(image):
    a=np.asarray(normalized(image))
    return rank_from_slots([classify_star(a[502:532,x-15:x+15]) for x in (1164,1220,1277,1334,1391)])

def merge_fields(baseline, texts, stars, known_names):
    out=dict(baseline)
    names={n.casefold():n for n in known_names}
    out['name']=names.get(texts['name'].strip().casefold())
    level=texts['level'].strip()
    out['level']=int(level) if re.fullmatch(r'[1-9]\d{0,2}',level) else None
    out['stars']=stars
    # Use isolated stats only when the whole-panel parser abstained; no correction by expected values.
    xp=re.fullmatch('('+NUMBER+r')\s*/\s*(\d+(?:\.\d+)?[KkMm]?)',texts['xp'].strip())
    if out['xp_current'] is None and out['xp_required_display'] is None and xp:
        out['xp_current']=int(xp[1].replace(',',''));out['xp_required_display']=xp[2].upper()
    power=texts['power'].strip()
    if out['power'] is None and re.fullmatch(NUMBER,power): out['power']=int(power.replace(',',''))
    relic=re.fullmatch('('+NUMBER+r')\s*/\s*('+NUMBER+')',texts['relic'].strip())
    if out['relic_current'] is None and out['relic_required'] is None and relic:
        n,d=(int(v.replace(',','')) for v in relic.groups())
        if 0<=n<d:out['relic_current'],out['relic_required']=n,d
    return out
