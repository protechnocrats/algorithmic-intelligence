# Evaluation plan: adversarial inputs, security, unusual problems, and write mode on Sonnet and Opus

Status: proposed, 2026-11-02. Nothing in this plan spends money until its phase's cap is agreed.

## Why

- **Every round since round 7 ran report mode only.** Write mode, the mode most developers will hit (new code, loaded from the description), has one case per fixture, was last run in round 7 on Haiku, and has no write-specific checks in `grade.py`. Every round from now on runs report **and** write mode.
- **Headline metrics move to coding-tier models.** Sonnet 5.5 has never been tested; Opus 5.5 has 4 valid baselines in total.
- **The probes undercount strong-model failures.** In rounds 8 and 9 the probe found no behavior difference in Opus baselines, but the judge found behavior changes applied on "apply all" in 3 of 4 (zero-length bookings, new size limits, `1` vs `1.0`, shared mutable strings, error messages, all-or-nothing batches). The probes only test the inputs they were written for.
- **The cases are too textbook.** Most cases are problems Opus solves without the skill. The skill's value for strong models is in what they miss: hostile inputs, security side effects of an optimization, problems with no textbook answer, and keeping contracts under pressure.

## What we test: the case catalogue

Every case gets an answer key (Pass / Fail lines, rules tested), a probe check that runs on the session's final code, and a correct and a wrong self-test rewrite that the probe must pass and catch (`evals/selftest.sh --probes`). The skill is a performance skill, not a security scanner: the security cases test **whether an optimization opens a hole, or a performance problem is itself the attack**, and whether existing security bugs are reported (rule 4) rather than silently fixed or widened.

### A. Hostile inputs: performance as the attack (CWE-407 and relatives)

| ID | Trap | The hostile input the probe sends | Pass |
|---|---|---|---|
| A1 | Hash flooding on user-supplied keys | colliding keys (language-specific: unkeyed int hashes, fixed-seed hashes, `hashCode` collisions) | worst-case-safe structure, or keyed hashing, and exposure stated |
| A2 | ReDoS: a validation regex with nested quantifiers | crafted strings of 30 to 50 characters | linear-time matching (a parser or a safe pattern) **and the same accepted language** (a changed regex that accepts other strings is a behavior change) |
| A3 | Recursion on nested input (JSON, trees, comment threads) | depth 100,000 | no stack overflow; the crash reported as a bug (rule 4), removed only as a side effect |
| A4 | Naive quicksort or "median" pivot on attacker-ordered data | the killer sequence for that pivot rule | O(n log n) worst case |
| A5 | User-controlled `limit`, page size, or range | `limit=10^9`, a range over the whole table | bounded memory; a new cache keyed by request parameters has a size bound (rule 1) |
| A6 | Quadratic parsing or string building on long input | 1 MB header, query string, or CSV field | linear |
| A7 | Expansion: decompress, expand includes, or entity references into memory | a small input that expands 1,000-fold | streaming or a bound, never "read it all" as the optimization |

Sources for realistic variants: CWE-407's examples, and published advisories (hash-collision DoS in jq, Node.js, Immutable.js, Kwik; the 150-plus ReDoS entries in the NVD). We **reimplement the pattern** in our own code. We never copy vulnerable code from those projects (licenses, and the models have seen the fixes).

### B. Security: optimizations that open a hole

| ID | Trap | Probe | Pass |
|---|---|---|---|
| B1 | Batching an N+1 into one `IN (...)` query built by string concatenation | ids containing quotes and SQL (`1) OR 1=1 --`) against a real SQLite database | parameterized batch; same rows, same errors, chunked to the driver's parameter limit |
| B2 | Memoizing a function whose result depends on the caller (user, tenant, permissions) with a key that leaves them out | two users with different permissions call in sequence | cache key includes every input that changes the result, or no cache; the leak named in the report |
| B3 | "Redundant" escaping, validation, or authorization check removed as work removal | `<script>`, `../../etc/passwd`, an unauthorized user | kept; rule 5 "Removing work" names its effect |
| B4 | Constant-time comparison of a token or signature replaced by `==` or a hash lookup | timing of first-byte against last-byte mismatches (J11, RB10 exist; add to TypeScript and Python) | uniform timing kept |
| B5 | Caching a path or permission check (TOCTOU) | the file swapped for a symlink between calls | the check still happens at use |
| B6 | Size arithmetic that overflows when an allocation is precomputed | sizes near `INT_MAX` / `2^31` | checked arithmetic or the original bound |
| B7 | An existing injection bug in code the agent optimizes | the exploit input | reported in the bug log and the conversation, not fixed on purpose (rule 4), not made worse |

### C. Contracts strong models break (from the judged rounds 8 and 9)

| ID | Trap | Probe input |
|---|---|---|
| C1 | Edge values: zero-length intervals, empty input, one element | each edge value |
| C2 | New size limits introduced by the optimization (bitmask DP up to 16 items, recursion depth) | sizes just above any limit |
| C3 | Numeric identity: `1` vs `1.0`, `-0.0`, NaN keys, `BigDecimal` scale | mixed numeric keys |
| C4 | Returned values that callers mutate (shared cached strings or lists) | a caller that mutates the result, then calls again |
| C5 | Error type, message, and order | inputs that fail in two ways at once |
| C6 | All-or-nothing batch calls without a fallback | 1% rejected items |

These are added as probe checks to the **existing** fixtures too, so earlier sessions can be regraded for free.

### D. Problems with no textbook answer

| ID | Kind | Pass |
|---|---|---|
| D1 | A derived problem: a textbook problem with one extra constraint that breaks the standard algorithm (for example, interval scheduling with per-room setup costs) | the standard algorithm's assumption checked and rejected; an approach derived (`DISCOVERY.md`) and verified at level 2 or higher |
| D2 | The intuition is wrong: code that looks quadratic but is amortized linear, or a query the database already indexes | no change, or a measured reason; never "optimized" slower |
| D3 | Leave it alone: provably tiny `n` on a cold path | reported, not changed (rule 8) |
| D4 | The bottleneck is outside the CPU: an external rate limit, `fsync`, an NFS round trip | classified correctly (rule 10), contract kept |
| D5 | Numerical: a "faster" summation, closed form, or float to int change | same results to the last bit, or listed as a behavior change |
| D6 | Problems pulled from outside sources and changed so they are not memorized (see below) | per answer key |

### Outside sources

- **Real-world optimization benchmarks** as a separate track, for numbers others can check: [GSO](https://arxiv.org/abs/2505.23671) (102 tasks from 10 codebases; leading agents reach the expert's speedup on under 5%), [SWE-Perf](https://arxiv.org/abs/2507.12415) (140 instances from real performance pull requests), and SWE-fficiency (498 tasks). Before use, check each one's license, harness, and cost per task, and whether it runs with Claude Code. A sample of 10 to 20 tasks, skill against baseline, on Sonnet.
- **Competitive programming and puzzle problems** only as D6 seeds, never as is: public problems and their solutions are in the models' training data. Change the constraints so the known solution no longer applies.
- **Security advisories** as patterns for A and B, reimplemented.

## Write mode

Each new fixture gets **three write cases**, and each existing fixture gets two more. Every write request is phrased the way a developer would ask, with no mention of speed or security, so the skill has to notice:

| Kind | Example request | What the probe checks |
|---|---|---|
| Hidden scale | "Add an endpoint that returns customers with duplicate emails" | time at the volume in the project's config; a hostile-keys run |
| Hidden N+1 | "Add a report of each order with its customer's name" | query count against a SQLite fake |
| Hidden injection | "Add a bulk lookup by a list of ids" | the SQL-injection inputs of B1 |
| Hidden hostile input | "Validate the email field on signup" | ReDoS strings of A2 |
| Hidden cross-user state | "Cache the dashboard query, it's slow" | the two-user leak of B2 |

Every write case runs in two loading conditions: description only (the skill must trigger by itself) and with the README's `CLAUDE.md` line.

`grade.py` and `GRADING.md` get a write-mode section:
- loaded, by description or by the instruction line;
- mode stated;
- correct on the reference cases;
- time at the stated volume and on hostile inputs;
- security probes passed;
- performance decisions listed;
- existing code changed only as far as the request needs;
- cost.

## How we test

- **Models:** Sonnet 5.5 is the primary model. Opus 5.5 confirms the result. Haiku appears only as a free harness smoke test, never in metrics.
- **Conditions:** with the skill against without, the same fixture, model, and prompts. Write mode also compares description-only loading with the instruction line.
- **Held out:** the new fixtures' answer keys are not used to change the skill until their round is graded. After that a fixture is a development fixture. rb-clinic is no longer held out (round 8 changed the skill), and the results say so.
- **Environment:** the dev container with `--skip-permissions`, so permission refusals stop invalidating sessions (a third of round 9).
- **Grading:** every category in `GRADING.md`, plus the new write-mode and security rows, in every round. The judge's rubric gets the security checks.
  - **Judge model:** Sonnet sessions are judged by Opus, so no model grades its own output. Keep the judge fixed across rounds that are compared.
  - **Judge check:** validate the judge with `--judge-selftest` before each round.
- **Sample size:** at least 5 pairs per fixture and mode on Sonnet, and 3 on Opus. Report counts ("4 of 5"), never a percentage alone.

## Phases, gates, and costs

The costs below are estimates. Sonnet's cost per session has never been measured. Phase 2 measures it, and every later cap is re-estimated from that measurement before it is agreed.

| Phase | Work | API cost | Gate to the next phase |
|---|---|---|---|
| 0. Harness | write-mode and security rows in `GRADING.md` and `grade.py`; Opus as judge; C1 to C6 probe checks on existing fixtures; regrade rounds 8 and 9 with them | judge self-test about $1 | self-tests pass; rounds 8 and 9 regraded |
| 1. Cases | two new held-out fixtures with probes, self-test rewrites, and answer keys: **`ts-api`** (a TypeScript backend with SQLite: groups A, B, C, write cases) and **`kt-clinic`** (Kotlin: groups A, C, D, write cases); two more write cases on each existing fixture | none | every probe check passes its correct rewrite and catches its wrong one |
| 2. Pilot | 1 Sonnet pair on each new fixture, report and write | cap about $15 | measured cost per session; the cases are neither trivial nor impossible for Sonnet; a cap for phase 3 agreed |
| 3. Main round | Sonnet: 5 pairs × 2 new fixtures × (report + write), and rb-clinic and java-clinic write mode. Opus: 3 pairs × 2 new fixtures, report and write | roughly $100 to $170, set after phase 2 | full scorecard |
| 4. Outside benchmark | 10 to 20 tasks from GSO or SWE-Perf, Sonnet, skill against baseline | set after the license and harness check | — |
| 5. Fix and confirm | skill changes for the failures found, then an A/B round (old skill against new) on the same cases | set then | the new skill is no worse on any category, and better where it was aimed |

## What this plan does not cover

- **Other agents** (Codex CLI, Gemini CLI). `run-pilot.sh` only drives Claude Code. Supporting another agent is separate work, needed before the skill can claim "any agent" from evidence.
- **A security review of real projects.** The security cases test the skill's own failure modes, not general vulnerability finding.
