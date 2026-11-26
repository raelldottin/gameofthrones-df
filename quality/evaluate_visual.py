"""Reproduce the visual-reader development benchmark; never a release gate."""
import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.dragon_analyzer.panel import FIELDS, parse_panel
from scripts.dragon_analyzer.panel_reader import prepare_panel
from scripts.dragon_analyzer.visual import BOXES, CONFIG, crop_field, merge_fields, read_stars


def main():
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument("--images",type=Path,required=True)
    args=arg.parse_args()
    fixture=json.loads((ROOT/"quality/fixtures/panel-dev-2026-11-26.json").read_text())
    rows=fixture["rows"]
    names=sorted({r["expected"]["name"] for r in rows})
    entries=[]
    ranks=[]
    with tempfile.TemporaryDirectory(prefix="dragonfire-visual-") as tmp:
        root=Path(tmp)
        keys=["panel",*BOXES]
        for k in keys:(root/k).mkdir()
        for row in rows:
            path=args.images/row["source"]
            entries.append(path.name+":"+hashlib.sha256(path.read_bytes()).hexdigest()+"\n")
            with Image.open(path) as im:
                prepare_panel(im).save(root/"panel"/(path.name+".png"))
                for k in BOXES:crop_field(im,k).save(root/k/(path.name+".png"))
                ranks.append(read_stars(im))
        digest=hashlib.sha256("".join(entries).encode()).hexdigest()
        if digest!=fixture["manifest_sha256"]:
            raise ValueError("Image manifest mismatch")
        pages={}
        raw_hashes={}
        for k in keys:
            listing=root/(k+".txt")
            listing.write_text("\n".join(str(root/k/(r["source"]+".png")) for r in rows)+"\n"))
            config="--psm 6" if k=="panel" else CONFIG[k]
            subprocess.run(["tesseract",str(listing),str(root/(k+"-ocr")),*shlex.split(config),"-l","eng"],
                           check=True,timeout=300)
            raw=(root/(k+"-ocr.txt")).read_bytes()
            raw_hashes[k]=hashlib.sha256(raw).hexdigest()
            pages[k]=raw.decode().split("\f")
            if pages[k] and pages[k][-1]=="":pages[k].pop()
            if len(pages[k])!=len(rows):
                raise ValueError("OCR page count mismatch; refuse to shift labels")
    metrics={k:dict(correct=0,wrong=0,abstain=0) for k in FIELDS}
    wrong=[]
    abstentions=[]
    for i,row in enumerate(rows):
        actual=merge_fields(parse_panel(pages["panel"][i],names),{k:pages[k][i] for k in BOXES},ranks[i],names)
        for k in FIELDS:
            value,expected=actual[k],row["expected"][k]
            state="abstain" if value is None else "correct" if value==expected else "wrong"
            metrics[k][state]+=1
            if state=="wrong":wrong.append(dict(source=row["source"],field=k,expected=expected,actual=value))
            if state=="abstain":abstentions.append(dict(source=row["source"],field=k))
    totals={k:sum(v[k] for v in metrics.values()) for k in ("correct","wrong","abstain")}
    print(json.dumps({"partition":fixture["partition"],"manifest_sha256":digest,
                      "raw_ocr_sha256":raw_hashes,"metrics":metrics,"totals":totals,
                      "wrong_values":wrong,"abstentions":abstentions},indent=2))


if __name__=="__main__":
    main()
