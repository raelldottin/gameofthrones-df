"""Reproduce the development-only real-image benchmark from local screenshots."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.dragon_analyzer.panel import FIELDS, parse_panel
from scripts.dragon_analyzer.panel_reader import prepare_panel


def main():
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument("--images", type=Path, required=True)
    args = arg.parse_args()
    fixture = json.loads((ROOT / "quality/fixtures/panel-dev-2026-11-26.json").read_text())
    rows = fixture["rows"]
    names = sorted({r["expected"]["name"] for r in rows})
    entries = []
    with tempfile.TemporaryDirectory(prefix="dragonfire-panels-") as tmp:
        root = Path(tmp)
        crops = []
        for row in rows:
            path = args.images / row["source"]
            entries.append(path.name + ":" + hashlib.sha256(path.read_bytes()).hexdigest() + "\n")
            with Image.open(path) as image:
                crop = prepare_panel(image)
                target = root / (path.stem + ".png")
                crop.save(target)
                crops.append(str(target))
        digest = hashlib.sha256("".join(entries).encode()).hexdigest()
        if digest != fixture["manifest_sha256"]:
            raise ValueError("Image manifest mismatch: do not score against different images")
        listing = root / "files.txt"
        listing.write_text("\n".join(crops) + "\n")
        subprocess.run(["tesseract", str(listing), str(root / "ocr"), "--psm", "6", "-l", "eng"],
                       check=True, timeout=300)
        raw = (root / "ocr.txt").read_bytes()
        pages = raw.decode().split("\f")
        if pages and pages[-1] == "":
            pages.pop()
        if len(pages) != len(rows):
            raise ValueError("OCR page count mismatch; refuse to shift labels")
    metrics = {k: dict(correct=0, wrong=0, abstain=0) for k in FIELDS}
    wrong = []
    for row, page in zip(rows, pages):
        actual = parse_panel(page, names)
        for k in FIELDS:
            value, expected = actual[k], row["expected"][k]
            state = "abstain" if value is None else "correct" if value == expected else "wrong"
            metrics[k][state] += 1
            if state == "wrong":
                wrong.append(dict(source=row["source"], field=k, expected=expected, actual=value))
    totals = {k: sum(v[k] for v in metrics.values()) for k in ("correct", "wrong", "abstain")}
    print(json.dumps({"partition": fixture["partition"], "manifest_sha256": digest,
                      "raw_ocr_sha256": hashlib.sha256(raw).hexdigest(),
                      "metrics": metrics, "totals": totals, "wrong_values": wrong}, indent=2))
    # Do not pass a release gate on development data, regardless of accuracy.


if __name__ == "__main__":
    main()
