"""Replay development icon benchmark from the 40 original local screenshots."""
import argparse
import hashlib
import json
from pathlib import Path
from scripts.dragon_analyzer.icons import read_icon_candidate

ROOT=Path(__file__).resolve().parents[1]


def evaluate(images):
    fixture=json.loads((ROOT/"quality/fixtures/icons-dev-2026-11-26.json").read_text())
    manifest=[]
    metrics={k:dict(correct=0,wrong=0,abstain=0) for k in ("habit_slots","affinity_slots")}
    errors=[]
    for row in fixture["rows"]:
        actual=read_icon_candidate(images/row["source"])
        manifest.append(row["source"]+":"+actual["source_sha256"]+"\n")
        for k in metrics:
            if len(actual[k])!=len(row[k]):
                raise ValueError("slot census mismatch")
            for i,(got,want) in enumerate(zip(actual[k],row[k])):
                state="abstain" if got is None else "correct" if got==want else "wrong"
                metrics[k][state]+=1
                if state!="correct":
                    errors.append(dict(source=row["source"],field=k,slot=i,expected=want,actual=got))
    if hashlib.sha256("".join(manifest).encode()).hexdigest()!=fixture["manifest_sha256"]:
        raise ValueError("image manifest mismatch")
    return {"partition":fixture["partition"],"metrics":metrics,"errors":errors,
            "release_accepted":False}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images",type=Path,required=True)
    print(json.dumps(evaluate(parser.parse_args().images),indent=2))
