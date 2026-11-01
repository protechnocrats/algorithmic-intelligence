# Algorithmic Intelligence

### Algorithmic Reasoning and Performance Engineering for AI Coding Agents

**Make AI agents think beyond code generation.**

Algorithmic Intelligence is an agent-independent reasoning and performance engineering skill, installed as `complexity-optimizer`, that helps AI coding agents understand computational problems, discover better algorithms, select efficient data structures, analyze complexity, and engineer solutions that scale. In existing code it never changes behavior without your explicit approval: every change is backed by differential tests that run the original and the optimized code on the same inputs and compare the results, and anything that would behave differently is listed for your decision first. In new code it chooses efficient algorithms and data structures from the first version.

It brings systematic algorithmic thinking and performance engineering discipline into AI-assisted software development.

Rather than simply asking an agent to optimize code, Algorithmic Intelligence guides it to question the problem, challenge its assumptions, explore alternative approaches, establish what is achievable, and engineer a solution backed by correctness and performance evidence.

The result is a different approach to building software: one where computational efficiency is considered from the beginning, not treated as an afterthought.

## The Core Idea

An AI coding agent should not stop at finding a solution that works.

It should understand the problem well enough to find a better solution.

Algorithmic Intelligence provides a systematic reasoning framework that guides agents through the complete engineering process:

1. **Understand the problem** — Establish the computational problem, behavioral requirements, constraints, and workload.
2. **Analyze the solution** — Examine existing algorithms, data structures, complexity, and resource consumption.
3. **Explore alternatives** — Evaluate different approaches, establish theoretical lower bounds (or state why none can be established), and discover better algorithms.
4. **Engineer the solution** — Select appropriate algorithms and data structures while considering real-world system constraints.
5. **Verify correctness** — Preserve observable behavior through testing, differential testing, and explicit verification.
6. **Measure performance** — Benchmark meaningful workloads and distinguish theoretical improvements from measured results.

This is not simply about making existing code faster.

It is about improving the reasoning that produces software in the first place.

## Core Capabilities

### 1. Algorithmic Reasoning and Discovery

Move beyond recognizing familiar optimization patterns.

Guide agents to understand the underlying computational problem and reason about the best achievable solution.

Capabilities include:

- Time and space complexity analysis.
- Identifying exponential, factorial, polynomial, and linear-time opportunities.
- Establishing theoretical lower bounds, or stating why none can be established; a bound is never invented.
- Comparing multiple algorithmic approaches.
- Combining techniques such as hash maps, prefix sums, binary search, dynamic programming, and graph algorithms.
- Identifying when an existing representation or algorithm prevents better performance.
- Deriving new approaches when conventional techniques are insufficient.
- Evaluating algorithmic assumptions rather than applying patterns blindly.

The objective is not merely to find an improvement. It is to identify the best achievable approach and explain why.

### 2. Intelligent Data Structure Selection

Choosing the right data structure can fundamentally change the performance characteristics of a system.

Evaluate:

- Arrays, lists, hash maps, sets, trees, heaps, and specialized structures.
- Lookup, insertion, deletion, traversal, and update costs.
- Amortized versus worst-case performance.
- Memory overhead and allocation behavior.
- Cache locality and garbage collection implications.
- Language-specific standard library implementations.
- Whether introducing a new data structure or dependency is justified.

Data structures should be selected based on computational requirements, not familiarity or convenience alone.

### 3. Performance Engineering Beyond Big-O

Big-O is essential, but it does not tell the entire performance story.

Investigate actual system bottlenecks across multiple dimensions:

- CPU-bound computations.
- Memory allocation and memory pressure.
- Database queries and N+1 problems.
- Repeated network and service calls.
- I/O operations and unnecessary serialization.
- Main-thread blocking.
- Lock contention and concurrency.
- Queues, latency, and distributed system behavior.
- Workload characteristics and invocation frequency.
- Exposure: untrusted input, secrets, and hard deadlines, where the worst case decides. Counting n keys in a hash map is O(n) on average but O(n²) when an attacker chooses colliding keys, so worst-case-safe structures are chosen there.

The goal is to understand not just the theoretical cost of an algorithm, but the actual cost of executing it in a real system.

### 4. Correctness-Preserving Engineering

Performance improvements should not silently change application behavior.

For existing code, establish a behavioral contract before making changes.

Use differential testing to compare original and optimized implementations against the same inputs, checking observable behavior such as:

- Return values.
- Input mutations.
- Exceptions.
- Side effects.
- Ordering and stability.
- Other externally observable behavior.

Verification is reported using explicit levels:

- Tested.
- Property-checked.
- Exhaustively checked to a stated bound.
- Proven.

Passing tests are evidence, not proof.

Unverified equivalence and known behavior changes require explicit developer approval.

### 5. Measurement-Driven Performance

A theoretically superior algorithm is not automatically a faster implementation for every workload.

Guide agents to:

- Identify actual hotspots through profiling when possible.
- Estimate realistic input sizes and execution frequency.
- Predict expected speedups before benchmarking.
- Measure execution time and memory consumption.
- Compare performance at realistic and larger input sizes.
- Investigate discrepancies between predictions and measurements.
- Distinguish measured results from theoretical estimates.
- Avoid optimizing code that is already sufficiently efficient for its workload.

**Reason about performance. Then measure it.**

### 6. Performance-Aware Code Generation

Algorithmic reasoning should happen before code is written, not only after performance problems appear.

When implementing new code, guide agents to:

- Select appropriate algorithms and data structures from the beginning.
- Consider expected input sizes and invocation frequency.
- Avoid unnecessary repeated computation.
- Minimize calls into expensive existing code.
- Account for the complexity of the surrounding system.
- Test new implementations against simple, obviously correct reference implementations.
- Explain the performance decisions made during implementation.

The goal is to prevent inefficient implementations from becoming technical debt in the first place.

## Engineering Principles

Algorithmic Intelligence is built around engineering principles that guide every mode.

| Principle | Philosophy |
| --- | --- |
| Algorithmic optimality | Establish lower bounds and always report the best achievable approach; apply a change only when evidence shows it pays off. |
| Time-first optimization | Optimize execution time before space, subject to hard memory constraints. |
| Correctness preservation | Treat observable behavior as a contract. |
| Evidence over intuition | Never claim measured improvements without measurements. |
| Workload awareness | Evaluate performance using realistic input sizes and execution frequency. |
| Explicit assumptions | Validate the assumptions behind every algorithmic technique. |
| Resource awareness | Consider CPU, memory, I/O, network, concurrency, and latency. |
| Controlled changes | Never silently introduce behavior changes or unverified optimizations. |
| Engineering simplicity | Respect the project's idioms; never trade readability for an unmeasured gain, and comment any non-obvious trick. |
| Continuous reasoning | Do not stop at the first improvement when a better solution may exist. |

The objective is not to maximize optimization activity. It is to maximize engineering quality.

Sometimes the best engineering decision is to leave the code alone.

## Agent Independence

Algorithmic Intelligence is not tied to a particular AI model, coding agent, or vendor.

It uses the open Agent Skills convention: a directory containing a `SKILL.md` file and supporting reference documents.

Any coding agent that supports this convention can use it.

It can also be incorporated into project-level agent instructions for agents that read files such as `AGENTS.md` or `CLAUDE.md`.

The intention is to make algorithmic reasoning and performance engineering a reusable capability across the AI coding ecosystem.

## Quick start

```bash
# 1. Install into the project you want to optimize
cd path/to/your-project
npx skills add https://github.com/protechnocrats/complexity-optimizer-skill --skill complexity-optimizer

# 2. Start your coding agent in that project and ask:
#    "find time complexity problems in this project"
```

The agent returns a ranked report and changes nothing until you approve specific items.

## Installation

### Option 1: Skills CLI (recommended)

The [Skills CLI](https://skills.sh) installs the skill into the right place for your agent.

Per project (only active in this project; can be committed so your team gets it too):

```bash
npx skills add https://github.com/protechnocrats/complexity-optimizer-skill \
  --skill complexity-optimizer
```

For your user account (active in every project):

```bash
npx skills add https://github.com/protechnocrats/complexity-optimizer-skill \
  --skill complexity-optimizer \
  --global
```

Run `npx skills --help` to choose a specific agent or run non-interactively. Requires Node.js.

### Option 2: Manual install

Copy the `skills/complexity-optimizer/` folder (the folder that contains `SKILL.md`) into your agent's skills directory:

```bash
git clone https://github.com/protechnocrats/complexity-optimizer-skill.git
cp -r complexity-optimizer-skill/skills/complexity-optimizer <your-agent-skills-dir>/
```

For example, Claude Code reads skills from `.claude/skills/` in a project or `~/.claude/skills/` for your user. For other agents, check their documentation for the skills directory. Keep the folder intact: `SKILL.md` links to the other files by relative path.

### Option 3: Agents without skill support

If your agent does not support skills but reads a project instructions file (such as `AGENTS.md`), copy the folder into your repository and add a line to that file:

```markdown
For performance, time complexity, or data-structure work, follow skills/complexity-optimizer/SKILL.md and the files it links to.
```

### Verify the installation

Ask your agent: "Which skills do you have for optimizing time complexity?" It should name `complexity-optimizer`. Or ask it to "explain the complexity-optimizer rules" and check that it lists the mandatory rules.

### Update

Re-run the install command to fetch the latest version, or `git pull` your clone and copy the folder again.

## How it works

### Three engineering modes

| Mode | Triggered by | What happens |
|---|---|---|
| **Report** | "find performance problems", "review this for complexity", "what can be optimized?" | The agent surveys existing code, analyzes it, and returns a ranked report. **No code changes.** |
| **Apply** | "apply items 1 and 3", "optimize `findDuplicates` in `Util.kt`" | The agent changes only the existing code you named, one optimization at a time, with differential tests and a benchmark for each. |
| **Write** | "add CSV export for orders", "build a rate limiter", "write a function that merges these feeds" | The agent writes the new code you asked for, choosing algorithms and data structures for the expected input sizes, and ends with a short list of its performance decisions. It does not change existing code just for speed; if existing code is the bottleneck, it tells you and asks. |

The agent names the mode it picked in one line at the start, so you can redirect it. If the request is ambiguous, or you invoke the skill with no task, it asks. Approving one item never approves the others.

Write mode works only when the agent loads the skill for the task. Agents load skills by matching the request against the skill's description, which asks to load it before writing new code that loops over collections or data (aggregating, counting, searching, filtering, sorting, ranking, joining, merging, deduplicating, or grouping), code that runs per request, per item, per frame, or per keystroke, database or service calls in loops, and data-structure choices, even when the request does not mention size or speed. For a small, ordinary feature the agent may not load it. To make sure it is used, add this line to the project's agent instructions (`CLAUDE.md`, `AGENTS.md`, or your agent's equivalent):

```
Use the complexity-optimizer skill when writing new code that loops over collections or data, and for any question about the speed or complexity of existing code.
```

This matters most for smaller models. In testing, Haiku 5.5 loaded the skill for 2 of 24 new-code requests from the description alone, and for 22 of 24 with this line, while still skipping trivial requests (0 of 24). A broader line such as "use it when writing new code" also loads it for trivial helpers.

### Workflow

Report and apply mode:

1. **Setup:** detects languages and versions, finds your test, benchmark, profiling, and verification tooling, and runs your existing test suite. If tests already fail, report mode lists them and continues the analysis; apply mode stops before changing any code until you decide. In apply mode it asks once whether to commit each optimization, unless your project's instructions already say.
2. **Survey:** confirms the scope you asked for, profiles the code when it can run, and finds candidate hotspots. For each one it writes the contract, finds who calls it and traces the callers up to a real entry point (a route, job, listener, command, UI handler, or public API, including code reached through dependency injection, plugins, or reflection), multiplies the cost along that call chain, estimates input sizes, classifies the limiting resource (CPU, memory, I/O, network, lock, queue), and checks exposure: untrusted input, secrets, or hard deadlines. Code with no caller found is never assumed dead: its reachability is reported as unknown and you are asked.
3. **Analyze:** first asks whether the work is needed at all, then states the lower bound (or says none can be established, and why) and compares approaches (deriving new ones with a discovery method when no known technique fits) in proportion to difficulty: at least three plausible ones (including combinations such as hash map plus prefix sum) for nontrivial problems, or the strongest one with a short reason for straightforward ones. It checks each technique's assumptions against the code, labels each algorithm established, experimental, or derived, writes a prediction of the speedup and of the end-to-end effect, and plans how strongly the change can be verified.
4. **Report:** starts with the test-suite baseline and the scope (including what was not inspected), lists behavior changes for review first, then ranks items by real-world impact.
5. **Apply** (only on approval): writes differential tests and contract checks against the original first, makes the change, verifies it at the highest cheap level, benchmarks the function against its written prediction and states its share of the end-to-end operation, and commits each optimization separately only if you authorized commits.
6. **Close out:** summarizes what was applied and at which verification level, predictions against measurements, what was tried and rejected, what is marked as needing testing, bugs found, pending dependency requests, items whose reachability is unknown, the commits made or the files each item changed, and regression benchmarks you chose to keep.

Write mode: estimates input sizes and call frequency for each part of the new code, picks or derives algorithms and data structures to match, keeps calls into slow existing code to a minimum, tests the new code against a slow, obviously correct reference version and its contract, and lists its performance decisions with their complexity, size assumptions, and verification level.

## Getting the best results

- **For existing code, start in report mode.** Read the report, then approve items by ID. You stay in control of every change.
- **Start from a clean working tree on a new branch.** The agent commits only if you authorize it (it asks once at the start of apply mode, or follows your project's instructions). With commits, each optimization lands as its own commit; without them, the report lists the files each item changed, so any one can be reviewed or reverted.
- **Share what you know about performance.** Profiler output, slow screens, slow endpoints, or "this list can hold 50,000 items" helps the agent focus on what matters. Without it, the agent estimates input sizes from the code and says so.
- **Narrow the scope for large projects.** Point it at a module, a directory, a file, or a single function instead of the whole repository.
- **Have a working test suite.** The agent runs it before and after every change. Projects with no tests still work, because the agent writes differential tests, but your own tests catch more.
- **Answer dependency requests deliberately.** When the best data structure is not in your language's standard library, the agent asks before adding a library and explains what it buys. You can decline; it then uses the best option without the dependency.
- **Check the verification evidence.** For each applied item, the report gives its verification level, the inputs and properties checked, the tests and tools actually run, what remains unverified, the prediction against the measurement, and which numbers are measured versus estimated. Passing tests are evidence, not proof. Changes that were tried and measured but not kept are listed too.
- **Follow up on `NEEDS-TESTING` markers.** If a change could not be fully verified and you approved it anyway, the agent marks it in the code and in the report with exactly what to verify. Search for `NEEDS-TESTING` before releasing.
- **Review behavior changes.** If an optimization would change behavior in any way, even for the better, the agent lists it under "Behavior changes for review" with the before and after behavior and waits for your decision. Approved ones are marked `BEHAVIOR-CHANGE` in the code.
- **Read the bug log.** Bugs the agent notices are documented in `BUGS-FOUND.md` and never fixed on purpose. Fix them separately. Each entry says whether the code was left as is, optimized with the bug preserved, or optimized with the bug removed as a side effect.

## Example prompts

```
find time complexity problems in this project
```

```
review the data structures in app/src/main/java/com/example/feed for performance
```

```
why is FeedRepository.mergeItems slow? the list can have 20,000 items
```

```
apply items 1 and 3 from the optimization report
```

```
optimize findDuplicates in app/src/main/java/com/example/Util.kt
```

```
add an endpoint that returns each customer's lifetime spend; we have about 2 million orders
```

```
check this module for N+1 database queries
```

## What you get

- **`OPTIMIZATION-REPORT.md`:** opens with the test-suite baseline (including tests that were already failing), the scope and what was not inspected, behavior changes awaiting your decision, and changes marked as needing testing. Then, for each item: the location, its contract, who calls it and the entry point it is reached from, the limiting resource, exposure, current complexity, lower bound and its basis, the candidates considered with their sources, the recommendation and why nothing better was chosen, the kind of win (asymptotic, constant-factor, or work avoided), memory impact across all copies, dependency needs, behavior risks, the prediction, the verification level reached, benchmark results against the prediction with the end-to-end share, how to reproduce them, and the files changed. Changes that were tried and rejected are listed with their measurements.
- **`.complexity-optimizer/languages/<LANGUAGE>.md`** (only for a language without a companion file, and only if you allow it): the language profile the agent built, for later sessions to reuse. Commit it.
- **`BUGS-FOUND.md`:** bugs noticed during analysis, with inputs, whether the bug was reproduced or only suspected, impact, a suggested fix (not applied), and whether an optimization removed it as a side effect.
- **Differential tests** in your test sources, with the original implementation kept as a reference. You decide whether to keep them as regression tests.
- **One commit per applied optimization, if you authorize commits,** with the before and after complexity and benchmark numbers. Without authorization nothing is committed, and the report lists each item's changed files.

For small results, the report is shown in the conversation instead of written to files. For larger ones, the agent asks where to write it (suggesting `optimization-report/`).

## Rules it enforces

Algorithmic Intelligence is designed to help agents make better decisions, not to encourage unnecessary optimization.

1. **Time is invaluable. Space is cheap, but not infinite.** Memory may be spent to save time, but it must stay bounded and must not cost time through GC pressure, cache misses, or OOM crashes. Memory is counted across every copy that can exist at once (per process, worker, request, or tenant), and a hard memory budget (embedded, kernel, mobile, per-request limits) rules out any approach that exceeds it.
2. **Time first, then space.** Space is optimized only after time is optimal, and never at the expense of time, except when the code exceeds a hard memory budget, and then only with your approval.
3. **Write the contract, then verify behavior is unchanged** with differential tests that compare return values, input mutation, exceptions, side effects, and ordering, and climb the verification ladder where it is cheap: tested, property-checked, exhaustively checked to a bound (bounded model checkers, concurrency checkers), proven. Only a machine-checked proof or a check of the whole input domain is called proven.
4. **Bugs are always documented and reported, never fixed on purpose.** If the buggy code is not optimized (already optimal, or behavior cannot be guaranteed unchanged), it is left exactly as is. If it is optimized, the optimization is applied and you are told about the bug; the bug stays unless the optimization removes it as a side effect (for example, an iterative rewrite that no longer overflows the stack), which is marked `BEHAVIOR-CHANGE`. That counts only when the bug was reproduced with a failing input and the change is the one the agent would make for speed alone; anything shaped to fix a bug goes to you for review.
5. **Behavior changes are never silent.** Unverified changes and any change that alters behavior (even for the better) are documented for developer review and applied only with explicit approval of that item; a general "apply all" does not approve them. Removing work counts as a change too: it needs proof that nothing uses the result and that the work has no other effect. Approved ones are marked `NEEDS-TESTING` or `BEHAVIOR-CHANGE` in code and in the report.
6. **Aim for the best possible complexity.** State the lower bound (or that none can be established, and why; never an invented one) and compare approaches in proportion to difficulty, without inventing alternatives to fill a quota. Analysis always reports the best achievable approach; applying is driven by evidence.
7. **Data structures must earn their place.** New dependencies need the developer's permission.
8. **Measure, do not only reason.** Profile before choosing, predict the speedup before benchmarking and compare, benchmark time and memory before and after with sound statistics, label results as measured or estimated, report what share of the whole operation the changed code took, and leave cold code with tiny inputs alone. Finding no caller is not evidence that code is cold. Shorter, newer, or more sophisticated code is never evidence of speed.
9. **Label the case:** worst, average, expected, or amortized, and judge by the worst case when attackers control the input, the code handles secrets, or a deadline is hard.
10. **Look beyond CPU loops:** N+1 queries, network calls in loops, main-thread blocking, repeated parsing, and repeated I/O.
11. **Keep the public contract:** signatures, return types, mutability of returned collections, threading, and errors.
12. **Start green:** the existing test suite runs before and after. If tests already fail, report mode lists them and continues; apply mode stops until you decide.
13. **Respect the project's idioms** and comment any non-obvious trick.
14. **Prefer the language's own data structures** over its host platform's (for example, Kotlin's `ArrayDeque` over `java.util.ArrayDeque`).

The full wording is in [`SKILL.md`](skills/complexity-optimizer/SKILL.md).

## Language independence

Algorithmic reasoning is independent of programming language, but implementation details and performance characteristics are not.

Language-specific companion references provide information about native data structures, standard library complexity, hidden costs, behavioral differences, testing, and benchmarking tools.

The rules, workflow, algorithm arsenal, differential testing, and behavior traps apply to every language. Companion files add language-specific detail. Currently supported language references:

| Language | Companion file |
|---|---|
| Kotlin (JVM, Multiplatform, Native, JS) | `languages/KOTLIN.md` |
| Java | `languages/JAVA.md` |
| Python | `languages/PYTHON.md` |
| Swift | `languages/SWIFT.md` |
| JavaScript and TypeScript | `languages/JAVASCRIPT-TYPESCRIPT.md` |
| C# | `languages/CSHARP.md` |
| C | `languages/C.md` |
| Rust | `languages/RUST.md` |
| Any other language | `languages/GENERIC.md`: the agent builds the same language profile before analyzing, and saves it in your project (see below) |

**Languages without a companion file.** For a language such as Erlang, Elixir, Go, or C++, the agent builds a language profile (data structures and their costs, hidden costs, ordering and number semantics, traps, tooling) and asks whether to save it to `.complexity-optimizer/languages/<LANGUAGE>.md` in your project, for example `.complexity-optimizer/languages/ERLANG.md`. Commit that file: later sessions load it instead of starting from scratch, so every developer and agent on the project works from the same facts, and updating the skill never overwrites it. Each claim in it is marked as documented (with its source), measured, or unverified, and unverified claims are not relied on until checked. You can correct the file by hand, and because it uses the same structure as the skill's companion files, it can be contributed back to the skill.

Each language file covers the language and its standard library only: built-in data structures and their costs, which structures need a dependency, hidden costs, bit-manipulation APIs, language-specific behavior traps, and test, profiling, benchmark, and verification tooling. Frameworks and platforms (UI toolkits, ORMs, web frameworks, game engines) are deliberately not covered; the general rules (N+1 queries, main-thread blocking, I/O in loops) apply to them. The reasoning methodology remains consistent across languages.

## Files

The skill's knowledge base is modular and organized around its engineering workflow.

| File | Purpose |
|---|---|
| `SKILL.md` | Mandatory rules, modes, language detection, workflow overview, anti-patterns |
| `WORKFLOW.md` | Report and apply mode: setup (including the test baseline and commit authorization), survey (scope, contracts, reachability to entry points, cost along the call chain, exposure), analysis, report, apply, close-out |
| `WRITING-NEW-CODE.md` | Write mode: which rules apply to new code, sizing the workload, choosing structures, existing-code bottlenecks, tests, summary |
| `ALGORITHM-ARSENAL.md` | How to find candidates: six triage questions (starting with whether the work is needed at all), complexity reference, routing by current complexity, lower bounds, reformulation |
| `CORE-TECHNIQUES.md` | Lookup tables of core techniques with their assumptions, production patterns, database queries, bit manipulation, combinations; loaded one section at a time |
| `DISCOVERY.md` | The method for finding better algorithms when no known technique fits, with a research log and a table of which move to try when one stalls: counting repeated work, carrying answers forward, designing from invariants, changing representation, special cases, reductions, amortization, randomization, work and span, lower-bound proofs (including conditional bounds from fine-grained complexity), estimates, doubling experiments, experiments on small cases, exchange arguments for greedy choices, small parameters, relaxations, duality, derivation by program transformation, and algorithms that use predictions while keeping a worst-case guarantee |
| `ADVANCED-TECHNIQUES.md` | Index of the advanced techniques: which domain file to load for which problem, and the rules shared by all of them |
| `techniques/*.md` | Advanced techniques by domain: graphs, trees, and compiler analyses; sequences, DP, search, and NP-hard problems; strings, automata, parsers, and ranked retrieval; math and numerics; machine learning and AI; image and signal processing; geometry and CAD; games, simulation, and game-tree search; spatial data; hardware and concurrency (including optimistic concurrency, CPU-feature dispatch, and what the compiler already does); data at scale (including change propagation and compression); optimization and scheduling (operations research); hostile inputs (including adaptive adversaries that observe outputs), secrets, and hard deadlines; distributed systems; queues and latency; specialized data structures |
| `DIFFERENTIAL-TESTING.md` | How to verify equivalence: reference copies and what to do when the original cannot be copied, what to compare (including aliasing and object identity), inputs, verification levels, the contract as executable checks, checking the check (planted differences and an A/A run), reporting evidence |
| `BENCHMARKING.md` | How to measure: predictions, doubling experiments, the noise floor from an A/A run, sound statistics, memory, regression guards, component versus end-to-end effect, and whether a proxy metric implies the real target |
| `BEHAVIOR-TRAPS.md` | Rewrites that look equivalent but are not, including ordering, aliasing and identity, removed work, numerical, machine-learning, image, geometry, simulation, hidden-input, concurrency, cancellation, and security traps |
| `REPORTING.md` | Report header (test baseline, scope), item format (including reachability and changed files), tried and rejected, behavior changes for review, bug log, `NEEDS-TESTING` and `BEHAVIOR-CHANGE` markers, final summary |
| `languages/INDEX.md`, `languages/*.md` | Which companion file to load for which project, and the per-language companions |

## Evaluation and Testing

The [`evals/`](evals/README.md) folder has test projects in Kotlin, TypeScript, Swift, C, and Rust, plus a held-out Python project never used for tuning, with planted cases: straightforward fixes, exponential and cubic starting points, costs that only appear along the call chain, code reached only through a plugin registration, techniques whose assumptions do not hold, ordering traps, planted bugs, security traps, and code that is not worth changing. Each has an answer key and a scorecard, and the Python and TypeScript projects have grading probes that run trap inputs against each session's final code. It also has a headless runner, cost and token statistics per session, a check of which prompts load the skill, a token-budget check, and tests of language-file claims that the official documentation does not settle.

Results so far (round 3, in [`evals/results/`](evals/results/)): on the held-out Python project, report-flow cases passed at 1.00 with the skill against 0.50 without it on Opus 5.5, and 0.83 against 0.39 on Haiku 5.5. On both models the code was correct even without the skill; the difference was judgment. Without the skill, every baseline run applied an unapproved concurrency change and shipped a hash-based fix that is quadratic on attacker-chosen keys. With the skill, no Opus run did either; Haiku held the concurrency change for review but still shipped the quadratic fix in two of three runs. These runs used Claude Code only; the skill is written to be agent-neutral, but other agents have not been evaluated yet. The Swift fixture has not yet been run on a Swift toolchain. See [`evals/README.md`](evals/README.md) to run the evaluations with and without the skill.

## The Philosophy

Better software doesn't begin with writing more code.

It begins with understanding the problem, questioning assumptions, exploring what's possible, and making deliberate engineering decisions.

It requires looking beyond the obvious solution, reasoning about computational trade-offs, discovering better approaches, and engineering implementations that are correct, efficient, and built to scale.

**Understand deeply.**

**Reason algorithmically.**

**Engineer exceptionally.**

## Contributing

Contributions are welcome, particularly in:

- New algorithmic techniques and discovery methods.
- Additional language-specific references.
- Improvements to correctness verification.
- Benchmarking methodologies.
- Evaluation fixtures and test cases.
- Real-world performance engineering scenarios.

When contributing algorithmic or language-specific knowledge, document assumptions, complexity characteristics, behavioral considerations, and authoritative references.

New language companion files are welcome. Use [`languages/GENERIC.md`](skills/complexity-optimizer/languages/GENERIC.md) as the checklist for what to cover, follow the structure of the existing files, and add a row to the table in `languages/INDEX.md`. Cover the language and its standard library only, not frameworks or platforms. Cite official documentation for every complexity and ordering claim, and list it in the file's "References" section. Where a claim is implementation behavior rather than documented behavior, say so, and add a check for it under `evals/claims/` (see `evals/claims/kotlin/` for an example).

When you change the skill itself, put each instruction in the file where it belongs, written so that any agent, from the smallest model to the largest, can follow it without guessing. Then run `evals/token-budget.sh`: budgets make growth visible and are raised when a needed instruction exceeds them, never met by trimming instructions.

## License

MIT. See [LICENSE](LICENSE).
