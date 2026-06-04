#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 12:00:00
# File: tests/scitex_msword/_cli/test__mcp.py

"""Wiring tests for scitex_msword._cli._mcp."""

import pytest


pytestmark = pytest.mark.skipif(
    not pytest.importorskip("click", reason="click not installed"),
    reason="click not installed",
)


def _build_cli():
    """Import the root Click group fresh so wiring is exercised on every call."""
    import importlib

    cli_mod = importlib.import_module("scitex_msword.cli")
    return cli_mod.main_group


class TestMcpGroupRegistration:
    """The `mcp` noun group + its verbs should be attached to the root."""

    def test_mcp_command_group_present(self):
        """`mcp` (group) should be a registered subcommand of the root."""
        # Arrange
        group = _build_cli()

        # Act
        names = sorted(group.commands)

        # Assert
        assert "mcp" in names

    def test_mcp_group_has_list_tools(self):
        """`mcp list-tools` is required by audit §1a."""
        # Arrange
        group = _build_cli()
        mcp_group = group.commands["mcp"]

        # Act
        names = sorted(mcp_group.commands)

        # Assert
        assert "list-tools" in names

    def test_mcp_group_has_start(self):
        """`mcp start` exposes the stdio MCP server."""
        # Arrange
        group = _build_cli()
        mcp_group = group.commands["mcp"]

        # Act
        names = sorted(mcp_group.commands)

        # Assert
        assert "start" in names
