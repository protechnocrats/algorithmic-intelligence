# Language Companion Files

Load the file for each language the analysis touches. In a project with several languages, load one file per language. Also record the language and runtime version (Kotlin/JVM versus Kotlin Multiplatform, Java version, Python interpreter and version, Swift version and target, Node or browser target, .NET version): standard-library availability depends on it.

| Signals | Load |
|---|---|
| `*.kt`, `*.kts`, Kotlin Gradle plugin | [KOTLIN.md](KOTLIN.md) (plus [JAVA.md](JAVA.md) only for JVM structures Kotlin lacks; rule 14) |
| `*.java`, `pom.xml`, `build.gradle` without Kotlin | [JAVA.md](JAVA.md) |
| `*.swift`, `Package.swift`, `*.xcodeproj` | [SWIFT.md](SWIFT.md) |
| `*.js`, `*.mjs`, `*.cjs`, `*.jsx`, `*.ts`, `*.mts`, `*.cts`, `*.tsx`, `package.json`, `tsconfig.json`, `deno.json` | [JAVASCRIPT-TYPESCRIPT.md](JAVASCRIPT-TYPESCRIPT.md) |
| `*.cs`, `*.csproj`, `*.sln` | [CSHARP.md](CSHARP.md) |
| `*.c`, `*.h` (without C++ sources), C build files (`Makefile`, `CMakeLists.txt`, `meson.build`) | [C.md](C.md) |
| `*.rs`, `Cargo.toml` | [RUST.md](RUST.md) |
| `*.py`, `*.pyi`, `pyproject.toml`, `setup.py`, `requirements.txt` | [PYTHON.md](PYTHON.md) |
| Any other language | [GENERIC.md](GENERIC.md), after first looking for a profile saved in the project at `.complexity-optimizer/languages/<LANGUAGE>.md` (for example `ERLANG.md`). `GENERIC.md` says how to use it, and how to build and save one when none exists |
