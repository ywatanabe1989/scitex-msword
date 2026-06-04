#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: tests/hooks/conftest.py

"""Shared fixtures for the ``sxm.hooks`` test suite.

Each test runs against a fresh dispatcher registry **and** a fresh
lookup cache so prior tests cannot leak state across the file
boundary. A second fixture (:func:`project_tree_with_hook`) builds a
temporary directory tree that mirrors the project-local discovery
contract: ``<root>/.scitex/msword/hooks/foo.py`` that calls
:func:`scitex_msword.hooks.register` at import time.
"""

from __future__ import annotations

import inspect
import os
from pathlib import Path
from typing import Callable, Iterator

import pytest


@pytest.fixture(autouse=True)
def _clean_hooks_state() -> Iterator[None]:
    """Reset the registry and lookup cache around every test."""
    from scitex_msword.hooks import _dispatch, _lookup

    _dispatch._reset()
    _lookup.reset()
    try:
        yield
    finally:
        _dispatch._reset()
        _lookup.reset()


@pytest.fixture
def project_tree_with_hook(tmp_path: Path) -> Callable[[str, str], Path]:
    """Return a factory that creates ``<tmp>/.scitex/msword/hooks/<name>.py``.

    The factory accepts a module ``name`` (without ``.py``) and the
    Python source to write into it, then returns the project root path
    (``tmp_path``) so the caller can pass it to ``lookup(start=...)``
    or ``chdir`` into it.
    """
    hooks_dir = tmp_path / ".scitex" / "msword" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    def _factory(name: str, source: str) -> Path:
        (hooks_dir / f"{name}.py").write_text(inspect.cleandoc(source) + "\n")
        return tmp_path

    return _factory


@pytest.fixture
def chdir_to(monkeypatch: pytest.MonkeyPatch) -> Callable[[Path], None]:
    """Tiny helper to ``chdir`` into a fixture-built tree without leaking state."""

    def _go(path: Path) -> None:
        monkeypatch.chdir(path)

    return _go


# EOF
