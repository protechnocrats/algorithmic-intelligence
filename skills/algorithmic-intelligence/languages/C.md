# C

Load this file for C projects. Record the C standard (`-std=c99`, `c11`, `c17`, `c23`), the compiler and version (GCC, Clang, MSVC), the target platform, and the optimization flags. Builtins and headers below depend on them. For C++ projects, use `GENERIC.md`; this file does not cover the C++ standard library.

## Built-in structures

C's standard library has almost no data structures. What it provides:

| Structure or function | API | Key costs | Notes |
|---|---|---|---|
| Fixed array | `T a[n]`, `malloc(n * sizeof(T))` | index O(1) | No bounds checking |
| Growable array | `realloc` with **geometric** growth (double the capacity) | append amortized O(1) | Growing by a fixed amount is O(n²) total |
| Sorting | `qsort` | O(n log n) average; **not stable**; worst case is implementation-defined | Comparator called through a function pointer |
| Binary search | `bsearch` | O(log n) | Returns **any** matching element among duplicates, or `NULL` |
| Strings | `<string.h>` | **`strlen` is O(n)**; `strcat` is O(length of destination + source) | Null-terminated; length is not stored |
| Memory moves | `memmove`, `memcpy`, `memset` | O(n), highly optimized | `memcpy` requires non-overlapping regions |

**Not in the standard library: hash maps, hash sets, balanced trees, heaps, queues, deques, bitsets, or tries.** Options, in order:

1. Use what the project already has: its own containers, or a library it already depends on (GLib, APR, klib, uthash, stb_ds).
2. A small in-project implementation with its own tests: a growable array, an open-addressing hash table for a known key type (see "Hash table design" in `techniques/data-structures.md`), a binary heap, a ring buffer, or a bitset over `uint64_t` words.
3. A new library, including copying a single-header library into the tree, is a dependency. Ask first (rule 7).

## Hidden costs

| Pattern | Cost | Fix |
|---|---|---|
| `for (i = 0; i < strlen(s); i++)` | `strlen` runs every iteration: O(n²) | Compute the length once before the loop (only if the loop does not change `s`) |
| `strcat(buf, piece)` in a loop | Rescans `buf` each time: O(n²) | Track the end pointer or current length and copy there |
| `realloc(p, size + 1)` or growth by a constant per append | O(n²) total copying | Geometric growth (multiply capacity by 1.5 or 2) |
| Removing from the front of an array with `memmove` | O(n) per removal | Head index or ring buffer |
| Linear search with a loop over an array inside another loop | O(n·m) | Sort plus `bsearch`, or an in-project hash table |
| `malloc`/`free` per element in hot loops | Allocator overhead and fragmentation | Preallocate, use an arena or pool, or embed elements in an array |
| Linked lists traversed in hot paths | Cache misses on every node | Arrays or index-based links |
| `sprintf`/`snprintf` or `printf` in hot loops | Format parsing and locking | Direct conversion, buffered output |
| `qsort` on small fixed-size or hot inputs | Indirect comparator calls | Specialized sort only if a benchmark shows it matters |
| Recomputing values a struct could cache (lengths, counts) | Repeated O(n) work | Store and maintain the value, if every writer updates it |

## Bit manipulation

| Operation | C |
|---|---|
| And, or, xor, not, shifts | `&`, `\|`, `^`, `~`, `<<`, `>>` |
| Popcount, trailing / leading zeros (C23) | `<stdbit.h>`: `stdc_count_ones`, `stdc_trailing_zeros`, `stdc_leading_zeros` |
| Popcount, trailing / leading zeros (GCC, Clang) | `__builtin_popcount(ll)`, `__builtin_ctz(ll)`, `__builtin_clz(ll)` |
| Popcount, bit scan (MSVC) | `__popcnt`, `_BitScanForward`, `_BitScanReverse` |
| Fixed-width types | `<stdint.h>`: `uint32_t`, `uint64_t` |

Use **unsigned** types for bit manipulation. In C:

- shifting by a count greater than or equal to the type width is **undefined behavior**;
- left-shifting a negative value, or a signed left shift whose result does not fit the type, is undefined behavior;
- right-shifting a negative value is implementation-defined;
- `__builtin_ctz(0)` and `__builtin_clz(0)` are undefined.

## C-specific traps

- **Undefined behavior.** A rewrite must never introduce undefined behavior: signed integer overflow, out-of-bounds access, use after free, uninitialized reads, strict-aliasing violations, or invalid shifts. The compiler may assume undefined behavior never happens, so a rewrite that relies on it can behave differently at different optimization levels. Run differential tests under sanitizers (see Testing).
- **`qsort` is not stable.** Switching to or from a stable sort changes the order of equal elements. Comparators written as `return a - b;` overflow for large values; keep the original comparator's exact behavior when replacing it.
- **`bsearch` returns any matching element.** If the original linear search returned the first match, a `bsearch` replacement can return a different one.
- **Unsigned wraparound.** `for (size_t i = n - 1; i >= 0; i--)` never ends; rewriting loop directions with unsigned indices is a common source of bugs.
- **Integer promotions and implicit conversions** change results when rewriting arithmetic with narrower or wider types.
- **Ownership and lifetimes.** Who allocates and who frees must stay the same. Returning a pointer into an internal buffer, a static buffer, or a cache changes ownership and lifetime for callers.
- **Reentrancy and thread safety.** Static buffers, `strtok`, and global caches make functions non-reentrant and unsafe across threads.
- **`errno` and error returns.** Callers may check `errno` or specific return codes; a rewrite must set them identically.
- **Floating point.** `-ffast-math`, `-ffp-contract`, and vectorization can change results. Do not change floating-point compiler flags as an optimization without developer review.
- **Compiler flags are part of behavior.** Changing optimization levels, enabling LTO, or adding `restrict` can expose existing undefined behavior; `restrict` that is not actually true is undefined behavior.

## Testing and benchmarking

- **Tests:** whatever the project uses (Unity, CMocka, Check, Criterion, greatest), or a plain `assert`-based test program if it has nothing. A new framework is a dependency; ask first.
- **Sanitizers:** build and run differential tests with `-fsanitize=address,undefined` (GCC and Clang) where available. Also run under Valgrind if the project already uses it.
- **Benchmarks:** compile both versions with the project's release flags. Time with `clock_gettime(CLOCK_MONOTONIC)` (POSIX) or `QueryPerformanceCounter` (Windows), repeat runs, and report medians. Store results in a `volatile` sink so the compiler cannot remove the measured work. Use `perf` or the platform profiler for cache-miss and hotspot evidence.
- **Memory:** Valgrind Massif or heaptrack for peak heap; count allocations with a wrapper if no tool is available.
- **Verification beyond tests** (see "Verification levels" in `DIFFERENTIAL-TESTING.md`; installs, so ask unless present): CBMC for bounded model checking, including equivalence harnesses that assert `old(x) == new(x)` for every input within stated bounds; KLEE for symbolic execution; Frama-C with WP (proofs of ACSL contracts) or E-ACSL (runtime checking of the same contracts).
- **Constant-time comparison** (for secrets; see `techniques/hostile-inputs.md`): `CRYPTO_memcmp` (OpenSSL), `sodium_memcmp` (libsodium), or `timingsafe_bcmp` where the C library provides it, never `memcmp`.

## References (for verifying claims; not required reading)

- C standard library reference: en.cppreference.com/w/c; GNU C Library manual: www.gnu.org/software/libc/manual/
