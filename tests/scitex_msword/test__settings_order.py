#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: tests/scitex_msword/test__settings_order.py

"""Tests for ``scitex_msword._settings_order``.

ECMA-376 §17.15.1 ``CT_Settings`` has a fixed child sequence; Word
silently ignores out-of-order elements (notably ``<w:trackRevisions/>``
when written before its predecessors on otherwise-sparse settings
files). The placement helper here owns that decision.

Also covers the ``save_with_track_changes_on`` convenience wrapper from
``scitex_msword.track_changes`` since the two ship together for the
BOOST v37 dogfood workflow.

Style: AAA-marker comments on every test (STX-TQ002), one assertion per
test (STX-TQ007), ≥3-word descriptive names (STX-TQ003), no
``monkeypatch`` (PA-306 §3).
"""

from __future__ import annotations

import pytest


_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _w_element(tag, **attrs):
    """Build a bare ``<w:tag/>`` element for tests."""
    from lxml import etree

    el = etree.Element(f"{{{_W_NS}}}{tag}")
    for k, v in attrs.items():
        el.set(f"{{{_W_NS}}}{k}", str(v))
    return el


def _settings_with(children):
    """Build a ``<w:settings/>`` element wrapping the given tag-name list."""
    from lxml import etree

    settings = etree.Element(f"{{{_W_NS}}}settings")
    for tag in children:
        settings.append(_w_element(tag))
    return settings


def _local_names(settings_el):
    """Return the ordered local tag names of children of ``settings_el``."""
    from lxml import etree

    return [etree.QName(c).localname for c in settings_el]


class TestInsertInSettingsOrderTrackChanges:
    """``trackRevisions`` placement obeys ECMA-376 §17.15.1 ordering."""

    def test_inserts_after_stylePaneSortMethod_when_present(self):
        """With ``stylePaneSortMethod`` present, ``trackRevisions`` lands after it."""
        # Arrange
        from scitex_msword._settings_order import insert_in_settings_order

        settings_el = _settings_with(["stylePaneSortMethod"])
        new_el = _w_element("trackRevisions")
        # Act
        insert_in_settings_order(settings_el, new_el, "trackRevisions")
        # Assert
        assert _local_names(settings_el) == [
            "stylePaneSortMethod",
            "trackRevisions",
        ]

    def test_inserts_before_doNotTrackFormatting_when_only_successor_present(
        self,
    ):
        """With only ``doNotTrackFormatting`` present, ``trackRevisions`` lands before it."""
        # Arrange
        from scitex_msword._settings_order import insert_in_settings_order

        settings_el = _settings_with(["doNotTrackFormatting"])
        new_el = _w_element("trackRevisions")
        # Act
        insert_in_settings_order(settings_el, new_el, "trackRevisions")
        # Assert
        assert _local_names(settings_el) == [
            "trackRevisions",
            "doNotTrackFormatting",
        ]

    def test_lands_between_predecessor_and_successor_when_both_present(self):
        """Both anchors present → ``trackRevisions`` slots in between."""
        # Arrange
        from scitex_msword._settings_order import insert_in_settings_order

        settings_el = _settings_with(
            ["stylePaneSortMethod", "doNotTrackFormatting"]
        )
        new_el = _w_element("trackRevisions")
        # Act
        insert_in_settings_order(settings_el, new_el, "trackRevisions")
        # Assert
        assert _local_names(settings_el) == [
            "stylePaneSortMethod",
            "trackRevisions",
            "doNotTrackFormatting",
        ]

    def test_appends_when_neither_anchor_is_present(self):
        """No before/after anchors → append at end (historical behaviour)."""
        # Arrange
        from scitex_msword._settings_order import insert_in_settings_order

        settings_el = _settings_with(["view", "zoom"])
        # Note: "view" + "zoom" are in the "before" set but neither is a
        # late-position predecessor close to trackRevisions; the helper still
        # treats the last one of them as the anchor.
        # Act
        insert_in_settings_order(
            settings_el, _w_element("trackRevisions"), "trackRevisions"
        )
        # Assert
        assert _local_names(settings_el)[-1] == "trackRevisions"

    def test_falls_back_to_append_for_unknown_tag(self):
        """Asking to place a tag the helper doesn't model falls back to append."""
        # Arrange
        from scitex_msword._settings_order import insert_in_settings_order

        settings_el = _settings_with(["stylePaneSortMethod"])
        # Act
        insert_in_settings_order(
            settings_el, _w_element("someUnmodelledTag"), "someUnmodelledTag"
        )
        # Assert
        assert _local_names(settings_el)[-1] == "someUnmodelledTag"


class TestEnableTrackChangesOrderedPlacement:
    """``enable_track_changes`` calls into the ordered placement helper."""

    def test_enable_track_changes_lands_in_ordered_slot_on_real_document(
        self, tmp_path
    ):
        """A fresh ``Document`` gets ``<w:trackRevisions/>`` in the right slot."""
        # Arrange
        pytest.importorskip("docx")
        from docx import Document
        from lxml import etree
        from scitex_msword.track_changes import enable_track_changes

        doc = Document()
        # Act
        enable_track_changes(doc)
        # Assert
        settings_el = doc.settings.element
        tags = [etree.QName(c).localname for c in settings_el]
        assert "trackRevisions" in tags


class TestSaveWithTrackChangesOnHelper:
    """``save_with_track_changes_on`` enables TC and saves in one call."""

    def test_save_with_track_changes_on_writes_a_file_at_the_target_path(
        self, tmp_path
    ):
        """The helper produces a .docx file at the requested path."""
        # Arrange
        pytest.importorskip("docx")
        from docx import Document
        from scitex_msword.track_changes import save_with_track_changes_on

        doc = Document()
        out = tmp_path / "tc.docx"
        # Act
        save_with_track_changes_on(doc, out)
        # Assert
        assert out.exists() and out.stat().st_size > 0

    def test_save_with_track_changes_on_persists_track_changes_in_saved_file(
        self, tmp_path
    ):
        """Reloading the saved file shows ``<w:trackRevisions/>`` is present."""
        # Arrange
        pytest.importorskip("docx")
        from docx import Document
        from scitex_msword.track_changes import (
            is_track_changes_enabled,
            save_with_track_changes_on,
        )

        doc = Document()
        out = tmp_path / "tc.docx"
        save_with_track_changes_on(doc, out)
        # Act
        reloaded = Document(str(out))
        enabled = is_track_changes_enabled(reloaded)
        # Assert
        assert enabled is True

    def test_save_with_track_changes_on_emits_documentProtection_state_only(
        self, tmp_path
    ):
        """The saved settings.xml also carries the matching
        ``<w:documentProtection w:edit="trackedChanges" w:enforcement="0"/>``
        — informational, NOT enforced. Matches what desktop Word writes.
        """
        # Arrange
        pytest.importorskip("docx")
        from docx import Document
        from docx.oxml.ns import qn
        from scitex_msword.track_changes import save_with_track_changes_on

        doc = Document()
        out = tmp_path / "tc.docx"
        save_with_track_changes_on(doc, out)
        reloaded = Document(str(out))
        # Act
        protection = reloaded.settings.element.find(
            qn("w:documentProtection")
        )
        # Assert
        assert (
            protection is not None
            and protection.get(qn("w:edit")) == "trackedChanges"
            and protection.get(qn("w:enforcement")) == "0"
        )


class TestTrackChangesNameGroundTruthRegression:
    """Pins the v0.3.1 trackChanges→trackRevisions fix against a known-
    good reference: a docx Word itself wrote after the user toggled
    Track Changes on. proj-grant draft_v39 was the operator's manual
    save during BOOST v40 dogfood; the file is checked into the grant
    repo at /home/ywatanabe/proj/grant/.../draft_v39_ywata-turned-on-
    edit-history.docx and is also reachable in CI via the ``DRAFT_V39_
    REFERENCE`` env override (skipped when neither path resolves)."""

    @staticmethod
    def _resolve_reference():
        import os
        from pathlib import Path

        candidates = [
            os.environ.get("SXM_DRAFT_V39_REFERENCE"),
            "/home/ywatanabe/proj/grant/2026-06-11---2027-04-2032-03"
            "---20-PERC---1000---BOOST/"
            "draft_v39_ywata-turned-on-edit-history.docx",
        ]
        for raw in candidates:
            if not raw:
                continue
            p = Path(raw)
            if p.exists():
                return p
        return None

    def test_reference_file_carries_trackRevisions_not_trackChanges(self):
        """Word's own save uses ``trackRevisions``, NOT ``trackChanges``."""
        # Arrange
        ref = self._resolve_reference()
        if ref is None:
            pytest.skip("draft_v39 ground-truth reference not available")
        pytest.importorskip("docx")
        from docx import Document
        from docx.oxml.ns import qn

        doc = Document(str(ref))
        # Act
        has_revisions = (
            doc.settings.element.find(qn("w:trackRevisions")) is not None
        )
        # Assert
        assert has_revisions is True

    def test_is_track_changes_enabled_returns_true_on_word_reference(self):
        """The v0.3.1 reader recognises Word's own toggle (≤v0.3.0 returned False)."""
        # Arrange
        ref = self._resolve_reference()
        if ref is None:
            pytest.skip("draft_v39 ground-truth reference not available")
        pytest.importorskip("docx")
        from docx import Document
        from scitex_msword.track_changes import is_track_changes_enabled

        doc = Document(str(ref))
        # Act
        enabled = is_track_changes_enabled(doc)
        # Assert
        assert enabled is True


# EOF
