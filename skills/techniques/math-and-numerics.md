# Math and Numerics

Part of the advanced techniques. The shared rules in `ADVANCED-TECHNIQUES.md` apply to every table in this file; read them first. Tables are read as described there.

## Number theory and math

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Many primality or divisibility checks up to N | Sieve of Eratosthenes | N fits in memory | Per-query trial division → O(N log log N) once, then O(1) |
| Many factorizations up to N | Smallest-prime-factor sieve | N fits in memory | O(√n) per query → O(log n) per query |
| Primality of large individual numbers | Miller-Rabin with deterministic bases for 64-bit integers | Use the known deterministic base set; otherwise the result is probabilistic and a behavior change | O(√n) → O(log³ n) |
| GCD, LCM, linear Diophantine equations, modular inverses | Euclidean and extended Euclidean algorithm | — | O(log min(a, b)) |
| Combinations, factorial ratios modulo a prime | Precomputed factorials and inverse factorials | The modulus is prime and larger than n | O(n) per query → O(1) after O(n) setup |
| Large powers, modular exponentiation | Binary exponentiation | Intermediate products cannot overflow differently from the original: a 64-bit modulus needs 128-bit multiplication or a safe multiply-mod; for floating point, results can differ in the last bits from repeated multiplication | O(n) → O(log n) multiplications |
| Linear recurrence of order k for very large n, where matrix exponentiation ("Reusing work" in `CORE-TECHNIQUES.md`) is too slow because k is large | Kitamasa's method: reduce xⁿ modulo the recurrence's characteristic polynomial by repeated squaring | Same arithmetic semantics as the original (modulus, overflow, exact integers) | O(k³ log n) → O(k² log n), or O(k log k log n) with FFT-based polynomial multiplication |
| Polynomial multiplication, convolution, counting pair sums | FFT or NTT | Floating-point FFT rounds, so results can differ (behavior change) unless values are small enough to round back exactly, with a stated error bound. NTT computes the result **modulo a prime**: it equals the exact integer result only when the prime exceeds every possible output coefficient, or when several primes are combined with the Chinese remainder theorem | O(n²) → O(n log n) |
| XOR constraints, parity systems, maximum subset XOR | XOR basis; Gaussian elimination over GF(2) | — | Exponential subset search → O(n · bits), or O(n³/w) with bitsets |

## Numerical computation

Floating-point results depend on the order and form of every operation. Most techniques here change results, usually for the better: they are behavior changes under rule 5, never reasons to skip the technique. Report the before and after values on representative and adversarial inputs (for example, the error against a high-precision reference), and let the developer decide. Compilers must not reassociate the new code (no fast-math flags on it), or the technique can silently stop working.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Summing many floating-point values where accumulated rounding error matters | Kahan or Neumaier compensated summation (Neumaier also handles terms larger than the running sum) | Behavior change: results differ, usually closer to the exact sum. Strict floating-point semantics in the compiled code | Same O(n), a few more operations per element. Worst-case error bound grows with n for naive summation, and is nearly independent of n with compensation |
| Floating-point sum that should be vectorized or parallelized | Pairwise (cascade) summation | Behavior change: results differ | O(n); error bound grows as O(log n) instead of O(n); splits naturally into independent chunks |
| Sum must be identical regardless of order, chunking, or thread count | Reproducible summation: fixed-point integer accumulation, or an exact (superaccumulator) sum rounded once | Behavior change unless the original order was already fixed; value range is known for fixed point | Deterministic results that allow parallel and vectorized evaluation |
| Variance or standard deviation computed as mean of squares minus square of mean, or in two passes | Welford's online algorithm | Behavior change: avoids catastrophic cancellation, so results differ | Two passes → one pass, O(1) memory |
| Polynomial evaluated by computing each power separately | Horner's method | Behavior change in floating point (different rounding); exact for integers without overflow | O(n²) or O(n log n) multiplications → O(n) |
| Dense matrix multiplication written as a triple loop | An optimized BLAS library (blocked, vectorized, multithreaded); Strassen-type algorithms only for very large matrices | BLAS may sum in a different order (results differ in the last bits); Strassen is less numerically stable: both are behavior changes for exact-bit callers | Constant factors of ten or more from BLAS; O(n³) → O(n^2.81) with Strassen at large n |
| Large sparse symmetric positive-definite linear systems solved by dense elimination | Conjugate gradient with a preconditioner | The matrix is symmetric positive definite; results are approximate to a stated tolerance (behavior change against an exact solver) | O(n³) → about O(nonzeros × iterations) |
| Integrals computed with many equally spaced evaluations (fixed-step trapezoid or Simpson rule) | Gaussian quadrature for smooth integrands; adaptive quadrature (Gauss-Kronrod) that refines only where the error estimate is large | Results change within the tolerance: a behavior change; the integrand's smoothness checked | Far fewer function evaluations for the same accuracy |
| Smooth optimization by plain gradient descent taking thousands of small steps | Newton's method for small problems; quasi-Newton (L-BFGS) for large ones; with a line search | The objective is smooth and gradients are available; the iterates and the final point within tolerance differ (behavior change) | Many more iterations → superlinear convergence near the optimum |
| Same linear system solved for many right-hand sides | Factorize once (LU, Cholesky, QR), then solve per right-hand side | Matrix does not change between solves; results may differ in the last bits | O(n³) per solve → O(n³) once + O(n²) per solve |
| Matrices or vectors that are mostly zeros | Sparse formats (CSR, CSC, COO) and sparse kernels | Density below a measured threshold (dense kernels win above it); summation order in the kernel may change floating-point results | O(n²) per matrix-vector product → O(nnz), with O(nnz) memory |
| Tight numeric loops in floating point | SIMD-friendly kernels: contiguous data, no aliasing, no data-dependent branches; vectorized math libraries | Vectorized reductions reorder additions (behavior change); vectorized math functions may round differently | Several times faster per core |
| Repeated exact arithmetic on integers or rationals carried in floating point | Integer or fixed-point arithmetic | Value ranges fit without overflow; switching from floating point is a behavior change | Faster on many platforms, and exact; required where floating point is unavailable (for example, most kernel code) |

## Quantum software

Quantum simulators and circuit compilers are classical programs with exponential costs, and the right representation often removes them. Simulator output (amplitudes, sampled measurement counts) and compiled circuits are observable: a different but equivalent circuit, or a different random sample, is a behavior change unless the original contract allows it.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Circuits made only of Clifford gates (Hadamard, phase, CNOT, Pauli gates, measurement) simulated with a full state vector | Stabilizer (tableau) simulation | Only Clifford gates; with a few non-Clifford gates, extended stabilizer methods cost exponential only in the number of those gates | Memory 2ⁿ amplitudes → O(n²) bits; O(n) per gate, O(n²) per measurement |
| State-vector memory of 2ⁿ amplitudes limits the qubit count, on circuits with limited entanglement | Tensor-network or matrix-product-state simulation, with the contraction order chosen by a heuristic optimizer | Exact only without bond-dimension truncation; truncation is approximate (behavior change); cost depends heavily on contraction order, so measure it | Cost exponential in entanglement or treewidth instead of qubit count |
| Many measurement shots sampled by re-running the whole simulation per shot | Simulate once and draw all shots from the final probability distribution | No mid-circuit measurements or noise that depends on earlier outcomes; seeded sampling reproduces the original's sample only if the random draws match | Shots × simulation → one simulation plus sampling |
| Mapping a circuit onto hardware connectivity (qubit routing) by exhaustive search | Heuristic routing such as SABRE, with several random trials | The problem is NP-hard: results are not optimal, and a different routed circuit with a different gate count is a behavior change | Exponential search → polynomial per trial: linear in the number of gates, polynomial in the number of qubits |

## References (for verifying claims; not required reading)

- Donald E. Knuth, *The Art of Computer Programming*, Vol. 2: Seminumerical Algorithms, 3rd ed. (1997).
- Nicholas J. Higham, *Accuracy and Stability of Numerical Algorithms*, 2nd ed. (2002).
- Scott Aaronson and Daniel Gottesman, "Improved Simulation of Stabilizer Circuits," *Physical Review A* 70, 2004; Johnnie Gray and Stefanos Kourtis, "Hyper-Optimized Tensor Network Contraction," *Quantum* 5, 2021; Gushu Li, Yufei Ding, and Yuan Xie, "Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices" (SABRE), ASPLOS 2019.
- Jorge Nocedal and Stephen J. Wright, *Numerical Optimization*, 2nd ed. (2006); Yousef Saad, *Iterative Methods for Sparse Linear Systems*, 2nd ed. (2003).
- David Goldberg, "What Every Computer Scientist Should Know About Floating-Point Arithmetic" (1991).
