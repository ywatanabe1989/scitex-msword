#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: src/scitex_msword/_settings_order.py
#
# Part of scitex-msword (AGPL-3.0-only). See LICENSE at the repo root.

"""ECMA-376 §17.15.1 ``CT_Settings`` child-order helper.

Word silently ignores some ``word/settings.xml`` children — including
``<w:trackChanges/>`` — when they appear out of the schema-prescribed
order. proj-grant 2026-06-04 (lost ~1h to this on the BOOST v37 build):

    "ECMA-376 requires <w:trackChanges/> placed in word/settings.xml
    AFTER <w:stylePaneSortMethod/> and BEFORE <w:doNotTrackFormatting/>."

This module owns the placement decision so ``track_changes.py`` (and
any future callers) can drop new settings elements at the correct
ordered slot without recomputing the schema each time.
"""

from __future__ import annotations

try:
    from lxml import etree  # type: ignore[import-untyped]

    _LXML_AVAILABLE = True
except ImportError:  # pragma: no cover
    etree = None  # type: ignore[assignment]
    _LXML_AVAILABLE = False


# The ECMA-376 sequence is long. For the placement of
# ``<w:trackChanges/>`` we only need the children that may legitimately
# precede it (anchor before) and those that may follow (anchor after).
_SETTINGS_CHILDREN_BEFORE_TRACK_CHANGES = (
    "writeProtection",
    "view",
    "zoom",
    "removePersonalInformation",
    "removeDateAndTime",
    "doNotDisplayPageBoundaries",
    "displayBackgroundShape",
    "printPostScriptOverText",
    "printFractionalCharacterWidth",
    "printFormsData",
    "embedTrueTypeFonts",
    "embedSystemFonts",
    "saveSubsetFonts",
    "saveFormsData",
    "mirrorMargins",
    "alignBordersAndEdges",
    "bordersDoNotSurroundHeader",
    "bordersDoNotSurroundFooter",
    "gutterAtTop",
    "hideSpellingErrors",
    "hideGrammaticalErrors",
    "activeWritingStyle",
    "proofState",
    "formsDesign",
    "attachedTemplate",
    "linkStyles",
    "stylePaneFormatFilter",
    "stylePaneSortMethod",
    "documentType",
    "mailMerge",
    "revisionView",
)
# ``<w:trackChanges/>`` slots in here, immediately followed by:
_SETTINGS_CHILDREN_AFTER_TRACK_CHANGES = (
    "doNotTrackMoves",
    "doNotTrackFormatting",
    "documentProtection",
    # …many more; not needed for the placement decision.
)


def insert_in_settings_order(settings_el, new_el, local_name: str) -> None:
    """Insert ``new_el`` into ``settings_el`` at the ECMA-376 ordered slot.

    Walks the existing children once. The new element lands immediately
    after the last present predecessor (per
    ``_SETTINGS_CHILDREN_BEFORE_TRACK_CHANGES``) and before the first
    present successor (per ``_SETTINGS_CHILDREN_AFTER_TRACK_CHANGES``).

    If neither anchor is present, the element is appended at the end —
    that is a position Word accepts when the file is otherwise sparse,
    and it preserves the historical behaviour of ``enable_track_changes``
    for already-flat settings files.

    The function takes ``local_name`` so a future caller can place
    additional ordered elements with the same routine. Today only
    ``"trackChanges"`` is supported; other tags fall back to append.
    """
    if not _LXML_AVAILABLE:  # pragma: no cover
        raise ImportError(
            "lxml is required for scitex_msword._settings_order. "
            "Install via `pip install lxml`."
        )

    if local_name != "trackChanges":
        settings_el.append(new_el)
        return

    before_set = set(_SETTINGS_CHILDREN_BEFORE_TRACK_CHANGES)
    after_set = set(_SETTINGS_CHILDREN_AFTER_TRACK_CHANGES)

    last_before_idx = -1
    first_after_idx = None
    for i, child in enumerate(settings_el):
        tag = etree.QName(child).localname
        if tag in before_set:
            last_before_idx = i
        elif tag in after_set and first_after_idx is None:
            first_after_idx = i

    if last_before_idx >= 0:
        settings_el.insert(last_before_idx + 1, new_el)
    elif first_after_idx is not None:
        settings_el.insert(first_after_idx, new_el)
    else:
        settings_el.append(new_el)


__all__ = ["insert_in_settings_order"]


# EOF
