"""Behavioral contract for the legacy analyzer boundary, not OCR accuracy."""
import json
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from scripts.dragon_analyzer import analyzer, ocr, config
from scripts.dragon_analyzer.cli import app
from scripts.dragon_analyzer.models import Dragon, DragonClass, DragonData


def profile(stars=7):
    return DragonData(
        dragon=Dragon(name="Jagadrix", level=22, stars=stars,
                      dragon_class=DragonClass.HUNTER),
        confidence=None,
    )


@pytest.mark.parametrize("stars", [1, 5, 6, 7, 8, 9, 10])
def test_valid_star_ranks(stars):
    assert Dragon(name="Jagadrix", level=22, stars=stars,
                  dragon_class=DragonClass.HUNTER).stars == stars


@pytest.mark.parametrize("stars", [-1, 11, 1.5, True, "7"])
def test_invalid_star_ranks(stars):
    with pytest.raises(ValidationError):
        Dragon(name="Jagadrix", level=22, stars=stars,
               dragon_class=DragonClass.HUNTER)


@pytest.mark.parametrize("level", [0, -1, True, "22"])
def test_invalid_reign_levels(level):
    with pytest.raises(ValidationError):
        Dragon(name="Jagadrix", level=level, stars=5,
               dragon_class=DragonClass.HUNTER)


def test_missing_confidence_is_unknown():
    data = DragonData(dragon=Dragon(name="Jagadrix", level=22, stars=5,
                                   dragon_class=DragonClass.HUNTER))
    assert data.confidence is None


def test_coordinate_groups():
    result = ocr.DragonScreenshotOCR()._parse_battle_header("Pinkmaiden (123, 456)")
    assert result["location"] == "Pinkmaiden"
    assert result["coords"] == (123, 456)


def test_ability_order_is_stable():
    result = ocr.DragonScreenshotOCR()._parse_right_panel(
        "Lure Basic Attack Lure Shadowflame")
    assert result["abilities"] == ["Lure", "Basic Attack", "Shadowflame"]


def test_ocr_engine_failure_is_visible(monkeypatch):
    processor = ocr.OCRProcessor()
    monkeypatch.setattr(processor, "preprocess", lambda img: img)

    def fail(*args, **kwargs):
        raise RuntimeError("engine failure")

    monkeypatch.setattr(ocr.pytesseract, "image_to_string", fail)
    with pytest.raises(RuntimeError, match="engine failure"):
        processor.extract_text(np.zeros((3, 3), dtype=np.uint8))


def test_portable_output_config():
    assert "/Users/raelldottin" not in str(config.OUTPUT_DIR)


def test_default_reader_fails_closed(tmp_path):
    image = tmp_path / "IMG_1.jpeg"
    image.write_bytes(b"unverified")
    output = tmp_path / "out"
    worker = analyzer.DragonAnalyzer(output_dir=output)
    with pytest.raises(RuntimeError, match="profile reader"):
        worker.analyze_screenshot(image)
    assert not list(output.rglob("*.json"))


def test_injected_reader_records_observation_not_canonical_data(tmp_path):
    image = tmp_path / "IMG_1.jpeg"
    image.write_bytes(b"fixture")
    output = tmp_path / "out"
    canonical = output / "dragons" / "jagadrix.json"
    canonical.parent.mkdir(parents=True)
    canonical.write_text('{"historical": true}')
    worker = analyzer.DragonAnalyzer(output_dir=output, profile_reader=lambda _: profile())
    result = worker.analyze_screenshot(image)
    assert result.dragon.stars == 7
    assert canonical.read_text() == '{"historical": true}'
    files = list((output / "observations").glob("*.json"))
    assert len(files) == 1
    record = json.loads(files[0].read_text())
    assert record["source_sha256"] == __import__("hashlib").sha256(b"fixture").hexdigest()
    assert record["observation"]["dragon"]["level"] == 22
    worker.analyze_screenshot(image)
    assert len(list((output / "observations").glob("*.json"))) == 1


def test_reader_failure_leaves_no_json(tmp_path):
    image = tmp_path / "IMG_1.jpeg"
    image.write_bytes(b"fixture")
    def fail(_):
        raise RuntimeError("adapter failed")
    worker = analyzer.DragonAnalyzer(output_dir=tmp_path / "out", profile_reader=fail)
    with pytest.raises(RuntimeError, match="adapter failed"):
        worker.analyze_screenshot(image)
    assert not list((tmp_path / "out").rglob("*.json"))


def test_conflicting_observation_is_not_overwritten(tmp_path):
    image = tmp_path / "IMG_1.jpeg"
    image.write_bytes(b"fixture")
    output = tmp_path / "out"
    analyzer.DragonAnalyzer(output, profile_reader=lambda _: profile(7)).analyze_screenshot(image)
    with pytest.raises(RuntimeError, match="conflict"):
        analyzer.DragonAnalyzer(output, profile_reader=lambda _: profile(8)).analyze_screenshot(image)
    files = list((output / "observations").glob("*.json"))
    assert len(files) == 1
    assert json.loads(files[0].read_text())["observation"]["dragon"]["stars"] == 7


def test_batch_supports_jpeg_and_deterministic_order(tmp_path):
    for name in ["IMG_2.jpeg", "IMG_1.png", "IMG_3.txt"]:
        (tmp_path / name).write_bytes(name.encode())
    seen = []
    def read(path):
        seen.append(path.name)
        return profile()
    worker = analyzer.DragonAnalyzer(tmp_path / "out", profile_reader=read)
    assert len(worker.batch_analyze(tmp_path)) == 2
    assert seen == ["IMG_1.png", "IMG_2.jpeg"]


def test_empty_batch_fails(tmp_path):
    worker = analyzer.DragonAnalyzer(tmp_path / "out", profile_reader=lambda _: profile())
    with pytest.raises(ValueError, match="no screenshots"):
        worker.batch_analyze(tmp_path)


def test_export_without_armies_fails(tmp_path):
    worker = analyzer.DragonAnalyzer(tmp_path)
    with pytest.raises(ValueError, match="army"):
        worker.export_army_compositions()
    assert not list(tmp_path.rglob("*.json"))


@pytest.mark.parametrize("filename", ["../escape.json", "/tmp/escape.json"])
def test_analysis_export_rejects_path_traversal(tmp_path, filename):
    worker = analyzer.DragonAnalyzer(tmp_path / "out")
    with pytest.raises(ValueError):
        worker.save_analysis({}, filename)


def test_cli_validate_valid_and_invalid(tmp_path):
    good = tmp_path / "good.json"
    good.write_text(profile(5).model_dump_json())
    bad = tmp_path / "bad.json"
    bad.write_text("{}")
    runner = CliRunner()
    assert runner.invoke(app, ["validate", str(good)]).exit_code == 0
    assert runner.invoke(app, ["validate", str(bad)]).exit_code != 0
    assert runner.invoke(app, ["validate", str(good), "--schema", "unknown"]).exit_code != 0


def test_cli_analyze_and_batch_do_not_claim_success(tmp_path):
    image = tmp_path / "IMG_1.jpeg"
    image.write_bytes(b"fixture")
    output = tmp_path / "out"
    runner = CliRunner()
    assert runner.invoke(app, ["analyze", str(image), "--output", str(output)]).exit_code != 0
    assert runner.invoke(app, ["batch", str(tmp_path), "--output", str(output)]).exit_code != 0
    assert not list(output.rglob("*.json"))
