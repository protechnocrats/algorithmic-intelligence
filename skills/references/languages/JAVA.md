# References for `languages/JAVA.md`

Sources for the claims in `languages/JAVA.md`. Read only to verify a claim, on the page for the project's language and library version.

- Java collections API: docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/package-summary.html (Java 21; replace `21` with the project's version)
- `Comparator.comparing`: src/java.base/share/classes/java/util/Comparator.java in github.com/openjdk/jdk. Stream reuse: java/util/stream/AbstractPipeline.java. `ArrayList.hashCode`, `removeAll`: java/util/ArrayList.java. `String` hash cache: java/lang/String.java. `Throwable` stack traces, `List.subList`: docs.oracle.com/en/java/javase/21/docs/api.
- Packages: guava.dev API docs (`MinMaxPriorityQueue`, `Comparators`, `TreeMultiset`, `Multimap`); github.com/vigna/fastutil; github.com/eclipse-collections/eclipse-collections; versions from Maven Central metadata.
