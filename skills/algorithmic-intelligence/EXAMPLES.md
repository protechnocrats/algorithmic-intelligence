# Worked Examples

One short example per mode, showing the shape of a run: the request, what the agent does, and what it hands back. They illustrate the files that govern each step; where the two differ, the governing file wins. Code, names, and numbers are invented.

**Contents:** Report mode · Apply mode · Write mode

## Report mode

**Request.** "The orders export page times out for our biggest customers. Can you find out why?"

**What the agent does.**

1. First line: `Mode: report. A symptom with no code named, so I find and explain the cause and change nothing.`
2. Translates the request ("Translate the request" in `SKILL.md`): goal is a page that finishes; traced from the route `/orders/export` to `OrderExporter.build`; sizes from `config/limits.yml` (10,000 orders per page) and a comment saying 500 (both reported, the larger used); constraint "partners diff the file", so row order is contract; problem underneath is a join of orders to customers.
3. Opens `WORKFLOW.md`, `REPORTING.md`, and `languages/PYTHON.md` before reading code. Phase 1 finds pytest and no profiler; the test suite is not run ("not run (report mode)").
4. Phase 2: for each row, `build` calls `customers.find(id)`, a linear scan over a list: O(n·m) along the call chain, hot (per request), reached from the route. Also notes a bug: a `None` customer is skipped silently.
5. Phase 3: audit of `customers` (`DATA-STRUCTURES.md`): dominant operation is lookup by id, now O(m), best is a dict built once, switching. Lower bound Ω(n + m) (must read both). Candidates: dict index (chosen, at the bound); a database join (changes the query, a behavior risk); sorting both and merging (reorders output, which partners diff). Prediction: 10,000 × 2,000 comparisons → about 12,000 operations, roughly 200× on the loop, about 60% of the request (estimated). Behavior traps walked: duplicate ids in `customers` (the scan returned the first; the index must keep the first). Verification plan: a pin test through the route on a throwaway SQLite database, a seeded comparison against a verbatim copy of `build`, an assumption pin that ids are unique or the first wins, a planted difference (keep the last duplicate).
6. Phase 4: the result is one item, so it is presented in the conversation, with the "Request as understood" header, the bug log entry, and the closing lines.

**What the developer gets.** The item in the compact format, "Bugs noticed: BUG-1, `None` customer skipped silently", the question "shall I apply item 1?", and "Complexity: O(n·m) → O(n + m) expected [worst case O(n·m) if ids are attacker-chosen; they are internal], lower bound Ω(n + m) because every row and customer must be read". Nothing in the project changed.

## Apply mode

**Request.** "Go ahead with item 1."

**What the agent does.**

1. First line: `Mode: apply. Item 1 approved; it keeps behavior, so a general approval covers it.` Opens `APPLYING.md` and `DIFFERENTIAL-TESTING.md`.
2. Settles commits (asks once; the developer says no), then runs the baseline suite the way the project documents it, after reading `pytest.ini` and `conftest.py`: 212 passed.
3. Writes the tests named in the plan the way the nearby tests are written, before touching `build`: the pin test through the route; `legacy_build`, a verbatim copy, compared with `build` on edge cases (empty, one customer, duplicate ids, a missing id) and 2,000 seeded cases; the assumption pin. They pass on the unchanged code; the A/A run passes; the planted difference (an index that keeps the last duplicate) is caught.
4. Changes `build` to build the dict once, keeping the first occurrence per id and the `None` skip (the bug stays, rule 4). Signature unchanged.
5. Differential tests and the suite pass. Benchmark at 10,000 × 2,000: 1.9 s → 11 ms (measured, median of 20, A/A noise 3%); growth exponent 1.0 against the predicted 1; request time 3.1 s → 1.3 s (measured through the route).
6. Writes `APPLY-RESULTS.md` once, offers to keep the tests, deletes the mutant copy, confirms from `git status` that only intended files changed.

**What the developer gets.** The apply summary: "Applied: item 1 (verified: level 1, 2,000 seeded cases, planted difference caught)", complexity and data-structure lines, "Bugs noticed: BUG-1 preserved", "Behavior changes: none", "Commands not run: none", "Test suite: 212 passed before and after", nothing committed, and the list of changed files.

## Write mode

**Request.** "Add an endpoint that returns each customer's lifetime spend. We have about 2 million orders."

**What the agent does.**

1. First line: `Mode: write. New endpoint; existing code changes only as far as the request needs.` Opens `WRITING-NEW-CODE.md` and the language file.
2. Sizes the work: 2 million orders (request), about 40,000 customers (from the customers table's size in a migration comment, labeled estimated), called per dashboard load. Problem underneath: a grouped sum.
3. Audits the design (`DATA-STRUCTURES.md`): a dict from customer id to running total is O(n) with O(c) memory, about 40,000 × 100 bytes = 4 MB per process. Chooses an aggregate query in the database (`SUM GROUP BY`, "Push work to the right layer" in `ALGORITHM-ARSENAL.md`) over loading 2 million rows, with the nulls, currencies, and refund rows handled exactly as the existing report code does; a cache is not added, since no size or latency requirement asks for one and other processes write orders.
4. Finds that the only existing helper, `Orders.all()`, loads every row; it is not changed. The endpoint reads the aggregate directly, and the helper is reported as a bottleneck for other callers.
5. Tests: a slow reference (a Python loop over generated orders) against the endpoint on edge cases and seeded data, including refunds and a customer with no orders; a round trip against rows the existing writer produced.

**What the developer gets.** The endpoint, its tests, and "Performance decisions": one entry with size, data structures, approach, memory, and "Verified: level 1 against a reference version"; the `Orders.all()` item as a proposed optimization awaiting a decision; and the closing lines.
