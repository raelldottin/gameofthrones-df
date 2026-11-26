from pathlib import Path
import pytest
from scripts.dragon_analyzer.strategy import plan, optimize, xp_gap, load_context, star_milestones

ROOT=Path(__file__).resolve().parents[1]

def option(id,cost,utility,group=None):
    return {"id":id,"cost":cost,"utility":utility,"group":group or id}

def test_exact_multi_resource_budget_beats_greedy():
    x=[option("a",{"gold":4,"core":4},7),option("b",{"gold":3,"core":2},6),
       option("c",{"gold":2,"core":3},6)]
    r=optimize(x,{"gold":5,"core":5})
    assert r["selected"]==["b","c"] and r["utility"]==12
    assert r["spent"]=={"core":5,"gold":5}

def test_missing_currency_not_zero_or_unlimited():
    r=optimize([option("a",{"gold":1,"core":1},10)],{"gold":10})
    assert r["selected"]==[] and r["unknown_budget"]==["a"]

def test_group_mutually_exclusive():
    r=optimize([option("a",{"gold":1},1,"commander"),option("b",{"gold":1},2,"commander")],{"gold":10})
    assert r["selected"]==["b"]

def test_order_independent_and_tie_preserves_resources():
    x=[option("z",{"gold":2},2),option("a",{"gold":1},2)]
    r=optimize(x,{"gold":2})
    assert r==optimize(list(reversed(x)),{"gold":2})
    assert r["selected"]==["a"]

@pytest.mark.parametrize("cost",[{"gold":-1},{"gold":True},{"gold":1.5},{}])
def test_invalid_cost_rejected(cost):
    with pytest.raises(ValueError):optimize([option("a",cost,1)],{"gold":10})

def test_xp_rounded_not_exact():
    assert xp_gap(90746,"95.7K")=={"gap":4954,"exact":False}
    assert xp_gap(0,"165")=={"gap":165,"exact":True}
    with pytest.raises(ValueError):xp_gap(0,"unknown")

def test_real_roster_and_milestones():
    r=plan(load_context(ROOT))
    assert len(r["stars"])==38
    assert r["stars"][0]["name"]=="Vhagar" and r["stars"][0]["missing_relics"]==5
    active=[x for x in r["stars"] if x["march"] in (1,2,3,4,5) and x["next_star"]==6]
    assert active[0]["name"]=="Solstryker" and active[0]["missing_relics"]==155
    assert next(x for x in r["stars"] if x["name"]=="Bevlorin")["missing_relics"]==170
    assert next(x for x in r["stars"] if x["name"]=="Shimmer")["next_star"]==7

def test_historical_costs_not_spend_authority():
    r=plan(load_context(ROOT))
    assert len(r["habit_candidates"])==5
    assert all(x["status"]=="historical_cost_recheck" for x in r["habit_candidates"])
    assert r["dragon_core_budget"] is None
    assert r["spend_authorized"] is False
    assert r["battle_improvement"] is None

def test_commander_previews_independent():
    r=plan(load_context(ROOT))
    assert len(r["commander_previews"])==3
    assert all(x["group"]=="Rhaenyra Targaryen (Princess)" for x in r["commander_previews"])
    assert all(x["status"]=="dated_preview_recheck" for x in r["commander_previews"])
    assert r["commander_budget"]["medals"] is None

def test_reign_unknown_and_near_level():
    r=plan(load_context(ROOT))
    assert r["season"]["reign_id"] is None
    assert r["season"]["status"]=="dated_snapshot_only"
    d={x["name"]:x for x in r["season"]["levels"]}
    assert d["Malachite"]["gap"]==4954 and not d["Malachite"]["exact"]
    assert d["Solstryker"]["gap"]==3419 and not d["Solstryker"]["exact"]

def test_stale_habit_cost_level_excluded():
    x=load_context(ROOT)
    d=next(d for d in x["roster"]["updates"] if d["name"]=="Zivern")
    next(h for h in d["habits"] if h["name"]=="Fearsome Reach")["level"]=3
    assert not any(h["name"]=="Zivern" for h in plan(x)["habit_candidates"])

def test_no_duplicate_dragon_assignments():
    x=load_context(ROOT)
    x["formations"]["marches"][1]["left"]=x["formations"]["marches"][0]["left"]
    with pytest.raises(ValueError,match="duplicate"):plan(x)
