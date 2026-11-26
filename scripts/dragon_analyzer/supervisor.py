"""Bounded workflow contract. Dispatcher authentication and isolation are external."""
import copy
import hashlib
import math
import re

from .reconcile import digest

STAGES=("Research","Plan","Write","Review","Benchmark","QA")
DIMENSIONS={"correctness":35,"test_effectiveness":25,"architecture":20,
            "reproducibility":10,"operational_safety":10}
REQUIRED_GATES={"tests","mutations","holdout","architecture"}
MAX_ARTIFACT=2_000_000


def hash_bytes(value):
    return hashlib.sha256(value).hexdigest()


def hex64(value):
    return isinstance(value,str) and bool(re.fullmatch(r"[0-9a-f]{64}",value))


def nonblank(value):
    return isinstance(value,str) and bool(value.strip()) and value==value.strip()


def number(value):
    return type(value) in (int,float) and math.isfinite(value)


def validate_policy(p):
    if not isinstance(p,dict) or set(p)!={"fixture_hash","baseline_hash","gates","metrics","max_repairs","min_score"}:
        raise ValueError("invalid policy fields")
    if not hex64(p["fixture_hash"]) or not hex64(p["baseline_hash"]):
        raise ValueError("invalid policy hashes")
    g=p["gates"]
    if (not isinstance(g,list) or not all(nonblank(x) for x in g)
            or len(set(g))!=len(g) or not REQUIRED_GATES<=set(g)):
        raise ValueError("missing or invalid hard gates")
    if (type(p["max_repairs"]) is not int or not 0<=p["max_repairs"]<=10
            or type(p["min_score"]) is not int or not 95<=p["min_score"]<=100):
        raise ValueError("invalid acceptance or repair budget")
    if not isinstance(p["metrics"],dict) or not p["metrics"]:
        raise ValueError("missing benchmark metrics")
    for k,m in p["metrics"].items():
        if not nonblank(k) or not isinstance(m,dict):
            raise ValueError("invalid metric policy")
        direction=m.get("direction")
        bound="min" if direction=="higher" else "max"
        if (direction not in ("higher","lower") or set(m)!={bound,"baseline","direction"}
                or not number(m[bound]) or not number(m["baseline"])):
            raise ValueError("invalid metric policy")


def validate_benchmark(b,p,candidate):
    if not isinstance(b,dict) or set(b)!={"fixture_hash","baseline_hash","candidate_hash","gates","metrics"}:
        return None
    if (b["candidate_hash"]!=candidate or b["fixture_hash"]!=p["fixture_hash"]
            or b["baseline_hash"]!=p["baseline_hash"]):
        return None
    g,m=b["gates"],b["metrics"]
    if (not isinstance(g,dict) or set(g)!=set(p["gates"]) or any(type(v) is not bool for v in g.values())
            or not isinstance(m,dict) or set(m)!=set(p["metrics"]) or not all(number(v) for v in m.values())):
        return None
    passed=all(g.values())
    for k,s in p["metrics"].items():
        v=m[k]
        if s["direction"]=="higher":
            passed=passed and v>=max(s["min"],s["baseline"])
        else:
            passed=passed and v<=min(s["max"],s["baseline"])
    return passed


def validate_evaluation(e,candidate,benchmark_hash,known):
    if not isinstance(e,dict) or set(e)!={"benchmark_hash","candidate_hash","dimensions"}:
        return None
    if e["candidate_hash"]!=candidate or e["benchmark_hash"]!=benchmark_hash:
        return None
    dims=e["dimensions"]
    if not isinstance(dims,dict) or set(dims)!=set(DIMENSIONS):
        return None
    for k,d in dims.items():
        if (not isinstance(d,dict) or set(d)!={"score","evidence"} or type(d["score"]) is not int
                or not 0<=d["score"]<=DIMENSIONS[k] or not isinstance(d["evidence"],list)
                or not d["evidence"] or not all(isinstance(x,str) and x in known for x in d["evidence"])):
            return None
    return sum(d["score"] for d in dims.values())


def valid_issues(issues):
    return isinstance(issues,list) and all(isinstance(i,dict) and set(i)=={"severity","route","detail"}
        and i["severity"] in ("critical","high","medium","low")
        and i["route"] in STAGES[:-1] and nonblank(i["detail"]) for i in issues)


def run(input_commit,policy,dispatch):
    """Run synchronous trusted dispatch callbacks. Accepted means contract only,
    never release authorization. Real agent identity, execution, timeout and
    immutable external storage must be enforced by the integration adapter.
    """
    if not isinstance(input_commit,str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}",input_commit):
        raise ValueError("invalid input commit")
    p=copy.deepcopy(policy)
    validate_policy(p)
    policy_hash=digest(p)
    history=[];agents=set();contexts=set();active={}
    stage_index=0;repairs=0;feedback=[];score=None
    candidate=None;benchmark_hash=None

    def result(status,reason):
        return {"status":status,"reason":reason,"input_commit":input_commit,
                "policy_hash":policy_hash,"repairs":repairs,"history":history,
                "score":score,"release_authorized":False}

    while stage_index<len(STAGES):
        stage=STAGES[stage_index]
        prior=active.get(STAGES[stage_index-1]) if stage_index else None
        req={"stage":stage,"input_commit":input_commit,"policy":copy.deepcopy(p),
             "policy_hash":policy_hash,"attempt":len(history)+1,
             "prior_hash":prior["artifact_hash"] if prior else None,
             "prior_artifact_hex":prior["artifact_hex"] if prior else None,
             "candidate_hash":candidate,"benchmark_hash":benchmark_hash,
             "repair_feedback":copy.deepcopy(feedback)}
        req["request_hash"]=digest(req)
        expected=copy.deepcopy(req)
        try:
            res=dispatch(req)
        except Exception:
            return result("blocked","dispatch_failed")
        if req!=expected or not isinstance(res,dict):
            return result("blocked","invalid_handoff")
        agent,context=res.get("agent_id"),res.get("context_id")
        blob=res.get("artifact")
        if (not nonblank(agent) or not nonblank(context)
                or res.get("request_hash")!=expected["request_hash"]
                or not isinstance(blob,bytes) or not 0<len(blob)<=MAX_ARTIFACT
                or res.get("artifact_hash")!=hash_bytes(blob)
                or res.get("decision") not in ("pass","repair","blocked")
                or not valid_issues(res.get("issues"))):
            return result("blocked","invalid_handoff")
        if agent in agents or context in contexts:
            return result("blocked","reused_identity")
        agents.add(agent);contexts.add(context)
        issues=copy.deepcopy(res["issues"])
        entry={"stage":stage,"agent_id":agent,"context_id":context,
               "request_hash":expected["request_hash"],"artifact_hash":hash_bytes(blob),
               "artifact_hex":blob.hex(),"decision":res["decision"],"issues":issues}
        history.append(entry)
        if res["decision"]=="blocked":
            return result("blocked","stage_blocked")
        if res["decision"]=="repair":
            if not issues:
                return result("blocked","missing_repair_evidence")
            target=min(STAGES.index(i["route"]) for i in issues)
            if target>stage_index:
                return result("blocked","invalid_repair_route")
            if repairs>=p["max_repairs"]:
                return result("blocked","repair_budget_exhausted")
            repairs+=1
            feedback=issues
            for old in STAGES[target:]:
                active.pop(old,None)
            if target<=STAGES.index("Write"):
                candidate=None
            if target<=STAGES.index("Benchmark"):
                benchmark_hash=None
            score=None
            stage_index=target
            continue
        if any(i["severity"] in ("high","critical") for i in issues):
            return result("blocked","unresolved_high_issue")
        if stage=="Write":
            candidate=entry["artifact_hash"]
        if stage=="Benchmark":
            b=res.get("benchmark")
            valid=validate_benchmark(b,p,candidate)
            if valid is None:
                return result("blocked","invalid_benchmark")
            entry["benchmark"]=copy.deepcopy(b)
            benchmark_hash=digest(entry)
            if not valid:
                return result("blocked","benchmark_failed")
        if stage=="QA":
            known={x["artifact_hash"] for x in active.values()}|{benchmark_hash}
            e=res.get("evaluation")
            score=validate_evaluation(e,candidate,benchmark_hash,known)
            if score is None:
                return result("blocked","invalid_evaluation")
            entry["evaluation"]=copy.deepcopy(e)
            if score<p["min_score"]:
                return result("blocked","score_below_threshold")
        active[stage]=entry
        feedback=[]
        stage_index+=1
    return result("accepted","contract_passed")
