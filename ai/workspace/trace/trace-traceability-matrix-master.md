Created: 2026 June 24

# Traceability Matrix

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Functional Requirements](<#2.0 functional requirements>)
[3.0 Non-Functional Requirements](<#3.0 non-functional requirements>)
[4.0 Component Mapping](<#4.0 component mapping>)
[5.0 Design Document Cross-Reference](<#5.0 design document cross-reference>)
[6.0 Test Coverage](<#6.0 test coverage>)
[7.0 Bidirectional Navigation](<#7.0 bidirectional navigation>)
[Version History](<#version history>)

---

## 1.0 Purpose

Maintains bidirectional traceability links between requirements, design, source
code, and tests for the mcp-ripgrep project. Updated at every phase boundary per
P05.

Current state: requirements baselined (`requirements-ca02a3db-mcp-ripgrep.md`),
master design drafted (`design-mcp-ripgrep-master.md`). Code and tests pending.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Functional Requirements

| ID | Requirement | Design | Code | Test | Status |
|---|---|---|---|---|---|
| e1e3a1c8 | search tool (rg --json, structured matches) | master §3.0 components.server/ripgrep/parser | pending | pending | designed |
| d76b2602 | count-matches tool (lines vs matches) | master §3.0 components.server/ripgrep | pending | pending | designed |
| eaecf140 | list-files tool (all vs with-matches) | master §3.0 components.server/ripgrep | pending | pending | designed |
| 3a7478f7 | list-file-types tool (--type-list) | master §3.0 components.server/ripgrep | pending | pending | designed |
| b2e1dfdd | text/bytes data decoding | master §3.0 components.parser | pending | pending | designed |
| f6954177 | actionable errors; exit 1 vs 2 | master §3.0 error_handling | pending | pending | designed |

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Non-Functional Requirements

| ID | Requirement | Target | Design | Code | Test | Status |
|---|---|---|---|---|---|---|
| 98378a50 | cross-platform Windows + macOS | 0 platform-specific failures | master §3.0 nonfunctional_requirements.reliability | pending | pending | designed |
| 991086ca | typed, tested, formatted | mypy 0 errors | master §3.0 nonfunctional_requirements.maintainability | pending | pending | designed |
| 32109138 | no shell injection | shell=False; no string commands | master §3.0 nonfunctional_requirements.security | pending | pending | designed |
| 065a7579 | bounded output | configurable result cap honoured | master §3.0 nonfunctional_requirements.performance | pending | pending | designed |

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Component Mapping

| Component | Requirements | Design | Source | Test |
|---|---|---|---|---|
| server | e1e3a1c8, d76b2602, eaecf140, 3a7478f7, 60a85fc9, af695f17 | master §3.0 components.server | src/mcp_ripgrep/server.py, __main__.py | pending |
| ripgrep | 920668bb, 14c2e121, f6954177, 32109138 | master §3.0 components.ripgrep | src/mcp_ripgrep/ripgrep.py | pending |
| parser | b2e1dfdd | master §3.0 components.parser | src/mcp_ripgrep/parser.py | pending |
| models | 065a7579 | master §3.0 components.models | src/mcp_ripgrep/models.py | pending |
| errors | f6954177 | master §3.0 components.errors | src/mcp_ripgrep/errors.py | pending |

Note: architectural requirements 60a85fc9 (transport/pin), 920668bb (subprocess
invariant), af695f17 (stderr logging), and 14c2e121 (rg on PATH) are traced here
via their owning components, as the matrix has no separate architectural table.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Design Document Cross-Reference

| Design Doc | Requirements | Code | Tests |
|---|---|---|---|
| design-mcp-ripgrep-master.md | all (requirements-ca02a3db set) | src/mcp_ripgrep/* | tests/* (pending) |

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Test Coverage

| Test File | Requirements Verified | Code Coverage |
|---|---|---|
| pending | — | — |

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Bidirectional Navigation

**Forward:** Req → Design → Code → Test

**Backward:** Test → Code → Design → Req

| Direction | Path |
|---|---|
| Forward | requirements-ca02a3db → design-mcp-ripgrep-master → src/mcp_ripgrep → tests |
| Backward | tests → src/mcp_ripgrep → design-mcp-ripgrep-master → requirements-ca02a3db |

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-06-24 | Initial skeleton — P01 project initialization |
| 0.2 | 2026-06-24 | Registered 14 requirements (requirements-ca02a3db) and mapped them to the master design (design-mcp-ripgrep-master) at the requirements→design boundary (P05). |

---

Copyright (c) 2026 William Watson. MIT License.
