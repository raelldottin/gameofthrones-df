"""Synthetic combat contracts; not observed game outcomes."""
from pathlib import Path
import pytest
from scripts.dragon_analyzer.combat import simulate, sample, compile_actions, prospective_gate
from scripts.dragon_analyzer.reconcile import digest
from scripts.dragon_analyzer.battle import audit

def unit(name,side,lane,stars=6,troops=100):
    return dict(name=name,side=side,lane=lane,stars=stars,troops=troops,
                damage_unit=10,recovery_unit=10)

def action(actor,kind="damage",rounds=(1,),target="same",rate=100,gate=0,
           chance=100,duration=1,damage="Tactical",count=1):
    return dict(actor=actor,kind=kind,rounds=list(rounds),target=target,rate=rate,
                gate=gate,chance=chance,duration=duration,damage=damage,count=count)

def arena():
    return [unit("a","player",0),unit("b","enemy",0)]

def test_simultaneous_elimination():
    out=simulate(arena(),[action("a",rate=1000),action("b",rate=1000)],seed=1)
    assert out["outcome"]=="mutual_elimination"
    assert len(out["rounds"])==1
    assert out["win_probability"] is None

def test_star_gate():
    u=arena();u[0]["stars"]=5
    assert simulate(u,[action("a",gate=6)],seed=1)["end"]["b"]==100

def test_round_schedule():
    r=simulate(arena(),[action("a",rounds=(2,4))],seed=1)
    assert [x["troops"]["b"] for x in r["rounds"][:5]]==[100,90,90,80,80]

def test_adjacent_never_reaches_far_lane():
    u=[unit("a","player",0),unit("b","enemy",1),unit("c","enemy",2)]
    r=simulate(u,[action("a",target="adjacent",count=3)],seed=1)
    assert r["end"]=={"a":100,"b":90,"c":100}

def test_recovery_cap_and_no_resurrection():
    u=arena()
    r=simulate(u,[action("a",rate=1000),action("b","heal",target="self",rate=1000)],seed=1)
    assert r["end"]["b"]==0
    r=simulate(u,[action("a",rate=100),action("b","heal",target="self",rate=1000)],seed=1)
    assert r["end"]["b"]==100

def test_weakened_duration_and_no_stacking():
    actions=[action("a","weakened",target="same",rate=50,duration=2),
             action("b",rounds=(1,2,3))]
    r=simulate(arena(),actions,seed=1)
    assert [x["troops"]["a"] for x in r["rounds"][:3]]==[95,90,80]
    assert simulate(arena(),actions+[actions[0]],seed=1)["end"]["a"]==80

def test_nullify_recovery():
    actions=[action("a",rate=100),action("a","nullify",rate=0,duration=1),
             action("b","heal",target="self",rate=100)]
    assert simulate(arena(),actions,seed=1)["end"]["b"]==90

def test_resistance_is_targeted_and_expires():
    actions=[action("a",rounds=(1,2)),action("b","resistance",target="self",rate=50)]
    r=simulate(arena(),actions,seed=1)
    assert [x["troops"]["b"] for x in r["rounds"][:2]]==[95,85]

def test_seed_repeatability_and_no_predictive_probability():
    a=[action("a",chance=50,rounds=tuple(range(1,11)))]
    assert sample(arena(),a,seed=77,trials=20)==sample(arena(),a,seed=77,trials=20)
    assert sample(arena(),a,seed=77,trials=20)["win_probability"] is None

def test_probability_zero_never_activates():
    assert simulate(arena(),[action("a",chance=0)],seed=1)["end"]["b"]==100

def test_unknown_action_rejected():
    with pytest.raises(ValueError): simulate(arena(),[action("a","magic")],seed=1)

def test_unsupported_command_not_silently_complete():
    root=Path(__file__).resolve().parents[1]
    result=compile_actions(root,["Sheepstealer","Malachite","Shimmer"])
    assert result["complete"] is False
    assert "Sheepstealer" in result["unsupported"]
    heals=[a for a in result["actions"] if a["actor"]=="Shimmer" and a["kind"]=="heal"]
    assert len(heals)==1 and heals[0]["rate"]==51 and heals[0]["gate"]==6

def test_historical_evidence_gate_abstains():
    root=Path(__file__).resolve().parents[1]
    report=audit(root)
    assert report["round_replays"]==3
    gate=prospective_gate([],[],mode="pve")
    assert gate["status"]=="blocked" and gate["win_probability"] is None

def row(i,group,partition):
    return {"id":str(i),"group":group,"mode":"pve","partition":partition,
            "scenario_digest":digest({"scenario":i}),"start":[100,100],"end":[80,60],
            "prediction":[80,60],"baseline":[100,100],
            "observed_outcome":"stalemate","predicted_outcome":"stalemate"}

def test_calibration_rejects_group_leakage():
    train=[row(1,"same","train")];hold=[row(2,"same","holdout")]
    assert prospective_gate(train,hold,mode="pve")["reason"]=="group_leakage"

def test_duplicate_scenario_rejected_even_if_group_differs():
    train=[row(1,"a","train")];hold=[{**row(2,"b","holdout"),"scenario_digest":train[0]["scenario_digest"]}]
    assert prospective_gate(train,hold,mode="pve")["reason"]=="scenario_leakage"

def test_synthetic_calibration_can_only_be_diagnostic():
    train=[row(i,"t"+str(i),"train") for i in range(20)]
    hold=[row(i+20,"h"+str(i),"holdout") for i in range(20)]
    out=prospective_gate(train,hold,mode="pve")
    assert out["status"]=="diagnostic_only" and out["release_accepted"] is False
    assert out["mean_error"]==0 and out["baseline_error"]==.3

def test_worse_than_baseline_blocks():
    train=[row(i,"t"+str(i),"train") for i in range(20)]
    hold=[{**row(i+20,"h"+str(i),"holdout"),"prediction":[0,0]} for i in range(20)]
    assert prospective_gate(train,hold,mode="pve")["status"]=="blocked"
