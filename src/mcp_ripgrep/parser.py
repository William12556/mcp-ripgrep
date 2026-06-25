"""Parser for ripgrep JSON output.

Handles the JSON Lines format from rg --json, decoding data elements
that may be UTF-8 text or base64-encoded bytes.
"""

import base64
import json
import sys
from typing import Any, Dict, List, Optional, Tuple

from .models import FileCount, FileType, Match


def decode_data(elem: Dict[str, Any]) -> str:
    """Decode a ripgrep data element.

    Ripgrep JSON output represents text content in data elements that
    contain either a 'text' key (UTF-8 string) or a 'bytes' key
    (base64-encoded bytes for non-UTF-8 content).

    Args:
        elem: Dictionary with either 'text' or 'bytes' key.

    Returns:
        Decoded string content.
    """
    if "text" in elem:
        return str(elem["text"])

    if "bytes" in elem:
        # Base64-decode and decode as UTF-8 with replacement for invalid chars
        raw_bytes = base64.b64decode(str(elem["bytes"]))
        return raw_bytes.decode("utf-8", errors="replace")

    # Fallback for unexpected format
    return ""


def parse_search_json(stdout: str) -> Tuple[List[Match], int]:
    """Parse ripgrep JSON output into Match objects.

    Args:
        stdout: Raw stdout from rg --json.

    Returns:
        Tuple of (list of Match objects, total match count).
    """
    matches: List[Match] = []
    current_path: Optional[str] = None
    total_count = 0

    for line in stdout.splitlines():
        if not line.strip():
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            # Skip malformed JSON lines without crashing
            print("Warning: skipping malformed JSON line", file=sys.stderr)
            continue

        msg_type = record.get("type")

        if msg_type == "begin":
            # Begin message contains the file path
            path_data = record.get("data", {}).get("path", {})
            current_path = decode_data(path_data)

        elif msg_type == "match":
            data = record.get("data", {})

            # Extract path (may be in match data or from begin message)
            path_data = data.get("path", {})
            path = decode_data(path_data) if path_data else current_path or ""

            # Extract line number
            line_number = data.get("line_number", 0)

            # Extract line text
            lines_data = data.get("lines", {})
            text = decode_data(lines_data).rstrip("\n\r")

            # Extract submatch positions if available
            match_start: Optional[int] = None
            match_end: Optional[int] = None
            submatches = data.get("submatches", [])
            if submatches:
                first_match = submatches[0]
                match_start = first_match.get("start")
                match_end = first_match.get("end")

            match = Match(
                path=path,
                line_number=line_number,
                text=text,
                match_start=match_start,
                match_end=match_end,
            )
            matches.append(match)
            total_count += len(submatches) if submatches else 1

        elif msg_type == "summary":
            # Summary contains stats; we could extract total from here
            # but we're already counting matches
            pass

    return matches, total_count


def parse_count_output(stdout: str) -> Tuple[List[FileCount], int]:
    """Parse ripgrep count output into FileCount objects.

    Count output format: path:count (one per line)

    Args:
        stdout: Raw stdout from rg --count or rg --count-matches.

    Returns:
        Tuple of (list of FileCount objects, total count).
    """
    files: List[FileCount] = []
    total = 0

    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue

        # Format is path:count
        # Handle Windows paths with drive letters (C:\path:count)
        # Find the last colon that precedes a number
        last_colon = line.rfind(":")
        if last_colon == -1:
            continue

        path = line[:last_colon]
        count_str = line[last_colon + 1 :]

        try:
            count = int(count_str)
        except ValueError:
            continue

        files.append(FileCount(path=path, count=count))
        total += count

    return files, total


def parse_file_list(stdout: str) -> List[str]:
    """Parse ripgrep file list output.

    Args:
        stdout: Raw stdout from rg -l or rg --files.

    Returns:
        List of file paths.
    """
    files: List[str] = []

    for line in stdout.splitlines():
        line = line.strip()
        if line:
            files.append(line)

    return files


def parse_type_list(stdout: str) -> List[FileType]:
    """Parse ripgrep type list output.

    Type list format: typename: glob1, glob2, ...

    Args:
        stdout: Raw stdout from rg --type-list.

    Returns:
        List of FileType objects.
    """
    types: List[FileType] = []

    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue

        # Format is "typename: glob1, glob2, ..."
        if ": " not in line:
            continue

        name, globs_str = line.split(": ", 1)
        globs = [g.strip() for g in globs_str.split(",")]

        types.append(FileType(name=name, globs=globs))

    return types
