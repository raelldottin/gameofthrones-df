import itertools
import json
from pathlib import Path
import pytest
from scripts.dragon_analyzer.solver import optimize, score, assign_commanders, basis, load_inputs, evaluate

def d(name, stars, affinities, habits=None, capacity=100, trait="Nimble"):
    return dict(name=name, stars=stars, habits=list(habits if habits is not None else [1]*(stars//2)), affinities=list(affinities),
                capacity=capacity, trait=trait)

def test_permanent_score_is_explicit():
    assert score(d("A",5,["Archers"],[2,3]))==60

def test_exact_solver_matches_independent_exhaustive_oracle():
    dragons=[d("A",7,["Archers","Cavalry"]),d("B",6,["Archers"]),
             d("C",5,["Cavalry"]),d("D",4,["Archers","Cavalry"]),
             d("E",3,["Archers"]),d("F",2,["Cavalry"]),d("G",1,["Cavalry"])]
    q={"Archers":3,"Cavalry":3}
    feasible=[]
    for a in itertools.combinations(dragons,3):
        if not all("Archers" in x["affinities"] for x in a): continue
        for c in itertools.combinations([x for x in dragons if x not in a],3):
            if all("Cavalry" in x["affinities"] for x in c):
                feasible.append(sum(10*x["stars"]+2*sum(x["habits"]) for x in a+c))
    result=optimize(dragons,q)
    assert result["score"]==max(feasible)
    assert len(set(sum(result["assignments"].values(),[])))==6

def test_global_matching_not_greedy():
    ds=[d("A",9,["Archers","Cavalry"]),d("B",8,["Archers"]),d("C",1,["Cavalry"])]
    assert optimize(ds,{"Archers":1,"Cavalry":1})["assignments"]=={"Archers":["B"],"Cavalry":["A"]}

def test_order_independent():
    ds=[d("A",3,["Archers","Cavalry"]),d("B",3,["Archers","Cavalry"]),d("C",3,["Archers","Cavalry"])]
    q={"Archers":1,"Cavalry":1}
    assert all(optimize(list(p),q)==optimize(ds,q) for p in itertools.permutations(ds))

def test_seasonal_capacity_does_not_change_persistent_selection():
    ds=[d("A",5,["Archers"],capacity=1),d("B",4,["Archers"],capacity=100000)]
    assert optimize(ds,{"Archers":1})["assignments"]=={"Archers":["A"]}

def test_infeasible_is_explicit():
    with pytest.raises(ValueError,match="infeasible"):
        optimize([d("A",5,["Archers"])],{"Cavalry":1})

def test_duplicate_dragon_rejected():
    with pytest.raises(ValueError,match="duplicate"):
        optimize([d("A",5,["Archers"]),d("A",4,["Archers"])],{"Archers":1})

def test_retention_breaks_equal_scores():
    ds=[d("A",5,["Archers"]),d("B",5,["Archers"])]
    assert optimize(ds,{"Archers":1},{"B":"Archers"})["assignments"]=={"Archers":["B"]}

def test_locked_commander_excluded_and_unique():
    marches=[{"march":1,"left":"A","vanguard":"B","right":"C"},{"march":2,"left":"D","vanguard":"E","right":"F"}]
    ds=[d(n,3,["Archers"],trait="Nimble" if n in "ABC" else "Cunning") for n in "ABCDEF"]
    cs=[{"name":"R","rank":1,"preferred_traits":["Nimble"]},{"name":"C","rank":1,"preferred_traits":["Cunning"]},{"name":"Locked","rank":None,"preferred_traits":["Nimble","Cunning"]}]
    assert assign_commanders(marches,ds,cs)=={1:"R",2:"C"}

def test_fingerprint_includes_commander_catalog_equipment_and_reign():
    original=dict(roster=[1],season=[2],commanders=[3],affinity=[4],equipment=None,reign=None)
    for k in original:
        changed={**original,k:"changed"}
        assert basis(original)!=basis(changed)

def test_real_roster_benchmark():
    root=Path(__file__).resolve().parents[1]
    inputs=load_inputs(root)
    result=evaluate(inputs)
    assert result["candidate"]["score"]>=result["baseline"]["score"]
    assert result["candidate"]["count"]==30
    assert len(result["bench"])==8
    assert result["candidate"]["affinity_violations"]==0
    assert result["battle_improvement"] is None


def test_readiness_mode_has_separate_objective():
    dragons=[d("A",5,["Archers"],capacity=1),d("B",4,["Archers"],capacity=100000)]
    result=optimize(dragons,{"Archers":1},objective="readiness")
    assert result["assignments"]=={"Archers":["B"]}
    assert result["score"]==44
    assert result["objective_value"]==100000


def test_readiness_exact_oracle_with_shared_affinity():
    dragons=[d("A",7,["Archers","Cavalry"],capacity=200),d("B",5,["Archers"],capacity=150),
             d("C",3,["Cavalry"],capacity=100)]
    r=optimize(dragons,{"Archers":1,"Cavalry":1},objective="readiness")
    assert r["assignments"]=={"Archers":["B"],"Cavalry":["A"]}
    assert r["objective_value"]==350


def test_invalid_objective_rejected():
    with pytest.raises(ValueError,match="objective"):
        optimize([d("A",5,["Archers"])],{"Archers":1},objective="winrate")


def test_actual_readiness_alternative_never_worse_on_capacity():
    root=Path(__file__).resolve().parents[1]
    r=evaluate(load_inputs(root))
    assert r["readiness_alternative"]["capacity"]>=r["baseline"]["capacity"]
    assert r["readiness_alternative"]["affinity_violations"]==0
    assert r["readiness_alternative"]["count"]==30
    assert r["recommendation_policy"]=="alternatives_only"
