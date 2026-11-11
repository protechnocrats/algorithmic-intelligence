# Sources for `skills/algorithmic-intelligence/references/BEHAVIOR-TRAPS.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill.

- David Goldberg, "What Every Computer Scientist Should Know About Floating-Point Arithmetic," *ACM Computing Surveys* 23(1), 1991.
- Scott A. Crosby and Dan S. Wallach, "Denial of Service via Algorithmic Complexity Attacks," USENIX Security 2003.
- Unicode Standard Annex #15, "Unicode Normalization Forms" (unicode.org/reports/tr15/); case mapping and folding: The Unicode Standard, section 3.13, and SpecialCasing.txt in the Unicode Character Database.
- Unicode Technical Standard #18, "Unicode Regular Expressions" (unicode.org/reports/tr18/), for which characters `\d` and similar classes match.
- Donald E. Knuth, *The Art of Computer Programming*, Vol. 2, section 3.4.2 (Algorithm P, the unbiased shuffle); the bias of sorting with a random comparator follows from the sort's comparison sequence not being uniform over permutations.
- Language documentation for the platform-specific claims (hash iteration order, sort stability, float-to-integer conversion, numeric equality in hash keys): the files under `docs/sources/languages/` (for example "Bit manipulation and traps" in `docs/sources/languages/JAVA.md`).
