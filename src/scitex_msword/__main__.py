#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 12:00:00
# File: src/scitex_msword/__main__.py
#
# Part of scitex-msword (AGPL-3.0-only). See LICENSE at the repo root.

"""Allow ``python -m scitex_msword`` to invoke the CLI."""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
