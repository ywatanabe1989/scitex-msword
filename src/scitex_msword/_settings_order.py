#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: src/scitex_msword/_settings_order.py
#
# Part of scitex-msword (AGPL-3.0-only). See LICENSE at the repo root.

"""ECMA-376 §17.15.1 ``CT_Settings`` child-order helper.

Word silently ignores some ``word/settings.xml`` children when they
appear out of the schema-prescribed order, and silently ignores some
elements outright when the wrong name is used. proj-grant 2026-06-04
(lost ~1h on the BOOST v37 build) flagged the ordering bug for the
trackRevisions toggle; the second pass on BOOST v40 surfaced that the
v0.3.0 release was emitting ``<w:trackChanges/>`` (CT_HdrFtr
§17.10.1.84 — a different element entirely) instead of the actual
toggle ``<w:trackRevisions/>`` (CT_Settings §17.15.1.92). Both
mistakes are addressed by this module owning placement decisions for
the named CT_Settings children that ``track_changes.py`` writes.
"""

from __future__ import annotations

try:
    from lxml import etree  # type: ignore[import-untyped]

    _LXML_AVAILABLE = True
except ImportError:  # pragma: no cover
    etree = None  # type: ignore[assignment]
    _LXML_AVAILABLE = False


_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


# The ECMA-376 sequence is long. For the placements ``track_changes``
# performs we only need the children that may legitimately precede
# each target (anchor before) and those that may follow (anchor after).
# Confirmed against Word's own emission on a manually-toggled document
# (proj-grant draft_v39 reference): the ordered tail is …,
# stylePaneSortMethod, trackRevisions, doNotTrackFormatting,
# documentProtection, …
_SETTINGS_CHILDREN_BEFORE_TRACK_REVISIONS = (
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
_SETTINGS_CHILDREN_AFTER_TRACK_REVISIONS = (
    "doNotTrackMoves",
    "doNotTrackFormatting",
    "documentProtection",
    # …many more; not needed for the placement decision.
)

# documentProtection slots in AFTER doNotTrackFormatting; everything
# before doNotTrackFormatting (inclusive) is a valid predecessor.
_SETTINGS_CHILDREN_BEFORE_DOCUMENT_PROTECTION = (
    _SETTINGS_CHILDREN_BEFORE_TRACK_REVISIONS
    + ("trackRevisions", "doNotTrackMoves", "doNotTrackFormatting")
)
_SETTINGS_CHILDREN_AFTER_DOCUMENT_PROTECTION = (
    "autoFormatOverride",
    "styleLockTheme",
    "styleLockQFSet",
    # …many more; not needed for the placement decision.
)


_ANCHOR_TABLES = {
    "trackRevisions": (
        _SETTINGS_CHILDREN_BEFORE_TRACK_REVISIONS,
        _SETTINGS_CHILDREN_AFTER_TRACK_REVISIONS,
    ),
    "documentProtection": (
        _SETTINGS_CHILDREN_BEFORE_DOCUMENT_PROTECTION,
        _SETTINGS_CHILDREN_AFTER_DOCUMENT_PROTECTION,
    ),
}


def insert_in_settings_order(settings_el, new_el, local_name: str) -> None:
    """Insert ``new_el`` into ``settings_el`` at the ECMA-376 ordered slot.

    Walks the existing children once. The new element lands immediately
    after the last present predecessor and before the first present
    successor (per the per-tag anchor tables).

    If neither anchor is present, the element is appended at the end —
    that is a position Word accepts when the file is otherwise sparse,
    and it preserves the historical behaviour of
    ``enable_track_changes`` for already-flat settings files.

    The function takes ``local_name`` so callers can place any of the
    ordered CT_Settings children supported by ``_ANCHOR_TABLES`` with
    one routine. Today: ``"trackRevisions"`` (the actual Track Changes
    toggle, §17.15.1.92) and ``"documentProtection"`` (§17.15.1.29).
    Tags not in the table fall back to append at the end.
    """
    if not _LXML_AVAILABLE:  # pragma: no cover
        raise ImportError(
            "lxml is required for scitex_msword._settings_order. "
            "Install via `pip install lxml`."
        )

    anchors = _ANCHOR_TABLES.get(local_name)
    if anchors is None:
        settings_el.append(new_el)
        return
    before_set = set(anchors[0])
    after_set = set(anchors[1])

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


def ensure_document_protection_for_tracked_changes(settings_el, make_w) -> None:
    """Ensure ``<w:documentProtection w:edit="trackedChanges" w:enforcement="0"/>``.

    Mirrors what desktop Word writes when the user toggles Track
    Changes on (proj-grant draft_v39 reference). The element is
    informational (``enforcement=0`` = state-only, not locked) but
    matching Word's emission improves round-trip compatibility.

    ``make_w`` is the caller's ``_make_w_element``-style factory so
    this module stays independent of ``track_changes`` imports.
    """
    if not _LXML_AVAILABLE:  # pragma: no cover
        raise ImportError(
            "lxml is required for scitex_msword._settings_order."
        )
    W_TAG = f"{{{_W_NS}}}documentProtection"

    existing = [c for c in settings_el if c.tag == W_TAG]
    if existing:
        target = existing[0]
        target.set(f"{{{_W_NS}}}edit", "trackedChanges")
        target.set(f"{{{_W_NS}}}enforcement", "0")
        for dup in existing[1:]:
            settings_el.remove(dup)
        return

    new = make_w("documentProtection", edit="trackedChanges", enforcement="0")
    insert_in_settings_order(settings_el, new, "documentProtection")


__all__ = [
    "insert_in_settings_order",
    "ensure_document_protection_for_tracked_changes",
]


# EOF
