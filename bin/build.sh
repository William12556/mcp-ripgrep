#!/bin/bash
# mcp-ripgrep Build Script
# Cleans previous builds and produces a wheel + sdist via the build backend.
# Copyright (c) 2026 William Watson. MIT License.

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# python3 availability and version (>= 3.9)
# ---------------------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]; }; then
    echo "ERROR: Python 3.9+ required, found $PYTHON_VERSION"
    exit 1
fi

# ---------------------------------------------------------------------------
# build module availability
# ---------------------------------------------------------------------------
if ! python3 -m build --version >/dev/null 2>&1; then
    echo "ERROR: 'build' module not found"
    echo "Install: python3 -m pip install build"
    exit 1
fi

# ---------------------------------------------------------------------------
# Version (read-only; not auto-incremented)
# ---------------------------------------------------------------------------
VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
if [ -z "$VERSION" ]; then
    echo "ERROR: Could not extract version from pyproject.toml"
    exit 1
fi

echo "==> Building mcp-ripgrep version $VERSION"

# ---------------------------------------------------------------------------
# Clean and build
# ---------------------------------------------------------------------------
echo "==> Cleaning previous builds..."
rm -rf dist/ build/ ./*.egg-info src/*.egg-info

echo "==> Building distribution..."
python3 -m build

# ---------------------------------------------------------------------------
# Verify artefacts
# ---------------------------------------------------------------------------
WHEEL=$(ls dist/*.whl 2>/dev/null | head -1)
SDIST=$(ls dist/*.tar.gz 2>/dev/null | head -1)
if [ -z "$WHEEL" ] || [ -z "$SDIST" ]; then
    echo "ERROR: Expected wheel and sdist not found in dist/"
    exit 1
fi

echo ""
echo "✓ Build successful: version $VERSION"
ls -lh "$WHEEL" "$SDIST"
echo ""
echo "Next: ./bin/release.sh   (publish)   or   ./bin/install.sh   (install from GitHub)"
