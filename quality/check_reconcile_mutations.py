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
    ("ignore approval", "reconcile.py", "if not nonblank(reviewer):", "if False:", "test_no_approval_no_promotion"),
    ("allow self approval", "reconcile.py", 'elif reviewer == e["extractor_id"]:', "elif False:", "test_self_approval_is_not_independent"),
    ("allow seasonal leak", "reconcile.py", "if not exact_keys(p, PERMANENT) or not exact_keys(s, SEASONAL):", "if not exact_keys(s, SEASONAL):", "test_seasonal_field_in_permanent_is_rejected"),
    ("ignore source conflict", "reconcile.py", 'quarantine[key]="source_conflict"', "pass", "test_same_source_different_payload_quarantines_both"),
    ("ignore timestamp conflict", "reconcile.py", 'quarantine[key]="timestamp_conflict"', "pass", "test_same_timestamp_disagreement_quarantines_both"),
    ("accept wrong reign", "reconcile.py", 'elif active_reign(registry,at)!=e["reign_id"]:', "elif False:", "test_reign_mismatch_is_not_inferred"),
    ("allow progression regression", "reconcile.py", "if progression_regresses(permanent.get(name),e,prior):", "if False:", "test_same_reign_level_regression_even_with_more_stars"),
    ("retain old levels on reset", "reconcile.py", "seasonal=copy.deepcopy(history.get(current,{}))", "seasonal=copy.deepcopy(next(iter(history.values()),{}))", "test_reign_reset_keeps_permanent_and_clears_current_season"),
    ("ignore cutoff", "reconcile.py", "if at>cutoff:", "if False:", "test_future_observations_do_not_affect_as_of_snapshot"),
    ("ignore reign in plan fingerprint", "reconcile.py", '"reign":current,"permanent":permanent,"seasonal":seasonal', '"permanent":permanent,"seasonal":seasonal', "test_empty_reign_changes_formation_basis"),
    ("accept missing unlocked habits", "reconcile.py", 'len(p["habits"]) == p["stars"]//2', 'len(p["habits"]) <= p["stars"]//2', "test_missing_unlocked_habit_is_invalid"),
    ("ignore legacy profile source", "reconcile.py", 'if x.get("source_screenshot")!=y.get("source_screenshot") or x.get("source_screenshot") not in sources:', "if False:", "test_legacy_mismatched_profile_source_rejected"),
    ("allow xp regression", "reconcile.py", 'if s["level"] == previous_season["level"] and s["xp_current"] < previous_season["xp_current"]:', "if False:", "test_same_reign_xp_regression"),
]


def run(root: Path, test: str = "") -> tuple[int, list[str], str]:
    report = root / "mutation-junit.xml"
    report.unlink(missing_ok=True)
    target = "scripts/test_reconcile.py" + ("::" + test if test else "")
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
