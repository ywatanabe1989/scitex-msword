#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-02 00:00:00
# File: src/scitex_msword/track_changes.py
#
# Part of scitex-msword (AGPL-3.0-only). See LICENSE at the repo root.

"""
Track-Changes (revision) utilities for python-docx Documents.

This module surfaces the OOXML revision primitives so agents can:

1. Toggle Word's "Track Changes" switch (``<w:trackChanges/>`` in
   ``word/settings.xml``) via :func:`enable_track_changes`.
2. Wrap agent edits as ``<w:ins>`` / ``<w:del>`` revisions
   (:func:`wrap_as_tracked_insertion`, :func:`wrap_as_tracked_deletion`).
3. Extract all tracked changes (:func:`extract_tracked_changes`).
4. Accept / reject all changes in bulk
   (:func:`accept_all_tracked_changes`, :func:`reject_all_tracked_changes`).

OOXML refs: ``w:trackChanges`` (ECMA-376 §17.15.1.86), ``w:ins``
(§17.13.5.18), ``w:del`` (§17.13.5.14), ``w:delText`` (§17.13.5.15).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional, Sequence

try:
    from docx.document import Document as DocxDocument  # type: ignore[import-untyped]
    from docx.oxml.ns import qn  # type: ignore[import-untyped]
    from docx.text.paragraph import Paragraph  # type: ignore[import-untyped]
    from docx.text.run import Run  # type: ignore[import-untyped]
    from lxml import etree

    DOCX_AVAILABLE = True
    _DOCX_IMPORT_ERROR: Optional[Exception] = None
except ImportError as exc:  # pragma: no cover
    DOCX_AVAILABLE = False
    _DOCX_IMPORT_ERROR = exc
    DocxDocument = None  # type: ignore[assignment,misc]
    Paragraph = None  # type: ignore[assignment,misc]
    Run = None  # type: ignore[assignment,misc]
    qn = None  # type: ignore[assignment]
    etree = None  # type: ignore[assignment]


_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _ensure_docx_available() -> None:
    if not DOCX_AVAILABLE:
        raise ImportError(
            "python-docx (and lxml) are required for scitex_msword.track_changes. "
            "Install via `pip install python-docx`."
        ) from _DOCX_IMPORT_ERROR


# Internal OOXML helpers live in ``_track_changes_helpers`` so this
# module stays focused on the public API surface. The names are
# re-imported verbatim so existing call-sites need no changes.
from ._track_changes_helpers import (
    _make_w_element,
    _next_revision_id,
    _now_iso,
    _resolve_runs,
    _scan_max_revision_id,
    _settings_element,
    _wrap_runs_in_element,
)


# ---------------------------------------------------------------------------
# API 1: enable_track_changes / is_track_changes_enabled
# ---------------------------------------------------------------------------


def enable_track_changes(
    document: "DocxDocument",
    enabled: bool = True,
    *,
    emit_doc_protection_echo: bool = True,
) -> "DocxDocument":
    """Toggle Word's Track Changes switch on the document.

    ``enabled=True`` writes ``<w:trackRevisions/>`` (ECMA-376
    §17.15.1.92 — the actual toggle in ``CT_Settings``). When
    ``emit_doc_protection_echo=True`` (default) also writes the
    matching ``<w:documentProtection w:edit="trackedChanges"
    w:enforcement="0"/>`` to mirror desktop Word's emit so the
    Restrict-Editing pane reads correctly and so some Word
    2016/2019 enterprise builds preserve TC across reopen.
    ``enabled=False`` removes both elements.

    v0.3.1 fix: ≤v0.3.0 emitted ``<w:trackChanges/>`` (``CT_HdrFtr``
    §17.10.1.84) which desktop Word silently ignores in
    ``CT_Settings`` — TC was never actually toggled. Re-save older
    sxm-produced files with this version.
    """
    _ensure_docx_available()
    from ._settings_order import (
        ensure_document_protection_for_tracked_changes,
        insert_in_settings_order,
    )

    settings_el = _settings_element(document)
    existing = settings_el.findall(qn("w:trackRevisions"))

    if enabled:
        if not existing:
            insert_in_settings_order(
                settings_el,
                _make_w_element("trackRevisions"),
                "trackRevisions",
            )
        else:
            for dup in existing[1:]:
                settings_el.remove(dup)
        if emit_doc_protection_echo:
            ensure_document_protection_for_tracked_changes(
                settings_el, _make_w_element
            )
    else:
        for el in existing:
            settings_el.remove(el)
        for el in settings_el.findall(qn("w:documentProtection")):
            if el.get(qn("w:edit")) == "trackedChanges":
                settings_el.remove(el)
    return document


def save_with_track_changes_on(
    document: "DocxDocument",
    path,
    *,
    track_revisions: bool = True,
    emit_doc_protection_echo: bool = True,
) -> "DocxDocument":
    """Save a Document, default-correct for Word Track Changes.

    Default kwargs write the Word-matching recipe (``trackRevisions``
    + ``documentProtection`` ``enforcement=0``) — desktop Word
    honours this natively. Pass ``track_revisions=False`` for the
    clean-export step that strips TC; pair with
    ``emit_doc_protection_echo=False`` if you want ``trackRevisions``
    without the protection-pane echo. See :func:`enable_track_changes`.
    """
    _ensure_docx_available()
    enable_track_changes(
        document,
        enabled=track_revisions,
        emit_doc_protection_echo=emit_doc_protection_echo,
    )
    document.save(str(path))
    return document


def is_track_changes_enabled(document: "DocxDocument") -> bool:
    """Return True iff ``<w:trackRevisions/>`` is present in settings.xml.

    v0.3.1 fix: previous releases pattern-matched against
    ``<w:trackChanges/>`` (a different element entirely — see
    :func:`enable_track_changes`) and so returned False for documents
    created by Word itself or by sxm v0.3.1+. Now reads the correct
    ECMA-376 §17.15.1.92 ``<w:trackRevisions/>`` toggle.
    """
    _ensure_docx_available()
    return (
        _settings_element(document).find(qn("w:trackRevisions"))
        is not None
    )


# ---------------------------------------------------------------------------
# API 2: wrap_as_tracked_insertion
# ---------------------------------------------------------------------------


def wrap_as_tracked_insertion(
    paragraph: "Paragraph",
    runs: Sequence[Any],
    author: str = "agent",
    date: Optional[str] = None,
    w_id: Optional[int] = None,
) -> List[Any]:
    """
    Wrap the given runs of ``paragraph`` in ``<w:ins>`` revision blocks.

    Word renders the wrapped content as "inserted by <author>" and
    surfaces it as an accept/reject-able revision.

    Parameters
    ----------
    paragraph : docx.text.paragraph.Paragraph
        Paragraph that owns the runs to wrap.
    runs : sequence of Run or int
        Runs to wrap, by Run object or by 0-based index.
    author : str, default "agent"
        Recorded in ``w:author``.
    date : str, optional
        ISO-8601 string for ``w:date``; defaults to ``now(UTC)``.
    w_id : int, optional
        Explicit revision id; auto-assigned (max+1) when ``None``.

    Returns
    -------
    list
        Newly created ``<w:ins>`` lxml elements.
    """
    _ensure_docx_available()
    target_runs = _resolve_runs(paragraph, runs)
    if not target_runs:
        return []

    attrs = {
        "id": _next_revision_id(paragraph, w_id),
        "author": author,
        "date": date or _now_iso(),
    }
    return _wrap_runs_in_element(paragraph, target_runs, "ins", attrs)


# ---------------------------------------------------------------------------
# API 3: wrap_as_tracked_deletion
# ---------------------------------------------------------------------------


def wrap_as_tracked_deletion(
    paragraph: "Paragraph",
    runs: Sequence[Any],
    author: str = "agent",
    date: Optional[str] = None,
    w_id: Optional[int] = None,
) -> List[Any]:
    """
    Wrap the given runs of ``paragraph`` in ``<w:del>`` revision blocks.

    Each wrapped run's ``<w:t>`` children are also retagged as
    ``<w:delText>`` so Word renders the deletion with strike-through.

    Parameters
    ----------
    paragraph : docx.text.paragraph.Paragraph
        Paragraph that owns the runs to wrap.
    runs : sequence of Run or int
        Runs to wrap, by Run object or by 0-based index.
    author : str, default "agent"
        Recorded in ``w:author``.
    date : str, optional
        ISO-8601 string for ``w:date``; defaults to ``now(UTC)``.
    w_id : int, optional
        Explicit revision id; auto-assigned (max+1) when ``None``.

    Returns
    -------
    list
        Newly created ``<w:del>`` lxml elements.
    """
    _ensure_docx_available()
    target_runs = _resolve_runs(paragraph, runs)
    if not target_runs:
        return []

    attrs = {
        "id": _next_revision_id(paragraph, w_id),
        "author": author,
        "date": date or _now_iso(),
    }
    wrappers = _wrap_runs_in_element(paragraph, target_runs, "del", attrs)

    t_qn = qn("w:t")
    delText_qn = qn("w:delText")
    for wrapper in wrappers:
        for t in list(wrapper.iter(t_qn)):
            t.tag = delText_qn
    return wrappers


# ---------------------------------------------------------------------------
# API 4: extract_tracked_changes
# ---------------------------------------------------------------------------


def extract_tracked_changes(
    document: "DocxDocument",
) -> List[dict]:
    """
    Return every ``<w:ins>`` / ``<w:del>`` revision as a structured dict.

    Parameters
    ----------
    document : docx.Document
        The Document to scan.

    Returns
    -------
    list[dict]
        Each entry is shaped as::

            {"type": "insert" | "delete",
             "paragraph_idx": int,
             "author": str,
             "date": str,
             "id": str,
             "text": str}
    """
    _ensure_docx_available()
    ins_tag = f"{{{_W_NS}}}ins"
    del_tag = f"{{{_W_NS}}}del"
    t_tag = f"{{{_W_NS}}}t"
    delText_tag = f"{{{_W_NS}}}delText"
    id_attr = qn("w:id")
    author_attr = qn("w:author")
    date_attr = qn("w:date")

    results: List[dict] = []
    for pi, para in enumerate(document.paragraphs):
        for elem in para._p.iter():
            if elem.tag not in (ins_tag, del_tag):
                continue
            texts: List[str] = []
            for t in elem.iter():
                if t.tag in (t_tag, delText_tag) and t.text:
                    texts.append(t.text)
            results.append(
                {
                    "type": "insert" if elem.tag == ins_tag else "delete",
                    "paragraph_idx": pi,
                    "author": elem.get(author_attr, ""),
                    "date": elem.get(date_attr, ""),
                    "id": elem.get(id_attr, ""),
                    "text": "".join(texts),
                }
            )
    return results


# ---------------------------------------------------------------------------
# API 5: accept_all / reject_all
# ---------------------------------------------------------------------------


def _unwrap_element(elem) -> None:
    """Replace ``elem`` in its parent with its own children, in order."""
    parent = elem.getparent()
    if parent is None:
        return
    idx = parent.index(elem)
    for offset, child in enumerate(list(elem)):
        elem.remove(child)
        parent.insert(idx + offset, child)
    parent.remove(elem)


def accept_all_tracked_changes(document: "DocxDocument") -> "DocxDocument":
    """
    Accept all tracked changes — equivalent to Word's "Accept All".

    ``<w:ins>`` wrappers are unwrapped (content remains); ``<w:del>``
    wrappers and their contents are removed.

    Parameters
    ----------
    document : docx.Document
        The Document to mutate in place.

    Returns
    -------
    docx.Document
        The same Document, mutated.
    """
    _ensure_docx_available()
    body = document.element.body
    ins_tag = f"{{{_W_NS}}}ins"
    del_tag = f"{{{_W_NS}}}del"

    for el in [e for e in body.iter() if e.tag in (ins_tag, del_tag)]:
        parent = el.getparent()
        if parent is None:
            continue
        if el.tag == ins_tag:
            _unwrap_element(el)
        else:
            parent.remove(el)
    return document


def reject_all_tracked_changes(document: "DocxDocument") -> "DocxDocument":
    """
    Reject all tracked changes — equivalent to Word's "Reject All".

    ``<w:ins>`` wrappers and contents are removed; ``<w:del>`` wrappers
    are unwrapped and their ``<w:delText>`` children retagged back to
    ``<w:t>`` so the original text is restored.

    Parameters
    ----------
    document : docx.Document
        The Document to mutate in place.

    Returns
    -------
    docx.Document
        The same Document, mutated.
    """
    _ensure_docx_available()
    body = document.element.body
    ins_tag = f"{{{_W_NS}}}ins"
    del_tag = f"{{{_W_NS}}}del"
    t_tag = qn("w:t")
    delText_tag = f"{{{_W_NS}}}delText"

    for el in [e for e in body.iter() if e.tag in (ins_tag, del_tag)]:
        parent = el.getparent()
        if parent is None:
            continue
        if el.tag == ins_tag:
            parent.remove(el)
        else:
            for dt in list(el.iter(delText_tag)):
                dt.tag = t_tag
            _unwrap_element(el)
    return document


__all__ = [
    "enable_track_changes",
    "is_track_changes_enabled",
    "wrap_as_tracked_insertion",
    "wrap_as_tracked_deletion",
    "extract_tracked_changes",
    "accept_all_tracked_changes",
    "reject_all_tracked_changes",
]
