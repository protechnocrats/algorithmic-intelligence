# Sources for `skills/algorithmic-intelligence/references/DIFFERENTIAL-TESTING.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill.

- William M. McKeeman, "Differential Testing for Software," *Digital Technical Journal* 10(1), 1998.
- Koen Claessen and John Hughes, "QuickCheck: A Lightweight Tool for Random Testing of Haskell Programs," ICFP 2000.
- C. A. R. Hoare, "An Axiomatic Basis for Computer Programming," *CACM* 12(10), 1969: preconditions, postconditions, invariants.
- Daniel Jackson, *Software Abstractions*, revised ed. (2012): the small-scope hypothesis and bounded checking.
- Richard A. DeMillo, Richard J. Lipton, and Frederick G. Sayward, "Hints on Test Data Selection: Help for the Practicing Programmer," *IEEE Computer* 11(4), 1978: mutation testing.
- T. Y. Chen, S. C. Cheung, and S. M. Yiu, "Metamorphic Testing: A New Approach for Generating Next Test Cases" (1998).
- Edmund Clarke, Daniel Kroening, and Flavio Lerda, "A Tool for Checking ANSI-C Programs," TACAS 2004 (CBMC).
- Nuno P. Lopes et al., "Alive2: Bounded Translation Validation for LLVM," PLDI 2021: bounded equivalence checking of a rewrite against the original with an SMT solver (level 3), and the time-outs it hits on multiplication, division, and floating point.
- Leslie Lamport, *Specifying Systems* (2002): TLA+ and its model checker for enumerating the interleavings of a concurrent algorithm up to a bound (level 3 for concurrency changes).
- Anthropic, "Migrating the Messages API to Rust" (2026), anthropic.com/research/migrating-api-to-rust: comparing old and new at each step so the first differing step locates the bug; grouping differences by a signature (step, piece, first differing byte, both lengths) because one bug leaves the same signature on every input it affects; running a nondeterministic dependency once and replaying its output to both versions; recording only the shape of each difference when the data is private; about 98% of tests passing while about a quarter of production inputs matched, with an escaping difference (an emoji in JSON) behind part of the gap; agents making outputs match by copying data into the code, which review rejected ("Finding the cause of a disagreement", "Inputs shaped like the real ones", "Record once, replay to both", "Offer a shadow comparison"; "Make the code right, not the comparison green" in `APPLYING.md`).
- GitHub Scientist (github.com/github/scientist): running a candidate code path beside the original on live requests, serving the original's result, and publishing mismatches.
- Diffy (github.com/opendiffy/diffy, originally from Twitter): comparing a candidate service's responses with the original's on the same traffic, with a second copy of the original to filter out nondeterministic noise.
