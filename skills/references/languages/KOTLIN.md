# References for `languages/KOTLIN.md`

Sources for the claims in `languages/KOTLIN.md`. Read only to verify a claim, on the page for the project's language and library version.

- Kotlin collections: kotlinlang.org/docs/collections-overview.html; API reference: kotlinlang.org/api/core/kotlin-stdlib/
- Floating-point comparison: kotlinlang.org/docs/numbers.html#floating-point-numbers-comparison
- `sortedBy` and `drop`: libraries/stdlib/common/src/generated/_Collections.kt in github.com/JetBrains/kotlin; `compareBy` calling the selector on both arguments: libraries/stdlib/src/kotlin/comparisons/Comparisons.kt. `subList` as a view, `toIntOrNull`: kotlinlang.org/api/core/kotlin-stdlib. `internal` and test source sets: kotlinlang.org/docs/visibility-modifiers.html; `internal` from Java and name mangling: kotlinlang.org/docs/java-to-kotlin-interop.html.
- Packages: github.com/Kotlin/kotlinx.collections.immutable; developer.android.com/reference/kotlin/androidx/collection/package-summary and the Gradle module metadata on Google Maven (platforms).
