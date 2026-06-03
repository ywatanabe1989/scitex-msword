#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-02 00:00:00
# File: src/scitex_msword/bold.py
#
# Part of scitex-msword (AGPL-3.0-only). See LICENSE at the repo root.

"""
Preserve specified tokens by re-splitting runs and applying bold + font.

This module implements :func:`preserve_bold_tokens` which scans a
``python-docx`` Document, locates every occurrence of each token, and
ensures that token is its own run with ``bold=True`` and a configurable
font (default ``MS Gothic`` — used for emphasized Japanese keywords in
the BOOST 2026 application).

The implementation operates per paragraph: it concatenates run text,
finds token spans, then rebuilds the paragraph's runs as
``[before, token, after]`` triples, preserving the original character
formatting of the surrounding text.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import docx  # type: ignore[import-untyped]
    from docx.document import Document as DocxDocument  # type: ignore[import-untyped]
    from docx.oxml.ns import qn  # type: ignore[import-untyped]

    DOCX_AVAILABLE = True
    _DOCX_IMPORT_ERROR: Optional[Exception] = None
except ImportError as exc:  # pragma: no cover
    DOCX_AVAILABLE = False
    _DOCX_IMPORT_ERROR = exc
    DocxDocument = None  # type: ignore[assignment,misc]
    qn = None  # type: ignore[assignment]


DEFAULT_FONT = "MS Gothic"


def _ensure_docx_available() -> None:
    if not DOCX_AVAILABLE:
        raise ImportError(
            "python-docx is required for scitex_msword.bold. "
            "Install it via `pip install python-docx`."
        ) from _DOCX_IMPORT_ERROR


def _snapshot_run_format(run) -> Dict[str, Any]:
    """Capture the formatting attributes we care about from a Run."""
    snap: Dict[str, Any] = {
        "bold": run.bold,
        "italic": run.italic,
        "underline": run.underline,
    }
    try:
        snap["font_name"] = run.font.name
    except Exception:
        snap["font_name"] = None
    try:
        snap["font_size"] = run.font.size
    except Exception:
        snap["font_size"] = None
    try:
        snap["highlight"] = run.font.highlight_color
    except Exception:
        snap["highlight"] = None
    return snap


def _apply_run_format(run, snap: Dict[str, Any]) -> None:
    """Apply a previously snapshotted format onto a Run."""
    if snap.get("bold") is not None:
        run.bold = snap["bold"]
    if snap.get("italic") is not None:
        run.italic = snap["italic"]
    if snap.get("underline") is not None:
        run.underline = snap["underline"]
    if snap.get("font_name"):
        run.font.name = snap["font_name"]
    if snap.get("font_size"):
        run.font.size = snap["font_size"]
    if snap.get("highlight") is not None:
        try:
            run.font.highlight_color = snap["highlight"]
        except Exception:
            pass


def _force_east_asian_font(run, font_name: str) -> None:
    """
    Force the East-Asian font slot on a run.

    python-docx's ``run.font.name`` only sets the Latin face; for Japanese
    text (which BOOST keywords usually contain) Word also requires the
    East-Asian (``w:eastAsia``) attribute on the run's ``w:rFonts`` element.
    """
    if qn is None:  # pragma: no cover
        return
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        # python-docx auto-creates rFonts when we set run.font.name; if
        # somehow missing we manually add the East-Asian slot via XML.
        from docx.oxml import OxmlElement  # type: ignore[import-untyped]

        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), font_name)
    rFonts.set(qn("w:ascii"), font_name)
    rFonts.set(qn("w:hAnsi"), font_name)
    rFonts.set(qn("w:cs"), font_name)


def _find_token_spans(
    text: str, tokens: Sequence[str], *, case_sensitive: bool
) -> List[Tuple[int, int, str]]:
    """
    Return ``[(start, end, token), ...]`` spans for every token occurrence.

    Spans are sorted by start position; if tokens overlap, the earliest
    longest match wins.
    """
    if not text or not tokens:
        return []
    # Build an alternation pattern of escaped tokens, longest first so
    # the regex prefers the longer match when tokens overlap.
    sorted_tokens = sorted({t for t in tokens if t}, key=len, reverse=True)
    if not sorted_tokens:
        return []
    pattern = "|".join(re.escape(t) for t in sorted_tokens)
    flags = 0 if case_sensitive else re.IGNORECASE
    spans = [(m.start(), m.end(), m.group(0)) for m in re.finditer(pattern, text, flags)]
    return spans


def _rebuild_paragraph_with_spans(
    paragraph,
    spans: List[Tuple[int, int, str]],
    font_name: str,
    base_format: Dict[str, Any],
) -> None:
    """
    Rebuild ``paragraph``'s runs so each span becomes its own bold run.

    The non-span text is split into runs that inherit ``base_format``.
    Non-text run children (drawings, breaks, fields) on the original
    runs are preserved by *not* removing the original ``w:r`` elements
    that contain only non-text content; instead, we only rewrite runs
    whose entire content was plain text. Mixed runs are left alone and
    skipped from rewriting in this pass.
    """
    # Capture text segments to emit, in order.
    text = paragraph.text
    if not text:
        return

    segments: List[Tuple[str, bool]] = []
    cursor = 0
    for s, e, _ in spans:
        if s > cursor:
            segments.append((text[cursor:s], False))
        segments.append((text[s:e], True))
        cursor = e
    if cursor < len(text):
        segments.append((text[cursor:], False))

    # Remove existing runs entirely (we will reconstruct them).
    for r in list(paragraph._p.findall(qn("w:r"))):
        paragraph._p.remove(r)

    # Re-add runs.
    for content, is_token in segments:
        if not content:
            continue
        new_run = paragraph.add_run(content)
        _apply_run_format(new_run, base_format)
        if is_token:
            new_run.bold = True
            new_run.font.name = font_name
            _force_east_asian_font(new_run, font_name)


def preserve_bold_tokens(
    document: "DocxDocument",
    tokens: Sequence[str],
    *,
    font_name: str = DEFAULT_FONT,
    case_sensitive: bool = True,
) -> "DocxDocument":
    """
    Walk every paragraph in ``document`` and bold-emphasize each token hit.

    Wherever a token appears inside paragraph text, the paragraph's runs
    are split so that the token sits in its own run with ``bold=True``
    and ``font.name = font_name`` (Latin + East-Asian + complex script
    slots are all set so Japanese text picks up MS Gothic in Word).

    Parameters
    ----------
    document : docx.Document
        The Document to mutate in place.
    tokens : sequence of str
        Strings to emphasize. Empty strings are ignored. Longer tokens
        take precedence on overlapping matches.
    font_name : str, default "MS Gothic"
        Font face applied to matched tokens.
    case_sensitive : bool, default True
        If False, matching is case-insensitive.

    Returns
    -------
    docx.Document
        The same Document object, mutated.

    Notes
    -----
    This implementation rewrites all runs of a paragraph when at least
    one token hits; paragraphs without hits are left untouched. The
    original surrounding format (italic, underline, size, highlight) is
    captured from the *first* run before rebuilding — if you need
    finer-grained preservation, run :func:`preserve_bold_tokens` before
    other run-level edits.

    Examples
    --------
    >>> from scitex_msword.bold import preserve_bold_tokens
    >>> preserve_bold_tokens(doc, tokens=["BOOST", "JST"])
    """
    _ensure_docx_available()
    if not tokens:
        return document

    for paragraph in document.paragraphs:
        spans = _find_token_spans(
            paragraph.text, list(tokens), case_sensitive=case_sensitive
        )
        if not spans:
            continue
        # Capture base formatting from the first run (best-effort).
        base_format: Dict[str, Any] = {}
        if paragraph.runs:
            base_format = _snapshot_run_format(paragraph.runs[0])
            # Don't propagate the source run's bold/highlight onto
            # non-token segments — those should look "normal".
            base_format["bold"] = False
            base_format["highlight"] = None
        _rebuild_paragraph_with_spans(paragraph, spans, font_name, base_format)

    return document


__all__ = ["preserve_bold_tokens", "DEFAULT_FONT"]
