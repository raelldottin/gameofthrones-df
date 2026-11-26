"""Certification checks evidence structure; fixtures never authorize release."""
import hashlib
import json
from pathlib import Path
import pytest
from quality.mutation_catalog import SUITES
from quality.mutation_runner import mutate_text
from scripts.dragon_analyzer.certification import certify, inspect_mutations, compare_performance, catalog_hash

ROOT=Path(__file__).resolve().parents[1]
TREE="a"*40

@pytest.fixture(autouse=True)
def independent_catalog(tmp_path,monkeypatch):
    # The oracle never derives expected source from certification.py, including
    # when the mutation runner is testing that verifier. Use a separate tiny tree.
    import sys
    from scripts.dragon_analyzer import certification
    catalog={"contract":("scripts/test_example.py",[
        ("example bug","example.py","return 1","return 2","test_value")])}
    source=tmp_path/"scripts/dragon_analyzer/example.py"
    source.parent.mkdir(parents=True)
    source.write_text("def value():\n    return 1\n")
    monkeypatch.setattr(certification,"SUITES",catalog)
    monkeypatch.setattr(sys.modules[__name__],"SUITES",catalog)
    monkeypatch.setattr(sys.modules[__name__],"ROOT",tmp_path)


def report(version="3.11"):
    suites=[]
    for name,(target,cases) in SUITES.items():
        rows=[]
        for label,filename,old,new,test in cases:
            src=(ROOT/"scripts/dragon_analyzer"/filename).read_text()
            changed=mutate_text(src,old,new)
            rows.append({"label":label,"file":filename,"test":test,"status":"killed","exit_code":1,
                         "expected_tests":1,"observed_tests":1,"failed_tests":[target.replace("/",".").removesuffix(".py")+"::"+test],
                         "source_before":hashlib.sha256(src.encode()).hexdigest(),
                         "source_after":hashlib.sha256(changed.encode()).hexdigest(),"error":None})
        suites.append({"suite":name,"target":target,"baseline":{"status":"pass","tests":1,"exit_code":0,"error":None},
                       "cases":rows,"counts":{"killed":len(rows)},"passed":True})
    n=sum(len(cases) for _,cases in SUITES.values())
    return {"schema_version":1,"kind":"targeted_source_mutation_development","source_snapshot":"git_tree",
            "candidate":{"commit":"b"*40,"tree":TREE,"tracked_clean":True},
            "catalog_sha256":hashlib.sha256(json.dumps(SUITES,sort_keys=True,separators=(",",":")).encode()).hexdigest(),"python":version+".9","planned":n,
            "counts":{"killed":n},"suites":suites,"passed":True,"release_authorized":False}

def test_exact_catalog_and_tree():
    assert catalog_hash()==report()["catalog_sha256"]
    assert inspect_mutations(ROOT,TREE,report(),"3.11")==[]

def test_wrong_tree_not_admitted():
    r=report();r["candidate"]["tree"]="c"*40
    assert "candidate_tree_mismatch" in inspect_mutations(ROOT,TREE,r,"3.11")

def test_incomplete_suite_not_admitted_even_if_summary_passes():
    r=report();r["suites"][0]["cases"].pop()
    assert "case_census:contract" in inspect_mutations(ROOT,TREE,r,"3.11")

def test_wrong_catalog_not_admitted():
    r=report();r["catalog_sha256"]="0"*64
    assert "catalog_mismatch" in inspect_mutations(ROOT,TREE,r,"3.11")

def test_fake_kill_not_admitted():
    r=report();r["suites"][0]["cases"][0]["exit_code"]=2
    assert "invalid_kill:contract" in inspect_mutations(ROOT,TREE,r,"3.11")

def test_source_hash_mismatch_not_admitted():
    r=report();r["suites"][0]["cases"][0]["source_after"]="0"*64
    assert "source_mismatch:contract" in inspect_mutations(ROOT,TREE,r,"3.11")

def test_both_versions_needed_and_no_synthetic_release():
    one=certify(ROOT,TREE,[report()],protected_unchanged=True)
    assert one["automated_matrix_complete"] is False
    both=certify(ROOT,TREE,[report(),report("3.12")],protected_unchanged=True)
    assert both["automated_matrix_complete"] is True
    assert both["status"]=="blocked" and both["score"] is None
    assert both["release_authorized"] is False and len(both["missing_gates"])==16

def test_duplicate_version_not_matrix():
    r=certify(ROOT,TREE,[report(),report()],protected_unchanged=True)
    assert r["automated_matrix_complete"] is False

def test_protected_data_changes_block():
    r=certify(ROOT,TREE,[report(),report("3.12")],protected_unchanged=False)
    assert r["automated_matrix_complete"] is False
    assert "protected_data_changed" in r["issues"]

def timing():
    return {"environment":"a"*64,"input":"b"*64,"workloads":{"allocation":{"samples_ms":[10,11,12,13,14],"output_digest":"c"*64}}}

def test_comparable_performance_and_explicit_budget():
    p=timing()
    assert compare_performance(p,p,{"allocation":{"max_median_ms":15,"max_regression_ratio":1.1}})["status"]=="development_pass"
    q=timing();q["workloads"]["allocation"]["samples_ms"]=[20]*5
    assert compare_performance(p,q,{"allocation":{"max_median_ms":30,"max_regression_ratio":1.1}})["status"]=="blocked"

def test_different_environment_or_inputs_cannot_certify():
    p=timing()
    for field in ("environment","input"):
        q=timing();q[field]="d"*64
        assert compare_performance(p,q,{"allocation":{"max_median_ms":15,"max_regression_ratio":1.1}})["status"]=="blocked"

def test_changed_output_or_missing_budget_blocks():
    p=timing();q=timing();q["workloads"]["allocation"]["output_digest"]="d"*64
    assert compare_performance(p,q,{"allocation":{"max_median_ms":15,"max_regression_ratio":1.1}})["status"]=="blocked"
    assert compare_performance(p,p,{})["status"]=="blocked"


def test_unrelated_test_failure_rejected():
    r=report()
    r["suites"][0]["cases"][0]["failed_tests"]=["other.module::test_value"]
    assert "invalid_kill:contract" in inspect_mutations(ROOT,TREE,r,"3.11")


def test_reported_summary_cannot_override_failed_baseline():
    r=report()
    r["suites"][0]["baseline"]["exit_code"]=1
    assert "baseline:contract" in inspect_mutations(ROOT,TREE,r,"3.11")


def test_certification_import_without_site_packages():
    import subprocess
    import sys
    from pathlib import Path
    repo=Path(__file__).resolve().parents[1]
    result=subprocess.run([sys.executable,"-S","-m","scripts.dragon_analyzer.certification","--help"],
                          cwd=repo,capture_output=True,text=True,timeout=30)
    assert result.returncode==0, result.stderr
    assert "--reports" in result.stdout


def test_public_package_exports_remain_compatible():
    from scripts.dragon_analyzer import DragonAnalyzer, DragonData, DragonScreenshotOCR
    from scripts.dragon_analyzer.analyzer import DragonAnalyzer as Analyzer
    from scripts.dragon_analyzer.models import DragonData as Data
    from scripts.dragon_analyzer.ocr import DragonScreenshotOCR as OCR
    assert (DragonAnalyzer,DragonData,DragonScreenshotOCR)==(Analyzer,Data,OCR)


def test_checkout_snapshot_mode_required():
    r=report()
    r["source_snapshot"]="working_directory"
    assert "source_snapshot_mismatch" in inspect_mutations(ROOT,TREE,r,"3.11")
