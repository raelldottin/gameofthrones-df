"""Durable receipt inbox for an external Boundroom operator; no agent launcher."""
import hashlib
import hmac
import json
import re
from pathlib import Path, PurePosixPath
import sqlite3

from .reconcile import digest
from .supervisor import STAGES, MAX_ARTIFACT, hash_bytes, hex64, nonblank, valid_issues, validate_policy

BOUNDROOM_PIN = "b193297829c68d2243e5e32d1517cf0b51568813"
HERMES_SWARM_PIN = "db79381997e68a0cc679a3b3f23affdd09b33720"
MAX_RECEIPT = 5_000_000
BASE_FIELDS = {"request_hash","agent_id","context_id","artifact_hex","artifact_hash",
               "decision","issues","boundroom_pin","runtime_report_hash",
               "verified_commit","isolation_attested"}


class ReceiptError(ValueError):
    pass


class PendingReceipt(RuntimeError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",",":"),
                      ensure_ascii=False, allow_nan=False)


def sign_receipt(receipt, key):
    """Operator-verifier MAC, never a worker credential or independent proof by itself."""
    if not isinstance(key,bytes) or len(key)<32:
        raise ValueError("verifier key must contain at least 32 bytes")
    payload=canonical(receipt).encode()
    if len(payload)>MAX_RECEIPT:
        raise ReceiptError("oversized receipt")
    return hmac.new(key,b"dragonfire-runtime-v1\0"+payload,hashlib.sha256).hexdigest()


def check_request(req):
    expected={"run_id","attempt","stage","input_commit","policy","policy_hash",
              "active_artifacts","prior_hash","prior_artifact_hex","candidate_hash",
              "benchmark_hash","repair_feedback","request_hash"}
    if not isinstance(req,dict) or set(req)!=expected:
        raise ReceiptError("invalid request fields")
    key=req.get("request_hash")
    if (not hex64(key) or digest({k:v for k,v in req.items() if k!="request_hash"})!=key
            or not nonblank(req.get("run_id")) or len(req["run_id"])>128
            or type(req.get("attempt")) is not int or req["attempt"]<1
            or req.get("stage") not in STAGES):
        raise ReceiptError("invalid request binding")
    if (not isinstance(req["input_commit"],str) or not re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}",req["input_commit"])):
        raise ReceiptError("invalid input commit")
    try:
        validate_policy(req["policy"])
    except ValueError as exc:
        raise ReceiptError("invalid policy") from exc
    if req["policy_hash"]!=digest(req["policy"]):
        raise ReceiptError("request policy hash mismatch")
    return key


def validate_receipt(r,req):
    fields=BASE_FIELDS|({"benchmark"} if req["stage"]=="Benchmark" and r.get("decision")=="pass"
                        else {"evaluation"} if req["stage"]=="QA" and r.get("decision")=="pass" else set())
    if (set(r)!=fields or r["request_hash"]!=req["request_hash"]
            or r["boundroom_pin"]!=BOUNDROOM_PIN or r["isolation_attested"] is not True
            or r["verified_commit"]!=req["input_commit"]
            or not hex64(r["runtime_report_hash"]) or not hex64(r["artifact_hash"])
            or not nonblank(r["agent_id"]) or not nonblank(r["context_id"])
            or r["decision"] not in ("pass","repair","blocked") or not valid_issues(r["issues"])
            or not isinstance(r["artifact_hex"],str) or len(r["artifact_hex"])>MAX_ARTIFACT*2):
        raise ReceiptError("receipt binding or evidence invalid")
    try:
        artifact=bytes.fromhex(r["artifact_hex"])
    except ValueError as exc:
        raise ReceiptError("invalid artifact encoding") from exc
    if not artifact or hash_bytes(artifact)!=r["artifact_hash"]:
        raise ReceiptError("artifact hash mismatch")
    out={k:r[k] for k in ("request_hash","agent_id","context_id","artifact_hash","decision","issues")}
    out["artifact"]=artifact
    for name in ("benchmark","evaluation"):
        if name in r:
            out[name]=r[name]
    return out


class Bridge:
    """Local durable receipt journal, not canonical work state or execution authority.

    Keep database and verifier key outside the consumer checkout and worker sandbox.
    Restart replay never launches a worker. Pending work requires operator reconciliation.
    """
    def __init__(self,path,key):
        sign_receipt({},key)
        self.key=key
        self.db=sqlite3.connect(Path(path),timeout=10,isolation_level=None)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS requests(
            hash TEXT PRIMARY KEY, run_id TEXT NOT NULL, attempt INTEGER NOT NULL,
            payload TEXT NOT NULL, UNIQUE(run_id,attempt));
          CREATE TABLE IF NOT EXISTS receipts(
            hash TEXT PRIMARY KEY REFERENCES requests(hash),
            agent TEXT NOT NULL UNIQUE, context TEXT NOT NULL UNIQUE,
            payload TEXT NOT NULL, signature TEXT NOT NULL);
        """)

    def __enter__(self):
        return self

    def __exit__(self,*args):
        self.db.close()

    def __call__(self,req):
        key=check_request(req)
        body=canonical(req)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing=self.db.execute("SELECT hash,payload FROM requests WHERE run_id=? AND attempt=?",
                                     (req["run_id"],req["attempt"])).fetchone()
            if existing is not None and existing!=(key,body):
                raise ReceiptError("attempt already bound to another request")
            if existing is None:
                self.db.execute("INSERT INTO requests VALUES(?,?,?,?)",
                                (key,req["run_id"],req["attempt"],body))
            stored=self.db.execute("SELECT payload,signature FROM receipts WHERE hash=?",(key,)).fetchone()
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise
        if stored is None:
            raise PendingReceipt(key)
        r=json.loads(stored[0])
        if not hmac.compare_digest(sign_receipt(r,self.key),stored[1]):
            raise ReceiptError("stored signature invalid")
        return validate_receipt(r,req)

    def pending(self):
        rows=self.db.execute("SELECT q.payload FROM requests q LEFT JOIN receipts r ON q.hash=r.hash "
                             "WHERE r.hash IS NULL ORDER BY q.run_id,q.attempt")
        return [json.loads(row[0]) for row in rows]

    def submit(self,r,signature):
        if not isinstance(r,dict) or not hex64(signature):
            raise ReceiptError("invalid receipt envelope")
        if not hmac.compare_digest(sign_receipt(r,self.key),signature):
            raise ReceiptError("invalid verifier signature")
        key=r.get("request_hash")
        if not hex64(key):
            raise ReceiptError("invalid receipt request hash")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row=self.db.execute("SELECT payload FROM requests WHERE hash=?",(key,)).fetchone()
            if row is None:
                raise ReceiptError("unknown request")
            validate_receipt(r,json.loads(row[0]))
            body=canonical(r)
            old=self.db.execute("SELECT payload,signature FROM receipts WHERE hash=?",(key,)).fetchone()
            if old is not None:
                if old!=(body,signature):
                    raise ReceiptError("receipt is immutable")
            else:
                self.db.execute("INSERT INTO receipts VALUES(?,?,?,?,?)",
                                (key,r["agent_id"],r["context_id"],body,signature))
            self.db.execute("COMMIT")
        except sqlite3.IntegrityError as exc:
            self.db.execute("ROLLBACK")
            raise ReceiptError("reused agent or context identity") from exc
        except Exception:
            self.db.execute("ROLLBACK")
            raise


def project_slice(req,*,allowed_paths,validations,max_files,timeout):
    """Produce one reviewable Boundroom v1 queue; do not write/launch it.

    Scope and validation commands are operator inputs, not generated from agent prose.
    Only project engineering paths are eligible in this draft.
    """
    key=check_request(req)
    roots={"scripts","quality","docs","analysis"}
    if not isinstance(allowed_paths,list) or not allowed_paths:
        raise ValueError("explicit scope required")
    for p in allowed_paths:
        if not isinstance(p,str) or not p or "\\" in p or p.startswith("/") or any(
                part in ("",".","..") for part in p.rstrip("/").split("/")):
            raise ValueError("unsafe scope")
        if PurePosixPath(p).parts[0] not in roots:
            raise ValueError("unsafe scope")
    if (not isinstance(validations,list) or not validations or not all(nonblank(v) for v in validations)
            or type(max_files) is not int or not 1<=max_files<=30
            or type(timeout) is not int or not 1<=timeout<=3600):
        raise ValueError("explicit bounded validation policy required")
    return {"version":1,"policy":{"consecutive_autonomous_limit":1,
            "handoff_timeout_seconds":timeout,"agent_command_template":"",
            "supervisor_owned_paths":["automation/queue/slices.json","automation/handoffs/"]},
            "slices":[{"slice_id":"df-"+key[:32],"title":"Dragonfire "+req["stage"],
                       "status":"queued","priority":10,"domain":"dragonfire",
                       "allowed_paths":list(allowed_paths),"required_validations":list(validations),
                       "depends_on":[],"max_files_changed":max_files,
                       "notes":"Operator-bound request SHA-256: "+key+
                               "; verify exact request and input commit before launch."}]}
