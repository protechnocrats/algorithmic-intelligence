# Language Companion Files

Load one file per language the analysis touches. Also record the language and runtime version (Kotlin/JVM versus Kotlin Multiplatform, Java version, Swift version, Node or browser target, .NET version): standard-library availability depends on it.

| Signals | Load |
|---|---|
| `*.kt`, `*.kts`, Kotlin Gradle plugin | [KOTLIN.md](KOTLIN.md) (plus [JAVA.md](JAVA.md) only for JVM structures Kotlin lacks; rule 14) |
| `AndroidManifest.xml`, Android Gradle plugin | Also [ANDROID.md](ANDROID.md) |
| `*.java`, `pom.xml`, `build.gradle` without Kotlin | [JAVA.md](JAVA.md) |
| `*.swift`, `Package.swift`, `*.xcodeproj` | [SWIFT.md](SWIFT.md) |
| `*.js`, `*.mjs`, `*.ts`, `*.tsx`, `package.json`, `tsconfig.json` | [JAVASCRIPT-TYPESCRIPT.md](JAVASCRIPT-TYPESCRIPT.md) |
| `*.cs`, `*.csproj`, `*.sln` | [CSHARP.md](CSHARP.md) |
| `*.c`, `*.h` (without C++ sources), C build files (`Makefile`, `CMakeLists.txt`, `meson.build`) | [C.md](C.md) |
| `*.rs`, `Cargo.toml` | [RUST.md](RUST.md) |
| `*.py`, `pyproject.toml`, `requirements.txt` | [PYTHON.md](PYTHON.md) |
| Any other language | [GENERIC.md](GENERIC.md) |
