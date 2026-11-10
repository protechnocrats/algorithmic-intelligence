# Benchmarking

How to measure speed and memory so the numbers can be trusted. Benchmarks are evidence of speed, not correctness; they never replace the differential tests.

## Benchmarks

**Before running**
- **Predict first.** Write the expected speedup at realistic `n` and the expected growth exponent of each version (the report's "Prediction" field). A measurement that misses the prediction badly means the analysis is wrong somewhere; find where before keeping the change.
- **The benchmark runs the original thousands of times,** so one email or delete becomes thousands. Fake its effects as for differential tests ("The test runs the original" in `DIFFERENTIAL-TESTING.md`), and estimate memory, disk, and time for each size so they stay well inside the machine.
- Use the project's benchmark tooling when present (see the language files); otherwise a simple harness in test code: warm up, many iterations, median, and a sink the compiler cannot discard (`black_box`, a blackhole, a printed checksum). A number an earlier session left is a claim, never quoted as measured.
- Same inputs, machine, build type, and load for both versions; release builds, since debug builds distort results.
- **Representative inputs.** Real data is often partly sorted, skewed, or full of duplicates, which uniform random data hides. Benchmark on generated data shaped like production (sizes, order, skew, duplicate rate, from configuration, documentation, or the developer) as well as uniform data.
- **Worst-case and adversarial inputs** where relevant: sorted or reversed data for sorting and selection, colliding keys for hash structures, degenerate shapes for trees and recursion. Under untrusted input, search for worst cases as in "Finding worst-case inputs" in `techniques/hostile-inputs.md`.

**Running**
- Measure at the smallest common size, at realistic `n`, and at a larger `n` (about 10×). When call sizes vary, weight by the call-size distribution and find the crossover: a win at large `n` can be a loss at the sizes most calls use.
- Code that runs concurrently in production is also benchmarked at production concurrency, for throughput and per-call latency: a single-thread win that holds a lock longer or saturates a pool is a loss. For latency-sensitive or deadline-bound paths, report p95, p99, and the maximum.
- **Doubling experiments** check a complexity claim: time N, 2N, 4N, 8N after warm-up and compute b ≈ log₂(T(2N) / T(N)). Near 1 is linear, slightly above 1 fits n log n, near 2 is quadratic. Predict the next size before measuring it. Start N large enough that fixed overhead does not dominate, and expect the constant to shift where the working set crosses a cache or memory boundary. An exponent that does not match the claim means the analysis missed a cost.
- **Alternate the versions** (A, B, B, A, or randomized) so drift in temperature, frequency, background load, and caches hits both equally. Report the median with the spread, never a single run.
- Note frequency scaling and turbo, pin cores where possible, and take more samples on shared or cloud machines.

**Measuring what you claim**
- **Same work on both sides.** Check in the harness that both outputs are equal; a faster version that does less work is not faster. If the function mutates, drains, or caches on its input, rebuild the input each iteration (from iteration 2 on, a sort sees sorted data) and exclude or subtract the copy time.
- **Keep the work alive:** consume every result, force lazy results, and read inputs the compiler cannot treat as constant.
- **Match production cache state.** A cache the change adds is measured at a realistic hit rate, cold and warm runs reported separately, not by repeating one input until every call hits. The same applies to file and database caches.

**Separating the effect from noise**
- **Measure the noise first (A/A):** benchmark the reference against an identical copy in the same harness. The difference is the noise floor. A large A/A difference means the setup is biased: environment size, link order, and memory layout can shift results by more than the effect (Mytkowicz et al., 2009), so randomize the setup and repeat in fresh processes.
- **Show the difference exceeds the noise** with a confidence interval for the difference (a bootstrap over per-run times) or at least a gap between medians larger than the spread. Inside the noise is "no measurable difference". Use the tool's own statistics when it has them (JMH, BenchmarkDotNet, Criterion, Google Benchmark).

**Reporting**
- Absolute times with the percentage change, plus machine and runtime details.
- Label every number measured or estimated (rule 8). Report what the runs gave, even when the developer expects a different result.
- Benchmark harnesses stay out of production code.
- **Offer a regression guard:** where the code exposes one, prefer a test that checks a size-dependent count (key-function calls, comparisons, queries, allocations), for example that a sort key ran exactly n times: it is deterministic, and it fails when the complexity regresses. Otherwise keep the benchmark in the project's tooling or as a CI job with a threshold against a recorded baseline; timing assertions in unit tests are flaky. Adding a CI job is a configuration change that needs approval.

## Component and end-to-end

A benchmark of the changed function shows how much faster the function became, not the program. Report both:

1. **Component:** the changed function or path, measured as above.
2. **End-to-end:** the whole operation the developer cares about (request, page load, frame, batch job, command), before and after, where the project can run it safely against local or faked services. If it cannot run, take the function's share from a profile or estimate it from survey call counts, labeled estimated.

The end-to-end saving cannot exceed the changed code's share of the time (Amdahl's law). State the share next to the component numbers: "`buildIndex` 40 ms → 4 ms (measured); it was about 8% of the 500 ms request (profiled), so the request is about 7% faster (estimated from the profile)." A large component win with a small end-to-end saving is still worth reporting, honestly labeled; it may matter more once other bottlenecks are fixed.

**Check that the proxy implies the target.** A component benchmark, operation count, cost model, or heuristic score is a proxy. Before optimizing against it, check on a few cases that it moves with the target: the component winner also wins end to end, fewer operations also means less time, a better score means a better real result. When they disagree, the proxy is missing a cost (I/O, allocation, cache effects, a different input distribution); fix it or measure the target directly. Learning theory makes the same point: optimizing a surrogate loss guarantees nothing unless the surrogate is consistent with the true objective (Bartlett, Jordan, and McAuliffe, 2006).

## Memory measurement

Rule 1 requires bounded memory, so measure it for both versions:

- **Peak memory** during the run.
- **Allocation volume** (bytes or objects), from the platform's allocation profiler or the benchmark tool.
- **Retained memory** after the call returns, to catch caches or indexes that grow without bound. In garbage-collected runtimes, force a full collection first, and prefer allocation volume as the comparable number, since peak and retained figures depend on when the collector ran.

If the platform cannot measure memory, say so and report the expected bound as estimated.
