Created: 2026 June 24

# mcp-ripgrep — Claude Code Context

---

## Table of Contents

[1.0 Project](<#1.0 project>)
[2.0 Governance](<#2.0 governance>)
[3.0 Technology Stack](<#3.0 technology stack>)
[4.0 Core Development Rules](<#4.0 core development rules>)
[5.0 Development Philosophy](<#5.0 development philosophy>)
[6.0 Coding Best Practices](<#6.0 coding best practices>)
[7.0 Formatting and Type Checking](<#7.0 formatting and type checking>)
[8.0 Common Commands](<#8.0 common commands>)
[9.0 Key Paths](<#9.0 key paths>)
[Version History](<#version history>)

---

## 1.0 Project

MCP server exposing ripgrep (`rg`) search to language model clients. Python package (`mcp-ripgrep`).

- Type: stdio MCP server; spawned as a subprocess by the MCP client (e.g. Claude Desktop).
- Transport: stdio. No network, no authentication.
- External dependency: ripgrep (`rg`) binary on `PATH`. Not bundled.
- Target platforms: Windows and macOS. Cross-platform correctness is a primary design constraint.
- Build / development hosts: Mac Mini (Apple Silicon, current) and Windows.
- Python: 3.9+  |  dev venv: `venv/`
- Install: `pip install -e .[dev]`
- Source: `src/` (implementation pending)  |  Tests: `tests/` (pytest)

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Governance

**Prime directive**: Do not create, add, remove, or change source code or documents
unless explicitly requested by the T04 prompt task.

- Governance: `ai/governance.md`  |  Orientation: `ai/primer.md`
- Workflow (`src/` changes only): T03 issue → T02 change → T04 prompt, sharing one 8-hex UUID
- Trivial exemption (P03 §1.4.12): single function, ≤20 line delta, no interface change,
  unambiguous, human-approved → git commit is the sole audit record
- Active docs: `ai/workspace/{issues,change,prompt}/`; completed move to `closed/` subdirs
- Task invocation: `implement ai/workspace/prompt/prompt-<uuid>-<name>.md`

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Technology Stack

| Concern | Implementation |
|---|---|
| MCP framework | Python MCP SDK (FastMCP), stdio transport |
| Tool schemas | Pydantic models; typed inputs and outputs |
| Subprocess | stdlib `subprocess` — invoke `rg` via an argument list, never a shell command string |
| Output parsing | `rg --json` where structured results are required; plain text otherwise |
| Async | `asyncio` (pytest `asyncio_mode = auto`) |
| Logging | stderr only — stdout is reserved for the MCP stdio channel |

**Critical cross-platform constraint**: `rg` must be invoked with `subprocess` using an
argument list (e.g. `["rg", "-n", pattern, path]`), not a shell string. Shell-string
construction with manual quoting fails on Windows: single quotes are passed to `rg` as
literal characters, producing an invalid path (os error 123). This is the root defect of
the reference implementation (`mcollina/mcp-ripgrep`) and the primary reason for this rewrite.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Core Development Rules

1. **Package management**: pip only. Editable install: `pip install -e .[dev]`. Do not introduce `uv` or `poetry`.
2. **Subprocess invocation**: always `subprocess` with an argument list; never `shell=True`;
   never hand-quote paths or patterns. Non-negotiable for cross-platform correctness.
3. **Path handling**: use `pathlib` / `os.path`; do not assume POSIX separators; validate
   Windows drive-letter paths (`C:\...`) and POSIX paths alike.
4. **Code quality**: type hints on all public interfaces; Google-style docstrings on public APIs;
   small, focused functions; follow existing patterns.
5. **Testing**: `pytest` (`pytest-asyncio`, `pytest-cov` configured). New features require tests;
   bug fixes require regression tests; cover edge cases, error paths, and both path separators.
6. **Naming / style**: PEP 8 — `snake_case` functions/variables, `PascalCase` classes,
   `UPPER_SNAKE_CASE` constants; f-strings for formatting.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Development Philosophy

- **Simplicity**: Write simple, straightforward code.
- **Readability**: Make code easy to understand.
- **Performance**: Consider performance without sacrificing readability.
- **Maintainability**: Write code that is easy to update.
- **Testability**: Ensure code is testable.
- **Reusability**: Create reusable components, subordinate to minimal-change scope.
- **Less code = less debt**: Minimize code footprint.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Coding Best Practices

- **Early returns**: Avoid nested conditions.
- **Descriptive names**: Clear variable and function names.
- **Constants over magic values**: Name fixed values (e.g. `rg` flags).
- **DRY**: Do not repeat yourself. Centralise `rg` command construction in one place.
- **Minimal changes**: Modify only code related to the task at hand.
- **Function ordering**: Define composing functions before their components.
- **TODO comments**: Mark issues in existing code with a `TODO:` prefix.
- **Build iteratively**: Start minimal and verify before adding complexity.
- **Cross-platform testing**: Verify on both Windows and macOS path forms before completion.
- **Clean logic**: Keep core logic clean; push implementation details to the edges.
- **Caveat**: This server is largely stateless subprocess orchestration. Prefer pure functions
  for command construction and output parsing; they are the most testable units.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Formatting and Type Checking

- Format: `black`, `isort` (profile `black`). Lint: `flake8`. Type: `mypy`.
- To be declared in `pyproject.toml` dev dependencies and tool config during implementation.
- Line length: confirm a single limit (PEP 8 79 vs `black` default 88) before relying on either.
- Fix order on failures: formatting → type errors → linting.
- Optional handling: explicit `None` checks; narrow types before use.
- Syntax check a file without execution: `python -c "import ast; ast.parse(open('src/path/to/file.py').read())"`

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Common Commands

```bash
# Activate dev venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows (PowerShell / cmd)

# Install
pip install -e .[dev]

# Run tests
pytest

# Test the server interactively (requires Node.js)
npx @modelcontextprotocol/inspector python -m <module>   # module name defined during design

# Syntax check a file
python -c "import ast; ast.parse(open('src/path/to/file.py').read())"
```

Note: the server entry point and import module name are defined during design
(see `ai/workspace/design/`) and are not asserted here.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Key Paths

```
src/                 MCP server implementation (currently placeholder)
tests/               pytest suite
bin/                 scripts (currently placeholder)
pyproject.toml       package metadata, pytest and coverage config
ai/
  governance.md      authoritative governance
  primer.md          orientation and quick reference
  workflow.md        full workflow flowchart
  workspace/         design, requirements, issues, change, prompt, test, trace
  templates/         T01–T07 document templates
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-06-24 | Initial draft. Adapted from `GTach/ai/doc/CLAUDE.md`; re-oriented to a Python stdio MCP server wrapping ripgrep. Encoded the cross-platform subprocess argument-list constraint (os error 123 root cause). Open decision flagged: adopt or defer `black`/`isort`/`flake8`/`mypy`. |
| 0.2 | 2026-06-24 | Corrected current dev host to Mac Mini (§1.0). Resolved §7.0: adopt `black`/`isort`/`flake8`/`mypy` for consistency with GTach, to be declared in `pyproject.toml` during implementation. |

---

Copyright (c) 2026 William Watson. MIT License.
