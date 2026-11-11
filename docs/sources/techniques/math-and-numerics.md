# Sources for `skills/algorithmic-intelligence/references/techniques/math-and-numerics.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill.

- Donald E. Knuth, *The Art of Computer Programming*, Vol. 2: Seminumerical Algorithms, 3rd ed. (1997).
- Nicholas J. Higham, *Accuracy and Stability of Numerical Algorithms*, 2nd ed. (2002): compensated and pairwise summation error bounds, Horner's method, factorizations.
- Arnold Neumaier, "Rundungsfehleranalyse einiger Verfahren zur Summation endlicher Summen," *Zeitschrift für Angewandte Mathematik und Mechanik* 54(1), 1974 (Neumaier summation); B. P. Welford, "Note on a Method for Calculating Corrected Sums of Squares and Products," *Technometrics* 4(3), 1962; Tony F. Chan, Gene H. Golub, and Randall J. LeVeque, "Algorithms for Computing the Sample Variance: Analysis and Recommendations," *The American Statistician* 37(3), 1983 (one-pass against two-pass accuracy).
- Volker Strassen, "Gaussian Elimination Is Not Optimal," *Numerische Mathematik* 13(4), 1969.
- Deterministic Miller-Rabin base sets for 64-bit integers: Gerhard Jaeschke, "On Strong Pseudoprimes to Several Bases," *Mathematics of Computation* 61(204), 1993; Jan Feitsma and William Galway's list of base-2 strong pseudoprimes below 2⁶⁴ (2010), from which the 64-bit sets are verified; François Arnault, "Rabin-Miller Primality Test: Composite Numbers Which Pass It," *Mathematics of Computation* 64(209), 1995 (composites passing fixed bases).
- Kitamasa's method (reducing xⁿ modulo the characteristic polynomial) is competitive-programming folklore with no standard published source; its correctness follows from polynomial arithmetic in Knuth, Vol. 2, section 4.6.
- Scott Aaronson and Daniel Gottesman, "Improved Simulation of Stabilizer Circuits," *Physical Review A* 70, 2004; Johnnie Gray and Stefanos Kourtis, "Hyper-Optimized Tensor Network Contraction," *Quantum* 5, 2021; Gushu Li, Yufei Ding, and Yuan Xie, "Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices" (SABRE), ASPLOS 2019.
- Jorge Nocedal and Stephen J. Wright, *Numerical Optimization*, 2nd ed. (2006); Yousef Saad, *Iterative Methods for Sparse Linear Systems*, 2nd ed. (2003).
- David Goldberg, "What Every Computer Scientist Should Know About Floating-Point Arithmetic" (1991).
- Martin R. Albrecht, Jake Massimo, Kenneth G. Paterson, and Juraj Somorovsky, "Prime and Prejudice: Primality Testing Under Adversarial Conditions," ACM CCS 2018: composites crafted to pass fixed-base Miller-Rabin tests.
