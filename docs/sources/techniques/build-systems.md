# Sources for `skills/algorithmic-intelligence/references/techniques/build-systems.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill.

## Model of build systems

- Andrey Mokhov, Neil Mitchell, and Simon Peyton Jones, "Build Systems à la Carte," *Proc. ACM Program. Lang.* 2(ICFP), Article 79, 2018 (extended version in *Journal of Functional Programming* 30, 2020).
  - Definition 2.1 (minimality: execute tasks at most once per build and only if they transitively depend on changed inputs): the definition of a correct incremental build in "Skip work whose inputs did not change".
  - §2.1 and footnote 5: Make uses file modification times and a static dependency graph executed in topological order; `touch` fools it. §4.2.1: Make requires timestamps to go only forward, which backup software can violate; Make cannot do early cutoff and can only approximate it by not modifying the output file, in which case the step reruns on every later build (the Make caveat in the write-if-changed row).
  - §2.3 and Fig. 3: early cutoff; Shake and Bazel support it, Make and Excel do not.
  - §2.4 and §4.2.3: cloud build systems share results through constructive traces keyed by hashes of inputs.
  - §6.3 "Impure Computations": untracked dependencies (the compiler version), non-determinism, volatility; sandboxing does not capture every dependency. §6.4 and Fig. 11: a nondeterministic step combined with deep constructive traces (keys on terminal inputs only) yields a "Frankenbuild" mixing results of different runs (the last sentence of "Non-hermetic steps").

## Change detection by time or content

- Avery Pennarun (apenwarr), "mtime comparison considered harmful," blog post, 13 November 2018: one-second timestamp granularity, clock skew on network file systems, clocks set wrong, old times on files restored from tarballs and packages, times that go backwards via `utimes`. A practitioner source, not peer-reviewed.
- Git FAQ, "Why isn't Git preserving modification time on files?" (archived Git wiki, archive.kernel.org/oldwiki/git.wiki.kernel.org/index.php/Git_FAQ.html): Git sets the current time on every file it modifies so timestamp-based build tools stay correct.
- Ninja manual (ninja-build.org/manual.html): decisions by modification time; "Outputs implicitly depend on the command line that was used to generate them," recorded in `.ninja_log`; the `restat` rule variable re-stats outputs and treats unchanged ones as not rebuilt (early cutoff); `depfile` and `deps` for dependencies discovered by the compiler. Implementation behavior.
- Gradle User Manual, "Incremental build": fingerprints hold paths and content hashes; file size and last-modified time are used as a shortcut, and "Gradle does not detect changes when the stats of a file did not change"; every property affecting output must be declared as an input, or the task is wrongly up to date; tasks without outputs are never up to date. Implementation behavior.
- ccache manual (ccache.dev/manual/latest.html), "Common hashed information," "The preprocessor mode," "The direct mode," and the sloppiness options: the hash covers compiler identity (by default its size and modification time), compiler options, and source or preprocessed source; the default compiler check can miss a compiler upgrade behind a wrapper. Implementation behavior.
- Docker documentation, "Build cache invalidation" (docs.docker.com/build/cache/invalidation/): once one instruction's cache is invalidated all later ones rebuild; `COPY` and `ADD` use a checksum that ignores modification time; `RUN` is matched by its command text and is not invalidated when fetched content changes; order rarely changing steps first. Implementation behavior.
- Eelco Dolstra, *The Purely Functional Software Deployment Model*, PhD thesis, Utrecht University, 2006: Nix store paths are named by a cryptographic hash of all inputs to the build (listing Nix among content-hash tools).

## Measuring

- Bazel documentation, "JSON Trace Profile" (bazel.build/advanced/performance/json-trace-profile): the profile shows where an invocation spent time, has a "Critical Path" row, and is viewed in `chrome://tracing`. Implementation behavior.
- Gradle User Manual, "Inspecting Gradle Builds" (docs.gradle.org/current/userguide/inspect.html): `--profile` HTML report; build scans split startup, configuration, dependency resolution, and task execution. Implementation behavior.
- Bazel documentation, "Hermeticity" (bazel.build/basics/hermeticity): a null build should rebuild nothing (the no-op rebuild check); compare output hashes across runs and machines to find nondeterminism.
- GNU Coreutils manual, "cp invocation," `--reflink`: a copy-on-write copy shares data blocks until modified, and `auto` is the default (so a copy looks nearly free on Btrfs, XFS, and similar file systems). Implementation behavior. The rest of the measuring advice follows rule 8 and `BENCHMARKING.md` ("No measurable difference here is not no difference in production").
- Gene M. Amdahl, "Validity of the Single Processor Approach to Achieving Large Scale Computing Capabilities," AFIPS Spring Joint Computer Conference, 1967 (speedup bounded by the serial fraction).

## Caching

- Bazel documentation, "Remote Caching" (bazel.build/remote/caching): action cache maps action hashes to results; a content-addressable store holds outputs; only environment variables declared with `--action_env` enter an action; tools outside the workspace are not tracked, so users with different compilers can "wrongly share cache hits"; modifying sources during a build can upload invalid results, and a poisoned cache must be replaced. Implementation behavior.
- Bazel documentation, "Debugging Remote Cache Hits for Local Execution" (bazel.build/remote/cache-remote): compare execution logs of two builds to find differing action keys; non-hermetic inputs cause misses. Implementation behavior.
- Bazel documentation, "Hermeticity": hermetic builds isolate the build from the host (tools as source, no external services); sources of non-hermeticity include timestamps and build IDs, host binaries, and absolute paths; outputs are cacheable when actions are hermetic.
- Gradle User Manual, "Build Cache" (docs.gradle.org/current/userguide/build_cache.html): the cache key covers task type and classpath, input values, and output property names; "Missing task inputs can cause incorrect cache hits"; volatile data and absolute paths cause misses; local cache first, then remote, with CI pushing; copy-like tasks are not cached because executing them is generally faster. Implementation behavior.
- Gradle User Manual, "Configuration Cache": configuration results are reused unless a recorded input (build scripts, environment variables and system properties read at configuration time, files read) changed. Implementation behavior; used for the no-op rebuild advice on configuration time.
- GitHub Docs, "Dependency caching reference" (docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching): exact key and restore-key matching, 10 GB per repository by default, entries not accessed in 7 days removed, cache contents readable through pull requests so no secrets. Implementation behavior. The advice to weigh restore time against time saved is general reasoning with no published source.

## Doing less work

- Milos Gligoric, Lamyaa Eloussi, and Darko Marinov, "Practical Regression Test Selection with Dynamic File Dependencies," ISSTA 2015 (Ekstazi): tracks each test's file dependencies at run time; on 615 revisions of 32 Java projects, end-to-end test time fell 32% on average and 54% for longer-running suites, compared with running all tests.
- Gregg Rothermel and Mary Jean Harrold, "A Safe, Efficient Regression Test Selection Technique," *ACM TOSEM* 6(2), 1997: selection is safe only when it includes every test whose behavior a change can affect (the dependency-completeness condition).
- Mateusz Machalica, Alex Samylkin, Meredith Porth, and Satish Chandra, "Predictive Test Selection," ICSE-SEIP 2019 (arXiv:1810.05286): learned selection at Facebook halves testing infrastructure cost while still reporting over 99.9% of faulty changes and over 95% of individual test failures, so some failures are missed by design.
- Atif Memon et al., "Taming Google-Scale Continuous Testing," ICSE-SEIP 2017: Google's continuous testing selects tests by reverse dependencies on changed files in the build graph.
- The Rust Compiler Development Guide, "Incremental compilation" and "Incremental compilation in detail" (rustc-dev-guide.rust-lang.org): query-based incremental compilation with red-green change tracking. Gradle User Manual, "Building Java & JVM projects," section "Incremental Java compilation." Implementation behavior.
- pytest documentation, "How to use fixtures," section "Fixture scopes" (function, class, module, package, session): an example of sharing generated test data across tests. Implementation behavior.

## Data pipelines

- dbt documentation, "Configure incremental models" (docs.getdbt.com/docs/build/incremental-models): `is_incremental()` filter; without `unique_key` most adapters append, duplicating rows on reruns; key columns must not be null and must be unique; when logic changes, rebuild with `--full-refresh` on the model and its downstream models; `on_schema_change` does not backfill old rows; lookback filters as examples for late rows. Implementation behavior.
- Apache Spark documentation, "Parquet Files," section "Partition Discovery": partition column values encoded in directory paths. Apache Iceberg documentation, "Partitioning": partitioning by date lets queries skip files for other dates; hidden partitioning. Implementation behavior.
- Apache Spark Structured Streaming Programming Guide, section on watermarking (spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html): data within the watermark delay is never dropped; later data may or may not be aggregated; state for finalized windows is cleared. Implementation behavior.
- Tyler Akidau et al., "The Dataflow Model: A Practical Approach to Balancing Correctness, Latency, and Cost in Massive-Scale, Unbounded, Out-of-Order Data Processing," *PVLDB* 8(12), 2015: watermarks as a heuristic estimate of event-time completeness, and late data arriving after the watermark.
- Martin Kleppmann, *Designing Data-Intensive Applications* (2017), Chapter 10 "Batch Processing" (immutable inputs, outputs replaced on rerun) and Chapter 11 "Stream Processing" (idempotence for exactly-once effects): idempotent steps make retries and reruns safe.

## Behavior traps

- Reproducible Builds project, "Timestamps" (reproducible-builds.org/docs/timestamps/): timestamps are the biggest source of unreproducible output; `SOURCE_DATE_EPOCH` replaces the current time in supporting tools.
- Bazel "Hermeticity" and Mokhov et al. §6.3–6.4 (above) for non-hermetic steps and mixed-run results; Gradle "Build Cache" and Bazel "Remote Caching" (above) for keys that omit inputs.
- The verification procedure (compare incremental and clean builds after modify, add, delete, flag and tool changes, cold and warm caches) applies rule 3 and `DIFFERENTIAL-TESTING.md` to builds; the Bazel "Hermeticity" page's advice to compare output hashes across runs and machines supports building twice from clean. No single published source states the whole procedure.
