# Changelog

Release notes for every version of the Algorithmic Intelligence skill (`algorithmic-intelligence`). Each release's section is published as its GitHub release notes when the version's tag is pushed (see [RELEASING.md](RELEASING.md)).

Versions follow [semantic versioning](https://semver.org): while the major version is 0, a minor release (0.2.0) can change how the skill behaves, and a patch release (0.1.1) only fixes wording or mistakes without changing behavior on purpose.

## [Unreleased]

## [0.2.0] - 2026-11-03

Agents follow the skill more reliably and load less of it. `SKILL.md` is half as long, and each mode reads only its own files. In every mode, the agent now reads the language file for the code it works on, and sizes the work from the project's configuration. It reports instructions planted in project files. It also catches more of what breaks optimizations: caches that serve stale data across processes, callers that change a returned value, and code that nothing runs. Install or update with `npx skills add https://github.com/protechnocrats/algorithmic-intelligence --skill algorithmic-intelligence`.

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
- **The language file is required reading.** In every mode, `SKILL.md` names the language files next to the mode file, to be read before any code: one for each language in the code being read or written, `GENERIC.md` for a language without one, and a language met partway through is loaded before its code is read. The language's hidden costs and security traps (such as unrandomized integer hashing in Python) are no longer skipped.
- **`SKILL.md` is about half as long** (about 2,900 words, from 5,600), so every session loads less. Each mandatory rule is stated in a few sentences there, and its full text moved to a new "Rule details" section in `WORKFLOW.md`, which report and apply mode already read. The workflow overview and anti-pattern list, which repeated `WORKFLOW.md` and the rules, were removed; their examples moved into the rules. Rule numbers are unchanged.
- **Report mode loads less.** Applying and close-out (Phases 5 and 6) moved from `WORKFLOW.md` to a new `APPLYING.md`, which only apply mode reads, in the same step as `WORKFLOW.md`. Text in "Rule details" that repeated those phases or `DIFFERENTIAL-TESTING.md` was removed.
- **Report mode reads the report format.** `SKILL.md` names `REPORTING.md` for report mode, to be read with `WORKFLOW.md`, so the required report header (including instructions found in project files) is not skipped. The apply results format and the `NEEDS-TESTING` and `BEHAVIOR-CHANGE` markers moved to `APPLYING.md`, so report mode does not load them.
- **Code that nothing reaches is not optimized.** The agent follows callers, including indirect ones (dependency injection, routing, listeners, plugins, reflection), up to an entry point. Evidence that the code runs (a profile or log, the developer saying it runs or is slow, documentation or deployment configuration saying what uses it or when it runs) also counts. When the chain reaches none, or only tests, the code is not optimized, since speeding it up saves nothing: it is listed in the report under "No entry point found" as likely unused, never deleted, bugs noticed in it are still logged, and the developer is asked where it is used. Before, it stayed a ranked item with unknown reachability.
- **Every file loads less.** The source lists at the end of each file moved to `references/`, which the agent reads only to verify a claim. The machine-learning, image, geometry, and simulation traps moved from `BEHAVIOR-TRAPS.md` to a "Behavior traps" section in the matching `techniques/` file, which `BEHAVIOR-TRAPS.md` names for code in those domains. All files were reworded to be shorter, with no rule, step, fact, or example removed.
- **Caches see writes from other processes.** A new trap, "Writers outside this process": when other processes, machines, or jobs share the data, a cache inside one process must detect their writes on every read (a version number or change counter the data source keeps) or cache only data they never change. In write mode the agent decides this before writing: it writes the version that keeps exact results and offers the faster, possibly stale version as an option, instead of shipping it and asking afterwards.
- **Fewer wasted steps.** The agent runs tests the way the project documents them instead of guessing a runner, and gives commands that can hang a time limit.
- **Conflicting size sources are reported.** When the README, configuration, code, or tests give different input sizes, the agent lists each source and number, says which one it used and why, and asks the developer to confirm when the choice changes a ranking or a design. The report header has a required "Input sizes" section that lists each size, its source, and every disagreement between sources.
- **Complexity is reported in every size variable, with the lower bound.** Apply results, the final summary, and write mode's performance decisions give each item's complexity before and after in every size variable (O(n·k) → O(n), not only O(n²) → O(n)) and the lower bound with its reason, or "unknown" with why.
- **Sizes come from the project's configuration first.** Before estimating sizes, in every mode and even for one named function, the agent reads the configuration and deployment files and the README for production sizes. Apply results open with the sizes used and their sources.
- **Callers' use of a result is part of the contract.** For each caller, the agent reads what it does after the call (changes, appends to, keeps, or encodes the result, or changes the arguments it passed) and names those callers, so a rewrite that returns shared memory or a different empty value is caught.
- **Measured numbers are checked against the output.** A number labeled measured must appear in a command's output from the session, or be computed from it with the arithmetic shown; projections are estimated even next to measured numbers. The agent checks every measured number before finishing.
- **Every cache or index gets a memory estimate:** its bound, its size in bytes across every copy that can exist at once, and the memory limit from the project's configuration it was compared with.
- **Shared state is tested under concurrent callers.** When new code adds a cache, memo table, index, or counter that several threads, goroutines, or workers can reach, the agent tests it concurrently, with the race detector or thread sanitizer where one exists.
- **Caching checks what callers do with the result.** Before caching, write mode reads each caller after the call; if any changes or keeps the returned value, the cache hands out copies or caches only the inputs.
- **Bugs are recorded in any code the agent reads,** not only in the function it optimizes: other functions in the same file, callers, and helpers.
- **The skill loads for more new-code requests:** code that walks trees, graphs, or parent/child links, or that handles input from users or public APIs, even when the request does not mention speed.
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
