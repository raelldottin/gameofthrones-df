"""Targeted source mutation gate: each real code change must fail its named test."""
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ("ignore habit progression", "solver.py", '10*dragon["stars"]+2*sum(dragon["habits"])', '10*dragon["stars"]', "test_permanent_score_is_explicit"),
    ("ignore affinity", "solver.py", 'counts[i]>=goal[i] or t not in d["affinities"]', 'counts[i]>=goal[i]', "test_infeasible_is_explicit"),
    ("seasonal score leakage", "solver.py", 'points+value', 'points+value+d["capacity"]', "test_seasonal_capacity_does_not_change_persistent_selection"),
    ("ignore retention", "solver.py", 'kept+int(retain.get(d["name"])==t)', 'kept', "test_retention_breaks_equal_scores"),
    ("locked commander eligible", "solver.py", 'type(c.get("rank")) is int and c["rank"]>0', 'True', "test_locked_commander_excluded_and_unique"),
    ("ignore readiness objective", "solver.py", 'value=score(d) if objective=="permanent" else d["capacity"]', "value=score(d)", "test_readiness_mode_has_separate_objective"),
    ("ignore input fingerprints", "solver.py", 'return digest(inputs)', 'return digest(inputs["roster"])', "test_fingerprint_includes_commander_catalog_equipment_and_reign"),
]


def run(root: Path, test: str = "") -> tuple[int, list[str], str]:
    report = root / "mutation-junit.xml"
    report.unlink(missing_ok=True)
    target = "scripts/test_solver.py" + ("::" + test if test else "")
    proc = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-o", "addopts=", "-q",
         target, "--junitxml", str(report)],
        cwd=root, text=True, capture_output=True, timeout=90,
        env={**os.environ, "PYTHONPATH": str(root), "PYTHONPYCACHEPREFIX": str(root / ".fresh-cache")},
    )
    failures = []
    if report.exists():
        failures = [case.attrib.get("name", "") for case in ET.parse(report).iter("testcase")
                    if case.find("failure") is not None]
    return proc.returncode, failures, proc.stdout + proc.stderr


def main() -> int:
    code, _, output = run(ROOT)
    if code:
        print("Clean baseline failed:\n" + output)
        return 1
    survivors = []
    for label, filename, old, new, test in CASES:
        with tempfile.TemporaryDirectory(prefix="dragonfire-mutation-") as temp:
            root = Path(temp)
            shutil.copytree(ROOT / "scripts", root / "scripts",
                            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
            shutil.copy2(ROOT / "pyproject.toml", root / "pyproject.toml")
            path = root / "scripts" / "dragon_analyzer" / filename
            text = path.read_text()
            if text.count(old) != 1:
                raise RuntimeError(f"Mutation target changed: {label}")
            path.write_text(text.replace(old, new, 1))
            code, failures, output = run(root, test)
            if code == 1 and any(n == test or n.startswith(test + "[") for n in failures):
                print(f"KILLED {label} via {test}")
            else:
                print(f"SURVIVED OR INFRASTRUCTURE FAILURE {label}\n{output}")
                survivors.append(label)
    print(f"Killed {len(CASES)-len(survivors)}/{len(CASES)} targeted source mutants")
    return int(bool(survivors))


if __name__ == "__main__":
    raise SystemExit(main())
