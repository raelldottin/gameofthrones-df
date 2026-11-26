"""Exact bounded tactical planning, not calibrated combat."""
from itertools import permutations
from pathlib import Path
import pytest
from scripts.dragon_analyzer.tactical import (
    directional_links, rank_positions, deploy, load_context, evaluate, POSITIONS,
)

def dragon(name, stars=4, habits=None):
    return {"name":name,"stars":stars,"habits":habits or []}

def rule(owner="A",habit="Buff",gate=2,position="left",damage="Physical"):
    return {"owner":owner,"habit":habit,"gate":gate,"position":position,
            "damage":damage,"rounds":[1,2,3],"levels":{"1":9},"source":"fixture"}

def attack(name,damage="Physical",rounds=(1,3)):
    return {"owner":name,"damage":damage,"rounds":list(rounds),"source":"fixture"}

def test_exact_direction_and_round_overlap():
    ds=[dragon("A",habits=[{"name":"Buff","level":1}]),dragon("B"),dragon("C")]
    out=directional_links(("B","A","C"),ds,[rule()],[attack("B")])
    assert len(out)==1 and out[0]["rounds"]==[1,3]
    assert out[0]["points"]==18

def test_locked_habit_not_scored():
    ds=[dragon("A",stars=1,habits=[{"name":"Buff","level":1}]),dragon("B"),dragon("C")]
    assert directional_links(("B","A","C"),ds,[rule()],[attack("B")])==[]

def test_wrong_damage_or_round_not_scored():
    ds=[dragon("A",habits=[{"name":"Buff","level":1}]),dragon("B"),dragon("C")]
    assert directional_links(("B","A","C"),ds,[rule()],[attack("B","Fire"),attack("B",rounds=(5,))])==[]

def test_owner_in_preferred_slot_abstains():
    ds=[dragon("A",habits=[{"name":"Buff","level":1}]),dragon("B"),dragon("C")]
    assert directional_links(("A","B","C"),ds,[rule()],[attack("B")])==[]

def test_missing_habit_level_abstains():
    ds=[dragon("A",habits=[{"name":"Buff","level":5}]),dragon("B"),dragon("C")]
    assert directional_links(("B","A","C"),ds,[rule()],[attack("B")])==[]

def test_position_search_against_independent_oracle():
    ds=[dragon("A",habits=[{"name":"Buff","level":1}]),dragon("B"),dragon("C")]
    r=rank_positions(("A","B","C"),ds,[rule()],[attack("B")])
    assert r["candidate"][0]=="B" and r["candidate_points"]==18
    assert r["permutations_evaluated"]==6
    assert r["candidate_points"]==max(18 if p[0]=="B" else 0 for p in permutations("ABC"))

def test_tie_preserves_baseline():
    ds=[dragon(n) for n in "ABC"]
    assert rank_positions(("C","B","A"),ds,[],[])["candidate"]==["C","B","A"]

def march(i,t,cap,ns):
    return {"march":i,"troop_type":t,"capacity":cap,"dragons":list(ns)}

def test_deployment_counter_before_capacity():
    ms=[march(1,"Cavalry",999,"ABC"),march(2,"Spearmen",20,"DEF")]
    out=deploy(ms,["Cavalry"])
    assert out["assignments"][0]["march"]==2

def test_global_deployment_matches_oracle():
    ms=[march(1,"Cavalry",100,"ABC"),march(2,"Spearmen",50,"DEF"),march(3,"Archers",80,"GHI")]
    out=deploy(ms,["Cavalry","Spearmen"])
    assert [x["march"] for x in out["assignments"]]==[2,3]
    assert out["advantage_count"]==2

def test_five_active_limit():
    ms=[march(i,"Cavalry",100,str(i)*3) for i in range(1,7)]
    with pytest.raises(ValueError,match="five"): deploy(ms,["Spearmen"]*6)

def test_overlapping_preset_cannot_deploy_twice():
    ms=[march(1,"Cavalry",100,"ABC"),march(2,"Cavalry",200,"ADE")]
    with pytest.raises(ValueError,match="infeasible"):deploy(ms,["Shieldbearers"]*2)

def test_unknown_enemy_not_guessed():
    with pytest.raises(ValueError,match="enemy"):deploy([march(1,"Cavalry",100,"ABC")],["Unknown"])

def test_real_roster_keeps_members_and_affinities():
    root=Path(__file__).resolve().parents[1]
    r=evaluate(load_context(root))
    assert len(r["marches"])==10 and sum(m["permutations_evaluated"] for m in r["marches"])==60
    assert all(set(m["baseline"])==set(m["candidate"]) for m in r["marches"])
    assert r["battle_improvement"] is None
    assert r["commander_effects"]["Rhaenyra Targaryen (Princess)"]["active_talents"]==["The Realm's Delight"]
    assert len(r["capacity_only_deployment"])==5
