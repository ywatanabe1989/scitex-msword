#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: src/scitex_msword/hooks/_builtins.py

"""Engine-shipped builtin hooks.

H1 (this PR) intentionally ships **zero** builtins so the framework
can land and be reviewed in isolation. H4 will add ``SXM-TC001``
(track-changes audit), H5 will add ``SXM-JP001`` (Japanese typography),
and ``SXM-FS001`` (front-matter / structure) is also queued for the
follow-up sprint.

The dict shape matches what :mod:`scitex_msword.hooks._lookup` expects:
``{hook_id: Hook}``.
"""

from __future__ import annotations

from typing import Dict

from ._base import Hook

ALL_HOOKS: Dict[str, Hook] = {}

__all__ = ["ALL_HOOKS"]


# EOF
