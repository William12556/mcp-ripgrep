"""Entry point for running mcp-ripgrep as a module.

Usage: python -m mcp_ripgrep
"""

from .server import mcp


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
