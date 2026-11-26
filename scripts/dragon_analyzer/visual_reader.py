"""Read-only Q3 candidate interface; visual guesses never promote canonical state."""
import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image
from .panel import parse_panel
from .panel_reader import prepare_panel
from .visual import BOXES, CONFIG, crop_field, merge_fields, read_stars


def engine(image, config):
    import pytesseract
    return pytesseract.image_to_string(image, lang="eng", config=config)


def read_visual_candidate(path, known_names, *, text_reader=engine):
    data=Path(path).read_bytes()
    if not data or len(data)>25_000_000:
        raise ValueError("Empty or oversized screenshot")
    names=tuple(known_names)
    with Image.open(io.BytesIO(data)) as image:
        if image.width*image.height>25_000_000:
            raise ValueError("Oversized image dimensions")
        baseline=text_reader(prepare_panel(image),"--psm 6")
        texts={k:text_reader(crop_field(image,k),CONFIG[k]) for k in BOXES}
        if not isinstance(baseline,str) or not all(isinstance(v,str) for v in texts.values()):
            raise TypeError("OCR reader must return text")
        fields=merge_fields(parse_panel(baseline,names),texts,read_stars(image),names)
    return {"status":"unverified_candidate","source_sha256":hashlib.sha256(data).hexdigest(),
            "reader_version":"panel-visual-v1","fields":fields}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image",type=Path)
    parser.add_argument("--catalog",type=Path,required=True)
    args=parser.parse_args()
    names=json.loads(args.catalog.read_text(encoding="utf-8"))
    if not isinstance(names,list) or not all(isinstance(n,str) and n for n in names):
        parser.error("catalog must contain a JSON list of nonempty names")
    print(json.dumps(read_visual_candidate(args.image,names),indent=2))


if __name__=="__main__":
    main()
