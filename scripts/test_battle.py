from pathlib import Path
import pytest
from scripts.dragon_analyzer.battle import normalize, replay, matchup, simulate, fit, benchmark, audit

def report(result="stalemate", p_end=80, e_end=70):
    return {"battle":{"result":result,"rounds":2},
            "player_side":{"role":"player","troop_type":"Shieldbearers","start_troops":100,"end_troops":p_end,"troop_losses":100-p_end},
            "enemy_side":{"role":"opposing_player","troop_type":"Archers","start_troops":100,"end_troops":e_end,"troop_losses":100-e_end},
            "round_totals":[{"round":1,"player_troops":75,"enemy_troops":80,"player_round_loss":25,"enemy_round_loss":20,"net_round_trade_for_player":-5},
                            {"round":2,"player_troops":p_end,"enemy_troops":e_end,"player_round_loss":75-p_end,"enemy_round_loss":80-e_end,"net_round_trade_for_player":(80-e_end)-(75-p_end)}]}

def test_counter_cycle():
    assert matchup("Shieldbearers","Archers")==1.07
    assert matchup("Archers","Shieldbearers")==.93
    assert matchup("Cavalry","Spearmen")==.93
    assert matchup("Spearmen","Cavalry")==1.07
    assert matchup("Cavalry","Shieldbearers")==1.07
    assert matchup("Archers","Spearmen")==1.07
    assert matchup("Spearmen","Shieldbearers")==1
    assert matchup("Cavalry","Siege")==1.07
    assert matchup("Siege","Cavalry") is None

def test_capacity_not_start():
    x=report()
    x["player_side"]["troops_start_or_capacity"]=x["player_side"].pop("start_troops")
    with pytest.raises(ValueError,match="start"):
        normalize(x,"a")

def test_recovery_is_negative_net_loss():
    r=normalize(report(),"a")
    assert replay(r)["player_net_recovery_rounds"]==[2]
    assert replay(r)["player_net_loss"]==20
    assert replay(r)["enemy_net_loss"]==30

def test_wrong_round_delta_rejected():
    x=report()
    x["round_totals"][1]["player_round_loss"]=5
    with pytest.raises(ValueError,match="delta"):
        replay(normalize(x,"a"))

def test_wrong_final_rejected():
    x=report()
    x["round_totals"].pop()
    with pytest.raises(ValueError,match="round"):
        replay(normalize(x,"a"))

def test_inconsistent_loss_rejected():
    x=report()
    x["player_side"]["troop_losses"]=3
    with pytest.raises(ValueError,match="loss"):
        normalize(x,"a")

def test_victory_requires_enemy_zero():
    with pytest.raises(ValueError,match="outcome"):
        normalize(report("victory"),"a")

def test_stalemate_not_victory_by_remaining_advantage():
    assert normalize(report(),"a")["outcome"]=="stalemate"

def test_simultaneous_damage_and_cap():
    x=simulate(100,100,"Shieldbearers","Archers",.1,.1,rounds=1)
    assert x["player_end"]==91 and x["enemy_end"]==89
    assert x["status"]=="illustrative_only"
    assert x["win_probability"] is None

def test_simulation_stops_at_elimination():
    x=simulate(100,10,"Shieldbearers","Archers",1,1)
    assert len(x["rounds"])==1
    assert x["enemy_end"]==0

def test_simulator_unsupported_siege_abstains():
    with pytest.raises(ValueError,match="matchup"):
        simulate(100,100,"Siege","Archers",.1,.1)

def test_no_cross_mode_calibration():
    a=normalize(report(),"a")
    b={**a,"id":"b","mode":"pve"}
    with pytest.raises(ValueError,match="training"):
        fit([b],"pvp")

def test_group_exclusion():
    a=normalize(report(),"a")
    b={**a,"id":"b","group":a["group"]}
    assert benchmark([a,b])["evaluated"]==0

def test_real_repository_audit():
    root=Path(__file__).resolve().parents[1]
    r=audit(root)
    assert r["files"]==15
    assert len(r["records"])==11
    assert r["round_replays"]==3
    assert r["calibration"]["release_accepted"] is False
