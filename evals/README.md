# Evaluating the skill

These evals check whether an agent using the skill makes the right call on code where the right answer is already known. Each fixture is a small project with planted cases. Each case targets one rule: a straightforward fix, a technique whose assumptions do not hold, an ordering trap, a planted bug, a security trap, code that is not worth changing, and so on.

`npx skills add` installs only the skill in `skills/`, so nothing in `evals/` reaches people who install the skill.

## Layout

```
evals/
├── fixtures/
│   ├── kotlin-shop/   ← 15 cases (Kotlin/JVM, Gradle, JUnit 4)
│   ├── ts-shop/       ← 12 cases + 1 write-mode case (TypeScript, Node's built-in test runner, no dependencies)
│   ├── swift-shop/    ← 10 cases (Swift Package Manager, XCTest); not yet verified on a toolchain
│   ├── c-shop/        ← 10 cases (C11, plain asserts, optional sanitizers)
│   ├── rust-shop/     ← 12 cases (Cargo, no dependencies)
│   ├── py-logistics/  ← 6 cases + 1 write-mode case (Python standard library); held out, never used for tuning
│   ├── java-clinic/   ← 10 cases + 1 write-mode case (Java standard library, javac); tuning set, twin of rb-clinic
│   └── rb-clinic/     ← 9 cases + 1 write-mode case (Ruby standard library, minitest); held out; tests languages/GENERIC.md
├── claims/            ← checks of language-file claims the docs do not settle (no agent)
├── answers/           ← answer keys; never let the agent see these
├── probes/            ← grading scripts: trap inputs run against the original and a run's final code
├── SCORECARD.md       ← copy per session and fill in
├── new-run.sh         ← creates a fresh run directory outside the repo
├── run-pilot.sh       ← runs a fixture headlessly with Claude Code, any skill version and model
├── session-stats.py   ← cost, tokens, and skill files read per session
├── cost-breakdown.py  ← where sessions spend their cost: reading, harnesses, tests, report, commits
├── token-budget.sh    ← fails when the skill's required loading grows past its budgets
└── trigger-test.sh    ← checks which prompts load the skill
```

## Testing the harness for free

`evals/selftest.sh` checks the runner with a stub agent instead of the real CLI, so it needs no API key and costs nothing: every runnable fixture sets up and runs its tests, the `CLAUDE.md` line lands only in with-skill runs, the cost cap stops sessions, and the stall watchdog stops a stuck turn without ending the batch (about 10 minutes). `evals/selftest.sh --probes` also checks the Java and Ruby grading probes against the correct and wrong rewrites in `probes/selftest/` (about 30 minutes more). Run it after changing any eval script.

## Requirements

- **kotlin-shop:** a full JDK 17 or newer (with `javac`) and network access for the first Gradle build. If your default Java has no compiler, point `JAVA_HOME` at a full JDK, for example the one bundled with Android Studio (`<android-studio>/jbr`).
- **ts-shop:** Node.js 23.6 or newer, which runs TypeScript files directly.
- **swift-shop:** Swift 5.9 or newer (Xcode on macOS, or a Swift toolchain on Linux). This fixture has not been run yet; see the status note in `answers/swift-shop.md`.
- **c-shop:** a C11 compiler (`cc`, `gcc`, or `clang`; set `CC` to choose). `./test.sh sanitize` builds with AddressSanitizer and UBSan where supported.
- **rust-shop:** Rust 1.80 or newer with Cargo.
- **py-logistics:** Python 3.10 or newer; standard library only. Since `languages/PYTHON.md` was added (after round 3), runs load it; rounds 1 to 3 ran with `languages/GENERIC.md`.
- **java-clinic:** a full JDK 17 or newer, with `javac` on `PATH` or `JAVA_HOME` pointing at it (export `JAVA_HOME` before starting the agent or `run-pilot.sh`). No build tool and no dependencies: `test.sh` compiles with `javac` and runs a minimal test runner.
- **rb-clinic:** Ruby 3.2 or newer; standard library only (minitest ships with Ruby). There is no Ruby companion file, so this fixture exercises `languages/GENERIC.md`.

**Platform:** the scripts need Bash, Git, Python 3, and GNU-compatible `timeout` (on macOS, install GNU coreutils). The dev container in `.devcontainer/` has everything, including Swift; it has not yet been built and tested, so the first build may need small fixes.

Check that the fixture is green before you start:

```bash
cd evals/fixtures/kotlin-shop && ./gradlew test
cd evals/fixtures/ts-shop && npm test
cd evals/fixtures/swift-shop && swift test
cd evals/fixtures/c-shop && ./test.sh && ./test.sh sanitize
cd evals/fixtures/rust-shop && cargo test
cd evals/fixtures/py-logistics && ./test.sh
cd evals/fixtures/java-clinic && ./test.sh
cd evals/fixtures/rb-clinic && ./test.sh
```

## Running one evaluation

1. **Create a run directory** outside the repository so the agent cannot read the answer keys:

   ```bash
   # With the skill (copies it into the run directory, here for Claude Code):
   evals/new-run.sh kotlin-shop --skill .claude/skills

   # Baseline without the skill:
   evals/new-run.sh kotlin-shop
   ```

   The script prints the new directory. It contains the fixture as a fresh Git repository with one commit. For other agents, pass that agent's project skills directory to `--skill`, or install the skill there with the agent's own method.

   For a baseline run, make sure the skill is not installed globally for your agent.

2. **Start the agent in the run directory** and send the report-mode prompt:

   ```
   Find time complexity and data-structure problems in this project and write a report.
   ```

   Score the report against the answer key. Check that the agent changed no files (`git status`).

3. **Send the apply-mode prompt:**

   ```
   Apply all the optimizations you recommend.
   ```

   To keep runs comparable, **decline every approval request and every dependency request** during the eval. This tests that the agent asks, and that it falls back to the best option that needs no approval. The question about commits counts too: declining it means the agent must not commit, and must list the changed files per item instead. Rounds 1 to 3 ran before commits became opt-in (2026-10-31), so their "one commit per change" results are not comparable with later runs.

4. **Check the result:**

   ```bash
   git log --oneline                 # one commit per optimization, only if commits were authorized
   git diff HEAD~N -- src            # what changed
   ./gradlew test   # or npm test, swift test, ./test.sh, cargo test: still green on the final code
   ```

5. **Score** the run in a copy of `SCORECARD.md` using `answers/<fixture>.md`.

## Running a write-mode evaluation

Write-mode cases (IDs ending in `W1`, `W2`, and so on) test new code, not existing code. Run each in its own fresh run directory, never after the report and apply prompts, since those would already have optimized the code the new feature calls.

1. Create a run directory as above, with or without the skill.
2. Send the prompt from the case's section of the answer key, unchanged.
3. Decline every approval and dependency request, as above. Write mode should still finish the feature without them.
4. Check that existing files are unchanged unless the case says otherwise (`git status`, `git diff`), that the new tests and the existing suite pass, and score the case.

## Running headlessly with Claude Code

`evals/run-pilot.sh` runs a fixture's report flow (report, "apply all", decline every approval) and its write-mode case through `claude -p`, and keeps every transcript, the git state, and the test results under `~/complexity-optimizer-evals/`. It limits tools to file reads and edits plus the fixture's test command and `git`, and caps spending per turn. Options:

- `--fixture ts-shop | py-logistics | java-clinic | rb-clinic`, or, report flow only, `kotlin-shop | swift-shop | c-shop | rust-shop` (configured but not yet run; kotlin-shop's first Gradle build needs network access)
- `--cases report,write` and `--conditions skill,baseline`
- `--skill-ref <commit>` installs the skill as it was at that commit, to compare versions
- `--model <model>` runs another model
- `--runs N`, `--parallel P`, `--budget USD` (per turn), `--out DIR`
- `--max-total-usd USD` stops starting sessions once the round has reported that much in total; use it on every paid run, with `--parallel 1` when the limit must be tight
- `--instructions TEXT` writes a `CLAUDE.md` line (such as the README's recommended loading line) into with-skill run directories
- `--effort LEVEL` passes `claude --effort`. Medium effort cut cost by about a third in round 5 with identical code results, but thinner reports: fine for sweeps graded by the probe, not for grading reports
- `--skill-src DIR` tests a skill variant from a directory without committing it; `--allow-subagents` also allows the sub-agent tool
- `--stall-seconds S` (default 600) stops a turn whose transcript has stopped growing while no tool runs, marks the session invalid, and skips its later turns; the rest of the batch continues

Start it detached so it survives closing the terminal:

```bash
nohup setsid evals/run-pilot.sh --fixture py-logistics --runs 3 > /dev/null 2>&1 &
```

Follow `progress.log` in the output directory. Then:

1. `python3 -I evals/session-stats.py <out>` for cost, tokens, and the skill files each session opened, and `python3 -I evals/cost-breakdown.py <out>` for what that cost was spent on (add `--samples` to spot-check how tool calls were classified).
2. The fixture's probe for each session's final code: `python3 -I evals/probes/py-logistics.py <session directory>`, `node evals/probes/ts-shop.ts evals/fixtures/ts-shop/src <session directory>/src`, `JAVA_HOME=<jdk> python3 -I evals/probes/java-clinic.py <session directory>`, or `python3 -I evals/probes/rb-clinic.py <session directory>`. The clinic probes run the whole check list against the original and the session's code and take several minutes (the original's slow cases are part of it).
3. Score each session in a copy of `SCORECARD.md`, using the answer key and the probe's output.

Sessions that hit a usage limit are marked "API ERROR, session invalid" in `progress.log`: rerun them rather than scoring them. Results from past runs are in `results/`.

`evals/trigger-test.sh` checks which prompts load the skill. Besides `--runs`, `--ids`, and `--parallel`, it takes `--model`, `--skill-ref <commit>` (another version of the skill), and `--instructions "<text>"` (written to `CLAUDE.md` in each run directory, to test a project-instruction line).

`evals/token-budget.sh` checks the skill's required loading per mode against budgets without running an agent. Run it after every change to the skill.

`evals/claims/kotlin-claims.sh` checks claims in `languages/KOTLIN.md` that the official documentation does not settle (IDs `K-P*` while pending; none are pending as of 2026-11-01), plus claims already confirmed by a run (`K-C*`, regression checks). It prints one `CLAIM` line per check and fails when a claim is wrong. After each run, update `KOTLIN.md` from the `K-P*` results: state confirmed behavior plainly (noting it is undocumented where that matters) and move the check to the confirmed section. No agent is involved and it costs nothing, so run it whenever the Kotlin version or `KOTLIN.md` changes.

## Next runs

The most valuable runs not yet done, in order, with their commands. Each needs a spending limit that allows it; always keep `--max-total-usd`.

```bash
line="Use the algorithmic-intelligence skill when writing new code that loops over collections or data, and for any question about the speed or complexity of existing code."

# 1. Held-out rb-clinic, 4 more pairs (about $3.60): a defensible skill-versus-baseline rate.
evals/run-pilot.sh --fixture rb-clinic --cases report --runs 4 --parallel 1 \
  --model claude-haiku-5-5 --instructions "$line" --max-total-usd 4.50

# 2. The same on the default model (about $4 per pair at round 3's rates): the README's headline numbers are from it.
evals/run-pilot.sh --fixture rb-clinic --cases report --runs 2 --parallel 1 \
  --instructions "$line" --max-total-usd 10

# 3. A second java-clinic baseline (about $0.30), and the verified-batching change before and after (J1, J3).
evals/run-pilot.sh --fixture java-clinic --cases report --conditions baseline --runs 1 \
  --model claude-haiku-5-5 --max-total-usd 1
```

Another agent (Codex CLI, Gemini CLI) is not supported by `run-pilot.sh` yet: it calls `claude -p` and parses Claude Code's stream format. Supporting one means a per-agent command, allowed-tools mapping, and transcript parser.

## Getting meaningful results

- **Run each fixture three times.** Agents vary between runs; one run proves little.
- **Compare with and without the skill.** Cases that pass either way show where the skill adds nothing. Cases that fail even with the skill show where its wording needs work. Record the difference in the "Skill lift" table of `SCORECARD.md`.
- **Compare agents.** The skill is meant to be agent-neutral. A case that passes in one agent but fails in another usually points to an ambiguous rule.
- **Fix the skill, not the fixture, and only on tuning fixtures.** When a case fails, change the skill's wording, then rerun. Change a fixture only if the case itself is wrong. Tuning fixtures (`ts-shop`, `java-clinic`, and the four never-run shop fixtures) are for finding where the wording fails. Held-out fixtures (`py-logistics`, `rb-clinic`) only measure: a change made because of a held-out result must be checked on a tuning fixture, and the held-out fixture is then replaced for the next round. `java-clinic` and `rb-clinic` are twins: each category has a case in both, with a different surface, so an improvement found on one can be checked on the other.

## Adding a case

A case earns its place only if it can tell the skill apart from no skill. Before any run, its answer key states why an agent without the skill is likely to fail it and which instruction should prevent that; a case every condition passes is a control or a regression check, and the answer key labels it so. Invented problems are welcome (models cannot recall their answers), but the key's own answer must then be checked: compare the intended solution with a brute-force reference on every small input, and state the lower bound with its basis or say that none is known.

1. Add the code to a fixture, written as ordinary project code. Do not hint at the answer in names or comments.
2. Keep the fixture's existing tests green. Planted bugs must not be caught by the existing tests.
3. Verify that the trap actually triggers (for example, that the recursion really overflows, or that the alternative really changes output).
   If the trap depends on the platform or library version (for example, `qsort` stability or stack depth), record where you verified it in the answer key.
4. Add the case to the answer key with the expected outcome, pass criteria, failure signals, and why a baseline is likely to fail.
5. If the fixture has a probe, add a check, and confirm it on two rewrites of your own: a correct one (the probe must report no difference) and the tempting wrong one (the probe must catch it).
