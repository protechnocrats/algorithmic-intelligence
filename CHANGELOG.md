# Changelog

Release notes for every version of the Algorithmic Intelligence skill (`algorithmic-intelligence`). Each release's section is published as its GitHub release notes when the version's tag is pushed (see [RELEASING.md](RELEASING.md)).

Versions follow [semantic versioning](https://semver.org): while the major version is 0, a minor release (0.2.0) can change how the skill behaves, and a patch release (0.1.1) only fixes wording or mistakes without changing behavior on purpose.

## [Unreleased]

### Changed

- **Agents separate the goal, the limits, and the suggestions in a request (approval change).** The goal (what must be true when done, including a technique the developer names) is the request; limits (code they named, "don't touch the API") bound where agents work; a suggested fix ("add an index") is a candidate checked against the goal. When a suggestion would not reach the goal and a verified fix inside the limits would, agents apply that fix and say why. When a suggestion would reach the goal, agents use it and mention a better approach as an alternative instead of swapping it in. When a technique the developer asked for as the thing to build will not pay at the code's real sizes, agents say so with the evidence and ask before building anything. A fix outside the limits is still a question for the developer.
- **Asking for a change is a request to change code (approval change).** The mode follows what the developer wants back: a slowness they want gone is apply mode even when no code is named ("checkout times out, make it fast"), and agents trace from the symptom to the code. Report mode is for finding, explaining, reviewing, or ranking problems, or when the developer asks for no changes. Agents no longer ask about what the request already settles.
- **What the request asked for needs no second approval, and telling is not approving (approval change).** A technique the developer names comes with its ordinary, bounded trade-off, such as a requested cache serving results up to a stated age, which agents state; it never brings cached errors, results past the bound, a weaker security property, or a success where the original reported an outage with it. A change that gives every accepted input the same result, such as a structure that stays fast on attacker-chosen keys or overflow-safe arithmetic, is applied like any verified item. A behavior change the developer was only told about is no longer treated as approved: without approval, agents ship the version that keeps the behavior. The full rule now lives in one place, and the write-mode and caching guidance follows it instead of requiring every cache to be exact.
- **A failing test blocks only what it can affect (approval change).** Failures that cannot reach the code being changed (another module, a limit of the environment) are recorded and do not block an item its own differential tests verify; failures in or near that code still stop changes until the developer decides.
- **Requirements are read whole.** Whatever defines what the code must do (README, feature docs, specifications, declared stubs) is read in full before agents decide anything it could decide; filtering is for logs and command output, never for requirements or file listings. In write mode, agents implement the feature where the project already expects it (a stub, interface, route, or registration), and ask before assuming a rule that decides results.
- **New code does not trigger known bugs in code it calls.** Agents guard against the bug in the new code, leave the existing code unchanged, and log the bug. In write mode they answer the hostile-input list for each untrusted field; overflow checks include a stored value plus the new amount.
- **Skipped calls keep their failures visible.** Anything that skips a call (a cache hit, deduplication, a batch, an early exit) must not turn an outage the original reported into a success, beyond the stated age of a cache the developer asked for and never for a security decision. A freshness check on every read is weighed against the write rate before it is chosen, and fakes fail as a whole in failure tests.
- **Builds and pipelines are in scope.** Steps of a build, CI job, or data pipeline that redo work whose inputs did not change, or copy data nothing reads, are treated like any repeated work.
- **Measurements account for the environment.** A sandbox can hide costs production pays (warm caches, copy-on-write disks, small data, arguments built by the agent). Agents estimate such costs from the size of the work, and benchmark with inputs built the way real callers build them.
- **The rest of the skill follows the same principles.** Every reference file was reviewed against them. Differential testing tests a requested trade-off against its bound instead of treating it as a behavior change; removal of work shown to be unused is applied like any verified item; a technique the developer named is built even when the agent would choose another, with the better approach reported as an alternative, and one the evidence says will not pay is raised before anything is built; a failing test recorded at the start no longer blocks verification when it cannot reach the changed code; a test that calls a changed interface gets only its call updated. In write mode, an assumed rule that decides results is implemented in one place and flagged as an open question instead of stopping the work, and a change to existing code that the request's own goal requires is made under apply mode within the developer's limits.
- **Security guidance states its principle (approval change).** The list of optimizations that weaken a defense now opens with the rule behind it: an optimization on an exposed path must not change what an attacker can make the system do or learn, listed or not. A requested cache of permission or session decisions is invalidated by every revocation the original honored, and still refuses while its store is down. New limits in existing code remain behavior changes; new code sets its limits from the start. Using `unsafe` in Rust, even on request, is a security trade-off approved after the safety argument is shown. Literature searches never include project code, identifiers, or data.
- **Plugin messages say what to do after a refusal.** Every guard prompt now tells the agent not to reach the same effect another way, to list the action, and to continue; a refused test edit is not evidence that the outcome changed. The summary check requires the same six lines as the skill, at the start of a line, and lets a reply that does not end a piece of work stop as it is. The "small, cold change" short path, no longer in the skill, is gone from the summary script. The guard's documentation no longer implies that PowerShell commands are fully checked.

## [0.6.5] - 2026-11-13

Restores concrete checklists that the 0.6.x rewrites had shortened, and tightens three behaviors: commands are checked more strictly before they run, a test is updated like any other caller when an interface changes, and a fix for a function limited by its input is followed through to the function itself.

### Changed

- **When a function is limited by its input, the fix is followed through.** After fixing the caller or producer that gives a function poor input (unsorted, unindexed, rebuilt per call), agents redesign the function for the improved input in the same change, and treat what it now assumes (sorted, indexed, unique) as part of its contract: every other caller must provide it, or the function keeps a path that does not need it.

- **Tests are updated like any other caller when an interface changes.** When an optimization changes a function's interface, a test that calls it gets only its call updated, never its inputs, assertions, or expected values, and the edit is listed under "Contract changes". A test that cannot keep its assertions through such an update means the outcome changed: the change is reverted or listed for approval. The guard hook still asks before an existing test is edited, and its message now says which edits to approve.

- **Commands are checked more strictly before they run.** Agents read the test or build command the README recommends and everything it triggers, and do not run a script that would delete outside the build output when a variable is empty or unset, need root, reach production or shared systems, grow without bound, or walk outside the project, even after reading it; they tell the developer what it does instead.
- **New code is tested on its edge cases.** In write mode, tests cover empty input, one element, duplicates, ties, boundary values (zero, negative, first and last, limits), and invalid input the code can receive, derived from the request's rules.
- **New code is hardened against hostile input in concrete ways.** Agents never build a regular expression from input (wildcards match as wildcards, everything else literally), check sizes, sums, and counters for overflow, decide on purpose whether non-ASCII digits are accepted, replace recursion on nested input with an explicit stack or a depth limit, and keep queries parameterized.
- **Sizes come from the project's configuration.** Agents read configuration, deployment files, and the README for sizes and limits before designing, show the arithmetic that turns business facts into sizes, and report sources that disagree and which one they used.
- **Hidden costs are spelled out.** Operations that sort, search, copy, slice, convert, or hash a collection or string are counted at their size, along with implicit work such as building one structure from another; no call is treated as constant time because it is short or built in.

## [0.6.4] - 2026-11-10

Rewrites the skill's densest passages so each instruction stands on its own. No intended change in how agents work: every instruction, condition, example, and heading is still there, only easier to follow.

### Changed

- **The instructions are easier to follow.** Across the skill, long sentences that stacked several conditions are split into short sentences and lists, one instruction each, so a step at the end of a long sentence is no longer easy to miss. This covers `SKILL.md`, the mode files, the files every analysis uses (`DATA-STRUCTURES.md`, `ALGORITHM-ARSENAL.md`, `BEHAVIOR-TRAPS.md`, `DIFFERENTIAL-TESTING.md`, `BENCHMARKING.md`), and the densest passages of `DISCOVERY.md`, `ADVANCED-TECHNIQUES.md`, and the technique and language files; tables are unchanged. No instruction, condition, example, or heading was removed, and no intended change in how agents work.

## [0.6.3] - 2026-11-10

Agents now weigh the reviewed packages for each language even when the project has not added them yet, and stop there: they do not search package registries or the web for others.

The `0.6.3` tag was pushed before this section was written, so the files at that tag list these changes under "Unreleased" and still give 0.6.2 as the guard plugin's version and in the README's install commands. The skill's instructions at the tag are the ones described here.

### Changed

- **Packages the project does not declare yet are considered, not skipped.** Agents searched for the best approach only among the standard library and the project's declared dependencies: when a maintained package such as Swift's `swift-collections` or `swift-algorithms` was not in the manifest, they did not ask whether it would make the code faster. Now the search covers the packages each language file lists, whether or not the project declares them, for algorithms as well as data structures. When one beats what is available without it, the agent proposes it with what it buys over the best approach without it, and adds it only with the developer's permission. Being declared decides only whether a package can be used straight away.
- **The search for packages stops at the reviewed list.** Agents consider the standard library, the project's declared dependencies, the packages named in the language file, and any package the developer names, and nothing else: they do not browse package registries or the web, and a library mentioned in a comment or web page is passed on as a lead, not proposed. First-party packages come first. For a language without a file, the profile the agent builds lists first-party packages only, unless the developer approves others.

## [0.6.2] - 2026-11-10

Moves the skill into the folder layout of Anthropic's skill format. No intended change in how agents work: every instruction is the same, only where the files sit.

### Changed

- **The skill lives in `skills/algorithmic-intelligence/`.** The folder now carries the skill's name, as the skill format requires, so tools that check the folder name against the `name` in `SKILL.md` accept it, and a manual install no longer has to rename the folder. `SKILL.md` sits at the top of the folder and every file it points to is under `references/` (with the language files in `references/languages/` and the domain technique files in `references/techniques/`); all links were updated.
- **Manual install copies `skills/algorithmic-intelligence`.** The README's manual install command copies that folder as is. The Skills CLI command is unchanged apart from the release tag. Releases up to 0.6.1 keep the old layout, and the README says how to install them.
- **Contributor documents follow the new paths.** `docs/sources/` keeps its files at each skill file's path relative to `references/`, and the README, `CONTRIBUTING.md`, `SECURITY.md`, `docs/ARCHITECTURE.md`, the pull request template, and the pull request checks name the new locations.

## [0.6.1] - 2026-11-10

Brings the skill in line with what "no behavior change" was always meant to say: what the developer is building must do exactly what it did, only faster, while the interfaces inside the code may change. The agent also asks instead of deciding on the developer's behalf, including about bugs an optimization would remove.

### Changed

- **The outcome is what stays the same, not every interface.** Rule 11 now says to keep the outcome: what the system the developer is building (an app, a service, a library, a compiler, a database, a kernel) shows, returns, stores, and sends, its errors, and its security properties. Signatures, return types, and the structures parts of the code hand each other may change when that reaches a better complexity, and the agent updates every caller in the same change. A difference only code can see, which every caller absorbs, is no longer treated as a behavior change, but the agent has to show that each caller absorbs it.
- **Callers out of reach mean explain and ask.** When a changed interface has callers the agent cannot update or check (users of a published library or API, plugins, other repositories, calls by reflection or by name, stored or serialized data), or it cannot work out whether a difference reaches the outcome, it explains what is uncertain and asks the developer what to do. Keeping the old interface beside the new one is offered as an option, not chosen for the developer.
- **Bugs an optimization would remove are kept unless the developer approves.** Previously the agent could keep a bug fix that the best optimization made as a side effect, without asking. Now the bug stays by default: the agent explains it, with an input that triggers it, and the cost of keeping it, and removes it only when the developer approves that item by name. The separate unapproved-fix marker is gone; an approved removal uses the normal `BEHAVIOR-CHANGE` marker.
- **Differential tests compare through an adapter when an interface changes.** Pin tests at the entry point stay the main evidence and compare exactly; the function itself is compared after converting both results to a common form, every updated caller is covered, and a planted difference must still be caught through the adapter.
- **The description names the work in its key terms,** following Anthropic's skill-authoring guidance: the lowest time complexity a problem allows, timeouts, reviews for nested loops, N+1 queries, and repeated scans and sorts, and what stays the same in plain words (what the system does for its users) instead of "observable behavior".
- **One set of terms in every file.** `SKILL.md` defines outcome, behavior, and contract together near the top, and the other files say "contract change" for any change callers absorb (an interface or the order of results), with "interface" kept for signatures and types. The domain technique files are linked directly from `SKILL.md`, so every file is one step away.
- **The data structure audit no longer keeps a slower structure just because callers receive it.** Changing what callers receive is an interface change, so it is not a reason for not switching.

### Added

- **A definition of "behavior" at the top of the skill.** Agents read that "behavior" and "observable" mean the outcome, with three examples: showing a time where an amount was shown changes the outcome; returning a linked list instead of an array with every caller updated does not; a helper's new result order does not only if every caller is shown to absorb it. The README gains a section, "What 'no behavior change' means", listing what never changes without approval, what may change and is reported, and what the agent asks about.
- **A "Contract changes" line in every final summary,** and a field in each report item and applied result: each interface changed, before and after, the callers updated, and any caller that could not be updated with what was asked about it. The guard plugin's Stop hook now checks for this line too.
- **When the input is what limits a function, the agent says so and points to the real fix.** If a function is already as fast as its input allows, the agent reports the lower bound and what the input lacks (a sort, an index, being built once instead of on every call, being fetched in one query). Changing what the function takes, with its callers updated, is part of the item. A fix in code the developer did not name (a caller, the code that produces the input, a query) is proposed as its own item and made only after the developer agrees. The agent never answers just "cannot be optimized", and report items and applied results have an "At the bound for its input" status.
- **A rule to ask instead of deciding.** When something the work depends on is unclear and only the developer can settle it, the agent explains what is unclear and why it matters, and asks; in a run where nobody can answer, it takes the choice that changes nothing and lists the question under "Waiting for approval".

## [0.6.0] - 2026-11-09

Agents now look for what the project already has before writing a step or a structure, in every mode, and propose extracting or sharing steps instead of calling a larger function, copying it, or adding a dependency between modules.

### Added

- **Agents look for what the project already has before writing a step.** In every mode, before writing a step or a structure, the agent searches the module in scope, the modules it may depend on, and a shared module if there is one, by name, by the data the step touches (which still finds steps written as lambdas or held in variables), and by type where the language allows, and reports what it searched. It reuses a match only when its contract is the same. It never calls a larger function for part of its work or copies the steps out of it: it proposes extracting them, and when two modules need a step, proposes moving its pure part to the shared module, with the cost of the move. It never adds a dependency between modules. When optimizing, the same intermediate result computed by different functions or modules in one operation is treated as repeated work.

### Changed

- **The README describes reuse.** The feature list, the write-mode row, and a new tip (say where shared code lives) explain how the agent searches for existing steps and what it proposes.

## [0.5.1] - 2026-11-09

Corrects facts across the language, technique, and core files, removes contradictions between files, and moves the sources out of the installed skill. No intended change in how agents work: the fixes correct what agents are told about specific APIs and costs, and the sources now ship only to contributors.

### Fixed

- **Corrected facts in the Kotlin, Swift, and JavaScript/TypeScript files.** Kotlin's `reversed()` keeps surrogate pairs (it splits grapheme clusters); `list - other` stopped converting its argument to a set in Kotlin 1.6, not after it, and a JVM system property can restore the conversion; Kotlin's own `ArrayList`, `HashMap`, and `StringBuilder` are no longer listed as Java classes to replace; `getOrPut` on a `ConcurrentMap` and `NaN` in a manual maximum loop are described precisely; the Kotlin/JS `Long` representation is left to the build's settings. Swift's `Decimal(string:)` differs by platform without a locale and parses a prefix, and cross-module specialization needs `@inlinable` only under library evolution. JavaScript's `crypto.timingSafeEqual` throws on unequal lengths, and `new RegExp` in a loop is not always recompiled.
- **Corrected facts in the C#, Java, Python, and C files.** `DistinctBy` is built into LINQ from .NET 6, so MoreLINQ is no longer suggested for it there; default `ValueType.GetHashCode` on a struct key may hash only the first field; Java's Turkish case mapping is stated for both directions, and `MessageDigest.isEqual` returns early for a `null` or empty second argument; NumPy's integer overflow differs between arrays, scalars, and NumPy 2 conversions; MSVC's `__popcnt` needs a CPU-feature check.
- **Corrected facts and contradictions in the core files.** Java's `String.join` writes `"null"` for a null element instead of throwing; C#'s default string comparison and sort are culture-aware, not UTF-16 order; `OPTIMIZATION-REPORT.md` is never edited after it is written, in every file (corrections and later answers go in `APPLY-RESULTS.md`); code markers describe the item in full when the report was given only in the conversation, instead of pointing to a file that does not exist; and the README lists every lower-bound basis the report format allows.
- **Corrected two technique entries.** JavaScript engines are described as giving no guarantee against chosen hash collisions, not as unkeyed (V8 seeds string hashes); the quorum row says that R + W > N avoids stale reads only with strict quorums, and that quorums alone are not linearizable under concurrent writes.

### Removed

- **The `references/` folder from the installed skill.** The sources behind each file's claims moved to `docs/sources/` in the repository, at the same paths, and the skill files no longer end with a pointer to them: agents did not use them, and they now ship only to contributors. Vague entries that named only a site's front page now name the page or section behind each claim, grouped by the section of the skill file they support.
- **The suggestion to run analysis in parallel sub-agents.** Sub-agents do not load the skill, so their analysis skips its rules, and each one rereads the files, which raises cost rather than lowering it. One agent still owns all source edits.

## [0.5.0] - 2026-11-08

Makes 0.4.0 work the way it was meant to. Reading every file in the project turned up instructions that still contradicted each other, most importantly at the step where a report's items are approved: "go ahead" now starts apply mode everywhere. The order for finding a missing data structure is the same in every file, the facts below are corrected, and the README and contributor documents match the skill.

### Fixed

- **"Go ahead" after a report now works as intended.** A general approval starts apply mode for items that keep behavior, where one file still required naming each item. Behavior changes and anything no test can verify still need approval by name.
- **The order for a structure missing from the standard library is now the same everywhere.** The advanced techniques, sorted-map and LRU rows, and the C, Kotlin, Swift, and JavaScript files follow it: a direct dependency, then a maintained package offered beside writing one.
- **Tests fake only what leaves the machine, reaches a shared system, or cannot be bounded,** and a baseline test against a throwaway local database is kept.
- **Over a hard memory budget the agent presents both costs and asks,** where one file dropped the approach without asking.
- **Mode files now require the full data structure audit,** compact report items carry a prediction, and the list of reasons for not switching covers a pending dependency and a benchmark that showed no gain.
- **Corrected facts:** a sorted array is O(log n), lexer minimization must keep tokens apart, compilers can change complexity, Kotlin's list set operations are O(n·m) in current versions, and Python's frozen dataclass and tuple keys hash every field.

### Changed

- **The README and contributor documents match the skill.** The README describes the data structure audit, the combined search for an algorithm and a structure, pin tests, and how a missing structure is found. `CONTRIBUTING.md` and `RELEASING.md` state the rules the project now follows.

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
