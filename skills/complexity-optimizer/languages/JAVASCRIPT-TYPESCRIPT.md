# JavaScript and TypeScript

Load this file for JavaScript and TypeScript projects. Record the runtime (Node version, browsers, React Native, Deno, Bun) and the ECMAScript target. TypeScript types are erased at runtime, so all runtime costs below apply to both.

## Built-in structures

| Structure | API | Key costs | Notes |
|---|---|---|---|
| Array | `[]` | index O(1), `push`/`pop` O(1) amortized, **`shift`/`unshift`/`splice` O(n)**, `includes`/`indexOf`/`find` O(n) | |
| Map | `Map` | get/set/has/delete O(1) average | Iterates in insertion order; any key type; keys compared with SameValueZero |
| Set | `Set` | add/has/delete O(1) average | Insertion order; objects compared by reference |
| Plain object as map | `{}` / `Record<string, T>` | O(1) average | Keys become strings; inherited keys like `constructor` and `__proto__` are traps; prefer `Map` for dynamic keys |
| Weak references | `WeakMap`, `WeakSet` | O(1) average | Memoize per object without leaking memory |
| Typed arrays | `Int32Array`, `Uint8Array`, `Float64Array`, ... | O(1) access, fixed size, contiguous | Good for counting arrays and bitsets |
| Big integers | `BigInt` | Arbitrary precision, slower | Needed for exact 64-bit flag masks |
| Sorting | `Array.prototype.sort`, `toSorted` (ES2023) | O(n log n), stable since ES2019 | **Default comparator sorts as strings** |

### Not in the language

**No heap/priority queue, deque, sorted map/set, balanced tree, trie, or multi-word bitset.** Options, in order:

1. A small in-project implementation with tests (a binary heap or a ring-buffer deque is short).
2. For BFS-style queues: an array with a head index instead of `shift()`.
3. A dependency only with permission (rule 7). Check whether the project already depends on one.

## Hidden costs

| Pattern | Cost | Fix |
|---|---|---|
| `queue.shift()` in a loop (BFS, job queues) | O(n) per call in general, O(n²) total | Head index pointer, or a ring buffer |
| `arr.includes(x)` / `indexOf` inside `filter`, `map`, or a loop | O(n·m) | `new Set(arr)` built once |
| `arr.find(o => o.id === id)` inside a loop | O(n·m) | `new Map(arr.map(o => [o.id, o]))` once (later duplicates overwrite) |
| `reduce((acc, x) => [...acc, x], [])` | O(n²) | `push` into one array, or `map`/`filter` |
| `reduce((acc, x) => ({ ...acc, [x.k]: x }), {})` | O(n²) | Mutate one accumulator, or `Object.fromEntries`, or a `Map` |
| `arr = arr.concat(other)` in a loop | O(n²) | `push(...other)` for small chunks, or collect then flatten once |
| `Object.keys(obj).length` or `Object.entries(obj)` inside a loop | O(n) allocation per call | Compute once, or track size |
| `JSON.parse(JSON.stringify(x))` for copying | Full serialization | `structuredClone`, or avoid the copy |
| `new RegExp(...)` in a loop | Recompiles each time | Hoist |
| `delete obj.key` in hot code | Can deoptimize object shapes | `Map`, or set to `undefined` if semantics allow |
| `await` inside a loop over independent items | Sequential latency | `Promise.all` / bounded concurrency, which changes ordering and error behavior; ask first |
| `string += x` in a loop | Usually fine in modern engines (ropes) | Do not "optimize" without a benchmark; `join` when building from an array |

## Front-end and React Native hot spots

- **Layout thrashing.** Reading layout (`offsetHeight`, `getBoundingClientRect`) after writes inside a loop forces a layout each iteration. Batch reads, then writes.
- **React.** Expensive computation in render runs on every render: `useMemo` with correct dependencies. Unstable props (new arrays, objects, and functions each render) defeat `React.memo`. Lists need stable `key`s. Avoid storing derived data in state.
- **Large lists.** Virtualize (`FlatList` in React Native, windowing libraries on the web; the latter are dependencies).

## Bit manipulation

| Operation | JavaScript |
|---|---|
| And, or, xor, not | `&`, `\|`, `^`, `~` |
| Shifts | `<<`, `>>` (sign-propagating), `>>>` (zero-fill, unsigned) |
| Leading zeros | `Math.clz32(x)` |
| Popcount | Not built in; write it (for example, the SWAR bit-count) or loop with `x &= x - 1` |
| 64-bit masks | `BigInt` (`1n << 40n`), or two 32-bit numbers, or a `Uint32Array` bitset |

**Bitwise operators convert operands to 32-bit signed integers.** Values at or above 2³¹ become negative, and bits above 31 are lost. `1 << 31` is negative; `1 << 32` is `1`. Use `>>> 0` to read a result as unsigned. Use bitmasks only when every flag fits in 31 or 32 bits, or use `BigInt`/typed arrays.

## JavaScript-specific traps

- **Default sort compares strings:** `[10, 9, 1].sort()` gives `[1, 10, 9]`. Keep the original comparator exactly.
- **Object key order:** integer-like keys enumerate in ascending numeric order first, then string keys in insertion order. Replacing an object with a `Map` (pure insertion order) changes iteration order when keys look like integers.
- **SameValueZero:** `Map` and `Set` treat `NaN` as equal to `NaN` and `+0` equal to `-0`; `indexOf` uses strict equality (`NaN` is never found), while `includes` uses SameValueZero. Converting `indexOf` checks to a `Set` changes `NaN` behavior.
- **Objects as keys** compare by reference in `Map`/`Set`; a linear search comparing fields does not. Key by a primitive (an id or a composed string) when the original compared by value.
- **Numbers are doubles.** Integers are exact only up to 2⁵³ − 1. Floating-point reordering changes results.
- **String length** counts UTF-16 code units; `[...str]` and `Array.from(str)` iterate code points. Switching between them changes results for emoji and non-BMP characters.
- **Sparse arrays and holes** are skipped by `forEach`, `map`, and `filter` but visited by `for` loops.
- **Mutation:** `sort`, `reverse`, and `splice` mutate in place; `toSorted`, `toReversed`, and `toSpliced` (ES2023) return copies.
- **Async ordering:** `Promise.all` rejects on the first error, while a sequential loop stops at the error after earlier side effects; `Promise.allSettled` continues. All three behave differently.

## Testing and benchmarking

- **Tests:** Jest, Vitest, Mocha, `node:test`; React Testing Library for components.
- **Property-based testing, if already present:** fast-check.
- **Profiling:** `node --cpu-prof` or `--heap-prof`; the DevTools Performance panel; React DevTools Profiler.
- **Benchmarks, if already present:** Vitest `bench`, tinybench, Benchmark.js. Otherwise `performance.now()` with warmup and medians, keeping results observable so the JIT cannot discard work.
- **Verification beyond tests** (see "Verification levels" in `DIFFERENTIAL-TESTING.md`): fast-check reaches level 2 with shrinking, and its model-based testing (`fc.commands`) checks stateful structures against a simple model. Reach level 3 by enumerating small domains exhaustively in tests. TypeScript's type checker proves type-level facts only, never equivalence.
- **Constant-time comparison** (for secrets; see `techniques/hostile-inputs.md`): `crypto.timingSafeEqual` in Node.js; in browsers, verify message authentication codes with Web Crypto's `crypto.subtle.verify` rather than comparing bytes.

## References (for verifying claims; not required reading)

- MDN JavaScript reference: developer.mozilla.org/en-US/docs/Web/JavaScript/Reference; ECMAScript specification: tc39.es/ecma262/
