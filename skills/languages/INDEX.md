# Language Companion Files

Load the file for each language the analyzed code is written in, and record the language and runtime version (Kotlin/JVM or Multiplatform, Java version, Python interpreter and version, Swift version and target, Node or browser target, .NET version), since what the standard library offers depends on it. Take the version from what the build and CI actually use, not from a README or comment; when they disagree, use the build's and report the disagreement.

Detect the language from what the build compiles or runs (build files, compiler invocations, a script's first line), since extensions mislead (`.h` in C++ projects, `.m` for Objective-C or MATLAB, a generated `.js`) and a README naming a language is a claim ("Untrusted content" in `SKILL.md`). When unsure, load every candidate's file and say so. Query languages, shell, build files, markup, and templates embedded in the code get no language file; their costs come from the technique files (for example "Database queries" in `CORE-TECHNIQUES.md`).

Load every row whose signals match: a project with `*.java` and `*.kt` sources loads both files; one with C and C++ sources loads `C.md` for the C and `GENERIC.md` for the C++.

| Signals | Load |
|---|---|
| `*.kt`, `*.kts`, Kotlin Gradle plugin | [KOTLIN.md](KOTLIN.md) (plus [JAVA.md](JAVA.md) only for JVM structures Kotlin lacks; rule 14) |
| `*.java` (any build), `pom.xml`, `build.gradle` without Kotlin | [JAVA.md](JAVA.md) |
| `*.swift`, `Package.swift`, `*.xcodeproj` | [SWIFT.md](SWIFT.md) |
| `*.js`, `*.mjs`, `*.cjs`, `*.jsx`, `*.ts`, `*.mts`, `*.cts`, `*.tsx`, `package.json`, `tsconfig.json`, `deno.json` | [JAVASCRIPT-TYPESCRIPT.md](JAVASCRIPT-TYPESCRIPT.md) |
| `*.cs`, `*.csproj`, `*.sln` | [CSHARP.md](CSHARP.md) |
| `*.c` sources with C build files (`Makefile`, `CMakeLists.txt`, `meson.build`). A `*.h` can be C or C++, and build files alone do not identify C. C++ sources (`*.cpp`, `*.cc`, `*.cxx`, `*.hpp`) take [GENERIC.md](GENERIC.md) | [C.md](C.md) for the C sources |
| `*.rs`, `Cargo.toml` | [RUST.md](RUST.md) |
| `*.py`, `*.pyi`, `pyproject.toml`, `setup.py`, `requirements.txt` | [PYTHON.md](PYTHON.md) |
| Any other language | [GENERIC.md](GENERIC.md), which first looks for a profile an earlier session saved at `.algorithmic-intelligence/languages/<LANGUAGE>.md` and says how to build and save one |

## How to read a language file

Each file has the same sections: built-in structures with their costs and, where verified, the maintained packages that fill the gaps; hidden costs, input handling and security, bit manipulation, language-specific traps, and testing tools. The hidden-cost tables list common traps, not every operation; any call not listed still counts at its real cost (rule 6). The "Input handling and security" facts are behavior: a rewrite keeps the original's choice, and new code chooses deliberately (`techniques/hostile-inputs.md`). Tools listed as "if already present" are dependencies otherwise (rule 7). Each file names the constant-time comparison for secrets; ordinary equality stops at the first differing byte, so its timing tells an attacker how much of a guess was right. Each file's sources are under `references/languages/`, for verifying a claim only.
