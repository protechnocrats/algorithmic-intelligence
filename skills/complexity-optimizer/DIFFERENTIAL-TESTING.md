# Differential Testing

A differential test runs the original implementation and the optimized implementation on the same inputs and asserts that every observable result is identical. It is the evidence required by rule 3. Write it before changing the code, and run it against the unchanged code first.

Passing differential tests are strong evidence, not proof. They show equivalence on the inputs that ran, not on every possible input. Report the verification level reached (see "Verification levels" below), what was verified, and what was not.

## Setup

1. **Copy the original verbatim into test code** as a reference implementation, for example `legacyFindDuplicates` or `ReferenceImpl.findDuplicates`. Do not tidy it, fix it, or change its types. It lives only in test sources, never in production code.
2. **Call the production function** as the candidate. Before the optimization, the candidate and the reference are the same code, so the tests must pass; this shows the harness works.
3. **Keep the reference until the developer decides.** After the change is accepted, the developer may keep the differential test as a regression guard or delete the reference. Ask; do not decide for them.

If the original depends on collaborators (a repository, a clock, a network client), give both versions the same fakes, and record every call each version makes so calls can be compared.

### When the original cannot be copied

Sometimes a verbatim copy will not compile or will not behave like the original: it reads private state of its class, depends on native resources, or relies on objects that a framework creates and manages. Do not give up on the comparison, and do not silently compare against something weaker. Use the first option that works:

1. **Run the original itself.** Keep the original code reachable in the test build: under a different name in the same class (in test or debug code only), behind a test-only switch, or by building the pre-change version from version control (a separate worktree or checkout of the commit before the change) and running both builds on the same inputs.
2. **Record the original's outputs first (characterization tests).** Before changing anything, run the original on the edge cases and generated inputs, and save every observable result (return values, mutated inputs, exceptions, recorded collaborator calls) to test fixtures. After the change, run the new code on the same inputs and compare with the saved results. This covers only the inputs you recorded.
3. **Compare against the contract.** If neither works, check the new code against the executable contract ("The contract as executable properties," below) without an old-versus-new comparison.

Report which option you used. Options 2 and 3 are weaker than a live differential test: state exactly which observable behaviors were not compared old against new. If no option was possible, the item is unverified: follow rule 5, and never describe it as differentially tested.

## What to compare

Compare all of these, not only the return value:

- **Return value**, including element order, duplicates, nullability, and the concrete collection type when callers can observe it (mutable versus read-only, list versus lazy sequence).
- **Input mutation.** Snapshot every input before the call (deep copy) and compare the input after the call for both versions.
- **Exceptions.** Same exception type, and the same message when callers or logs depend on it. Same behavior on null, empty, and invalid input.
- **Side effects.** Calls to collaborators: which ones, with what arguments, how many times, and in what order. Writes, logs, events, and analytics.
- **State.** Any object or global state the function changes.
- **Aliasing and identity.** Whether the function behaves the same when arguments are the same object or share parts (the same list passed twice, a list and a view of it, an object and a collection that contains it), and whether it returns the same object identity where callers can observe it (it returns an argument itself rather than a copy, or reuses a cached or internal object). A deep-copy snapshot of the inputs cannot detect these differences: test them with inputs built to alias, and compare identity (`===`, `is`, `ReferenceEquals`, pointer equality) where the original's identity behavior is observable.
- **Laziness and short-circuiting.** If the original stops early (for example, `any`, `first`, a `break`), the candidate must not evaluate more elements when evaluation has side effects or can throw.

Floating-point results must match exactly unless the developer approves a tolerance. Reordering additions changes results.

## Inputs

Use both hand-written edge cases and generated inputs.

### Edge cases (always)

- Empty input, one element, two elements.
- All elements equal; all distinct; many duplicates.
- Already sorted, reverse sorted, nearly sorted.
- Negative values, zero, minimum and maximum values of the type, values that overflow when combined.
- Floating point: NaN, positive and negative infinity, `0.0` and `-0.0`, subnormal values, very large and very small magnitudes, and values that are nearly equal (to expose cancellation).
- Null elements or null input where the type allows it.
- Strings: empty string, whitespace, mixed case, non-ASCII, emoji and other characters outside the basic multilingual plane, combining characters.
- Ties for any ordering or "first match" logic.
- Aliased arguments: the same object passed for two parameters, an argument that contains or views another argument, and an output parameter that is also an input. The original and the optimized version must agree on these too.
- Inputs at and around every threshold, boundary, or special case visible in the original code.
- Malformed or unexpected input the function can receive (invalid formats, out-of-range values, inconsistent state), when callers can pass it.

### Generated inputs (always)

- Use a fixed random seed so failures reproduce. Print the seed and the failing input on failure.
- Generate many cases (at least 1,000 when the reference is fast enough), across a spread of sizes from 0 up to the largest size the reference can handle quickly.
- Bias the generator toward collisions: small value ranges produce duplicates and ties, which is where rewrites most often break.
- If the project already has a property-based testing library, use it and its shrinking. Do not add one without asking. A hand-written seeded generator is enough and needs no dependency.

### Exhaustive inputs (when the domain is small)

When every input in a small domain can be enumerated in reasonable time, test all of them instead of sampling: for example, every array of length 0 to 6 over the values 0 to 3, every 8-bit or 16-bit input to a bit-manipulation or encoding routine, or every 32-bit input to a fast pure function. Keep the generated inputs as well, for sizes beyond the exhaustive domain. Report the exact domain covered: an exhaustive pass shows equivalence on that domain only, not on larger inputs.

## Verification levels

Differential tests are the floor, not the ceiling. Every change is reported at the highest level it reached:

| Level | What was shown | How to reach it | Claim allowed |
|---|---|---|---|
| 1. Tested | Old and new agree on the edge cases and generated inputs that ran | This file's setup, comparisons, and inputs | "Verified by tests on <inputs>" |
| 2. Property-checked | The contract's properties hold, and old and new agree, on generated inputs, with failing cases shrunk to minimal ones | Executable contract (below) plus a property-based testing library already in the project, or a seeded generator | "Property-checked on <inputs>" |
| 3. Exhaustively checked | Old and new agree on every input up to a stated bound, or every thread interleaving up to a bound | Exhaustive enumeration of a small domain; a bounded model checker running an equivalence harness; a concurrency checker | "Equivalent on <domain>" |
| 4. Proven | Equivalence or the contract holds for all inputs | A machine-checked proof (for example, a refinement proof that the optimized code implements the original's specification), or level 3 over the entire domain (every value of a fixed-width scalar input) | "Proven: <what, by which tool>" |

Aim for the highest level that is cheap. An experimental or derived algorithm (see "Name the source" in `DISCOVERY.md`) needs level 2 or higher before it is applied or shipped. Level 3 is often cheaper than it sounds: most bugs in a rewrite show up on small inputs (the small-scope hypothesis), and a bounded model checker can check `old(x) == new(x)` for every array of length up to k over every value of its element type in minutes. A pure function of one 32-bit argument can be checked on all 2³² inputs, which is level 4. Concurrency changes that tests cannot verify become verifiable at level 3 with a tool that enumerates interleavings.

Verification tools beyond the test framework are dependencies or installs: use them when the project already has them, otherwise ask (rule 7). The language files name the tools for each language. Report what the tool checked, its bounds, and its version; a tool result is only as strong as the harness and the bounds.

## The contract as executable properties

Before changing a function, turn its contract (rule 3) into checks that run in the tests:

- **Postconditions** as assertions on every generated case: "the output is sorted and is a permutation of the input," "every returned ID exists in the input," "the total equals the sum of the parts."
- **Invariants** of a derived or new algorithm (move 3 in `DISCOVERY.md`) as debug assertions or a checking function the tests call after each step. The invariant is the correctness argument; checking it at runtime catches the cases where the argument was wrong.
- **Metamorphic relations** when no oracle exists: how outputs must relate across related inputs. Permuting the input does not change a total; adding an element never decreases a count; splitting the input and merging the partial results equals processing it whole; scaling every input scales the output.

These checks hold the new code to the contract, not just to the old code's outputs on the inputs that happened to run.

## When equivalence counts as verified

Treat an optimization as verified (level 1 or higher) only when all of these hold:

1. Differential tests cover every observable listed above that applies to the function.
2. Edge cases and generated inputs both pass.
3. The existing test suite passes, run on the final version of the code.
4. Every trap in `BEHAVIOR-TRAPS.md` that could apply is either covered by a test or ruled out by analysis you can state in one sentence.

If any part cannot be checked at any level (real database ordering, platform rendering, timing, hardware, or thread interleavings with no concurrency checker available), it is not verified. Follow rule 5: ask the developer, and if they accept, add the `NEEDS-TESTING` marker from `REPORTING.md`. If a differential test shows that the outputs differ and the difference is intended, it is a behavior change, not a test to relax: document it for review and use the `BEHAVIOR-CHANGE` marker only after approval.

## Reporting verification

For every applied item, report:

- **Level reached:** 1 to 4 from "Verification levels," with the domain and bounds for level 3 and the tool for levels 3 and 4.
- **Inputs and properties covered:** the edge-case categories, the number of generated cases, the seeds, the size range, and which observables were compared (return value, input mutation, exceptions, side effects, order).
- **Tests and tools actually run:** the commands or test names, and their results. Report only what actually ran.
- **Unverified behavior:** anything the tests could not cover, and why.

If tests could not be run at all (no test framework, an environment that cannot execute them, a timeout), say so. The item is then unverified: follow rule 5, and do not present it as a confirmed win.

## Testing a new data structure

When the optimization introduces a structure written inside the project (a heap, a deque, a bitset), give the structure its own unit tests in addition to the differential test of the function that uses it. Include a differential test of the structure against a simple, obviously correct model (for example, a heap against a sorted list) on generated operation sequences.

## References (for verifying claims; not required reading)

- William M. McKeeman, "Differential Testing for Software," *Digital Technical Journal* 10(1), 1998.
- Koen Claessen and John Hughes, "QuickCheck: A Lightweight Tool for Random Testing of Haskell Programs," ICFP 2000.
- C. A. R. Hoare, "An Axiomatic Basis for Computer Programming," *CACM* 12(10), 1969: preconditions, postconditions, invariants.
- Daniel Jackson, *Software Abstractions*, revised ed. (2012): the small-scope hypothesis and bounded checking.
- T. Y. Chen, S. C. Cheung, and S. M. Yiu, "Metamorphic Testing: A New Approach for Generating Next Test Cases" (1998).
- Edmund Clarke, Daniel Kroening, and Flavio Lerda, "A Tool for Checking ANSI-C Programs," TACAS 2004 (CBMC).
- Nuno P. Lopes et al., "Alive2: Bounded Translation Validation for LLVM," PLDI 2021.
- Leslie Lamport, *Specifying Systems* (2002): TLA+ for concurrent and distributed algorithms.
