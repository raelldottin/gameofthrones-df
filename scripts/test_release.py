"""Release policy tests: synthetic trust fixtures never constitute release evidence."""
import copy
import json
from pathlib import Path
import pytest
from scripts.dragon_analyzer.release import assess, inventory, GATES, POLICY_HASH
from scripts.dragon_analyzer.reconcile import digest, reconcile, formation_is_stale
from scripts.dragon_analyzer.supervisor import DIMENSIONS
from scripts.dragon_analyzer.visual_reader import read_visual_candidate
from scripts.dragon_analyzer.solver import evaluate, load_inputs
from scripts.dragon_analyzer.battle import audit
from PIL import Image

TREE="a"*40
OTHER="b"*40
ROOT=Path(__file__).resolve().parents[1]

def package():
    receipts=[{"gate":g,"tree":TREE,"policy":POLICY_HASH,"status":"pass",
               "issuer":"ci" if g not in ("independent_review","independent_qa") else g,
               "artifact":digest(g)} for g in GATES]
    qa={"tree":TREE,"policy":POLICY_HASH,"issuer":"independent_qa",
        "scores":dict(DIMENSIONS),"evidence":{k:[digest(r) for r in receipts if r["gate"]!="independent_qa"] for k in DIMENSIONS}}
    return receipts,qa

def trust(receipts,qa):
    return {digest(x) for x in [*receipts,qa]}

def test_no_receipts_blocks():
    assert assess(TREE,[],None,set())["status"]=="blocked"

def test_all_trusted_receipts_contract_only():
    r,q=package()
    out=assess(TREE,r,q,trust(r,q))
    assert out["status"]=="eligible_for_human_review"
    assert out["score"]==100
    assert out["release_authorized"] is False

def test_untrusted_receipts_block():
    r,q=package()
    assert assess(TREE,r,q,set())["status"]=="blocked"

@pytest.mark.parametrize("gate",GATES)
def test_every_gate_is_mandatory(gate):
    r,q=package()
    r=[x for x in r if x["gate"]!=gate]
    assert assess(TREE,r,q,trust(r,q))["status"]=="blocked"

def test_stale_tree_blocks():
    r,q=package()
    r[0]["tree"]=OTHER
    assert assess(TREE,r,q,trust(r,q))["status"]=="blocked"

def test_stale_policy_blocks():
    r,q=package()
    r[0]["policy"]="0"*64
    assert assess(TREE,r,q,trust(r,q))["status"]=="blocked"

def test_conflicting_receipt_blocks():
    r,q=package()
    r.append({**r[0],"status":"fail"})
    assert assess(TREE,r,q,trust(r,q))["status"]=="blocked"

def test_failed_gate_blocks():
    r,q=package()
    r[0]["status"]="fail"
    assert assess(TREE,r,q,trust(r,q))["status"]=="blocked"

def test_low_score_blocks():
    r,q=package()
    q["scores"]["architecture"]=14
    assert assess(TREE,r,q,trust(r,q))["status"]=="blocked"

def test_unresolved_independence_blocks():
    r,q=package()
    for x in r:
        if x["gate"]=="independent_review":x["issuer"]="ci"
    assert assess(TREE,r,q,trust(r,q))["status"]=="blocked"

def test_qa_missing_evidence_blocks():
    r,q=package()
    q["evidence"]["correctness"]=[]
    assert assess(TREE,r,q,trust(r,q))["status"]=="blocked"

def test_qa_evidence_cannot_reference_unknown_receipt():
    r,q=package()
    q["evidence"]["correctness"]=["0"*64]
    assert assess(TREE,r,q,trust(r,q))["status"]=="blocked"

def test_synthetic_score_cannot_replace_actual_evidence():
    r,q=package()
    assert assess(TREE,[],q,trust([],q))["score"] is None

def test_inventory_not_release_evidence():
    r=inventory(ROOT)
    assert r["status"]=="blocked"
    assert r["development"]["image_correct"]==599
    assert r["development"]["battle_calibration_cases"]==0
    assert r["release_authorized"] is False

def test_cross_boundary_candidate_cannot_promote(tmp_path):
    p=tmp_path/"sample.png"
    Image.new("RGB",(1536,709)).save(p)
    c=read_visual_candidate(p,["Jagadrix"],text_reader=lambda im,config:"")
    assert c["status"]=="unverified_candidate"
    out=reconcile([c],{},[],as_of="2026-11-26T00:00:00Z")
    assert out["permanent"]=={} and out["seasonal"]=={}
    assert out["quarantine"][0]["reason"]=="invalid_event"

def test_cross_boundary_reset_and_rollback():
    e={"source_sha256":"1"*64,"observed_at":"2026-01-02T00:00:00Z","reign_id":"old","name":"A","extractor_id":"reader",
       "permanent":{"stars":2,"relics_current":1,"relics_required":100,"habits":[1]},
       "seasonal":{"level":22,"xp_current":1,"xp_required_display":"165","power":100,"capacity":200,"energy_current":100,"energy_maximum":100}}
    registry=[{"id":"old","starts_at":"2026-01-01T00:00:00Z"},{"id":"new","starts_at":"2026-02-01T00:00:00Z"}]
    before=reconcile([e],{digest(e):"reviewer"},registry,as_of="2026-01-03T00:00:00Z")
    after=reconcile([e],{digest(e):"reviewer"},registry,as_of="2026-02-02T00:00:00Z")
    assert before["permanent"]==after["permanent"]
    assert after["seasonal"]=={}
    assert formation_is_stale(before["formation_basis"],after)
    assert reconcile([e],{digest(e):"reviewer"},registry,as_of="2026-01-03T00:00:00Z")==before

def test_real_data_pipeline_read_only():
    paths=[ROOT/"player-state/dragon-update-2026-11-26.json",ROOT/"armies/current-ten-marches-2026-11-26.json"]
    before=[p.read_bytes() for p in paths]
    x=evaluate(load_inputs(ROOT))
    y=audit(ROOT)
    assert x["battle_improvement"] is None
    assert y["calibration"]["win_probability"] is None
    assert [p.read_bytes() for p in paths]==before
