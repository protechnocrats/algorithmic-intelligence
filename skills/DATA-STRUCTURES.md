# Data Structures

The audit every hot path gets, in report and apply mode for each candidate and in write mode for each designed part, before choosing an approach. The wrong structure is the most common source of avoidable complexity, and it often shows no nested loop: a membership check behind a helper, a removal from the front of an array, a re-sort after each insert. Developers also read the audit to judge the analysis, so an item without one looks unexamined even when it was not.

**Contents:** The audit · Which structure suits the operations · Choosing the best structure · Recording the audit

## The audit

Cover every collection on a hot path: fields, locals, parameters, return values, caches, and those hidden behind helpers and library calls. Code whose sizes are provably small and that does not run hot (rule 8 in "Rule details" in `WORKFLOW.md`) is left out, with one line saying why. A collection a candidate approach introduces gets the same audit before the approach is chosen. For each collection, establish all four:

1. **Dominant operations.** What the code actually does to the collection, and how often per operation of the caller: lookup by key, membership, insert or remove at the ends or the middle, iteration, sorted iteration, range or nearest-value queries, taking the minimum or maximum, grouping, counting, updates to stored keys, and whether it is built once or changes throughout. The operation that costs the most in total, count times size, is dominant. Name the question each loop over the collection answers, not only the calls that implement it: a scan for the smallest element is "take the minimum", a filter inside a loop is a lookup, a loop over a slice is a range query.
2. **Current cost.** Each operation's cost from the "Built-in structures" section of the language file, multiplied by how often it runs. Library structures have documented costs; do not assume them from the name.
3. **Best structure.** The one that makes the dominant operation as cheap as possible, from the table below, named concretely from the "Built-in structures" section of the language file (if none matches, "When the best technique is not available" in `ALGORITHM-ARSENAL.md`), confirmed against the "Valid when" column of the section it names, and able to provide what callers rely on: iteration order (insertion, sorted, or none), duplicates, which equality it uses, null handling, whether callers modify what they receive, and whether threads share it. Name it even when you will not switch to it.
4. **Reason for not switching.** One of: it is already the best; callers rely on something no version of the best structure can provide (name it); it exceeds a hard memory budget (give the numbers); sizes are provably small; it needs a dependency the developer declined; or the chosen approach replaces or removes the collection (name the approach). "It works", "it is the one already there", and "it uses more memory" are not reasons.

## Which structure suits the operations

Section names are in `CORE-TECHNIQUES.md` unless a file is named. When a language lacks one of these, see "When the best technique is not available" in `ALGORITHM-ARSENAL.md`.

| What the code mostly does | Usually suits | Read |
|---|---|---|
| Lookup, membership, counting, or grouping by key, order irrelevant | Hash map (of counts or of lists) or hash set | "Lookup, membership, counting" |
| Lookup by key, and iteration in insertion order | Insertion-ordered hash map, or an array plus a hash index | Language file ("Built-in structures": which maps keep insertion order); "Ordering" in `BEHAVIOR-TRAPS.md` |
| Lookup by small dense integers or enum values | Array indexed by key; a bitset for membership | "Lookup, membership, counting" |
| Append, iterate, access by index | Dynamic array; a linked list is O(n) by index and slower at append and iteration despite the same bounds | Language file |
| Add or remove at either end (queues, sliding work lists) | Deque or ring buffer | "Order and search" |
| Insert or remove in the middle at a known position | Linked list with node handles, gap buffer when edits cluster, balanced tree | "Order and search"; for text, "Strings" in `techniques/strings-and-text.md` |
| Repeatedly take the minimum or maximum of a changing set | Binary heap | "Priority and selection" |
| Top k of many | Heap bounded to k; a stable bounded insertion when k is small and ties keep input order | "Priority and selection" |
| Minimum and maximum together, or a priority queue whose entries are also cancelled or re-prioritized | Sorted map of value to count (a sorted multiset where the language has one); or a heap with lazy deletion: push the new entry and skip stale ones when popped | "Priority and selection"; "Combinations" (heap + hash map) |
| Sorted iteration or sorted output, with inserts between reads | Append, then sort once before each read when reads are rare; binary insertion when reads and inserts interleave and n is modest; otherwise a sorted map | "Order and search" (the re-sorting row) |
| Range, floor, ceiling, predecessor, or successor queries, with updates | Sorted map or balanced tree | "Structures for repeated queries" |
| Those same queries on data that does not change | Sorted array and binary search | "Order and search" |
| Range sums or aggregates, with point updates | Fenwick tree or segment tree | "Structures for repeated queries" |
| Are these connected, with merges only | Union-find | "Structures for repeated queries" |
| Prefix lookup over strings | Trie | "Structures for repeated queries" |
| Recently used entries within a size limit | The language's bounded LRU where it has one; otherwise an insertion-ordered hash map, removing and re-inserting an entry on each hit and evicting its first entry; a hash map plus linked list only when neither exists | "Structures for repeated queries"; "Caching and eviction" in `techniques/specialized-structures.md` |
| Whole collection copied on every update to stay immutable or keep old versions | Build once and freeze when it stops changing; otherwise a persistent structure with structural sharing | "Production patterns"; "Specialized data structures" in `techniques/specialized-structures.md` |
| Read and written by several threads | The platform's concurrent structure, or the plain structure under one lock; a lock-free ring buffer only for exactly one producer and one consumer, with contention measured | "Contention and synchronization" in `techniques/hardware-and-concurrency.md`; "Concurrency" in `BEHAVIOR-TRAPS.md` |
| Overlap queries, timers, approximate membership or counts, a hash table the project implements itself | Interval tree, timing wheel, filters and sketches, table design | `techniques/specialized-structures.md` |
| A graph: neighbor iteration, edge tests, or whole-graph traversal | Adjacency list, matrix, or compressed form, by density and by which operation dominates | "Choosing a representation" in `techniques/graphs-and-trees.md` |
| Points or shapes in space; text search | Domain structures | `ADVANCED-TECHNIQUES.md` |

**Several access patterns on the same data** (lookup by key and order by time) usually need one structure per pattern, or a single combined structure. Every path that changes the data has to update all of them, and the memory counts toward rule 1.

## Choosing the best structure

- **Look past today's operations.** The table answers for what the code does now. A different algorithm can need a structure the code does not use at all, so also ask what structure would make a better algorithm possible, and take the lowest complexity reachable (rule 6).
- **Time comes first.** Extra memory that lowers time complexity is worth spending, whatever its size, as long as it fits the memory actually available (rule 1); if it does not, present both costs and ask. The time has to really go away: an index built for a single lookup saves nothing, and at provably small sizes a small array can beat a hash map.
- **Check the rest of the workload.** Making the dominant operation cheap can make a rarer one expensive enough to become dominant: multiply each operation's new cost by its count and compare totals, build cost included.
- **Replacing a structure is where behavior changes hide:** iteration order, duplicates collapsing, a different equality, and rejected nulls. Walk "Ordering", "Equality and keys", "Duplicates and nulls", and "Mutation and aliasing" in `BEHAVIOR-TRAPS.md`. With attacker-chosen keys, see `techniques/hostile-inputs.md`.
- **Prefer what is already available:** the language's own structures (rule 14), then the project's own and those from direct dependencies in its manifest. Beyond that, follow "When the best technique is not available" in `ALGORITHM-ARSENAL.md`, which offers a maintained package beside writing one; a new dependency needs permission (rule 7).

## Recording the audit

One entry per collection, under "Data structures" in the item (`REPORTING.md`) or the performance decisions (`WRITING-NEW-CODE.md`):

```
`pending` (array, Scheduler:41). Dominant: remove from front, 1 per job, n ≈ 20,000.
Now: O(n) per removal, O(n²) total. Best: deque, O(1) amortized, keeps order ("Order and search"). Switching.
`labels` (hash map, Scheduler:18). Dominant: lookup, 1 per job.
Now: O(1) expected. Best: hash map. Not switching: already the best.
```

## References

This file routes to tables held elsewhere. Sources are in the reference files of those tables, such as `references/CORE-TECHNIQUES.md`.
