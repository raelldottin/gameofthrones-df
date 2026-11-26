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
    ("reverse counter", "battle.py", "return 1.07", "return .93", "test_counter_cycle"),
    ("accept capacity as start", "battle.py", 'raw.get("start_troops",raw.get("troops_start"))', 'raw.get("start_troops",raw.get("troops_start",raw.get("troops_start_or_capacity")))', "test_capacity_not_start"),
    ("ignore delta mismatch", "battle.py", 'raise ValueError("round delta mismatch")', "pass", "test_wrong_round_delta_rejected"),
    ("ignore net loss mismatch", "battle.py", 'raise ValueError("inconsistent net loss")', "pass", "test_inconsistent_loss_rejected"),
    ("accept false victory", "battle.py", 'raise ValueError("inconsistent outcome")', "pass", "test_victory_requires_enemy_zero"),
    ("ignore mode isolation", "battle.py", 'if r["mode"]!=mode or not r["trace"]:', 'if not r["trace"]:', "test_no_cross_mode_calibration"),
    ("train on held out group", "battle.py", 'if x["group"]!=r["group"]', 'if x["id"]!=r["id"]', "test_group_exclusion"),
    ("continue after elimination", "battle.py", 'if p==0 or e==0:', "if False:", "test_simulation_stops_at_elimination"),
]


def run(root: Path, test: str = "") -> tuple[int, list[str], str]:
    report = root / "mutation-junit.xml"
    report.unlink(missing_ok=True)
    target = "scripts/test_battle.py" + ("::" + test if test else "")
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
