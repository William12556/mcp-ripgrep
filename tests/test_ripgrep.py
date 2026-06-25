"""Tests for ripgrep command construction and execution."""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_ripgrep.errors import RgNotFoundError, RipgrepExecutionError
from mcp_ripgrep.ripgrep import (
    EXIT_ERROR,
    EXIT_NO_MATCH,
    EXIT_SUCCESS,
    RG_BINARY,
    build_count_command,
    build_list_files_command,
    build_list_types_command,
    build_search_command,
    find_rg_binary,
    run_rg,
)


class TestBuildSearchCommand:
    """Tests for build_search_command function."""

    def test_basic_search_command(self):
        """Test basic search command construction."""
        args = build_search_command(
            pattern="test",
            path="/path/to/search",
            max_results=100,
        )

        assert args[0] == RG_BINARY
        assert "--json" in args
        assert "-m" in args
        assert "100" in args
        # Pattern and path must be last two arguments
        assert args[-2] == "test"
        assert args[-1] == "/path/to/search"

    def test_search_with_windows_path(self):
        """Test search command with Windows drive-letter path."""
        args = build_search_command(
            pattern="pattern",
            path="C:\\Users\\test\\project",
            max_results=200,
        )

        # Path should be passed through unquoted
        assert args[-1] == "C:\\Users\\test\\project"
        # No quotes around the path
        assert '"' not in args[-1]
        assert "'" not in args[-1]

    def test_search_with_posix_path(self):
        """Test search command with POSIX path."""
        args = build_search_command(
            pattern="pattern",
            path="/home/user/project",
            max_results=200,
        )

        assert args[-1] == "/home/user/project"

    def test_search_case_insensitive(self):
        """Test search command with case insensitivity."""
        args = build_search_command(
            pattern="Test",
            path="/path",
            max_results=100,
            case_sensitive=False,
        )

        assert "-i" in args

    def test_search_case_sensitive(self):
        """Test search command is case-sensitive by default."""
        args = build_search_command(
            pattern="Test",
            path="/path",
            max_results=100,
            case_sensitive=True,
        )

        assert "-i" not in args

    def test_search_with_hidden_files(self):
        """Test search command including hidden files."""
        args = build_search_command(
            pattern="test",
            path="/path",
            max_results=100,
            include_hidden=True,
        )

        assert "--hidden" in args

    def test_search_with_file_type(self):
        """Test search command with file type filter."""
        args = build_search_command(
            pattern="def",
            path="/path",
            max_results=100,
            file_type="py",
        )

        assert "--type" in args
        type_idx = args.index("--type")
        assert args[type_idx + 1] == "py"

    def test_search_with_glob(self):
        """Test search command with glob pattern."""
        args = build_search_command(
            pattern="test",
            path="/path",
            max_results=100,
            glob="*.py",
        )

        assert "--glob" in args
        glob_idx = args.index("--glob")
        assert args[glob_idx + 1] == "*.py"

    def test_search_with_context_lines(self):
        """Test search command with context lines."""
        args = build_search_command(
            pattern="test",
            path="/path",
            max_results=100,
            context_lines=3,
        )

        assert "-C" in args
        c_idx = args.index("-C")
        assert args[c_idx + 1] == "3"

    def test_search_no_shell_string(self):
        """Verify search command is a list, not a shell string."""
        args = build_search_command(
            pattern="test pattern",
            path="/path with spaces",
            max_results=100,
        )

        assert isinstance(args, list)
        assert all(isinstance(arg, str) for arg in args)


class TestBuildCountCommand:
    """Tests for build_count_command function."""

    def test_count_matches(self):
        """Test count command with --count-matches."""
        args = build_count_command(
            pattern="test",
            path="/path",
            count_type="matches",
        )

        assert "--count-matches" in args
        assert "--count" not in args

    def test_count_lines(self):
        """Test count command with --count."""
        args = build_count_command(
            pattern="test",
            path="/path",
            count_type="lines",
        )

        assert "--count" in args
        assert "--count-matches" not in args

    def test_count_with_windows_path(self):
        """Test count command with Windows path."""
        args = build_count_command(
            pattern="test",
            path="D:\\projects\\code",
        )

        assert args[-1] == "D:\\projects\\code"


class TestBuildListFilesCommand:
    """Tests for build_list_files_command function."""

    def test_list_files_with_matches(self):
        """Test list files with matches mode."""
        args = build_list_files_command(
            path="/path",
            pattern="test",
            mode="with-matches",
        )

        assert "-l" in args
        assert "--files" not in args
        assert "test" in args

    def test_list_all_files(self):
        """Test list all files mode."""
        args = build_list_files_command(
            path="/path",
            mode="all",
        )

        assert "--files" in args
        assert "-l" not in args

    def test_list_files_no_pattern_defaults_to_all(self):
        """Test that no pattern with with-matches mode uses --files."""
        args = build_list_files_command(
            path="/path",
            pattern=None,
            mode="with-matches",
        )

        # Without a pattern, --files is used regardless of mode
        assert "--files" in args


class TestBuildListTypesCommand:
    """Tests for build_list_types_command function."""

    def test_list_types_command(self):
        """Test type list command."""
        args = build_list_types_command()

        assert args == [RG_BINARY, "--type-list"]


class TestFindRgBinary:
    """Tests for find_rg_binary function."""

    def test_rg_found(self):
        """Test finding rg when it exists."""
        with patch("shutil.which", return_value="/usr/bin/rg"):
            result = find_rg_binary()
            assert result == "/usr/bin/rg"

    def test_rg_not_found(self):
        """Test RgNotFoundError when rg is missing."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(RgNotFoundError) as exc_info:
                find_rg_binary()
            assert "rg" in str(exc_info.value)


class TestRunRg:
    """Tests for run_rg async function."""

    async def test_run_rg_success(self):
        """Test successful rg execution."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"output", b"")
        mock_process.returncode = EXIT_SUCCESS

        with patch("shutil.which", return_value="/usr/bin/rg"):
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_process,
            ):
                result = await run_rg(["rg", "--json", "test", "/path"])

                assert result.stdout == "output"
                assert result.stderr == ""
                assert result.returncode == EXIT_SUCCESS

    async def test_run_rg_no_match(self):
        """Test rg execution with no matches (exit code 1)."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = EXIT_NO_MATCH

        with patch("shutil.which", return_value="/usr/bin/rg"):
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_process,
            ):
                result = await run_rg(["rg", "test", "/path"])

                # Exit code 1 should NOT raise an exception
                assert result.returncode == EXIT_NO_MATCH
                assert result.stdout == ""

    async def test_run_rg_error(self):
        """Test RipgrepExecutionError on exit code 2."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"rg: error message")
        mock_process.returncode = EXIT_ERROR

        with patch("shutil.which", return_value="/usr/bin/rg"):
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_process,
            ):
                with pytest.raises(RipgrepExecutionError) as exc_info:
                    await run_rg(["rg", "test", "/path"])

                assert "error message" in str(exc_info.value)

    async def test_run_rg_not_found(self):
        """Test RgNotFoundError when rg is not on PATH."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(RgNotFoundError):
                await run_rg(["rg", "test", "/path"])

    async def test_run_rg_uses_argument_list(self):
        """Verify run_rg uses create_subprocess_exec, not shell."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        with patch("shutil.which", return_value="/usr/bin/rg"):
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_process,
            ) as mock_exec:
                await run_rg(["rg", "--json", "test", "/path"])

                # Verify create_subprocess_exec was called (not shell)
                mock_exec.assert_called_once()
                # Arguments should be passed as separate items, not a single string
                call_args = mock_exec.call_args
                # First positional args should be the command parts
                assert "/usr/bin/rg" in call_args[0]

    async def test_run_rg_handles_non_utf8(self):
        """Test handling of non-UTF-8 output."""
        mock_process = AsyncMock()
        # Include some invalid UTF-8 bytes
        mock_process.communicate.return_value = (b"valid \xff invalid", b"")
        mock_process.returncode = 0

        with patch("shutil.which", return_value="/usr/bin/rg"):
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_process,
            ):
                result = await run_rg(["rg", "test", "/path"])

                # Should decode with replacement, not crash
                assert "valid" in result.stdout
                # The invalid byte should be replaced, not cause an exception
                assert isinstance(result.stdout, str)
