#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: src/scitex_msword/hooks/_lookup.py

"""Unified three-tier hook lookup.

:func:`lookup` returns the most authoritative :class:`Hook` registered
for a given id, merging three sources in this precedence order:

1. **Project-local** — Python modules under
   ``<root>/.scitex/msword/hooks/*.py`` where ``<root>`` is the first
   ancestor of ``cwd`` that contains a ``.scitex/msword`` directory.
   These modules are imported once at discovery time; the convention
   is that each module calls :func:`scitex_msword.hooks.register` at
   module top-level.
2. **Entry points** — distributions that advertise the
   ``scitex_msword.hooks`` group via ``pyproject.toml``. Each entry
   point may resolve to either a single :class:`Hook` or a
   ``dict[str, Hook]`` / iterable of :class:`Hook`.
3. **Engine builtins** — :data:`scitex_msword.hooks._builtins.ALL_HOOKS`.

On id collision, **project-local wins over entry-points wins over
builtins**, mirroring how :mod:`scitex_dev.linter._rules._lookup`
resolves rule overrides.

The merged dict is cached after the first call; tests and other
runtime callers can drop the cache via :func:`reset`.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Dict, Iterable, Optional

from ._base import Hook

_logger = logging.getLogger(__name__)
_cache: Optional[Dict[str, Hook]] = None
_PROJECT_LOCAL_DIR_PARTS = (".scitex", "msword", "hooks")


# ---------------------------------------------------------------------
# Entry-point loader
# ---------------------------------------------------------------------


def _iter_entry_points(group: str) -> Iterable:
    """Yield entry points for *group*, compatible with Python 3.10+."""
    from importlib.metadata import entry_points

    if sys.version_info >= (3, 10):
        return entry_points(group=group)
    eps = entry_points()
    return eps.get(group, [])  # pragma: no cover - 3.10+ required by pyproject


def _load_entry_point_hooks() -> Dict[str, Hook]:
    """Collect hooks advertised under the ``scitex_msword.hooks`` group.

    Each entry point may resolve to:

    * a single :class:`Hook`,
    * an iterable of :class:`Hook`,
    * or a ``dict[str, Hook]`` keyed by hook id.

    Anything else is logged and skipped — entry-point misbehaviour
    must never crash the host application.
    """
    merged: Dict[str, Hook] = {}
    for ep in _iter_entry_points("scitex_msword.hooks"):
        try:
            obj = ep.load()
        except Exception:  # pragma: no cover - defensive
            _logger.debug("Failed to load hook entry point %s", ep.name, exc_info=True)
            continue
        for hook in _coerce_to_hooks(obj):
            merged[hook.id] = hook
    return merged


def _coerce_to_hooks(obj: object) -> Iterable[Hook]:
    """Normalise an entry-point payload into an iterable of :class:`Hook`."""
    if isinstance(obj, Hook):
        return [obj]
    if isinstance(obj, dict):
        return [h for h in obj.values() if isinstance(h, Hook)]
    if isinstance(obj, (list, tuple, set)):
        return [h for h in obj if isinstance(h, Hook)]
    _logger.debug("Entry-point payload %r is not a Hook/dict/iterable", obj)
    return []


# ---------------------------------------------------------------------
# Project-local discovery
# ---------------------------------------------------------------------


def _find_project_hooks_dir(start: Optional[Path] = None) -> Optional[Path]:
    """Walk upward from *start* looking for ``.scitex/msword/hooks``.

    Returns the directory if found, else ``None``. ``start`` defaults
    to the current working directory.
    """
    cursor = Path(start) if start is not None else Path.cwd()
    cursor = cursor.resolve()
    for candidate in (cursor, *cursor.parents):
        hooks_dir = candidate.joinpath(*_PROJECT_LOCAL_DIR_PARTS)
        if hooks_dir.is_dir():
            return hooks_dir
    return None


def _load_project_local_hooks(start: Optional[Path] = None) -> Dict[str, Hook]:
    """Import every ``*.py`` under the discovered project-local hooks dir.

    Each module is loaded under a unique synthetic module name to avoid
    collisions across projects. Modules are expected to call
    :func:`scitex_msword.hooks.register` at import time; this function
    snapshots the dispatcher registry before and after each import so
    the newly registered hooks are attributable to project-local
    discovery (and therefore take precedence over earlier tiers).
    """
    hooks_dir = _find_project_hooks_dir(start)
    if hooks_dir is None:
        return {}

    # Late import to avoid a circular import with _dispatch (which imports
    # this module transitively via the package __init__).
    from . import _dispatch

    discovered: Dict[str, Hook] = {}
    for py_file in sorted(hooks_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        mod_name = f"_sxm_project_hook_{py_file.stem}_{abs(hash(str(py_file)))}"
        spec = importlib.util.spec_from_file_location(mod_name, py_file)
        if spec is None or spec.loader is None:  # pragma: no cover - defensive
            continue
        before = dict(_dispatch._REGISTRY)
        module = importlib.util.module_from_spec(spec)
        try:
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
        except Exception:
            _logger.debug(
                "Failed to import project-local hook module %s", py_file, exc_info=True
            )
            sys.modules.pop(mod_name, None)
            continue
        # New entries in the dispatcher registry are this module's hooks.
        for hook_id, hook in _dispatch._REGISTRY.items():
            if hook_id not in before:
                discovered[hook_id] = hook
    return discovered


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------


def _build_cache(start: Optional[Path] = None) -> Dict[str, Hook]:
    """Merge the three discovery tiers in low-to-high precedence order."""
    from ._builtins import ALL_HOOKS

    merged: Dict[str, Hook] = dict(ALL_HOOKS)
    merged.update(_load_entry_point_hooks())
    merged.update(_load_project_local_hooks(start))
    return merged


def lookup(hook_id: str, *, start: Optional[Path] = None) -> Optional[Hook]:
    """Return the :class:`Hook` registered for *hook_id*, else ``None``.

    Parameters
    ----------
    hook_id : str
        The hook id to resolve (e.g. ``"SXM-TC001"``).
    start : pathlib.Path, optional
        Where to begin the upward walk for project-local hooks.
        Defaults to the current working directory. Primarily for tests.

    Notes
    -----
    The first call builds and caches the merged dict; subsequent calls
    are O(1) dict lookups. Call :func:`reset` to drop the cache.
    """
    global _cache
    if _cache is None:
        _cache = _build_cache(start=start)
    return _cache.get(hook_id)


def all_hooks(*, start: Optional[Path] = None) -> Dict[str, Hook]:
    """Return a shallow copy of the merged hook dict (for tooling)."""
    global _cache
    if _cache is None:
        _cache = _build_cache(start=start)
    return dict(_cache)


def reset() -> None:
    """Drop the cached merged dict so the next :func:`lookup` rebuilds.

    Tests that mutate the dispatcher registry or the project tree must
    call this between mutations.
    """
    global _cache
    _cache = None


__all__ = ["lookup", "all_hooks", "reset"]


# EOF
