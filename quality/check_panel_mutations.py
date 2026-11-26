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
    ("fabricated star", "panel.py", "# Star icons and habits are deliberately not inferred from relic thresholds.\n    return out", "out['stars'] = 3\n    return out", "test_no_star_inference"),
    ("name fallback", "panel.py", "names.get(lines[0].casefold())", "names.get(lines[0].casefold(), next(iter(names.values()), None))", "test_missing_or_corrupt_name_is_unknown"),
    ("zero energy cap", "panel.py", "if energy and number(energy[2]) > 0:", "if energy:", "test_zero_energy_maximum_is_unknown"),
    ("ambiguous relics accepted", "panel.py", "if len(relics) == 1 and", "if len(relics) >= 1 and", "test_conflicting_relic_rows_abstain"),
    ("sign stripped", "panel.py", "if match and re.search", "if False and re.search", "test_negative_values_are_not_made_positive"),
    ("candidate falsely verified", "panel_reader.py", '"status": "unverified_candidate"', '"status": "verified"', "test_preview_is_unverified_and_does_not_write"),
]


def run(root: Path, test: str = "") -> tuple[int, list[str], str]:
    report = root / "mutation-junit.xml"
    report.unlink(missing_ok=True)
    target = "scripts/test_panel.py" + ("::" + test if test else "")
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
