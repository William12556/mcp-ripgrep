"""FastMCP server exposing ripgrep search tools.

This module defines the MCP server and registers four tools:
- search: Full-text search with pattern matching
- count-matches: Count pattern occurrences
- list-files: List files matching criteria
- list-file-types: List available file type filters
"""

import os
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .errors import RipgrepError, SearchPathError
from .models import (
    DEFAULT_MAX_RESULTS,
    CountResult,
    FileList,
    SearchResult,
    TypeList,
)
from .parser import (
    parse_count_output,
    parse_file_list,
    parse_search_json,
    parse_type_list,
)
from .ripgrep import (
    build_count_command,
    build_list_files_command,
    build_list_types_command,
    build_search_command,
    run_rg,
)

# Create the FastMCP server instance
mcp = FastMCP("mcp-ripgrep")


def validate_path(path: str) -> None:
    """Validate that a search path exists.

    Args:
        path: File or directory path to validate.

    Raises:
        SearchPathError: If the path does not exist.
    """
    if not os.path.exists(path):
        raise SearchPathError(path)


@mcp.tool(name="search")
async def search(
    pattern: str,
    path: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    case_sensitive: bool = True,
    include_hidden: bool = False,
    file_type: Optional[str] = None,
    glob: Optional[str] = None,
    context_lines: int = 0,
) -> SearchResult:
    """Search for a pattern in files using ripgrep.

    Args:
        pattern: Regular expression pattern to search for.
        path: File or directory path to search in.
        max_results: Maximum number of matches to return (default 200).
        case_sensitive: Whether the search is case-sensitive (default True).
        include_hidden: Whether to search hidden files (default False).
        file_type: File type to search (e.g., 'py', 'js', 'rust').
        glob: Glob pattern to filter files (e.g., '*.py', 'src/**/*.ts').
        context_lines: Number of context lines before and after match.

    Returns:
        SearchResult with matches and metadata.
    """
    try:
        validate_path(path)

        args = build_search_command(
            pattern=pattern,
            path=path,
            max_results=max_results,
            case_sensitive=case_sensitive,
            include_hidden=include_hidden,
            file_type=file_type,
            glob=glob,
            context_lines=context_lines,
        )

        result = await run_rg(args)

        matches, total = parse_search_json(result.stdout)

        # Determine if results were truncated
        truncated = len(matches) >= max_results

        return SearchResult(
            matches=matches,
            total_matches=total,
            truncated=truncated,
        )

    except RipgrepError as e:
        # Log to stderr and return empty result with error indication
        print(f"Search error: {e}", file=sys.stderr)
        raise


@mcp.tool(name="count-matches")
async def count_matches(
    pattern: str,
    path: str,
    count_type: str = "matches",
    case_sensitive: bool = True,
    include_hidden: bool = False,
    file_type: Optional[str] = None,
    glob: Optional[str] = None,
) -> CountResult:
    """Count pattern occurrences in files using ripgrep.

    Args:
        pattern: Regular expression pattern to count.
        path: File or directory path to search in.
        count_type: 'matches' counts total occurrences, 'lines' counts
            lines with at least one match (default 'matches').
        case_sensitive: Whether the search is case-sensitive (default True).
        include_hidden: Whether to search hidden files (default False).
        file_type: File type to search (e.g., 'py', 'js', 'rust').
        glob: Glob pattern to filter files.

    Returns:
        CountResult with per-file counts and total.
    """
    try:
        validate_path(path)

        args = build_count_command(
            pattern=pattern,
            path=path,
            count_type=count_type,
            case_sensitive=case_sensitive,
            include_hidden=include_hidden,
            file_type=file_type,
            glob=glob,
        )

        result = await run_rg(args)

        files, total = parse_count_output(result.stdout)

        return CountResult(files=files, total=total)

    except RipgrepError as e:
        print(f"Count error: {e}", file=sys.stderr)
        raise


@mcp.tool(name="list-files")
async def list_files(
    path: str,
    pattern: Optional[str] = None,
    mode: str = "with-matches",
    include_hidden: bool = False,
    file_type: Optional[str] = None,
    glob: Optional[str] = None,
) -> FileList:
    """List files matching criteria using ripgrep.

    Args:
        path: Directory path to list files from.
        pattern: Pattern to search for. When provided with mode='with-matches',
            lists only files containing matches. When omitted with mode='all',
            lists all searchable files.
        mode: 'with-matches' lists files containing pattern matches (-l),
            'all' lists all files ripgrep would search (--files).
        include_hidden: Whether to include hidden files (default False).
        file_type: File type to filter (e.g., 'py', 'js', 'rust').
        glob: Glob pattern to filter files.

    Returns:
        FileList with file paths and count.
    """
    try:
        validate_path(path)

        args = build_list_files_command(
            path=path,
            pattern=pattern,
            mode=mode,
            include_hidden=include_hidden,
            file_type=file_type,
            glob=glob,
        )

        result = await run_rg(args)

        files = parse_file_list(result.stdout)

        return FileList(files=files, total=len(files))

    except RipgrepError as e:
        print(f"List files error: {e}", file=sys.stderr)
        raise


@mcp.tool(name="list-file-types")
async def list_file_types() -> TypeList:
    """List available file types for filtering.

    Returns a list of file type names and their associated glob patterns.
    These types can be used with the file_type parameter in other tools.

    Returns:
        TypeList with available file types and their globs.
    """
    try:
        args = build_list_types_command()

        result = await run_rg(args)

        types = parse_type_list(result.stdout)

        return TypeList(types=types)

    except RipgrepError as e:
        print(f"List types error: {e}", file=sys.stderr)
        raise
