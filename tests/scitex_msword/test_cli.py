#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 12:00:00
# File: tests/scitex_msword/_cli/test_cli_smoke.py

"""Smoke tests for scitex_msword._cli subcommand wiring."""

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


# ---------------------------------------------------------------------------
# Top-level command surface
# ---------------------------------------------------------------------------


class TestTopLevelCommands:
    """The canonical §1a leaves should be wired onto the root group."""

    def test_insert_table_command_present(self):
        """`insert-table` should be a registered subcommand of the root."""
        # Arrange
        group = _build_cli()

        # Act
        names = sorted(group.commands)

        # Assert
        assert "insert-table" in names

    def test_list_python_apis_command_present(self):
        """`list-python-apis` should be a registered subcommand of the root."""
        # Arrange
        group = _build_cli()

        # Act
        names = sorted(group.commands)

        # Assert
        assert "list-python-apis" in names

    def test_mcp_command_group_present(self):
        """`mcp` (group) should be a registered subcommand of the root."""
        # Arrange
        group = _build_cli()

        # Act
        names = sorted(group.commands)

        # Assert
        assert "mcp" in names

    def test_skills_command_group_present(self):
        """`skills` (group) should be a registered subcommand of the root."""
        # Arrange
        group = _build_cli()

        # Act
        names = sorted(group.commands)

        # Assert
        assert "skills" in names


# ---------------------------------------------------------------------------
# Subcommand wiring inside groups
# ---------------------------------------------------------------------------


class TestSubcommandWiring:
    """Inner commands inside the mcp / skills noun groups should be wired."""

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

    def test_skills_group_has_list_get_install(self):
        """`skills` group should expose {list, get, install} (audit §1a)."""
        # Arrange
        group = _build_cli()
        skills_group = group.commands["skills"]

        # Act
        names = set(skills_group.commands)

        # Assert
        assert {"list", "get", "install"}.issubset(names)


# ---------------------------------------------------------------------------
# Main entry point behaviour
# ---------------------------------------------------------------------------


class TestMainEntryPoint:
    """`cli.main(argv)` should return integer exit codes without raising."""

    def test_main_help_returns_zero(self):
        """`scitex-msword --help` should exit with code 0."""
        # Arrange
        from scitex_msword.cli import main

        # Act
        rc = main(["--help"])

        # Assert
        assert rc == 0

    def test_main_version_returns_zero(self):
        """`scitex-msword --version` should exit with code 0."""
        # Arrange
        from scitex_msword.cli import main

        # Act
        rc = main(["--version"])

        # Assert
        assert rc == 0

    def test_main_skills_list_returns_zero(self):
        """`scitex-msword skills list` should exit cleanly with code 0."""
        # Arrange
        from scitex_msword.cli import main

        # Act
        rc = main(["skills", "list", "--json"])

        # Assert
        assert rc == 0
