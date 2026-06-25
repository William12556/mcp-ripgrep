Created: 2026 June 24

# Prompt (T04) — Implement mcp-ripgrep

---

## Table of Contents

[1.0 Overview](<#1.0 overview>)
[2.0 Prompt Specification](<#2.0 prompt specification>)
[3.0 Tactical Brief](<#3.0 tactical brief>)
[4.0 References](<#4.0 references>)
[Version History](<#version history>)

---

## 1.0 Overview

T04 implementation prompt (protocol P09) directing Claude Code to implement the
mcp-ripgrep server per the baselined master design.

- Source design: `design-mcp-ripgrep-master.md`
- Requirements: `requirements-ca02a3db-mcp-ripgrep.md`
- Coupling: not applicable. This is the initial greenfield build; no T03 issue or
  T02 change exists. `coupled_docs.change_ref` is intentionally empty — a documented
  deviation from the T04 schema, which assumes a change-coupled prompt.

Invocation (per CLAUDE.md §2.0): `implement ai/workspace/prompt/prompt-8057f3c0-implement-mcp-ripgrep.md`

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Prompt Specification

```yaml
prompt_info:
  id: "prompt-8057f3c0"
  task_type: "code_generation"
  source_ref: "design-mcp-ripgrep-master"
  date: "2026-06-24"
  iteration: 1
  coupled_docs:
    change_ref: ""        # not applicable — greenfield initial build (see notes)
    change_iteration: 0

context:
  purpose: "Implement a cross-platform Python stdio MCP server exposing ripgrep search via four consolidated tools."
  integration: "New package src/mcp_ripgrep/; run as a stdio MCP server by an MCP client (e.g. Claude Desktop)."
  knowledge_references: []
  constraints:
    - "Invoke rg via subprocess with an argument list; shell=False; never quote paths/patterns (req 920668bb, 32109138)."
    - "Diagnostics to stderr only; stdout reserved for the stdio protocol (req af695f17)."
    - "Decode data elements keyed 'text' or 'bytes' (base64); tolerate non-UTF-8 (req b2e1dfdd)."
    - "Pin mcp>=1.27,<2; use mcp.server.fastmcp.FastMCP, not PrefectHQ fastmcp (req 60a85fc9)."
    - "Function on Windows and macOS; accept drive-letter and POSIX paths (req 98378a50)."

specification:
  description: "Five-module package implementing search, count-matches, list-files, list-file-types; with pytest suite and pyproject adaptation."
  requirements:
    functional:
      - "search: rg --json; structured matches (path, line_number, text); empty result on no match (req e1e3a1c8)."
      - "count-matches: parameter selects --count (lines) or --count-matches (matches); default matches; per-file + total (req d76b2602)."
      - "list-files: parameter/pattern selects -l (with-matches) vs --files (all); default with-matches when pattern given (req eaecf140)."
      - "list-file-types: rg --type-list; type name + globs (req 3a7478f7)."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Type hints on public interfaces; mypy clean"
        - "Google-style docstrings"
        - "Comprehensive error handling; actionable messages"
        - "Pure functions for command construction and parsing"
  performance:
    - target: "bounded search output"
      metric: "result cap via -m / DEFAULT_MAX_RESULTS (req 065a7579)"

design:
  architecture: "Layered pipeline: server (adapter) -> ripgrep (build + run) -> rg -> parser; errors raised to server."
  components:
    - name: "errors"
      type: "module"
      purpose: "Exception hierarchy."
      interface:
        outputs:
          type: "exceptions"
          description: "RipgrepError, RgNotFoundError, SearchPathError, RipgrepExecutionError."
        raises: []
      logic:
        - "RipgrepError(Exception); the three specific exceptions subclass it; each carries an actionable message."
    - name: "models"
      type: "module"
      purpose: "Pydantic input/output models."
      interface:
        outputs:
          type: "BaseModel subclasses"
          description: "SearchInput, Match, SearchResult, CountResult, FileList, TypeList; DEFAULT_MAX_RESULTS constant."
        raises:
          - "ValidationError"
      logic:
        - "Declarative models; field types drive FastMCP schema generation."
        - "Define DEFAULT_MAX_RESULTS (provisional 200; tunable)."
    - name: "ripgrep"
      type: "module"
      purpose: "Command construction and subprocess execution."
      interface:
        inputs:
          - name: "tool, params"
            type: "str, BaseModel"
            description: "Tool name and validated parameters."
        outputs:
          type: "list[str] / RgResult"
          description: "build_command returns args; run_rg returns stdout/stderr/returncode."
        raises:
          - "RgNotFoundError"
          - "RipgrepExecutionError"
      logic:
        - "build_command(tool, params) -> list[str]: pure; append flags; end with [pattern, path]; no quoting."
        - "run_rg(args) -> RgResult: resolve rg via shutil.which (else RgNotFoundError); asyncio.create_subprocess_exec(*args); shell=False."
        - "Map exit codes: EXIT_NO_MATCH=1 -> empty (not error); EXIT_ERROR=2 -> RipgrepExecutionError(stderr)."
    - name: "parser"
      type: "module"
      purpose: "Parse rg --json; decode data elements."
      interface:
        inputs:
          - name: "stdout"
            type: "str"
            description: "rg --json output."
        outputs:
          type: "list[Match]"
          description: "Parsed matches."
        raises: []
      logic:
        - "parse_search_json(stdout): json.loads each non-empty line; dispatch on 'type' (begin/match/context/end/summary)."
        - "decode_data(elem): return elem['text'] if present; else base64-decode elem['bytes']."
        - "Skip malformed JSON lines without crashing."
    - name: "server"
      type: "module"
      purpose: "FastMCP app and tool registration."
      interface:
        outputs:
          type: "FastMCP"
          description: "Four tools registered with hyphenated names; run over stdio."
        raises: []
      logic:
        - "mcp = FastMCP('mcp-ripgrep')."
        - "Register async tools: search, count_matches (name='count-matches'), list_files (name='list-files'), list_file_types (name='list-file-types')."
        - "Each tool: build args, await run_rg, parse, return model. Translate RipgrepError to an actionable tool error."
        - "__main__.py calls mcp.run() (stdio default)."
  dependencies:
    internal:
      - "errors"
      - "models"
      - "ripgrep"
      - "parser"
    external:
      - "mcp>=1.27,<2"
      - "pydantic"

error_handling:
  strategy: "Validate inputs via Pydantic; map rg exit codes; raise typed exceptions translated to actionable tool errors."
  exceptions:
    - exception: "RgNotFoundError"
      condition: "rg not on PATH"
      handling: "Message names the missing 'rg' binary."
    - exception: "SearchPathError"
      condition: "search path does not exist"
      handling: "Message identifies the path."
    - exception: "RipgrepExecutionError"
      condition: "rg returncode == 2"
      handling: "Message includes rg stderr."
  logging:
    level: "INFO/ERROR"
    format: "concise; stderr only"

testing:
  unit_tests:
    - scenario: "build_command for search with pattern and path"
      expected: "argument list begins with rg, ends with [pattern, path]; no shell string"
    - scenario: "build_command with Windows drive-letter path and POSIX path"
      expected: "path passed through unquoted on both"
    - scenario: "decode_data with text element"
      expected: "returns text verbatim"
    - scenario: "decode_data with bytes element"
      expected: "returns base64-decoded string"
    - scenario: "run_rg with returncode 1"
      expected: "empty result, no exception"
    - scenario: "run_rg with returncode 2"
      expected: "raises RipgrepExecutionError"
    - scenario: "rg absent"
      expected: "raises RgNotFoundError"
  edge_cases:
    - "No matches (exit 1)."
    - "Non-UTF-8 path/content (bytes element)."
    - "count-matches lines vs matches semantics."
    - "list-files all vs with-matches semantics."
  validation:
    - "pytest passes; mypy clean; black, isort, flake8 clean."

deliverable:
  format_requirements:
    - "Save generated code directly to the specified paths."
  files:
    - path: "src/mcp_ripgrep/__init__.py"
      content: ""
    - path: "src/mcp_ripgrep/__main__.py"
      content: ""
    - path: "src/mcp_ripgrep/errors.py"
      content: ""
    - path: "src/mcp_ripgrep/models.py"
      content: ""
    - path: "src/mcp_ripgrep/ripgrep.py"
      content: ""
    - path: "src/mcp_ripgrep/parser.py"
      content: ""
    - path: "src/mcp_ripgrep/server.py"
      content: ""
    - path: "pyproject.toml"
      content: "Add mcp>=1.27,<2 runtime dep; add black/isort/flake8/mypy dev deps and tool config; add [tool.setuptools.packages.find] where=['src']."
    - path: "tests/test_ripgrep.py"
      content: ""
    - path: "tests/test_parser.py"
      content: ""
    - path: "tests/test_server.py"
      content: ""

success_criteria:
  - "Four tools register and are callable over stdio."
  - "rg invoked as an argument list; no shell=True; Windows and POSIX paths both work."
  - "Parser decodes text and bytes; non-UTF-8 does not crash."
  - "Exit 1 = empty result; exit 2 = RipgrepExecutionError; missing rg = RgNotFoundError."
  - "mcp pinned >=1.27,<2."
  - "pytest passes; mypy clean; black/isort/flake8 clean."

element_registry:
  source: "ai/workspace/design/design-mcp-ripgrep-master.md"
  entries:
    modules:
      - name: "mcp_ripgrep.server"
        path: "src/mcp_ripgrep/server.py"
      - name: "mcp_ripgrep.ripgrep"
        path: "src/mcp_ripgrep/ripgrep.py"
      - name: "mcp_ripgrep.parser"
        path: "src/mcp_ripgrep/parser.py"
      - name: "mcp_ripgrep.models"
        path: "src/mcp_ripgrep/models.py"
      - name: "mcp_ripgrep.errors"
        path: "src/mcp_ripgrep/errors.py"
    classes:
      - name: "SearchInput"
        module: "mcp_ripgrep.models"
      - name: "Match"
        module: "mcp_ripgrep.models"
      - name: "SearchResult"
        module: "mcp_ripgrep.models"
      - name: "CountResult"
        module: "mcp_ripgrep.models"
      - name: "FileList"
        module: "mcp_ripgrep.models"
      - name: "TypeList"
        module: "mcp_ripgrep.models"
      - name: "RipgrepError"
        module: "mcp_ripgrep.errors"
      - name: "RgNotFoundError"
        module: "mcp_ripgrep.errors"
      - name: "SearchPathError"
        module: "mcp_ripgrep.errors"
      - name: "RipgrepExecutionError"
        module: "mcp_ripgrep.errors"
    functions:
      - name: "build_command"
        module: "mcp_ripgrep.ripgrep"
        signature: "build_command(tool: str, params: BaseModel) -> list[str]"
      - name: "run_rg"
        module: "mcp_ripgrep.ripgrep"
        signature: "async run_rg(args: list[str]) -> RgResult"
      - name: "parse_search_json"
        module: "mcp_ripgrep.parser"
        signature: "parse_search_json(stdout: str) -> list[Match]"
      - name: "decode_data"
        module: "mcp_ripgrep.parser"
        signature: "decode_data(elem: dict) -> str"
    constants:
      - name: "RG_BINARY"
        module: "mcp_ripgrep.ripgrep"
        type: "str"
      - name: "EXIT_NO_MATCH"
        module: "mcp_ripgrep.ripgrep"
        type: "int"
      - name: "EXIT_ERROR"
        module: "mcp_ripgrep.ripgrep"
        type: "int"
      - name: "DEFAULT_MAX_RESULTS"
        module: "mcp_ripgrep.models"
        type: "int"

notes: |
  Greenfield initial build: no T03/T02 coupling (coupled_docs.change_ref empty by design).
  DEFAULT_MAX_RESULTS provisional value 200 — tunable; confirm with human if a different
  default is preferred. Build order: errors -> models -> ripgrep -> parser -> server ->
  __main__ -> tests -> pyproject. Verify on both Windows and macOS before SHIP.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Tactical Brief

```yaml
tactical_brief: |
  Implement the mcp-ripgrep Python stdio MCP server. Package: src/mcp_ripgrep/.
  Files: errors.py, models.py, ripgrep.py, parser.py, server.py, __main__.py,
  __init__.py; tests under tests/; adapt pyproject.toml.

  Hard constraints:
  - Invoke rg via asyncio.create_subprocess_exec with an argument LIST; shell=False;
    never quote paths/patterns (Windows fails on quoted paths: os error 123).
  - Logging to stderr only; stdout is the stdio protocol channel.
  - Decode rg --json data elements keyed 'text' or 'bytes' (base64); tolerate non-UTF-8.
  - Use mcp.server.fastmcp.FastMCP; pin mcp>=1.27,<2 (not PrefectHQ fastmcp).
  - Must work on Windows and macOS; accept C:\ and POSIX paths.

  Steps:
  1. errors.py: RipgrepError base; RgNotFoundError, SearchPathError, RipgrepExecutionError.
  2. models.py: Pydantic SearchInput, Match, SearchResult, CountResult, FileList, TypeList;
     DEFAULT_MAX_RESULTS=200.
  3. ripgrep.py: build_command(tool, params)->list[str] (pure); run_rg(args)->RgResult
     (async; resolve rg via shutil.which else RgNotFoundError); RG_BINARY='rg',
     EXIT_NO_MATCH=1, EXIT_ERROR=2; exit1=empty, exit2=RipgrepExecutionError.
  4. parser.py: parse_search_json(stdout) over JSON lines by 'type'; decode_data(elem)
     text or base64 bytes; skip malformed lines.
  5. server.py: FastMCP('mcp-ripgrep'); async tools search, count-matches, list-files,
     list-file-types; translate RipgrepError to actionable tool errors.
  6. __main__.py: mcp.run() (stdio default).
  7. pyproject.toml: add mcp>=1.27,<2; black/isort/flake8/mypy dev deps + config;
     [tool.setuptools.packages.find] where=['src'].
  8. tests: build_command (both path separators), decode_data (text+bytes),
     exit-code mapping (1 vs 2), rg-not-found.

  Success: 4 tools callable over stdio; arg-list invocation; text/bytes decoding;
  exit-code mapping correct; pytest passes; mypy/black/isort/flake8 clean.
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 References

GALLANT, A. (BurntSushi), 2026. *rg(1) — ripgrep manual* [online]. Available at: https://manpages.debian.org/testing/ripgrep/rg.1.en.html [Accessed 24 June 2026].

MODEL CONTEXT PROTOCOL, 2026. *python-sdk: the official Python SDK for Model Context Protocol servers and clients* [online]. Available at: https://github.com/modelcontextprotocol/python-sdk [Accessed 24 June 2026].

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-06-24 | Initial draft. Greenfield T04 implementation prompt for the five-module ripgrep MCP server, derived from `design-mcp-ripgrep-master`. Includes tactical brief and documented coupling deviation. |

---

Copyright (c) 2026 William Watson. MIT License.
