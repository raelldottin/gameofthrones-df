"""Behavioral tests for unverified panel candidates, not OCR accuracy."""
import pytest
from PIL import Image
from scripts.dragon_analyzer.panel import parse_panel, FIELDS
from scripts.dragon_analyzer.panel_reader import prepare_panel, read_candidate

TEXT = """JAGADRIX
@ Hunter Willful
v4
22 819/84.7K
& 17,800
ty 4407.0
¥ 100/100
E# Average
—— Adult ——
* 82/1,250"""
NAMES = ["Jagadrix", "Shimmer"]


def test_selected_profile():
    assert parse_panel(TEXT, NAMES) == dict(zip(FIELDS, [
        "Jagadrix", "Hunter", "Willful", "Average", "Adult", 22, 819,
        "84.7K", 17800, 4407, 100, 100, 82, 1250, None]))


def test_no_star_inference():
    assert parse_panel(TEXT, NAMES)["stars"] is None


@pytest.mark.parametrize("text", [TEXT.replace("JAGADRIX\n", ""), TEXT.replace("JAGADRIX", "JAGADR1X")])
def test_missing_or_corrupt_name_is_unknown(text):
    assert parse_panel(text, NAMES)["name"] is None


def test_exact_trait_and_speed():
    assert parse_panel(TEXT.replace("Average", "Very Fast"), NAMES)["speed"] == "Very Fast"


def test_malformed_xp_abstains():
    result = parse_panel(TEXT.replace("819/84.7K", "8:19/84.7K"), NAMES)
    assert result["level"] is None and result["xp_current"] is None


def test_overfilled_energy_is_valid():
    assert parse_panel(TEXT.replace("100/100", "250/100"), NAMES)["energy_current"] == 250


def test_zero_energy_maximum_is_unknown():
    assert parse_panel(TEXT.replace("100/100", "100/0"), NAMES)["energy_maximum"] is None


def test_conflicting_relic_rows_abstain():
    assert parse_panel(TEXT + "\n20/30", NAMES)["relic_current"] is None


def test_empty_text_abstains():
    assert all(v is None for v in parse_panel("", NAMES).values())


def test_crop_is_resolution_independent():
    assert prepare_panel(Image.new("RGB", (1536, 709))).size == (614, 1170)
    assert prepare_panel(Image.new("RGB", (3072, 1418))).size == (614, 1170)


def test_wrong_aspect_rejected():
    with pytest.raises(ValueError):
        prepare_panel(Image.new("RGB", (709, 1536)))


def test_preview_is_unverified_and_does_not_write(tmp_path):
    path = tmp_path / "image.png"
    Image.new("RGB", (1536, 709)).save(path)
    result = read_candidate(path, NAMES, text_reader=lambda im: TEXT)
    assert result["status"] == "unverified_candidate"
    assert result["fields"]["name"] == "Jagadrix"
    assert result["fields"]["stars"] is None
    assert len(result["source_sha256"]) == 64
    assert list(tmp_path.iterdir()) == [path]


def test_reader_failure_is_not_a_candidate(tmp_path):
    path = tmp_path / "image.png"
    Image.new("RGB", (1536, 709)).save(path)
    def fail(im):
        raise RuntimeError("engine failed")
    with pytest.raises(RuntimeError, match="engine failed"):
        read_candidate(path, NAMES, text_reader=fail)


@pytest.mark.parametrize(("old", "new", "field"), [
    ("17,800", "-17,800", "power"),
    ("4407.0", "− 4407.0", "capacity"),
    ("100/100", "-100/100", "energy_current"),
    ("82/1,250", "-82/1,250", "relic_current"),
])
def test_negative_values_are_not_made_positive(old, new, field):
    assert parse_panel(TEXT.replace(old, new), NAMES)[field] is None
