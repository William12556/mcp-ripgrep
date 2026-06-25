"""Pydantic models for mcp-ripgrep tool inputs and outputs.

These models drive FastMCP schema generation and provide type-safe
data structures for search results.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# Default maximum number of results to return from search operations
DEFAULT_MAX_RESULTS: int = 200


class SearchInput(BaseModel):
    """Input parameters for the search tool."""

    pattern: str = Field(description="Regular expression pattern to search for")
    path: str = Field(description="File or directory path to search in")
    max_results: int = Field(
        default=DEFAULT_MAX_RESULTS,
        ge=1,
        description="Maximum number of matches to return",
    )
    case_sensitive: bool = Field(
        default=True, description="Whether the search is case-sensitive"
    )
    include_hidden: bool = Field(
        default=False, description="Whether to search hidden files and directories"
    )
    file_type: Optional[str] = Field(
        default=None, description="File type to search (e.g., 'py', 'js', 'rust')"
    )
    glob: Optional[str] = Field(
        default=None,
        description="Glob pattern to filter files (e.g., '*.py', 'src/**/*.ts')",
    )
    context_lines: int = Field(
        default=0, ge=0, description="Number of context lines before and after match"
    )


class Match(BaseModel):
    """A single search match."""

    path: str = Field(description="File path where the match was found")
    line_number: int = Field(description="Line number of the match (1-indexed)")
    text: str = Field(description="Text content of the matching line")
    match_start: Optional[int] = Field(
        default=None, description="Start column of the match (0-indexed)"
    )
    match_end: Optional[int] = Field(
        default=None, description="End column of the match (0-indexed)"
    )


class SearchResult(BaseModel):
    """Result of a search operation."""

    matches: List[Match] = Field(default_factory=list, description="List of matches")
    total_matches: int = Field(description="Total number of matches found")
    truncated: bool = Field(
        default=False, description="Whether results were truncated due to max_results"
    )


class CountInput(BaseModel):
    """Input parameters for the count-matches tool."""

    pattern: str = Field(description="Regular expression pattern to count")
    path: str = Field(description="File or directory path to search in")
    count_type: Literal["matches", "lines"] = Field(
        default="matches",
        description=(
            "'matches' counts total pattern occurrences (--count-matches); "
            "'lines' counts lines with at least one match (--count)"
        ),
    )
    case_sensitive: bool = Field(
        default=True, description="Whether the search is case-sensitive"
    )
    include_hidden: bool = Field(
        default=False, description="Whether to search hidden files and directories"
    )
    file_type: Optional[str] = Field(
        default=None, description="File type to search (e.g., 'py', 'js', 'rust')"
    )
    glob: Optional[str] = Field(
        default=None, description="Glob pattern to filter files"
    )


class FileCount(BaseModel):
    """Count result for a single file."""

    path: str = Field(description="File path")
    count: int = Field(description="Number of matches or lines with matches")


class CountResult(BaseModel):
    """Result of a count-matches operation."""

    files: List[FileCount] = Field(default_factory=list, description="Per-file counts")
    total: int = Field(description="Total count across all files")


class ListFilesInput(BaseModel):
    """Input parameters for the list-files tool."""

    path: str = Field(description="Directory path to list files from")
    pattern: Optional[str] = Field(
        default=None,
        description=(
            "Pattern to search for. When provided, lists files with matches (-l). "
            "When omitted with mode='all', lists all files (--files)."
        ),
    )
    mode: Literal["with-matches", "all"] = Field(
        default="with-matches",
        description=(
            "'with-matches' lists only files containing pattern matches (-l); "
            "'all' lists all files ripgrep would search (--files)"
        ),
    )
    include_hidden: bool = Field(
        default=False, description="Whether to include hidden files and directories"
    )
    file_type: Optional[str] = Field(
        default=None, description="File type to filter (e.g., 'py', 'js', 'rust')"
    )
    glob: Optional[str] = Field(
        default=None, description="Glob pattern to filter files"
    )


class FileList(BaseModel):
    """Result of a list-files operation."""

    files: List[str] = Field(default_factory=list, description="List of file paths")
    total: int = Field(description="Total number of files")


class FileType(BaseModel):
    """A ripgrep file type and its associated glob patterns."""

    name: str = Field(description="File type name (e.g., 'py', 'rust')")
    globs: List[str] = Field(
        description="Glob patterns associated with this type (e.g., ['*.py', '*.pyi'])"
    )


class TypeList(BaseModel):
    """Result of list-file-types operation."""

    types: List[FileType] = Field(
        default_factory=list, description="List of available file types"
    )
