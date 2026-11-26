"""Fail-closed observation boundary; no claim of validated screenshot extraction."""
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Protocol

from .config import IMAGE_EXTENSIONS, OUTPUT_DIR
from .models import ArmyComposition, DragonData


class ProfileReader(Protocol):
    """A verified adapter reads a selected Dragon Pit profile or raises."""
    def __call__(self, path: Path) -> DragonData: ...


def unsupported_reader(path: Path) -> DragonData:
    raise RuntimeError("No validated profile reader configured; screenshot extraction is unsupported")


def _safe_filename(value: str) -> str:
    if not value or value in {".", ".."} or Path(value).name != value or "\\" in value:
        raise ValueError("Expected a single filename, not a path")
    return value


def _atomic_json(path: Path, data: dict, *, immutable: bool = False) -> None:
    """Write complete JSON; immutable evidence cannot be replaced, even on a race."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n"
    fd, name = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if immutable:
            try:
                os.link(temp, path)
            except FileExistsError:
                if path.read_text(encoding="utf-8") != payload:
                    raise RuntimeError("Observation conflict: existing evidence differs")
        else:
            os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


class DragonAnalyzer:
    def __init__(self, output_dir: Path | None = None,
                 *, profile_reader: ProfileReader | None = None):
        self.output_dir = Path(output_dir) if output_dir is not None else OUTPUT_DIR
        self.profile_reader = profile_reader if profile_reader is not None else unsupported_reader

    def analyze_screenshot(self, image_path: Path) -> DragonData:
        path = Path(image_path)
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError("Unsupported screenshot extension")
        original = path.read_bytes()
        if not original:
            raise ValueError("Empty screenshot")
        digest = hashlib.sha256(original).hexdigest()
        observed = self.profile_reader(path)
        if not isinstance(observed, DragonData):
            raise TypeError("Profile reader must return DragonData")
        # Revalidate serialized output even if the adapter constructed an unchecked model.
        observed = DragonData.model_validate_json(observed.model_dump_json())
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise RuntimeError("Screenshot changed during extraction")
        record = {
            "kind": "unreconciled_profile_observation",
            "source_sha256": digest,
            "observation": observed.model_dump(mode="json"),
        }
        _atomic_json(self.output_dir / "observations" / f"{digest}.json", record,
                     immutable=True)
        return observed

    def batch_analyze(self, directory: Path, pattern: str = "IMG_*") -> list[DragonData]:
        paths = sorted(p for p in Path(directory).glob(pattern)
                       if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
        if not paths:
            raise ValueError("no screenshots matched")
        # Fail visibly at first rejected observation; completed evidence is retained.
        return [self.analyze_screenshot(p) for p in paths]

    def save_analysis(self, data: dict, filename: str) -> Path:
        path = self.output_dir / "analysis" / _safe_filename(filename)
        _atomic_json(path, data)
        return path

    def load_dragon_data(self, name: str) -> DragonData | None:
        path = self.output_dir / "dragons" / _safe_filename(name.lower().replace(" ", "_") + ".json")
        if not path.exists():
            return None
        return DragonData.model_validate_json(path.read_text(encoding="utf-8"))

    def export_army_compositions(self, armies: list[ArmyComposition] | None = None) -> Path:
        if armies is None or not armies:
            raise ValueError("explicit army data required")
        return self.save_analysis({"armies": [a.model_dump(mode="json") for a in armies]},
                                  "army_compositions.json")


def create_analyzer(output_dir: Path | None = None,
                    *, profile_reader: ProfileReader | None = None) -> DragonAnalyzer:
    return DragonAnalyzer(output_dir, profile_reader=profile_reader)
