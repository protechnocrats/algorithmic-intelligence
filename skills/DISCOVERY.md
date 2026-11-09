# Discovering Better Algorithms

`CORE-TECHNIQUES.md` and the files under `techniques/` hold known solutions. This file is for when none matches: a set of heuristics, each with a canonical example, drawn from how algorithm designers find better solutions (Bentley, Dijkstra, Tarjan, Knuth, Sedgewick, Pólya, and others). They are ways of looking at a problem, not a checklist, and the reason one fails usually points to the next.

**Contents:** When to use it · The loop · Consulting the literature · The moves · When a move stalls · Combining moves · Recording the result · References

## When to use it

When no row in the arsenal or the domain files matches the abstract problem; when the best match stays above the lower bound for no reason a dependency, call pattern, or measured constant explains; or when the problem is custom (a business rule, a domain aggregate, a mix of conditions no textbook names). When a known technique already reaches the lower bound, this file adds nothing.

## The loop

Pin the problem down first: the abstract statement, the contract as the code implements it (outputs, order, ties, errors, edge cases), every size variable, and the lower bound (move 10). A wrong statement yields a fast algorithm for a different problem. Keep the existing code, or in write mode the simplest correct version, as the baseline that every derivation is tested against.

Then try the moves, cheapest first, and keep a short research log: what each move gave (a candidate, a bound, or nothing) and what blocked it. A candidate from here still has to state its assumptions, have them confirmed from the code, and compete with the other candidates. Stop when a candidate reaches the lower bound, when a conditional bound (move 10) says the gap needs a breakthrough, or when the moves run out; record the gap and why it remains.

This is the algorithm-engineering cycle (Sanders; McGeoch): design, analyze, implement, experiment, and let the experiment send you back to the design. A measurement that contradicts the analysis (move 12) or a small case that breaks a conjecture (move 13) sends you back to the problem statement or the moves, not forward with the candidate.

**Name the source of every algorithm you recommend:**

- **Established:** in textbooks or standard references, or in widely used libraries. Cite its common name and a standard reference.
- **Experimental:** published (a recent paper or a preprint) with little production track record. Cite the publication, tell the developer it is new, and benchmark it on the project's own data.
- **Derived:** worked out in this analysis. Write its correctness argument (usually its invariant, move 3), and test any new structure as in "Testing a new data structure" in `DIFFERENTIAL-TESTING.md`. First check whether it is a known technique under another name; if so, use that name and its known pitfalls.

Experimental and derived algorithms carry a minimum verification level ("Verification levels" in `DIFFERENTIAL-TESTING.md`).

## Consulting the literature

When the tables and moves leave a gap on a nontrivial problem, or to check whether a derived algorithm is already known, consult published sources if the environment allows; without web access, use the references in this skill and say no further search was possible. Prefer textbooks, standard references, and peer-reviewed papers over course notes, preprints, and blog posts; a result found only in the last two is experimental.

- **Cite only what you have read** in this session or what this skill's references list; otherwise give the technique's name and mark the citation "reference not checked". An invented or misattributed citation is worse than none.
- **Check the claim, not the title.** Confirm the source states the bound and conditions you rely on, in your model (comparison-based, word RAM, external memory, expected or worst case).
- **Re-derive rather than paste.** Code from a paper, blog, or answer site may be wrong, carry a license, or miss this contract's edge cases; implement from the description and test it as derived.

## The moves

### 1. Count the repeated work (Knuth, Bentley)

Write the brute force and count how often each line runs as a function of the sizes (a line-level profiler gives the same numbers for existing code). The line that runs most is where the gain is: what does it compute that an earlier iteration already computed?

*Example:* counting pairs i < j with `a[i] + a[j] == k` runs the inner comparison n²/2 times. Each inner loop asks "how many earlier elements equal `k − a[j]`?", which earlier iterations already saw. A hash map of counts so far answers it in O(1) expected: O(n²) → O(n) expected.

### 2. Carry the answer forward (Bentley)

When the inner loop recomputes something over a range that grows by one element each step, keep it as running state. Applied repeatedly, this walks a problem down one complexity class at a time.

*Example (maximum subarray sum):* every range summed is O(n³); a running sum per start index is O(n²); divide and conquer is O(n log n); carrying "the best sum of a range ending here", `best_here = max(a[j], best_here + a[j])`, is O(n). *Check:* whether an empty range counts. Bentley's version returns 0 for all-negative input; many callers expect the largest element.

### 3. Design from the invariant (Dijkstra, Gries)

State what must be true after processing the first i elements, together with what the final answer needs. The algorithm is whatever restores that invariant when element i + 1 arrives. If restoring it is expensive, strengthen the invariant: keep extra state that makes each step cheap. The invariant is also the correctness argument for a derived algorithm.

*Example:* a stack that reports its minimum. "Each entry also stores the minimum of itself and everything below it" makes push, pop, and minimum O(1) instead of an O(n) scan. Monotonic stacks, sliding windows, and two pointers are all invariants of this kind.

### 4. Change the representation (Bentley, Knuth)

A problem can be easy in one representation and hard in another. Try sorting (many questions become adjacent comparisons or sweeps), indexing by a key, events in time order instead of intervals, prefix sums instead of values, canonical forms instead of raw strings, bitsets instead of sets, the complement instead of the target, or the dual of an optimization problem.

*Example:* counting overlapping pairs among n intervals checks every pair, O(n²). The complement is easier: two closed intervals do not overlap when one ends before the other starts. Sort the end points, binary search for each interval how many ends fall strictly before its start, and subtract that total from n(n − 1)/2: O(n log n). *Check:* whether touching end points overlap in the original.

### 5. Solve a special case, then generalize (Pólya)

Solve a simpler version (sorted input, k = 1, two dimensions instead of three, no deletions, small values), then ask what it relied on and whether the general case can be transformed into it (sort first, split into cases, process offline).

*Example:* pair sum on sorted input is two pointers in O(n). General input becomes that case after sorting a copy that keeps original indices, provided the output does not depend on the original order or it is restored.

### 6. Reduce to a solved problem, or from a hard one (CLRS, Karp)

Look for a known problem underneath: dependencies → topological sort; conflicts → bipartite check or graph coloring; assigning n workers to n jobs at minimum cost → the assignment problem (Hungarian algorithm, O(n³), instead of n! permutations); boolean constraints with two variables per clause → 2-SAT in linear time; "minimum capacity such that…" → binary search on a monotonic predicate.

The reverse direction tells you when to stop. If a known hard problem (subset sum, 3SUM, element distinctness, satisfiability) reduces to yours, yours is at least as hard. Then look for the structure that makes your instances easy (small integer weights, bounded treewidth, few distinct values), or accept the bound and say so. "After NP-hardness" in `techniques/sequences-dp-search.md` orders the options; `techniques/optimization-and-scheduling.md` has the polynomial special cases and solvers.

### 7. Pay later: amortize (Tarjan)

An expensive operation is fine if enough cheap ones pay for it: rebuild periodically, delete lazily, compress paths as they are walked, double capacity when full. Prove the bound over any sequence of operations, by showing each element is touched a bounded number of times or with a potential function that cheap operations raise and expensive ones spend.

*Example:* a sorted array with frequent inserts. Buffer inserts in a small unsorted list and merge it in at √n elements. Each O(n) merge happens once per √n inserts, so inserts cost O(√n) amortized instead of O(n), and lookups O(log n + √n). *Check:* amortized bounds allow a single slow operation. If every operation must be fast (real-time, latency budgets), spread the work (incremental rebuilding), or the latency change is a behavior change.

### 8. Use randomness (Mitzenmacher)

A random pivot makes selection O(n) expected whatever the input order, if the adversary cannot predict the pivots; a random sample estimates a distribution or picks partition boundaries (sample sort); hashing maps a large key space into a small one; two random choices instead of one balance load almost perfectly.

*Check:* randomness that changes only running time gives an expected bound; state what it is over. Randomness that can change the result (Monte Carlo, as opposed to Las Vegas, which is always right) makes the answer approximate, so it is a behavior change and unsuitable where the answer decides access, money, or deletion. Seed and reproducibility requirements still hold. If whoever chooses the inputs sees outputs that depend on the random choices before choosing more, the expected bound may not hold ("Adaptive adversaries" in `techniques/hostile-inputs.md`).

### 9. Shorten the critical path (Leiserson)

For parallel code the obstacle is usually the span, the longest chain of steps that must run in order, not the total work. Find that chain and break its dependencies: a running total looks sequential, yet a parallel prefix sum does the same O(n) work in O(log n) span. Definitions and bounds are under "Parallelism and vectorization" in `techniques/hardware-and-concurrency.md`.

*Check:* make the sequential work optimal first; a parallel version of a worse algorithm loses at scale. Parallel prefix sums and reductions regroup operations: exact for integers without overflow, different for floating point.

### 10. Prove a lower bound (Knuth, CLRS)

A lower bound says when to stop. Four ways to get one:

- **Adversary:** if any unread element could change the answer, every element must be read: Ω(n).
- **Counting:** a comparison algorithm with L possible outcomes needs at least log₂ L comparisons. Sorting has n! outcomes, so Ω(n log n).
- **Reduction:** if a problem with a known bound reduces to yours (element distinctness is Ω(n log n) by comparison; 3SUM is conjectured to need about n²), yours inherits it.
- **Conditional (fine-grained complexity):** many polynomial problems have no unconditional bound beyond Ω(n), but a believed conjecture rules out improvement. An O(n^(2−ε)) algorithm for edit distance or longest common subsequence would refute the Strong Exponential Time Hypothesis (Backurs and Indyk, 2015; Abboud, Backurs, and Vassilevska Williams, 2015). The 3SUM and all-pairs-shortest-paths conjectures play the same role for many geometric and graph problems. Report such a bound as "no O(n^(2−ε)) algorithm unless SETH is false", then look for structure in the real inputs the conjecture does not cover (small alphabets, bounded distances, few differences, approximate answers).

Each bound holds in a model. Leaving the model (hashing instead of comparing, bounded integer keys, preprocessing reused across queries) can beat it, and that is often the improvement.

### 11. Estimate before building (Bentley)

Multiply a candidate out before writing it: sizes × calls per period × operations per call. Take sizes from what the deployed code and configuration enforce, and from data the developer gives. A size nothing enforces is not a bound, so size for the largest input the code accepts. When sources disagree, state both; ask the developer if they would select different candidates, and when nobody can answer, pick the one that is safe at the larger size.

Rough orders of magnitude, for estimates only: a core runs about 10⁸ to 10⁹ simple operations per second; a main-memory cache miss costs about 100 ns; a random SSD read about 100 µs; a round trip inside a data center about 0.5 ms, across continents about 100 ms. An estimate in seconds against a budget in milliseconds rules a candidate out without building it; one far inside the budget says further moves are not needed.

Turn size and budget into the complexity needed before searching; it sets the target and rules out whole families. At about 10⁸ simple operations per second (constants and memory access move it 10× either way), one second allows roughly:

| Complexity | Largest n in about 1 s |
|---|---|
| O(n!) | 10 to 11 |
| O(2ⁿ) | 25 to 27 |
| O(n³) | about 500 |
| O(n²) | about 10⁴ |
| O(n log n) | about 5 × 10⁶ |
| O(n) | about 10⁸ |

Scale by the real budget and frequency: a job given an hour has 3,600 times the room; code that runs 1,000 times a second has a thousandth. Use every size variable: O(n·m) with both near 10⁵ is 10¹⁰. The table rules candidates out; it never shows one is fast enough. Near a boundary, or when memory is the limit, measure.

### 12. Measure the growth rate (Sedgewick)

Big-O claims are hypotheses an experiment can refute. Measure the growth exponent with a doubling experiment (`BENCHMARKING.md`), predict the time at the next size, and check the prediction. A failed prediction means the model is wrong: go back to the analysis. Run it on the baseline too: an original that measures quadratic where analysis said linear has a hidden cost (a library call, a copy, a rehash), and finding it is often the whole discovery.

### 13. Experiment on small cases, then conjecture (Pólya, Knuth)

When you cannot see the structure, compute it. Run the brute force on every small input (all lists up to length 6 or 7 over a few values, every graph on up to 6 vertices) and tabulate answers and optimal solutions against the parameters. Look for a recurrence, a closed form, monotonicity, symmetry, or a choice optimal solutions always make (the smallest element, the earliest deadline). For an integer sequence of answers, check the On-Line Encyclopedia of Integer Sequences (oeis.org), which often names the problem. Then prove the conjecture (moves 3, 10, 14) or check it at level 3 in `DIFFERENTIAL-TESTING.md`.

*Example:* does "largest coin first" give the fewest coins? For coins {1, 3, 4}, greedy pays 6 as 4 + 1 + 1, the optimum is 3 + 3: one counterexample settles it, so use a DP over amounts. For {1, 5, 10, 25} the table agrees with greedy on every amount tested, which is evidence, not proof. *Check:* small-case patterns can break later. The regions formed by chords between n points on a circle go 1, 2, 4, 8, 16, then 31 (Moser's circle problem, OEIS A000127).

### 14. Make the choice, then prove it safe (exchange arguments)

A greedy algorithm is one choice repeated: the earliest deadline, the cheapest edge, the best ratio. Take an optimal solution that disagrees with your choice and swap the two decisions; if the swap never makes it worse, greedy is optimal. Move 13 suggests the rule; the exchange argument proves it. When the swap can make it worse, it shows the counterexample, and the problem needs DP or search.

*Example:* jobs on one machine, minimize the sum of completion times. Swapping a longer job that runs just before a shorter one moves the shorter one earlier by the longer one's length and the longer one later by the shorter one's length, so the total drops. Shortest-processing-time-first is optimal by sorting, O(n log n) instead of n! orders; with weights the same swap gives Smith's rule (order by processing time divided by weight). *Check:* the proof says any order among equal keys is optimal, but the original's tie order may be part of its contract.

### 15. Find the small parameter (Downey and Fellows)

A problem hard in general may be exponential only in a quantity the real workload keeps small: solution size, distinct values, items with a special property, alphabet size, constraints of one kind, treewidth. Confine the exponential part to that parameter k: O(f(k) · n^c) instead of O(2^n).

*Example:* a vertex cover of size at most k, k ≤ 20 in practice. Any uncovered edge has an end in the cover, so branch on its two ends, at most k levels deep: O(2^k · m) for m edges, about a million branches for k = 20 whatever the graph size. *Check:* the parameter's bound comes from measured data or the domain; say what happens when it is large (the same exponential cost, or a fallback that changes results).

### 16. Relax, then bound or repair (Dantzig; Held and Karp)

Drop the constraint that makes the problem hard, solve the easier one, and use the result:

- **As a bound.** The relaxed optimum bounds the true one, so branch and bound prunes every branch whose relaxed bound cannot beat the best solution so far. Better bounds prune more.
- **As a certificate.** If the relaxed solution satisfies the dropped constraint, it is optimal for the original. The LP relaxation of the assignment problem always has an integral optimum, so the integer problem is solved exactly.
- **As a start.** Repair the relaxed solution into a feasible one. A repaired heuristic usually answers differently from exact code it would replace.

*Example:* 0/1 knapsack. The fractional knapsack, solved greedily by value-to-weight ratio, gives an upper bound that lets branch and bound explore a tiny part of the 2^n tree; Held and Karp's 1-trees do the same for the traveling salesperson. *Check:* pruning makes the search faster, not polynomial; the worst case stays exponential.

### 17. Look at the dual (LP duality; König)

Many optimization problems come in pairs: max flow equals min cut; in a bipartite graph the largest matching equals the smallest vertex cover (König); every linear program's dual bounds its optimum. The dual gives a bound for move 10, may be easier to design an algorithm for, and a pair of equal-valued solutions certifies both optimal.

*Example:* after computing a maximum matching, produce a vertex cover of the same size from the final augmenting-path search; equal sizes prove the matching maximum without trusting the matching code. *Check:* verify the certificate itself: the cover covers every edge and the sizes are equal.

### 18. Derive it by transformation (Burstall and Darlington; Bird)

Start from the clearest correct version and rewrite it in small meaning-preserving steps until it is fast. The chain of steps is the correctness argument, provided each step's side condition holds. Useful steps:

- **Unfold and fold:** replace a call by its body, simplify, and recognize the original call in the result.
- **Tupling:** compute two results that share work in one pass.
- **Accumulating parameters:** carry the partial result as an argument (often turns a quadratic list build linear).
- **Fusion:** merge producer and consumer into one loop, so the intermediate collection is never built.
- **Memoization and tabulation:** the route from recursion to DP.
- **Strength reduction and hoisting:** replace a recomputed expression by an updated one, or move it out of the loop.
- **For interpreters:** continuation-passing style then defunctionalization turns a recursive evaluator into an abstract machine (Ager, Biernacki, Danvy, and Midtgaard, 2003).

*Example:* `fib(n) = fib(n − 1) + fib(n − 2)` is exponential. Define `pair(n) = (fib(n), fib(n + 1))`, unfold `pair(n + 1)`, and fold back: `pair(n + 1) = (b, a + b)` where `(a, b) = pair(n)`. Linear, and each step was an equation. *Check:* side conditions break easily in code. Regrouping additions needs associativity, which floating point lacks; fusing loops moves side effects and exceptions; memoizing needs purity. Run the differential test after each group of steps so a broken step is found where it happened.

### 19. Use a prediction, keep the guarantee (Mitzenmacher and Vassilvitskii)

When something can predict part of the answer (a model, last run's result, a frequency estimate, where a key usually lands), use it to skip work, but bound the cost of a wrong prediction. State **consistency** (how good it is when the prediction is exact) and **robustness** (how bad when the prediction is arbitrarily wrong: never much worse than the classic algorithm).

*Example (learned indexes, Kraska et al., 2018):* a model predicts a key's position p in a sorted array; exponential search outward from p costs O(log d) for an error of d, so a good prediction is near O(1) and a useless one still O(log n). For caching, a randomized policy that follows predicted next-use times but falls back to randomized marking stays within a constant factor of optimal when predictions are good and within O(log k) for cache size k when not (Lykouris and Vassilvitskii, 2018); deterministic LRU guarantees only O(k), the best any deterministic policy can. *Check:* measure the prediction error on real data and the predictor's own cost (training, memory, staleness). Predictions that decide something callers observe (which entries are evicted, who is served first) change behavior. Untrusted inputs can steer the predictor, so judge robustness by the worst case.

### 20. Work backward, and from the extremes (Pólya)

- **Reverse the process.** With all operations known in advance, reversing them can turn a hard operation into an easy one: deleting edges while asking about connectivity becomes adding edges, which union-find handles in near-constant amortized time. Undoing, splitting, and expiring often become adding, merging, and arriving.
- **Start from the final state.** Ask which choice is made last (the last element chosen, the last interval closed, the last merge). Fixing it often splits the problem into independent parts, the step that turns a search into a DP or divide and conquer.
- **Go to the extremes.** All values equal, all distinct, sorted or reversed, one size equal to 1, a value at its maximum. An extreme shows the structure (the answer is trivial there, so what changes moving away?) or breaks a candidate fast.

*Check:* reversal needs every operation known up front; code that must answer each as it arrives cannot use it. A rule found at the extremes is a conjecture until checked on ordinary inputs and argued.

## When a move stalls

The reason a move failed points to the next one:

| Obstacle | Try next |
|---|---|
| The same value is computed again in a later iteration | Moves 1 and 2 |
| Restoring the needed state after each element is too expensive | Move 3 (strengthen the invariant), move 7 (amortize) |
| The input order or a pairwise comparison is in the way | Move 4 (sort, index, events, complement), move 5 |
| No structure is visible | Move 13 (compute small cases) |
| A candidate greedy rule with no proof | Move 14; move 13 for a counterexample |
| The problem looks NP-hard | Move 6 to confirm, then move 15 (small parameter), move 16 (relax and bound), and "After NP-hardness" in `techniques/sequences-dp-search.md` |
| One constraint makes it hard, the rest is easy | Move 16 |
| Unclear whether an answer or a bound is the best possible | Move 17 (dual), move 10 |
| Nothing goes below n² | Move 10: check for a SETH or 3SUM reduction before searching further |
| A correct but slow specification, and no move applies directly | Move 18 |
| A model, past results, or the data's usual shape could predict part of the answer | Move 19 |
| Operations are hard to undo (deletions, splits, expiry), or the first choice depends on later ones | Move 20 |
| Analysis and measurement disagree | Move 12, then restate the problem |

## Combining moves

Most real derivations chain moves. Bentley's maximum subarray is 1 → 2 → 3. Interval overlap counting is 4 → 5. Many query problems are 4 → 7 (sort or index once, then amortize updates). A greedy rule is usually 13 → 14: guess from small cases, then prove. A hard problem is usually 6 → 15 or 6 → 16. Move 18 can express several others as rewrites (carrying the answer forward is tupling or an accumulating parameter). When one move stalls, change the representation (move 4) and try the others on the new form.

## Recording the result

In the item's "Candidates" field (`REPORTING.md`), say how each candidate was found (a table row, or a move by number). Mark derived algorithms *derived* with their invariant or correctness argument in a sentence or two. Summarize the research log, including the moves that produced nothing and what blocked them, so the developer can see where the search stopped. For a conjecture from small cases, say whether it was proved or only checked, and up to which sizes. A log, derived algorithm, or bound from an earlier session is a claim to recheck.

## References

Sources for the claims in this file are in `references/DISCOVERY.md`. Read them only to verify a claim.
