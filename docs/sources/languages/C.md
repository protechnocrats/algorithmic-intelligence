# Sources for `skills/languages/C.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill. Section numbers are from the C17 standard (ISO/IEC 9899:2018); the free draft N2176 uses the same numbering.

## Built-in structures

- `malloc` size overflow and `calloc`: C17 7.22.3.2 (`calloc`) and 7.22.3.4 (`malloc`); cppreference pages "calloc" and "malloc" (en.cppreference.com/w/c/memory/calloc).
- `realloc` keeping the old block on failure: C17 7.22.3.5; cppreference "realloc".
- `qsort` stability and complexity unspecified: C17 7.22.5.2. glibc's merge sort, its fallback, and changes between releases: glibc manual, "Array Sort Function" (www.gnu.org/software/libc/manual/html_node/Array-Sort-Function.html), and `stdlib/qsort.c` and the `NEWS` file in the glibc source (sourceware.org/git/glibc.git); the implementation changed in recent releases, so read the version the project links against.
- `bsearch` returning any matching element: C17 7.22.5.1.
- `strlen`, `strcat`: C17 7.24.6.3 and 7.24.3.1. `memcpy` requiring non-overlapping regions, `memmove` allowing them: C17 7.24.2.1 and 7.24.2.2.

## Input handling and security

- `atoi`/`atof` undefined on overflow: C17 7.22.1.2 ("If the value of the result cannot be represented, the behavior is undefined").
- `strtol` (whitespace, sign, base 0 prefixes, `ERANGE`, `endptr`): C17 7.22.1.4. `strtod` (`nan`, `inf`, hex floats, locale decimal point): C17 7.22.1.3; the locale's effect on `printf` and `scanf`: C17 7.11.1.1 (`setlocale`, `LC_NUMERIC`).
- `<ctype.h>` arguments must be `EOF` or representable as `unsigned char`: C17 7.4 paragraph 1.
- Keyed hashing against chosen collisions: Jean-Philippe Aumasson and Daniel J. Bernstein, "SipHash: a fast short-input PRF," INDOCRYPT 2012; Crosby and Wallach, USENIX Security 2003 (see `docs/sources/techniques/hostile-inputs.md`).
- Default 8 MB main-thread stack on typical Linux: the `RLIMIT_STACK` soft limit in getrlimit(2) (man7.org/linux/man-pages/man2/getrlimit.2.html), whose default distributions set to 8 MiB; it is configuration, not a guarantee.
- POSIX `regexec` with backreferences: POSIX.1-2017, Base Definitions, chapter 9 "Regular Expressions" (backreferences in basic regular expressions); matching with backreferences is NP-hard (Alfred V. Aho, "Algorithms for Finding Patterns in Strings," *Handbook of Theoretical Computer Science*, 1990).

## Bit manipulation

- C23 `<stdbit.h>` (`stdc_count_ones`, `stdc_trailing_zeros`, `stdc_leading_zeros`): ISO/IEC 9899:2024 section 7.18; cppreference header page "Standard library header <stdbit.h>".
- GCC and Clang `__builtin_popcount`, `__builtin_ctz`, `__builtin_clz`, and the undefined result for 0: GCC manual, "Bit Operation Builtins" (named "Other Builtins" in older manuals), at gcc.gnu.org/onlinedocs/gcc/.
- MSVC `__popcnt` and the CPU support it assumes: learn.microsoft.com/cpp/intrinsics/popcnt16-popcnt-popcnt64. `_BitScanForward`, `_BitScanReverse`: learn.microsoft.com/cpp/intrinsics/bitscanforward-bitscanforward64 and bitscanreverse-bitscanreverse64.
- Shifts by at least the width, negative left shifts, and signed overflow undefined; right shift of a negative value implementation-defined: C17 6.5.7 paragraphs 3 to 5.

## C-specific traps

- Signed overflow undefined: C17 6.5 paragraph 5. Strict aliasing: C17 6.5 paragraph 7.
- Integer promotions (`uint8_t` to `int`): C17 6.3.1.1 paragraph 2.
- Padding bytes have unspecified values (so `memcmp` on structs compares them): C17 6.2.6.1 paragraph 6.
- `restrict` that does not hold is undefined: C17 6.7.3.1.
- `-ffast-math` and `-ffp-contract`: GCC manual, "Options That Control Optimization" (gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html).
- `strtok` non-reentrant: C17 7.24.5.8; POSIX `strtok_r`.

## Testing and benchmarking

- Sanitizers: clang.llvm.org/docs/AddressSanitizer.html and clang.llvm.org/docs/UndefinedBehaviorSanitizer.html; GCC manual, "Program Instrumentation Options".
- `clock_gettime(CLOCK_MONOTONIC)`: POSIX.1-2017 `clock_getres`; `QueryPerformanceCounter`: learn.microsoft.com/windows/win32/sysinfo/acquiring-high-resolution-time-stamps.
- CBMC equivalence harnesses: the CBMC user manual at www.cprover.org/cprover-manual/. KLEE: klee-se.org. Frama-C WP and E-ACSL: frama-c.com/fc-plugins/wp.html and frama-c.com/fc-plugins/e-acsl.html.
- Constant-time comparison: OpenSSL `CRYPTO_memcmp` (docs.openssl.org/master/man3/CRYPTO_memcmp/); libsodium `sodium_memcmp` ("Helpers" at doc.libsodium.org); `timingsafe_bcmp` (man.openbsd.org/timingsafe_bcmp).
