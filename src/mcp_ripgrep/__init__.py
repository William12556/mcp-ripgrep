"""mcp-ripgrep: MCP server exposing ripgrep search to language model clients.

This package provides a Model Context Protocol (MCP) server that exposes
ripgrep search capabilities through four tools:
- search: Full-text search with pattern matching
- count-matches: Count pattern occurrences
- list-files: List files matching criteria
- list-file-types: List available file type filters
"""

from .errors import (
    RgNotFoundError,
    RipgrepError,
    RipgrepExecutionError,
    SearchPathError,
)
from .models import (
    DEFAULT_MAX_RESULTS,
    CountResult,
    FileList,
    Match,
    SearchResult,
    TypeList,
)
from .server import mcp

__all__ = [
    # Server
    "mcp",
    # Models
    "Match",
    "SearchResult",
    "CountResult",
    "FileList",
    "TypeList",
    "DEFAULT_MAX_RESULTS",
    # Errors
    "RipgrepError",
    "RgNotFoundError",
    "SearchPathError",
    "RipgrepExecutionError",
]
