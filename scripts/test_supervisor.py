"""Supervisor contracts: simulated dispatch only, never real agent evidence."""
import pytest
from scripts.dragon_analyzer.supervisor import run, STAGES, DIMENSIONS, hash_bytes

GATES=("tests","mutations","holdout","architecture")
POLICY={"fixture_hash":"a"*64,"baseline_hash":"b"*64,"gates":list(GATES),
        "metrics":{"accuracy":{"min":99,"baseline":99,"direction":"higher"},
                   "latency":{"max":10,"baseline":9,"direction":"lower"}},
        "max_repairs":3,"min_score":95}
INPUT="c"*40

class Fake:
    def __init__(self, alter=lambda req,res:None):
        self.requests=[]
        self.alter=alter
    def __call__(self, req):
        self.requests.append(req)
        n=len(self.requests)
        stage=req["stage"]
        blob=f"{stage}:{n}".encode()
        res={"agent_id":f"agent-{n}","context_id":f"context-{n}",
             "request_hash":req["request_hash"],"artifact":blob,
             "artifact_hash":hash_bytes(blob),"decision":"pass","issues":[]}
        if stage=="Benchmark":
            res["benchmark"]={"fixture_hash":req["policy"]["fixture_hash"],
                              "baseline_hash":req["policy"]["baseline_hash"],
                              "candidate_hash":req["candidate_hash"],
                              "gates":dict.fromkeys(GATES,True),
                              "metrics":{"accuracy":99.5,"latency":8}}
        if stage=="QA":
            res["evaluation"]={"benchmark_hash":req["benchmark_hash"],
                               "candidate_hash":req["candidate_hash"],
                               "dimensions":{k:{"score":v,"evidence":[req["benchmark_hash"]]} for k,v in DIMENSIONS.items()}}
        self.alter(req,res)
        return res

def go(fake, policy=POLICY):
    return run(INPUT,policy,fake,run_id="fixture-run")

def test_happy_path_and_immutable_chain():
    f=Fake()
    r=go(f)
    assert r["status"]=="accepted"
    assert [q["stage"] for q in f.requests]==list(STAGES)
    assert r["score"]==100
    assert len(set(x["agent_id"] for x in r["history"]))==6
    assert f.requests[1]["prior_hash"]==r["history"][0]["artifact_hash"]

def test_reused_agent_blocked():
    f=Fake(lambda q,r:r.update(agent_id="agent-1"))
    assert go(f)["reason"]=="reused_identity"

def test_reused_context_blocked():
    f=Fake(lambda q,r:r.update(context_id="context-1"))
    assert go(f)["reason"]=="reused_identity"

def test_wrong_request_blocked():
    f=Fake(lambda q,r:r.update(request_hash="0"*64))
    assert go(f)["reason"]=="invalid_handoff"

def test_corrupt_artifact_blocked():
    f=Fake(lambda q,r:r.update(artifact=b"corrupt"))
    assert go(f)["reason"]=="invalid_handoff"

def test_benchmark_stale_candidate_blocked():
    def alter(q,r):
        if q["stage"]=="Benchmark":r["benchmark"]["candidate_hash"]="0"*64
    assert go(Fake(alter))["reason"]=="invalid_benchmark"

def test_missing_gate_not_pass():
    def alter(q,r):
        if q["stage"]=="Benchmark":r["benchmark"]["gates"].pop("holdout")
    assert go(Fake(alter))["reason"]=="invalid_benchmark"

def test_failed_gate_never_accepted():
    def alter(q,r):
        if q["stage"]=="Benchmark":r["benchmark"]["gates"]["holdout"]=False
    assert go(Fake(alter))["status"]=="blocked"

def test_metric_regression_blocks_even_if_above_threshold():
    def alter(q,r):
        if q["stage"]=="Benchmark":r["benchmark"]["metrics"]["latency"]=9.5
    assert go(Fake(alter))["status"]=="blocked"

def test_fake_numeric_gate_rejected():
    def alter(q,r):
        if q["stage"]=="Benchmark":r["benchmark"]["gates"]["holdout"]=1
    assert go(Fake(alter))["reason"]=="invalid_benchmark"

def test_stale_qa_rejected():
    def alter(q,r):
        if q["stage"]=="QA":r["evaluation"]["benchmark_hash"]="0"*64
    assert go(Fake(alter))["reason"]=="invalid_evaluation"

def test_missing_dimension_evidence_rejected():
    def alter(q,r):
        if q["stage"]=="QA":r["evaluation"]["dimensions"]["architecture"]["evidence"]=[]
    assert go(Fake(alter))["reason"]=="invalid_evaluation"

def test_score_over_cap_rejected():
    def alter(q,r):
        if q["stage"]=="QA":r["evaluation"]["dimensions"]["architecture"]["score"]=21
    assert go(Fake(alter))["reason"]=="invalid_evaluation"

def test_low_score_blocks():
    def alter(q,r):
        if q["stage"]=="QA":r["evaluation"]["dimensions"]["architecture"]["score"]=10
    assert go(Fake(alter))["status"]=="blocked"

def test_unresolved_high_blocks():
    def alter(q,r):
        if q["stage"]=="Review":r["issues"]=[{"severity":"high","route":"Plan","detail":"bad design"}]
    assert go(Fake(alter))["status"]=="blocked"

def test_repair_replays_downstream_with_fresh_identities():
    once=[]
    def alter(q,r):
        if q["stage"]=="Review" and not once:
            once.append(1)
            r.update(decision="repair",issues=[{"severity":"high","route":"Write","detail":"bug"}])
    f=Fake(alter)
    r=go(f)
    assert r["status"]=="accepted"
    assert [q["stage"] for q in f.requests]==["Research","Plan","Write","Review","Write","Review","Benchmark","QA"]
    assert r["repairs"]==1
    assert f.requests[4]["repair_feedback"][0]["detail"]=="bug"

def test_exhaustion_is_bounded():
    def alter(q,r):
        if q["stage"]=="Review":r.update(decision="repair",issues=[{"severity":"high","route":"Write","detail":"bug"}])
    f=Fake(alter)
    r=go(f)
    assert r["reason"]=="repair_budget_exhausted"
    assert r["repairs"]==3
    assert len(f.requests)==10

def test_adapter_error_blocks():
    def fail(q):raise TimeoutError("provider")
    assert go(fail)["reason"]=="dispatch_failed"

def test_policy_cannot_be_mutated_by_adapter():
    def alter(q,r):q["policy"]["min_score"]=0
    assert go(Fake(alter))["reason"]=="invalid_handoff"

def test_invalid_policy():
    with pytest.raises(ValueError):
        go(Fake(),{**POLICY,"min_score":0})


def test_all_active_artifacts_available_to_benchmark():
    f=Fake()
    assert go(f)["status"]=="accepted"
    request=f.requests[4]
    assert set(request["active_artifacts"])=={"Research","Plan","Write","Review"}
    write=request["active_artifacts"]["Write"]
    assert hash_bytes(bytes.fromhex(write["artifact_hex"]))==request["candidate_hash"]


@pytest.mark.parametrize("route",["Research","Plan","Write","Review","Benchmark"])
def test_qa_routes_replay_all_downstream_stages(route):
    once=[]
    def alter(q,r):
        if q["stage"]=="QA" and not once:
            once.append(1)
            r.update(decision="repair",issues=[{"severity":"high","route":route,"detail":"repair requested"}])
    f=Fake(alter)
    result=go(f)
    assert result["status"]=="accepted"
    assert [x["stage"] for x in f.requests]==list(STAGES)+list(STAGES[STAGES.index(route):])
    retry=f.requests[6]
    assert set(retry["active_artifacts"])==set(STAGES[:STAGES.index(route)])
    assert retry["benchmark_hash"] is None
    assert len({x["agent_id"] for x in result["history"]})==len(result["history"])


def test_run_id_binds_request_and_rejects_prior_run_receipt():
    f=Fake()
    old=run(INPUT,POLICY,f,run_id="run-old")
    assert old["status"]=="accepted"
    assert f.requests[0]["run_id"]=="run-old"
    fresh=Fake()
    assert run(INPUT,POLICY,fresh,run_id="run-new")["status"]=="accepted"
    assert fresh.requests[0]["run_id"]=="run-new"
    assert f.requests[0]["request_hash"]!=fresh.requests[0]["request_hash"]
    old_response=Fake()(f.requests[0])
    def stale(req):return old_response
    assert run(INPUT,POLICY,stale,run_id="run-new")["reason"]=="invalid_handoff"


def test_no_release_authorization_even_with_perfect_synthetic_score():
    assert go(Fake())["release_authorized"] is False


def test_unknown_evidence_reference_rejected():
    def alter(q,r):
        if q["stage"]=="QA":r["evaluation"]["dimensions"]["architecture"]["evidence"]=["f"*64]
    assert go(Fake(alter))["reason"]=="invalid_evaluation"


def test_forward_repair_route_rejected():
    f=Fake(lambda q,r:r.update(decision="repair",issues=[{"severity":"high","route":"Write","detail":"future stage"}]))
    assert go(f)["reason"]=="invalid_repair_route"


def test_repair_without_evidence_blocked():
    f=Fake(lambda q,r:r.update(decision="repair"))
    assert go(f)["reason"]=="missing_repair_evidence"


def test_missing_required_policy_gate_rejected():
    with pytest.raises(ValueError):
        go(Fake(),{**POLICY,"gates":["tests"]})
