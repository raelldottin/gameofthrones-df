"""Read-only upgrade strategy. Costs and budgets require explicit fresh verification."""
import json
import re
from decimal import Decimal
from itertools import combinations
from pathlib import Path
from .reconcile import digest


def integer(v,lo=0,hi=10**12):
    return type(v) is int and lo<=v<=hi


def optimize(options,budget):
    """Exact bounded subset search under caller-selected integer utilities.
    Utilities are preferences, not combat outcomes. One alternative per group.
    Unknown currencies make the corresponding option ineligible.
    """
    if not isinstance(options,list) or len(options)>18 or not isinstance(budget,dict):
        raise ValueError("bounded explicit budget required")
    if any(not isinstance(k,str) or not k or not integer(v) for k,v in budget.items()):
        raise ValueError("invalid budget")
    ids=set();eligible=[];unknown=[]
    for o in options:
        if (not isinstance(o,dict) or set(o)!={"id","cost","utility","group"}
                or not all(isinstance(o[k],str) and o[k].strip() for k in ("id","group"))
                or o["id"] in ids or not integer(o["utility"],1)
                or not isinstance(o["cost"],dict) or not o["cost"]
                or any(not isinstance(k,str) or not k or not integer(v) for k,v in o["cost"].items())):
            raise ValueError("invalid upgrade option or cost")
        ids.add(o["id"])
        if not set(o["cost"])<=set(budget):
            unknown.append(o["id"]);continue
        eligible.append(o)
    keys=sorted(budget)
    best=(0,tuple(0 for _ in keys),())
    for n in range(1,len(eligible)+1):
        for subset in combinations(eligible,n):
            if len({o["group"] for o in subset})!=n:continue
            costs=tuple(sum(o["cost"].get(k,0) for o in subset) for k in keys)
            if any(c>budget[k] for k,c in zip(keys,costs)):continue
            score=sum(o["utility"] for o in subset)
            selected=tuple(sorted(o["id"] for o in subset))
            candidate=(score,costs,selected)
            if score>best[0] or (score==best[0] and (costs,selected)<(best[1],best[2])):
                best=candidate
    return {"status":"conditional_budget_plan","selected":list(best[2]),"utility":best[0],
            "spent":dict(zip(keys,best[1])),"unknown_budget":sorted(unknown),
            "spend_authorized":False,"battle_improvement":None}


def xp_gap(current,required):
    if not integer(current) or not isinstance(required,str):
        raise ValueError("invalid XP")
    m=re.fullmatch(r"(\d+(?:\.\d+)?)([KM]?)",required)
    if not m or (not m[2] and "." in m[1]):raise ValueError("invalid XP display")
    multiplier={"":1,"K":1000,"M":1000000}[m[2]]
    target=Decimal(m[1])*multiplier
    if target!=int(target) or target<=0:raise ValueError("invalid XP threshold")
    return {"gap":max(0,int(target)-current),"exact":not bool(m[2])}


def star_milestones(roster,marches,profiles):
    rows=[]
    for d in roster:
        n=d["name"];stars=d["stars"];relic=d["relics_toward_next_star"]
        if not integer(stars,0,10) or not integer(relic["current"]) or not integer(relic["required"],1):
            raise ValueError("invalid relic evidence")
        next_star=stars+1 if stars<10 else None
        profile=profiles.get(n,{})
        unlocks=[h["name"] for h in profile.get("habits",[]) if h.get("unlock_at_stars")==next_star and next_star is not None]
        rows.append({"name":n,"stars":stars,"next_star":next_star,"march":marches.get(n),
                     "missing_relics":max(0,relic["required"]-relic["current"]) if next_star is not None else None,
                     "current_relics":relic["current"],"required_relics":relic["required"],
                     "documented_next_habits":unlocks,"status":"dated_milestone_only",
                     "acquisition_cost":None})
    return sorted(rows,key=lambda x:(x["missing_relics"] is None,x["missing_relics"] or 0,x["name"]))


def load_context(root):
    root=Path(root)
    def read(path):return json.loads((root/path).read_text())
    roster=read("player-state/dragon-update-2026-11-26.json")
    profiles={}
    for d in roster["updates"]:
        path=root/"dragons"/(d["name"].lower()+".json")
        if path.exists():
            p=json.loads(path.read_text())
            if p.get("name")==d["name"]:profiles[d["name"]]=p
    return {"roster":roster,"season":read("player-state/dragon-reign-snapshot-2026-11-26.json"),
            "formations":read("armies/current-ten-marches-2026-11-26.json"),
            "habit_costs":read("player-state/habit-update-2026-09-27.json"),
            "commanders":read("player-state/commander-update-2026-11-25.json"),"profiles":profiles}


def plan(ctx):
    roster=ctx["roster"]["updates"];by={d["name"]:d for d in roster}
    if len(by)!=len(roster):raise ValueError("duplicate roster name")
    marches={}
    for m in ctx["formations"]["marches"]:
        for lane in ("left","vanguard","right"):
            name=m[lane]
            if name in marches:raise ValueError("duplicate dragon assignment")
            if name not in by:raise ValueError("unknown dragon")
            marches[name]=m["march"]
    stars=star_milestones(roster,marches,ctx["profiles"])
    costs=[]
    for item in ctx["habit_costs"]["updates"]:
        d=by.get(item["name"])
        nxt=item.get("next_upgrade")
        if not d or not nxt:continue
        levels=[h["level"] for h in d["habits"] if h["name"]==item["habit"]]
        if len(levels)!=1 or nxt["to_level"]!=nxt["from_level"]+1 or nxt["to_level"]>5:continue
        if levels[0]!=nxt["from_level"]:continue
        c=nxt["cost"]
        if not c or not all(isinstance(k,str) and integer(v) for k,v in c.items()):raise ValueError("invalid historic cost")
        old=next((v for v in item["levels"] if v["level"]==levels[0]),{})
        new=next((v for v in item["levels"] if v["level"]==nxt["to_level"]),{})
        effects={k:{"before":old[k],"after":new[k]} for k in sorted(old.keys()&new.keys()-{"level","power"})
                 if type(old[k]) in (int,float) and type(new[k]) in (int,float)}
        costs.append({"name":d["name"],"habit":item["habit"],"march":marches.get(d["name"]),
                      "from":levels[0],"to":nxt["to_level"],"cost":c,"effects":effects,
                      "cost_observed_date":ctx["habit_costs"]["observed_date"],
                      "status":"historical_cost_recheck"})
    commander=ctx["commanders"];resources=commander["resources"]
    previews=[]
    for c in commander["commanders"]:
        if not integer(c.get("rank"),1,100):continue
        for t in c.get("talents",[]):
            if not t.get("name") or not t.get("next_cost") or t.get("preview_rank")!=t["rank"]+1:continue
            previews.append({"name":t["name"],"group":c["name"],"from":t["rank"],"to":t["preview_rank"],
                             "cost":t["next_cost"],"effect_preview":{k:v for k,v in t.items() if isinstance(v,dict) and "next" in v},
                             "observed_date":commander["observed_date"],"status":"dated_preview_recheck"})
    season=ctx["season"];levels=[]
    for d in season["dragons"]:
        if d["name"] not in by:raise ValueError("unknown seasonal dragon")
        levels.append({"name":d["name"],"march":marches.get(d["name"]),"level":d["level"],
                       "capacity":d["displayed_troop_capacity"],**xp_gap(d["xp"]["current"],d["xp"]["required_display"])})
    if len({d["name"] for d in levels})!=len(levels) or {d["name"] for d in levels}!=set(by):
        raise ValueError("season roster mismatch")
    return {"status":"conditional_strategy_only","basis":digest(ctx),"roster_date":ctx["roster"]["observed_date"],
            "stars":stars,"habit_candidates":costs,"dragon_core_budget":None,
            "commander_previews":previews,"commander_budget":{"observed_date":commander["observed_date"],
              "medals":None,"medals_display":resources["commander_medals_display"],"honors":resources["commander_honors"],
              "onyx_honors":resources["onyx_honors"],"gold":resources["gold"],"freshly_verified":False},
            "season":{"status":"dated_snapshot_only","observed_date":season["observed_date"],"reign_id":season["reign_id"],
                      "levels":sorted(levels,key=lambda x:(x["gap"],x["name"]))},
            "battle_improvement":None,"spend_authorized":False}


if __name__=="__main__":
    print(json.dumps(plan(load_context(Path(__file__).resolve().parents[2])),indent=2))
