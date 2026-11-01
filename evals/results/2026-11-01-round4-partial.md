# Round 4 (partial): java-clinic on Haiku 5.5, skill only, 2026-11-01

- **Agent:** Claude Code, headless (`claude -p`), model `claude-haiku-5-5`
- **Skill version:** `a571b10` (pinned with `--skill-ref`), with the recommended `CLAUDE.md` loading line in every run directory
- **Runs:** 3 valid with-skill report-flow sessions on `java-clinic` (report, "apply all", decline every approval). **No baseline sessions completed**, so this round measures how Haiku follows the skill, not the skill's lift.
- **Stopped early on purpose,** for cost. The plan was 42 sessions over four fixtures. A with-skill Haiku session now costs about $1, against $0.22 in round 3, because agents can now build, test, and benchmark (see "Harness problems"). The planned round would have cost $25 to $30, well above the $5 to $10 estimate it was approved under.
- **Grading:** `evals/probes/java-clinic.py` on each session's final code, the answer key `answers/java-clinic.md`, and `evals/cost-breakdown.py`.

## Correctness (probe)

**No probe difference in any check in any of the three sessions.** All three changed the same six methods and left the other four alone:

| Case | Change | Probe | Measured by the probe (original → session code) |
|---|---|---|---|
| J2 `CodeFormatter.label` | Index from code to term, rebuilt on `reload`, pattern hoisted | same in 3/3 (reload and first-match-wins kept) | 440 µs → 5 to 7 µs per label; 0 MB retained (no unbounded memo) |
| J5 `roomsNeeded` | Sweep over sorted start and end times | same in 3/3 (back-to-back appointments kept apart) | did not finish in 30 s → 18 to 19 ms at 400 appointments |
| J6 `weeklyRoomsNeeded` | Exact search kept, with pruning | same in 3/3 (odd cycles included) | still exponential, as it must be |
| J7 `minutesUntilOpen` | Precomputed table per calendar | same in 3/3 (every minute of 12 calendars, the Sunday wraparound included) | — |
| J8 `rangeTotals` | Ranges that share a start share one running sum, additions in the original order | same in 3/3 (bit-identical, including `NaN`, infinities, `-0.0`) | — |
| J9 `repeatedVisits` | Sort- or tree-based, worst case O(n log n) | same in 3/3 | 2.7 s → 62 to 69 ms on 60,000 colliding keys (a `HashMap` takes 10 s) |
| J10 `notStocked` | `HashSet` of the stock | same in 3/3 (order and repeats kept) | — |
| J1, J3, J4 | Not changed | same | J3 rate limit kept: at most 8 requests per 10 pauses |

## Scores against the answer key

| Case | Run 1 | Run 2 | Run 3 | Notes |
|---|---|---|---|---|
| J1 roster N+1 | ~ | ~ | ~ | All three found `fetchAll`, the 500-id limit, and the first-missing-patient contract, then held the change for review as unverifiable instead of applying the contract-preserving version |
| J2 bounded memory, reload | P | P | P | Index, not memo |
| J3 rate limit | P | P | P | Batching listed under "Behavior changes for review" (all-or-nothing batches), rate limit treated as a contract |
| J4 control | P | P | P | Listed as not worth changing |
| J5 special case | P | P | P | Sweep; run 2 labeled Ω(n log n) "proven", which overstates the bound (Ω(n) is what can be shown) |
| J6 honest hardness | P | P | P | All three named circular-arc coloring NP-complete (Garey et al. 1980) and marked the citation "not checked," as the skill requires |
| J7 verification | P | P | P | Exhaustive over all 10,080 minutes per calendar, with the level scoped to the calendars checked |
| J8 floating point | P | P | P | The bit-identical method; prefix sums listed as a behavior change for review (runs 2 and 3) |
| J9 hostile input | P | P | P | Exposure stated as untrusted input; worst-case-safe structure |
| J10 control | P | P | P | |

Report-flow pass rate (partial = half): **0.95** (28.5 of 30). There is no baseline in this round, so this says nothing about lift; it says Haiku with the skill made no correctness mistake on this fixture.

## Workflow

| Check | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| Stated the mode at the start | yes | in its first visible text only at the end | stated at the end ("Report mode is done") |
| Report mode changed no source files | yes | yes | yes |
| Nothing committed (commits declined) | yes | yes | yes |
| Ran the existing suite before and after | yes | yes | yes |
| Differential tests kept in the project | yes (`DifferentialTest.java`) | yes (`EquivalenceTest.java`) | **no:** 4.65 million checks in a harness under `/tmp` against the original copied from git, nothing left in the project |
| Check the check: planted differences | partial (mutants for 2 of 6 changes) | **yes, 7 of 7 caught** | partial (1 planted fault, `RoomPlanner`) |
| Check the check: A/A run | not reported | not clearly reported | not reported |
| Verification level reported per item | yes | yes | yes |
| End-to-end share (rule 8) | stated as not measured | missing | missing |
| Report written in few passes | 5 writes, **but the apply turn replaced the 40 KB analysis with an 8.8 KB close-out** | 5 edits, analysis kept | 4 edits, analysis kept |

## Findings

1. **No correctness failures on the tuning fixture.** Every trap a baseline was expected to fall into (unbounded memo, last-wins index, back-to-back intervals, interval sweep on arcs, Sunday wraparound, prefix-sum rounding, hash collisions on record keys, rate limit) was avoided in all three sessions. Without a baseline, whether the skill caused this is not measured.
2. **Regression from the "write the report once" instruction.** Run 1 rewrote the whole report at close-out and lost the analysis, including "Behavior changes for review." `REPORTING.md` said to fix mistakes "in one combined edit, or rewrite the file"; the wording now says close-out only adds to the report and a rewrite must keep every section.
3. **The instruction cut edits but not cost.** Report edits fell from about 15 per session (round 3) to 4 or 5, but report writing rose to 23% of the cost, because the reports are long (about 450 lines, 46,000 output tokens per session). Long reports, not edit count, are now the cost.
4. **Check-the-check is followed unevenly.** One run planted a difference in every changed item; the other two planted one or two; none reported an A/A run of the differential test.
5. **The end-to-end share (rule 8) is ignored.** No run reported what share of the whole operation the changed code took.
6. **Over-caution on J1.** All three treated the contract-preserving batch as unverifiable. It is verifiable with a fake directory, which is how the fixture's own test works.
7. **One overstated lower bound** (run 2, J5).

## Cost and permissions

- Mean $0.95 per session (`cost-breakdown.py`): own harnesses and benchmarks 36%, report writing 23%, reading 10%.
- 25 of 325 tool calls (8%) refused by permissions, mostly Claude Code's own checks on commands with shell variables, after the allowed-command fixes below.
- Spent today on round 4 work, all attempts: about $4.30 (35.6 million input tokens, 92% of them cache reads; 627,000 output tokens).

## Harness problems found and fixed

- **Permissions.** The first attempt refused ordinary commands (`cd … && bash test.sh`, `mkdir`, `python3`), and `javac` was not on `PATH`, so Java sessions could not run anything. Round 3 had the same problem in milder form: 14 to 21% of shell commands refused (the Python and TypeScript fixtures still allowed `python3` and `node`, so its measurements stand, but its costs were inflated). `run-pilot.sh` now allows a common set of commands, puts the JDK on `PATH`, and allows scratch files under `/tmp`; `cost-breakdown.py` flags a session group whose refusal rate exceeds 5%.
- **Loading line.** `run-pilot.sh --instructions` writes the README's recommended `CLAUDE.md` line into with-skill run directories (committed in their initial commit), so write mode can be measured once loaded.
- **Stall.** One baseline session stopped receiving output for 25 minutes. Stopping it ended the whole `xargs` batch. Not fixed yet: the runner needs stall detection and sessions that survive a stopped neighbor, and a cost cap that stops starting sessions past a set amount.

## Not run

Baselines for java-clinic; all of rb-clinic (held out), py-logistics, and ts-shop; every write-mode case. The fixtures and probes are ready for them.
