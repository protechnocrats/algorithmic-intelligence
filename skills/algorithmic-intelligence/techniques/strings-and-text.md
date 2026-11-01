# Strings and Text

Part of the advanced techniques. The shared rules in `ADVANCED-TECHNIQUES.md` apply to every table in this file; read them first. Tables are read as described there.

## Strings

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Many substring or repeated-pattern queries on a static text | Suffix array + LCP array (a suffix tree answers the same queries with several times more memory) | Text does not change; enough queries to amortize the build | Build: O(n log n), or O(n) with SA-IS; O(n) memory. Query: O(m log n) for a pattern of length m, plus O(k) to report k occurrences, instead of O(n·m) per scan |
| Searching a long text for one long pattern over a large alphabet, with a hand-written search loop | Boyer-Moore or Boyer-Moore-Horspool (skip ahead by mismatch tables), or the platform's optimized search, which often already uses them or two-way matching | Same matching semantics (case, overlapping matches, Unicode units) | O(n·m) → sublinear on average, O(n/m) in the best case |
| Distinct substrings, longest repeated or common substring | Suffix automaton | — | O(n²) or worse → O(n) build |
| Longest palindromic substring, all palindromes | Manacher's algorithm | Same unit of text as the original: bytes, code units, code points, or user-visible characters give different palindromes | O(n²) → O(n) |
| Border and period detection | Prefix function (KMP failure function) | — | O(n²) → O(n) |
| Edit distance when only small distances matter | Banded (Ukkonen) edit distance | A threshold k is known | O(n·m) → O(n·k) |
| Regular expression with nested or overlapping quantifiers (`(a+)+`, `(a\|a)*`, `.*.*x`), run by a backtracking engine on long or untrusted input | Rewrite the pattern to remove the ambiguity (atomic groups or possessive quantifiers where supported), or switch to a linear-time engine (Thompson NFA or lazy DFA, such as RE2, Rust's `regex`, Go's `regexp`) | Linear-time engines do not support backreferences or lookaround; match semantics must be checked one by one: leftmost-first versus leftmost-longest, capture group contents, Unicode classes, anchors and line modes. A new engine is usually a dependency (rule 7) | Exponential worst case → O(n·m) for text length n and pattern size m |
| Many regular expressions tried one after another on the same input | One combined alternation, or a regex set that reports every pattern that matched in one pass | Which pattern wins, and in which priority order, matches the original | k passes over the input → one pass |
| Keyword or term search across many documents by scanning each one | Inverted index: each term maps to a sorted list of the documents (and positions) containing it; ranking such as BM25 computed over those lists only; multi-term queries intersect lists | Tokenization, normalization, matching rules, and result order reproduce the original | O(total text) per query → O(length of the posting lists for the query terms) |
| Multi-term ranked search that scores every document in the union of the posting lists, then sorts | Dynamic pruning for top-k retrieval: MaxScore, WAND, or Block-Max WAND, using per-term (and per-block) upper bounds on score contributions to skip documents that cannot enter the current top k | The scoring function is a sum of per-term contributions with known maxima; ties at the k-th score are broken as in the original | Most postings skipped; same top k as exhaustive scoring |
| Intersecting posting lists or sorted ID sets of very different lengths | Galloping (exponential) search from the shorter list into the longer one, or skip pointers stored in the lists | Lists sorted by the same order; duplicates handled as the original does | O(m + n) → O(m log(n / m)) for lists of lengths m ≤ n |
| Sorting many strings that share long prefixes (paths, URLs, composite keys), where each comparison rescans the shared prefix | Multikey (three-way radix) quicksort: partition on one character at a time, recursing into the "equal" part on the next character | The order equals the original comparator's: plain code-unit or byte order, not locale collation or case-insensitive comparison | O(n log n) full-string comparisons → O(n log n + D) character comparisons expected, where D is the total length of the distinguishing prefixes |
| Prefix search, autocomplete, or near-neighbor search over a large string set, where a trie with one child slot per alphabet symbol uses too much memory | Ternary search trie: each node holds one character and three children (less, equal, greater) | Same matching rules (case, normalization) and result order as the original | O(k + log n) per lookup for a key of length k in a balanced tree, with memory proportional to the stored characters |
| Diffing two sequences (lines, tokens, characters, list items) with the full O(N·M) longest-common-subsequence table | Myers' O((N + M) · D) algorithm, where D is the edit distance, with its linear-space variant; Hunt-Szymanski when matches are rare | Same edit script: Myers returns a shortest edit script, but when several exist it may choose a different one than another algorithm, and patience or histogram diff choose different (often more readable) ones: a **behavior change** where the script is shown or stored | O(N·M) time and memory → O((N + M) · D) time and O(N + M) memory; fast when the inputs are similar |
| Editing a large text buffer by copying the whole string on each insert or delete (editors, collaborative documents, logs edited in place) | Gap buffer (edits near one cursor), piece table (original plus append-only buffer, with a list or tree of pieces), or rope (balanced tree of string chunks) | Index semantics preserved (code units versus code points versus graphemes); line and offset lookups maintained | O(n) per edit → O(1) amortized near the cursor (gap buffer) or O(log n) anywhere (rope, piece tree) |
| Breaking paragraphs into lines by trying combinations of break points | Knuth-Plass total-fit line breaking: DP over feasible break points, keeping only active break points within one line's width | The cost function matches the original's; replacing greedy first-fit with total-fit changes the output: **behavior change** | Exponential search → O(n · w) for n break points and at most w per line; first-fit greedy stays O(n) but is not optimal |
| Regular expression used only to find a fixed string or a fixed prefix | Plain substring search or prefix check | Same case sensitivity, escaping, and Unicode handling | Constant factor; no engine setup |

## Automata, lexers, and parsers

For lexers, tokenizers, regular-expression engines, protocol and file-format parsers, packet filters, and compilers. Any rewrite must reproduce the original's accept and reject decisions, match priorities, error positions, and error messages.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| A lexer that tries each token pattern in turn at every position | One combined deterministic finite automaton (DFA) over all token patterns, generated or hand-built | Longest-match and pattern-priority rules match the original | O(n · patterns) → O(n) |
| Large DFA tables (many states, poor cache fit) | DFA minimization (Hopcroft's algorithm), equivalence classes of input bytes to shrink the alphabet | The recognized language is unchanged, which minimization guarantees | Build O(s · σ log s) for s states and alphabet σ; fewer states and smaller tables |
| A protocol or format parser that rescans the buffer, or restarts when input arrives in pieces (network packets, streamed files) | Explicit state machine that consumes each byte once and keeps its state across buffer boundaries | Same results for every way the input can be split into chunks; limits on header and field sizes kept | O(n · chunks) when each chunk restarts the scan → O(n) |
| A backtracking parser (recursive descent with backtracking, parsing expression grammars) that is slow or exponential on some inputs | Packrat parsing: memoize each (rule, position) result | Rules are pure; ordered-choice semantics kept; memory O(n · rules) is acceptable, or memoize only the rules that backtrack | Exponential worst case → O(n · rules) |
| Arithmetic or filter expressions evaluated by repeatedly scanning for the highest-precedence operator and rewriting the string | Dijkstra's shunting-yard algorithm: one pass with an operator stack produces postfix order (or a tree), then one evaluation pass | Same precedence, associativity, unary-operator handling, and errors for malformed input | O(n²) → O(n) |
| General context-free parsing by exhaustive backtracking or the CYK algorithm | Earley, GLR, or GLL parsing; or a deterministic LL or LR parser when the grammar allows | Same parse result, including which parse is chosen for ambiguous input | Exponential or O(n³) → O(n³) worst case, O(n) for deterministic grammars |

## Combinations

| Combination | Solves | Result |
|---|---|---|
| Aho-Corasick + failure links + DP | Counting or avoiding many patterns in generated strings | Repeated scans → linear in text and automaton size |

## References (for verifying claims; not required reading)

- Dan Gusfield, *Algorithms on Strings, Trees, and Sequences* (1997).
- Russ Cox, "Regular Expression Matching Can Be Simple And Fast" (2007), swtch.com/~rsc/regexp/regexp1.html.
- Aho, Lam, Sethi, and Ullman, *Compilers: Principles, Techniques, and Tools*, 2nd ed. (2006): lexers, finite automata, parsing.
- Jon L. Bentley and Robert Sedgewick, "Fast Algorithms for Sorting and Searching Strings," SODA 1997.
- Edsger W. Dijkstra, "ALGOL 60 Translation" (1961), Mathematisch Centrum report MR 35: the shunting-yard algorithm.
- Eugene W. Myers, "An O(ND) Difference Algorithm and Its Variations," *Algorithmica* 1, 1986.
- Donald E. Knuth and Michael F. Plass, "Breaking Paragraphs into Lines," *Software: Practice and Experience* 11(11), 1981.
- Hans-J. Boehm, Russ Atkinson, and Michael Plass, "Ropes: An Alternative to Strings," *Software: Practice and Experience* 25(12), 1995.
- Bryan Ford, "Packrat Parsing: Simple, Powerful, Lazy, Linear Time" (2002).
- Manning, Raghavan, and Schütze, *Introduction to Information Retrieval* (2008); Ding and Suel, "Faster Top-k Document Retrieval Using Block-Max Indexes," SIGIR 2011.
