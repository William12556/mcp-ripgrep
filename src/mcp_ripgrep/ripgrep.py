"""Command construction and subprocess execution for ripgrep.

CRITICAL: All rg invocations use asyncio.create_subprocess_exec with an
argument list. Never use shell=True or construct shell command strings.
This is required for cross-platform correctness: Windows fails with
os error 123 when paths are quoted in shell strings.
"""

import asyncio
import shutil
from dataclasses import dataclass
from typing import List, Optional

from .errors import RgNotFoundError, RipgrepExecutionError

# Ripgrep binary name
RG_BINARY: str = "rg"

# Exit codes from ripgrep
EXIT_SUCCESS: int = 0
EXIT_NO_MATCH: int = 1
EXIT_ERROR: int = 2


@dataclass
class RgResult:
    """Result of a ripgrep subprocess execution."""

    stdout: str
    stderr: str
    returncode: int


def build_search_command(
    pattern: str,
    path: str,
    max_results: int,
    case_sensitive: bool = True,
    include_hidden: bool = False,
    file_type: Optional[str] = None,
    glob: Optional[str] = None,
    context_lines: int = 0,
) -> List[str]:
    """Build argument list for rg search with JSON output.

    Args:
        pattern: Regular expression pattern to search for.
        path: File or directory path to search in.
        max_results: Maximum number of matches to return.
        case_sensitive: Whether the search is case-sensitive.
        include_hidden: Whether to search hidden files.
        file_type: Optional file type filter (e.g., 'py', 'js').
        glob: Optional glob pattern filter.
        context_lines: Number of context lines before/after match.

    Returns:
        Argument list for subprocess execution. Ends with [pattern, path].
    """
    args: List[str] = [RG_BINARY, "--json"]

    # Limit results
    args.extend(["-m", str(max_results)])

    # Case sensitivity
    if not case_sensitive:
        args.append("-i")

    # Hidden files
    if include_hidden:
        args.append("--hidden")

    # File type filter
    if file_type:
        args.extend(["--type", file_type])

    # Glob filter
    if glob:
        args.extend(["--glob", glob])

    # Context lines
    if context_lines > 0:
        args.extend(["-C", str(context_lines)])

    # Pattern and path must come last, unquoted
    args.append(pattern)
    args.append(path)

    return args


def build_count_command(
    pattern: str,
    path: str,
    count_type: str = "matches",
    case_sensitive: bool = True,
    include_hidden: bool = False,
    file_type: Optional[str] = None,
    glob: Optional[str] = None,
) -> List[str]:
    """Build argument list for rg count operation.

    Args:
        pattern: Regular expression pattern to count.
        path: File or directory path to search in.
        count_type: 'matches' for --count-matches, 'lines' for --count.
        case_sensitive: Whether the search is case-sensitive.
        include_hidden: Whether to search hidden files.
        file_type: Optional file type filter.
        glob: Optional glob pattern filter.

    Returns:
        Argument list for subprocess execution.
    """
    args: List[str] = [RG_BINARY]

    # Count type
    if count_type == "matches":
        args.append("--count-matches")
    else:
        args.append("--count")

    # Case sensitivity
    if not case_sensitive:
        args.append("-i")

    # Hidden files
    if include_hidden:
        args.append("--hidden")

    # File type filter
    if file_type:
        args.extend(["--type", file_type])

    # Glob filter
    if glob:
        args.extend(["--glob", glob])

    # Pattern and path must come last
    args.append(pattern)
    args.append(path)

    return args


def build_list_files_command(
    path: str,
    pattern: Optional[str] = None,
    mode: str = "with-matches",
    include_hidden: bool = False,
    file_type: Optional[str] = None,
    glob: Optional[str] = None,
) -> List[str]:
    """Build argument list for listing files.

    Args:
        path: Directory path to list files from.
        pattern: Optional pattern to search for.
        mode: 'with-matches' for -l, 'all' for --files.
        include_hidden: Whether to include hidden files.
        file_type: Optional file type filter.
        glob: Optional glob pattern filter.

    Returns:
        Argument list for subprocess execution.
    """
    args: List[str] = [RG_BINARY]

    # Mode determines the operation
    if mode == "all" or pattern is None:
        # List all files that would be searched
        args.append("--files")
    else:
        # List files with matches
        args.append("-l")

    # Hidden files
    if include_hidden:
        args.append("--hidden")

    # File type filter
    if file_type:
        args.extend(["--type", file_type])

    # Glob filter
    if glob:
        args.extend(["--glob", glob])

    # Pattern (only for -l mode)
    if pattern and mode == "with-matches":
        args.append(pattern)

    # Path comes last
    args.append(path)

    return args


def build_list_types_command() -> List[str]:
    """Build argument list for listing file types.

    Returns:
        Argument list for --type-list.
    """
    return [RG_BINARY, "--type-list"]


def find_rg_binary() -> str:
    """Find the ripgrep binary on PATH.

    Returns:
        Full path to the rg binary.

    Raises:
        RgNotFoundError: If rg is not found on PATH.
    """
    rg_path = shutil.which(RG_BINARY)
    if rg_path is None:
        raise RgNotFoundError()
    return rg_path


async def run_rg(args: List[str]) -> RgResult:
    """Execute ripgrep with the given arguments.

    CRITICAL: Uses asyncio.create_subprocess_exec with an argument list.
    Never uses shell=True. Paths and patterns are passed directly without
    quoting - this is required for Windows compatibility.

    Args:
        args: Argument list starting with the rg command.

    Returns:
        RgResult containing stdout, stderr, and return code.

    Raises:
        RgNotFoundError: If the rg binary is not found.
        RipgrepExecutionError: If rg exits with error code 2.
    """
    # Verify rg exists before attempting to run
    rg_path = find_rg_binary()

    # Replace the first argument (rg) with the full path
    exec_args = [rg_path] + args[1:]

    # Execute subprocess - NEVER use shell=True
    process = await asyncio.create_subprocess_exec(
        *exec_args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout_bytes, stderr_bytes = await process.communicate()

    # Decode output, handling potential encoding issues
    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")
    returncode = process.returncode if process.returncode is not None else 1

    # Map exit codes
    if returncode == EXIT_ERROR:
        raise RipgrepExecutionError(stderr, returncode)

    # EXIT_NO_MATCH (1) is not an error - it means no matches found
    # EXIT_SUCCESS (0) means matches were found
    return RgResult(stdout=stdout, stderr=stderr, returncode=returncode)
