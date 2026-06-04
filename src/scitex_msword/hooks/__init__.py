#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: src/scitex_msword/hooks/__init__.py

"""``sxm.hooks`` — pluggable lifecycle-hook framework for DOCX I/O.

This package provides the bones of the v0.3.0 hook system: a tiny
core of dataclasses (:class:`Hook`, :class:`Phase`, :class:`Issue`,
:class:`HookContext`), a :func:`register` decorator, a
:func:`run_phase` dispatcher, and a three-tier discovery mechanism
that merges engine builtins, installed plugins, and project-local
hooks into a single addressable namespace.

Why
---
Project-policy enforcement (e.g. JST BOOST 2026 grant rules, journal
typography lints, audit checks before submission) had been creeping
into ad-hoc build scripts inside individual project repos. The hook
framework gives that policy a stable extension point that lives with
the documents it acts on — projects ship their own ``*.py`` files in
``.scitex/msword/hooks/`` and the engine picks them up automatically.

Phases
------
Only two phases are exposed; each has a sharply defined contract.

* :attr:`Phase.PRE_SAVE` — runs against the in-memory ``Document``
  immediately before serialization. Hooks may mutate the doc in
  place. They **must be idempotent**: running the same hook twice
  on the same input must produce the same output as running it once.
* :attr:`Phase.POST_SAVE` — runs against the freshly serialized file
  on disk. Hooks are **read-only**; any policy violation is signalled
  by raising :class:`Issue` (which is also an exception), aborting
  the save.

The earlier design draft included separate ``VALIDATE`` and
``PRE_LOAD`` phases; both were retired during the design-lock pass:
``VALIDATE`` folded into ``POST_SAVE`` (same read-only/raise-on-issue
contract), ``PRE_LOAD`` was dropped per YAGNI.

Three-tier discovery
--------------------
:func:`lookup` resolves a hook id by merging three sources, with
**later tiers winning over earlier tiers on id collision**:

1. Engine builtins (``_builtins.ALL_HOOKS``). Empty in v0.3.0 H1;
   ``SXM-TC001`` (track-changes audit) and ``SXM-JP001`` (Japanese
   typography) land in H4 / H5.
2. Installed plugins via the ``scitex_msword.hooks`` entry-point
   group. Distributions can ship hook bundles by exposing either a
   single :class:`Hook`, an iterable, or a ``dict[str, Hook]``.
3. Project-local hooks: any ``*.py`` under
   ``<root>/.scitex/msword/hooks/`` where ``<root>`` is the first
   ancestor of the current working directory that contains a
   ``.scitex/msword`` directory. Each module is expected to call
   :func:`register` at import time.

Namespacing convention
----------------------

================  ==============================  ============================
Source            Namespace                       Example
================  ==============================  ============================
SM builtins       ``SXM-*``                       ``SXM-TC001``, ``SXM-JP001``
Installed plugin  ``<DIST-PREFIX>-NNN``           ``SCITEX-WRITER-001``
Project-local     Project initials                ``GRANT-NB001``, ``CLEW-V4I-001``
================  ==============================  ============================

Fail-loud contract
------------------
:func:`run_phase` propagates the **first** exception any hook raises;
later hooks in the same phase do not run and the save is aborted.
This keeps debugging tractable (no silent skipped checks) and forces
hooks to be explicit about what they consider a hard failure.

Idempotency contract (pre_save)
-------------------------------
``PRE_SAVE`` hooks must be idempotent. The framework reserves the
right to invoke a hook more than once per logical save (e.g. when a
preceding hook triggered a re-validation pass), so any mutation must
converge after the first application.

Public surface
--------------
.. autosummary::

   Hook
   Phase
   Issue
   HookContext
   register
   run_phase
   lookup
   reset_cache
"""

from __future__ import annotations

from ._base import Hook, HookContext, Issue, Phase
from ._dispatch import ALL_HOOKS_BY_PHASE, register, run_phase
from ._lookup import lookup
from ._lookup import reset as reset_cache

__all__ = [
    "Hook",
    "Phase",
    "Issue",
    "HookContext",
    "register",
    "run_phase",
    "lookup",
    "reset_cache",
    "ALL_HOOKS_BY_PHASE",
]


# EOF
