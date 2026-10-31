# Evaluating the skill

These evals check whether an agent using the skill makes the right call on code where the right answer is already known. Each fixture is a small project with planted cases. Each case targets one rule: a straightforward fix, a technique whose assumptions do not hold, an ordering trap, a planted bug, a security trap, code that is not worth changing, and so on.

`npx skills add` installs only `skills/complexity-optimizer/`, so nothing in `evals/` reaches people who install the skill.

## Layout

```
evals/
├── fixtures/
│   ├── kotlin-shop/   ← 14 cases (Kotlin/JVM, Gradle, JUnit 4)
│   ├── ts-shop/       ← 12 cases + 1 write-mode case (TypeScript, Node's built-in test runner, no dependencies)
│   ├── swift-shop/    ← 10 cases (Swift Package Manager, XCTest); not yet verified on a toolchain
│   ├── c-shop/        ← 10 cases (C11, plain asserts, optional sanitizers)
│   ├── rust-shop/     ← 12 cases (Cargo, no dependencies)
│   └── py-logistics/  ← 6 cases + 1 write-mode case (Python standard library); held out, never used for tuning
├── answers/           ← answer keys; never let the agent see these
├── probes/            ← grading scripts: trap inputs run against the original and a run's final code
├── SCORECARD.md       ← copy per session and fill in
├── new-run.sh         ← creates a fresh run directory outside the repo
├── run-pilot.sh       ← runs a fixture headlessly with Claude Code, any skill version and model
├── session-stats.py   ← cost, tokens, and skill files read per session
├── token-budget.sh    ← fails when the skill's required loading grows past its budgets
└── trigger-test.sh    ← checks which prompts load the skill
```

## Requirements

- **kotlin-shop:** a full JDK 17 or newer (with `javac`) and network access for the first Gradle build. If your default Java has no compiler, point `JAVA_HOME` at a full JDK, for example the one bundled with Android Studio (`<android-studio>/jbr`).
- **ts-shop:** Node.js 23.6 or newer, which runs TypeScript files directly.
- **swift-shop:** Swift 5.9 or newer (Xcode on macOS, or a Swift toolchain on Linux). This fixture has not been run yet; see the status note in `answers/swift-shop.md`.
- **c-shop:** a C11 compiler (`cc`, `gcc`, or `clang`; set `CC` to choose). `./test.sh sanitize` builds with AddressSanitizer and UBSan where supported.
- **rust-shop:** Rust 1.80 or newer with Cargo.
- **py-logistics:** Python 3.10 or newer; standard library only. No language companion file covers Python, so this fixture also tests `languages/GENERIC.md`.

Check that the fixture is green before you start:

```bash
cd evals/fixtures/kotlin-shop && ./gradlew test
cd evals/fixtures/ts-shop && npm test
cd evals/fixtures/swift-shop && swift test
cd evals/fixtures/c-shop && ./test.sh && ./test.sh sanitize
cd evals/fixtures/rust-shop && cargo test
cd evals/fixtures/py-logistics && ./test.sh
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

   To keep runs comparable, **decline every approval request and every dependency request** during the eval. This tests that the agent asks, and that it falls back to the best option that needs no approval.

4. **Check the result:**

   ```bash
   git log --oneline                 # one commit per optimization
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

- `--fixture ts-shop | py-logistics`
- `--cases report,write` and `--conditions skill,baseline`
- `--skill-ref <commit>` installs the skill as it was at that commit, to compare versions
- `--model <model>` runs another model
- `--runs N`, `--parallel P`, `--budget USD`, `--out DIR`

Start it detached so it survives closing the terminal:

```bash
nohup setsid evals/run-pilot.sh --fixture py-logistics --runs 3 > /dev/null 2>&1 &
```

Follow `progress.log` in the output directory. Then:

1. `python3 -I evals/session-stats.py <out>` for cost, tokens, and the skill files each session opened.
2. The fixture's probe for each session's final code: `python3 -I evals/probes/py-logistics.py <session directory>`, or `node evals/probes/ts-shop.ts evals/fixtures/ts-shop/src <session directory>/src`.
3. Score each session in a copy of `SCORECARD.md`, using the answer key and the probe's output.

Sessions that hit a usage limit are marked "API ERROR, session invalid" in `progress.log`: rerun them rather than scoring them. Results from past runs are in `results/`.

`evals/trigger-test.sh` checks which prompts load the skill. Besides `--runs`, `--ids`, and `--parallel`, it takes `--model`, `--skill-ref <commit>` (another version of the skill), and `--instructions "<text>"` (written to `CLAUDE.md` in each run directory, to test a project-instruction line).

`evals/token-budget.sh` checks the skill's required loading per mode against budgets without running an agent. Run it after every change to the skill.

## Round 3 plan

Round 3 measures the discovery, verification, systems, and hostile-input work (commit `8054142`) against the skill before it (`3e73373`) and against no skill.

| Step | Command | Sessions |
|---|---|---|
| 1. Static budget | `evals/token-budget.sh` | — |
| 2. Regression on the tuned fixture | `run-pilot.sh --fixture ts-shop --cases report --conditions skill --runs 3`, once with the current skill and once with `--skill-ref 3e73373` | 6 |
| 3. Held-out fixture | `run-pilot.sh --fixture py-logistics --runs 3`, once with the current skill and baseline, once with `--skill-ref 3e73373 --conditions skill` | 18 |
| 4. Second model | `run-pilot.sh --fixture py-logistics --model <another model> --runs 3` | 12 |
| 5. Grade | `session-stats.py`, the probes, and `SCORECARD.md` per session | — |

Run steps 2 to 4 in separate time windows, or with `--parallel 1`, to stay inside usage limits. Round 2 costs suggest about $3.30 per report-flow session with the skill, $1 without it, and under $0.50 per write-mode session: roughly $60 for the whole round on the default model.

## Getting meaningful results

- **Run each fixture three times.** Agents vary between runs; one run proves little.
- **Compare with and without the skill.** Cases that pass either way show where the skill adds nothing. Cases that fail even with the skill show where its wording needs work. Record the difference in the "Skill lift" table of `SCORECARD.md`.
- **Compare agents.** The skill is meant to be agent-neutral. A case that passes in one agent but fails in another usually points to an ambiguous rule.
- **Fix the skill, not the fixture.** When a case fails, change the skill's wording, then rerun. Change a fixture only if the case itself is wrong.

## Adding a case

1. Add the code to a fixture, written as ordinary project code. Do not hint at the answer in names or comments.
2. Keep the fixture's existing tests green. Planted bugs must not be caught by the existing tests.
3. Verify that the trap actually triggers (for example, that the recursion really overflows, or that the alternative really changes output).
   If the trap depends on the platform or library version (for example, `qsort` stability or stack depth), record where you verified it in the answer key.
4. Add the case to the answer key with the expected outcome, pass criteria, and failure signals.
