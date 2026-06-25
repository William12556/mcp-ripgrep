"""Exception hierarchy for mcp-ripgrep.

All exceptions inherit from RipgrepError, enabling callers to catch
the base class for any ripgrep-related failure.
"""


class RipgrepError(Exception):
    """Base exception for all ripgrep-related errors."""

    pass


class RgNotFoundError(RipgrepError):
    """Raised when the rg binary is not found on PATH."""

    def __init__(self, message: str = "ripgrep (rg) binary not found on PATH") -> None:
        super().__init__(message)


class SearchPathError(RipgrepError):
    """Raised when the search path does not exist or is inaccessible."""

    def __init__(self, path: str) -> None:
        super().__init__(f"Search path does not exist or is inaccessible: {path}")
        self.path = path


class RipgrepExecutionError(RipgrepError):
    """Raised when rg exits with an error (exit code 2)."""

    def __init__(self, stderr: str, returncode: int = 2) -> None:
        message = f"ripgrep execution failed (exit {returncode}): {stderr}"
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode
