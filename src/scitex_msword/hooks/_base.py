#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: src/scitex_msword/hooks/_base.py

"""Core dataclasses for the ``sxm.hooks`` framework.

This module deliberately depends only on the Python standard library so
that downstream code (and tests) can build :class:`Hook` instances
without importing ``python-docx`` or any other heavy optional
dependency. The ``doc`` carried inside a :class:`HookContext` is typed
as ``object`` for the same reason — hook implementations narrow it as
needed at call time.

See ``scitex_msword.hooks.__init__`` for the high-level framework
overview (namespacing, three-tier discovery, fail-loud contract,
idempotency contract for pre_save hooks).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional


class Phase(str, Enum):
    """Lifecycle phases at which hooks may run.

    The framework intentionally exposes only two phases:

    ``PRE_SAVE``
        Runs against the in-memory document immediately before it is
        serialized to disk. Hooks may mutate the document in place.
        Must be **idempotent**: running the same hook twice on the same
        document must produce the same result as running it once.

    ``POST_SAVE``
        Runs against the freshly serialized file on disk. Hooks are
        expected to be **read-only**; any policy violation must be
        signalled by raising :class:`Issue` (or another exception),
        which aborts the save and surfaces the issue to the caller.

    Earlier design iterations included separate ``VALIDATE`` and
    ``PRE_LOAD`` phases. ``VALIDATE`` was folded into ``POST_SAVE``
    (read-only + raise-on-issue contract); ``PRE_LOAD`` was dropped per
    YAGNI. See proj-grant ``design_sxm_hooks_v01.md`` plus the
    proj-scitex-dev design-lock thread for the rationale.
    """

    PRE_SAVE = "pre_save"
    POST_SAVE = "post_save"


class Issue(Exception):
    """A policy violation surfaced by a hook.

    :class:`Issue` is both a dataclass-like record **and** an exception
    so that hooks can signal violations with a single ``raise``:

    .. code-block:: python

        raise Issue(
            hook_id="SXM-TC001",
            severity="error",
            location="word/settings.xml",
            message="Track Changes is enabled",
            suggestion="Run accept_all_tracked_changes(doc) before save",
        )

    The fail-loud contract of :func:`run_phase` then aborts the
    remainder of the phase and propagates the exception to the caller
    (typically ``save_docx``), which can either surface it to the user
    or convert it into a structured report.

    Attributes
    ----------
    hook_id : str
        Stable id of the hook that raised the issue (e.g. ``SXM-TC001``).
    severity : str
        One of ``"error"``, ``"warning"``, ``"info"``. Hooks that raise
        an :class:`Issue` are still aborting the phase regardless of
        severity — the severity is metadata for downstream reporting.
    location : str
        Human-readable pointer at where the violation lives, e.g.
        ``"§2.1 / para 14"`` or ``"word/settings.xml"``.
    message : str
        Short description of the violation.
    suggestion : str
        Actionable remediation hint shown to the user.
    """

    def __init__(
        self,
        hook_id: str,
        severity: str,
        location: str,
        message: str,
        suggestion: str = "",
    ) -> None:
        self.hook_id = hook_id
        self.severity = severity
        self.location = location
        self.message = message
        self.suggestion = suggestion
        super().__init__(f"[{hook_id}] {severity} @ {location}: {message}")

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"Issue(hook_id={self.hook_id!r}, severity={self.severity!r}, "
            f"location={self.location!r}, message={self.message!r}, "
            f"suggestion={self.suggestion!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Issue):
            return NotImplemented
        return (
            self.hook_id == other.hook_id
            and self.severity == other.severity
            and self.location == other.location
            and self.message == other.message
            and self.suggestion == other.suggestion
        )

    def __hash__(self) -> int:
        return hash(
            (self.hook_id, self.severity, self.location, self.message, self.suggestion)
        )


@dataclass
class HookContext:
    """Per-call context handed to every hook function.

    Attributes
    ----------
    doc : object
        The ``python-docx`` ``Document`` being saved. Typed as ``object``
        so this module stays dependency-free; hooks narrow as needed.
    profile : object | None
        The resolved :class:`scitex_msword.profiles.BaseWordProfile`
        for this save, or ``None`` when no profile is active.
    path : pathlib.Path
        Target output path of the save. ``post_save`` hooks receive the
        same path as ``out_path`` for convenience.
    config : dict
        Snapshot of the full ``.scitex/msword/config.yaml`` (or empty
        dict if no project config was found). Hooks read their own
        sub-tree under ``config["hooks"]``.

    Notes
    -----
    :meth:`element_for` is the documented XML-level escape hatch for
    hooks that need to inspect or mutate raw package parts (e.g.
    ``/word/settings.xml`` for SXM-TC001).
    """

    doc: object
    profile: Optional[object] = None
    path: Path = field(default_factory=Path)
    config: dict = field(default_factory=dict)

    def element_for(self, part: str) -> Any:
        """Return the lxml element for the named package part.

        Parameters
        ----------
        part : str
            Package-part name in the OOXML sense, e.g.
            ``"/word/settings.xml"``.

        Returns
        -------
        lxml.etree._Element
            Live XML element backing the requested part. Mutations are
            written through when the document is serialized.

        Raises
        ------
        AttributeError
            If ``self.doc`` is not a ``python-docx`` ``Document``
            (e.g. test stubs that don't expose ``.part.package.parts``).
        KeyError
            If the requested part is not present in the package.
        """
        # Loose attribute access keeps this module free of python-docx imports.
        return self.doc.part.package.parts[part].element  # type: ignore[attr-defined]


@dataclass(frozen=True)
class Hook:
    """Declarative metadata + callable for one hook.

    Attributes
    ----------
    id : str
        Stable identifier following ``<NAMESPACE>-<TAG><NUM>``.
        See module docstring of ``scitex_msword.hooks`` for the
        namespacing convention (``SXM-*`` for engine builtins,
        ``<DIST-PREFIX>-NNN`` for entry-point plugins, project initials
        for project-local hooks).
    phase : Phase
        Phase at which this hook runs.
    severity : str
        One of ``"error"``, ``"warning"``, ``"info"``. Mirrors the
        severity scheme used by scitex-dev's linter rules.
    category : str
        Free-form grouping label, e.g. ``"compliance"``, ``"typography"``,
        ``"audit"``. Used by tooling that filters hooks by category.
    message : str
        Short description of what the hook checks/does.
    suggestion : str
        Default remediation hint shown alongside any raised :class:`Issue`.
    fn : Callable | None
        The hook implementation. The signature depends on ``phase``:

        * ``PRE_SAVE``  → ``fn(doc, ctx: HookContext) -> Document | None``
        * ``POST_SAVE`` → ``fn(doc, ctx: HookContext, *, out_path: Path) -> None``

        May be ``None`` at construction time when used as a decorator
        target — :func:`register` stitches the function in.
    """

    id: str
    phase: Phase
    severity: str
    category: str
    message: str
    suggestion: str
    fn: Optional[Callable[..., Any]] = None


# EOF
