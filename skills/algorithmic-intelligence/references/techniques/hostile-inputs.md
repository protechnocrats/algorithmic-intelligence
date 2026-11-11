# Hostile Inputs, Secrets, and Hard Deadlines

The shared rules and table conventions in `ADVANCED-TECHNIQUES.md` apply to every table here.

**Contents:** Judge by the worst case · Optimizations that weaken a defense · Adaptive adversaries: when outputs reveal the randomness · Algorithmic complexity attacks · Secrets and timing side channels · Hard deadlines (worst-case execution time) · Finding worst-case inputs

For code where the exposure check (Phase 2 in `WORKFLOW.md`) finds untrusted input, secrets, or a hard deadline. Friendly benchmark data says nothing about these cases: the attacker, the secret, or the deadline picks the input that matters.

## Judge by the worst case

- **Untrusted input voids expected bounds.** Average-case and expected bounds hold only while the randomness behind them is secret from the attacker (a hash keyed with a per-process secret, pivots or priorities from an unpredictably seeded generator). Report the worst-case bound next to the expected one, and benchmark the worst case.
- **Keep every limit.** Input size, nesting depth, length fields, timeouts, rate limits, and per-client quotas are part of the defense; loosening one for speed is a security regression ("When the request itself is risky" in `SKILL.md`).
- **Covered elsewhere:** hash tables the project implements itself (`techniques/specialized-structures.md`), regular-expression backtracking (`techniques/strings-and-text.md`), unbounded queues and fan-out (`techniques/queues-and-latency.md`), cache keys that leave out the user or tenant ("Security-sensitive behavior" in `BEHAVIOR-TRAPS.md`).

## Optimizations that weaken a defense

Each looks like a plain speedup and passes tests built from friendly data. On an exposed path, a change that fails one of these checks is a security behavior change:

- **Caches of decisions.** Caching an authorization result, session, token validation, or permission delays revocation until the entry expires, so the entry's lifetime cannot exceed how soon the original honored a logout, role change, or password reset. Caching a check and acting on its result later is a time-of-check-to-time-of-use gap.
- **Cache poisoning.** Every input that changes a cached result is in the key (headers, host name, locale, the caller's identity), or one client's request fills the entry another receives. The same goes for caching error responses or partial results the original did not cache.
- **Caches and pools an attacker fills.** Entries keyed by attacker-chosen values (negative-cache entries for keys that do not exist, per-client or per-pattern entries, interned strings, compiled regular expressions) need a bound on count and on bytes, or the attacker evicts every useful entry and then exhausts memory.
- **Caches as oracles.** A cache shared across users whose hit or miss is observable (timing, a header, a metric, a counter) tells one user what another requested: a memoized "account by email" lookup or a content-addressed deduplication check answers "did someone else submit this?". Keep entries for user-supplied data private to that user or tenant, or make hit and miss indistinguishable.
- **Skipping work on the failure path.** A fast path taken only when a user, token, or record does not exist (skipping the password hash, the signature check, the database read) reveals existence by timing. Do the same work on both paths, or list the change as a security behavior change.
- **Random sources.** Anything an attacker must not predict (tokens, session and reset ids, salts, nonces, shuffles that decide money) keeps its cryptographic generator, unseeded; a faster or seeded generator is predictable.
- **Batching across callers.** Items from different users or tenants merged into one query, request, or buffer keep their own authorization check, and each result and error goes back to its own caller by identifier, never by position.
- **Approximate answers in decisions.** A Bloom filter, sketch, or sampled count deciding access, a deny list, deduplication of payments or messages, billing, or a limit on its own lets a false positive block a legitimate user, drop a payment, or admit an attacker. Confirm with the exact check, and key the hashes with a secret when attackers choose the items, or they can craft false positives.
- **Parser and normalization differences.** A faster parser, a byte-level or ASCII fast path, or a reordered normalization step must accept, reject, and interpret exactly what the original did: duplicate keys, number range and precision, invalid or overlong UTF-8, trailing data, non-ASCII digits that some parsers accept, Unicode normalization and case folding done before rather than after a check, and lengths counted in a different unit. When one component validates input and another acts on it, any disagreement is a bypass.
- **File paths.** Caching resolved paths, replacing a safe path join or canonicalization with string concatenation, or checking a path and then opening it by name lets `..`, absolute paths, and symbolic links escape the intended directory. Keep the original checks; in new code, resolve paths beneath a directory handle so no component can escape it (`openat2` with `RESOLVE_BENEATH` on Linux, or the platform's equivalent) where the platform allows it.
- **Logging and errors.** New logging, metrics labels, error messages, and benchmark or test output, including on a new slow path or fallback, leave out secrets, tokens, and the request data that contains them.

## Adaptive adversaries: when outputs reveal the randomness

The expected bounds of randomized structures assume the input does not depend on the structure's random choices. That holds when the attacker picks the whole input in advance (an *oblivious* adversary) and fails when the attacker sees outputs that depend on those choices and picks later inputs accordingly (an *adaptive* adversary): the guarantee can collapse after a modest number of queries even though each random choice was secret. Exposed this way:

- **Sketches and estimators** (HyperLogLog and other distinct-count sketches, MinHash, Count-Min, AMS and other linear sketches):
  - No linear sketch estimates the Euclidean norm within any fixed factor on polynomially many adaptively chosen inputs (Hardt and Woodruff, STOC 2013).
  - The standard estimators of distinct-count sketches with k registers (HyperLogLog and its variants) can be broken with a number of adaptive queries linear in k (Ahmadian and Cohen, ICML 2024).
  - About k² queries suffice against any estimator for such sketches, a bound that is tight (Cohen, Nelson, Sarlós, Singhal, and Stemmer, 2024 preprint).
- **Filters and caches** (Bloom and cuckoo filters, sampling or randomized-eviction caches): which requests hit, miss, or are rejected tells the attacker about the hidden state.
- **Randomized load balancing and scheduling:** which server or queue a request lands on, or how long it waits, can be observed and steered.
- **Keyed hash tables:** a secret per-process key stops precomputed collisions, but iteration order or timing that the attacker can observe can leak enough to build collisions over many requests.

**The check.** For every randomized structure on an exposed path: can the party that chooses the inputs observe anything that depends on the random choices (returned estimates, iteration or result order, timing, accept or reject decisions), and choose later inputs after seeing it? If not, the oblivious bound holds; say so. If yes:

1. **Write the attack before trusting the design.** A simple adaptive loop usually suffices: query, observe, keep the inputs that pushed the output in the attacker's direction, repeat. Run it locally against the candidate and report how many queries broke the bound, or that none did within a stated budget.
2. **Then choose a defense, and measure its cost:**
   - expose less of the raw output (round or aggregate it, or return only what the caller needs);
   - refresh the random seed or key periodically;
   - limit queries per client;
   - use an adversarially robust construction (sketch switching, Ben-Eliezer, Jayaram, Woodruff, and Yogev, PODS 2020; or techniques borrowed from differential privacy, Hassidim, Kaplan, Mansour, Matias, and Stemmer, NeurIPS 2020), which costs extra space;
   - or use a deterministic structure with a worst-case bound.
3. **Report the adversary model** next to the bound: "expected O(1) against an oblivious adversary; an adaptive client can observe iteration order, so worst case O(n) per operation."

## Algorithmic complexity attacks

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| A map, set, counter, or group-by keyed by attacker-chosen values (query parameters, JSON keys, header names, form fields, IDs) | Keep the platform's keyed hashing where it exists (the language file says which hashes are keyed: CPython integers and JVM `String.hashCode` are not, and JavaScript engines give no guarantee, since integer-like keys are unprotected and some embedders have shipped a fixed seed), otherwise a keyed hash (SipHash) or a sorted structure; bound the number of distinct keys per request | Changing the hash or structure changes iteration order; the key for a keyed hash never leaks | Hash flooding O(n) per operation → O(1) expected with a secret key, or O(log n) worst case with a sorted structure |
| Quicksort or quickselect with a deterministic pivot rule (first element, median of three) on attacker-supplied data | Introsort or pattern-defeating quicksort (fall back to heapsort past a depth limit); for selection, introselect or median-of-medians | Stability unchanged (all of these are unstable, like quicksort); tie order among equal elements may change | Attacker-forced O(n²) → O(n log n) worst case; selection O(n) worst case with median-of-medians |
| Randomized structures or algorithms (treaps, skip lists, cuckoo hashing, random pivots, randomized load balancing) on keys an attacker chooses | Draw the random choices from a source the attacker cannot predict or observe (seeded per process from the operating system), or switch to a structure with worst-case guarantees (balanced tree, introsort) | The seed never leaks through outputs, logs, or iteration order | Expected bounds then hold against an adversary; worst-case structures need no secret |
| Recursive parsing or tree walking over nested input (JSON, XML, protocol buffers, syntax trees) | Explicit stack with a depth limit, or a depth counter that fails cleanly | Existing limits and their errors kept; a limit where none existed is a behavior change | Stack exhaustion → bounded memory and a clean error |
| Decompression, archive extraction, or expansion driven by input (XML entities, YAML aliases, templates) | Limits on output size, expansion ratio, entry count, and nesting, checked while streaming rather than after | Limits agreed with the developer, since rejecting input changes behavior | Memory and time bounded regardless of how small the input is |
| Buffers allocated from a length field in the input | Check the length against the remaining input and a maximum before allocating, or grow while reading | Valid inputs parse to the same result | Memory proportional to data actually received |
| Sizes, offsets, counts, or sums computed from input values (count × element size, offset + length, a total of user amounts) in code being rewritten, or a narrower integer type proposed for speed | Keep the original's integer width and checks; in new arithmetic of this kind, use checked arithmetic or a range check before allocating or comparing | A narrower type only when validation proves the range, not test data; an overflow the original already has is a bug to record (rule 4), not to fix | No new path where a wrapped size allocates a short buffer that is then overrun, or a wrapped sum passes a limit check |
| Regular-expression patterns, not just inputs, supplied by users | A linear-time engine plus limits on pattern size and compiled program size | Match semantics checked as in the regular-expression row of `techniques/strings-and-text.md` | No pattern can force exponential matching |
| A pattern, query, or command built by inserting input into its text (a regular expression from a search term, a `LIKE` clause, a shell or SQL string) | Plain substring or prefix search, or escape the input with the platform's function (`re.escape`, `Pattern.quote`) and keep queries parameterized | Same matches as the original for every input, including input containing metacharacters; if the original did not escape, record the injection as a bug and keep its matching unchanged | No injection, and no attacker-chosen backtracking pattern |

## Secrets and timing side channels

Code that compares, derives, or looks up values using keys, tokens, passwords, message authentication codes, or private data is secret-dependent, marked or not; its running time, branches, and memory addresses stay independent of the secret.

- **Optimizations that create side channels:**
  - early exits and short-circuit evaluation on secret data;
  - lookup tables indexed by secrets (cache timing, as in table-based AES);
  - memoization or caching keyed by secrets (hit or miss timing);
  - loop counts that depend on secrets;
  - variable-time instructions such as division on some processors;
  - compressing secret data together with attacker-controlled data (the CRIME and BREACH attacks).

  Constant-time source does not stop speculative execution (Spectre-class attacks). The processor can run a bounds check's protected branch or a secret-indexed load ahead of time and leave a cache trace. So keep any existing mitigation (index masking, speculation barriers, compiler hardening flags) when rewriting such code, and treat removing one as weakening a defense.
- **Use the platform's constant-time primitive** for comparisons (the language files name it). Write one by hand only when none exists, and verify it.
  - To find a record by a secret token, either look it up by a non-secret identifier and compare the secret in constant time, or look it up by a hash of the token (which also protects the stored tokens if the database leaks) and compare the full value in constant time.
  - A lookup keyed by the raw token leaks match-prefix timing in principle, so do not introduce one. An existing one is a bug when the secret has low entropy (a password, PIN, or short code), and a hardening finding for a long random token.
- **Keep constant time.** A constant-time comparison only reads the rest of a short value instead of stopping at the first difference, so removing it saves almost nothing. A request to replace it, or to cache or skip a password hash, is a request to weaken security ("When the request itself is risky" in `SKILL.md`).
- **Verify constant time:** a statistical timing test (dudect; a tool to install, so ask first, rule 7), tracking secret memory through Valgrind (ctgrind-style), or a formal checker; and read the generated code, because compilers can turn branch-free source back into branches.
- **Every change to secret-dependent code needs the developer's review**, even when outputs match: equal outputs do not show equal timing.

## Hard deadlines (worst-case execution time)

For interrupt handlers, kernel paths that cannot sleep, embedded control loops, audio callbacks, and latency-critical trading or network paths. A missed deadline is a failure, so the bound that counts is the worst case of every operation on the path, not the amortized or expected one.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| A hash table or dynamic array grows on the deadline path | Preallocate to the maximum size, use a fixed-capacity ring buffer, or rehash incrementally (`techniques/specialized-structures.md`) | The maximum is known and fits the memory budget | No O(n) growth spike inside the deadline |
| Allocation, garbage collection, or lazy initialization on the deadline path | Preallocated pools and arenas; initialization moved to startup; no allocation in the path | Objects are fully reset before reuse | Allocator and collector pauses removed from the path |
| Amortized or self-adjusting structures (splay trees, structures with periodic rebuilds) on the deadline path | Structures with worst-case bounds (balanced trees, deamortized versions that spread rebuilds across operations) | Same results; usually slower on average | No single slow operation |

Measure the maximum and the highest percentiles over long runs, not the median. Certified systems use static worst-case execution-time analysis tools (for example aiT or OTAWA).

## Finding worst-case inputs

- **Run them bounded.** A worst-case input is built to exhaust time, memory, or stack: run every worst-case test and fuzzer under time and memory limits, starting small and doubling. Generate large or hostile inputs in the test instead of committing them as files.
- **Construct known worst cases:** sorted, reverse-sorted, and all-equal input; keys that collide under a known hash function; maximal nesting; the pathological strings for a regular expression; the adversary for a deterministic pivot rule.
- **Performance fuzzing:** fuzzers that search for inputs maximizing running time or resource use (PerfFuzz, SlowFuzz), or a coverage-guided fuzzer with a size and time objective; these are tools to install.
- **Report** the worst input found, its measured cost, and the worst-case bound it is consistent with. Describe a large or hostile input by the code that generates it rather than pasting it: fuzzer output can contain control characters or text addressed to AI assistants ("Untrusted content" in `SKILL.md`).
