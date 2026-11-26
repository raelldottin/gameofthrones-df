import numpy as np
from PIL import Image
import pytest
from scripts.dragon_analyzer.icons import (read_icons, choose, similarity, direction_class, habit_level,
                                            DIGITS, AFFINITIES, LOCKS, UNKNOWN)

def test_blank_is_not_locked_or_neutral():
    result=read_icons(Image.new("RGB",(1536,709)))
    assert result["habit_slots"]==[None]*5
    assert result["affinity_slots"]==[None]*4
    assert result["status"]=="unsupported_or_ambiguous"

def test_wrong_geometry():
    with pytest.raises(ValueError):
        read_icons(Image.new("RGB",(709,1536)))

def test_exact_digit_prototypes():
    for label,mask in DIGITS.items():
        assert choose(mask,DIGITS)==label

def test_exact_affinity_prototypes():
    for label,mask in AFFINITIES.items():
        assert choose(mask,AFFINITIES)==label

def test_tied_match_abstains():
    mask=DIGITS[1]
    assert choose(mask,{1:mask,2:mask}) is None

def test_low_similarity_abstains():
    assert choose(np.zeros_like(DIGITS[1]),DIGITS) is None

def test_lock_requires_visual_evidence():
    assert habit_level(np.zeros_like(DIGITS[1]),np.zeros_like(LOCKS[0])) is None
    assert habit_level(np.zeros_like(DIGITS[1]),LOCKS[0])==0

def test_positive_and_negative_markers():
    assert direction_class(.6,0,50)=="+"
    assert direction_class(0,.6,50)=="-"

def test_background_marker_cannot_create_affinity():
    assert direction_class(.01,.325,0) is None
    assert direction_class(0,1,0)=="-"
    assert choose(np.zeros_like(AFFINITIES["Cavalry"]),AFFINITIES) is None

def test_ambiguous_direction_abstains():
    assert direction_class(.6,.6,50) is None

def test_empty_affinity_requires_low_color_and_low_icon():
    assert direction_class(0,0,0)=="empty"
    assert direction_class(0,0,50) is None

def test_similarity_does_not_wrap():
    a=np.zeros((8,8),dtype=bool);a[3,0]=True
    b=np.zeros_like(a);b[3,-1]=True
    assert similarity(a,b)==0
