# Algorithmic Intelligence

### Algorithmic Reasoning and Performance Engineering for AI Coding Agents

**Make AI agents think beyond code generation.**

Algorithmic Intelligence (`algorithmic-intelligence`) is a skill for AI coding agents. It teaches an agent to reason about code the way an algorithms researcher, a performance engineer, a verification engineer, and an experimental scientist would: understand the computational problem, find the best achievable approach (or derive one when no known technique fits), prove that the change keeps behavior, and measure the result.

- **In existing code, it never changes behavior without your approval.** Every change is backed by differential tests that run the original and the optimized code on the same inputs and compare the results, and anything that would behave differently is listed for your decision first.
- **In new code, it chooses efficient algorithms and data structures from the first version,** sized for the inputs the code will really see.
- **It works with any coding agent that supports skills, in any programming language,** and in any kind of codebase: applications, backends, libraries, databases, compilers, kernels, and embedded firmware.

Sometimes the best engineering decision is to leave the code alone, and the skill says so when it is.

## Quick start

```bash
# 1. Install into the project you want to optimize
cd path/to/your-project
npx skills add https://github.com/protechnocrats/algorithmic-intelligence --skill algorithmic-intelligence

# 2. Start your coding agent in that project and ask:
#    "find time complexity problems in this project"
```

The agent returns a ranked report and changes nothing until you approve specific items.

## How it thinks

The skill guides the agent through six stages. Each is backed by detailed reference files that the agent loads only when a step needs them.

1. **Understand the problem.** Write the code's contract (what it requires, returns, changes, and throws, including order, ties, and duplicates), trace who calls it up to a real entry point, multiply the cost along that call chain, estimate realistic input sizes and call frequency, and name the resource that limits it: CPU, memory, I/O, network, a lock, or a queue. Check its exposure: untrusted input, secrets, or a hard deadline means judging by the worst case.
2. **Analyze the current solution.** State the current complexity in every size variable, labeled worst, average, expected, or amortized, and the lower bound for the problem with its basis: proven, conditional, conjectured, or unknown. A bound is never invented.
3. **Explore alternatives.** Compare approaches in proportion to the problem's difficulty: at least three for nontrivial problems, including combinations of techniques. Check every technique's assumptions against the code. When no known technique fits, derive one with a discovery method drawn from how the field's best algorithm designers work (see "The discovery method" below), and label every algorithm as established, experimental, or derived.
4. **Engineer the solution.** Choose the approach that is best for the real workload, not just the best on paper: memory stays bounded across every copy that can exist at once, data structures must earn their place, new dependencies need your permission, and the project's idioms are respected.
5. **Verify correctness.** Differential tests compare return values, input mutation, exceptions, side effects, and ordering. The tests must first prove they can fail: they must catch a deliberately planted difference and pass with the original on both sides. Then the agent climbs the verification ladder where it is cheap: tested, property-checked, exhaustively checked to a stated bound, proven. Passing tests are evidence, not proof; only a machine-checked proof or a check of the whole input domain is called proven.
6. **Measure performance.** Predict the speedup before benchmarking, then measure time and memory at realistic and larger sizes, against the noise floor of an identical A/A run, and report the changed code's share of the whole operation. A 10× speedup of code that takes 2% of a request saves under 2%, and the report says so. Every number is labeled measured or estimated.

### The discovery method

When no table of known techniques fits, `DISCOVERY.md` gives the agent the moves that algorithm designers use on problems nobody has solved before, with a research log and a table of which move to try when one stalls:

| Move | From |
|---|---|
| Count the repeated work; carry the answer forward; change the representation | Knuth, Bentley |
| Design from the invariant | Dijkstra, Gries |
| Solve a special case first; experiment on small cases, then conjecture | Pólya, Knuth |
| Reduce to a solved problem, or from a hard one, and know when to stop (including conditional lower bounds from fine-grained complexity) | Karp, CLRS, Vassilevska Williams |
| Amortize; randomize; shorten the critical path | Tarjan, Mitzenmacher, Leiserson |
| Prove a greedy choice with an exchange argument | Smith, Kleinberg and Tardos |
| Find the small parameter; relax, then bound or repair; look at the dual | Downey and Fellows, Held and Karp, König |
| Derive the fast version by transformation | Burstall and Darlington, Bird |
| Use a prediction while keeping a worst-case guarantee | Mitzenmacher and Vassilvitskii |
| Estimate before building; measure the growth rate | Bentley, Sedgewick |

The algorithm tables are the toolbox, not the product: the skill's value is the method of finding, verifying, and measuring a better solution.

## Three modes

| Mode | Triggered by | What happens |
|---|---|---|
| **Report** | "find performance problems", "review this for complexity", "what can be optimized?" | The agent surveys existing code, analyzes it, and returns a ranked report. **No code changes.** |
| **Apply** | "apply items 1 and 3", "optimize `findDuplicates` in `Util.kt`" | The agent changes only the existing code you named, one optimization at a time, with differential tests and a benchmark for each. |
| **Write** | "add CSV export for orders", "build a rate limiter", "write a function that merges these feeds" | The agent writes the new code you asked for, choosing algorithms and data structures for the expected input sizes, and ends with a short list of its performance decisions. It does not change existing code just for speed; if existing code is the bottleneck, it tells you and asks. |

The agent names the mode it picked in one line at the start, so you can redirect it. If the request is ambiguous, or you invoke the skill with no task, it asks. Approving one item never approves the others.

## Installation

### Option 1: Skills CLI (recommended)

The [Skills CLI](https://skills.sh) installs the skill into the right place for your agent.

Per project (only active in this project; can be committed so your team gets it too):

```bash
npx skills add https://github.com/protechnocrats/algorithmic-intelligence \
  --skill algorithmic-intelligence
```

For your user account (active in every project):

```bash
npx skills add https://github.com/protechnocrats/algorithmic-intelligence \
  --skill algorithmic-intelligence \
  --global
```

Run `npx skills --help` to choose a specific agent or run non-interactively. Requires Node.js.

### Option 2: Manual install

Copy the `skills/` folder (it contains `SKILL.md` and the files it links to) into your agent's skills directory, as a folder named `algorithmic-intelligence`:

```bash
git clone https://github.com/protechnocrats/algorithmic-intelligence.git
cp -r algorithmic-intelligence/skills <your-agent-skills-dir>/algorithmic-intelligence
```

For example, Claude Code reads skills from `.claude/skills/` in a project or `~/.claude/skills/` for your user. For other agents, check their documentation for the skills directory. Keep the folder intact: `SKILL.md` links to the other files by relative path.

### Option 3: Agents without skill support

If your agent does not support skills but reads a project instructions file (such as `AGENTS.md`), copy the folder into your repository and add a line to that file:

```markdown
For performance, time complexity, or data-structure work, follow skills/SKILL.md and the files it links to.
```

### Make sure it loads for new code

Agents load a skill by matching your request against the skill's description. Requests about speed or complexity match easily. Requests for new code match only when the code loops over data (aggregating, counting, searching, filtering, sorting, ranking, joining, merging, deduplicating, or grouping), runs per request, item, frame, or keystroke, calls databases or services in loops, or needs a data-structure choice; for a small, ordinary feature the agent may not load it. To make sure it is used, add this line to the project's agent instructions (`CLAUDE.md`, `AGENTS.md`, or your agent's equivalent):

```
Use the algorithmic-intelligence skill when writing new code that loops over collections or data, and for any question about the speed or complexity of existing code.
```

Without it, agents can skip the skill for new code. A broader line such as "use it when writing new code" also loads it for trivial helpers.

### Verify and update

Ask your agent: "Which skills do you have for optimizing time complexity?" It should name `algorithmic-intelligence`. Or ask it to "explain the algorithmic-intelligence rules" and check that it lists the mandatory rules.

To update, re-run the install command, or `git pull` your clone and copy the folder again.

**A specific release.** Every release is tagged (see [Releases](https://github.com/protechnocrats/algorithmic-intelligence/releases)). To install one, point the Skills CLI at the tag's `skills/` folder:

```bash
npx skills add https://github.com/protechnocrats/algorithmic-intelligence/tree/v0.1.0/skills \
  --skill algorithmic-intelligence
```

The Skills CLI documents folder URLs like this, not tags as such; it installed `v0.1.0` correctly when tested. For a manual install, `git clone --branch v0.1.0 https://github.com/protechnocrats/algorithmic-intelligence.git` and copy `skills/` as above.

## What happens in a run

Report and apply mode:

1. **Setup:** detects languages and versions, finds your test, benchmark, profiling, and verification tooling, and runs your existing test suite. If tests already fail, report mode lists them and continues; apply mode stops before changing any code until you decide. In apply mode it asks once whether to commit each optimization, unless your project's instructions already say.
2. **Survey:** confirms the scope you asked for, profiles the code when it can run, and finds candidate hotspots. For each one it writes the contract, traces the callers up to a real entry point (a route, job, listener, command, UI handler, or public API, including code reached through dependency injection, plugins, or reflection), multiplies the cost along that call chain, estimates input sizes, names the limiting resource, and checks exposure. Code with no caller found is never assumed dead: its reachability is reported as unknown and you are asked.
3. **Analyze:** first asks whether the work is needed at all, then states the lower bound and compares approaches as described in "How it thinks," writes a prediction of the speedup and of the end-to-end effect, and plans how strongly the change can be verified.
4. **Report:** starts with the test-suite baseline and the scope (including what was not inspected), lists behavior changes for review first, then ranks items by real-world impact. Report mode ends here.
5. **Apply** (only on approval): writes differential tests and contract checks against the original first and checks that they can fail, makes the change, verifies it at the highest cheap level, benchmarks it against its written prediction and states its share of the end-to-end operation, and commits each optimization separately only if you authorized commits.
6. **Close out:** summarizes what was applied and at which verification level, predictions against measurements, what was tried and rejected, what is marked as needing testing, bugs found, pending dependency requests, items whose reachability is unknown, the commits made or the files each item changed, and regression benchmarks you chose to keep.

Write mode: estimates input sizes and call frequency for each part of the new code, picks or derives algorithms and data structures to match, keeps calls into slow existing code to a minimum, tests the new code against a slow, obviously correct reference version and its contract, and lists its performance decisions with their complexity, size assumptions, and verification level.

## What you get

- **`OPTIMIZATION-REPORT.md`:** written once, at the end of report mode, and never edited afterward. It opens with the test-suite baseline (including tests that were already failing), the scope and what was not inspected, and behavior changes awaiting your decision. Then, for each item: the location, its contract, the entry point it is reached from, the limiting resource, exposure, current complexity, lower bound and its basis, the candidates considered with their sources, the recommendation and why nothing better was chosen, the kind of win (asymptotic, constant-factor, or work avoided), memory impact across all copies, dependency needs, behavior risks, the prediction, and the planned verification. Changes that were tried and rejected are listed with their measurements. Each field is one line unless you have a decision to make about it, and straightforward items use a shorter format, so the report stays proportional.
- **`APPLY-RESULTS.md`** (apply mode): written once at the end, so the analysis report stays exactly as you reviewed it. For each item you approved: the verification level, inputs and properties checked, the planted differences the tests caught, the tests and tools run, what remains unverified, measurements against the prediction with the end-to-end share, how to reproduce them, and the files changed. Also changes marked as needing testing, behavior-change decisions, changes tried and rejected while applying, and bugs found while applying.
- **`BUGS-FOUND.md`:** bugs noticed during analysis, with inputs, whether the bug was reproduced or only suspected, impact, a suggested fix (not applied), and whether an optimization removed it as a side effect.
- **Differential tests** in your test sources, with the original implementation kept as a reference. You decide whether to keep them as regression tests.
- **One commit per applied optimization, if you authorize commits,** with the before and after complexity and benchmark numbers. Without authorization nothing is committed, and the report lists each item's changed files.
- **`.algorithmic-intelligence/languages/<LANGUAGE>.md`** (only for a language without a companion file, and only if you allow it): the language profile the agent built, for later sessions to reuse. Commit it. See "Languages."

For small results, the report is shown in the conversation instead of written to files. For larger ones, the agent asks where to write it (suggesting `optimization-report/`).

## Getting the best results

- **For existing code, start in report mode.** Read the report, then approve items by ID. You stay in control of every change.
- **Start from a clean working tree on a new branch.** With commits authorized, each optimization lands as its own commit; without them, the report lists the files each item changed, so any one can be reviewed or reverted.
- **Share what you know about performance.** Profiler output, slow screens, slow endpoints, or "this list can hold 50,000 items" helps the agent focus on what matters. Without it, the agent estimates input sizes from the code and says so.
- **Narrow the scope for large projects.** Point it at a module, a directory, a file, or a single function instead of the whole repository.
- **Have a working test suite.** The agent runs it before and after every change. Projects with no tests still work, because the agent writes differential tests, but your own tests catch more.
- **Answer dependency requests deliberately.** When the best data structure is not in your language's standard library, the agent asks before adding a library and explains what it buys. You can decline; it then uses the best option without the dependency.
- **Check the verification evidence.** For each applied item, the report gives its verification level, the inputs and properties checked, the planted differences the tests caught, the tests and tools actually run, what remains unverified, the prediction against the measurement, and which numbers are measured versus estimated.
- **Follow up on `NEEDS-TESTING` markers.** If a change could not be fully verified and you approved it anyway, the agent marks it in the code and in the report with exactly what to verify. Search for `NEEDS-TESTING` before releasing.
- **Review behavior changes.** If an optimization would change behavior in any way, even for the better, the agent lists it under "Behavior changes for review" with the before and after behavior and waits for your decision. Approved ones are marked `BEHAVIOR-CHANGE` in the code.
- **Read the bug log.** Bugs the agent notices are documented in `BUGS-FOUND.md` and never fixed on purpose. Fix them separately.

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

## Rules it enforces

The skill exists to help agents make better decisions, not to encourage optimization for its own sake. Fourteen mandatory rules govern every mode:

1. **Time is invaluable. Space is cheap, but not infinite.** Memory may be spent to save time, but it must stay bounded and must not cost time through GC pressure, cache misses, or OOM crashes. Memory is counted across every copy that can exist at once (per process, worker, request, or tenant), and a hard memory budget (embedded, kernel, mobile, per-request limits) rules out any approach that exceeds it.
2. **Time first, then space.** Space is optimized only after time is optimal, and never at the expense of time, except when the code exceeds a hard memory budget, and then only with your approval.
3. **Write the contract, then verify behavior is unchanged** with differential tests that compare return values, input mutation, exceptions, side effects, and ordering, and that are first shown to catch a planted difference. Climb the verification ladder where it is cheap: tested, property-checked, exhaustively checked to a bound (bounded model checkers, concurrency checkers), proven. Only a machine-checked proof or a check of the whole input domain is called proven.
4. **Bugs are always documented and reported, never fixed on purpose.** If the buggy code is not optimized, it is left exactly as is. If it is optimized, the bug stays unless the optimization removes it as a side effect (for example, an iterative rewrite that no longer overflows the stack), which is marked `BEHAVIOR-CHANGE`. That counts only when the bug was reproduced with a failing input and the change is the one the agent would make for speed alone; anything shaped to fix a bug goes to you for review.
5. **Behavior changes are never silent.** Unverified changes and any change that alters behavior (even for the better) are documented for your review and applied only with your explicit approval of that item; a general "apply all" does not approve them. Removing work counts as a change too: it needs proof that nothing uses the result and that the work has no other effect.
6. **Aim for the best possible complexity.** Count every call at its real cost: the language's built-in operations, library and framework calls, and the project's own functions, multiplied by how often each runs, plus implicit work such as copies, conversions, and hashing; a call is never assumed O(1) because it is short or built in. State the lower bound (or that none can be established, and why; never an invented one) and compare approaches in proportion to difficulty, without inventing alternatives to fill a quota. Analysis always reports the best achievable approach; applying is driven by evidence.
7. **Data structures must earn their place.** New dependencies need your permission.
8. **Measure, do not only reason.** Profile before choosing, predict the speedup before benchmarking and compare, benchmark time and memory before and after with sound statistics, label results as measured or estimated, report the changed code's share of the whole operation, and leave cold code with tiny inputs alone. Finding no caller is not evidence that code is cold. Shorter, newer, or more sophisticated code is never evidence of speed.
9. **Label the case:** worst, average, expected, or amortized, and judge by the worst case when attackers control the input, the code handles secrets, or a deadline is hard.
10. **Look beyond CPU loops:** N+1 queries, network calls in loops, main-thread blocking, repeated parsing, and repeated I/O.
11. **Keep the public contract:** signatures, return types, mutability of returned collections, threading, and errors.
12. **Start green:** the existing test suite runs before and after. If tests already fail, report mode lists them and continues; apply mode, and write mode when existing code would change, stops until you decide.
13. **Respect the project's idioms** and comment any non-obvious trick.
14. **Prefer the language's own data structures** over its host platform's (for example, Kotlin's `ArrayDeque` over `java.util.ArrayDeque`).

The full wording is in [`SKILL.md`](skills/SKILL.md).

## Languages

Algorithmic reasoning is independent of the programming language, but costs and behavior are not. The rules, workflow, discovery method, differential testing, and behavior traps apply to every language; companion files add each language's data structures and their costs, hidden costs, bit-manipulation APIs, behavior traps, and test, profiling, benchmark, and verification tooling.

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
| Any other language | `languages/GENERIC.md`: the agent builds the same profile before analyzing, and saves it in your project |

**Languages without a companion file.** For a language such as Erlang, Elixir, Go, or C++, the agent builds a language profile and asks whether to save it to `.algorithmic-intelligence/languages/<LANGUAGE>.md` in your project, for example `.algorithmic-intelligence/languages/ERLANG.md`. Commit that file: later sessions load it instead of starting from scratch, so every developer and agent on the project works from the same facts, and updating the skill never overwrites it. Each claim in it is marked as documented (with its source), measured, or unverified, and unverified claims are not relied on until checked. You can correct the file by hand, and because it uses the same structure as the skill's companion files, it can be contributed back to the skill.

Companion files cover the language and its standard library only. Frameworks and platforms (UI toolkits, ORMs, web frameworks, game engines) are deliberately not covered; the general rules (N+1 queries, main-thread blocking, I/O in loops) apply to them.

## Evaluation

The skill will be evaluated by running the same coding agent on projects with planted problems, with and without the skill, and checking each session's final code and reports. The benchmarks are being built ([docs/EVAL-PLAN.md](docs/EVAL-PLAN.md)); results will be published here when they exist.

## Files

The skill's knowledge base is modular and organized around its workflow. The agent loads only the files a step names.

| File | Purpose |
|---|---|
| `SKILL.md` | Mandatory rules, modes, language detection, workflow overview, anti-patterns |
| `WORKFLOW.md` | Report and apply mode: setup (including the test baseline and commit authorization), survey (scope, contracts, reachability to entry points, cost along the call chain, exposure), analysis, report, apply, close-out |
| `WRITING-NEW-CODE.md` | Write mode: which rules apply to new code, sizing the workload, choosing structures, existing-code bottlenecks, tests, summary |
| `ALGORITHM-ARSENAL.md` | How to find candidates: six triage questions (starting with whether the work is needed at all), complexity reference, routing by current complexity, lower bounds, reformulation, behavior-changing techniques |
| `CORE-TECHNIQUES.md` | Lookup tables of core techniques with their assumptions, production patterns, database queries, bit manipulation, combinations; loaded one section at a time |
| `DISCOVERY.md` | The method for finding better algorithms when no known technique fits (see "The discovery method" above) |
| `ADVANCED-TECHNIQUES.md` | Index of the advanced techniques: which domain file to load for which problem, and the rules shared by all of them |
| `techniques/*.md` | Advanced techniques by domain: graphs and trees; sequences, DP, search, and NP-hard problems; strings, automata, parsers, and ranked retrieval; math and numerics; machine learning and AI; image and signal processing; geometry and CAD; games and simulation; spatial data; hardware and concurrency; data at scale; optimization and scheduling (operations research); hostile inputs (including adaptive adversaries that observe outputs), secrets, and hard deadlines; distributed systems; queues and latency; specialized data structures |
| `DIFFERENTIAL-TESTING.md` | How to verify equivalence: reference copies, what to compare (including aliasing and object identity), inputs, verification levels, the contract as executable checks, checking the check (planted differences and an A/A run), reporting evidence |
| `BENCHMARKING.md` | How to measure: predictions, doubling experiments, the noise floor from an A/A run, sound statistics, memory, regression guards, component versus end-to-end effect, and whether a proxy metric implies the real target |
| `BEHAVIOR-TRAPS.md` | Rewrites that look equivalent but are not: ordering, aliasing and identity, removed work, numerical, machine-learning, image, geometry, simulation, hidden-input, concurrency, cancellation, and security traps |
| `REPORTING.md` | Report header (test baseline, scope, language profile), item format, tried and rejected, behavior changes for review, bug log, `NEEDS-TESTING` and `BEHAVIOR-CHANGE` markers, final summary |
| `languages/INDEX.md`, `languages/*.md` | Which companion file to load for which project, the per-language companions, and `GENERIC.md` for building and saving a profile for any other language |

## For contributors

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): what each part of the repository does, what the agent loads in each mode, and where each idea lives.
- [CONTRIBUTING.md](CONTRIBUTING.md): how changes reach `main`, and the rules for changing the skill.
- `.devcontainer/`: the JDK, Ruby, Node, Rust, Python, and Swift toolchains, and a sandbox for running agent sessions.
- [docs/EVAL-PLAN.md](docs/EVAL-PLAN.md): the plan for the next evaluations.

## Releases and security

- **Releases:** every version is tagged (`v0.1.0`, `v0.2.0`, …) and published on the [Releases](https://github.com/protechnocrats/algorithmic-intelligence/releases) page with its release notes. The notes for every version are in [CHANGELOG.md](CHANGELOG.md); how releases are made is in [RELEASING.md](RELEASING.md).
- **Security:** to report a vulnerability, follow [SECURITY.md](SECURITY.md). Report privately through the repository's Security tab, not in a public issue.

## Contributing

Contributions are welcome, particularly new discovery methods and algorithmic techniques, language companion files, improvements to verification and benchmarking, and real-world performance problems. Judge each addition by whether it changes how the agent thinks, verifies, or measures, not by coverage alone, and document its assumptions, complexity, behavioral considerations, and authoritative references. [CONTRIBUTING.md](CONTRIBUTING.md) has the details: how changes reach `main`, the rules for changing the skill, and the checklist for language companion files.

**Understand deeply. Reason algorithmically. Engineer exceptionally.**

## License

MIT. See [LICENSE](LICENSE).
