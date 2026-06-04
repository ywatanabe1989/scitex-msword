#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 12:00:00
# File: tests/scitex_msword/_cli/test__list_apis.py

"""Wiring tests for scitex_msword._cli._list_apis."""

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


class TestListPythonApisRegistration:
    """The `list-python-apis` subcommand should be attached to the root group."""

    def test_list_python_apis_command_present(self):
        """`list-python-apis` should be a registered subcommand of the root."""
        # Arrange
        group = _build_cli()

        # Act
        names = sorted(group.commands)

        # Assert
        assert "list-python-apis" in names
