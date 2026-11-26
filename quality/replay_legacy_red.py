"""Replay selected regression tests against pinned pre-fix source, not broken TOML."""
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "381883cfeafa4ca9ab5be234e5a8310f66306f11"
EXPECTED = {
    "test_valid_star_ranks[7]",
    "test_invalid_reign_levels[0]",
    "test_coordinate_groups",
    "test_missing_confidence_is_unknown",
    "test_ocr_engine_failure_is_visible",
    "test_portable_output_config",
}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="dragonfire-red-") as temp:
        root = Path(temp)
        for name in ["__init__.py", "models.py", "analyzer.py", "ocr.py", "config.py", "cli.py"]:
            relative = "scripts/dragon_analyzer/" + name
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(subprocess.check_output(
                ["git", "show", OLD + ":" + relative], cwd=ROOT))
        shutil.copy2(ROOT / "scripts/test_analyzer.py", root / "scripts/test_analyzer.py")
        config = root / "pytest.ini"
        config.write_text("[pytest]\n")
        xml = root / "red.xml"
        args = [sys.executable, "-B", "-m", "pytest", "-c", str(config), "-q",
                "--junitxml", str(xml)]
        args.extend("scripts/test_analyzer.py::" + name for name in sorted(EXPECTED))
        result = subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=90,
                                env={**os.environ, "PYTHONPATH": str(root),
                                     "DRAGONFIRE_OUTPUT": str(root / "output")})
        print(result.stdout + result.stderr)
        if not xml.exists():
            return 1
        cases = list(ET.parse(xml).iter("testcase"))
        failed = {c.attrib["name"] for c in cases if c.find("failure") is not None}
        print("Expected original-code failures:", sorted(EXPECTED))
        print("Observed original-code failures:", sorted(failed))
        # Reject collection failures, skipped cases and unrelated failures.
        return int(not (result.returncode == 1 and len(cases) == len(EXPECTED)
                        and failed == EXPECTED and not any(c.find("error") is not None for c in cases)))


if __name__ == "__main__":
    raise SystemExit(main())
