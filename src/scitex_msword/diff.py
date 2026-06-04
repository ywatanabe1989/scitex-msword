#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-02 00:00:00
# File: src/scitex_msword/diff.py
#
# Part of scitex-msword (AGPL-3.0-only). See LICENSE at the repo root.

"""
Paragraph-level diff between two DOCX documents.

This module implements ``diff_docx`` which compares two .docx files (or two
already-loaded ``python-docx`` ``Document`` objects) and returns a list of
paragraph-level operations describing the changes.

The diff is computed with ``difflib.SequenceMatcher`` over paragraph text,
and per-paragraph run-level formatting deltas (bold / italic / underline /
font / highlight) are also captured for ``modify`` operations.

Typical usage
-------------
    >>> from scitex_msword.diff import diff_docx
    >>> ops = diff_docx("v15.docx", "v16.docx")
    >>> for op in ops:
    ...     print(op["op"], op["index"], op.get("text_b") or op.get("text_a"))
"""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import docx  # type: ignore[import-untyped]
    from docx.document import Document as DocxDocument  # type: ignore[import-untyped]

    DOCX_AVAILABLE = True
    _DOCX_IMPORT_ERROR: Optional[Exception] = None
except ImportError as exc:  # pragma: no cover — install-time issue
    DOCX_AVAILABLE = False
    _DOCX_IMPORT_ERROR = exc
    DocxDocument = None  # type: ignore[assignment,misc]


DocLike = Union[str, Path, "DocxDocument"]

# Run-level attributes we track for "modify" diffs.
_RUN_ATTRS = ("bold", "italic", "underline", "font_name", "font_size", "highlight")


def _ensure_docx_available() -> None:
    if not DOCX_AVAILABLE:
        raise ImportError(
            "python-docx is required for scitex_msword.diff. "
            "Install it via `pip install python-docx`."
        ) from _DOCX_IMPORT_ERROR


def _load(doc_like: DocLike) -> "DocxDocument":
    """Coerce a path or an already-open Document into a Document."""
    _ensure_docx_available()
    if isinstance(doc_like, (str, Path)):
        return docx.Document(str(doc_like))
    return doc_like


def _extract_run_info(run) -> Dict[str, Any]:
    """Extract diff-relevant attributes from a python-docx Run."""
    info: Dict[str, Any] = {
        "text": run.text,
        "bold": bool(run.bold) if run.bold is not None else False,
        "italic": bool(run.italic) if run.italic is not None else False,
        "underline": run.underline is not None and bool(run.underline),
    }
    try:
        if run.font.name:
            info["font_name"] = run.font.name
    except Exception:
        pass
    try:
        if run.font.size:
            info["font_size"] = run.font.size.pt
    except Exception:
        pass
    try:
        hl = run.font.highlight_color
        if hl is not None:
            # WD_COLOR_INDEX enum -> human-readable lowercase name.
            # str(hl) is e.g. "TURQUOISE (3)"; .name is "TURQUOISE".
            name = getattr(hl, "name", str(hl)).split(".")[-1].split(" ")[0]
            info["highlight"] = name.lower()
    except Exception:
        pass
    return info


def _paragraph_texts_and_runs(
    document: "DocxDocument",
) -> Tuple[List[str], List[List[Dict[str, Any]]]]:
    """Return per-paragraph (text, run-info-list) for the document body."""
    texts: List[str] = []
    runs: List[List[Dict[str, Any]]] = []
    for para in document.paragraphs:
        texts.append(para.text)
        runs.append([_extract_run_info(r) for r in para.runs])
    return texts, runs


def _diff_runs(
    runs_a: List[Dict[str, Any]], runs_b: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Compare run lists by index and return a list of run-level changes.

    Only the attributes in ``_RUN_ATTRS`` are tracked. For run-count
    mismatches, the extra runs are reported as added/removed.
    """
    changes: List[Dict[str, Any]] = []
    common = min(len(runs_a), len(runs_b))
    for i in range(common):
        ra, rb = runs_a[i], runs_b[i]
        delta: Dict[str, Any] = {}
        for attr in _RUN_ATTRS:
            va, vb = ra.get(attr), rb.get(attr)
            if va != vb:
                delta[attr] = {"a": va, "b": vb}
        if ra.get("text") != rb.get("text"):
            delta["text"] = {"a": ra.get("text"), "b": rb.get("text")}
        if delta:
            changes.append({"run_index": i, "delta": delta})
    if len(runs_a) > common:
        for i in range(common, len(runs_a)):
            changes.append({"run_index": i, "removed": runs_a[i]})
    if len(runs_b) > common:
        for i in range(common, len(runs_b)):
            changes.append({"run_index": i, "added": runs_b[i]})
    return changes


def diff_docx(
    a: DocLike,
    b: DocLike,
    *,
    include_run_diff: bool = True,
) -> List[Dict[str, Any]]:
    """
    Compute paragraph-level diff between two DOCX documents.

    Parameters
    ----------
    a, b : str | Path | docx.Document
        Inputs to compare. May be paths or already-loaded Documents.
    include_run_diff : bool, default True
        If True, ``modify`` operations include a ``runs_changed`` field
        listing the run-level formatting deltas.

    Returns
    -------
    list[dict]
        Each entry is one of::

            {"op": "equal",  "index": int, "text_a": str, "text_b": str}
            {"op": "insert", "index": int, "text_a": None, "text_b": str}
            {"op": "delete", "index": int, "text_a": str,  "text_b": None}
            {"op": "modify", "index": int, "text_a": str,  "text_b": str,
             "runs_changed": [...]}

        ``index`` refers to the paragraph index in document ``b`` for
        ``equal``/``insert``/``modify`` operations, and to the paragraph
        index in document ``a`` for ``delete`` operations.

    Examples
    --------
    >>> from scitex_msword.diff import diff_docx
    >>> ops = diff_docx("v15.docx", "v16.docx")
    >>> changes = [o for o in ops if o["op"] != "equal"]
    """
    doc_a = _load(a)
    doc_b = _load(b)

    texts_a, runs_a = _paragraph_texts_and_runs(doc_a)
    texts_b, runs_b = _paragraph_texts_and_runs(doc_b)

    matcher = difflib.SequenceMatcher(a=texts_a, b=texts_b, autojunk=False)
    ops: List[Dict[str, Any]] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                ops.append(
                    {
                        "op": "equal",
                        "index": j1 + k,
                        "text_a": texts_a[i1 + k],
                        "text_b": texts_b[j1 + k],
                    }
                )
        elif tag == "delete":
            for k in range(i2 - i1):
                ops.append(
                    {
                        "op": "delete",
                        "index": i1 + k,
                        "text_a": texts_a[i1 + k],
                        "text_b": None,
                    }
                )
        elif tag == "insert":
            for k in range(j2 - j1):
                ops.append(
                    {
                        "op": "insert",
                        "index": j1 + k,
                        "text_a": None,
                        "text_b": texts_b[j1 + k],
                    }
                )
        elif tag == "replace":
            # Pair up the replaced ranges; surplus on either side becomes
            # delete / insert.
            paired = min(i2 - i1, j2 - j1)
            for k in range(paired):
                ai, bi = i1 + k, j1 + k
                entry: Dict[str, Any] = {
                    "op": "modify",
                    "index": bi,
                    "text_a": texts_a[ai],
                    "text_b": texts_b[bi],
                }
                if include_run_diff:
                    entry["runs_changed"] = _diff_runs(runs_a[ai], runs_b[bi])
                ops.append(entry)
            for k in range(paired, i2 - i1):
                ai = i1 + k
                ops.append(
                    {
                        "op": "delete",
                        "index": ai,
                        "text_a": texts_a[ai],
                        "text_b": None,
                    }
                )
            for k in range(paired, j2 - j1):
                bi = j1 + k
                ops.append(
                    {
                        "op": "insert",
                        "index": bi,
                        "text_a": None,
                        "text_b": texts_b[bi],
                    }
                )

    return ops


def summarize_diff(ops: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Convenience helper: count operations by type.

    Parameters
    ----------
    ops : list[dict]
        Output of :func:`diff_docx`.

    Returns
    -------
    dict[str, int]
        Mapping ``{"equal": n, "insert": n, "delete": n, "modify": n}``.
    """
    summary = {"equal": 0, "insert": 0, "delete": 0, "modify": 0}
    for op in ops:
        summary[op["op"]] = summary.get(op["op"], 0) + 1
    return summary


__all__ = ["diff_docx", "summarize_diff"]
