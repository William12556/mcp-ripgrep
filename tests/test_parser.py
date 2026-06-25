"""Tests for ripgrep JSON output parsing."""

import base64

from mcp_ripgrep.parser import (
    decode_data,
    parse_count_output,
    parse_file_list,
    parse_search_json,
    parse_type_list,
)


class TestDecodeData:
    """Tests for decode_data function."""

    def test_decode_text_element(self):
        """Test decoding a text element."""
        elem = {"text": "hello world"}
        result = decode_data(elem)
        assert result == "hello world"

    def test_decode_bytes_element(self):
        """Test decoding a base64-encoded bytes element."""
        # Base64 encode "hello world"
        encoded = base64.b64encode(b"hello world").decode("ascii")
        elem = {"bytes": encoded}
        result = decode_data(elem)
        assert result == "hello world"

    def test_decode_bytes_with_non_utf8(self):
        """Test decoding bytes with non-UTF-8 content."""
        # Include invalid UTF-8 byte sequence
        raw_bytes = b"valid \xff invalid"
        encoded = base64.b64encode(raw_bytes).decode("ascii")
        elem = {"bytes": encoded}

        # Should not raise, should use replacement character
        result = decode_data(elem)
        assert "valid" in result
        assert isinstance(result, str)

    def test_decode_empty_element(self):
        """Test decoding element with neither text nor bytes."""
        elem = {}
        result = decode_data(elem)
        assert result == ""

    def test_decode_prefers_text_over_bytes(self):
        """Test that text is preferred when both are present."""
        elem = {"text": "from text", "bytes": base64.b64encode(b"from bytes").decode()}
        result = decode_data(elem)
        assert result == "from text"


class TestParseSearchJson:
    """Tests for parse_search_json function."""

    def test_parse_single_match(self):
        """Test parsing a single match from JSON output."""
        # fmt: off
        json_output = (
            '{"type":"begin","data":{"path":{"text":"/path/to/file.py"}}}\n'
            '{"type":"match","data":{"path":{"text":"/path/to/file.py"},'
            '"lines":{"text":"def test_function():\\n"},"line_number":10,'
            '"submatches":[{"match":{"text":"test"},"start":4,"end":8}]}}\n'
            '{"type":"end","data":{"path":{"text":"/path/to/file.py"},"stats":{}}}\n'
            '{"type":"summary","data":{"stats":{"matches":1}}}'
        )
        # fmt: on

        matches, total = parse_search_json(json_output)

        assert len(matches) == 1
        assert matches[0].path == "/path/to/file.py"
        assert matches[0].line_number == 10
        assert "def test_function" in matches[0].text
        assert matches[0].match_start == 4
        assert matches[0].match_end == 8

    def test_parse_multiple_matches(self):
        """Test parsing multiple matches."""
        json_output = """
{"type":"begin","data":{"path":{"text":"/path/file1.py"}}}
{"type":"match","data":{"path":{"text":"/path/file1.py"},"lines":{"text":"line1\\n"},"line_number":1,"submatches":[{"match":{"text":"line"},"start":0,"end":4}]}}
{"type":"end","data":{"path":{"text":"/path/file1.py"}}}
{"type":"begin","data":{"path":{"text":"/path/file2.py"}}}
{"type":"match","data":{"path":{"text":"/path/file2.py"},"lines":{"text":"line2\\n"},"line_number":5,"submatches":[{"match":{"text":"line"},"start":0,"end":4}]}}
{"type":"end","data":{"path":{"text":"/path/file2.py"}}}
""".strip()

        matches, total = parse_search_json(json_output)

        assert len(matches) == 2
        assert matches[0].path == "/path/file1.py"
        assert matches[1].path == "/path/file2.py"

    def test_parse_no_matches(self):
        """Test parsing empty output (no matches)."""
        json_output = ""

        matches, total = parse_search_json(json_output)

        assert matches == []
        assert total == 0

    def test_parse_with_bytes_data(self):
        """Test parsing match with base64-encoded bytes data."""
        # Base64 encode the path and line content
        path_bytes = base64.b64encode(b"/path/to/file.py").decode()
        line_bytes = base64.b64encode(b"test content\n").decode()

        json_output = f"""
{{"type":"begin","data":{{"path":{{"bytes":"{path_bytes}"}}}}}}
{{"type":"match","data":{{"path":{{"bytes":"{path_bytes}"}},"lines":{{"bytes":"{line_bytes}"}},"line_number":1,"submatches":[]}}}}
""".strip()

        matches, total = parse_search_json(json_output)

        assert len(matches) == 1
        assert matches[0].path == "/path/to/file.py"
        assert "test content" in matches[0].text

    def test_parse_skips_malformed_json(self):
        """Test that malformed JSON lines are skipped."""
        json_output = """
{"type":"begin","data":{"path":{"text":"/path/file.py"}}}
not valid json
{"type":"match","data":{"path":{"text":"/path/file.py"},"lines":{"text":"test\\n"},"line_number":1,"submatches":[]}}
""".strip()

        # Should not raise, should skip the invalid line
        matches, total = parse_search_json(json_output)

        assert len(matches) == 1

    def test_parse_strips_newlines_from_text(self):
        """Test that trailing newlines are stripped from match text."""
        json_output = """
{"type":"match","data":{"path":{"text":"/path"},"lines":{"text":"content\\r\\n"},"line_number":1,"submatches":[]}}
""".strip()

        matches, total = parse_search_json(json_output)

        assert matches[0].text == "content"

    def test_parse_windows_path(self):
        """Test parsing match with Windows path."""
        json_output = """
{"type":"match","data":{"path":{"text":"C:\\\\Users\\\\test\\\\file.py"},"lines":{"text":"content\\n"},"line_number":1,"submatches":[]}}
""".strip()

        matches, total = parse_search_json(json_output)

        assert matches[0].path == "C:\\Users\\test\\file.py"


class TestParseCountOutput:
    """Tests for parse_count_output function."""

    def test_parse_count_single_file(self):
        """Test parsing count output for single file."""
        output = "/path/to/file.py:5"

        files, total = parse_count_output(output)

        assert len(files) == 1
        assert files[0].path == "/path/to/file.py"
        assert files[0].count == 5
        assert total == 5

    def test_parse_count_multiple_files(self):
        """Test parsing count output for multiple files."""
        output = """/path/file1.py:3
/path/file2.py:7
/path/file3.py:2"""

        files, total = parse_count_output(output)

        assert len(files) == 3
        assert total == 12

    def test_parse_count_windows_path(self):
        """Test parsing count with Windows drive-letter path."""
        output = "C:\\Users\\test\\file.py:10"

        files, total = parse_count_output(output)

        assert len(files) == 1
        assert files[0].path == "C:\\Users\\test\\file.py"
        assert files[0].count == 10

    def test_parse_count_empty_output(self):
        """Test parsing empty count output."""
        output = ""

        files, total = parse_count_output(output)

        assert files == []
        assert total == 0

    def test_parse_count_skips_invalid_lines(self):
        """Test that invalid lines are skipped."""
        output = """/path/file1.py:5
invalid line
/path/file2.py:3"""

        files, total = parse_count_output(output)

        assert len(files) == 2
        assert total == 8


class TestParseFileList:
    """Tests for parse_file_list function."""

    def test_parse_file_list(self):
        """Test parsing file list output."""
        output = """/path/file1.py
/path/file2.py
/path/file3.py"""

        files = parse_file_list(output)

        assert len(files) == 3
        assert "/path/file1.py" in files

    def test_parse_file_list_with_windows_paths(self):
        """Test parsing file list with Windows paths."""
        output = """C:\\Users\\test\\file1.py
D:\\projects\\file2.py"""

        files = parse_file_list(output)

        assert len(files) == 2
        assert "C:\\Users\\test\\file1.py" in files

    def test_parse_file_list_empty(self):
        """Test parsing empty file list."""
        output = ""

        files = parse_file_list(output)

        assert files == []

    def test_parse_file_list_with_blank_lines(self):
        """Test that blank lines are skipped."""
        output = """/path/file1.py

/path/file2.py
"""

        files = parse_file_list(output)

        assert len(files) == 2


class TestParseTypeList:
    """Tests for parse_type_list function."""

    def test_parse_type_list(self):
        """Test parsing type list output."""
        output = """py: *.py, *.pyi
rust: *.rs
js: *.js, *.mjs, *.cjs"""

        types = parse_type_list(output)

        assert len(types) == 3

        py_type = next(t for t in types if t.name == "py")
        assert "*.py" in py_type.globs
        assert "*.pyi" in py_type.globs

        rust_type = next(t for t in types if t.name == "rust")
        assert rust_type.globs == ["*.rs"]

    def test_parse_type_list_empty(self):
        """Test parsing empty type list."""
        output = ""

        types = parse_type_list(output)

        assert types == []

    def test_parse_type_list_skips_invalid(self):
        """Test that lines without colon are skipped."""
        output = """py: *.py
invalid line
js: *.js"""

        types = parse_type_list(output)

        assert len(types) == 2
