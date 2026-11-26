"""Test the mutation framework itself, including real subprocess canaries."""
import json
from pathlib import Path
import pytest
from quality.mutation_runner import (
    Case, classify, parse_junit, select_cases, mutate_text, run_suite, TestResult,
)
from quality.mutation_catalog import SUITES

def result(code, *rows):
    return TestResult(code,tuple(rows),"",None)

A=("scripts.test_example","test_value[1]")
B=("scripts.test_example","test_value[2]")
EXPECTED={A,B}

def test_kill_needs_expected_failure_and_complete_census():
    assert classify(result(1,(*A,"failure"),(*B,"pass")),EXPECTED)=="killed"

def test_zero_exit_is_survivor():
    assert classify(result(0,(*A,"pass"),(*B,"pass")),EXPECTED)=="survived"

@pytest.mark.parametrize("code,rows",[
    (1,[(*A,"failure")]),
    (1,[(*A,"failure"),(*B,"error")]),
    (1,[(*A,"failure"),(*B,"skip")]),
    (1,[(*A,"failure"),(*B,"failure"),(*B,"failure")]),
    (1,[(*A,"failure"),("wrong.module",B[1],"pass")]),
    (2,[(*A,"failure"),(*B,"pass")]),
    (0,[(*A,"failure"),(*B,"pass")]),
    (1,[(*A,"pass"),(*B,"pass")]),
    (5,[]),
])
def test_infrastructure_or_inconsistent_evidence_never_killed(code,rows):
    assert classify(result(code,*rows),EXPECTED)=="infrastructure_error"

def test_timeout_never_killed():
    assert classify(TestResult(None,(),"","timeout"),EXPECTED)=="infrastructure_error"

def test_select_parametrized_cases_exactly():
    rows=((*A,"pass"),(*B,"pass"),("scripts.test_example","test_value_extra","pass"))
    assert select_cases(rows,"test_value")==EXPECTED
    assert select_cases(rows,"test_value[1]")=={A}

def test_missing_target_rejected():
    with pytest.raises(ValueError):
        select_cases(((*A,"pass"),),"not_a_test")

def test_mutation_requires_unique_match():
    assert mutate_text("abc","b","x")=="axc"
    for text in ("abcabc","zzz"):
        with pytest.raises(ValueError):
            mutate_text(text,"b","x")

def test_invalid_xml_is_not_evidence(tmp_path):
    path=tmp_path/"bad.xml"
    path.write_text("<broken")
    with pytest.raises(ValueError):
        parse_junit(path)

def test_catalog_preserves_all_original_cases():
    assert {name:len(cases) for name,(_,cases) in SUITES.items()}=={
        "contract":11,"panel":6,"visual":7,"reconcile":13,
        "solver":7,"battle":8,"supervisor":13,"release":9,"runtime":9,"icons":7}
    assert sum(len(cases) for _,cases in SUITES.values())==90

def test_real_canaries_and_source_immutability(tmp_path):
    root=tmp_path/"project"
    source=root/"scripts/dragon_analyzer/example.py"
    source.parent.mkdir(parents=True)
    source.write_text("def value():\n    return 1\n")
    (root/"scripts/test_example.py").write_text(
        "from scripts.dragon_analyzer.example import value\n"
        "def test_value():\n    assert value()==1\n")
    (root/"pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    cases=[Case("known bug","example.py","return 1","return 2","test_value"),
           Case("equivalent","example.py","return 1","return (1)","test_value"),
           Case("syntax error","example.py","return 1","return (","test_value"),
           Case("missing target","example.py","return 7","return 2","test_value")]
    original=source.read_bytes()
    report=run_suite(root,"canary","scripts/test_example.py",cases)
    assert report["baseline"]["status"]=="pass"
    assert [r["status"] for r in report["cases"]]==[
        "killed","survived","infrastructure_error","infrastructure_error"]
    assert report["passed"] is False
    assert source.read_bytes()==original
    assert not list(root.rglob("*.xml"))

def test_broken_baseline_blocks_all_mutants(tmp_path):
    root=tmp_path/"project"
    (root/"scripts/dragon_analyzer").mkdir(parents=True)
    (root/"scripts/test_example.py").write_text("def test_value():\n    assert False\n")
    (root/"pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    report=run_suite(root,"canary","scripts/test_example.py",[
        Case("bug","example.py","a","b","test_value")])
    assert report["baseline"]["status"]=="fail"
    assert report["cases"]==[]
    assert report["passed"] is False


@pytest.mark.parametrize("module",["reconcile","supervisor"])
def test_domain_core_has_no_direct_io_dependencies(module):
    import ast
    root=Path(__file__).resolve().parents[1]
    tree=ast.parse((root/"scripts/dragon_analyzer"/(module+".py")).read_text())
    forbidden={"os","pathlib","subprocess","socket","requests","httpx","urllib",
               "pytesseract","cv2","sqlite3","shutil"}
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            assert all(a.name.split(".")[0] not in forbidden for a in node.names)
        if isinstance(node,ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
            assert node.func.id not in {"open","exec","eval","__import__"}
