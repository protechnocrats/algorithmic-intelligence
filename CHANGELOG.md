# Changelog

Release notes for every version of the Algorithmic Intelligence skill (`algorithmic-intelligence`). Each release's section is published as its GitHub release notes when the version's tag is pushed (see [RELEASING.md](RELEASING.md)).

Versions follow [semantic versioning](https://semver.org): while the major version is 0, a minor release (0.2.0) can change how the skill behaves, and a patch release (0.1.1) only fixes wording or mistakes without changing behavior on purpose.

## [Unreleased]

### Changed

- **Changes to how code calls another system are now verifiable.** Batching, deduplicating, or caching calls to a database or service is checked against a fake that implements the collaborator's documented contract (limits, missing items, partial failure, error order), comparing everything callers observe and the requested items as a set. Only behavior the documentation does not settle stays unverified. In round 7 the skill held such changes back as unverifiable even when they were safe.
- **Before filing a speedup as a behavior change, the agent looks for a version that keeps the behavior:** redo costly work only when its input changed, hand out copies of cached values, or read data that something outside the operation may change once per operation (only results the original could also produce). A behavior change is listed only when no such version exists, with each way tried. When the developer declines a behavior change, the agent applies the version that keeps the behavior. In round 8, every Haiku session with the skill left two items slow for lack of this.
- **The agent reads the file for its mode before looking at code** (`WORKFLOW.md` or `WRITING-NEW-CODE.md`), and `DIFFERENTIAL-TESTING.md` before writing differential tests. In round 8, 6 of 8 sessions read neither.
- **The agent states its mode first.** The instruction now opens `SKILL.md` and the first step of each workflow, since sessions often skipped it.
- **The A/A run of a differential test is required only when the behavior can vary between runs** (time, randomness, hash or iteration order, concurrency, external systems); deterministic code records "not needed".
- **The end-to-end share is its own field** in the apply results and part of each item's prediction, since sessions often left it out.

### Added

- **Harness guards** (none are installed with the skill or add to an agent's context): `evals/check-refs.py` fails CI on broken links, file names, section names, and rule numbers in the skill; `evals/rule-cases.py` generates `docs/RULE-EVIDENCE.md`, the eval cases that test each rule, from the answer keys, and CI fails when it is out of date; `evals/check-report.py` grades a session's report files against the formats in `REPORTING.md`. `CONTRIBUTING.md` gains "Pruning rules" (a rule with no case needs a case, not deletion) and "Guards". 32 answer-key cases now name the rules they test by number.

- **For contributors:** `docs/ARCHITECTURE.md` (what loads when, where each idea lives), `CONTRIBUTING.md`, issue and pull-request templates, `CODEOWNERS`, and a dev container with every toolchain the fixtures need (not yet built and tested).
- **Free self-tests:** `evals/selftest.sh` tests the eval runner with a stub agent (no API, no cost); `--probes` also checks the Java and Ruby grading probes against committed correct and wrong rewrites.
- **More runnable fixtures:** `run-pilot.sh` now runs the report flow on kotlin-shop, swift-shop, c-shop, and rust-shop; its stall watchdog no longer relies on Linux-only `stat` options.
- **Results overview:** `evals/results/README.md` summarizes every round and each clinic case's history.
- **Installing a specific release** is documented in the README (the tag's `skills/` folder URL).
- `examples/`: a real report-and-apply run on the Java fixture, unedited, and one item compared with and without the skill (hostile input on a hash map), linked from the top of the README.

### Evaluation

- Round 8 ([results](evals/results/2026-11-02-round8.md)), held-out Ruby project, 5 Haiku 5.5 pairs and 3 Opus 5.5 pairs: with Haiku, behavior differences in 0 of 5 sessions with the skill and 4 of 5 without (corrupted labels); with Opus, 0 of 3 in both, and the baseline was faster and cheaper. With the skill, Haiku held back two speedups as behavior changes where equivalent versions exist.
- Round 7 ([results](evals/results/2026-11-01-round7.md)), Haiku 5.5: on the held-out Ruby project, neither skill session changed behavior while the baseline corrupted user-visible labels; on the Java project, the baseline's "optimization" became 3.5 times slower on attacker-chosen keys, which none of 11 skill sessions did. Write mode loaded the skill with the README's recommended project-instruction line.

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
