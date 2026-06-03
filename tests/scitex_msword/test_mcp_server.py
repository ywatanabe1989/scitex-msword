#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-02 00:00:00
# File: tests/scitex_msword/test_mcp_server.py

"""Smoke tests for the MCP server scaffold."""

import pytest


class TestMcpServerScaffoldImport:
    """The scaffold should always be importable even without the mcp dep."""

    def test_module_exposes_server_name_attribute(self):
        """scitex_msword.mcp_server should expose SERVER_NAME."""
        # Arrange
        import importlib

        # Act
        mod = importlib.import_module("scitex_msword.mcp_server")
        # Assert
        assert hasattr(mod, "SERVER_NAME")

    def test_server_name_is_scitex_msword(self):
        """SERVER_NAME constant should be 'scitex-msword'."""
        # Arrange
        import importlib

        # Act
        value = importlib.import_module("scitex_msword.mcp_server").SERVER_NAME
        # Assert
        assert value == "scitex-msword"

    def test_mcp_available_is_boolean(self):
        """MCP_AVAILABLE should be a boolean flag."""
        # Arrange
        import importlib

        # Act
        flag = importlib.import_module("scitex_msword.mcp_server").MCP_AVAILABLE
        # Assert
        assert isinstance(flag, bool)


_MCP_INSTALLED: bool
try:
    import mcp  # noqa: F401  # pragma: no cover

    _MCP_INSTALLED = True
except ImportError:
    _MCP_INSTALLED = False


@pytest.mark.skipif(
    _MCP_INSTALLED, reason="mcp is installed; cannot exercise the no-mcp branch"
)
class TestMcpServeRequiresMcp:
    """serve() should raise a helpful ImportError when 'mcp' is missing."""

    def test_serve_raises_import_error_without_mcp(self):
        """If mcp is not installed, serve() should raise ImportError."""
        # Arrange
        from scitex_msword.mcp_server import serve

        ctx = pytest.raises(ImportError)
        # Act
        # Assert
        with ctx:
            serve()


@pytest.mark.skipif(not _MCP_INSTALLED, reason="mcp not installed")
class TestBuildServer:
    """build_server() smoke (only runs when mcp is installed)."""

    def test_build_server_returns_non_none_when_mcp_installed(self):
        """When mcp is installed, build_server() should return a server obj."""
        # Arrange
        from scitex_msword.mcp_server import build_server

        # Act
        server = build_server()
        # Assert
        assert server is not None


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__)])
