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
    ("accept missing icons", "visual.py", "return sum(slots) or None", "return sum(slots)", "test_rank_contract"),
    ("accept out-of-order icons", "visual.py", "if slots!=sorted(slots,reverse=True) or (2 in slots and 0 in slots): return None", "pass", "test_rank_contract"),
    ("lose blue title contrast", "visual.py", "np.max(a,axis=2) if kind=='name' else np.min(a,axis=2)", "np.min(a,axis=2)", "test_blue_name_contrast_preserved"),
    ("trust original bad level", "visual.py", "out['level']=int(level) if re.fullmatch(r'[1-9]\\d{0,2}',level) else None", "pass", "test_isolated_level_replaces_whole_panel_error"),
    ("fabricate name from catalog", "visual.py", "names.get(texts['name'].strip().casefold())", "names.get(texts['name'].strip().casefold(),next(iter(names.values()),None))", "test_unknown_name_no_fuzzy_fallback"),
    ("overwrite primary power", "visual.py", "if out['power'] is None and re.fullmatch(NUMBER,power):", "if re.fullmatch(NUMBER,power):", "test_existing_stats_not_overwritten_by_secondary_ocr"),
    ("candidate false promotion", "visual_reader.py", '"status":"unverified_candidate"', '"status":"verified"', "test_visual_reader_never_promotes_or_writes"),
]


def run(root: Path, test: str = "") -> tuple[int, list[str], str]:
    report = root / "mutation-junit.xml"
    report.unlink(missing_ok=True)
    target = "scripts/test_visual.py" + ("::" + test if test else "")
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
