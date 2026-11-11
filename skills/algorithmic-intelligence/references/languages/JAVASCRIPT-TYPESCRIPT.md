# JavaScript and TypeScript

Record the runtime (Node version, browsers, Deno, Bun, Hermes) and the ECMAScript target. TypeScript types are erased, so every runtime cost below applies to both.

**Contents:** Built-in structures · Hidden costs · Bit manipulation · JavaScript-specific traps · Testing and benchmarking

## Built-in structures

| Structure | API | Key costs | Notes |
|---|---|---|---|
| Array | `[]` | index O(1), `push`/`pop` amortized O(1), `shift`/`unshift`/`splice` O(n), `includes`/`indexOf`/`find` O(n) | |
| Map | `Map` | O(1) average | Insertion order; any key type; SameValueZero keys. Bounded LRU: `delete` then `set` on a hit, evict `keys().next().value` (a plain `set` on an existing key keeps its old position) |
| Set | `Set` | O(1) average | Insertion order; objects by reference |
| Plain object as map | `{}`, `Record<string, T>` | O(1) average | Keys become strings; inherited keys (`constructor`, `__proto__`) are traps; prefer `Map` for dynamic keys |
| Weak references | `WeakMap`, `WeakSet` | O(1) average | Per-object memoization without leaks |
| Typed arrays | `Int32Array`, `Uint8Array`, `Float64Array`, ... | O(1), fixed size, contiguous | Counting arrays, bitsets (see traps) |
| Big integers | `BigInt` | Arbitrary precision, slower | Exact 64-bit masks |
| Sorting | `sort`, `toSorted` (ES2023) | O(n log n), stable since ES2019 | Default comparator sorts as strings |

### Not in the language

No heap, deque, sorted map or set, balanced tree, trie, binary search, or multi-word bitset. For BFS, an array with a head index replaces `shift()`. Otherwise see "Packages" below, which offers a package beside a short in-project version (a binary heap or ring-buffer deque, with tests).

### Packages

These are dependencies (rule 7). Besides what the project declares and what the developer names, they are the only packages to consider, whether or not the module's manifest declares them: use a declared one like the standard library, and propose an undeclared one when it beats what the standard library offers ("When the best technique is not available" in `ALGORITHM-ARSENAL.md`).

| Package | Provides | Watch for |
|---|---|---|
| `heap-js` | `Heap` (`push`, `pop`, `peek`, `top(n)`), with static `nsmallest` and `nlargest` | A min-heap of integers by default. `top(n)` is unordered except its first element. Iterating the heap directly consumes it. No priority update: `remove`, then `push` |
| `mnemonist` | `Heap`, `FixedDeque`, `LRUCache`, `LRUMap`, `MultiMap`, `MultiSet`, `BiMap`, `Trie`, `BitSet`, `BloomFilter` | Costs are not documented: measure. `BloomFilter` is approximate |
| `lru-cache` | `LRUCache` with `max`, `maxSize`, `ttl` | One of `max`, `ttl`, or `maxSize` is required. TTL is not a strong guarantee. Keys and values cannot be `null` or `undefined`, and `set(key, undefined)` deletes |
| `sorted-btree` | A sorted map with `nextHigherKey`, `nextLowerKey`, `getRange`, and O(1) `clone` | No duplicate keys and no `NaN` keys. `forEach` passes `(value, key)` |
| `lodash` | `sortedIndex`, `sortedIndexBy`, `sortedLastIndex` (binary search) | The array must already be sorted |

## Hidden costs

| Pattern | Cost | Fix |
|---|---|---|
| `queue.shift()` in a loop | O(n) per call, O(n²) total | Head index, or a ring buffer |
| `includes`/`indexOf` inside `filter`, `map`, or a loop | O(n·m) | `new Set(arr)` once |
| `arr.find(o => o.id === id)` in a loop | O(n·m) | `new Map(arr.map(o => [o.id, o]))` once (later duplicates overwrite) |
| `reduce((acc, x) => [...acc, x], [])`, `reduce((acc, x) => ({ ...acc, [x.k]: x }), {})` | O(n²) | Mutate one accumulator, `Object.fromEntries`, or a `Map` |
| `arr = arr.concat(other)` in a loop | O(n²) | Collect, then flatten once. Spreading into a call (`push(...big)`, `Math.max(...arr)`) throws `RangeError` above an engine-dependent count, often tens of thousands |
| `arr.sort((a, b) => parse(a) - parse(b))` | The comparator runs per comparison, so `parse` runs about 2·n log n times | `arr.map(x => [parse(x), x]).sort(([a], [b]) => a - b).map(([, x]) => x)` (stable since ES2019). Not needed for a property read |
| `a.localeCompare(b)` in a comparator over a large array | Slower than a reused collator | One `Intl.Collator` with the same locale and options, and its `compare` |
| `arr.slice(1)` or `[first, ...rest]` in recursion | Copies each call: O(n²) | Pass an index |
| `JSON.stringify(obj)` as a `Map` key | Serializes on every lookup, and depends on property order | A primitive ID or a key built once |
| `Object.keys(obj).length`, `Object.entries(obj)` in a loop | O(n) allocation per call | Compute once, or track size |
| `JSON.parse(JSON.stringify(x))` to copy | Full serialization | `structuredClone` or no copy; they differ on `Date`, `undefined`, `Map`, functions, class instances |
| `new RegExp(...)` in a loop | A new object each time; engines such as V8 cache compiled patterns by source and flags, so recompilation is not guaranteed, and a dynamic pattern can still miss the cache | Hoist. A hoisted regex with `g` or `y` shares `lastIndex` across calls, changing `test` and `exec` results: reset it or drop the flag |
| `delete obj.key` in hot code | Can deoptimize object shapes | `Map`, or set `undefined` if semantics allow |
| `await` in a loop over independent items | Sequential latency | `Promise.all` or bounded concurrency; this changes ordering and error timing |
| `string += x` in a loop | Usually fine (engines use ropes) | Leave it without a benchmark |

### Input handling and security

- **Number parsing.** `Number("")`, `Number(" ")`, and `Number(null)` are `0`; `Number("0x1F")` is 31; `parseInt("12px")` is 12 and `parseFloat` also stops at the first bad character; `+x` is `Number(x)`. Non-ASCII digits give `NaN`. Integers above 2⁵³ lose precision, including large ids from `JSON.parse`.
- **Regular expressions backtrack** in V8 and most engines. Escape input in a pattern (`RegExp.escape` only in recent runtimes, ES2025; otherwise by hand).
- **Prototype pollution.** Writing input-controlled keys into a plain object (`acc[key] = v`, deep merge, `Object.assign` from parsed JSON) lets `__proto__` replace the object's prototype, and through a recursive merge change `Object.prototype` globally. Replacing a `Map` with an object for speed reopens this; use `Map` or `Object.create(null)`.
- **Hash flooding.** `Map`, `Set`, and object keys are not guaranteed to resist chosen collisions: worst case O(n) per lookup.
- **Recursion** throws `RangeError` at an engine-dependent depth, often around 10,000 frames; `--stack-size` is not a fix.
- **Hidden inputs.** `toLocaleString`, `localeCompare`, `Intl`, and `toLocaleUpperCase` read the runtime's locale; `new Date("2024-01-01")` is UTC but `new Date("2024-01-01T00:00")` is local. `eval`, `new Function`, and `vm` run code from data and are not a sandbox.

## Bit manipulation

| Operation | JavaScript |
|---|---|
| And, or, xor, not | `&`, `\|`, `^`, `~` |
| Shifts | `<<`, `>>` (sign-propagating), `>>>` (zero-fill) |
| Leading zeros | `Math.clz32(x)` |
| Popcount | Not built in: SWAR bit-count, or loop with `x &= x - 1` |
| 64-bit masks | `BigInt` (`1n << 40n`), two 32-bit numbers, or a `Uint32Array` bitset |

**Bitwise operators convert operands to 32-bit signed integers:** bits above 31 are lost, `1 << 31` is negative, `1 << 32` is `1`. `>>> 0` reads a result as unsigned.

## JavaScript-specific traps

- **Default sort compares strings:** `[10, 9, 1].sort()` is `[1, 10, 9]`.
- **Object key order:** integer-like keys come first in ascending order, then string keys in insertion order. A `Map` is pure insertion order, so replacing an object with one changes iteration when keys look like integers.
- **Key types:** `obj[1] === obj["1"]`, but `map.get(1) !== map.get("1")`. Converting between them changes which lookups hit when ids arrive as strings in one place and numbers in another.
- **Typed arrays wrap or clamp:** `Uint8Array` stores 256 as 0 and -1 as 255, `Uint8ClampedArray` clamps, NaN becomes 0, no holes or `undefined`, fixed size.
- **SameValueZero:** `Map`, `Set`, and `includes` find `NaN` and treat `+0` as `-0`; `indexOf` uses strict equality and never finds `NaN`.
- **Objects as keys** compare by reference; key by a primitive when the original compared fields.
- **Numbers are doubles:** integers exact only to 2⁵³ − 1; reordering float arithmetic changes results.
- **String length** counts UTF-16 code units; `[...str]` iterates code points.
- **Holes** are skipped by `forEach`, `map`, and `filter` but visited by `for` loops.
- **Generators and iterators are single-use:** a second `for...of` over a finished generator sees nothing and raises no error.
- **Mutation:** `sort`, `reverse`, `splice` mutate; `toSorted`, `toReversed`, `toSpliced` (ES2023) copy.
- **`Promise.all`** rejects on the first error while the rest keep running and their side effects happen; a sequential loop never starts them.

## Testing and benchmarking

- **Tests:** Jest, Vitest, Mocha, `node:test`. `npm install` runs lifecycle scripts of the project and every dependency; `npm test` runs `pretest` and `posttest`; test configs load setup files; `npx` can download and run a package. Prefer `npm ci --ignore-scripts` when dependencies must be installed.
- **Testing an extracted function:** export it from an internal module that the package's public entry point does not re-export.
- **Property-based testing, if already present:** fast-check, including model-based testing (`fc.commands`) for stateful structures.
- **Profiling:** `node --cpu-prof`, `--heap-prof`; the DevTools Performance panel.
- **Benchmarks:** Vitest `bench`, tinybench, or Benchmark.js if present; otherwise `performance.now()` with warmup, medians, and results kept observable.
- **Verification beyond tests** ("Verification levels" in `DIFFERENTIAL-TESTING.md`): fast-check reaches level 2 with shrinking; reach level 3 by enumerating small domains in tests. TypeScript's checker proves types, never equivalence.
- **Constant-time comparison:** `crypto.timingSafeEqual` in Node; in browsers, `crypto.subtle.verify` for MACs. `timingSafeEqual` throws `RangeError` when the inputs differ in length, where `===` returned `false`: compare fixed-length values (MACs, or hashes of both inputs) or check the length first, or the replacement adds an exception (rule 5).
