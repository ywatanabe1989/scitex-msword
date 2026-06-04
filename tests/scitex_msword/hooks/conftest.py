#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: tests/scitex_msword/hooks/conftest.py

"""Shared fixtures for the ``sxm.hooks`` test suite.

Each test runs against a fresh dispatcher registry, a fresh lookup cache,
a clean ``_builtins.ALL_HOOKS`` snapshot, the original
``_lookup._iter_entry_points``, and its original CWD. State that tests
mutate is snapshotted on entry and restored on exit — no ``monkeypatch``
needed (PA-306 §3 forbids it).

A second fixture (:func:`project_tree_with_hook`) builds a temporary
directory tree that mirrors the project-local discovery contract:
``<root>/.scitex/msword/hooks/foo.py`` that calls
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
    """Snapshot all mutable hook-system state on entry; restore on exit.

    Restores: registry (``_dispatch._REGISTRY``), lookup cache,
    ``_builtins.ALL_HOOKS`` contents, ``_lookup._iter_entry_points``
    attribute, and CWD.
    """
    from scitex_msword.hooks import _builtins, _dispatch, _lookup

    builtins_snapshot = dict(_builtins.ALL_HOOKS)
    iter_eps_original = _lookup._iter_entry_points
    cwd_original = os.getcwd()

    _dispatch._reset()
    _lookup.reset()
    try:
        yield
    finally:
        _builtins.ALL_HOOKS.clear()
        _builtins.ALL_HOOKS.update(builtins_snapshot)
        _lookup._iter_entry_points = iter_eps_original
        try:
            os.chdir(cwd_original)
        except OSError:
            # Original cwd may have been a tmp dir that got cleaned up.
            os.chdir(str(Path.home()))
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
def chdir_to() -> Callable[[Path], None]:
    """Plain ``os.chdir`` helper. CWD is restored by ``_clean_hooks_state``."""

    def _go(path: Path) -> None:
        os.chdir(str(path))

    return _go


# EOF
