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
    ("old five-star ceiling", "models.py", "le=10, strict=True", "le=5, strict=True", "test_valid_star_ranks[7]"),
    ("zero level accepted", "models.py", "Field(ge=1, strict=True)", "Field(ge=0, strict=True)", "test_invalid_reign_levels[0]"),
    ("fabricated confidence", "models.py", "default=None, ge=0.0, le=1.0", "default=1.0, ge=0.0, le=1.0", "test_missing_confidence_is_unknown"),
    ("wrong coordinate capture", "ocr.py", "int(loc_match.group(2)), int(loc_match.group(3))", "int(loc_match.group(1)), int(loc_match.group(2))", "test_coordinate_groups"),
    ("lost ability order", "ocr.py", "list(dict.fromkeys(abilities))", "sorted(set(abilities))", "test_ability_order_is_stable"),
    ("silenced engine error", "ocr.py", 'raise RuntimeError(f"OCR failed: {e}") from e', 'return ""', "test_ocr_engine_failure_is_visible"),
    ("conflict ignored", "analyzer.py", 'raise RuntimeError("Observation conflict: existing evidence differs")', "pass", "test_conflicting_observation_is_not_overwritten"),
    ("empty batch success", "analyzer.py", 'raise ValueError("no screenshots matched")', "return []", "test_empty_batch_fails"),
    ("unchecked adapter accepted", "analyzer.py", "observed = DragonData.model_validate_json(observed.model_dump_json())", "pass", "test_unchecked_adapter_data_is_rejected"),
    ("changed source ignored", "analyzer.py", 'raise RuntimeError("Screenshot changed during extraction")', "pass", "test_source_change_is_rejected"),
    ("CLI false success", "cli.py", "raise typer.Exit(code=1)", "raise typer.Exit(code=0)", "test_cli_analyze_and_batch_do_not_claim_success"),
]


def run(root: Path, test: str = "") -> tuple[int, list[str], str]:
    report = root / "mutation-junit.xml"
    report.unlink(missing_ok=True)
    target = "scripts/test_analyzer.py" + ("::" + test if test else "")
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
            if code == 1 and test in failures:
                print(f"KILLED {label} via {test}")
            else:
                print(f"SURVIVED OR INFRASTRUCTURE FAILURE {label}\n{output}")
                survivors.append(label)
    print(f"Killed {len(CASES)-len(survivors)}/{len(CASES)} targeted source mutants")
    return int(bool(survivors))


if __name__ == "__main__":
    raise SystemExit(main())
