# Benchmarking

How to measure speed and memory so the numbers can be trusted. Benchmarks are evidence of speed, not of correctness, and they never replace the differential tests in `DIFFERENTIAL-TESTING.md`.

## Benchmarks

**Before running**
- **Predict first.** Write down the expected speedup at realistic `n` and the expected growth exponent of each version (the report's "Prediction" field), and compare the measurement with it afterward. A prediction that misses badly means the analysis is wrong somewhere: find out where before keeping the change.
- Use the project's existing benchmark tooling when present (see the language files). Otherwise write a simple timing harness in test code: warm up, run many iterations, report the median, and keep the result in a variable the compiler cannot discard.
- Give both versions the same inputs, the same machine, the same build type, and the same load. Prefer release builds, since debug builds distort results; JIT compilation and garbage collection distort them too, which warm-up and repeated runs handle (below).
- **Use representative inputs.** Uniform random data can hide or exaggerate gains: real inputs are often partly sorted, skewed, or full of duplicates. Benchmark on production-like data (or a recorded sample) as well as generated data.
- **Include worst-case and adversarial inputs** where relevant: already-sorted or reverse-sorted data for sorting and selection, colliding hash keys for hash-based structures, deep or degenerate shapes for trees and recursion. When untrusted parties control the input, search for the worst inputs as in "Finding worst-case inputs" in `techniques/hostile-inputs.md`.

**Running**
- Measure both versions at realistic `n` and at a larger `n` (for example, 10× realistic) to show the growth difference.
- **Doubling experiments.** To check a complexity claim, time both versions at N, 2N, 4N, and 8N after warm-up, and compute the exponent b ≈ log₂(T(2N) / T(N)): near 1 is linear, slightly above 1 fits n log n, near 2 is quadratic. Predict the next size's time before measuring it. Start N large enough that fixed overhead does not dominate, and expect the constant to shift where the working set crosses a cache or memory boundary. A measured exponent that does not match the claimed complexity means the analysis missed a cost.
- Warm up where the runtime has a JIT or caches, and run many times: report the median and the spread (or min and max), never a single run.
- **Alternate the versions.** Run reference and candidate in alternating or randomized order (A, B, B, A, …), not all of one and then all of the other, so drift in temperature, CPU frequency, background load, or caches affects both equally.
- **Control noise.** Avoid other heavy load on the benchmark machine, note CPU frequency scaling and turbo settings, and pin to cores where the platform allows. In cloud or shared environments, expect more noise and take more samples.

**Separating the effect from noise**
- **Measure the noise first (an A/A run).** Before comparing, benchmark the reference against an identical copy of itself, in the same harness and order. The difference is the noise floor: a gain smaller than it is "no measurable difference." An A/A run that shows a large difference means the setup itself is biased: small changes to the environment (environment-variable size, link order, memory layout) can shift results by more than the effect being measured (Mytkowicz et al., 2009), so vary or randomize the setup and repeat in fresh processes before trusting any number.
- **Show the difference exceeds the noise.** Report a confidence interval for the difference (for example, a bootstrap interval over the per-run times), or at least show that the gap between medians exceeds the run-to-run spread. A difference inside the noise is "no measurable difference," not a speedup. Use the benchmark tool's own statistics when it has them (JMH, BenchmarkDotNet, Criterion, Google Benchmark).

**Reporting**
- Report absolute times together with the percentage change; percentages alone can make a tiny gain look large. Record machine and runtime details with the numbers.
- Label every number measured. Big-O improvements and workload estimates are labeled estimated and never presented as measured.
- Do not commit benchmark harnesses into production code. Keep them in test or benchmark sources if the developer wants them.
- **Offer a regression guard.** Propose keeping the benchmark (in the project's benchmark tooling, or as a separate job in continuous integration) with a threshold relative to a recorded baseline, so a later change that brings the cost back is caught. Never put timing assertions in unit tests: they are flaky. A test that checks a size-dependent count instead (comparisons, queries, allocations) is a stable alternative where the code exposes one. The developer decides whether to keep it.

## Component and end-to-end

A benchmark of the changed function (a component benchmark) shows how much faster that function became. It does not show how much faster the program became. Report both levels:

1. **Component:** the changed function or code path, measured as above.
2. **End-to-end:** the whole operation the developer cares about (the request, page load, frame, batch job, or command that runs this code). Measure it before and after where the project lets you run it (an existing benchmark, an integration test, a local run of the command). If it cannot be run, take the function's share of the operation from a profile, or estimate it from the call counts in the survey, and label the result estimated.

The end-to-end saving can never exceed the share of time the changed code took (Amdahl's law): if the code took 2% of the operation, even an infinitely fast version saves at most 2%. State the share and the resulting saving next to the component numbers. For example: "`buildIndex` 40 ms → 4 ms (measured); it was about 8% of the 500 ms request (profiled), so the request is about 7% faster (estimated from the profile)." A large component speedup with a small end-to-end saving is still worth reporting, labeled honestly, because it may matter more after other bottlenecks are fixed.

**Check that the proxy implies the target.** A benchmark, a cost model, an operation count, or a heuristic's objective is a proxy for what the developer cares about. Improving the proxy is worth something only if it implies improving the target. Before optimizing against a proxy, check on a few cases that it moves with the target: that a candidate which wins the component benchmark also wins end to end, that fewer counted operations also means less measured time, that a better heuristic score also means a better real result. When they disagree, the proxy is missing a cost (I/O, allocation, cache effects, a different input distribution); fix the proxy or measure the target directly. The same question is studied for learning objectives: optimizing a surrogate loss guarantees nothing about the true objective unless the surrogate is consistent with it (Bartlett, Jordan, and McAuliffe, 2006).

## Memory measurement

Rule 1 requires memory to stay bounded, so measure it, not just time:

- **Peak memory** during the benchmark for both versions.
- **Allocation volume** (bytes or objects allocated), using the platform's allocation profiler or benchmark tool where available.
- **Retained memory** after the call returns, to catch caches or indexes that grow without bound.

If the platform offers no way to measure memory, state that, and report the expected memory bound as estimated.

## References (for verifying claims; not required reading)

- Andy Georges, Dries Buytaert, and Lieven Eeckhout, "Statistically Rigorous Java Performance Evaluation," OOPSLA 2007.
- Todd Mytkowicz et al., "Producing Wrong Data Without Doing Anything Obviously Wrong!", ASPLOS 2009: measurement bias from environment and layout.
- Catherine C. McGeoch, *A Guide to Experimental Algorithmics* (2012): designing experiments, variance reduction, generating test inputs.
- Peter L. Bartlett, Michael I. Jordan, and Jon D. McAuliffe, "Convexity, Classification, and Risk Bounds," *Journal of the American Statistical Association* 101(473), 2006: when optimizing a surrogate implies optimizing the target.
