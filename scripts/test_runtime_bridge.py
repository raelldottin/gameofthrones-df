"""Real SQLite restart/replay tests; synthetic verifier receipts, no live agents."""
import copy
import pytest
from scripts.dragon_analyzer.runtime_bridge import (
    Bridge, PendingReceipt, ReceiptError, project_slice, sign_receipt,
)
from scripts.dragon_analyzer.reconcile import digest
from scripts.dragon_analyzer.supervisor import hash_bytes, run, STAGES, DIMENSIONS

KEY=b"x"*32
PIN="b193297829c68d2243e5e32d1517cf0b51568813"
POLICY={"fixture_hash":"a"*64,"baseline_hash":"b"*64,
        "gates":["tests","mutations","holdout","architecture"],
        "metrics":{"accuracy":{"min":99,"baseline":99,"direction":"higher"}},
        "max_repairs":3,"min_score":95}

def request(attempt=1,run_id="run-1",stage="Research"):
    r={"run_id":run_id,"attempt":attempt,"stage":stage,"input_commit":"c"*40,
       "policy":POLICY,"policy_hash":digest(POLICY),"active_artifacts":{},
       "prior_hash":None,"prior_artifact_hex":None,"candidate_hash":None,
       "benchmark_hash":None,"repair_feedback":[]}
    return {**r,"request_hash":digest(r)}

def receipt(req,n=1):
    blob=("artifact-"+str(n)).encode()
    r={"request_hash":req["request_hash"],"agent_id":"agent-"+str(n),
       "context_id":"context-"+str(n),"artifact_hex":blob.hex(),
       "artifact_hash":hash_bytes(blob),"decision":"pass","issues":[],
       "boundroom_pin":PIN,"runtime_report_hash":"d"*64,
       "verified_commit":req["input_commit"],"isolation_attested":True}
    if req["stage"]=="Benchmark":
        r["benchmark"]={"fixture_hash":POLICY["fixture_hash"],"baseline_hash":POLICY["baseline_hash"],
                        "candidate_hash":req["candidate_hash"],"gates":dict.fromkeys(POLICY["gates"],True),
                        "metrics":{"accuracy":99.5}}
    if req["stage"]=="QA":
        r["evaluation"]={"candidate_hash":req["candidate_hash"],"benchmark_hash":req["benchmark_hash"],
                         "dimensions":{k:{"score":v,"evidence":[req["benchmark_hash"]]} for k,v in DIMENSIONS.items()}}
    return r

def test_pending_is_durable_and_never_fakes_success(tmp_path):
    path=tmp_path/"bridge.sqlite"
    req=request()
    for _ in range(3):
        with Bridge(path,KEY) as b:
            with pytest.raises(PendingReceipt):
                b(req)
            assert b.pending()==[req]

def test_signed_receipt_replays_after_restart(tmp_path):
    path=tmp_path/"bridge.sqlite"
    req=request()
    r=receipt(req)
    with Bridge(path,KEY) as b:
        with pytest.raises(PendingReceipt): b(req)
        b.submit(r,sign_receipt(r,KEY))
    with Bridge(path,KEY) as b:
        out=b(req)
        assert out["artifact"]==b"artifact-1"
        assert b.pending()==[]
        b.submit(r,sign_receipt(r,KEY))
        assert b(req)==out

@pytest.mark.parametrize("change",["signature","request_hash","artifact_hash","boundroom_pin","isolation_attested","verified_commit"])
def test_invalid_receipt_cannot_be_admitted(tmp_path,change):
    req=request()
    r=receipt(req)
    with Bridge(tmp_path/"db",KEY) as b:
        with pytest.raises(PendingReceipt): b(req)
        if change!="signature":
            r[change]=False if change=="isolation_attested" else "0"*64
        sig="0"*64 if change=="signature" else sign_receipt(r,KEY)
        with pytest.raises(ReceiptError): b.submit(r,sig)
        assert b.pending()==[req]

def test_duplicate_attempt_with_changed_request_rejected(tmp_path):
    with Bridge(tmp_path/"db",KEY) as b:
        with pytest.raises(PendingReceipt): b(request())
        with pytest.raises(ReceiptError): b(request(stage="Plan"))

def test_worker_identity_cannot_be_reused(tmp_path):
    with Bridge(tmp_path/"db",KEY) as b:
        for req in (request(),request(2)):
            with pytest.raises(PendingReceipt): b(req)
        a=receipt(request());b.submit(a,sign_receipt(a,KEY))
        c=receipt(request(2))
        with pytest.raises(ReceiptError): b.submit(c,sign_receipt(c,KEY))

def test_receipt_cannot_be_replaced(tmp_path):
    req=request()
    with Bridge(tmp_path/"db",KEY) as b:
        with pytest.raises(PendingReceipt): b(req)
        a=receipt(req);b.submit(a,sign_receipt(a,KEY))
        c=receipt(req,2)
        with pytest.raises(ReceiptError): b.submit(c,sign_receipt(c,KEY))
        assert b(req)["agent_id"]=="agent-1"

def test_request_tampering_rejected(tmp_path):
    r=request();r["stage"]="Write"
    with Bridge(tmp_path/"db",KEY) as b:
        with pytest.raises(ReceiptError): b(r)

def test_supervisor_resume_with_one_new_stage_per_external_receipt(tmp_path):
    path=tmp_path/"db"
    for i,stage in enumerate(STAGES,1):
        with Bridge(path,KEY) as b:
            out=run("c"*40,POLICY,b,run_id="real-shape-fixture")
            assert out["status"]=="blocked"
            req,=b.pending()
            assert req["stage"]==stage
            r=receipt(req,i);b.submit(r,sign_receipt(r,KEY))
    with Bridge(path,KEY) as b:
        out=run("c"*40,POLICY,b,run_id="real-shape-fixture")
        assert out["status"]=="accepted"
        assert len(out["history"])==6
        assert out["release_authorized"] is False

def test_projection_one_bounded_slice_and_no_implicit_launcher():
    req=request()
    q=project_slice(req,allowed_paths=["docs/"],validations=["git diff --check"],
                    max_files=2,timeout=60)
    assert q["version"]==1 and len(q["slices"])==1
    s=q["slices"][0]
    assert s["slice_id"]=="df-"+req["request_hash"][:32]
    assert s["allowed_paths"]==["docs/"]
    assert req["request_hash"] in s["notes"]
    assert q["policy"]["agent_command_template"]==""
    assert q["policy"]["consecutive_autonomous_limit"]==1

@pytest.mark.parametrize("paths",[["../"],["/tmp"],["."],["automation/"],[".github/"],["player-state/"]])
def test_projection_rejects_unsafe_scope(paths):
    with pytest.raises(ValueError):
        project_slice(request(),allowed_paths=paths,validations=["git diff --check"],max_files=2,timeout=60)
