# Sources for `skills/algorithmic-intelligence/references/languages/JAVASCRIPT-TYPESCRIPT.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill. MDN pages are under developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/ followed by the path given (for example `Global_Objects/Array/sort`). Section names in the ECMAScript specification are from tc39.es/ecma262/.

## Built-in structures

- `Array` method behavior: MDN `Global_Objects/Array` and the page for each method. Sort stability (ES2019) and the default string comparison: MDN `Global_Objects/Array/sort`. `toSorted` (ES2023): MDN `Global_Objects/Array/toSorted`.
- `Map` insertion order, SameValueZero keys, and `set` keeping an existing key's position: MDN `Global_Objects/Map` ("Description", "Key equality"). `Set`: MDN `Global_Objects/Set`. `WeakMap`, `WeakSet`: MDN `Global_Objects/WeakMap`.
- Plain objects and inherited keys: MDN `Global_Objects/Object` ("Object prototype properties") and `Global_Objects/Object/create` (`Object.create(null)`).
- Typed arrays and their conversion (wrapping, `Uint8ClampedArray` clamping, NaN to 0): MDN `Global_Objects/TypedArray` ("Value encoding and normalization") and `Global_Objects/Uint8ClampedArray`. `BigInt`: MDN `Global_Objects/BigInt`.

## Packages

- heap-js (`top(n)`, `nsmallest`, iteration consuming the heap, `remove`): README at github.com/ignlg/heap-js.
- mnemonist structures: yomguithereal.github.io/mnemonist (one page per structure).
- lru-cache (`max`, `maxSize`, `ttl` requirement; `null`/`undefined` keys and values; `set(key, undefined)`): README at github.com/isaacs/node-lru-cache.
- sorted-btree (`nextHigherKey`, `nextLowerKey`, `getRange`, O(1) `clone`, `forEach(value, key)`): README at github.com/qwertie/btree-typescript.
- lodash `sortedIndex`, `sortedIndexBy`, `sortedLastIndex`: lodash.com/docs (entries under "Array").
- Release dates for all packages: registry.npmjs.org/<package>.

## Hidden costs

- Argument-count limits on spread calls and `apply`: MDN `Global_Objects/Function/apply` ("Using apply and built-in functions", the engine's argument length limit).
- `localeCompare` versus a reused `Intl.Collator`: MDN `Global_Objects/String/localeCompare` ("Performance").
- `slice` copying: MDN `Global_Objects/Array/slice`. `structuredClone` and what it cannot copy: MDN "Window: structuredClone() method" and "The structured clone algorithm" (developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Structured_clone_algorithm).
- `lastIndex` on regexes with `g` or `y`: MDN `Global_Objects/RegExp/lastIndex`. V8 caching compiled patterns by source and flags: the RegExp table of the compilation cache, `src/codegen/compilation-cache.h` in the V8 source (chromium.googlesource.com/v8/v8) (implementation behavior).
- `delete` and object shapes: V8 blog, "Fast properties in V8" (v8.dev/blog/fast-properties). String concatenation with ropes: no published guarantee; engine implementation behavior, so the row says to benchmark.
- `Promise.all` behavior: MDN `Global_Objects/Promise/all`.

## Input handling and security

- `Number()` conversion (`""`, `" "`, `null`, `0x` prefixes): MDN `Global_Objects/Number` ("Number coercion") and the specification's StringToNumber. `parseInt`, `parseFloat` stopping at the first invalid character: MDN `Global_Functions/parseInt` and `Global_Functions/parseFloat`. `Number.MAX_SAFE_INTEGER`: MDN `Global_Objects/Number/MAX_SAFE_INTEGER`.
- `RegExp.escape` (ES2025): MDN `Global_Objects/RegExp/escape`.
- Prototype pollution: MDN "Prototype pollution" (developer.mozilla.org/en-US/docs/Web/Security/Attacks/Prototype_pollution) and `Global_Objects/Object/proto`.
- Recursion depth: no published limit; engine- and frame-size-dependent, so the file says to measure.
- Date-only forms parsed as UTC and date-time forms as local time: MDN `Global_Objects/Date/parse` ("Date time string format") and the specification's Date Time String Format.
- `eval`, `new Function`, and Node's `vm` not being a sandbox: Node.js `vm` documentation (nodejs.org/api/vm.html, "The node:vm module is not a security mechanism").

## Bit manipulation and traps

- 32-bit conversion in bitwise operators, `1 << 32`, `>>> 0`: MDN `Operators/Left_shift` and `Operators/Unsigned_right_shift`; the specification's ToInt32. `Math.clz32`: MDN `Global_Objects/Math/clz32`.
- Property order (integer-like keys first): the specification's OrdinaryOwnPropertyKeys; MDN "Enumerability and ownership of properties".
- SameValueZero versus strict equality in `includes` and `indexOf`: MDN "Equality comparisons and sameness" (developer.mozilla.org/en-US/docs/Web/JavaScript/Equality_comparisons_and_sameness).
- String length in UTF-16 code units and iteration by code points: MDN `Global_Objects/String/length` and `Global_Objects/String/Symbol.iterator`.
- Holes skipped by array methods: MDN "Array" ("Array methods and empty slots").
- Single-use iterators: MDN "Iteration protocols".
- `toSorted`, `toReversed`, `toSpliced` (ES2023): MDN pages for each.

## Testing and benchmarking

- npm lifecycle scripts and `pretest`/`posttest`: docs.npmjs.com/cli/using-npm/scripts. `npm ci --ignore-scripts`: docs.npmjs.com/cli/commands/npm-ci.
- fast-check, including `fc.commands` model-based testing: fast-check.dev (documentation, "Model based testing").
- `--cpu-prof`, `--heap-prof`: nodejs.org/api/cli.html.
- `crypto.timingSafeEqual` throwing on unequal lengths: nodejs.org/api/crypto.html#cryptotimingsafeequala-b. `crypto.subtle.verify`: MDN "SubtleCrypto: verify() method".
