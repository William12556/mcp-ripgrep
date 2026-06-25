Created: 2026 June 24

# Requirements — mcp-ripgrep

---

## Table of Contents

[1.0 Overview](<#1.0 overview>)
[2.0 Requirements Specification](<#2.0 requirements specification>)
[3.0 References](<#3.0 references>)
[Version History](<#version history>)

---

## 1.0 Overview

Requirements (T07, protocol P10) for the mcp-ripgrep server: a Python stdio MCP
server exposing ripgrep (`rg`) search to language model clients. The tool surface
is consolidated to four tools. The defining constraint is cross-platform
correctness (Windows and macOS), addressed by invoking `rg` via a subprocess
argument list rather than a shell command string.

This document is `active`. It requires human approval to baseline before design (P02).

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Requirements Specification

```yaml
project_info:
  name: "mcp-ripgrep"
  version: "0.1.0"
  date: "2026-06-24"
  author: ""
  status: "active"

naming_conventions:
  package_name: "mcp_ripgrep"
  module_style: "snake_case"
  class_style: "PascalCase"
  function_style: "snake_case"
  constant_style: "UPPER_SNAKE_CASE"
  notes: "Distribution name 'mcp-ripgrep'; import package 'mcp_ripgrep'."

functional_requirements:
  - id: "e1e3a1c8"
    type: "functional"
    description: "Provide a 'search' tool that runs ripgrep with --json and returns structured match results. Consolidates basic and advanced search into one parameterised tool."
    acceptance_criteria:
      - "Accepts a pattern (regex by default) and a search path."
      - "Supports options: case sensitivity, fixed-strings, whole-word, file globs, file types, context lines (before/after), include-hidden, line numbers, result limit."
      - "Parses begin/match/context/end/summary messages; returns matches with file path, line number, and matched text."
      - "Returns an empty result set (not an error) when there are no matches."
    source: "stakeholder"
    rationale: "Consolidation per Decision 1; --json yields structured output."
    dependencies:
      - "920668bb"
      - "b2e1dfdd"
  - id: "d76b2602"
    type: "functional"
    description: "Provide a 'count-matches' tool returning match counts per file."
    acceptance_criteria:
      - "A parameter selects semantics: matching lines (--count) or individual matches (--count-matches)."
      - "Default is individual matches."
      - "Returns per-file counts and an aggregate total."
    source: "constraint"
    rationale: "ripgrep distinguishes matching lines from individual matches; both are exposed via one parameter (semantic fork resolved)."
    dependencies:
      - "920668bb"
  - id: "eaecf140"
    type: "functional"
    description: "Provide a 'list-files' tool enumerating files."
    acceptance_criteria:
      - "A parameter selects scope: all searchable files (--files) or files containing a match (-l/--files-with-matches)."
      - "Default: files-with-matches when a pattern is supplied; all searchable files when no pattern is supplied."
      - "Honours file globs and type filters."
    source: "constraint"
    rationale: "Semantic fork resolved by parameter; --files takes no pattern, -l requires one."
    dependencies:
      - "920668bb"
  - id: "3a7478f7"
    type: "functional"
    description: "Provide a 'list-file-types' tool returning ripgrep's supported type definitions via --type-list."
    acceptance_criteria:
      - "Returns type names with their associated globs."
      - "Requires no parameters."
    source: "stakeholder"
    rationale: "Parity with the reference tool surface."
    dependencies:
      - "920668bb"
  - id: "b2e1dfdd"
    type: "functional"
    description: "Decode ripgrep JSON data elements that may be keyed 'text' or 'bytes'."
    acceptance_criteria:
      - "When a data element uses 'text', use it directly."
      - "When a data element uses 'bytes', base64-decode it without corrupting the protocol stream."
      - "Non-UTF-8 paths or content do not crash any tool."
    source: "constraint"
    rationale: "ripgrep emits text or bytes because paths and contents are not guaranteed to be valid UTF-8."
    dependencies: []
  - id: "f6954177"
    type: "functional"
    description: "Return actionable errors for failure conditions."
    acceptance_criteria:
      - "Missing 'rg' on PATH produces a clear message naming the missing binary."
      - "A non-existent search path produces a clear message identifying the path."
      - "ripgrep exit code 1 (no matches) is treated as a normal empty result, not an error; exit code 2 is reported as an error."
    source: "constraint"
    rationale: "Distinguishing exit 1 from exit 2 prevents misreporting empty results as failures."
    dependencies:
      - "14c2e121"
      - "920668bb"

non_functional_requirements:
  - id: "98378a50"
    type: "non_functional"
    category: "reliability"
    description: "Identical behaviour on Windows and macOS."
    acceptance_criteria:
      - "All tools function on both Windows and macOS."
      - "Windows drive-letter paths (C:\\...) and POSIX paths are both accepted."
      - "Regression tests cover both path separators."
    target_metric: "0 platform-specific failures across the tool set on Windows and macOS"
    source: "constraint"
    rationale: "The reference implementation failed on Windows (os error 123); cross-platform correctness is the primary driver of this project."
    dependencies:
      - "920668bb"
  - id: "991086ca"
    type: "non_functional"
    category: "maintainability"
    description: "Typed, tested, consistently formatted code."
    acceptance_criteria:
      - "Type hints on all public interfaces; mypy reports no errors."
      - "pytest suite with coverage; new behaviour is covered."
      - "black, isort, and flake8 report clean."
    target_metric: "mypy: 0 errors; command construction and JSON parsing under test"
    source: "constraint"
    rationale: "Toolchain adopted per Decision 2 (CLAUDE.md section 7.0)."
    dependencies: []
  - id: "32109138"
    type: "non_functional"
    category: "security"
    description: "Avoid shell injection."
    acceptance_criteria:
      - "rg is invoked without a shell (shell=False); arguments are passed as a list."
      - "Patterns and paths are never interpolated into a shell string."
    target_metric: "no use of shell=True; no string-built commands"
    source: "constraint"
    rationale: "An argument list eliminates the injection surface and the Windows quoting defect simultaneously."
    dependencies:
      - "920668bb"
  - id: "065a7579"
    type: "non_functional"
    category: "usability"
    description: "Bound output to protect client context."
    acceptance_criteria:
      - "The search tool supports a result limit mapped to ripgrep's -m/--max-count."
      - "Output is concise and structured."
    target_metric: "configurable result cap is honoured"
    source: "constraint"
    rationale: "Unbounded results degrade client context; a cap keeps responses focused."
    dependencies:
      - "e1e3a1c8"

architectural_requirements:
  - id: "60a85fc9"
    type: "architectural"
    description: "stdio MCP server built on the official SDK's FastMCP."
    acceptance_criteria:
      - "Server uses mcp.server.fastmcp.FastMCP and runs over stdio."
      - "Dependency pinned as mcp>=1.27,<2."
    constraints:
      - "Use the official 'mcp' package, not PrefectHQ 'fastmcp'."
      - "mcp v2 (stable 2026-07-27) introduces breaking changes; defer adoption until validated."
    source: "constraint"
    rationale: "Decision 3; the <2 pin avoids an imminent breaking major release."
    dependencies: []
  - id: "920668bb"
    type: "architectural"
    description: "ripgrep is invoked via subprocess with an argument list."
    acceptance_criteria:
      - "The command is built as a list (e.g. ['rg', '--json', pattern, path]); never a shell string."
      - "Patterns and paths are not manually quoted."
    constraints:
      - "shell=False always."
    source: "constraint"
    rationale: "Single-quote shell-string construction is the root cause of the reference defect (os error 123 on Windows)."
    dependencies: []
  - id: "af695f17"
    type: "architectural"
    description: "Diagnostic logging is written to stderr only."
    acceptance_criteria:
      - "No tool writes diagnostics to stdout."
      - "stdout carries only the MCP stdio protocol stream."
    constraints:
      - "Use stderr or the FastMCP Context logging API."
    source: "constraint"
    rationale: "stdout is the stdio transport channel; writing to it corrupts the protocol."
    dependencies:
      - "60a85fc9"
  - id: "14c2e121"
    type: "architectural"
    description: "ripgrep binary is an external runtime dependency."
    acceptance_criteria:
      - "rg is resolved from PATH."
      - "Absence is detected and reported (see f6954177)."
      - "rg is not bundled with the package."
    constraints:
      - "No vendoring of the rg binary."
    source: "constraint"
    rationale: "Keeps the package light and defers binary distribution to the platform."
    dependencies: []

traceability:
  design_refs: []
  test_refs: []
  code_refs: []

validation:
  completeness_check: "Tool surface (4 tools), invocation invariant, encoding contract, error handling, portability, security, and transport are captured."
  clarity_check: "Requirements are unambiguous; the two semantic forks (count, list-files) are resolved by parameter."
  testability_check: "All acceptance criteria are verifiable via pytest, including cross-platform path cases."
  conflicts_identified: []

version_history:
  - version: "0.1"
    date: "2026-06-24"
    author: ""
    changes:
      - "Initial requirements for the Python stdio ripgrep MCP server (consolidated four-tool surface)."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t07_requirements"
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 References

GALLANT, A. (BurntSushi), 2026. *rg(1) — ripgrep manual* [online]. Available at: https://manpages.debian.org/testing/ripgrep/rg.1.en.html [Accessed 24 June 2026].

MODEL CONTEXT PROTOCOL, 2026. *python-sdk: the official Python SDK for Model Context Protocol servers and clients* [online]. Available at: https://github.com/modelcontextprotocol/python-sdk [Accessed 24 June 2026].

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-06-24 | Initial draft. Captures the consolidated four-tool surface, the subprocess argument-list invariant, the ripgrep text/bytes encoding contract, the `mcp>=1.27,<2` pin, and the two semantic forks (count, list-files) resolved by parameter. |

---

Copyright (c) 2026 William Watson. MIT License.
