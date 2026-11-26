"""Q4 domain behavior. No OCR, filesystem or network required for reconciliation."""
import copy
import itertools
import json
from pathlib import Path

import pytest

from scripts.dragon_analyzer.reconcile import (
    digest, reconcile, stage_legacy, formation_is_stale,
)

R1={"id":"r1","starts_at":"2026-01-01T00:00:00Z"}
R2={"id":"r2","starts_at":"2026-02-01T00:00:00Z"}
NOW="2026-02-10T00:00:00Z"
JAN="2026-01-15T00:00:00Z"
FEB="2026-02-02T00:00:00Z"


def event(source="a", at=JAN, reign="r1", stars=5, level=22, name="Jagadrix"):
    return dict(source_sha256=digest(source), observed_at=at, reign_id=reign,
                name=name, extractor_id="reader",
                permanent=dict(stars=stars, relics_current=50, relics_required=500,
                               habits=[2,1]+([1] if stars>=6 else [])),
                seasonal=dict(level=level, xp_current=10, xp_required_display="165",
                              power=100, capacity=200, energy_current=250, energy_maximum=100))


def approvals(*events):
    return {digest(e):"reviewer" for e in events}


def run(events, approved=None, reigns=(R1,R2), as_of=NOW):
    return reconcile(events, approvals(*events) if approved is None else approved,
                     list(reigns), as_of=as_of)


def test_reign_reset_keeps_permanent_and_clears_current_season():
    e=event()
    result=run([e])
    assert result["current_reign"]=="r2"
    assert result["permanent"]["Jagadrix"]["stars"]==5
    assert result["seasonal"]=={}
    assert result["history"]["r1"]["Jagadrix"]["level"]==22


def test_new_reign_lower_level_is_valid():
    a,b=event(),event("b",FEB,"r2",6,1)
    r=run([a,b])
    assert r["seasonal"]["Jagadrix"]["level"]==1
    assert r["permanent"]["Jagadrix"]["stars"]==6
    assert r["history"]["r1"]["Jagadrix"]["level"]==22


def test_no_approval_no_promotion():
    r=run([event()],{})
    assert r["permanent"]=={} and r["history"]=={}
    assert r["quarantine"][0]["reason"]=="unapproved"


def test_self_approval_is_not_independent():
    e=event()
    assert run([e],{digest(e):"reader"})["quarantine"][0]["reason"]=="self_approval"


def test_approval_binds_exact_payload():
    e=event()
    a=approvals(e)
    e["permanent"]["stars"]=6
    assert run([e],a)["permanent"]=={}


def test_duplicate_replay_idempotent_and_input_unchanged():
    a,b=event(),event("b",FEB,"r2",6,1)
    original=copy.deepcopy([a,b])
    assert run([a,b])==run([a,b,a,b])
    assert [a,b]==original


def test_all_arrival_orders_equal():
    e=[event(),event("b",FEB,"r2",6,1),event("c","2026-02-03T00:00:00Z","r2",6,2)]
    results=[run(list(order)) for order in itertools.permutations(e)]
    assert all(r==results[0] for r in results)


def test_same_source_different_payload_quarantines_both():
    a,b=event(),event(stars=6)
    r=run([a,b])
    assert r["permanent"]=={}
    assert [q["reason"] for q in r["quarantine"]]==["source_conflict"]*2


def test_same_timestamp_disagreement_quarantines_both():
    a,b=event(),event("b",stars=6)
    r=run([a,b])
    assert r["permanent"]=={}
    assert [q["reason"] for q in r["quarantine"]]==["timestamp_conflict"]*2


def test_same_timestamp_equal_payload_different_source_allowed():
    a,b=event(),event("b")
    r=run([a,b])
    assert len(r["accepted"])==2 and not r["quarantine"]


def test_unapproved_conflict_cannot_poison_approved_source():
    a,b=event(),event(stars=6)
    r=run([a,b],approvals(a))
    assert r["permanent"]["Jagadrix"]["stars"]==5
    assert r["quarantine"][0]["reason"]=="unapproved"


def test_stale_same_reign_level_and_star_regression_rejected():
    a,b=event(),event("b","2026-01-16T00:00:00Z",stars=4,level=21)
    r=run([a,b])
    assert r["permanent"]["Jagadrix"]["stars"]==5
    assert r["quarantine"][0]["reason"]=="progression_regression"


def test_same_reign_level_regression_even_with_more_stars():
    a,b=event(),event("b","2026-01-16T00:00:00Z",stars=6,level=21)
    assert run([a,b])["quarantine"][0]["reason"]=="progression_regression"


def test_habit_regression_rejected():
    a,b=event(),event("b",FEB,"r2",6,1)
    b["permanent"]["habits"]=[1,1,1]
    assert run([a,b])["quarantine"][0]["reason"]=="progression_regression"


def test_relic_balance_may_decrease_on_upgrade():
    a,b=event(),event("b",FEB,"r2",6,1)
    b["permanent"]["relics_current"]=0
    assert run([a,b])["permanent"]["Jagadrix"]["relics_current"]==0


@pytest.mark.parametrize("key,value", [("level",22),("xp_current",0),("energy",100)])
def test_seasonal_field_in_permanent_is_rejected(key,value):
    e=event()
    e["permanent"][key]=value
    assert run([e])["quarantine"][0]["reason"]=="invalid_event"


@pytest.mark.parametrize("key,value",[("stars",True),("stars",11),("habits",[6]),("relics_current",500)])
def test_invalid_permanent_values(key,value):
    e=event()
    e["permanent"][key]=value
    assert run([e])["quarantine"][0]["reason"]=="invalid_event"


def test_unknown_critical_value_rejected():
    e=event()
    e["permanent"]["stars"]=None
    assert run([e])["quarantine"][0]["reason"]=="invalid_event"


def test_reign_mismatch_is_not_inferred():
    e=event(at=FEB)
    assert run([e])["quarantine"][0]["reason"]=="reign_mismatch"


def test_unknown_reign_is_quarantined():
    e=event(reign=None)
    assert run([e])["quarantine"][0]["reason"]=="invalid_event"


def test_ambiguous_reign_registry_rejected():
    with pytest.raises(ValueError):
        run([],reigns=(R1,dict(R2,starts_at=R1["starts_at"])))


def test_future_observations_do_not_affect_as_of_snapshot():
    a,b=event(),event("b",FEB,"r2",6,1)
    r=run([a,b],as_of="2026-01-20T00:00:00Z")
    assert r==run([a],as_of="2026-01-20T00:00:00Z")
    assert r["seasonal"]["Jagadrix"]["level"]==22


def test_reign_reset_and_progression_invalidate_formation():
    e=event()
    before=run([e],as_of="2026-01-20T00:00:00Z")
    after=run([e])
    assert not formation_is_stale(before["formation_basis"],before)
    assert formation_is_stale(before["formation_basis"],after)
    assert formation_is_stale(None,after)


def test_no_reign_at_cutoff():
    assert run([],as_of="2025-12-31T00:00:00Z")["current_reign"] is None


def test_actual_legacy_roster_staged_without_inventing_reign_or_approval():
    root=Path(__file__).resolve().parents[1]
    p=json.loads((root/"player-state/dragon-update-2026-11-26.json").read_text())
    s=json.loads((root/"player-state/dragon-reign-snapshot-2026-11-26.json").read_text())
    out=stage_legacy(p,s)
    assert out["status"]=="migration_pending_verification"
    assert len(out["profiles"])==38
    assert out["reign_id"] is None and out["events"]==[]
    assert "level" not in out["profiles"][0]["permanent"]
    assert out["profiles"][0]["seasonal"]["level"]>=1


def test_legacy_mismatched_roster_rejected():
    with pytest.raises(ValueError):
        stage_legacy({"updates":[{"name":"A"}]},{"dragons":[{"name":"B"}]})


def test_same_reign_xp_regression():
    a,b=event(),event("b","2026-01-16T00:00:00Z")
    b["seasonal"]["xp_current"]=0
    assert run([a,b])["quarantine"][0]["reason"]=="progression_regression"


def test_missing_unlocked_habit_is_invalid():
    e=event(stars=6)
    e["permanent"]["habits"]=[2,1]
    assert run([e])["quarantine"][0]["reason"]=="invalid_event"


def test_offset_equivalent_timestamp_conflict():
    a,b=event(),event("b","2026-01-14T19:00:00-05:00",stars=6)
    assert [q["reason"] for q in run([a,b])["quarantine"]]==["timestamp_conflict"]*2


def test_new_evidence_does_not_mutate_old_snapshot():
    a,b=event(),event("b",FEB,"r2",6,1)
    before=run([a],as_of="2026-01-20T00:00:00Z")
    saved=copy.deepcopy(before)
    run([a,b])
    assert before==saved


def test_reordered_reign_registry_has_same_result():
    assert run([event()])==run([event()],reigns=(R2,R1))


def test_current_season_mutation_cannot_change_history():
    r=run([event("b",FEB,"r2",6,1)])
    r["seasonal"]["Jagadrix"]["level"]=99
    assert r["history"]["r2"]["Jagadrix"]["level"]==1


def test_empty_reign_changes_formation_basis():
    a=run([],as_of="2026-01-20T00:00:00Z")
    b=run([])
    assert formation_is_stale(a["formation_basis"],b)


def test_all_720_arrival_orders_with_conflicts_and_reset():
    a=event()
    b=event("b",FEB,"r2",6,1)
    c=event("c","2026-02-03T00:00:00Z","r2",6,2)
    d=event("d","2026-02-04T00:00:00Z","r2",7,3)
    e=event("d","2026-02-04T00:00:00Z","r2",6,3)
    f=event("f","2026-02-05T00:00:00Z","r2",7,4)
    events=[a,b,c,d,e,f]
    approved=approvals(a,b,c,d,e)
    expected=run(events,approved)
    assert expected["seasonal"]["Jagadrix"]["level"]==2
    assert sorted(q["reason"] for q in expected["quarantine"])==["source_conflict","source_conflict","unapproved"]
    for order in itertools.permutations(events):
        assert run(list(order),approved)==expected


def minimal_legacy():
    p={"observed_date":"2026-11-26","source_screenshots":["IMG_1.jpeg"],
       "updates":[{"name":"A","stars":5,"source_screenshot":"IMG_1.jpeg"}]}
    s={"observed_date":"2026-11-26","source_screenshots":["IMG_1.jpeg"],
       "dragons":[{"name":"A","level":22,"source_screenshot":"IMG_1.jpeg"}]}
    return p,s


def test_legacy_mismatched_profile_source_rejected():
    p,s=minimal_legacy()
    s["dragons"][0]["source_screenshot"]="IMG_2.jpeg"
    with pytest.raises(ValueError,match="profile source"):
        stage_legacy(p,s)


def test_legacy_missing_date_rejected():
    p,s=minimal_legacy()
    p.pop("observed_date")
    s.pop("observed_date")
    with pytest.raises(ValueError,match="date"):
        stage_legacy(p,s)


def test_legacy_different_manifest_rejected():
    p,s=minimal_legacy()
    s["source_screenshots"].append("IMG_2.jpeg")
    with pytest.raises(ValueError,match="manifest"):
        stage_legacy(p,s)


def test_legacy_staged_records_do_not_alias_sources():
    p,s=minimal_legacy()
    out=stage_legacy(p,s)
    out["profiles"][0]["permanent"]["stars"]=7
    assert p["updates"][0]["stars"]==5
    assert out["source_document_digests"]==[digest(p),digest(s)]
