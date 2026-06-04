#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 12:00:00
# File: src/scitex_msword/_cli/__init__.py
#
# Part of scitex-msword (AGPL-3.0-only). See LICENSE at the repo root.

"""Internal CLI submodule package — split per subcommand group.

Importing ``scitex_msword.cli`` triggers each module here so the
subcommands attach themselves to ``main_group`` at import time.
External callers should not import this package directly.
"""
