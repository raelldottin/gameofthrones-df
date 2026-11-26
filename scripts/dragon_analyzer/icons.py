"""Development-only icon recognition using fixed binary silhouette prototypes."""
import hashlib
import io
from pathlib import Path
import numpy as np
from PIL import Image
from .visual import normalized

UNKNOWN=None
CENTERS=(663,757,849,942,1034)
# Derived packed binary feature masks, not original screenshots or dragon identities.
def unpack(value,shape):
    return np.unpackbits(np.frombuffer(bytes.fromhex(value),dtype=np.uint8),
                         count=shape[0]*shape[1]).reshape(shape).astype(bool)

DIGITS={k:unpack(v,(16,13)) for k,v in {
1:'0000000380040020010008004002001000800400f80000000000',
2:'00001803e031000c004006006006006002003001fc0000000000',
3:'00003803e001000800401c007000800604303100f00000000000',
4:'000000006007003802c03601301980fe00700300180000000000',
5:'00040003e010008005803e011800400200303100f80000000000',
}.items()}
AFFINITIES={k:unpack(v,(23,25)) for k,v in {
'Cavalry':'000320003fe000fff001fff803fffe03ffff83ffffe1fffff8fffffe7fffffbfffffdffffffffc3ffffc00fbfe0039fe0000ff00007f80003fc0001fe0000fe00000500000080000',
'Shieldbearers':'e000003800000e600003c1e000f7fe00ffffc07ffff007fff803fffc01fffe00ffff007fff803fffc01fffe007fff003fff001fff8007ffc001fff0007ffc001fbe00038f800001c',
'Siege':'0000000000000000180c001c07000f07e00f83f807e1fe03f0ffc3fc7ff1b6087fdb001fccc007e660f0ff38fc3ffeffffff7fbfffb7c03fdfe007e7e001f1e00078000000000000',
'Archers':'08000007e000007c000007000001e0000079e0001cf00007f00001f80003e00003f800079c007f06007e03001e01800f004003002000001000000800000400000600000200000100',
'Spearmen':'00000e00001f00001f00003f00003f80003f80003f80003f80003f80001f80000f80000fc0000fc0001f00001f00001f00001f00001f80000780000f800007000003000000',
}.items()}
LOCKS=[unpack(v,(18,27)) for v in (
'0000000000000000fe00007ff0001e0f0007007000c006003800e006000c00c00180180030030006006000e00c001801800300fffff839e3ff87fffff0',
'fffffffffffffffffffffffffffffe0fffff007fffc007fff000fffeff0ffed7f1ffdbff3ffb3fe7ff67fefe08ff9dc19ff3b8fffffa33c7ff87ffff70',
'0000000000000000fc00007fe0001e0e0007006000c006003000c006000c00c00180180030030006006000c008001801800300fffff03ba3ff87fffff0',
'fff00fffff01fffffe1ffffff3ffff07bffb803bfee003bf980077e3000e3c6000c78c00186180030c30006184000c20c001847ffffc9db3ffd7fffff8',
)]


def central(mask):
    return mask[1:-2,2:-2] if mask.shape==(16,13) else mask


def similarity(a,b):
    a,b=central(a),central(b)
    if a.shape!=b.shape:
        raise ValueError("feature geometry mismatch")
    best=0.0
    for y in (-1,0,1):
        for x in (-1,0,1):
            c=np.roll(b,(y,x),axis=(0,1))
            if y==1:c[0,:]=0
            if y==-1:c[-1,:]=0
            if x==1:c[:,0]=0
            if x==-1:c[:,-1]=0
            best=max(best,2*(a&c).sum()/max(1,a.sum()+c.sum()))
    return float(best)


def choose(p,templates):
    scores=sorted(((similarity(p,v),k) for k,v in templates.items()),reverse=True)
    if len(scores)<2:
        raise ValueError("need competing prototypes")
    return scores[0][1] if scores[0][0]>=.72 and scores[0][0]-scores[1][0]>=.10 else UNKNOWN


def digit_mask(im,j):
    x=CENTERS[j]
    return np.min(im[659:675,x-6:x+7],axis=2)>145


def lock_mask(im,j):
    x=CENTERS[j]
    p=im[603:621,x-13:x+14].astype(float)
    return (np.min(p,axis=2)>65)&((np.max(p,axis=2)-np.min(p,axis=2))<35)


def icon_mask(im,j):
    x=1155+72*j
    r,g,b=im[133:156,x-12:x+13].astype(float).transpose(2,0,1)
    return (r>110)&(g>75)&(r>1.15*b)&(g>1.05*b)


def direction(im,j):
    x=1183+72*j
    r,g,b=im[132:155,x-10:x+11].astype(float).transpose(2,0,1)
    return ((g>60)&(g>1.5*r)&(g>1.5*b)).mean(),((r>65)&(r>1.5*g)&(r>1.5*b)).mean()


def habit_level(digit,lock):
    if central(digit).sum()<=2:
        return 0 if max(similarity(lock,t) for t in LOCKS)>=.70 else UNKNOWN
    return choose(digit,DIGITS)


def direction_class(g,r,icon_pixels):
    if max(g,r)<.08 and icon_pixels<10:
        return "empty"
    if max(g,r)>.35 and min(g,r)<.08:
        return "+" if g>r else "-"
    return UNKNOWN


def read_icons(image):
    im=np.asarray(normalized(image))
    affinities=[]
    for j in range(4):
        mask=icon_mask(im,j)
        g,r=direction(im,j)
        sign=direction_class(g,r,mask.sum())
        if sign in ("+","-"):
            name=choose(mask,AFFINITIES)
            affinities.append(sign+name if name else UNKNOWN)
        else:
            affinities.append(sign)
    # Require a recognizable positive first badge before treating layout as supported.
    if not isinstance(affinities[0],str) or not affinities[0].startswith("+"):
        return {"status":"unsupported_or_ambiguous","habit_slots":[UNKNOWN]*5,
                "affinity_slots":[UNKNOWN]*4}
    levels=[habit_level(digit_mask(im,j),lock_mask(im,j)) for j in range(5)]
    return {"status":"unverified_candidate","habit_slots":levels,"affinity_slots":affinities}


def read_icon_candidate(path):
    data=Path(path).read_bytes()
    if not data or len(data)>25_000_000:
        raise ValueError("empty or oversized screenshot")
    with Image.open(io.BytesIO(data)) as image:
        if image.width*image.height>25_000_000:
            raise ValueError("oversized image dimensions")
        return {**read_icons(image),"reader_version":"icons-dev-v1",
                "source_sha256":hashlib.sha256(data).hexdigest()}
