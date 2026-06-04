#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 12:00:00
# File: tests/scitex_msword/_cli/test__skills.py

"""Wiring tests for scitex_msword._cli._skills."""

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


class TestSkillsGroupRegistration:
    """The `skills` noun group + its verbs should be attached to the root."""

    def test_skills_command_group_present(self):
        """`skills` (group) should be a registered subcommand of the root."""
        # Arrange
        group = _build_cli()

        # Act
        names = sorted(group.commands)

        # Assert
        assert "skills" in names

    def test_skills_group_has_list_get_install(self):
        """`skills` group should expose {list, get, install} (audit §1a)."""
        # Arrange
        group = _build_cli()
        skills_group = group.commands["skills"]

        # Act
        names = set(skills_group.commands)

        # Assert
        assert {"list", "get", "install"}.issubset(names)

    def test_main_skills_list_returns_zero(self):
        """`scitex-msword skills list --json` should exit cleanly with code 0."""
        # Arrange
        from scitex_msword.cli import main

        # Act
        rc = main(["skills", "list", "--json"])

        # Assert
        assert rc == 0
