#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 12:00:00
# File: tests/scitex_msword/test_cli.py

"""Smoke tests for the scitex_msword.cli orchestrator (root group + main())."""

import pytest


pytestmark = pytest.mark.skipif(
    not pytest.importorskip("click", reason="click not installed"),
    reason="click not installed",
)


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
