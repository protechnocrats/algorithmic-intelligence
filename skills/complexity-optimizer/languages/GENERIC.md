# Other Languages

Use this file for any language without a dedicated companion file: Go, C++, Dart, Ruby, PHP, Scala, F#, Haskell, or anything else. The skill applies fully to every language. Build the missing language knowledge before analyzing any candidate, and state any uncertainty in the report.

## Build a language profile first

Before Phase 3, write down for the project's language and version, from official documentation where possible:

1. **Built-in structures and their costs.** Dynamic array, hash map, hash set, insertion-ordered map, sorted map/set, queue/deque, priority queue, bitset, string builder. For each: whether it exists in the standard library and its access, insert, delete, and search costs.
2. **What needs a dependency.** Every structure from the list above that is not in the standard library. Each requires developer permission (rule 7).
3. **Hidden costs.** Operations that look O(1) but are not: removal from the front of arrays, string concatenation, list indexing on linked structures, length operations on strings, copying on assignment, lazy re-evaluation.
4. **Ordering guarantees.** Whether hash structures have defined iteration order, whether it is randomized, and which sorts are stable.
5. **Numbers.** Integer widths, overflow behavior (wrap, trap, or arbitrary precision), and bitwise operator semantics.
6. **Evaluation model.** Eager or lazy collections, value or reference semantics, and copy-on-write behavior.
7. **Native versus host platform.** If the language runs on or interoperates with another platform (JVM, .NET, JavaScript runtimes, Objective-C, C libraries), list which structures the language provides itself and which come only from the platform. Prefer the language's own when both exist (rule 14).
8. **Tooling.** The test framework, any property-based testing library already in the project, the benchmark tool and profiler already in the project, the language's constant-time comparison primitive for secrets, and any verification tools for the language (bounded model checkers, concurrency checkers, proof tools; see "Verification levels" in `DIFFERENTIAL-TESTING.md`).

If the documentation does not state a cost or a guarantee, treat it as unknown: do not rely on it for an optimization, and mention it in the report.

## Then follow the normal workflow

All rules, `WORKFLOW.md`, `ALGORITHM-ARSENAL.md`, `CORE-TECHNIQUES.md`, `DIFFERENTIAL-TESTING.md`, `BENCHMARKING.md`, and `BEHAVIOR-TRAPS.md` apply unchanged. Tell the developer that no dedicated language file exists and that the profile above was built during the run.
