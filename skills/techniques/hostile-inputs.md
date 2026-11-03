# Hostile Inputs, Secrets, and Hard Deadlines

Part of the advanced techniques. First read `ADVANCED-TECHNIQUES.md`: its shared rules apply to every table in this file and explain how to read the tables.

Load this file when the exposure check (Phase 2 in `WORKFLOW.md`, or write mode step 2) finds that untrusted parties control the input, that the code handles secrets, or that it runs under a hard deadline. Friendly benchmark data says nothing about these cases: the attacker, the secret, or the deadline picks the input that matters.

## Judge by the worst case

- **Untrusted input voids expected bounds.** An attacker chooses the input, so average-case and expected bounds hold only when the randomness behind them is secret from the attacker: a hash keyed with a per-process secret, pivots or priorities drawn from a generator seeded unpredictably. Report the worst-case bound next to the expected one, and benchmark the worst case (see "Finding worst-case inputs").
- **Keep every limit.** Input size, nesting depth, length fields, timeouts, and rate limits are part of the defense. Never remove or loosen one to gain speed; that is a security regression (`BEHAVIOR-TRAPS.md`).
- **Already covered elsewhere:** hash flooding (keyed-hash row in `techniques/data-structures.md`), regular-expression backtracking (`techniques/strings-and-text.md`), unbounded queues (`techniques/queues-and-latency.md`).

## Adaptive adversaries: when outputs reveal the randomness

The expected bounds of randomized structures assume the input does not depend on the structure's random choices. That holds when an attacker picks the whole input in advance (an *oblivious* adversary). It fails when the attacker sees outputs that depend on those random choices and picks later inputs after seeing them (an *adaptive* adversary). Then the guarantee can collapse after a modest number of queries, even though each random choice was secret:

- **Sketches and estimators** (HyperLogLog and other distinct-count sketches, MinHash, Count-Min, AMS and other linear sketches): no linear sketch estimates the Euclidean norm within any fixed factor on polynomially many adaptively chosen inputs (Hardt and Woodruff, STOC 2013), and the standard estimators of distinct-count sketches with k registers (HyperLogLog and its variants) can be broken with a number of adaptive queries linear in k (Ahmadian and Cohen, ICML 2024), while about k² queries suffice against any estimator for such sketches, a bound that is tight (Cohen, Nelson, Sarlós, Singhal, and Stemmer, SODA 2026).
- **Filters and caches** (Bloom and cuckoo filters, sampling or randomized-eviction caches): which requests hit, miss, or are rejected tells the attacker about the hidden state.
- **Randomized load balancing and scheduling:** which server or queue a request lands on, or how long it waits, can be observed and steered.
- **Keyed hash tables:** a secret per-process key stops precomputed collisions, but iteration order or timing that the attacker can observe can leak enough to build collisions over many requests.

**The check.** For every randomized structure on an exposed path, ask: can the party that chooses the inputs observe anything that depends on the random choices (returned estimates, iteration or result order, timing, accept or reject decisions), and choose later inputs after seeing it? If not, the oblivious bound holds; say so. If yes:

1. **Write the attack before trusting the design.** A simple adaptive loop is usually enough to test it: query, observe, keep the inputs that pushed the output in the attacker's direction, repeat. Run it against the candidate in a test, and report how many queries it took to break the bound, or that it did not within a stated budget.
2. **Then choose a defense, and measure its cost:** do not expose the raw output (round or aggregate it, or return only what the caller needs); refresh the random seed or key periodically; limit queries per client (rate limits are part of the defense, `BEHAVIOR-TRAPS.md`); use an adversarially robust construction (sketch switching, Ben-Eliezer, Jayaram, Woodruff, and Yogev, PODS 2020; or techniques borrowed from differential privacy, Hassidim, Kaplan, Mansour, Matias, and Stemmer, NeurIPS 2020), which costs extra space; or use a deterministic structure with a worst-case bound.
3. **Report the adversary model** next to the bound: "expected O(1) against an oblivious adversary; an adaptive client can observe iteration order, so worst case O(n) per operation."

## Algorithmic complexity attacks

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Quicksort or quickselect with a deterministic pivot rule (first element, median of three) on attacker-supplied data | Introsort or pattern-defeating quicksort (fall back to heapsort past a depth limit); for selection, introselect or median-of-medians | Stability unchanged (all of these are unstable, like quicksort); tie order among equal elements may change, a behavior change if observable | Attacker-forced O(n²) → O(n log n) worst case; selection O(n) worst case with median-of-medians |
| Randomized structures or algorithms (treaps, skip lists, cuckoo hashing, random pivots, randomized load balancing) on keys an attacker chooses | Draw the random choices from a source the attacker cannot predict or observe (seeded per process from the operating system), or switch to a structure with worst-case guarantees (balanced tree, introsort) | The seed never leaks through outputs, logs, or iteration order | Expected bounds then hold against an adversary; worst-case structures need no secret |
| Recursive parsing or tree walking over nested input (JSON, XML, protocol buffers, syntax trees) | Explicit stack with a depth limit, or a depth counter that fails cleanly | Keep existing limits and their errors; adding a limit where none existed is a behavior change (rule 5) | Stack exhaustion → bounded memory and a clean error |
| Decompression, archive extraction, or expansion driven by input (XML entities, YAML aliases, templates) | Limits on output size, expansion ratio, entry count, and nesting, checked while streaming rather than after | Limits agreed with the developer; rejecting input is a behavior change | Memory and time bounded regardless of how small the input is |
| Buffers allocated from a length field in the input | Check the length against the remaining input and a maximum before allocating, or grow while reading | Valid inputs parse to the same result | Memory proportional to data actually received |
| Regular-expression patterns, not just inputs, supplied by users | A linear-time engine plus limits on pattern size and compiled program size | Match semantics checked as in the regular-expression row of `techniques/strings-and-text.md` | No pattern can force exponential matching |

## Secrets and timing side channels

Code that compares, derives, or looks up values using keys, tokens, passwords, message authentication codes, or private data is secret-dependent, whether or not it is marked as such. Its running time, branches, and memory addresses must not depend on the secret.

- **Optimizations that create side channels:** early exits and short-circuit evaluation on secret data; lookup tables indexed by secrets (cache timing, as in table-based AES); memoization or caching keyed by secrets (hit or miss timing); loop counts that depend on secrets; variable-time instructions such as division on some processors; compressing secret data together with attacker-controlled data (the CRIME and BREACH attacks).
- **Use the platform's constant-time primitive** for comparisons (the language files name it). Write one by hand only when none exists, and verify it.
- **Verify constant time:** a statistical timing test (dudect), tracking secret memory through Valgrind (ctgrind-style), or a formal checker; read the generated code, because compilers can turn branch-free source back into branches.
- **Every change to secret-dependent code needs review** under rule 5, even when outputs match: equal outputs do not show equal timing.

## Hard deadlines (worst-case execution time)

For interrupt handlers, kernel paths that cannot sleep, embedded control loops, audio callbacks, and latency-critical trading or network paths. A missed deadline is a failure, so the bound that counts is the worst case of every operation on the path, not the amortized or expected one.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| A hash table or dynamic array grows on the deadline path | Preallocate to the maximum size, use a fixed-capacity ring buffer, or rehash incrementally (`techniques/data-structures.md`) | The maximum is known and fits the memory budget (rule 1) | No O(n) growth spike inside the deadline |
| Allocation, garbage collection, or lazy initialization on the deadline path | Preallocated pools and arenas; initialization moved to startup; no allocation in the path | Objects are fully reset before reuse | Allocator and collector pauses removed from the path |
| Amortized or self-adjusting structures (splay trees, structures with periodic rebuilds) on the deadline path | Structures with worst-case bounds (balanced trees, deamortized versions that spread rebuilds across operations) | Same results; usually slower on average | No single slow operation |

Measure the maximum and the highest percentiles over long runs, never the median. Certified systems use static worst-case execution-time analysis tools (for example aiT or OTAWA).

## Finding worst-case inputs

- **Construct known worst cases:** sorted, reverse-sorted, and all-equal input; keys that collide under a known hash function; maximal nesting; the pathological strings for a regular expression; the adversary for a deterministic pivot rule.
- **Performance fuzzing:** fuzzers that search for inputs maximizing running time or resource use (PerfFuzz, SlowFuzz), or a coverage-guided fuzzer with a size and time objective. A fuzzer is a tool to install: ask first (rule 7).
- **Report** the worst input found, its measured cost, and the worst-case bound it is consistent with.

## References

Sources for the claims in this file are in `references/techniques/hostile-inputs.md`. Read them only to verify a claim.
