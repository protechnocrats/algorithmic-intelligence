# Android

Load this file, in addition to `KOTLIN.md` or `JAVA.md`, for Android apps and libraries. Record `minSdk`, `targetSdk`, and whether core-library desugaring is enabled: newer `java.util` APIs are unavailable on old devices without it.

## Android-specific structures

`SparseArray`, `SparseIntArray`, `SparseBooleanArray`, `LongSparseArray`, and `ArrayMap`/`ArraySet` avoid boxing and use less memory, but lookups are binary search, **O(log n)**, and insertion and removal are O(n). By rule 2, do not replace a `HashMap` with one of these to save memory when it makes lookups slower. They fit small collections (hundreds of entries) where a benchmark shows they are at least as fast. Do not apply Android Lint's "use SparseArray" suggestion blindly. `android.util.LruCache` is a bounded cache (rule 1).

## Hot spots

- **Main thread.** Anything over a few milliseconds on the main thread is a time problem regardless of Big-O: at 60 Hz a frame has 16 ms, at 120 Hz about 8 ms. Disk, network, and database work on the main thread shows up in `StrictMode`. Moving work to `Dispatchers.Default` (CPU) or `Dispatchers.IO` changes threading (rule 11): ask unless the call is already asynchronous.
- **Jetpack Compose.** Expensive computation in a composable runs on every recomposition: `remember(keys) { }` for derived values, `derivedStateOf` for values derived from frequently changing state. Read fast-changing state in the layout or draw phase (lambda modifiers such as `Modifier.offset { }`, `drawBehind`, `graphicsLayer { }`) so it does not recompose. Give `LazyColumn` items stable `key`s and a `contentType`. Unstable parameters (a plain `List`, a class from a module the Compose compiler does not process) defeat skipping; with strong skipping (the default in recent Compose compilers) they are compared by instance, so a new list each recomposition still recomposes. Check the compiler's stability reports before changing types.
- **Views.** No allocation or heavy work in `onDraw`, `onMeasure`, `onLayout`, or `onBindViewHolder`. `DiffUtil`/`ListAdapter` instead of `notifyDataSetChanged()`. Deep or nested weighted layouts multiply measure passes.
- **Room and SQLite.** Queries inside loops (N+1): one query with `IN (:ids)`, a `@Relation`, or a join. Many inserts outside a transaction each commit separately: wrap them in one `@Transaction` (changes atomicity, so it is a behavior change for review). Indexes for filtered and joined columns are a schema change: ask.
- **Startup.** Work in `Application.onCreate`, content providers, and eager dependency-injection graphs delays the first frame. Baseline Profiles precompile hot code paths; adding one is a build change, so ask.
- **Coroutines and Flow.** See "Coroutines and server-side Kotlin" in `KOTLIN.md`. `collectAsStateWithLifecycle` and `repeatOnLifecycle` stop collection in the background; switching from them changes when work runs.

## Profiling and benchmarking

- **Profiling:** Android Studio's CPU and memory profilers (sampled and traced method recording, allocation tracking); Perfetto system traces for jank, main-thread blocking, and binder calls; `Trace.beginSection`/`endSection` (or `androidx.tracing`) to mark sections. Profile a release build (`profileable`) on a real device: debuggable builds disable optimizations and distort results.
- **Benchmarks, if already present:** Jetpack Microbenchmark (`androidx.benchmark`) for code, Macrobenchmark for startup, scrolling, and frame timing. Otherwise a timing harness in an instrumented test, with warmup and medians, on a real device; emulators and debug builds mislead.
- **Tests:** Robolectric for framework code on the JVM; instrumented tests on a device for anything that depends on ART, the GPU, or real I/O timing.

## References (for verifying claims; not required reading)

- Android performance: developer.android.com/topic/performance; Compose performance: developer.android.com/develop/ui/compose/performance
