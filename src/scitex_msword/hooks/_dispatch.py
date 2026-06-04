#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: src/scitex_msword/hooks/_dispatch.py

"""Registration + dispatch for ``sxm.hooks``.

This module owns the in-process registry that :func:`register`
populates and :func:`run_phase` reads from. It also exposes
:data:`ALL_HOOKS_BY_PHASE` — a phase-bucketed view of the registry
that tooling (e.g. ``sxm hooks list``) can iterate without rebuilding
its own grouping.

Design notes
------------
* The registry is process-global and append-only; tests use
  :func:`scitex_msword.hooks._lookup.reset` (and the :func:`_reset`
  helper here) to flush state.
* :func:`run_phase` resolves the **active** hook set from
  ``ctx.config["hooks"]["enable"]``; the absolute, declaration order
  of that list is preserved. This makes ordering predictable and
  controllable per project without re-registering hooks.
* When ``ctx.config["hooks"]["enable"]`` is missing, every registered
  hook for the requested phase runs in registration order. This keeps
  trivial bootstrapping ergonomic during early adoption.
* Dispatch is **fail-loud**: the first hook that raises aborts the
  remainder of the phase. ``post_save`` hooks that want to signal a
  policy violation must raise :class:`Issue` (also an exception).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ._base import Hook, HookContext, Phase

# Process-global registry. Keyed by hook id; values are fully-stitched
# Hook records (i.e. their ``fn`` attribute is populated).
_REGISTRY: Dict[str, Hook] = {}


def register(hook: Hook) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register *hook* with the dispatcher.

    The function supports two call styles:

    **As a decorator (preferred when defining hooks inline):**

    .. code-block:: python

        @register(Hook(
            id="GRANT-NB001",
            phase=Phase.PRE_SAVE,
            severity="warning",
            category="audit",
            message="No-Borders rule",
            suggestion="Strip table borders before save",
            fn=None,           # filled in by the decorator
        ))
        def grant_nb001(doc, ctx):
            ...

    **As a plain call (when registering pre-built callables):**

    .. code-block:: python

        register(Hook(
            id="SXM-EX001", phase=Phase.PRE_SAVE, severity="info",
            category="example", message="...", suggestion="...",
            fn=my_existing_function,
        ))

    Returns
    -------
    Callable
        A decorator. When *hook* already has a non-``None`` ``fn``,
        invoking the decorator (or not) is harmless — the returned
        decorator just records the function and returns it untouched.

    Notes
    -----
    Re-registering an id overwrites the previous record. Combined with
    :func:`_lookup.reset`, this lets tests construct deterministic
    registry states.
    """

    def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        # Hooks are frozen dataclasses, so build a new record with `fn`
        # stitched in (or unchanged if already provided).
        final = hook if hook.fn is not None else _replace_fn(hook, fn)
        _REGISTRY[final.id] = final
        return fn

    # If the Hook already has a callable, record it eagerly so the
    # plain-call style works without invoking the decorator.
    if hook.fn is not None:
        _REGISTRY[hook.id] = hook
    return _decorator


def _replace_fn(hook: Hook, fn: Callable[..., Any]) -> Hook:
    """Return a copy of *hook* with ``fn`` set to *fn*."""
    return Hook(
        id=hook.id,
        phase=hook.phase,
        severity=hook.severity,
        category=hook.category,
        message=hook.message,
        suggestion=hook.suggestion,
        fn=fn,
    )


def _reset() -> None:
    """Drop every registered hook. Intended for tests only."""
    _REGISTRY.clear()


# ---------------------------------------------------------------------
# Phase-bucketed views
# ---------------------------------------------------------------------


class _PhaseView:
    """Lazy, dict-like view that buckets the live registry by phase.

    A plain ``dict`` would be a snapshot at import time and lie about
    later registrations. This proxy reads :data:`_REGISTRY` on every
    access so callers always see the up-to-date set.
    """

    def __getitem__(self, phase: Phase) -> List[Hook]:
        return [h for h in _REGISTRY.values() if h.phase == phase]

    def __iter__(self):
        return iter(Phase)

    def __contains__(self, phase: object) -> bool:
        return isinstance(phase, Phase)

    def get(self, phase: Phase, default: Optional[List[Hook]] = None) -> List[Hook]:
        if not isinstance(phase, Phase):
            return default if default is not None else []
        return self[phase]

    def keys(self):  # pragma: no cover - convenience
        return list(Phase)

    def items(self):  # pragma: no cover - convenience
        return [(p, self[p]) for p in Phase]


ALL_HOOKS_BY_PHASE: _PhaseView = _PhaseView()


# ---------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------


def _resolved_hooks_for_phase(phase: Phase, config: dict) -> List[Hook]:
    """Resolve the ordered hook list for *phase* given *config*.

    Resolution
    ----------
    * If ``config["hooks"]["enable"]`` is present and is a list, each
      entry is looked up through :func:`scitex_msword.hooks.lookup`
      (which consults the three-tier merged dict). Unknown ids are
      ignored — they may belong to a sibling phase, a plugin not
      installed in this environment, or a typo we surface elsewhere.
      The resulting list is then filtered to entries whose phase
      matches *phase*. Declaration order is preserved.
    * If no enable-list is configured, every registered hook for the
      phase runs in registration order. This default keeps
      bootstrapping ergonomic.

    Parameters
    ----------
    phase : Phase
    config : dict
        The full project config snapshot (typically
        ``.scitex/msword/config.yaml`` deserialised). Missing keys are
        tolerated.
    """
    from ._lookup import lookup

    enable = (config or {}).get("hooks", {}).get("enable")
    if enable is None:
        return [h for h in _REGISTRY.values() if h.phase == phase]

    resolved: List[Hook] = []
    for hook_id in enable:
        hook = lookup(hook_id) or _REGISTRY.get(hook_id)
        if hook is None:
            continue
        if hook.phase != phase:
            continue
        resolved.append(hook)
    return resolved


def run_phase(
    phase: Phase,
    doc: object,
    ctx: HookContext,
    *,
    out_path: Optional[Path] = None,
) -> None:
    """Run every hook bound to *phase* against *doc* / *ctx*.

    Parameters
    ----------
    phase : Phase
        The lifecycle phase to dispatch.
    doc : object
        The ``python-docx`` document (or a stand-in in tests).
    ctx : HookContext
        Per-call context carrying ``profile``, ``path``, ``config``.
    out_path : pathlib.Path, optional
        Required when ``phase`` is ``POST_SAVE`` — the path of the file
        the document was just serialized to.

    Raises
    ------
    AssertionError
        If ``phase`` is ``POST_SAVE`` and ``out_path`` is ``None``.
    Exception
        Any exception raised by a hook is propagated immediately,
        aborting the remainder of the phase. Hooks signalling a
        policy violation should raise :class:`Issue`.
    """
    if phase is Phase.POST_SAVE:
        assert out_path is not None, "post_save dispatch requires out_path"

    for hook in _resolved_hooks_for_phase(phase, ctx.config):
        if hook.fn is None:
            # Defensive: a Hook record without a callable cannot run.
            # Registering one is a programmer error; surface loudly.
            raise RuntimeError(
                f"Hook {hook.id!r} is registered without a callable `fn`"
            )
        if phase is Phase.PRE_SAVE:
            hook.fn(doc, ctx)
        else:  # POST_SAVE
            hook.fn(doc, ctx, out_path=out_path)


__all__ = [
    "register",
    "run_phase",
    "ALL_HOOKS_BY_PHASE",
]


# EOF
