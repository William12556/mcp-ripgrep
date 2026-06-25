"""Tests for the MCP server and tools."""

import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from mcp_ripgrep.errors import RgNotFoundError, RipgrepExecutionError, SearchPathError
from mcp_ripgrep.ripgrep import RgResult
from mcp_ripgrep.server import (
    count_matches,
    list_file_types,
    list_files,
    search,
    validate_path,
)


class TestValidatePath:
    """Tests for path validation."""

    def test_valid_path(self):
        """Test validation passes for existing path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Should not raise
            validate_path(tmpdir)

    def test_invalid_path(self):
        """Test validation fails for non-existent path."""
        with pytest.raises(SearchPathError) as exc_info:
            validate_path("/nonexistent/path/that/does/not/exist")

        assert "nonexistent" in str(exc_info.value)


class TestSearchTool:
    """Tests for the search tool."""

    async def test_search_returns_matches(self):
        """Test search returns parsed matches."""
        # fmt: off
        json_output = (
            '{"type":"begin","data":{"path":{"text":"/test/file.py"}}}\n'
            '{"type":"match","data":{"path":{"text":"/test/file.py"},'
            '"lines":{"text":"def test():\\n"},"line_number":1,'
            '"submatches":[{"match":{"text":"test"},"start":4,"end":8}]}}\n'
            '{"type":"end","data":{"path":{"text":"/test/file.py"}}}'
        )
        # fmt: on

        mock_result = RgResult(stdout=json_output, stderr="", returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mcp_ripgrep.server.run_rg", new_callable=AsyncMock) as mock_run:
                mock_run.return_value = mock_result

                result = await search(pattern="test", path=tmpdir)

                assert len(result.matches) == 1
                assert result.matches[0].path == "/test/file.py"
                assert result.matches[0].line_number == 1

    async def test_search_no_matches(self):
        """Test search with no matches returns empty result."""
        mock_result = RgResult(stdout="", stderr="", returncode=1)

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mcp_ripgrep.server.run_rg", new_callable=AsyncMock) as mock_run:
                mock_run.return_value = mock_result

                result = await search(pattern="nonexistent", path=tmpdir)

                assert result.matches == []
                assert result.total_matches == 0

    async def test_search_invalid_path_raises(self):
        """Test search with invalid path raises SearchPathError."""
        with pytest.raises(SearchPathError):
            await search(pattern="test", path="/nonexistent/path")

    async def test_search_rg_not_found_raises(self):
        """Test search raises when rg is not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mcp_ripgrep.server.run_rg", new_callable=AsyncMock) as mock_run:
                mock_run.side_effect = RgNotFoundError()

                with pytest.raises(RgNotFoundError):
                    await search(pattern="test", path=tmpdir)

    async def test_search_truncation_flag(self):
        """Test truncated flag is set when max results reached."""
        # Generate enough matches to hit the max
        matches_json = "\n".join(
            [
                (
                    f'{{"type":"match","data":{{"path":{{"text":"/file.py"}},'
                    f'"lines":{{"text":"line{i}\\n"}},"line_number":{i},'
                    f'"submatches":[]}}}}'
                )
                for i in range(10)
            ]
        )
        mock_result = RgResult(stdout=matches_json, stderr="", returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mcp_ripgrep.server.run_rg", new_callable=AsyncMock) as mock_run:
                mock_run.return_value = mock_result

                result = await search(pattern="test", path=tmpdir, max_results=10)

                assert result.truncated is True


class TestCountMatchesTool:
    """Tests for the count-matches tool."""

    async def test_count_matches_returns_counts(self):
        """Test count-matches returns per-file counts and total."""
        count_output = "/path/file1.py:5\n/path/file2.py:3"
        mock_result = RgResult(stdout=count_output, stderr="", returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mcp_ripgrep.server.run_rg", new_callable=AsyncMock) as mock_run:
                mock_run.return_value = mock_result

                result = await count_matches(pattern="test", path=tmpdir)

                assert len(result.files) == 2
                assert result.total == 8

    async def test_count_matches_no_matches(self):
        """Test count-matches with no matches."""
        mock_result = RgResult(stdout="", stderr="", returncode=1)

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mcp_ripgrep.server.run_rg", new_callable=AsyncMock) as mock_run:
                mock_run.return_value = mock_result

                result = await count_matches(pattern="nonexistent", path=tmpdir)

                assert result.files == []
                assert result.total == 0

    async def test_count_matches_invalid_path_raises(self):
        """Test count-matches with invalid path raises."""
        with pytest.raises(SearchPathError):
            await count_matches(pattern="test", path="/nonexistent/path")


class TestListFilesTool:
    """Tests for the list-files tool."""

    async def test_list_files_returns_files(self):
        """Test list-files returns file paths."""
        file_output = "/path/file1.py\n/path/file2.py"
        mock_result = RgResult(stdout=file_output, stderr="", returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mcp_ripgrep.server.run_rg", new_callable=AsyncMock) as mock_run:
                mock_run.return_value = mock_result

                result = await list_files(path=tmpdir)

                assert len(result.files) == 2
                assert result.total == 2

    async def test_list_files_no_files(self):
        """Test list-files with no matching files."""
        mock_result = RgResult(stdout="", stderr="", returncode=1)

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mcp_ripgrep.server.run_rg", new_callable=AsyncMock) as mock_run:
                mock_run.return_value = mock_result

                result = await list_files(path=tmpdir, pattern="nonexistent")

                assert result.files == []
                assert result.total == 0

    async def test_list_files_invalid_path_raises(self):
        """Test list-files with invalid path raises."""
        with pytest.raises(SearchPathError):
            await list_files(path="/nonexistent/path")


class TestListFileTypesTool:
    """Tests for the list-file-types tool."""

    async def test_list_file_types_returns_types(self):
        """Test list-file-types returns type definitions."""
        types_output = "py: *.py, *.pyi\nrust: *.rs"
        mock_result = RgResult(stdout=types_output, stderr="", returncode=0)

        with patch("mcp_ripgrep.server.run_rg", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result

            result = await list_file_types()

            assert len(result.types) == 2

            py_type = next(t for t in result.types if t.name == "py")
            assert "*.py" in py_type.globs

    async def test_list_file_types_rg_not_found(self):
        """Test list-file-types raises when rg not found."""
        with patch("mcp_ripgrep.server.run_rg", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = RgNotFoundError()

            with pytest.raises(RgNotFoundError):
                await list_file_types()


class TestErrorHandling:
    """Tests for error handling across tools."""

    async def test_ripgrep_execution_error_propagates(self):
        """Test that RipgrepExecutionError propagates from tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mcp_ripgrep.server.run_rg", new_callable=AsyncMock) as mock_run:
                mock_run.side_effect = RipgrepExecutionError("invalid regex", 2)

                with pytest.raises(RipgrepExecutionError):
                    await search(pattern="[invalid", path=tmpdir)
