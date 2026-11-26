"""Historical evidence replay and illustrative aggregate attrition; not game simulation."""
from collections import Counter
from math import isfinite
from pathlib import Path
import json
from .reconcile import digest

COUNTERS={"Shieldbearers":"Archers","Archers":"Spearmen",
          "Spearmen":"Cavalry","Cavalry":"Shieldbearers"}
TROOPS=set(COUNTERS)|{"Siege"}


def matchup(attacker, defender):
    """Observed June 24 field troop rules; Siege's own direction is unknown."""
    if attacker not in COUNTERS or defender not in TROOPS:
        return None
    if defender=="Siege" or COUNTERS[attacker]==defender:
        return 1.07
    if COUNTERS.get(defender)==attacker:
        return .93
    return 1.0


def count(value, label, minimum=0):
    if type(value) is not int or value<minimum:
        raise ValueError("invalid "+label)
    return value


def side(raw):
    if not isinstance(raw,dict):
        raise ValueError("missing side")
    start=count(raw.get("start_troops",raw.get("troops_start")),"start",1)
    end=count(raw.get("end_troops",raw.get("troops_end")),"end")
    losses=raw.get("troop_losses")
    if end>start or type(losses) is not int or losses!=start-end:
        raise ValueError("inconsistent net loss")
    troop=raw.get("troop_type")
    if troop not in TROOPS:
        raise ValueError("unknown troop type")
    return {"start":start,"end":end,"troop":troop}


def normalize(raw, source, *, group=None):
    b=raw.get("battle",{})
    p=raw.get("player_side",raw.get("attacker_side"))
    e=raw.get("enemy_side",raw.get("defender_side"))
    player,enemy=side(p),side(e)
    outcome=b.get("result")
    if outcome not in ("victory","stalemate","defeat"):
        raise ValueError("unsupported outcome")
    if ((outcome=="victory" and (enemy["end"]!=0 or player["end"]==0))
            or (outcome=="defeat" and (player["end"]!=0 or enemy["end"]==0))
            or (outcome=="stalemate" and (player["end"]==0 or enemy["end"]==0))):
        raise ValueError("inconsistent outcome")
    mode="pve" if b.get("encounter_type","").startswith("pve_") else (
        "pvp" if e.get("role")=="opposing_player" or e.get("player_name") else "unknown")
    rounds=b.get("rounds",b.get("duration_rounds"))
    if rounds is not None and (type(rounds) is not int or not 1<=rounds<=10):
        raise ValueError("invalid round count")
    trace=raw.get("round_totals",[])
    if not isinstance(trace,list):
        raise ValueError("invalid round trace")
    return {"id":source,"group":group or source,"source_digest":digest(raw),
            "mode":mode,"outcome":outcome,"player":player,"enemy":enemy,
            "round_count":rounds,"trace":trace}


def replay(record):
    """Reconcile observed net troop changes, not gross damage/healing."""
    trace=record["trace"]
    if not trace or len(trace)!=record["round_count"]:
        raise ValueError("incomplete round trace")
    p,e=record["player"]["start"],record["enemy"]["start"]
    recovery_p,recovery_e=[],[]
    for i,row in enumerate(trace,1):
        if row.get("round")!=i:
            raise ValueError("round order")
        pn=count(row.get("player_troops"),"player troops")
        en=count(row.get("enemy_troops"),"enemy troops")
        if pn>record["player"]["start"] or en>record["enemy"]["start"]:
            raise ValueError("round count exceeds initial troops")
        pl,el=p-pn,e-en
        if (row.get("player_round_loss")!=pl or row.get("enemy_round_loss")!=el
                or row.get("net_round_trade_for_player")!=el-pl):
            raise ValueError("round delta mismatch")
        if pl<0: recovery_p.append(i)
        if el<0: recovery_e.append(i)
        if (pn==0 or en==0) and i<len(trace):
            raise ValueError("round after elimination")
        p,e=pn,en
    if (p,e)!=(record["player"]["end"],record["enemy"]["end"]):
        raise ValueError("round final mismatch")
    return {"player_net_loss":record["player"]["start"]-p,
            "enemy_net_loss":record["enemy"]["start"]-e,
            "player_net_recovery_rounds":recovery_p,
            "enemy_net_recovery_rounds":recovery_e}


def simulate(player,enemy,player_type,enemy_type,player_rate,enemy_rate,*,rounds=10):
    """Illustrative simultaneous aggregate attack model. No lanes or commands.
    Rates are assumed net attrition coefficients, not documented game stats.
    """
    p=count(player,"player start",1);e=count(enemy,"enemy start",1)
    if type(rounds) is not int or not 1<=rounds<=10:
        raise ValueError("invalid rounds")
    if any(type(v) not in (int,float) or not isfinite(v) or not 0<=v<=1
           for v in (player_rate,enemy_rate)):
        raise ValueError("invalid assumed rate")
    pm,em=matchup(player_type,enemy_type),matchup(enemy_type,player_type)
    if pm is None or em is None:
        raise ValueError("unsupported matchup")
    trace=[]
    for i in range(1,rounds+1):
        inflicted=min(e,round(p*player_rate*pm))
        suffered=min(p,round(e*enemy_rate*em))
        p-=suffered;e-=inflicted
        trace.append({"round":i,"player_troops":p,"enemy_troops":e})
        if p==0 or e==0:
            break
    outcome=("mutual_elimination" if p==e==0 else "victory" if e==0 else
             "defeat" if p==0 else "stalemate" if rounds==10 else "unfinished")
    return {"status":"illustrative_only","player_end":p,"enemy_end":e,
            "rounds":trace,"outcome":outcome,"win_probability":None}


def fit(records,mode):
    """Fit net loss/exposure ratios within one encounter mode; full traces only."""
    numer=[0,0];denom=[0.,0.];used=[]
    for r in records:
        if r["mode"]!=mode or not r["trace"]:
            continue
        pm=matchup(r["player"]["troop"],r["enemy"]["troop"])
        em=matchup(r["enemy"]["troop"],r["player"]["troop"])
        if pm is None or em is None:
            continue
        replay(r)
        p,e=r["player"]["start"],r["enemy"]["start"]
        for row in r["trace"]:
            pn,en=row["player_troops"],row["enemy_troops"]
            numer[0]+=e-en;numer[1]+=p-pn
            denom[0]+=p*pm;denom[1]+=e*em
            p,e=pn,en
        used.append(r["id"])
    if not used or min(denom)<=0:
        raise ValueError("no eligible training evidence")
    return {"player_rate":max(0.,min(1.,numer[0]/denom[0])),
            "enemy_rate":max(0.,min(1.,numer[1]/denom[1])),
            "training_ids":sorted(used)}


def benchmark(records):
    """Leave capture groups out, never train on another mode or same group."""
    rows=[];skips=[]
    for r in records:
        if not r["trace"] or r["mode"] not in ("pve","pvp"):
            continue
        train=[x for x in records if x["group"]!=r["group"]]
        try:
            coeff=fit(train,r["mode"])
        except ValueError:
            skips.append({"id":r["id"],"reason":"no independent same-mode training group"})
            continue
        p,e=r["player"],r["enemy"]
        predicted=simulate(p["start"],e["start"],p["troop"],e["troop"],
                           coeff["player_rate"],coeff["enemy_rate"],rounds=r["round_count"])
        error=(abs(predicted["player_end"]-p["end"])/p["start"]+
               abs(predicted["enemy_end"]-e["end"])/e["start"])/2
        naive=((p["start"]-p["end"])/p["start"]+(e["start"]-e["end"])/e["start"])/2
        rows.append({"id":r["id"],"training_ids":coeff["training_ids"],
                     "mean_normalized_end_error":error,"no_change_error":naive})
    return {"evaluated":len(rows),"rows":rows,"skips":skips,
            "release_accepted":False,"win_probability":None}


def audit(root):
    paths=sorted((Path(root)/"battle-logs").glob("*.json"))
    records=[];excluded=[]
    for path in paths:
        raw=json.loads(path.read_text())
        candidates=[(path.name,raw)]
        if "reports" in raw and all("attacker_side" in x and "defender_side" in x for x in raw["reports"]):
            candidates=[(path.name+"#"+str(i),{"battle":x,"attacker_side":x["attacker_side"],
                         "defender_side":x["defender_side"]}) for i,x in enumerate(raw["reports"],1)]
        elif "reports" in raw or "tests" in raw:
            excluded.append({"id":path.name,"reason":"grouped summaries: capacity/start or carryover unresolved"})
            continue
        for source,item in candidates:
            try:
                r=normalize(item,source,group=path.name[:10])
                if r["trace"]:
                    replay(r)
                records.append(r)
            except ValueError as exc:
                excluded.append({"id":source,"reason":str(exc)})
    return {"files":len(paths),"records":records,"excluded":excluded,
            "outcomes":dict(Counter(r["outcome"] for r in records)),
            "round_replays":sum(bool(r["trace"]) for r in records),
            "calibration":benchmark(records)}


if __name__=="__main__":
    print(json.dumps(audit(Path(__file__).resolve().parents[2]),indent=2))
