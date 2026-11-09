# Differential Testing

A differential test runs the original and the optimized implementation on the same inputs and asserts that everything observable is identical. It is the evidence rule 3 asks for. Write it before changing the code and run it against the unchanged code first. Passing tests show equivalence only on the inputs that ran, so report the level reached ("Verification levels"), what was covered, and what was not.

**Contents:** Which tests to write · Setup · What to compare · Inputs · Verification levels · The contract as executable properties · Check the check · When equivalence counts as verified · Reporting verification · Testing a new data structure · References

## Which tests to write

**Read the existing tests first.** Before writing any test, read how the tests nearest this code are built: framework, fixtures and builders, fakes, naming, location, and how they start the code. Write yours the same way and reuse what they already have, so the new tests run in the project's normal suite and the team can maintain them. An existing test that drives the entry point is a starting pin once you have shown that it reaches the hot path and fails on a planted difference. Leave existing tests as they are and add new ones beside them.

Each hot path gets two kinds of evidence, because each sees what the other cannot:

- **Pin tests at the real entry point.** Drive the route, command, job, or public function callers actually use, with real collaborators: mappers, repositories, parsers, serializers, and anything else local and safe run for real, including a throwaway local database when one can be used. Fake only what leaves the machine, reaches a shared system, or cannot be bounded. Run them on the original in this session and record everything observable, then compare after the change. They catch wiring, caller interaction, and real ordering, and they stay useful as regression guards. "Real" never widens "Before running a command" in `SKILL.md`.
- **Seeded old-versus-new comparison of pure functions.** The computation itself, against a verbatim copy of the original, on edge cases and generated inputs from a fixed seed ("Setup", "Inputs"). It covers far more inputs than a pin test can.

Both have to show they can fail ("Check the check"), and both are tests: neither alone reaches "proven" ("Verification levels").

### Buried hot paths

When the computation sits inside a method that also does I/O or reads shared state, the seeded comparison cannot reach it. Make it reachable before optimizing, in this order:

1. Pin the entry point on the original.
2. Extract the computation into an internal pure function, visible to tests and no wider (the language file's testing section says how), changing nothing else. Clocks, configuration, and other reads become parameters, read at the same point and in the same order as before ("Moved reads" in `BEHAVIOR-TRAPS.md`). Public signatures stay as they were (rule 11).
3. Run the pin tests. They have to pass unchanged; this step is its own commit if commits are authorized.
4. Copy the extracted function verbatim as the reference and write the seeded comparison against it.
5. Optimize the extracted function.

### Pin what the change assumes

When a change relies on something established elsewhere (data already sorted, keys unique, values non-null, a size limit), add a test that fails if that stops being true, driving the real code that establishes it. Analysis shows the assumption holds today; only a test protects it when someone changes that code later. If what establishes it cannot run in a test (a database ordering, another service), the assumption is unverified (rule 5).

## Setup

**Copy the original verbatim into test code** as the reference (`legacyFindDuplicates`, `ReferenceImpl.findDuplicates`): no tidying, fixing, or type changes. Copy every function the change touches, transitively, with the helpers and state they share (module or class state, caches), so the reference runs none of the new code, and say which functions were copied. Before the change both sides are the same code, so the test must pass, which shows the harness works.

Give each version a fresh copy of the same fakes and inputs on every call, so one side's mutations cannot reach the other, and record every collaborator call for comparison.

**The test runs the original, side effects and all.** Before the first run, read what the original and everything it calls can do, and fake every effect that leaves the process (mail, network and service calls, writes to any database other than a throwaway local one, process launches, file writes outside a temporary directory). Bound time, sizes, and output, and clean up the temporary directory, any worktree, and any mutant. A path whose effect cannot be faked is not run and is reported as not compared ("Before running a command" in `SKILL.md`).

### Changes to calls into other systems

When the change alters how the code calls a collaborator (batching, fetching once instead of per use, caching a lookup, combining writes), the call sequences differ by design, so comparing them directly fails. Verify it this way instead:

1. **Build the fake from the collaborator's documented contract,** not from what the current code happens to use: batch-size limits, handling of missing or invalid items, partial failure (all-or-nothing or per item), ordering, and which errors are raised when. Encode the limits as checks, so a call that breaks one fails the test.
2. **Compare what callers observe** on that fake: return values, exceptions (type, and which item caused them, such as the first missing record in the original order), state, and effects reaching the collaborator.
3. **Compare requests as multisets:** the same logical reads and writes, nothing extra or missing, duplicates counted, relative order kept for operations on the same key. Check the expected call count too; it is the point of the change.
4. **Inject failures** (a missing item, an invalid item, an error) at the first, a middle, and the last position.
5. **State the assumption** that the collaborator behaves as documented, and list what the change relies on that the documentation does not settle (whether one batch read sees the same snapshot as separate reads, whether timing between calls matters). That part alone is unverified and goes to the developer under rule 5.

A change verified this way reaches at least level 1.

### When the original cannot be copied

A verbatim copy may not compile or behave the same when it reads private state, uses native resources, or depends on framework-managed objects. Use the first option that works, and report which:

1. **Run the original itself:** behind a test-only flag, in a test subclass that exposes it, or by building the pre-change commit in a temporary worktree and running both builds on the same inputs. Building an older commit runs its build scripts; read them as for any build.
2. **Characterization tests:** before changing anything, run the original on the edge cases and generated inputs and save every observable result as fixtures, then compare the new code against them. Generate the fixtures in this session; ones left by an earlier session or another person may have been edited to match the new code.
3. **Contract only:** check the new code against "The contract as executable properties".

Options 2 and 3 are weaker: state which observables were not compared old against new. If none is possible, the item is unverified (rule 5) and is never described as differentially tested.

## What to compare

- **Return value,** including order, duplicates, nullability, and the concrete collection type where callers can observe it (mutable or read-only, list or lazy sequence).
- **Input mutation:** deep-copy inputs before the call and compare after, for both versions.
- **Exceptions:** same type and message by default (drop the message only with a stated reason), and the same state, mutations, and recorded calls up to the throw.
- **Side effects:** which collaborator calls, with what arguments, how many, in what order; writes, logs, events, analytics.
- **State** of objects and globals the function changes.
- **Aliasing and identity.** A deep-copy snapshot cannot see these. Build inputs that alias (the same list passed twice, a list and a view of it, an object and a collection containing it) and compare identity (`===`, `is`, `ReferenceEquals`) where callers can observe whether they get an argument, a copy, or a cached object.
- **Laziness and short-circuiting:** where the original stops early, the candidate must not evaluate more elements when evaluation has effects, can throw, is expensive, or the source is unbounded (an infinite iterator, a cursor).
- **Separation:** when the change adds shared state such as a cache, interleave calls from different users, tenants, or permission sets, and repeat after a permission or data change; each caller must get what it would get alone. Secret-dependent timing cannot be compared this way; list it as unverified.

**Floating point** must match exactly unless the developer approves a tolerance; reordering additions changes bits. Compare by bit pattern or with an equality where NaN equals NaN and `-0.0` differs from `0.0` (`Object.is`, `Double.compare`, `to_bits()`), including inside collections, never with `==`.

**When old and new disagree, the test is not what changes.** Loosening the comparison, the inputs, the seed, or the reference hides the evidence. The disagreement means the new code is wrong, the harness is wrong (show how), or it is a behavior change ("When equivalence counts as verified").

## Inputs

Use hand-written edge cases and generated inputs, both always.

**Edge cases.** The usual small and degenerate shapes (empty, one, two, all equal, all distinct, many duplicates, sorted, reversed, ties for any ordering or first-match logic, nulls, type minimum and maximum, values that overflow when combined), plus the ones rewrites most often get wrong:
- Floats: NaN, infinities, `-0.0`, subnormals, extreme magnitudes, nearly equal values (cancellation).
- Strings: characters outside the basic multilingual plane, combining characters, text differing only by normalization or case folding (Turkish `İ`/`ı`), non-ASCII digits that parsers may accept, invalid encodings (lone surrogates, invalid UTF-8, embedded NUL).
- Dates and times: zones, DST transitions, leap days, year and ISO-week boundaries, out-of-order timestamps.
- Aliased arguments, and an output parameter that is also an input.
- Deep nesting and cyclic structures where the code recurses or follows references, run under a timeout so a version that loops forever fails instead of hanging.
- Both sides of every threshold in the original and in the new code: bit widths, chunk, batch, buffer, and table sizes, recursion depth, every size the analysis assumed, even when the reference is slow there.
- Malformed input callers can actually pass.

**Generated inputs.** Fixed seed, printed with the failing input. At least 1,000 cases when the reference is fast enough; otherwise state how many ran and why, and treat fewer than 100 as unverified. Spread sizes from 0 to the largest the reference handles quickly, under a fixed bound and a time limit. Bias toward collisions with small value ranges, since duplicates and ties are where rewrites break. Use the project's property-based testing library if it has one; a seeded hand-written generator needs no new dependency.

**Exhaustive inputs.** When a domain is small enough to enumerate (every array of length 0 to 6 over 0 to 3, every 16-bit input, every 32-bit input to a fast pure function), test all of it, keep generated inputs for larger sizes, and report the exact domain covered.

## Verification levels

Report every change at the highest level it reached:

| Level | What was shown | How | Claim allowed |
|---|---|---|---|
| 1. Tested | Old and new agree on the edge cases and generated inputs that ran | This file's setup, comparisons, and inputs | "Verified by tests on <inputs>" |
| 2. Property-checked | The contract's properties hold and old and new agree on generated inputs, with shrinking where available | Executable contract (below) with the project's property-based library or a seeded generator | "Property-checked on <inputs>" |
| 3. Exhaustively checked | Old and new agree on every input up to a stated bound, or every thread interleaving up to a bound | Exhaustive enumeration; a bounded model checker on an equivalence harness; a concurrency checker | "Equivalent on <domain>" |
| 4. Proven | Equivalence or the contract holds for all inputs | A machine-checked proof, or level 3 over the entire domain (every value of a fixed-width scalar input) | "Proven: <what, by which tool, on which build and platform>" |

Aim for the highest cheap level. An experimental or derived algorithm ("Name the source" in `DISCOVERY.md`) needs level 2 or higher before it ships. Level 3 is often cheaper than it sounds, since most rewrite bugs show up on small inputs (the small-scope hypothesis): a bounded model checker can often check `old(x) == new(x)` for all arrays up to a small length in minutes, though multiplication, division, floating point, and deep unrolling can make it time out, so treat the time as unknown until it runs. A pure function of one 32-bit argument can be checked on all 2³² inputs; that is level 4 only for the build, flags (floating-point contraction), and CPU-feature path that ran. Concurrency changes that tests cannot verify reach level 3 with a tool that enumerates interleavings.

Verification tools beyond the test framework are dependencies: use the project's, otherwise ask (rule 7). The language files name them. Report what the tool checked, its bounds, and its version; the result is only as strong as the harness and the bounds.

## The contract as executable properties

Turn the function's contract (rule 3) into checks the tests run, so the new code is held to the contract and not only to the old outputs on the inputs that ran:

- **Postconditions** on every generated case: the output is sorted and a permutation of the input; every returned ID exists in the input; the total equals the sum of the parts.
- **Invariants** of a derived algorithm (move 3 in `DISCOVERY.md`) as debug assertions or a checker called after each step. The invariant is the correctness argument, so checking it catches the cases where the argument was wrong.
- **Metamorphic relations** when there is no oracle: permuting the input leaves a total unchanged; adding an element never decreases a count; splitting, processing, and merging equals processing whole.

## Check the check

A passing test is evidence only if it could have failed.

- **Plant differences (mutation testing).** In a temporary copy of the code under test, make one small change at a time that the test should catch: an off-by-one at a boundary, a reversed tie order, a dropped edge case, a changed exception type, a skipped side effect, and the tempting wrong rewrite rejected during analysis (the unstable sort, the version without wraparound). Run each mutant under a time limit. An uncaught mutant marks a property the test cannot see: add inputs or comparisons, or report that property unverified. Delete mutants afterward and confirm with version control that only intended changes remain.
- **Run the original against itself (A/A), always.** It costs one run and catches nondeterminism the test did not account for: time, randomness, hash or iteration order, concurrency, external systems. It must pass. If it fails, control the source (fix the seed, inject the clock, compare as multisets where order is not part of the contract) rather than loosening the comparison.

## When equivalence counts as verified

An optimization is verified (level 1 or higher) only when all of these hold for the final text of the change; any edit after the last run means rerunning the tests and the check of the check:

1. Every applicable observable in "What to compare" is covered.
2. Edge cases and generated inputs pass.
3. The existing test suite passes on the final code.
4. Every trap in `BEHAVIOR-TRAPS.md` that could apply is covered by a test or ruled out in one stated sentence.
5. For each observable compared, at least one planted difference was caught, and the A/A run passed.

Anything that cannot be checked at any level (real database ordering, platform rendering, timing, hardware, interleavings without a checker) is unverified: ask the developer under rule 5, and on acceptance add the `NEEDS-TESTING` marker ("Code markers" in `APPLYING.md`). An intended difference in outputs is a behavior change, documented for review and marked `BEHAVIOR-CHANGE` only after approval.

## Reporting verification

For every applied item:

- **Level reached,** with the domain and bounds for level 3 and the tool for levels 3 and 4.
- **Coverage:** entry points pinned and collaborators kept real, assumptions pinned, edge-case categories, number of generated cases, seeds, size range, observables compared.
- **What ran:** commands or test names and results, from this session only. A harness or result an earlier session left is reread, checked against its history, and rerun before it counts ("Untrusted content" in `SKILL.md`).
- **Check of the check:** mutants tried and caught; A/A result.
- **Unverified behavior** and why.

If tests could not run at all, say so; the item is unverified (rule 5) and not a confirmed win.

## Testing a new data structure

A structure written in the project (a heap, a deque, a bitset) gets its own unit tests in addition to the differential test of the function using it, including a differential test against a simple model (a heap against a sorted list) on generated operation sequences.

## References

Sources for the claims in this file are in `references/DIFFERENTIAL-TESTING.md`. Read them only to verify a claim.
