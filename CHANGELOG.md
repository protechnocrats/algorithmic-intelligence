# Changelog

Release notes for every version of the Algorithmic Intelligence skill (`algorithmic-intelligence`). Each release's section is published as its GitHub release notes when the version's tag is pushed (see [RELEASING.md](RELEASING.md)).

Versions follow [semantic versioning](https://semver.org): while the major version is 0, a minor release (0.2.0) can change how the skill behaves, and a patch release (0.1.1) only fixes wording or mistakes without changing behavior on purpose.

## [Unreleased]

### Changed

- **Clearer instructions throughout:** `SKILL.md`, `WORKFLOW.md`, `REPORTING.md`, `DIFFERENTIAL-TESTING.md`, `BENCHMARKING.md`, and `ALGORITHM-ARSENAL.md` rewritten in shorter sentences, with each instruction stated once and the rest pointing to it. No rule, step, threshold, example, or named section was removed.
- **Before filing a speedup as a behavior change, the agent looks for a version that keeps the behavior:** redo costly work only when its input changed, hand out copies of cached values, take the fast path and fall back to the original where it cannot match (for example, resend a failed batch one item at a time), or read data that something outside the operation may change once per operation. A behavior change is listed only when no such version exists, with each way tried. When the developer declines a behavior change, the agent applies the version that keeps the behavior.
- **Changes to how code calls another system are now verifiable.** Batching, deduplicating, or caching calls to a database or service is checked against a fake that implements the collaborator's documented contract (limits, missing items, partial failure, error order), comparing everything callers observe and the requested items as a set. Only behavior the documentation does not settle stays unverified.
- **The agent states its mode first, then reads the file for that mode before looking at code** (`WORKFLOW.md` or `WRITING-NEW-CODE.md`), and `DIFFERENTIAL-TESTING.md` before writing differential tests.
- **The agent says when it runs on a small model.** If it knows its model and the model is a small, fast, or low-cost tier, it adds one line after the mode: the skill is built for coding-tier models such as Claude Sonnet and Opus.
- **New behavior traps:** numeric identity in hash keys (`1` against `1.0`), new size limits an optimization introduces, and batched queries that must keep values as bound parameters. In write mode, a cache key must include the user, tenant, and permissions when they change the result.
- **The A/A run of a differential test is required only when the behavior can vary between runs** (time, randomness, hash or iteration order, concurrency, external systems); deterministic code records "not needed".
- **The end-to-end share is its own field** in the apply results and part of each item's prediction.
- **One "Reproduce" section can cover every item** in `APPLY-RESULTS.md` when one harness tests them all.

- **The skill loads for more requests.** The description now leads with speed requests ("fix the performance problem", "make it faster", a profile or hot spot), including ones about a single small function or a regular expression, and covers new code that parses or imports files or adds a cache.
- **The mode file is read before any code.** `SKILL.md` now says that invoking the skill loads only its summary, and that skipping `WORKFLOW.md` or `WRITING-NEW-CODE.md` is the most common way the skill fails.
- **Behavior changes on inputs that "should not happen" are held for review.** If the code accepts a cyclic, malformed, out-of-range, or hostile input, a rewrite that handles it differently (a hang instead of an error) is a behavior change, and mentioning it in a note does not approve it. Schema changes, migrations, new indexes, and configuration changes need approval of that specific item even when results are unchanged.
- **"Fixed as a side effect" needs proof.** The agent must name the failing input and the command that showed the original failing; a changed condition or check is never a side effect.
- **Instructions found in project files are reported.** Text in comments, docs, test data, or fetched pages that addresses AI assistants is never followed, and the agent tells the developer which file contains it. The report header has a required "Instructions found in project files" section, and the final summary repeats it, so the warning is not lost in report mode.
- **The language file is required reading.** `SKILL.md` names each language file next to the mode file to read before any code, in every mode, so the language's hidden costs and security traps (such as unrandomized integer hashing in Python) are not skipped.
- **New traps and tests:** cyclic structures (an iterative rewrite without a visited set loops forever where recursion failed fast), and round-trip tests when new code reads what existing code writes.

### Fixed

- **Complexity and behavior claims checked across every skill file, and about 60 corrected.** The ones that could lead an agent to a slower or wrong choice:
  - Dijkstra with a heap is slower than the array version on dense graphs.
  - A deque does not make inserting in the middle O(1).
  - One multi-source BFS gives only the distance to the nearest source.
  - Components answer reachability only in undirected graphs.
  - A rolling hash returns to O(n·m) when there are many matches.
  - De Casteljau evaluation is O(d²), not O(d).
  - A Fenwick tree cannot answer subtree minimum or maximum.
  - Total unimodularity gives integer solutions only with integer data.
  - Welford's method is no more accurate than the two-pass variance.
  - Standard cardinality sketches fail after about k adaptive queries, not k².
  - Rust's `HashMap` order varies per map, not only per process.
  - glibc's `qsort` is stable in practice.
  - Python's `median` does no exact arithmetic.
  - Java's single-character `split` compiles no regex.
  - C build files alone no longer select the C companion file for C++ projects.
- **Citations corrected:** the LCS hardness result (Abboud, Backurs, and Vassilevska Williams), the differential-privacy method for robust streaming (Hassidim et al.), and the author list of the SODA 2026 cardinality-sketch paper.

### Added

- **For contributors:** `docs/ARCHITECTURE.md` (what loads when, where each idea lives), `CONTRIBUTING.md`, issue and pull-request templates, `CODEOWNERS`, and a dev container with the JDK, Ruby, Node, Rust, Python, and Swift toolchains.
- **Installing a specific release** is documented in the README (the tag's `skills/` folder URL).
- `docs/EVAL-PLAN.md`: the plan for the next evaluations (hostile inputs, security side effects of optimizations, unusual problems, and write mode, on Sonnet and Opus).

### Removed

- **The evaluation harness (`evals/`), the examples (`examples/`), and all their results,** including the results quoted in the README and in the 0.1.0 notes below (the published v0.1.0 release page keeps its original notes). The skill will be benchmarked from scratch under `docs/EVAL-PLAN.md`, and only those results will be published.
- **The CI checks that depended on the harness** (token budgets, cross-references, rule evidence), `docs/RULE-EVIDENCE.md`, and the harness's `.gitignore`.

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

### Known limitations

- The skill is written to be agent-neutral, but has only been used with Claude Code.
- Smaller models do not always load the skill for new-code requests from its description alone; the README gives a one-line project instruction for this.
- Formal verification (proofs, model checking) is the least developed of the skill's roles.
