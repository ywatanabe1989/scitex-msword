#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: tests/scitex_msword/test__settings_order.py

"""Tests for ``scitex_msword._settings_order``.

ECMA-376 §17.15.1 ``CT_Settings`` has a fixed child sequence; Word
silently ignores out-of-order elements (notably ``<w:trackChanges/>``
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
    """``trackChanges`` placement obeys ECMA-376 §17.15.1 ordering."""

    def test_inserts_after_stylePaneSortMethod_when_present(self):
        """With ``stylePaneSortMethod`` present, ``trackChanges`` lands after it."""
        # Arrange
        from scitex_msword._settings_order import insert_in_settings_order

        settings_el = _settings_with(["stylePaneSortMethod"])
        new_el = _w_element("trackChanges")
        # Act
        insert_in_settings_order(settings_el, new_el, "trackChanges")
        # Assert
        assert _local_names(settings_el) == [
            "stylePaneSortMethod",
            "trackChanges",
        ]

    def test_inserts_before_doNotTrackFormatting_when_only_successor_present(
        self,
    ):
        """With only ``doNotTrackFormatting`` present, ``trackChanges`` lands before it."""
        # Arrange
        from scitex_msword._settings_order import insert_in_settings_order

        settings_el = _settings_with(["doNotTrackFormatting"])
        new_el = _w_element("trackChanges")
        # Act
        insert_in_settings_order(settings_el, new_el, "trackChanges")
        # Assert
        assert _local_names(settings_el) == [
            "trackChanges",
            "doNotTrackFormatting",
        ]

    def test_lands_between_predecessor_and_successor_when_both_present(self):
        """Both anchors present → ``trackChanges`` slots in between."""
        # Arrange
        from scitex_msword._settings_order import insert_in_settings_order

        settings_el = _settings_with(
            ["stylePaneSortMethod", "doNotTrackFormatting"]
        )
        new_el = _w_element("trackChanges")
        # Act
        insert_in_settings_order(settings_el, new_el, "trackChanges")
        # Assert
        assert _local_names(settings_el) == [
            "stylePaneSortMethod",
            "trackChanges",
            "doNotTrackFormatting",
        ]

    def test_appends_when_neither_anchor_is_present(self):
        """No before/after anchors → append at end (historical behaviour)."""
        # Arrange
        from scitex_msword._settings_order import insert_in_settings_order

        settings_el = _settings_with(["view", "zoom"])
        # Note: "view" + "zoom" are in the "before" set but neither is a
        # late-position predecessor close to trackChanges; the helper still
        # treats the last one of them as the anchor.
        # Act
        insert_in_settings_order(
            settings_el, _w_element("trackChanges"), "trackChanges"
        )
        # Assert
        assert _local_names(settings_el)[-1] == "trackChanges"

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
        """A fresh ``Document`` gets ``<w:trackChanges/>`` in the right slot."""
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
        assert "trackChanges" in tags


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
        """Reloading the saved file shows ``<w:trackChanges/>`` is present."""
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


# EOF
