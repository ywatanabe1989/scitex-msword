#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: src/scitex_msword/_save_document.py
#
# Part of scitex-msword (AGPL-3.0-only). See LICENSE at the repo root.

"""Document-based save API.

``save_docx`` round-trips a SciTeX writer-dict through ``WordWriter`` —
useful when the source-of-truth is a SciTeX intermediate, but lossy when
the caller has already done python-docx-level work (table cell XML
manipulation, embedded image positioning, run-level bold preservation,
…). proj-grant 2026-06-04: "We need ``save_document(doc, path,
profile=None)`` that applies profile + hook chain."

This module owns that direct save path. It accepts a live
``docx.Document``, optionally applies the profile's advisory layout
hints at the document-defaults level (so the caller's per-run / per-
paragraph overrides win), runs the registered ``PRE_SAVE`` and
``POST_SAVE`` hooks (sxm.hooks H1 dispatcher), and saves.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Union

try:
    from docx.oxml.ns import qn  # type: ignore[import-untyped]
    from lxml import etree  # type: ignore[import-untyped]

    _DOCX_AVAILABLE = True
    _IMPORT_ERROR: Optional[Exception] = None
except ImportError as exc:  # pragma: no cover
    _DOCX_AVAILABLE = False
    _IMPORT_ERROR = exc
    qn = None  # type: ignore[assignment]
    etree = None  # type: ignore[assignment]


_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _ensure_docx_available() -> None:
    if not _DOCX_AVAILABLE:
        raise ImportError(
            "python-docx (and lxml) are required for scitex_msword."
            "_save_document. Install via `pip install python-docx`."
        ) from _IMPORT_ERROR


def _make_w(local_name: str, **attrs):
    """Create a ``w:<tag>`` lxml element with namespaced ``w:`` attributes."""
    el = etree.Element(f"{{{_W_NS}}}{local_name}")
    for key, value in attrs.items():
        if value is None:
            continue
        el.set(f"{{{_W_NS}}}{key}", str(value))
    return el


def _ensure_child(parent, local_name: str):
    """Return the existing ``w:<local_name>`` child of ``parent``, or add one."""
    existing = parent.find(qn(f"w:{local_name}"))
    if existing is not None:
        return existing
    child = _make_w(local_name)
    parent.append(child)
    return child


def _apply_profile_to_document_defaults(doc, profile) -> None:
    """Write profile body/bold/font-size/line-spacing hints into ``docDefaults``.

    Lands the advisory fields at ``<w:docDefaults>`` so the caller's
    per-run / per-paragraph overrides keep winning. Only the fields the
    profile sets are touched (others stay at the document's existing
    defaults).

    Mapping (corrected v0.3.1 per proj-grant BOOST v40 dogfood):

        profile.body_font           → rPrDefault / rPr / rFonts
                                      @w:eastAsia + @w:ascii + @w:hAnsi
                                      (BOOST uses Mincho for both
                                      Japanese body AND embedded Latin
                                      runs — operator id 685).
        profile.body_font_size_pt   → rPrDefault / rPr / sz @w:val   (half-pts)
        profile.line_spacing        → pPrDefault / pPr / spacing
                                      @w:line + @w:lineRule=auto      (240ths)

    ``profile.bold_font`` is intentionally NOT applied here. Putting it
    in docDefaults @w:eastAsia (as v0.3.0 did) made every Japanese body
    paragraph render in Gothic and destroyed the visual contrast bold
    is supposed to provide. v0.3.1 ships
    :func:`_apply_bold_font_to_bold_runs` instead, which sets
    ``rFonts/@w:eastAsia`` on the existing bold runs only.
    """
    if profile is None:
        return

    body_font = getattr(profile, "body_font", None)
    body_font_size_pt = getattr(profile, "body_font_size_pt", None)
    line_spacing = getattr(profile, "line_spacing", None)

    if not any(
        v is not None
        for v in (body_font, body_font_size_pt, line_spacing)
    ):
        return

    styles_part = doc.styles.element
    doc_defaults = _ensure_child(styles_part, "docDefaults")

    if body_font or body_font_size_pt is not None:
        rpr_default = _ensure_child(doc_defaults, "rPrDefault")
        rpr = _ensure_child(rpr_default, "rPr")

        if body_font:
            r_fonts = _ensure_child(rpr, "rFonts")
            # body_font fills all three of eastAsia/ascii/hAnsi — BOOST
            # uses Mincho for embedded Latin runs too (operator id 685).
            # cs (complex-script) is left untouched.
            r_fonts.set(qn("w:eastAsia"), str(body_font))
            r_fonts.set(qn("w:ascii"), str(body_font))
            r_fonts.set(qn("w:hAnsi"), str(body_font))

        if body_font_size_pt is not None:
            sz = _ensure_child(rpr, "sz")
            # ECMA-376 §17.3.2.38: w:val is half-points.
            sz.set(qn("w:val"), str(int(round(float(body_font_size_pt) * 2))))

    if line_spacing is not None:
        ppr_default = _ensure_child(doc_defaults, "pPrDefault")
        ppr = _ensure_child(ppr_default, "pPr")
        spacing = _ensure_child(ppr, "spacing")
        # ECMA-376 §17.3.1.33: w:line is in 240ths of a line; lineRule=auto.
        spacing.set(qn("w:line"), str(int(round(float(line_spacing) * 240))))
        spacing.set(qn("w:lineRule"), "auto")


def _apply_bold_font_to_bold_runs(doc, bold_font: str) -> None:
    """Set ``<w:r>/<w:rPr>/<w:rFonts>@w:eastAsia=bold_font`` on every bold run.

    Japanese-grant typography uses a Gothic typeface only on bold runs
    so the bold/heading weight contrast lives in the typeface itself
    (sans vs serif), not in a synthetic-bold transform. proj-grant
    BOOST v40 confirmed this is the correct semantics — putting the
    Gothic font in docDefaults @w:eastAsia (as v0.3.0 did) wrongly
    propagates it to non-bold body paragraphs.

    Walks ``doc.paragraphs`` and every nested run in headers / footers
    too. Only runs whose ``rPr/b/@w:val`` is truthy (or whose ``b``
    child is present without an explicit ``w:val="false"``) are
    touched; non-bold runs are left at the docDefaults Mincho.
    """
    if not bold_font:
        return

    bold_font_str = str(bold_font)

    def _run_is_bold(r_el) -> bool:
        rpr = r_el.find(qn("w:rPr"))
        if rpr is None:
            return False
        b = rpr.find(qn("w:b"))
        if b is None:
            return False
        val = b.get(qn("w:val"))
        if val is None:
            return True  # presence = bold
        return val.lower() not in ("0", "false", "off")

    def _set_eastAsia(r_el) -> None:
        rpr = _ensure_child(r_el, "rPr")
        r_fonts = _ensure_child(rpr, "rFonts")
        r_fonts.set(qn("w:eastAsia"), bold_font_str)

    body = doc.element.body
    for r_el in body.iter(qn("w:r")):
        if _run_is_bold(r_el):
            _set_eastAsia(r_el)


def save_document(
    doc: Any,
    path: Union[str, Path],
    profile: Union[str, Any, None] = None,
) -> Path:
    """Save a python-docx ``Document`` directly (no writer-dict round-trip).

    Unlike :func:`scitex_msword.save_docx`, which converts a SciTeX
    writer-dict, this entry point operates on a live ``docx.Document``
    so python-docx-level edits (table cell XML, image positioning,
    run-level bold preservation, …) survive intact.

    If ``profile`` is given, its advisory layout hints (``body_font``,
    ``bold_font``, ``body_font_size_pt``, ``line_spacing``) are applied
    at the document-defaults level — caller overrides always win.

    The sxm.hooks H1 dispatcher fires for both phases: ``PRE_SAVE``
    hooks run before the file is written; ``POST_SAVE`` hooks run after
    with ``out_path=path``.

    Parameters
    ----------
    doc : docx.Document
        The Document to mutate (in place) and save.
    path : str | Path
        Destination ``.docx`` path.
    profile : str | BaseWordProfile | None
        Profile name (resolved via :func:`scitex_msword.get_profile`),
        profile instance, or ``None`` to skip profile application.

    Returns
    -------
    pathlib.Path
        The absolute output path.
    """
    _ensure_docx_available()
    from .hooks import HookContext, Phase, run_phase
    from .profiles import BaseWordProfile, get_profile

    out_path = Path(path)
    if profile is None:
        profile_obj = None
    elif isinstance(profile, BaseWordProfile):
        profile_obj = profile
    else:
        profile_obj = get_profile(profile)

    if profile_obj is not None:
        _apply_profile_to_document_defaults(doc, profile_obj)
        bold_font = getattr(profile_obj, "bold_font", None)
        if bold_font:
            _apply_bold_font_to_bold_runs(doc, bold_font)

    ctx = HookContext(doc=doc, profile=profile_obj, path=out_path)
    run_phase(Phase.PRE_SAVE, doc, ctx)
    doc.save(str(out_path))
    run_phase(Phase.POST_SAVE, doc, ctx, out_path=out_path)
    return out_path


__all__ = ["save_document"]


# EOF
