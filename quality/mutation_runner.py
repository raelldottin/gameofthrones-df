"""Unified targeted mutation harness. Local evidence, never a release receipt."""
import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

if __package__:
    from .mutation_catalog import SUITES
else:
    from mutation_catalog import SUITES

ROOT=Path(__file__).resolve().parents[1]
INPUT_DIRS=("scripts","quality","player-state","armies","battle-logs","dragons",
            "mechanics","roster","analysis","docs","hatchery","heirlooms","market","world-map")
INPUT_FILES=("pyproject.toml","README.md","AGENTS.md","manifest.md","armies.json",
             "battles.json","dragons.json","habits.json","upgrade_system.json")


@dataclass(frozen=True)
class Case:
    label: str
    filename: str
    old: str
    new: str
    test: str


@dataclass(frozen=True)
class TestResult:
    __test__ = False
    code: int | None
    rows: tuple
    output: str
    error: str | None


def parse_junit(path):
    try:
        tree=ET.parse(path)
    except (ET.ParseError,OSError) as exc:
        raise ValueError("missing or invalid JUnit report") from exc
    rows=[]
    for node in tree.iter("testcase"):
        cls,name=node.get("classname"),node.get("name")
        outcomes=[v for v,tag in (("failure","failure"),("error","error"),("skip","skipped"))
                  if node.find(tag) is not None]
        if not cls or not name or len(outcomes)>1:
            raise ValueError("invalid testcase record")
        rows.append((cls,name,outcomes[0] if outcomes else "pass"))
    if not rows:
        raise ValueError("empty test census")
    return tuple(rows)


def select_cases(rows, test):
    selected={(cls,name) for cls,name,_ in rows
              if name==test or name.startswith(test+"[")}
    if not selected:
        raise ValueError("target test absent from clean census")
    return selected


def classify(result,expected):
    identities=[(cls,name) for cls,name,_ in result.rows]
    statuses=[status for _,_,status in result.rows]
    if (result.error is not None or not expected or len(identities)!=len(set(identities))
            or set(identities)!=expected or any(s not in ("pass","failure") for s in statuses)):
        return "infrastructure_error"
    if result.code==1 and "failure" in statuses:
        return "killed"
    if result.code==0 and all(s=="pass" for s in statuses):
        return "survived"
    return "infrastructure_error"


def mutate_text(text,old,new):
    if not old or old==new or text.count(old)!=1:
        raise ValueError("mutation source anchor missing, ambiguous or unchanged")
    return text.replace(old,new,1)


def snapshot(src,dst):
    """Copy only known project inputs; not a hostile-code sandbox."""
    for name in INPUT_DIRS:
        if (src/name).is_dir():
            shutil.copytree(src/name,dst/name,
                            ignore=shutil.ignore_patterns("__pycache__",".pytest_cache",
                                                          "*.pyc","mutation-junit.xml"))
    for name in INPUT_FILES:
        if (src/name).is_file():
            shutil.copy2(src/name,dst/name)


def execute(root,target,timeout=90):
    with tempfile.TemporaryDirectory(prefix="df-junit-") as tmp:
        report=Path(tmp)/"report.xml"
        env={k:v for k,v in os.environ.items()
             if k not in ("PYTEST_ADDOPTS","PYTEST_PLUGINS","PYTHONPATH","PYTHONPYCACHEPREFIX")}
        env.update(PYTHONPATH=str(root),PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
                   PYTHONDONTWRITEBYTECODE="1")
        try:
            p=subprocess.run([sys.executable,"-B","-m","pytest","-o","addopts=",
                              "-p","no:cacheprovider","-q",target,
                              "--junitxml",str(report)],cwd=root,env=env,
                             text=True,capture_output=True,timeout=timeout)
        except subprocess.TimeoutExpired:
            return TestResult(None,(),"","timeout")
        except OSError as exc:
            return TestResult(None,(),"",str(exc))
        output=p.stdout+p.stderr
        try:
            rows=parse_junit(report)
        except ValueError as exc:
            return TestResult(p.returncode,(),output,str(exc))
        return TestResult(p.returncode,rows,output,None)


def run_suite(root,name,target,cases,*,executor=execute):
    root=Path(root).resolve()
    with tempfile.TemporaryDirectory(prefix="df-clean-") as temp:
        clean=Path(temp)
        snapshot(root,clean)
        baseline=executor(clean,target)
    census={(c,n) for c,n,_ in baseline.rows}
    clean_ok=bool(census) and classify(baseline,census)=="survived"
    report={"suite":name,"target":target,"baseline":{"status":"pass" if clean_ok else "fail",
            "tests":len(census),"exit_code":baseline.code,"error":baseline.error},
            "cases":[],"passed":False}
    if not clean_ok:
        print("Clean baseline failed: "+name+"\n"+baseline.output[-4000:],file=sys.stderr)
        return report
    for case in cases:
        row={"label":case.label,"file":case.filename,"test":case.test}
        try:
            expected=select_cases(baseline.rows,case.test)
            if Path(case.filename).name!=case.filename or not case.filename.endswith(".py"):
                raise ValueError("invalid mutation source filename")
            with tempfile.TemporaryDirectory(prefix="df-mutant-") as temp:
                mutant=Path(temp)
                snapshot(root,mutant)
                path=mutant/"scripts/dragon_analyzer"/case.filename
                original=path.read_text(encoding="utf-8")
                updated=mutate_text(original,case.old,case.new)
                path.write_text(updated,encoding="utf-8")
                run=executor(mutant,target+"::"+case.test)
                row.update(status=classify(run,expected),exit_code=run.code,
                           expected_tests=len(expected),observed_tests=len(run.rows),
                           failed_tests=sorted(f"{c}::{n}" for c,n,s in run.rows if s=="failure"),
                           source_before=hashlib.sha256(original.encode()).hexdigest(),
                           source_after=hashlib.sha256(updated.encode()).hexdigest(),
                           error=run.error)
                if row["status"]!="killed":
                    print(run.output[-4000:],file=sys.stderr)
        except (OSError,ValueError) as exc:
            row.update(status="infrastructure_error",error=str(exc))
        report["cases"].append(row)
        print(f"{row['status'].upper()} {name}: {case.label}",file=sys.stderr,flush=True)
    report["counts"]=dict(Counter(r["status"] for r in report["cases"]))
    report["passed"]=bool(cases) and len(report["cases"])==len(cases) and all(
        r["status"]=="killed" for r in report["cases"])
    return report



def export_tree(root,destination,commit):
    """Materialize exact regular Git blobs; do not read dirty or untracked files."""
    root=Path(root);destination=Path(destination)
    if not destination.is_dir() or any(destination.iterdir()):
        raise ValueError("empty export destination required")
    entries=subprocess.check_output(["git","ls-tree","-r","-z",commit],cwd=root)
    validated=[]
    for entry in entries.split(b"\0"):
        if not entry:continue
        header,name=entry.split(b"\t",1)
        mode,kind,oid=header.decode("ascii").split()
        rel=Path(os.fsdecode(name))
        if (mode not in ("100644","100755") or kind!="blob" or rel.is_absolute()
                or any(x in (".","..",".git") for x in rel.parts) or not rel.parts):
            raise ValueError("unsupported tree entry")
        validated.append((mode,oid,rel))
    for mode,oid,rel in validated:
        path=destination/rel
        path.parent.mkdir(parents=True,exist_ok=True)
        data=subprocess.check_output(["git","cat-file","blob",oid],cwd=root)
        with path.open("xb") as f:f.write(data)
        path.chmod(0o755 if mode=="100755" else 0o644)


def git_info(root):
    def read(*args):
        return subprocess.check_output(["git",*args],cwd=root,text=True).strip()
    return {"commit":read("rev-parse","HEAD"),"tree":read("rev-parse","HEAD^{tree}"),
            "tracked_clean":subprocess.run(["git","diff","--quiet","HEAD","--"],cwd=root).returncode==0}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite",choices=tuple(SUITES),action="append")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args(argv)
    names=args.suite or list(SUITES)
    if len(names)!=len(set(names)):
        parser.error("duplicate suite")
    candidate=git_info(ROOT)
    catalog_hash=hashlib.sha256(json.dumps(SUITES,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    results=[]
    with tempfile.TemporaryDirectory(prefix="df-git-tree-") as temp:
        frozen=Path(temp)
        export_tree(ROOT,frozen,candidate["commit"])
        for name in names:
            target,raw=SUITES[name]
            results.append(run_suite(frozen,name,target,[Case(*row) for row in raw]))
    totals=Counter(r["status"] for s in results for r in s["cases"])
    planned=sum(len(SUITES[n][1]) for n in names)
    passed=candidate["tracked_clean"] and git_info(ROOT)==candidate and all(s["passed"] for s in results) and totals["killed"]==planned
    report={"schema_version":1,"kind":"targeted_source_mutation_development","source_snapshot":"git_tree",
            "candidate":candidate,"catalog_sha256":catalog_hash,"python":sys.version.split()[0],
            "planned":planned,"counts":dict(totals),"suites":results,"passed":passed,
            "release_authorized":False}
    payload=json.dumps(report,indent=2,sort_keys=True)+"\n"
    if args.output:
        with args.output.open("x",encoding="utf-8") as f:
            f.write(payload)
    print(payload)
    return int(not passed)


if __name__=="__main__":
    raise SystemExit(main())
