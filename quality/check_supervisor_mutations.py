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
    ("reuse agent", "supervisor.py", "agent in agents or context in contexts", "context in contexts", "test_reused_agent_blocked"),
    ("reuse context", "supervisor.py", "agent in agents or context in contexts", "agent in agents", "test_reused_context_blocked"),
    ("ignore corrupt artifact", "supervisor.py", 'or res.get("artifact_hash")!=hash_bytes(blob)', "or False", "test_corrupt_artifact_blocked"),
    ("stale benchmark candidate", "supervisor.py", 'b["candidate_hash"]!=candidate or b["fixture_hash"]', 'False or b["fixture_hash"]', "test_benchmark_stale_candidate_blocked"),
    ("ignore hard gate", "supervisor.py", "passed=all(g.values())", "passed=True", "test_failed_gate_never_accepted"),
    ("ignore latency regression", "supervisor.py", 'v<=min(s["max"],s["baseline"])', 'v<=s["max"]', "test_metric_regression_blocks_even_if_above_threshold"),
    ("stale QA", "supervisor.py", 'or e["benchmark_hash"]!=benchmark_hash', "or False", "test_stale_qa_rejected"),
    ("ignore score threshold", "supervisor.py", 'if score<p["min_score"]:', "if False:", "test_low_score_blocks"),
    ("unresolved architecture issue", "supervisor.py", 'if any(i["severity"] in ("high","critical") for i in issues):', "if False:", "test_unresolved_high_blocks"),
    ("allow mutable request", "supervisor.py", "if req!=expected or not isinstance(res,dict):", "if not isinstance(res,dict):", "test_policy_cannot_be_mutated_by_adapter"),
    ("ignore run binding", "supervisor.py", 'req={"stage":stage,"run_id":run_id,', 'req={"stage":stage,', "test_run_id_binds_request_and_rejects_prior_run_receipt"),
    ("omit active artifacts", "supervisor.py", '"active_artifacts":{k:{"artifact_hash":v["artifact_hash"],"artifact_hex":v["artifact_hex"]} for k,v in active.items()},', '"active_artifacts":{},', "test_all_active_artifacts_available_to_benchmark"),
    ("ignore repair limit", "supervisor.py", 'if repairs>=p["max_repairs"]:', 'if repairs>=p["max_repairs"]+1:', "test_exhaustion_is_bounded"),
]


def run(root: Path, test: str = "") -> tuple[int, list[str], str]:
    report = root / "mutation-junit.xml"
    report.unlink(missing_ok=True)
    target = "scripts/test_supervisor.py" + ("::" + test if test else "")
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
