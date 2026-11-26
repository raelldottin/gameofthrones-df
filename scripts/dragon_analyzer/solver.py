"""Exact additive roster allocation, not a battle-strength model."""
from collections import Counter
from itertools import permutations
from pathlib import Path
import json
from .reconcile import digest

POSITIONS=("left","vanguard","right")
TROOPS={"Archers","Cavalry","Spearmen","Shieldbearers","Siege"}


def score(dragon):
    return 10*dragon["stars"]+2*sum(dragon["habits"])


def optimize(dragons, quotas, retain=None, *, objective="permanent"):
    """Exact dynamic program over troop quotas; additive score, retention, stable tie.
    Each dragon considered once; no position or battle effects are modeled.
    """
    if objective not in ("permanent","readiness"):
        raise ValueError("invalid objective")
    names=[d["name"] for d in dragons]
    if len(set(names))!=len(names):
        raise ValueError("duplicate dragon")
    if not quotas or any(k not in TROOPS or type(v) is not int or v<0 for k,v in quotas.items()):
        raise ValueError("invalid quotas")
    types=tuple(sorted(quotas))
    goal=tuple(quotas[t] for t in types)
    retain=retain or {}
    # tuple comparison: chosen objective, retained assignments, deterministic choice path.
    states={tuple(0 for _ in types):(0,0,())}
    ordered=sorted(dragons,key=lambda d:d["name"])
    for d in ordered:
        if (type(d["stars"]) is not int or not 1<=d["stars"]<=10
                or len(d["habits"])!=d["stars"]//2
                or any(type(x) is not int or not 1<=x<=5 for x in d["habits"])
                or not set(d["affinities"])<=TROOPS):
            raise ValueError("invalid dragon progression or affinity")
        next_states={}
        for counts,(points,kept,path) in states.items():
            options=[(counts,(points,kept,path+(-1,)))]
            for i,t in enumerate(types):
                if counts[i]>=goal[i] or t not in d["affinities"]:
                    continue
                new=list(counts);new[i]+=1
                value=score(d) if objective=="permanent" else d["capacity"]
                options.append((tuple(new),(points+value,kept+int(retain.get(d["name"])==t),path+(i,))))
            for key,value in options:
                if key not in next_states or value>next_states[key]:
                    next_states[key]=value
        states=next_states
    if goal not in states:
        raise ValueError("infeasible troop quotas")
    points,kept,path=states[goal]
    out={t:[] for t in types}
    for d,i in zip(ordered,path):
        if i>=0:
            out[types[i]].append(d["name"])
    permanent=sum(score(d) for d,i in zip(ordered,path) if i>=0)
    return {"score":permanent,"objective_value":points,"retained":kept,"assignments":out}


def arrange(assignments, baseline, dragons):
    """Preserve baseline positions where possible; fill holes deterministically.
    Does not optimize positional mechanics or imply synergy.
    """
    by={d["name"]:d for d in dragons}
    available={t:set(ns) for t,ns in assignments.items()}
    out=[]
    for m in sorted(baseline,key=lambda x:x["march"]):
        row={"march":m["march"],"troop_type":m["troop_type"]}
        for pos in POSITIONS:
            n=m[pos]
            row[pos]=n if n in available[row["troop_type"]] else None
            if row[pos] is not None:
                available[row["troop_type"]].remove(n)
        out.append(row)
    for row in out:
        pool=available[row["troop_type"]]
        for pos in POSITIONS:
            if row[pos] is None:
                n=min(pool,key=lambda n:(-score(by[n]),n))
                row[pos]=n;pool.remove(n)
    return out


def assign_commanders(marches,dragons,commanders):
    """Exact distinct assignment maximizing preferred-trait counts, not talent effects."""
    cs=sorted((c for c in commanders if type(c.get("rank")) is int and c["rank"]>0
               and c.get("preferred_traits")),key=lambda c:c["name"])
    ms=sorted(marches,key=lambda m:m["march"])
    if len(cs)>len(ms):
        raise ValueError("more eligible commanders than marches")
    if len({c["name"] for c in cs})!=len(cs):
        raise ValueError("duplicate commander")
    traits={d["name"]:d["trait"] for d in dragons}
    def matches(c,m):
        return sum(traits[m[p]] in c["preferred_traits"] for p in POSITIONS)
    best=max(permutations(ms,len(cs)),key=lambda rows:(sum(matches(c,m) for c,m in zip(cs,rows)),
                                                      tuple(-m["march"] for m in rows)))
    return {m["march"]:c["name"] for c,m in zip(cs,best)}


def basis(inputs):
    return digest(inputs)


def load_inputs(root):
    def read(path):
        return json.loads((Path(root)/path).read_text())
    return {"roster":read("player-state/dragon-update-2026-11-26.json"),
            "season":read("player-state/dragon-reign-snapshot-2026-11-26.json"),
            "commanders":read("player-state/commander-update-2026-11-25.json"),
            "baseline":read("armies/current-ten-marches-2026-11-26.json"),
            "affinity":read("quality/fixtures/2026-11-26.json")["affinity"],
            "equipment":None,"ability_catalog":None,"reign":None,
            "objective_version":"additive-v1"}


def evaluate(inputs):
    p=inputs["roster"]["updates"]
    s={d["name"]:d for d in inputs["season"]["dragons"]}
    aff=inputs["affinity"]
    if len(s)!=len(inputs["season"]["dragons"]) or set(s)!=set(aff) or set(s)!={d["name"] for d in p}:
        raise ValueError("roster mismatch")
    dragons=[{"name":d["name"],"stars":d["stars"],"habits":[h["level"] for h in d["habits"]],
              "affinities":aff[d["name"]],"capacity":s[d["name"]]["displayed_troop_capacity"],
              "trait":d["temperament"]} for d in p]
    by={d["name"]:d for d in dragons}
    old=inputs["baseline"]["marches"]
    quotas=Counter(m["troop_type"] for m in old)
    quotas={k:v*3 for k,v in quotas.items()}
    retain={m[pos]:m["troop_type"] for m in old for pos in POSITIONS}
    def metrics(marches):
        assigned=[m[pos] for m in marches for pos in POSITIONS]
        violations=sum(m["troop_type"] not in by[m[pos]]["affinities"] for m in marches for pos in POSITIONS)
        if len(set(assigned))!=len(assigned) or violations:
            raise ValueError("invalid formation")
        return {"count":len(assigned),"score":sum(score(by[n]) for n in assigned),
                "stars":sum(by[n]["stars"] for n in assigned),
                "habit_levels":sum(sum(by[n]["habits"]) for n in assigned),
                "capacity":sum(by[n]["capacity"] for n in assigned),
                "affinity_violations":violations}
    baseline=metrics(old)
    optimal=optimize(dragons,quotas,retain)
    candidate=arrange(optimal["assignments"],old,dragons)
    cm=metrics(candidate)
    if cm["score"]!=optimal["score"]:
        raise RuntimeError("assignment score mismatch")
    commands=assign_commanders(candidate,dragons,inputs["commanders"]["commanders"])
    for m in candidate:
        m["commander_candidate"]=commands.get(m["march"])
        m["permanent_score"]=sum(score(by[m[pos]]) for pos in POSITIONS)
        m["displayed_capacity"]=sum(by[m[pos]]["capacity"] for pos in POSITIONS)
        m["reign_levels"]=[s[m[pos]]["level"] for pos in POSITIONS]
    readiness=optimize(dragons,quotas,retain,objective="readiness")
    ready_marches=arrange(readiness["assignments"],old,dragons)
    rm=metrics(ready_marches)
    if rm["capacity"]!=readiness["objective_value"]:
        raise RuntimeError("readiness score mismatch")
    assigned={m[pos] for m in candidate for pos in POSITIONS}
    return {"status":"unvalidated_additive_candidate","objective_version":inputs["objective_version"],
            "basis":basis(inputs),"baseline":baseline,"candidate":cm,"marches":candidate,
            "bench":sorted(set(by)-assigned),"retained_troop_assignments":optimal["retained"],
            "readiness_alternative":rm,"readiness_marches":ready_marches,
            "recommendation_policy":"alternatives_only","battle_improvement":None,"reign":inputs["reign"],"equipment":inputs["equipment"],
            "ability_catalog":inputs["ability_catalog"]}


if __name__=="__main__":
    print(json.dumps(evaluate(load_inputs(Path(__file__).resolve().parents[2])),indent=2))
