Created: 2026 June 24

# mcp-ripgrep

MCP server exposing ripgrep search capabilities to language model clients.

---

## Table of Contents

[1.0 Overview](<#1.0 overview>)
[2.0 Installation](<#2.0 installation>)
[2.1 Prerequisite](<#2.1 prerequisite>)
[2.2 Install](<#2.2 install>)
[2.3 MCP Client Configuration](<#2.3 mcp client configuration>)
[3.0 Usage](<#3.0 usage>)
[4.0 Development](<#4.0 development>)
[Version History](<#version history>)

---

## 1.0 Overview

Placeholder.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Installation

Installs from source via pip. ripgrep itself is a separate runtime dependency (see 2.1).

[Return to Table of Contents](<#table of contents>)

---

## 2.1 Prerequisite

ripgrep (`rg`) must be installed and on `PATH`; it is not bundled.

- macOS: `brew install ripgrep`
- Debian/Ubuntu: `sudo apt-get install ripgrep`

[Return to Table of Contents](<#table of contents>)

---

## 2.2 Install

Single command, into the active Python environment:

```
pip install git+https://github.com/William12556/mcp-ripgrep.git
```

Optional — isolated install on `PATH` (requires pipx):

```
pipx install git+https://github.com/William12556/mcp-ripgrep.git
```

Append a tag to pin a released version, e.g. `@v0.1.0`.

[Return to Table of Contents](<#table of contents>)

---

## 2.3 MCP Client Configuration

Configure the MCP client to launch the `mcp-ripgrep` console script. Example entry for `claude_desktop_config.json`:

```
"mcp-ripgrep": {
  "command": "mcp-ripgrep"
}
```

If the console script is not on the client's `PATH`, give its absolute path.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Usage

Placeholder.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Development

Placeholder.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-06-24 | Initial skeleton |
| 0.2 | 2026-06-24 | Completed §2.0 Installation: ripgrep prerequisite, pip one-liner, optional pipx, MCP client configuration. |

---

Copyright (c) 2026 William Watson. MIT License.
