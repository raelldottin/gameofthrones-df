"""Measure repeatable local development workloads, not release performance certification."""
import hashlib
import json
import platform
import statistics
import time
from pathlib import Path
from scripts.dragon_analyzer.solver import evaluate, load_inputs
from scripts.dragon_analyzer.battle import audit
from scripts.dragon_analyzer.reconcile import digest, stage_legacy

ROOT=Path(__file__).resolve().parents[1]


def measure(fn, repeats=5):
    samples=[];hashes=[]
    fn()  # explicit warmup
    for _ in range(repeats):
        start=time.perf_counter_ns()
        result=fn()
        samples.append((time.perf_counter_ns()-start)/1e6)
        hashes.append(digest(result))
    if len(set(hashes))!=1:
        raise RuntimeError("nondeterministic workload result")
    return {"samples_ms":samples,"median_ms":statistics.median(samples),
            "max_ms":max(samples),"output_digest":hashes[0]}


def main():
    inputs=load_inputs(ROOT)
    results={"allocation":measure(lambda:evaluate(inputs)),
             "historical_battle_audit":measure(lambda:audit(ROOT)),
             "migration_staging":measure(lambda:stage_legacy(inputs["roster"],inputs["season"]))}
    print(json.dumps({"status":"development_measurement_only","python":platform.python_version(),
                      "platform":platform.platform(),"input_digest":digest(inputs),
                      "warmups":1,"repeats":5,"workloads":results,
                      "release_budget_verified":False},indent=2))


if __name__=="__main__":
    main()
