# Dynamic engineering workflow

Research → Plan → Write/Implement → Review → Benchmark → QA/Eval → accept or loop.

Each stage and retry requires a **new agent identity and fresh context**. Supervisor owns dispatch, budget and artifact handoffs; no self-approval. Each handoff includes source ledger, input commit, artifact hashes, assumptions, acceptance tests, failure evidence and stage decision. Keep reviewer and evaluator independent of implementer. Freeze benchmark fixtures and weights before implementation; additions create a version with a comparable baseline.

## Stage requirements

1. Research: verify evidence, distinguish assumptions, current mechanics and historical data.
2. Plan: design for testability first; pure domain core, injected OCR/filesystem/time, deterministic outputs, typed failures. Define regression tests, properties, edge cases, benchmark and architecture review before implementation.
3. Write: TDD red → green → improve; bug tests must fail on prior code, never weaken assertions to pass. Test the tests using fault injection, negative controls and eventually actual source mutation. Unknown evidence stays unknown.
4. Review: independent architecture and correctness review. Tests do not catch bad design. Prefer replacement over incremental refactoring where the existing boundary cannot satisfy its contract; require compatibility, migration, comparison and rollback. Never delete historical evidence.
5. Benchmark: run frozen golden cases, property/invariant tests, mutation checks, and measured latency/resource budgets. Do not substitute line coverage for behavior. Report failures, abstentions and data limitations.
6. QA/Eval: score correctness 35, test effectiveness 25, architecture 20, reproducibility 10, operational safety 10 (100 total). Proposed acceptance ≥95, zero unresolved critical/high defects, all hard gates pass and no benchmark regression. Missing evidence is not a pass. Independent evaluator records evidence per dimension; never invent a score.
7. Loop: send invalid assumptions to Research, design defects to Plan, bugs to Write, review issues to Review, measurement issues to Benchmark, then reevaluate. Every iteration uses fresh agents. Default maximum three repair cycles, configurable by supervisor; on exhaustion or blocker park with evidence. No indefinite loops or silent gate bypass.

## Implemented baseline

Run `node quality/benchmark.mjs`. The gate checks dated roster/season/formation JSON against screenshot-transcribed affinities and five golden profile anchors. It rejects 21 injected input faults and requires the disabled-validator negative control to detect zero. The first run rejected legitimate provenance fields; explicit allowlist correction and one additional confirmation-source fault case repaired that false positive. This is input fault injection, not source-code mutation coverage or OCR accuracy. Fixture is frozen to Nov 26, not automatically regenerated from candidate output; historical snapshot changes require reviewed evidence. No private screenshots are added.

Actual multi-agent dispatch, independent QA, source mutation and full release evaluation are not yet implemented. This audit used one assistant, not separate agents. The local pure JS benchmark ran against fetched repository content; the Node wrapper and CI are separate verification targets.

What you do not measure regresses. Be ambitious, but report measured results and limitations. No fake defaults, hidden failures, or unimplemented success paths. Reign level resets; never persist it as permanent progression.
