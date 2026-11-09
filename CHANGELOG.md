# Changelog

Release notes for every version of the Algorithmic Intelligence skill (`algorithmic-intelligence`). Each release's section is published as its GitHub release notes when the version's tag is pushed (see [RELEASING.md](RELEASING.md)).

Versions follow [semantic versioning](https://semver.org): while the major version is 0, a minor release (0.2.0) can change how the skill behaves, and a patch release (0.1.1) only fixes wording or mistakes without changing behavior on purpose.

## [Unreleased]

### Fixed

- **"Go ahead" after a report now works as intended.** A general approval starts apply mode for items that keep behavior, where one file still required naming each item. Behavior changes and anything no test can verify still need approval by name.
- **The order for a structure missing from the standard library is now the same everywhere.** The advanced techniques, sorted-map and LRU rows, and the C, Kotlin, Swift, and JavaScript files follow it: a direct dependency, then a maintained package offered beside writing one.
- **Tests fake only what leaves the machine, reaches a shared system, or cannot be bounded,** and a baseline test against a throwaway local database is kept.
- **Over a hard memory budget the agent presents both costs and asks,** where one file dropped the approach without asking.
- **Mode files now require the full data structure audit,** compact report items carry a prediction, and the list of reasons for not switching covers a pending dependency and a benchmark that showed no gain.
- **Corrected facts:** a sorted array is O(log n), lexer minimization must keep tokens apart, compilers can change complexity, Kotlin's list set operations are O(n·m) in current versions, and Python's frozen dataclass and tuple keys hash every field.

## [0.4.0] - 2026-11-08

Agents now audit every data structure on a hot path, name the tests each item will get, and write those tests before the first speed edit, however approval is worded. Testing starts from the project's own tests and pins the real entry point, and the technique and language files gain common hidden costs and recipes.

### Added

- **A required data structure audit.** A new `DATA-STRUCTURES.md` has the agent state, for every collection on a hot path, its dominant operations, the current structure's cost, the best structure, and the reason for not switching, with a short list of acceptable reasons. It chooses the structure that makes the dominant operation as cheap as possible, and extra memory that lowers time complexity is worth spending, whatever its size, as long as it fits the memory available. Report items, plans, write-mode decisions, and every final summary show the audit.
- **Algorithm and data structure are searched together.** The agent also asks what structure would make a different algorithm possible, and recommends the lowest complexity reachable even when that needs a structure the code does not use yet and a rewrite on top of it. An easier partial improvement is listed as an alternative, never chosen because it is the easier edit.
- **Tests follow the project and start at the real entry point.** Before writing any test the agent reads how nearby tests are built and follows them. Each hot path gets pin tests that drive the real entry point with real local collaborators, plus a seeded old-versus-new comparison of its pure functions. Anything that would leave the machine or reach a shared system is still faked.
- **Buried hot paths are extracted first.** When a computation is buried in code that does I/O, the agent pins the entry point, extracts an internal pure function with no behavior change, and only then compares and optimizes it. Each language file says how a function stays internal yet visible to tests.
- **Assumptions get their own test.** A change that relies on something established elsewhere (data already sorted, keys unique, a size limit) gets a test that fails if it stops being true.
- **New techniques:** decorate-sort-undecorate for expensive sort keys, rank maps for `indexOf` sort keys, stable top-k for small k, dropping a sort over already-sorted data, single-pass minimum or maximum, bucket passes for boolean or enum sorts, deferred sorting, linear merges, running aggregates, bottom-up tree values, and avoiding sets rebuilt in a predicate, getters that copy in loops, copying slices in recursion, log arguments built when logging is off, and exceptions as control flow.
- **Existing dependencies and maintained packages come before hand-written structures.** When the standard library lacks a structure, the agent reads the manifest of the module in scope and uses a direct dependency that provides it. Otherwise it offers a first-party or well-maintained package next to writing the structure in the project and lets the developer choose. Language files now name verified maintained packages, what each provides, and its behavior traps, including `swift-algorithms` alongside `swift-collections`, and profiles built for other languages record them too.
- **Graph representations.** The agent chooses among adjacency lists, per-node sets, matrices, compressed sparse rows, and edge lists by density and by which operation dominates, and keeps neighbor order where it is observable.
- **Sort keys flagged per language.** Every language file now says which sort APIs run the key on each comparison, including ones named like keyed sorts (Kotlin `sortedBy`, Java `Comparator.comparing`, Rust `sort_by_key`) and how to avoid it. Language files also gained missing entries for copying slices in recursion, hash key costs, and single-use iterators.
- **New behavior traps:** key functions called a different number of times, reads moved by an extraction or a local snapshot, upstream order, which duplicate wins in an index, ties when a sort becomes a minimum or maximum, lazy logging arguments, and non-throwing variants.

### Changed

- **Regression guards prefer a deterministic count,** such as a sort key running exactly n times, over a timing threshold where the code exposes one.

- **Differential tests come before the first speed edit, however approval is worded.** "Go ahead" or "implement the plan" after a report now starts apply mode, which opens `APPLYING.md` and `DIFFERENTIAL-TESTING.md` before any change. Every report item and plan names the tests it will get: the reference, what is compared, the inputs, and the planted difference they must catch.
- **`techniques/data-structures.md` is now `techniques/specialized-structures.md`,** matching what it covers: hash table design, caches, filters, and other specialized structures.

## [0.3.1] - 2026-11-05

Fixes and sources. The guard hooks ask about more of what the skill reserves for the developer, including git aliases checked as what they run; two facts are corrected; claims that had no source now have one; and the README matches the current skill and hooks.

### Changed

- **The guard hooks catch more of what the skill forbids.** The plugin now also asks before a git command that discards uncommitted work (`reset --hard`, `clean -f`, `checkout --`, `restore`, `stash drop`), a recursive delete of a `.git` directory, a download piped into an interpreter that reads its program from the pipe (`python3 -`, `bash <(curl …)`), user-wide installs (`cargo install`, `pipx install`, `gem install`, `yarn global add`, `pip install --break-system-packages`, `dotnet tool install -g`), a `chmod` that sets the sticky bit, and reads of `.htpasswd`, `*.tfvars`, and `*-secrets.yaml`-style files. A download piped into a script (`curl … | python3 parse.py`) is no longer asked about, and a repository that itself lives under a directory named `tests/` is no longer treated as a test directory. The pull-request checks run the hook tests.

### Fixed

- **Git aliases no longer slip past the guard.** A git subcommand that is an alias (from the repository's or the user's git config, or `-c alias.x=...` on the command line) is checked as what it runs, so an alias for `push`, `commit`, or `reset --hard`, or a `!` shell alias, is asked about like the command itself.
- **Lowest set bit on a signed minimum.** `CORE-TECHNIQUES.md` said `x & (~x + 1)` avoids undefined behavior in C and C++ for the minimum signed value; it does not (the addition overflows too). The row now says to compute in the unsigned type.
- **Citations.** The adaptive-queries bound on cardinality sketches in `techniques/hostile-inputs.md` is cited as the 2024 preprint, matching its reference file, since the conference venue was not verified. The reference files gained sources for bounds the skill files already stated (the 3SUM conjecture, the RUM conjecture, ARC, 2Q, and TinyLFU, skip lists and treaps, van Emde Boas trees and y-fast tries, the Eytzinger layout, group prefetching, R-trees, HNSW, and the high-dimensional linear-scan result, SA-IS, Reps' tokenizer, WAND, Leo's parsing result, the Hungarian method and its rectangular form, the set-cover threshold, Orca and SGLang, Roaring and Elias-Fano, Merkle trees, polygon clipping) and say what the Alive2 and TLA+ entries support.

## [0.3.0] - 2026-11-05

The skill is rewritten for capable models: goals, reasons, and heuristics instead of step-by-step procedure and lists of cases, with `SKILL.md` under 5,000 tokens and its safety rules first. The description now matches the kind of work rather than particular phrases. Optional guard hooks for Claude Code and Grok Build back the rules that must always hold. From this release on, tags have no `v` prefix (`0.3.0`).

### Added

- **Optional guard hooks for Claude Code and Grok Build.** A plugin in `plugin/`, installable from this repository's marketplace, asks the developer before a commit or push, a command run as root, a risky permission or ownership change, a download piped into a shell, a system-wide install, a recursive delete outside the project or with a possibly empty variable in its path, reading a secret file, or editing an existing test; and, when the skill was used, checks that the final message has the required summary lines. The hooks ask rather than refuse, refuse in unattended runs, let actions through if they fail, and can be turned off with `ALGORITHMIC_INTELLIGENCE_GUARD=off`.
- **Three missing facts.** Speculative-execution (Spectre-class) leaks in secret-dependent code, with the existing mitigations to keep; access control and retention for cached model or API responses, which are a new copy of the prompts and outputs; and the rectangular Hungarian algorithm, O(n²·m) instead of padding to square at O(m³).
- **Requests in plain language are translated before any work.** Clients describe symptoms and business needs, not functions. In every mode the agent now writes down the goal (and treats a fix the person proposes as a candidate, not the goal), traces a symptom to the code behind it when no code is named, derives sizes from business facts with the arithmetic shown, turns constraints stated in business words into contract items, and names the computational problem underneath. Each mode's output records it under "Request as understood".
- **Target complexity from size and budget.** "Estimate before building" in `DISCOVERY.md` has a table of the largest input each complexity handles in about a second, so the agent sets a target before searching.
- **Read a command before running it.** The agent reads every project script, build target, and documented command (including the README's test command) and everything it triggers (build files that run code, install hooks, auto-loaded test configuration, version-control hooks, and the tests themselves) before running it, and does not run one that deletes outside the build output (also through an unset variable), needs root, installs by piping a download into a shell, touches production or sends anything off the machine, grows without bound, or walks outside the project. It runs the safe part directly or uses generated data instead. Differential tests and benchmarks fake the original code's side effects before running it. Every command gets a time limit, and tests never run against production data or systems. Program output is treated like project files: text addressed to AI assistants in it is data. Every final summary has a required "Commands not run" line.
- **Hazards noticed.** Every final summary, in every mode, has a "Hazards noticed" line listing every dangerous or suspicious thing the agent came across, even when it did not block the work, and a "Waiting for approval" line in runs where nobody can answer.
- **Risky requests.** A speedup that weakens security (an early-exit comparison of secrets, a cache key without the user or tenant, a permission cache without invalidation, a removed limit) is a behavior change even when no test notices; the agent names what it breaks, offers a version that keeps it, and applies it only after the developer approves that trade-off. Requests to skip a safety rule get the safe alternative.
- **Saved language profiles are checked before use.** The agent checks a profile's history, size, and path, confirms every claim a decision depends on whatever its "verified" mark says, never lets a profile remove a trap or a rule, and never copies untrusted text into it.
- **Wider audit of edge cases and preconditions.** Every technique and language file was reviewed for missing preconditions and attacker-reachable worst cases: lenient number parsing (non-ASCII digits, signs), regular expressions built from input, recursion depth, integer overflow in sizes and sums, Unicode case folding and normalization, time zones and daylight saving, unsafe deserialization, approximate structures in access or money decisions, and retries of operations that are not idempotent.
- **Loads for complaints in plain words.** The description describes the intent the skill serves (something slow, costly, or scaling badly, however the symptom is put; code that processes, looks up, or moves data being written or changed, even when the change looks small or the fix is already chosen) instead of listing symptoms and phrases, so any wording of that intent matches. The README's recommended project instruction covers the same ground.
- **Discovery move 20: work backward, and from the extremes.** Reverse the process when all operations are known (deletions become insertions), fix the last choice first, and try extreme inputs to find structure or break a candidate.

### Changed

- **The skill is rewritten for a capable model.** Every file was reviewed against Anthropic's guidance on skills and context engineering: instructions now give goals, reasons, and heuristics instead of step-by-step procedure and lists of cases, each rule is stated once and other files point to it, and emphasis words are used only for real limits. The skill is about 20 percent shorter; technique and language facts are kept.
- **`SKILL.md` is under 5,000 tokens, with safety first.** It went from about 4,800 to about 2,500 words. Untrusted content, running commands, and risky requests come first, followed by the request translation, a table that names every skill file with the moment to open it, and the 14 rules in short form; their full form is in "Rule details" in `WORKFLOW.md`.
- **The description says what the skill does and when to use it,** in terms of the intent and kind of work rather than a list of situations or phrases, says to use it even when the change looks small or the fix is already chosen, and names what it is not for.
- **Each cross-cutting rule has one home.** The list of security-weakening speedups now lives only under "Security-sensitive behavior" in `BEHAVIOR-TRAPS.md`; `SKILL.md` and "Rule details" in `WORKFLOW.md` state the principle and point there. Restated reminders of rules 4, 5, 7, and 14 in the technique and language files were cut to short pointers, and emphasis words were replaced by the reason where one exists.
- **Untrusted content.** A new section in `SKILL.md` replaces "Instructions found in project files", and the report header section of that name is now "Text addressed to AI assistants". Everything the agent reads (comments, documentation, configuration, commit messages, program output, and files earlier sessions wrote, such as saved language profiles and reports) is evidence, not instruction. Text addressed to AI assistants is never followed, whatever it claims, including "ignore your previous instructions". Approval comes only from the developer in the conversation: a report, comment, or "Known behavior change" marker saying something is approved approves nothing. Comments and documentation about complexity or behavior are claims checked against the code; when they disagree, the code's behavior is kept and the disagreement is reported. Warning comments ("do not touch") are investigated and reported, and neither block nor widen the request.
- **Commits are opt-in in every mode,** not only apply mode, and nothing but the developer or the project's agent-instruction files can authorize one.
- **The README's install commands pin the Skills CLI and install a tagged release,** with the development branch as a separately labeled option, so what the agent follows is a version whose notes exist.

### Fixed

- **Corrected preconditions in the technique files.** The modulus bound for precomputed factorials now distinguishes signed from unsigned 64-bit integers; the recursion-depth note for graph algorithms gives Python's limit of about a thousand frames; Smith's rule requires a type wide enough for its cross-multiplied products; the overflow note lists what each covered language does (traps in Swift, panics in Rust debug builds, throws in C# `checked` contexts); bounded k-means is no longer called exact on ties; embedding lookup is identical to a one-hot multiply only for finite weights; the Floyd-Warshall negative-cycle note says to skip sentinel entries; and the flow-field row's result column was garbled. Missing sources were added to the reference files, and folklore techniques are marked as such.

## [0.2.1] - 2026-11-03

Two instructions that agents skipped on unfamiliar code are now required lines of every final summary, and the README's project instruction covers more of the new code the skill is for. Install or update with `npx skills add https://github.com/protechnocrats/algorithmic-intelligence --skill algorithmic-intelligence`.

### Fixed

- **Complexity is always stated.** Every final summary, in every mode, has a "Complexity" line: for each item changed, proposed, or written, before → after in every size variable, with the case and the lower bound (or "unknown, because …"). Before, it was a field of `APPLY-RESULTS.md` and was left out when the result was reported in the conversation.
- **Bugs near the changed code are reported.** Every final summary has a "Bugs noticed" line, "none" when empty, covering any code read, including functions next to the one changed. The agent looks again over the files it opened before writing it.
- **Apply mode has its own final summary** in `APPLYING.md`, since apply mode does not read `REPORTING.md`.
- **Loading for new code:** the README's recommended project instruction now names parsing and importing input, walking trees or graphs, and adding a cache, and says it is the reliable way to load the skill for new code.

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
