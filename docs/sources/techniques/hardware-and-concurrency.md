# Sources for `skills/algorithmic-intelligence/references/techniques/hardware-and-concurrency.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill.

- Ulrich Drepper, "What Every Programmer Should Know About Memory" (2007).
- Frigo, Leiserson, Prokop, and Ramachandran, "Cache-Oblivious Algorithms," FOCS 1999.
- Maurice Herlihy and Nir Shavit, *The Art of Multiprocessor Programming*, 2nd ed. (2020).
- Paul E. McKenney, *Is Parallel Programming Hard, And, If So, What Can You Do About It?* (RCU, sequence locks, per-CPU counters).
- Cormen, Leiserson, Rivest, and Stein, *Introduction to Algorithms*, 4th ed. (2022), chapter on parallel algorithms (work and span, the greedy-scheduler bound).
- Gene M. Amdahl, "Validity of the Single Processor Approach to Achieving Large Scale Computing Capabilities," AFIPS 1967.
- Paul-Virak Khuong and Pat Morin, "Array Layouts for Comparison-Based Searching," *ACM Journal of Experimental Algorithmics* 22, 2017 (Eytzinger and B-tree layouts with prefetching).
- Shimin Chen, Anastassia Ailamaki, Phillip B. Gibbons, and Todd C. Mowry, "Improving Hash Join Performance through Prefetching," ICDE 2004 (group prefetching).
- Runtime dispatch by CPU feature (GNU `ifunc`, function multiversioning, the kernel's alternatives patching) is documented in the GCC manual ("Function Multiversioning" at gcc.gnu.org/onlinedocs/gcc/Function-Multiversioning.html, and the `ifunc` entry in "Common Function Attributes") and the Linux kernel source (`arch/x86/kernel/alternative.c`); the row states implementation practice, not a published bound.
