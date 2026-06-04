#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: src/scitex_msword/_track_changes_helpers.py
#
# Part of scitex-msword (AGPL-3.0-only). See LICENSE at the repo root.

"""Internal OOXML helpers extracted from ``track_changes.py``.

``track_changes.py`` was hitting the file-size cap once the v0.3.1
``emit_doc_protection_echo`` / ``track_revisions`` kwargs landed. The
generic OOXML primitives here have no semantic ownership of the
track-changes feature — they're plumbing that ``track_changes.py`` /
``_settings_order.py`` both happen to need. Extracting them keeps the
public-API module focused on the surface and leaves a natural seat for
future tiny OOXML utilities.

All names start with ``_`` to mark them as private to scitex-msword;
``track_changes.py`` re-imports them with the same names.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional, Sequence

try:
    from docx.oxml.ns import qn  # type: ignore[import-untyped]
    from docx.text.run import Run  # type: ignore[import-untyped]
    from lxml import etree

    _DOCX_AVAILABLE = True
except ImportError:  # pragma: no cover
    qn = None  # type: ignore[assignment]
    Run = None  # type: ignore[assignment,misc]
    etree = None  # type: ignore[assignment]
    _DOCX_AVAILABLE = False


_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _settings_element(document):
    """Return the lxml ``<w:settings>`` element for the document."""
    return document.settings.element


def _now_iso() -> str:
    """UTC ISO-8601 timestamp at second precision (Word-friendly)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _make_w_element(tag_local_name: str, **attrs):
    """Create a ``w:<tag>`` lxml element with namespaced ``w:`` attributes."""
    el = etree.Element(f"{{{_W_NS}}}{tag_local_name}")
    for key, value in attrs.items():
        if value is None:
            continue
        el.set(f"{{{_W_NS}}}{key}", str(value))
    return el


def _scan_max_revision_id(document) -> int:
    """Largest ``w:id`` currently used on a ``<w:ins>`` / ``<w:del>``."""
    body = document.element.body
    ins_tag = f"{{{_W_NS}}}ins"
    del_tag = f"{{{_W_NS}}}del"
    max_id = 0
    for elem in body.iter():
        if elem.tag in (ins_tag, del_tag):
            raw = elem.get(qn("w:id"))
            try:
                cid = int(raw) if raw is not None else 0
            except (TypeError, ValueError):
                cid = 0
            if cid > max_id:
                max_id = cid
    return max_id


def _resolve_runs(paragraph, runs: Sequence[Any]) -> List["Run"]:
    """Resolve Run objects / run indices into a list of paragraph Runs."""
    all_runs = list(paragraph.runs)
    elems = [r._r for r in all_runs]
    resolved: List = []
    for item in runs:
        if isinstance(item, int):
            if 0 <= item < len(all_runs):
                resolved.append(all_runs[item])
        else:
            elem = getattr(item, "_r", None) or getattr(item, "element", None)
            if elem is not None and elem in elems:
                resolved.append(item)
    return resolved


def _wrap_runs_in_element(
    paragraph, target_runs: Sequence, wrapper_tag: str, attrs: dict
):
    """Wrap each run's ``<w:r>`` in a new ``<w:wrapper_tag>`` parent."""
    wrappers = []
    for run in target_runs:
        r_elem = run._r
        parent = r_elem.getparent()
        if parent is None:
            continue
        idx = parent.index(r_elem)
        wrapper = _make_w_element(wrapper_tag, **attrs)
        parent.insert(idx, wrapper)
        parent.remove(r_elem)
        wrapper.append(r_elem)
        wrappers.append(wrapper)
    return wrappers


def _next_revision_id(paragraph, explicit: Optional[int]) -> int:
    """Resolve the ``w:id`` for a new revision, defaulting to max+1."""
    if explicit is not None:
        return int(explicit)
    try:
        document = paragraph.part.document  # type: ignore[attr-defined]
    except Exception:
        document = None
    if document is None:
        return 1
    return _scan_max_revision_id(document) + 1


__all__ = [
    "_W_NS",
    "_settings_element",
    "_now_iso",
    "_make_w_element",
    "_scan_max_revision_id",
    "_resolve_runs",
    "_wrap_runs_in_element",
    "_next_revision_id",
]


# EOF
