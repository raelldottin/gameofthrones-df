"""Read-only candidate preview; never promotes evidence to the canonical roster."""
import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image, ImageOps

from .panel import parse_panel


def prepare_panel(image):
    w, h = image.size
    if w < 768 or h < 350 or abs(w / h / (1536 / 709) - 1) > 0.02:
        raise ValueError("Unsupported Dragon Pit screenshot geometry")
    box = tuple(round(v * scale) for v, scale in zip(
        (1128, 45, 1435, 630), (w / 1536, h / 709, w / 1536, h / 709)))
    panel = image.convert("L").crop(box).resize((614, 1170))
    return ImageOps.invert(panel.point(lambda x: 255 if x > 145 else 0))


def tesseract_text(image):
    import pytesseract
    return pytesseract.image_to_string(image, lang="eng", config="--psm 6")


def read_candidate(path, known_names, *, text_reader=tesseract_text):
    data = Path(path).read_bytes()
    if not data or len(data) > 25_000_000:
        raise ValueError("Empty or oversized screenshot")
    with Image.open(io.BytesIO(data)) as image:
        if image.width * image.height > 25_000_000:
            raise ValueError("Oversized image dimensions")
        prepared = prepare_panel(image)
    text = text_reader(prepared)
    if not isinstance(text, str):
        raise TypeError("Text adapter must return str")
    return {
        "status": "unverified_candidate",
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "reader_version": "panel-v0",
        "fields": parse_panel(text, known_names),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--catalog", type=Path, required=True,
                        help="JSON list of recognized dragon names")
    args = parser.parse_args()
    names = json.loads(args.catalog.read_text(encoding="utf-8"))
    if not isinstance(names, list) or not all(isinstance(n, str) and n for n in names):
        parser.error("catalog must contain a JSON list of nonempty names")
    print(json.dumps(read_candidate(args.image, names), indent=2))


if __name__ == "__main__":
    main()
