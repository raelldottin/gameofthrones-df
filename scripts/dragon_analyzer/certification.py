"""Certification evidence inventory. Structural validation is not authentication."""
import argparse
import hashlib
import json
import math
import re
import statistics
import subprocess
from pathlib import Path
from .release import assess, GATES, POLICY_HASH
from quality.mutation_catalog import SUITES
from quality.mutation_runner import mutate_text, git_info

VERSIONS=("3.11","3.12")
PROTECTED_BASE="381883cfeafa4ca9ab5be234e5a8310f66306f11"
PROTECTED_PATHS=("player-state","armies")
ROOT=Path(__file__).resolve().parents[2]


def hex64(value):
    return isinstance(value,str) and bool(re.fullmatch(r"[a-f0-9]{64}",value))


def catalog_hash():
    return hashlib.sha256(json.dumps(SUITES,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def inspect_mutations(root,tree,report,version):
    """Require exact catalog census, source hashes, test identities and matrix version.
    The report is still caller-supplied and not an authenticated receipt.
    """
    if not isinstance(report,dict):
        return ["invalid_report"]
    issues=[]
    def flag(reason):
        if reason not in issues:issues.append(reason)
    candidate=report.get("candidate")
    if not isinstance(candidate,dict) or candidate.get("tree")!=tree:
        flag("candidate_tree_mismatch")
    if not isinstance(candidate,dict) or candidate.get("tracked_clean") is not True:
        flag("candidate_not_clean")
    if report.get("source_snapshot")!="git_tree":
        flag("source_snapshot_mismatch")
    if report.get("catalog_sha256")!=catalog_hash():
        flag("catalog_mismatch")
    if not isinstance(report.get("python"),str) or not re.fullmatch(re.escape(version)+r"\.\d+",report["python"]):
        flag("python_mismatch")
    n=sum(len(cases) for _,cases in SUITES.values())
    if (report.get("schema_version")!=1 or report.get("kind")!="targeted_source_mutation_development"
            or report.get("planned")!=n or report.get("counts")!={"killed":n}
            or report.get("passed") is not True or report.get("release_authorized") is not False):
        flag("invalid_summary")
    suites=report.get("suites")
    if not isinstance(suites,list) or any(not isinstance(s,dict) or not isinstance(s.get("suite"),str) for s in suites):
        return issues+["invalid_suites"]
    by={s["suite"]:s for s in suites}
    if len(by)!=len(suites) or set(by)!=set(SUITES):
        flag("suite_census")
    for name,(target,cases) in SUITES.items():
        s=by.get(name,{})
        baseline=s.get("baseline")
        if (s.get("target")!=target or s.get("passed") is not True
                or not isinstance(baseline,dict) or baseline.get("status")!="pass"
                or baseline.get("exit_code")!=0 or baseline.get("error") is not None
                or type(baseline.get("tests")) is not int or baseline["tests"]<=0):
            flag("baseline:"+name)
        if s.get("counts")!={"killed":len(cases)}:
            flag("suite_counts:"+name)
        rows=s.get("cases")
        if not isinstance(rows,list) or any(not isinstance(r,dict) or not isinstance(r.get("label"),str) for r in rows):
            flag("case_census:"+name);continue
        indexed={r["label"]:r for r in rows}
        if len(indexed)!=len(rows) or set(indexed)!={c[0] for c in cases}:
            flag("case_census:"+name)
        for label,filename,old,new,test in cases:
            r=indexed.get(label)
            if r is None:continue
            failed=r.get("failed_tests")
            expected=r.get("expected_tests")
            # JUnit class names are generated from the selected file; require exact
            # class/test prefix, including a parameter suffix where applicable.
            prefix=target.replace("/",".").removesuffix(".py")+"::"+test
            if (r.get("file")!=filename or r.get("test")!=test or r.get("status")!="killed"
                    or r.get("exit_code")!=1 or r.get("error") is not None
                    or type(expected) is not int or expected<1 or r.get("observed_tests")!=expected
                    or not isinstance(failed,list) or not 1<=len(failed)<=expected
                    or any(not isinstance(x,str) or not (x==prefix or x.startswith(prefix+"[")) for x in failed)
                    or len(set(failed))!=len(failed)):
                flag("invalid_kill:"+name)
            src=(Path(root)/"scripts/dragon_analyzer"/filename).read_text(encoding="utf-8")
            changed=mutate_text(src,old,new)
            if (r.get("source_before")!=hashlib.sha256(src.encode()).hexdigest()
                    or r.get("source_after")!=hashlib.sha256(changed.encode()).hexdigest()):
                flag("source_mismatch:"+name)
    return issues


def certify(root,tree,reports,*,protected_unchanged):
    issues=[]
    by={}
    for report in reports:
        version=report.get("python","") if isinstance(report,dict) else ""
        version=".".join(version.split(".")[:2]) if isinstance(version,str) else ""
        if version not in VERSIONS or version in by:
            issues.append("unexpected_or_duplicate_version");continue
        by[version]=inspect_mutations(root,tree,report,version)
    for version in VERSIONS:
        if version not in by:issues.append("missing_python:"+version)
        else:issues.extend(version+":"+x for x in by[version])
    if protected_unchanged is not True:issues.append("protected_data_changed")
    # No self-issued receipts. The real Q8 assessment is intentionally empty.
    result=assess(tree,[],None,set())
    return {**result,"automated_matrix_complete":not issues,
            "matrix_versions":sorted(by),"mutation_catalog_count":sum(len(c) for _,c in SUITES.values()),
            "issues":issues,"protected_unchanged":protected_unchanged,
            "evidence_kind":"structural_development_only",
            "trusted_receipts":0}


def finite_positive(x):
    return type(x) in (int,float) and math.isfinite(x) and x>0


def compare_performance(baseline,candidate,budgets):
    """Compare externally frozen, like-for-like timing inputs, never a release receipt."""
    def blocked(reason):
        return {"status":"blocked","reason":reason,"release_authorized":False}
    for value in (baseline,candidate):
        if (not isinstance(value,dict) or set(value)!={"environment","input","workloads"}
                or not hex64(value["environment"]) or not hex64(value["input"])
                or not isinstance(value["workloads"],dict) or not value["workloads"]):
            return blocked("invalid_manifest")
    if baseline["environment"]!=candidate["environment"] or baseline["input"]!=candidate["input"]:
        return blocked("incomparable_inputs")
    names=set(baseline["workloads"])
    if not isinstance(budgets,dict) or set(budgets)!=names or set(candidate["workloads"])!=names:
        return blocked("workload_census")
    metrics={}
    for name in sorted(names):
        a,b=baseline["workloads"][name],candidate["workloads"][name]
        p=budgets[name]
        for row in (a,b):
            if (not isinstance(row,dict) or set(row)!={"samples_ms","output_digest"}
                    or not hex64(row["output_digest"]) or not isinstance(row["samples_ms"],list)
                    or len(row["samples_ms"])!=5 or not all(finite_positive(x) for x in row["samples_ms"])):
                return blocked("invalid_samples")
        if a["output_digest"]!=b["output_digest"]:return blocked("changed_output")
        if (not isinstance(p,dict) or set(p)!={"max_median_ms","max_regression_ratio"}
                or not all(finite_positive(x) for x in p.values())):
            return blocked("invalid_budget")
        old=statistics.median(a["samples_ms"]);new=statistics.median(b["samples_ms"])
        if new>p["max_median_ms"] or new/old>p["max_regression_ratio"]:
            return blocked("performance_regression")
        metrics[name]={"baseline_median_ms":old,"candidate_median_ms":new,"ratio":new/old}
    return {"status":"development_pass","metrics":metrics,"release_authorized":False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reports",type=Path,nargs="+",required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    candidate=git_info(ROOT)
    unchanged=(candidate["tracked_clean"] and subprocess.run(
        ["git","diff","--quiet",PROTECTED_BASE,"HEAD","--",*PROTECTED_PATHS],cwd=ROOT).returncode==0)
    reports=[json.loads(path.read_text()) for path in args.reports]
    out=certify(ROOT,candidate["tree"],reports,protected_unchanged=unchanged)
    out.update(candidate=candidate,protected_base=PROTECTED_BASE)
    payload=json.dumps(out,indent=2,sort_keys=True)+"\n"
    with args.output.open("x",encoding="utf-8") as f:f.write(payload)
    print(payload)
    # CI checks structural evidence, not production approval.
    return 0 if out["automated_matrix_complete"] else 1


if __name__=="__main__":
    raise SystemExit(main())
