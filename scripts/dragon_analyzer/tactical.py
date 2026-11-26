"""Evidence-constrained tactical planning. Opportunity points are not damage."""
import hashlib
import json
from itertools import permutations
from pathlib import Path
from .reconcile import digest
from .battle import matchup

POSITIONS=("left","vanguard","right")
FIELD_TYPES={"Cavalry","Spearmen","Shieldbearers","Archers"}


def directional_links(order,dragons,rules,attacks):
    by={d["name"]:d for d in dragons}
    if len(order)!=3 or len(set(order))!=3 or not set(order)<=by.keys():
        raise ValueError("invalid trio")
    links=[]
    for rule in rules:
        owner=rule["owner"]
        if owner not in order: continue
        d=by[owner]
        if d["stars"]<rule["gate"]: continue
        levels=[h["level"] for h in d["habits"] if h["name"]==rule["habit"]]
        if len(levels)!=1 or str(levels[0]) not in rule["levels"]: continue
        target=order[POSITIONS.index(rule["position"])]
        # Unknown fallback targeting is not scored.
        if target==owner: continue
        active=set()
        sources=set()
        for a in attacks:
            if a["owner"]==target and a["damage"]==rule["damage"]:
                overlap=set(a["rounds"])&set(rule["rounds"])
                if overlap:
                    active.update(overlap);sources.add(a["source"])
        if active:
            value=rule["levels"][str(levels[0])]
            links.append({"owner":owner,"habit":rule["habit"],"target":target,
                          "damage":rule["damage"],"rounds":sorted(active),
                          "percent":value,"points":round(value*len(active),6),
                          "sources":sorted(sources|{rule["source"]})})
    return links


def rank_positions(order,dragons,rules,attacks):
    original=tuple(order)
    def assess(p):
        links=directional_links(p,dragons,rules,attacks)
        return round(sum(x["points"] for x in links),6),links
    baseline,base_links=assess(original)
    options=[]
    for p in permutations(original):
        value,links=assess(p)
        options.append((value,sum(a==b for a,b in zip(p,original)),p,links))
    points,_,candidate,links=max(options,key=lambda x:(x[0],x[1],x[2]))
    return {"baseline":list(original),"candidate":list(candidate),"baseline_points":baseline,
            "candidate_points":points,"baseline_links":base_links,"candidate_links":links,
            "permutations_evaluated":len(options),"status":"unvalidated_position_alternative"}


def deploy(marches,enemies):
    """Exact assignment of disjoint presets to explicit field targets, max five."""
    if not 1<=len(enemies)<=5: raise ValueError("one to five simultaneous targets required")
    if any(e not in FIELD_TYPES|{"Siege"} for e in enemies): raise ValueError("unknown enemy troop")
    if len({m["march"] for m in marches})!=len(marches): raise ValueError("duplicate march")
    for m in marches:
        if (m["troop_type"] not in FIELD_TYPES or type(m["capacity"]) is not int
                or m["capacity"]<1 or len(m["dragons"])!=3 or len(set(m["dragons"]))!=3):
            raise ValueError("invalid deployment preset")
    best=None
    for group in permutations(marches,len(enemies)):
        names=[n for m in group for n in m["dragons"]]
        if len(names)!=len(set(names)): continue
        mods=[matchup(m["troop_type"],e) for m,e in zip(group,enemies)]
        if any(x is None for x in mods): continue
        advantages=sum(x>1 for x in mods)
        disadvantages=sum(x<1 for x in mods)
        capacity=sum(m["capacity"] for m in group)
        objective=(advantages,-disadvantages,capacity,tuple(-m["march"] for m in group))
        if best is None or objective>best[0]: best=(objective,group,mods)
    if best is None: raise ValueError("infeasible disjoint deployment")
    objective,group,mods=best
    return {"status":"unvalidated_matchup_alternative","advantage_count":objective[0],
            "disadvantage_count":-objective[1],"capacity":objective[2],
            "assignments":[{"march":m["march"],"enemy":e,"troop_type":m["troop_type"],
                            "troop_damage_modifier":v,"capacity":m["capacity"]}
                           for m,e,v in zip(group,enemies,mods)],
            "battle_improvement":None}


def load_context(root):
    root=Path(root)
    def read(path):return json.loads((root/path).read_text())
    catalog=read("quality/fixtures/tactical-rules-v1.json")
    for path,expected in catalog["source_blobs"].items():
        data=(root/path).read_bytes()
        blob=hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
        if blob!=expected:
            raise ValueError("mechanics source changed: "+path)
    return {"roster":read("player-state/dragon-update-2026-11-26.json"),
            "season":read("player-state/dragon-reign-snapshot-2026-11-26.json"),
            "baseline":read("armies/current-ten-marches-2026-11-26.json"),
            "commanders":read("player-state/commander-update-2026-11-25.json"),
            "affinity":read("quality/fixtures/2026-11-26.json")["affinity"],
            "catalog":catalog,"equipment":None,"reign":None}


def evaluate(inputs):
    ds=inputs["roster"]["updates"]
    by={d["name"]:d for d in ds}
    season={d["name"]:d for d in inputs["season"]["dragons"]}
    catalog=inputs["catalog"]
    rules=catalog["directional_rules"]
    attacks=[a for a in catalog["attacks"] if a["owner"] in by
             and by[a["owner"]].get("command")==a["command"]
             and by[a["owner"]]["stars"]>=a.get("gate",0)]
    results=[];presets=[]
    for m in inputs["baseline"]["marches"]:
        order=tuple(m[p] for p in POSITIONS)
        if not all(m["troop_type"] in inputs["affinity"][n] for n in order):
            raise ValueError("unverified positive affinity")
        r=rank_positions(order,ds,rules,attacks)
        cap=sum(season[n]["displayed_troop_capacity"] for n in order)
        if cap!=m["displayed_troop_capacity_sum"]:
            raise ValueError("stale capacity")
        if int(cap)!=cap: raise ValueError("nonintegral capacity")
        cap=int(cap)
        r.update(march=m["march"],troop_type=m["troop_type"],capacity=cap)
        results.append(r)
        presets.append({"march":m["march"],"troop_type":m["troop_type"],"capacity":cap,"dragons":list(order)})
    if len({n for m in presets for n in m["dragons"]})!=3*len(presets):
        raise ValueError("duplicate dragon across baseline")
    commanders={}
    for c in inputs["commanders"]["commanders"]:
        if type(c.get("rank")) is not int or c["rank"]<=0: continue
        commanders[c["name"]]={"rank":c["rank"],"preferred_traits":c.get("preferred_traits",[]),
            "active_talents":[t["name"] for t in c.get("talents",[]) if t.get("name") and type(t.get("rank")) is int and t["rank"]>0],
            "unidentified_active_talents":sum(t.get("name") is None and type(t.get("rank")) is int and t["rank"]>0 for t in c.get("talents",[])),
            "effect_scored":False}
    top=sorted(presets,key=lambda m:(-m["capacity"],m["march"]))[:5]
    return {"status":"unvalidated_tactical_alternatives","basis":digest(inputs),"marches":results,
            "baseline_points":round(sum(m["baseline_points"] for m in results),6),
            "candidate_points":round(sum(m["candidate_points"] for m in results),6),
            "capacity_only_deployment":[m["march"] for m in top],
            "capacity_only_total":sum(m["capacity"] for m in top),
            "illustrative_counter_deployment":deploy(presets,["Cavalry","Spearmen","Archers","Shieldbearers","Siege"]),
            "commander_effects":commanders,"battle_improvement":None}


if __name__=="__main__":
    print(json.dumps(evaluate(load_context(Path(__file__).resolve().parents[2])),indent=2))
