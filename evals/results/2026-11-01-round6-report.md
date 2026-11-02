# Round 6: report format test, 2026-11-01

- **Change tested:** the two-file report (`OPTIMIZATION-REPORT.md` written once in report mode and never edited afterward; `APPLY-RESULTS.md` written once in apply mode), with one line per field unless the developer has a decision to make. Skill snapshot `round6-report/skill-R` (skill A from round 5 plus this change; still named `complexity-optimizer`, before the rename).
- **Before:** round 5, Test A (2 sessions).
- **Runs:** Haiku 5.5, `java-clinic` report flow, $3 cap. **Only 1 valid session:** session 2 was stopped in its apply turn by the account's monthly spend limit, and the runner marked it invalid and skipped its last turn as designed.

## Results

| | Test A (before) | Round 6 (after), 1 session |
|---|---|---|
| `OPTIMIZATION-REPORT.md` size | about 13,500 to 14,700 tokens | **about 8,500 tokens (about 40% smaller)** |
| Report writing, cost | $0.25 per session (27%) | $0.16 (13%) |
| Session cost | $0.93, $0.94 | $1.19 (harness work $0.41 against $0.28) |
| Probe differences | 0 | 0 (the same speedups: J2 5.8 µs per label, J5 19 ms, J9 52 ms on colliding keys; J3 rate limit kept) |
| Analysis report edited after the report turn | yes (round 4 run 1 overwrote it) | **no:** written once, two small fixes in the same turn |
| Apply results | edits to the analysis report | `APPLY-RESULTS.md` written once in apply, then **6 small edits in the decline turn** |
| Decision completeness | — | all 8 nontrivial items have every field and 3 to 4 candidates; the 2 others use the compact format |
| Behavior changes for review, tried and rejected, scope, test baseline | kept | kept |
| Planted differences reported | 2 of 2 | yes |
| End-to-end share reported | 2 of 2 | **no** |
| A/A run of the differential test | 0 of 2 | no |
| Differential tests kept in the project; report mode changed no source | yes | yes |

## Findings

1. **The format does what it was built to do.** The analysis report is about 40% smaller and is never rewritten, so the round 4 overwrite cannot happen, and report writing fell from $0.25 to $0.16. The session as a whole cost more ($1.19), driven by harness work; with one session and about $0.20 of noise between identical setups (round 5), that difference says nothing either way.
2. **Quality held on the bar set before the run,** with one gap: the end-to-end share was not reported (Test A: 2 of 2). One session cannot tell whether that is the format or noise; the "Performance" field of the apply results format asks for it.
3. **"Write once" was broken in the decline turn,** where the agent recorded the declined approvals in six edits to `APPLY-RESULTS.md`. Answers that arrive after close-out are legitimately new, but they belong in one combined edit.
4. **Evidence is thin.** One session per side is a smoke test, not a measurement. The change stays because it removes a failure by design and shrinks the report as intended; rerun this comparison with two or more sessions when spend allows.

## Next

- Rerun with 2 sessions per side once the account's spend limit allows it.
- Watch the end-to-end share and the decline-turn edits in the next rounds.
