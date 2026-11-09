# C

Record the C standard (`-std=c99`, `c11`, `c17`, `c23`), the compiler and version (GCC, Clang, MSVC), the target, and the optimization flags; builtins and headers below depend on them. C++ projects build a `CPP.md` profile with `GENERIC.md` and also use this file for the subset the languages share (undefined behavior, flags, sanitizers, number parsing, shifts); it does not cover the C++ standard library.

**Contents:** Built-in structures · Hidden costs · Bit manipulation · C-specific traps · Testing and benchmarking · References

## Built-in structures

| Structure or function | API | Key costs | Notes |
|---|---|---|---|
| Fixed array | `T a[n]`, `malloc(n * sizeof(T))` | index O(1) | No bounds checking; `n * sizeof(T)` can overflow to a small size, so check `n <= SIZE_MAX / sizeof(T)` or use `calloc` |
| Growable array | `realloc` with geometric growth | append amortized O(1) | Fixed-amount growth is O(n²) total; check that doubling cannot overflow, and keep the old pointer until `realloc` succeeds |
| Sorting | `qsort` | O(n log n) average; stability and worst case unspecified by the standard | glibc's is a merge sort, stable when it can allocate memory, and has changed between releases; other C libraries' are not stable |
| Binary search | `bsearch` | O(log n) | Returns any matching element among duplicates, or `NULL` |
| Strings | `<string.h>` | `strlen` is O(n); `strcat` is O(destination + source) | Null-terminated; length is not stored |
| Memory moves | `memmove`, `memcpy`, `memset` | O(n), highly optimized | `memcpy` requires non-overlapping regions |

**Not in the standard library: hash maps, hash sets, balanced trees, heaps, queues, deques, bitsets, tries.** In order of preference: what the project already has (its own containers, or GLib, APR, klib, uthash, stb_ds if already a dependency); a small in-project implementation with its own tests (growable array, open-addressing hash table, see "Hash table design" in `techniques/specialized-structures.md`, binary heap, ring buffer, bitset over `uint64_t`); a new library, including a copied single-header one, is a dependency (rule 7).

## Hidden costs

| Pattern | Cost | Fix |
|---|---|---|
| `for (i = 0; i < strlen(s); i++)` | O(n²) | Compute the length once, if the loop does not change `s` |
| `strcat(buf, piece)` in a loop | Rescans `buf`: O(n²) | Track the end pointer or length |
| `realloc(p, size + 1)`, or constant growth per append | O(n²) copying | Multiply capacity by 1.5 or 2 |
| Removing from the front with `memmove` | O(n) per removal | Head index or ring buffer |
| Linear search inside another loop | O(n·m) | Sort plus `bsearch`, or an in-project hash table |
| `malloc`/`free` per element in hot loops | Allocator overhead, fragmentation | Preallocate, arena or pool, or elements in an array |
| Linked lists in hot paths | A cache miss per node | Arrays or index-based links |
| `sprintf`/`snprintf`/`printf` in hot loops | Format parsing and locking | Direct conversion, buffered output. A bounded call (`snprintf`, a length-checked copy) stays bounded: trading it for `sprintf` or `strcpy` is a buffer overflow |
| A `qsort` comparator that parses, or calls `strlen` or `strtol` | Runs inside every comparison | Sort an array of structs holding the computed key and a pointer to the element; `qsort`'s tie order stays unspecified |
| `qsort` on small or hot inputs | Indirect comparator calls | Specialized sort only if a benchmark shows it matters |

### Input handling and security

- **Number parsing.** `atoi` and `atof` cannot report errors, and overflow in them is undefined behavior. `strtol` skips leading whitespace, accepts a sign, accepts `0x` and leading-zero octal with base 0, sets `errno` to `ERANGE` on overflow, and stops at the first bad character (callers check `endptr`). `strtod` also accepts `nan`, `inf`, and hex floats, and uses the locale's decimal point, as do `printf("%f")` and `scanf`. A hand-written parser has to match all of this.
- **`<ctype.h>` on `char`.** `isdigit(c)` with a negative `char` (a non-ASCII byte where `char` is signed) is undefined behavior; cast to `unsigned char`. The classification and case functions depend on the locale.
- **Sizes from input.** Lengths, counts, and offsets read from input can overflow and wrap, giving a small allocation and a large copy. Check before multiplying or adding, and check a length field against the bytes actually remaining.
- **Hash tables written in the project** use a fixed hash unless seeded, so chosen keys make every lookup O(n). For untrusted keys, use a keyed hash (SipHash) with a per-process seed.
- **Stack.** Recursion on input depth, and a VLA or `alloca` sized from input, overflow the stack and crash (8 MB main thread on typical Linux, far less on other threads and embedded targets). POSIX `regexec` with backreferences can take exponential time.

## Bit manipulation

| Operation | C |
|---|---|
| And, or, xor, not, shifts | `&`, `\|`, `^`, `~`, `<<`, `>>` |
| Popcount, trailing / leading zeros (C23) | `<stdbit.h>`: `stdc_count_ones`, `stdc_trailing_zeros`, `stdc_leading_zeros` |
| Same (GCC, Clang) | `__builtin_popcount(ll)`, `__builtin_ctz(ll)`, `__builtin_clz(ll)` |
| Same (MSVC) | `__popcnt`, `_BitScanForward`, `_BitScanReverse` |
| Fixed-width types | `<stdint.h>`: `uint32_t`, `uint64_t` |

Use unsigned types. Shifting by at least the type width is undefined; so are left-shifting a negative value and a signed left shift that overflows. Right-shifting a negative value is implementation-defined. `__builtin_ctz(0)` and `__builtin_clz(0)` are undefined.

## C-specific traps

- **Undefined behavior.** Signed overflow, out-of-bounds access, use after free, uninitialized reads, strict-aliasing violations, and invalid shifts are not slow paths but UB: the compiler assumes they never happen, so code relying on them behaves differently at different optimization levels.
- **`qsort` stability.** Code may depend on glibc's stable-in-practice order without knowing it; a hand-written unstable sort changes the order of equal elements there. Comparators written as `return a - b;` overflow; keep the original comparator's exact behavior.
- **`bsearch` returns any match**, where a linear search returned the first.
- **Unsigned wraparound.** `for (size_t i = n - 1; i >= 0; i--)` never ends; reversing loop direction with unsigned indices is a common bug.
- **Integer promotions.** `(uint8_t)x << 24` promotes to `int` and is undefined for `x >= 0x80`; changing operand widths changes results.
- **`memcmp` and byte hashing of structs** include uninitialized padding and compare float bit patterns (`-0.0` differs from `0.0`, NaN equals itself). They are not a faster field-by-field `==`.
- **Word-at-a-time reads** through a cast `char*` violate aliasing and alignment; `memcpy` into the wider type, and account for endianness.
- **Ownership, reentrancy, `errno`.** Who allocates and frees is part of the contract; returning a pointer into an internal, static, or cached buffer changes lifetimes for callers. Static buffers, `strtok`, and global caches make code non-reentrant and thread-unsafe. Callers may read `errno` and specific return codes.
- **Compiler flags are behavior.** `-ffast-math`, `-ffp-contract`, and vectorization change floating-point results; higher optimization, LTO, or `restrict` can expose existing UB, and a `restrict` that does not hold is UB.

## Testing and benchmarking

- **Tests:** the project's framework (Unity, CMocka, Check, Criterion, greatest), or a plain `assert` program. Makefiles, `configure`, and CMake (`execute_process`, custom commands) run shell commands; compiling the test program directly avoids them.
- **Testing an extracted function:** keep it out of the public header: declare it in an internal header, or have the test include the `.c` file so a `static` function stays `static`.
- **Sanitizers:** run differential tests with `-fsanitize=address,undefined`, and under Valgrind if the project uses it.
- **Benchmarks:** the project's release flags (`-O0` or a sanitizer build measures something else). `clock_gettime(CLOCK_MONOTONIC)` or `QueryPerformanceCounter`, medians, results stored to a `volatile` sink. `perf` for hotspots and cache misses; Massif or heaptrack for peak heap.
- **Verification beyond tests** ("Verification levels" in `DIFFERENTIAL-TESTING.md`): CBMC, including equivalence harnesses asserting `old(x) == new(x)` within bounds; KLEE; Frama-C with WP or E-ACSL.
- **Constant-time comparison:** `CRYPTO_memcmp` (OpenSSL), `sodium_memcmp`, or `timingsafe_bcmp`. `memcmp` returns at the first differing byte.

## References

Sources: `references/languages/C.md`.
