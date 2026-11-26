"""Fail-closed release assessment; never deploys or grants release authorization."""
import json
import re
from pathlib import Path

from .reconcile import digest
from .supervisor import DIMENSIONS

GATES=("clean_install","behavioral_tests","source_mutations","roster_regression",
       "image_holdout","habit_recognition","authoritative_ledger","tactical_validation",
       "prospective_battle_validation","authenticated_dispatch","durable_artifacts",
       "performance_nonregression","rollback_drill","independent_review",
       "no_high_critical_findings","independent_qa")
POLICY_HASH=digest({"version":"q8-v1","gates":GATES,"dimensions":DIMENSIONS,"min_score":95})
RECEIPT_FIELDS={"gate","tree","policy","status","issuer","artifact"}


def nonblank(x):
    return isinstance(x,str) and bool(x.strip()) and x==x.strip()


def hex64(x):
    return isinstance(x,str) and bool(re.fullmatch("[a-f0-9]{64}",x))


def assess(tree,receipts,qa,trusted_digests):
    """Trusted digests MUST be obtained independently by an authenticated verifier.
    Hashing submitted receipts does not authenticate them. No trust store is shipped.
    """
    if not isinstance(tree,str) or not re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}",tree):
        raise ValueError("invalid candidate tree")
    if not isinstance(receipts,list):
        raise ValueError("receipts must be a list")
    valid={};issues=[];seen=set()
    for r in receipts:
        if not isinstance(r,dict) or set(r)!=RECEIPT_FIELDS or not isinstance(r["gate"],str) or r["gate"] not in GATES:
            issues.append("malformed receipt")
            continue
        gate=r["gate"]
        if gate in seen:
            issues.append("duplicate receipt:"+gate)
            valid.pop(gate,None)
            continue
        seen.add(gate)
        if (r["tree"]!=tree or r["policy"]!=POLICY_HASH or r["status"]!="pass"
                or not nonblank(r["issuer"]) or not hex64(r["artifact"])):
            issues.append("invalid or failed receipt:"+gate)
            continue
        if digest(r) not in trusted_digests:
            issues.append("untrusted receipt:"+gate)
            continue
        valid[gate]=r
    missing=[g for g in GATES if g not in valid]
    score=None
    if not missing and not issues:
        review=valid["independent_review"]["issuer"]
        evaluator=valid["independent_qa"]["issuer"]
        implementers={r["issuer"] for g,r in valid.items() if g not in ("independent_review","independent_qa")}
        if review==evaluator or review in implementers or evaluator in implementers:
            issues.append("independence not established")
        elif not isinstance(qa,dict) or set(qa)!={"tree","policy","issuer","scores","evidence"}:
            issues.append("missing or malformed evaluation")
        elif qa["tree"]!=tree or qa["policy"]!=POLICY_HASH or qa["issuer"]!=evaluator or digest(qa) not in trusted_digests:
            issues.append("untrusted or stale evaluation")
        else:
            scores=qa["scores"]; evidence=qa["evidence"]
            known={digest(r) for g,r in valid.items() if g!="independent_qa"}
            if (not isinstance(scores,dict) or set(scores)!=set(DIMENSIONS)
                    or not isinstance(evidence,dict) or set(evidence)!=set(DIMENSIONS)
                    or any(type(scores[k]) is not int or not 0<=scores[k]<=DIMENSIONS[k] for k in DIMENSIONS)
                    or any(not isinstance(evidence[k],list) or not evidence[k]
                           or not all(isinstance(x,str) and x in known for x in evidence[k]) for k in DIMENSIONS)):
                issues.append("invalid scores or evidence")
            else:
                score=sum(scores.values())
                if score<95:
                    issues.append("score below threshold")
    return {"status":"blocked" if missing or issues else "eligible_for_human_review",
            "tree":tree,"policy_hash":POLICY_HASH,"missing_gates":missing,
            "issues":issues,"score":score,"release_authorized":False}


def inventory(root):
    """Report historical observations, NOT authenticated release receipts."""
    root=Path(root)
    def read(name):
        return json.loads((root/"quality/results"/name).read_text())
    image=read("visual-dev-2026-11-26.json")
    formation=read("formation-dev-2026-11-26.json")
    battle=read("battle-dev-2026-11-26.json")
    return {"status":"blocked","release_authorized":False,"score":None,
            "policy_hash":POLICY_HASH,"required_gates":list(GATES),
            "authenticated_receipts":0,
            "development":{"image_correct":image["correct"],"image_total":image["total"],
                           "image_partition":image["partition"],"image_wrong":image["wrong"],
                           "permanent_baseline":formation["baseline"]["score"],
                           "permanent_optimum":formation["permanent"]["score"],
                           "battle_calibration_cases":battle["calibration"]["evaluated"]},
            "blockers":["independent image holdout and habits","authoritative ledger and corrections",
                        "ability-aware tactical validation","prospective combat calibration",
                        "authenticated fresh-agent runtime and durable artifacts",
                        "measured non-regression budgets and deployment rollback drill",
                        "independent architecture review and QA"],
            "note":"Historical development data are not release receipts. No promotion or deployment."}


if __name__=="__main__":
    print(json.dumps(inventory(Path(__file__).resolve().parents[2]),indent=2))
