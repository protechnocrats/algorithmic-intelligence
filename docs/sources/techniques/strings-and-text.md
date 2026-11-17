# Sources for `skills/algorithmic-intelligence/references/techniques/strings-and-text.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill.

- Dan Gusfield, *Algorithms on Strings, Trees, and Sequences* (1997).
- Russ Cox, "Regular Expression Matching Can Be Simple And Fast" (2007), swtch.com/~rsc/regexp/regexp1.html.
- Aho, Lam, Sethi, and Ullman, *Compilers: Principles, Techniques, and Tools*, 2nd ed. (2006): lexers, finite automata, parsing.
- Jon L. Bentley and Robert Sedgewick, "Fast Algorithms for Sorting and Searching Strings," SODA 1997.
- Edsger W. Dijkstra, "ALGOL 60 Translation" (1961), Mathematisch Centrum report MR 35: the shunting-yard algorithm.
- Eugene W. Myers, "An O(ND) Difference Algorithm and Its Variations," *Algorithmica* 1, 1986.
- Donald E. Knuth and Michael F. Plass, "Breaking Paragraphs into Lines," *Software: Practice and Experience* 11(11), 1981.
- Hans-J. Boehm, Russ Atkinson, and Michael Plass, "Ropes: An Alternative to Strings," *Software: Practice and Experience* 25(12), 1995.
- Bryan Ford, "Packrat Parsing: Simple, Powerful, Lazy, Linear Time" (2002).
- Manning, Raghavan, and Schütze, *Introduction to Information Retrieval* (2008); Ding and Suel, "Faster Top-k Document Retrieval Using Block-Max Indexes," SIGIR 2011; Andrei Z. Broder, David Carmel, Michael Herscovici, Aya Soffer, and Jason Zien, "Efficient Query Evaluation Using a Two-Level Retrieval Process," CIKM 2003 (WAND).
- Ge Nong, Sen Zhang, and Wai Hong Chan, "Two Efficient Algorithms for Linear Time Suffix Array Construction," *IEEE Transactions on Computers* 60(10), 2011 (SA-IS).
- Thomas Reps, "'Maximal-Munch' Tokenization in Linear Time," *ACM TOPLAS* 20(2), 1998; Joop M. I. M. Leo, "A General Context-Free Parsing Algorithm Running in Linear Time on Every LR(k) Grammar Without Using Lookahead," *Theoretical Computer Science* 82(1), 1991.
- Glenn K. Manacher, "A New Linear-Time On-Line Algorithm for Finding the Smallest Initial Palindrome of a String," *Journal of the ACM* 22(3), 1975; Alfred V. Aho and Margaret J. Corasick, "Efficient String Matching: An Aid to Bibliographic Search," *CACM* 18(6), 1975.
- Unicode Standard Annex #15, "Unicode Normalization Forms," and Unicode Technical Report #36, "Unicode Security Considerations": normalization, case folding that changes length, and non-ASCII digits.

Biological sequences:

- Saul B. Needleman and Christian D. Wunsch, "A General Method Applicable to the Search for Similarities in the Amino Acid Sequence of Two Proteins," *Journal of Molecular Biology* 48(3), 1970; T. F. Smith and M. S. Waterman, "Identification of Common Molecular Subsequences," *Journal of Molecular Biology* 147(1), 1981; Osamu Gotoh, "An Improved Algorithm for Matching Biological Sequences," *Journal of Molecular Biology* 162(3), 1982 (affine gaps in O(n·m)); Michael Farrar, "Striped Smith-Waterman Speeds Database Searches Six Times over Other SIMD Implementations," *Bioinformatics* 23(2), 2007 (striped SIMD, 8-bit lanes with overflow detection and recomputation); D. S. Hirschberg, "A Linear Space Algorithm for Computing Maximal Common Subsequences," *CACM* 18(6), 1975.
- Genome size: Genome Reference Consortium, GRCh38 assembly statistics (about 3.1 billion bases in total assembly length).
- UCSC Genome Browser, ".2bit" file format description (genome.ucsc.edu/FAQ/FAQformat.html#format7): two bits per base, with N blocks and lowercase (soft-masked) blocks stored separately. Format specification.
- Guillaume Marçais and Carl Kingsford, "A Fast, Lock-Free Approach for Efficient Parallel Counting of Occurrences of k-mers," *Bioinformatics* 27(6), 2011 (Jellyfish: 2-bit packed k-mers, canonical k-mers); Sebastian Deorowicz et al., "KMC 2: Fast and Resource-Frugal k-mer Counting," *Bioinformatics* 31(10), 2015 (disk-based partitioned counting).
- Michael Roberts, Wayne Hayes, Brian R. Hunt, Stephen M. Mount, and James A. Yorke, "Reducing Storage Requirements for Biological Sequence Comparison," *Bioinformatics* 20(18), 2004 (minimizers; sequences sharing a match of w + k − 1 bases share a minimizer; lexicographic order over-selects low-complexity k-mers); Saul Schleimer, Daniel S. Wilkerson, and Alex Aiken, "Winnowing: Local Algorithms for Document Fingerprinting," SIGMOD 2003 (expected density 2/(w + 1) under a random order); Guillaume Marçais et al., "Improving the Performance of Minimizers and Winnowing Schemes," *Bioinformatics* 33(14), 2017.
- Heng Li, "Minimap2: Pairwise Alignment for Nucleotide Sequences," *Bioinformatics* 34(18), 2018 (minimizer seeds, chaining, banded extension, skipping highly repetitive minimizers).
- Paolo Ferragina and Giovanni Manzini, "Opportunistic Data Structures with Applications," FOCS 2000 (FM-index, backward search, sampled suffix array); M. Burrows and D. J. Wheeler, "A Block-Sorting Lossless Data Compression Algorithm," DEC SRC Research Report 124, 1994; Ben Langmead, Cole Trapnell, Mihai Pop, and Steven L. Salzberg, "Ultrafast and Memory-Efficient Alignment of Short DNA Sequences to the Human Genome," *Genome Biology* 10, R25, 2009 (Bowtie: backtracking for mismatches); Heng Li and Richard Durbin, "Fast and Accurate Short Read Alignment with Burrows-Wheeler Transform," *Bioinformatics* 25(14), 2009 (BWA).
- Stephen F. Altschul, Warren Gish, Webb Miller, Eugene W. Myers, and David J. Lipman, "Basic Local Alignment Search Tool," *Journal of Molecular Biology* 215(3), 1990 (seed and extend); Stephen F. Altschul et al., "Gapped BLAST and PSI-BLAST," *Nucleic Acids Research* 25(17), 1997 (X-drop gapped extension); Kun-Mao Chao, William R. Pearson, and Webb Miller, "Aligning Two Sequences within a Specified Diagonal Band," *CABIOS* 8(5), 1992 (banded alignment).
- The suffix array's 4 to 8 bytes per base follows from storing one 32- or 64-bit position per suffix; "a few bits per base" for the FM-index is from Ferragina and Manzini and the Bowtie and BWA papers' reported index sizes.
