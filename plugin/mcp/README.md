# algorithmic-intelligence MCP server

Exact helpers for the [algorithmic-intelligence](https://github.com/protechnocrats/algorithmic-intelligence) skill: benchmark statistics with an A/A noise floor, growth-rate fits from doubling experiments, planting a known difference in a source file and restoring it byte for byte to show a test can fail, declarations for edits that need no differential test, and the final-summary check.

It never runs project code. The agent runs builds, tests, and benchmarks in its own shell and passes the results in. Standard library only, Python 3.9 or later. The project root is the directory the agent starts the server in, or `ALGORITHMIC_INTELLIGENCE_ROOT`.

Run it without cloning (replace `<tag>` with a release tag):

```
uvx --from "git+https://github.com/protechnocrats/algorithmic-intelligence@<tag>#subdirectory=plugin/mcp" algorithmic-intelligence-mcp
```

or `pipx run --spec "git+https://github.com/protechnocrats/algorithmic-intelligence@<tag>#subdirectory=plugin/mcp" algorithmic-intelligence-mcp`, or `python3 server.py` from a clone. The repository README shows how to register it with each agent.
