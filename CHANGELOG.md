# Changelog

Release notes for every version of the Algorithmic Intelligence skill (`algorithmic-intelligence`). Each release's section is published as its GitHub release notes when the version's tag is pushed (see [RELEASING.md](RELEASING.md)).

Versions follow [semantic versioning](https://semver.org): while the major version is 0, a minor release (0.2.0) can change how the skill behaves, and a patch release (0.1.1) only fixes wording or mistakes without changing behavior on purpose.

## [Unreleased]

### Changed

- **Clearer instructions throughout:** `SKILL.md`, `WORKFLOW.md`, `REPORTING.md`, `DIFFERENTIAL-TESTING.md`, `BENCHMARKING.md`, and `ALGORITHM-ARSENAL.md` rewritten in shorter sentences, with each instruction stated once and the rest pointing to it. No rule, step, threshold, example, or named section was removed.
- **Before filing a speedup as a behavior change, the agent looks for a version that keeps the behavior:** redo costly work only when its input changed, hand out copies of cached values, take the fast path and fall back to the original where it cannot match (for example, resend a failed batch one item at a time), or read data that something outside the operation may change once per operation. A behavior change is listed only when no such version exists, with each way tried. When the developer declines a behavior change, the agent applies the version that keeps the behavior.
- **Changes to how code calls another system are now verifiable.** Batching, deduplicating, or caching calls to a database or service is checked against a fake that implements the collaborator's documented contract (limits, missing items, partial failure, error order), comparing everything callers observe and the requested items as a set. Only behavior the documentation does not settle stays unverified.
- **The agent states its mode first, then reads the file for that mode before looking at code** (`WORKFLOW.md` or `WRITING-NEW-CODE.md`), and `DIFFERENTIAL-TESTING.md` before writing differential tests.
- **The agent says when it runs on a small model.** If it knows its model and the model is a small, fast, or low-cost tier, it adds one line after the mode: the skill is tested with coding-tier models such as Claude Sonnet and Opus.
- **New behavior traps,** from changes coding-tier models made in testing: numeric identity in hash keys (`1` against `1.0`), new size limits an optimization introduces, and batched queries that must keep values as bound parameters. In write mode, a cache key must include the user, tenant, and permissions when they change the result.
- **The A/A run of a differential test is required only when the behavior can vary between runs** (time, randomness, hash or iteration order, concurrency, external systems); deterministic code records "not needed".
- **The end-to-end share is its own field** in the apply results and part of each item's prediction.
- **One "Reproduce" section can cover every item** in `APPLY-RESULTS.md` when one harness tests them all.

### Added

- **For contributors:** `docs/ARCHITECTURE.md` (what loads when, where each idea lives), `CONTRIBUTING.md`, issue and pull-request templates, `CODEOWNERS`, and a dev container with the JDK, Ruby, Node, Rust, Python, and Swift toolchains.
- **Installing a specific release** is documented in the README (the tag's `skills/` folder URL).
- `docs/EVAL-PLAN.md`: the plan for the next evaluations (hostile inputs, security side effects of optimizations, unusual problems, and write mode, on Sonnet and Opus).

### Removed

- **The evaluation harness (`evals/`) and the examples (`examples/`),** to be rebuilt per `docs/EVAL-PLAN.md`. Both stay readable in the [repository history](https://github.com/protechnocrats/algorithmic-intelligence/tree/da47e4b), with every round's results.
- **The CI checks that depended on it** (token budgets, cross-references, rule evidence) and `docs/RULE-EVIDENCE.md`.

### Evaluation

Results on Claude Opus 5.5 from the rounds since 0.1.0 ([results in the history](https://github.com/protechnocrats/algorithmic-intelligence/tree/da47e4b/evals/results)), graded on every category including a judge reading each session's code and reports:
- Without the skill, Opus applied behavior changes on a general "apply all" in all 3 sessions where this could be scored. With it, Opus held every one for review, in 4 of 4 sessions.
- Bugs were reported to the developer in 4 of 4 sessions with the skill and 0 of 3 without.
- Sessions with the skill cost 1.7 to 3 times as much.

## [0.1.0] - 2026-11-01

The first release. Install it with `npx skills add https://github.com/protechnocrats/algorithmic-intelligence --skill algorithmic-intelligence`.

### What the skill does

- **Three modes.** Report mode analyzes existing code and changes nothing; apply mode optimizes the code the developer names, one item at a time; write mode builds new code with efficient algorithms and data structures from the first version. The agent states the mode it picked.
- **Fourteen mandatory rules,** among them: behavior is never changed without the developer's approval of that specific item; every change is verified with differential tests that compare the original and the optimized code; memory stays bounded across every copy that can exist at once; every call counts at its real cost, built-in and library calls included; lower bounds are stated with their basis and never invented; commits happen only when the developer authorizes them.
- **Analysis:** contracts, reachability from real entry points, cost along the call chain, the limiting resource (CPU, memory, I/O, network, lock, queue), and exposure (untrusted input, secrets, hard deadlines), with worst-case reasoning where attackers control the input, including adaptive adversaries that can observe outputs.
- **A discovery method** (`DISCOVERY.md`) for problems no known technique fits: 19 moves drawn from Knuth, Bentley, Dijkstra and Gries, Pólya, Karp, Tarjan, Mitzenmacher, Leiserson, Sedgewick, exchange arguments, parameterized algorithms, relaxations and duality, conditional lower bounds from fine-grained complexity, derivation by program transformation, and algorithms with predictions; a research log; and a table of which move to try when one stalls.
- **Verification:** four levels (tested, property-checked, exhaustively checked to a stated bound, proven), with "check the check": differential tests must catch a planted difference and pass with the original on both sides before they count.
- **Measurement:** predictions written before benchmarking, doubling experiments, an A/A run for the noise floor, sound statistics, memory measurement, the changed code's share of the whole operation, and a check that a proxy metric implies the real goal.
- **Languages:** companion files for Kotlin, Java, Python, Swift, JavaScript and TypeScript, C#, C, and Rust. For any other language the agent builds a profile and, with permission, saves it in the project (`.algorithmic-intelligence/languages/<LANGUAGE>.md`) for later sessions to reuse.
- **Techniques:** core tables plus 16 domain files (graphs and trees; sequences, DP, search, and NP-hard problems; strings and text; math and numerics; machine learning; images and signals; geometry and CAD; games and simulation; spatial data; hardware and concurrency; data at scale; optimization and scheduling; hostile inputs; distributed systems; queues and latency; specialized data structures).
- **Reports:** `OPTIMIZATION-REPORT.md` written once in report mode and never rewritten, `APPLY-RESULTS.md` written once in apply mode, and `BUGS-FOUND.md`. Bugs are documented, never fixed on purpose. Behavior changes are listed for review and marked in the code once approved.

### Evaluation

- Test projects in Kotlin, TypeScript, Swift, C, Rust, Java, Ruby, and Python with planted cases and answer keys; held-out Python and Ruby projects; grading probes for the Python, TypeScript, Java, and Ruby projects; a headless runner with a spending cap and a stall watchdog; cost, token, and permission-refusal statistics; trigger tests; token budgets; and checks of Kotlin claims the official documentation does not settle.
- Results so far are in `evals/results/`. On the held-out Python project (round 3), report-flow cases passed at 1.00 with the skill against 0.50 without it on Opus 5.5, and 0.83 against 0.39 on Haiku 5.5. On the Java tuning project (rounds 4 to 6, Haiku 5.5, with the skill only) no session changed the code's behavior.

### Known limitations

- Only Claude Code has been evaluated; the skill is written to be agent-neutral.
- The Java and Ruby projects have no baseline runs yet, the Ruby held-out project has not been run, and the Swift project has not been run on a Swift toolchain.
- Smaller models do not always load the skill for new-code requests from its description alone; the README gives a one-line project instruction that fixes most of it.
- Formal verification (proofs, model checking) is the least developed of the skill's roles.
