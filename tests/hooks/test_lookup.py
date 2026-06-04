#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: tests/hooks/test_lookup.py

"""Tests for ``sxm.hooks._lookup`` (builtins + entry-points + project-local).

Entry-point coverage uses a tiny stub for ``_iter_entry_points`` so the
test never depends on installed distributions.
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestBuiltinsOnly:
    def test_h1_ships_no_builtins(self):
        from scitex_msword.hooks._builtins import ALL_HOOKS

        # H1 deliberately ships zero builtins. Guard against silent
        # additions: H4/H5 must update this expectation alongside.
        assert ALL_HOOKS == {}

    def test_lookup_returns_none_for_unknown(self):
        from scitex_msword.hooks import lookup

        assert lookup("DOES-NOT-EXIST") is None

    def test_lookup_resolves_temporary_builtin(self, monkeypatch):
        from scitex_msword.hooks import Hook, Phase, lookup, reset_cache
        from scitex_msword.hooks import _builtins

        h = Hook(
            id="SXM-BUILTIN",
            phase=Phase.PRE_SAVE,
            severity="info",
            category="ex",
            message="m",
            suggestion="s",
            fn=lambda doc, ctx: None,
        )
        monkeypatch.setitem(_builtins.ALL_HOOKS, "SXM-BUILTIN", h)
        reset_cache()
        assert lookup("SXM-BUILTIN") is h


class TestProjectLocalDiscovery:
    def test_walk_up_finds_project_hooks(
        self, project_tree_with_hook, chdir_to
    ):
        from scitex_msword.hooks import lookup, reset_cache

        source = """
            from scitex_msword.hooks import Hook, Phase, register

            register(Hook(
                id="GRANT-NB001",
                phase=Phase.PRE_SAVE,
                severity="warning",
                category="audit",
                message="No-Borders rule",
                suggestion="Strip table borders before save",
                fn=lambda doc, ctx: None,
            ))
        """
        root = project_tree_with_hook("nb001", source)
        chdir_to(root)
        reset_cache()
        found = lookup("GRANT-NB001")
        assert found is not None
        assert found.id == "GRANT-NB001"

    def test_walk_up_finds_from_subdirectory(
        self, project_tree_with_hook, chdir_to, tmp_path
    ):
        from scitex_msword.hooks import lookup, reset_cache

        source = """
            from scitex_msword.hooks import Hook, Phase, register

            register(Hook(
                id="GRANT-SUB001",
                phase=Phase.PRE_SAVE,
                severity="info",
                category="audit",
                message="m",
                suggestion="s",
                fn=lambda doc, ctx: None,
            ))
        """
        root = project_tree_with_hook("sub001", source)
        nested = root / "deep" / "nested" / "dir"
        nested.mkdir(parents=True)
        chdir_to(nested)
        reset_cache()
        assert lookup("GRANT-SUB001") is not None

    def test_underscore_prefixed_files_are_ignored(
        self, project_tree_with_hook, chdir_to
    ):
        from scitex_msword.hooks import lookup, reset_cache

        # Files starting with `_` are conventionally private helpers.
        source = """
            from scitex_msword.hooks import Hook, Phase, register

            register(Hook(
                id="GRANT-PRIVATE",
                phase=Phase.PRE_SAVE,
                severity="info",
                category="audit",
                message="m",
                suggestion="s",
                fn=lambda doc, ctx: None,
            ))
        """
        root = project_tree_with_hook("_private", source)
        chdir_to(root)
        reset_cache()
        assert lookup("GRANT-PRIVATE") is None


class TestOverridePrecedence:
    def test_project_local_overrides_builtin(
        self, project_tree_with_hook, chdir_to, monkeypatch
    ):
        from scitex_msword.hooks import Hook, Phase, lookup, reset_cache
        from scitex_msword.hooks import _builtins

        builtin = Hook(
            id="SXM-COLLIDE",
            phase=Phase.PRE_SAVE,
            severity="info",
            category="builtin",
            message="builtin",
            suggestion="s",
            fn=lambda doc, ctx: None,
        )
        monkeypatch.setitem(_builtins.ALL_HOOKS, "SXM-COLLIDE", builtin)

        source = """
            from scitex_msword.hooks import Hook, Phase, register

            register(Hook(
                id="SXM-COLLIDE",
                phase=Phase.PRE_SAVE,
                severity="warning",
                category="project",
                message="project override",
                suggestion="s",
                fn=lambda doc, ctx: None,
            ))
        """
        root = project_tree_with_hook("override", source)
        chdir_to(root)
        reset_cache()
        resolved = lookup("SXM-COLLIDE")
        assert resolved is not None
        assert resolved.category == "project"
        assert resolved.message == "project override"

    def test_entry_point_overrides_builtin(self, monkeypatch):
        from scitex_msword.hooks import Hook, Phase, lookup, reset_cache
        from scitex_msword.hooks import _builtins, _lookup

        builtin = Hook(
            id="SXM-EP",
            phase=Phase.PRE_SAVE,
            severity="info",
            category="builtin",
            message="builtin",
            suggestion="s",
            fn=lambda doc, ctx: None,
        )
        plugin = Hook(
            id="SXM-EP",
            phase=Phase.PRE_SAVE,
            severity="warning",
            category="plugin",
            message="plugin override",
            suggestion="s",
            fn=lambda doc, ctx: None,
        )
        monkeypatch.setitem(_builtins.ALL_HOOKS, "SXM-EP", builtin)

        class _EP:
            name = "fake"

            def load(self_inner):
                return plugin

        monkeypatch.setattr(_lookup, "_iter_entry_points", lambda group: [_EP()])
        reset_cache()
        resolved = lookup("SXM-EP")
        assert resolved is not None
        assert resolved.category == "plugin"

    def test_project_local_overrides_entry_point(
        self, project_tree_with_hook, chdir_to, monkeypatch
    ):
        from scitex_msword.hooks import Hook, Phase, lookup, reset_cache
        from scitex_msword.hooks import _lookup

        plugin = Hook(
            id="SXM-WIN",
            phase=Phase.PRE_SAVE,
            severity="info",
            category="plugin",
            message="plugin",
            suggestion="s",
            fn=lambda doc, ctx: None,
        )

        class _EP:
            name = "fake"

            def load(self_inner):
                return plugin

        monkeypatch.setattr(_lookup, "_iter_entry_points", lambda group: [_EP()])

        source = """
            from scitex_msword.hooks import Hook, Phase, register

            register(Hook(
                id="SXM-WIN",
                phase=Phase.PRE_SAVE,
                severity="error",
                category="project",
                message="project",
                suggestion="s",
                fn=lambda doc, ctx: None,
            ))
        """
        root = project_tree_with_hook("win", source)
        chdir_to(root)
        reset_cache()
        resolved = lookup("SXM-WIN")
        assert resolved is not None
        assert resolved.category == "project"


class TestEntryPointPayloadCoercion:
    def test_dict_payload_is_unpacked(self, monkeypatch):
        from scitex_msword.hooks import Hook, Phase, lookup, reset_cache
        from scitex_msword.hooks import _lookup

        bundle = {
            "SXM-A": Hook(
                id="SXM-A",
                phase=Phase.PRE_SAVE,
                severity="info",
                category="bundle",
                message="m",
                suggestion="s",
                fn=lambda doc, ctx: None,
            ),
            "SXM-B": Hook(
                id="SXM-B",
                phase=Phase.PRE_SAVE,
                severity="info",
                category="bundle",
                message="m",
                suggestion="s",
                fn=lambda doc, ctx: None,
            ),
        }

        class _EP:
            name = "bundle"

            def load(self_inner):
                return bundle

        monkeypatch.setattr(_lookup, "_iter_entry_points", lambda group: [_EP()])
        reset_cache()
        assert lookup("SXM-A") is not None
        assert lookup("SXM-B") is not None

    def test_garbage_payload_logged_and_skipped(self, monkeypatch):
        from scitex_msword.hooks import lookup, reset_cache
        from scitex_msword.hooks import _lookup

        class _EP:
            name = "garbage"

            def load(self_inner):
                return 42  # not a Hook / dict / iterable

        monkeypatch.setattr(_lookup, "_iter_entry_points", lambda group: [_EP()])
        reset_cache()
        # The lookup must succeed (return None) without raising.
        assert lookup("DOES-NOT-EXIST") is None


class TestResetCache:
    def test_reset_drops_cache(self, monkeypatch):
        from scitex_msword.hooks import Hook, Phase, lookup, reset_cache
        from scitex_msword.hooks import _builtins

        # Prime the cache.
        assert lookup("anything") is None

        h = Hook(
            id="SXM-NEW",
            phase=Phase.PRE_SAVE,
            severity="info",
            category="ex",
            message="m",
            suggestion="s",
            fn=lambda doc, ctx: None,
        )
        monkeypatch.setitem(_builtins.ALL_HOOKS, "SXM-NEW", h)
        # Without reset, the cache is stale.
        assert lookup("SXM-NEW") is None
        reset_cache()
        assert lookup("SXM-NEW") is h


# EOF
