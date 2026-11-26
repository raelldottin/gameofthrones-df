"""Q3 visual recognition contracts; synthetic images are not real-image accuracy."""
import pytest
from PIL import Image
from scripts.dragon_analyzer.visual import (
    classify_star, crop_field, merge_fields, rank_from_slots, read_stars,
)
from scripts.dragon_analyzer.panel import FIELDS


@pytest.mark.parametrize("slots,expected", [
    ([1,0,0,0,0],1), ([1,1,1,1,1],5), ([2,1,1,1,1],6),
    ([2,2,1,1,1],7), ([2,2,2,2,2],10),
    ([1,0,1,0,0],None), ([2,1,0,0,0],None),
    ([1,1,None,0,0],None), ([0,0,0,0,0],None), ([1,1],None),
])
def test_rank_contract(slots, expected):
    assert rank_from_slots(slots) == expected


def test_blank_screenshot_is_not_rank_zero():
    assert read_stars(Image.new("RGB", (1536,709))) is None


def test_gold_patch_classified():
    assert classify_star(Image.new("RGB", (30,30), (200,160,20))) == 1


def test_red_patch_needs_gold_highlight():
    assert classify_star(Image.new("RGB", (30,30), (240,50,10))) is None


def test_blue_name_contrast_preserved():
    im = Image.new("RGB", (1536,709))
    im.paste((20,70,180), (1150,60,1160,70))
    assert crop_field(im, "name").getextrema() == (0,255)


def test_unsupported_geometry_rejected():
    with pytest.raises(ValueError):
        crop_field(Image.new("RGB", (709,1536)), "name")


def texts(**kwargs):
    return dict({"name":"JAGADRIX","level":"2","xp":"35/225",
                 "power":"17,800","relic":"82/1,250"}, **kwargs)


def test_isolated_level_replaces_whole_panel_error():
    baseline = dict.fromkeys(FIELDS)
    baseline["level"] = 9
    assert merge_fields(baseline,texts(),7,["Jagadrix"])["level"] == 2


def test_uncertain_level_cannot_fall_back_to_bad_panel():
    baseline = dict.fromkeys(FIELDS)
    baseline["level"] = 9
    assert merge_fields(baseline,texts(level="2?"),None,["Jagadrix"])["level"] is None


def test_unknown_name_no_fuzzy_fallback():
    baseline = dict.fromkeys(FIELDS)
    baseline["name"] = "Jagadrix"
    assert merge_fields(baseline,texts(name="JAGADR1X"),None,["Jagadrix"])["name"] is None


def test_missing_fields_filled_only_by_valid_isolated_text():
    out = merge_fields(dict.fromkeys(FIELDS),texts(),7,["Jagadrix"])
    assert [out[k] for k in ("name","level","stars","xp_current","xp_required_display",
                            "power","relic_current","relic_required")] == [
        "Jagadrix",2,7,35,"225",17800,82,1250]


def test_invalid_fallback_is_not_coerced():
    out=merge_fields(dict.fromkeys(FIELDS),texts(power="-12",xp="3:5/225",relic="41/40"),None,["Jagadrix"])
    assert all(out[k] is None for k in ("power","xp_current","relic_current","stars"))


def test_existing_stats_not_overwritten_by_secondary_ocr():
    baseline=dict.fromkeys(FIELDS)
    baseline.update(power=4530,xp_current=12488,xp_required_display="84.7K",
                    relic_current=5,relic_required=100)
    out=merge_fields(baseline,texts(power="4330",xp="12,483/84.7K",relic="8/100"),2,["Jagadrix"])
    assert [out[k] for k in ("power","xp_current","relic_current")] == [4530,12488,5]
