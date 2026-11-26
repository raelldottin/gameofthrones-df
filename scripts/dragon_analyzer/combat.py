"""Illustrative round engine and diagnostic calibration, not calibrated game predictions."""
import json
import math
import random
from pathlib import Path
from statistics import mean
from .reconcile import digest
from .tactical import load_context
from .battle import audit

KINDS={"damage","heal","weakened","resistance","nullify"}
DAMAGE={"Physical","Tactical","Fire"}
TARGETS={"same","adjacent","any","self","others","adjacent_allies"}
UNIT_FIELDS={"name","side","lane","stars","troops","damage_unit","recovery_unit"}
ACTION_FIELDS={"actor","kind","rounds","target","rate","gate","chance","duration","damage","count"}


def integer(value,lo,hi):
    return type(value) is int and lo<=value<=hi


def numeric(value,lo,hi):
    return type(value) in (int,float) and math.isfinite(value) and lo<=value<=hi


def validate(units,actions,seed):
    if not isinstance(units,list) or not 2<=len(units)<=6 or not integer(seed,0,2**64-1):
        raise ValueError("invalid scenario")
    names=set();lanes=set();sides=set()
    for u in units:
        if (not isinstance(u,dict) or set(u)!=UNIT_FIELDS or not isinstance(u["name"],str)
                or not u["name"].strip() or u["name"] in names or u["side"] not in ("player","enemy")
                or not integer(u["lane"],0,2) or (u["side"],u["lane"]) in lanes
                or not integer(u["stars"],0,10) or not integer(u["troops"],1,1_000_000)
                or not numeric(u["damage_unit"],0,1_000_000) or not numeric(u["recovery_unit"],0,1_000_000)):
            raise ValueError("invalid unit")
        names.add(u["name"]);lanes.add((u["side"],u["lane"]));sides.add(u["side"])
    if len(sides)!=2 or not isinstance(actions,list) or len(actions)>200:
        raise ValueError("invalid sides or actions")
    for a in actions:
        if (not isinstance(a,dict) or not ACTION_FIELDS<=set(a) or set(a)-ACTION_FIELDS-{"resistance_multiplier"}
                or a["actor"] not in names or a["kind"] not in KINDS
                or a["target"] not in TARGETS or a["damage"] not in DAMAGE
                or not isinstance(a["rounds"],list) or not a["rounds"]
                or not all(integer(r,1,10) for r in a["rounds"])
                or len(set(a["rounds"]))!=len(a["rounds"])
                or not numeric(a["rate"],0,10000) or not numeric(a["chance"],0,100)
                or not integer(a["gate"],0,10) or not integer(a["duration"],1,10)
                or not integer(a["count"],1,3)):
            raise ValueError("invalid action")
        if a["kind"] in ("weakened","resistance","nullify") and a["rate"]>100:
            raise ValueError("invalid status rate")
        if "resistance_multiplier" in a and (a["kind"]!="heal" or not numeric(a["resistance_multiplier"],1,3)):
            raise ValueError("invalid conditional heal")
        hostile=a["kind"] in ("damage","weakened","nullify")
        if hostile and a["target"] in ("self","others","adjacent_allies"):
            raise ValueError("hostile action targets ally")


def simulate(units,actions,*,seed):
    """Hypothetical phases: statuses, simultaneous damage, survivor recovery.
    Lanes are fixed; adjacency includes same and neighboring lanes. Targets
    sampled without replacement. No actual game ordering/stacking is asserted.
    """
    validate(units,actions,seed)
    rng=random.Random(seed)
    by={u["name"]:u for u in units}
    troops={n:u["troops"] for n,u in by.items()}
    effects={n:{} for n in by}
    trace=[]
    for r in range(1,11):
        alive={n for n,v in troops.items() if v>0}
        def targets(a):
            owner=by[a["actor"]]
            hostile=a["kind"] in ("damage","weakened","nullify")
            eligible=[]
            for n in sorted(alive):
                t=by[n]
                if (t["side"]!=owner["side"])!=hostile: continue
                mode=a["target"]
                if mode=="self" and n!=a["actor"]: continue
                if mode=="others" and n==a["actor"]: continue
                if mode=="same" and t["lane"]!=owner["lane"]: continue
                if mode in ("adjacent","adjacent_allies") and abs(t["lane"]-owner["lane"])>1: continue
                if mode=="adjacent_allies" and n==a["actor"]: continue
                eligible.append(n)
            return rng.sample(eligible,min(len(eligible),a["count"]))
        for n in effects:
            effects[n]={k:v for k,v in effects[n].items() if v[1]>=r}
        eligible=[a for a in actions if a["actor"] in alive and r in a["rounds"]
                  and by[a["actor"]]["stars"]>=a["gate"]]
        events=[]
        for a in eligible:
            if a["kind"] in ("damage","heal"): continue
            if rng.random()*100>=a["chance"]: continue
            for n in targets(a):
                old=effects[n].get(a["kind"],(0,0))
                # Explicit illustrative non-stacking policy: retain stronger active effect.
                value=max(old[0],a["rate"])
                end=max(old[1],r+a["duration"]-1)
                effects[n][a["kind"]]=(value,end)
                events.append({"actor":a["actor"],"target":n,"kind":a["kind"],"rate":a["rate"]})
        losses=dict.fromkeys(by,0)
        for a in eligible:
            if a["kind"]!="damage" or rng.random()*100>=a["chance"]: continue
            strength=by[a["actor"]]["damage_unit"]*a["rate"]/100
            strength*=1-effects[a["actor"]].get("weakened",(0,0))[0]/100
            for n in targets(a):
                loss=round(strength*(1-effects[n].get("resistance",(0,0))[0]/100))
                losses[n]+=loss
                events.append({"actor":a["actor"],"target":n,"kind":"damage",
                               "damage":a["damage"],"nominal":loss})
        for n in troops: troops[n]=max(0,troops[n]-losses[n])
        # Eliminated actors/targets cannot recover or act after the damage phase.
        alive={n for n in alive if troops[n]>0}
        for a in eligible:
            if a["kind"]!="heal" or a["actor"] not in alive or rng.random()*100>=a["chance"]: continue
            for n in targets(a):
                if "nullify" in effects[n]: continue
                rate=a["rate"]*(a.get("resistance_multiplier",1) if "resistance" in effects[n] else 1)
                restored=min(by[n]["troops"]-troops[n],round(by[a["actor"]]["recovery_unit"]*rate/100))
                troops[n]+=restored
                events.append({"actor":a["actor"],"target":n,"kind":"heal","restored":restored})
        trace.append({"round":r,"troops":dict(troops),"events":events})
        sides={by[n]["side"] for n,v in troops.items() if v>0}
        if len(sides)<2: break
    outcome="stalemate" if len(sides)==2 else "victory" if sides=={"player"} else "defeat" if sides=={"enemy"} else "mutual_elimination"
    return {"status":"illustrative_only","end":troops,"rounds":trace,"outcome":outcome,
            "scenario_digest":digest({"units":units,"actions":actions}),"seed":seed,
            "win_probability":None,"release_accepted":False}


def sample(units,actions,*,seed,trials):
    if not integer(trials,1,1000) or not integer(seed,0,2**64-1):
        raise ValueError("invalid sampling budget")
    rng=random.Random(seed)
    results=[simulate(units,actions,seed=rng.getrandbits(64)) for _ in range(trials)]
    by_side={s:[sum(x["end"][u["name"]] for u in units if u["side"]==s) for x in results]
             for s in ("player","enemy")}
    return {"status":"illustrative_sensitivity_only","trials":trials,"seed":seed,
            "scenario_digest":results[0]["scenario_digest"],
            "remaining_troops":{s:{"min":min(v),"max":max(v),"mean":mean(v)} for s,v in by_side.items()},
            "win_probability":None,"release_accepted":False}


def compile_actions(root,names):
    """Partial historical command schedule; no inferred missing ability or coefficient."""
    root=Path(root)
    ctx=load_context(root)  # verify pinned historical mechanics source blobs
    by={d["name"]:d for d in ctx["roster"]["updates"]}
    if not 1<=len(names)<=3 or len(set(names))!=len(names) or not all(n in by for n in names):
        raise ValueError("invalid owned roster subset")
    supported={"Malachite","Shimmer","Dawnseeker","Syrax","Arrax"}
    actions=[];sources={};unsupported=[]
    for name in names:
        if name not in supported:
            unsupported.append(name);continue
        path="dragons/"+name.lower()+".json"
        profile=json.loads((root/path).read_text())
        d=by[name];cmd=profile["command"]
        if d.get("command")!=cmd["name"]:
            unsupported.append(name);continue
        sources[name]=ctx["catalog"]["source_blobs"][path]
        v=cmd["displayed_values"]
        def add(kind,rounds,target,rate,count=1,gate=0,damage="Tactical",chance=100,duration=1,**extra):
            actions.append(dict(actor=name,kind=kind,rounds=rounds,target=target,rate=rate,
                                gate=gate,damage=damage,count=count,chance=chance,duration=duration,**extra))
        if name=="Malachite":
            add("damage",v["tactical_damage_rounds"],"same",v["tactical_damage_rate_percent"])
            add("heal",v["recovery_rounds"],"any",v["recovery_rate_percent"],3)
        elif name=="Shimmer":
            add("damage",v["tactical_damage_rounds"],"adjacent",v["tactical_damage_rate_percent"],2)
            level=next((x["level"] for x in d["habits"] if x["name"]=="Loyal Shield"),None)
            habit=next(x for x in profile["habits"] if x["name"]=="Loyal Shield")
            row=next((x for x in habit["levels"] if x["level"]==level),None)
            if d["stars"]>=habit["unlock_at_stars"] and row:
                add("heal",v["six_star_recovery_rounds"],"others",row["recovery_rate_percent"],2,
                    habit["unlock_at_stars"],resistance_multiplier=2)
        elif name=="Dawnseeker":
            # Only current below-six-star command; do not guess later habit scaling.
            if d["stars"]>=6:
                unsupported.append(name);continue
            add("damage",v["tactical_damage_rounds"],"same",v["tactical_damage_rate_percent"])
            add("heal",v["recovery_rounds"],"adjacent_allies",v["recovery_rate_percent"],2)
        elif name=="Syrax":
            add("damage",v["tactical_damage_rounds"],"adjacent",v["tactical_damage_rate_percent"])
        elif name=="Arrax":
            add("damage",v["physical_damage_rounds"],"adjacent",v["physical_damage_rate_percent"],2,damage="Physical")
            add("weakened",v["weakened_rounds"],"adjacent",abs(v["weakened_damage_dealt_percent"]),
                chance=v["weakened_chance_percent"],duration=v["weakened_duration_rounds"])
    return {"complete":False,"actions":actions,"unsupported":unsupported,"sources":sources,
            "omitted":["Basic Attacks","stat scaling","command/habit effects not explicitly compiled",
                       "lane merging","control and initiative","commander effects","gear","troop counter damage"],
            "status":"partial_schedule_only"}


def prospective_gate(train,holdout,*,mode):
    """Diagnostic only. Supplied prediction records cannot prove prospective capture.
    Require disjoint groups and scenario hashes. No trust or release authority.
    """
    def blocked(reason):
        return {"status":"blocked","reason":reason,"release_accepted":False,"win_probability":None}
    if mode not in ("pve","pvp") or not isinstance(train,list) or not isinstance(holdout,list):
        return blocked("invalid_partition")
    required={"id","group","mode","partition","scenario_digest","start","end","prediction",
              "baseline","observed_outcome","predicted_outcome"}
    for partition,rows in (("train",train),("holdout",holdout)):
        for r in rows:
            if (not isinstance(r,dict) or set(r)!=required or r["mode"]!=mode or r["partition"]!=partition
                    or not all(isinstance(r[k],str) and r[k].strip() for k in ("id","group"))
                    or not isinstance(r["scenario_digest"],str) or len(r["scenario_digest"])!=64
                    or any(c not in "0123456789abcdef" for c in r["scenario_digest"])
                    or not isinstance(r["start"],list) or len(r["start"])!=2
                    or not all(integer(v,1,1_000_000) for v in r["start"])):
                return blocked("invalid_record")
            for k in ("end","prediction","baseline"):
                if not isinstance(r[k],list) or len(r[k])!=2 or not all(integer(v,0,s) for v,s in zip(r[k],r["start"])):
                    return blocked("invalid_record")
            def outcome(x):
                return "mutual_elimination" if x==[0,0] else "victory" if x[1]==0 else "defeat" if x[0]==0 else "stalemate"
            if r["observed_outcome"]!=outcome(r["end"]) or r["predicted_outcome"]!=outcome(r["prediction"]):
                return blocked("invalid_outcome")
    if len({r["id"] for r in train+holdout})!=len(train)+len(holdout): return blocked("duplicate_report")
    if {r["group"] for r in train}&{r["group"] for r in holdout}: return blocked("group_leakage")
    if {r["scenario_digest"] for r in train}&{r["scenario_digest"] for r in holdout}: return blocked("scenario_leakage")
    if len({r["group"] for r in train})<20 or len({r["group"] for r in holdout})<20:
        return blocked("insufficient_independent_groups")
    def group_error(k):
        grouped={}
        for r in holdout:
            error=mean(abs(a-b)/s for a,b,s in zip(r[k],r["end"],r["start"]))
            grouped.setdefault(r["group"],[]).append(error)
        return round(mean(mean(v) for v in grouped.values()),9)
    error=group_error("prediction");baseline=group_error("baseline")
    if error>=baseline: return blocked("no_baseline_improvement")
    return {"status":"diagnostic_only","mean_error":error,"baseline_error":baseline,
            "holdout_groups":len({r["group"] for r in holdout}),
            "release_accepted":False,"win_probability":None}



FORECAST_FIELDS={"id","group","mode","partition","scenario_digest","start","prediction","baseline","predicted_outcome"}
OUTCOME_FIELDS={"id","scenario_digest","end","observed_outcome"}


def hex_digest(x):
    return isinstance(x,str) and len(x)==64 and all(c in "0123456789abcdef" for c in x)


def freeze_predictions(train,forecasts,*,mode,model_digest):
    """Generate a manifest BEFORE capture; caller must externally timestamp/checkpoint it."""
    if mode not in ("pve","pvp") or not hex_digest(model_digest) or not isinstance(train,list) or not isinstance(forecasts,list) or not forecasts:
        raise ValueError("invalid forecast manifest")
    for f in forecasts:
        if (not isinstance(f,dict) or set(f)!=FORECAST_FIELDS or f["mode"]!=mode
                or f["partition"]!="holdout" or not isinstance(f["id"],str) or not f["id"]
                or not isinstance(f["group"],str) or not f["group"] or not hex_digest(f["scenario_digest"])):
            raise ValueError("invalid forecast fields")
        if f["baseline"]!=f["start"]:
            raise ValueError("baseline must be fixed no-change prediction")
    if len({f["id"] for f in forecasts})!=len(forecasts):
        raise ValueError("duplicate forecast")
    # Serialize and reparse to detach mutable caller references.
    return json.loads(json.dumps({"version":1,"mode":mode,"model_digest":model_digest,
                                  "training_digest":digest(train),"forecasts":forecasts},
                                 allow_nan=False))


def evaluate_frozen(manifest,expected_digest,train,outcomes):
    """Compare only frozen forecasts; the externally trusted checkpoint is required.
    This checks content binding, not timestamp, independent source or actual model execution.
    """
    def blocked(reason):
        return {"status":"blocked","reason":reason,"release_accepted":False,"win_probability":None}
    if not hex_digest(expected_digest) or digest(manifest)!=expected_digest:
        return blocked("checkpoint_mismatch")
    if (not isinstance(manifest,dict) or set(manifest)!={"version","mode","model_digest","training_digest","forecasts"}
            or manifest["version"]!=1 or not hex_digest(manifest["model_digest"])):
        return blocked("invalid_manifest")
    if digest(train)!=manifest["training_digest"]:
        return blocked("training_changed")
    try:
        checked=freeze_predictions(train,manifest["forecasts"],mode=manifest["mode"],model_digest=manifest["model_digest"])
    except ValueError:
        return blocked("invalid_manifest")
    if not isinstance(outcomes,list) or any(not isinstance(o,dict) or set(o)!=OUTCOME_FIELDS
                                           or not isinstance(o["id"],str) for o in outcomes):
        return blocked("invalid_outcomes")
    by={o["id"]:o for o in outcomes}
    forecasts=checked["forecasts"]
    if len(by)!=len(outcomes) or set(by)!={f["id"] for f in forecasts}:
        return blocked("outcome_census_mismatch")
    rows=[]
    for f in forecasts:
        o=by[f["id"]]
        if o["scenario_digest"]!=f["scenario_digest"]:
            return blocked("outcome_scenario_mismatch")
        rows.append({**f,**o})
    result=prospective_gate(train,rows,mode=manifest["mode"])
    return {**result,"manifest_digest":expected_digest,"model_digest":manifest["model_digest"]}


if __name__=="__main__":
    root=Path(__file__).resolve().parents[2]
    print(json.dumps({"march_1_partial":compile_actions(root,["Sheepstealer","Malachite","Shimmer"]),
                      "historical_complete_traces":audit(root)["round_replays"],
                      "prospective_gate":prospective_gate([],[],mode="pve")},indent=2))
