#!/bin/bash
# mcp-ripgrep Install Script  (DEVELOPER CONVENIENCE — not the user-facing install)
#
# End users do NOT need this script. Install with a single command:
#   pip install git+https://github.com/William12556/mcp-ripgrep.git
#   (or, isolated:  pipx install git+https://github.com/William12556/mcp-ripgrep.git)
#
# This helper is for maintainers working from a clone: it creates an isolated
# venv at ~/mcp-ripgrep/venv, installs from GitHub, and prints the MCP client
# config. Because it lives inside the repository, it cannot be the user-facing
# installer.
#
# Supports: macOS, Linux
# Usage: ./install.sh [git-ref]
#   git-ref  optional branch or tag (default: repository default branch)
# Copyright (c) 2026 William Watson. MIT License.

set -e  # Exit on error

# ---------------------------------------------------------------------------
# Configuration (override via environment)
# ---------------------------------------------------------------------------
REPO_URL="${MCP_RIPGREP_REPO:-https://github.com/William12556/mcp-ripgrep.git}"
INSTALL_DIR="${MCP_RIPGREP_HOME:-$HOME/mcp-ripgrep}"
VENV_DIR="$INSTALL_DIR/venv"
REF="${1:-}"

# ---------------------------------------------------------------------------
# OS check
# ---------------------------------------------------------------------------
OS="$(uname -s)"
case "$OS" in
    Darwin*|Linux*) ;;
    *)
        echo "ERROR: Unsupported operating system: $OS (macOS/Linux only)"
        echo "Windows: use a PowerShell equivalent or install into a venv manually."
        exit 1
        ;;
esac

# ---------------------------------------------------------------------------
# python3 availability
# ---------------------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found in PATH"
    exit 1
fi

# ---------------------------------------------------------------------------
# ripgrep availability (runtime dependency; not bundled)
# ---------------------------------------------------------------------------
if ! command -v rg >/dev/null 2>&1; then
    echo "WARNING: ripgrep (rg) not found on PATH."
    echo "         The server requires it at runtime."
    case "$OS" in
        Darwin*) echo "         Install: brew install ripgrep" ;;
        Linux*)  echo "         Install: sudo apt-get install ripgrep" ;;
    esac
fi

# ---------------------------------------------------------------------------
# Build the pip source specifier
# ---------------------------------------------------------------------------
if [ -n "$REF" ]; then
    SPEC="git+${REPO_URL}@${REF}"
else
    SPEC="git+${REPO_URL}"
fi

echo "==> Installing mcp-ripgrep"
echo "==> Source:  $SPEC"
echo "==> Target:  $INSTALL_DIR"

# ---------------------------------------------------------------------------
# Virtual environment
# ---------------------------------------------------------------------------
mkdir -p "$INSTALL_DIR"
if [ ! -d "$VENV_DIR" ]; then
    echo "==> Creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------
echo "==> Upgrading pip..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip

echo "==> Installing package from GitHub..."
"$VENV_DIR/bin/pip" install --upgrade "$SPEC"

# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------
echo "==> Verifying installation..."
"$VENV_DIR/bin/python" -c "import mcp_ripgrep; print('import ok')"

SERVER_BIN="$VENV_DIR/bin/mcp-ripgrep"
if [ ! -x "$SERVER_BIN" ]; then
    echo "ERROR: console script not found at $SERVER_BIN"
    exit 1
fi

echo ""
echo "✓ Installation successful"
echo ""
echo "MCP client configuration (claude_desktop_config.json):"
echo ""
echo "  \"mcp-ripgrep\": {"
echo "    \"command\": \"$SERVER_BIN\""
echo "  }"
echo ""
echo "To update later:   ./bin/install.sh [git-ref]"
echo "Raw one-liner:     $VENV_DIR/bin/pip install --upgrade \"$SPEC\""
