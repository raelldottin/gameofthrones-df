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
    ("trust submitted receipts", "release.py", "if digest(r) not in trusted_digests:", "if False:", "test_untrusted_receipts_block"),
    ("ignore candidate tree", "release.py", 'r["tree"]!=tree or r["policy"]!=POLICY_HASH', 'False or r["policy"]!=POLICY_HASH', "test_stale_tree_blocks"),
    ("ignore policy version", "release.py", 'r["tree"]!=tree or r["policy"]!=POLICY_HASH', 'r["tree"]!=tree or False', "test_stale_policy_blocks"),
    ("ignore failed gate", "release.py", 'or r["status"]!="pass"', "or False", "test_failed_gate_blocks"),
    ("ignore independence", "release.py", "if review==evaluator or review in implementers or evaluator in implementers:", "if False:", "test_unresolved_independence_blocks"),
    ("ignore minimum score", "release.py", "if score<95:", "if False:", "test_low_score_blocks"),
    ("allow missing QA evidence", "release.py", "or not evidence[k]", "or False", "test_qa_missing_evidence_blocks"),
    ("ignore unknown QA evidence", "release.py", "isinstance(x,str) and x in known", "isinstance(x,str)", "test_qa_evidence_cannot_reference_unknown_receipt"),
    ("authorize deployment", "release.py", '"issues":issues,"score":score,"release_authorized":False', '"issues":issues,"score":score,"release_authorized":True', "test_all_trusted_receipts_contract_only"),
]


def run(root: Path, test: str = "") -> tuple[int, list[str], str]:
    report = root / "mutation-junit.xml"
    report.unlink(missing_ok=True)
    target = "scripts/test_release.py" + ("::" + test if test else "")
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
