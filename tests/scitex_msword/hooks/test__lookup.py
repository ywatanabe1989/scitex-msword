#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: tests/scitex_msword/hooks/test__lookup.py

"""Tests for ``sxm.hooks._lookup`` (builtins + entry-points + project-local).

Entry-point coverage uses a tiny stub for ``_iter_entry_points`` so the
test never depends on installed distributions. State mutated here
(``_builtins.ALL_HOOKS`` and ``_lookup._iter_entry_points``) is
snapshotted by the autouse ``_clean_hooks_state`` fixture in
``conftest.py`` and restored after every test — no ``monkeypatch``
needed (PA-306 §3).

Style: AAA-marker comments on every test (STX-TQ002), one assertion per
test (STX-TQ007), ≥3-word descriptive names (STX-TQ003).
"""

from __future__ import annotations

from pathlib import Path

import pytest


def _make_hook(hook_id, *, category="ex"):
    """Helper: build a minimal valid ``Hook`` with a no-op ``fn``."""
    from scitex_msword.hooks import Hook, Phase

    return Hook(
        id=hook_id,
        phase=Phase.PRE_SAVE,
        severity="info",
        category=category,
        message="m",
        suggestion="s",
        fn=lambda doc, ctx: None,
    )


def _install_builtin(hook):
    """Helper: temporarily insert ``hook`` into ``_builtins.ALL_HOOKS``.

    The autouse ``_clean_hooks_state`` fixture restores the dict after
    every test, so callers do not need to clean up themselves.
    """
    from scitex_msword.hooks import _builtins

    _builtins.ALL_HOOKS[hook.id] = hook


def _install_iter_entry_points(stub):
    """Helper: replace ``_lookup._iter_entry_points`` with ``stub``.

    The autouse ``_clean_hooks_state`` fixture restores the original
    callable after every test.
    """
    from scitex_msword.hooks import _lookup

    _lookup._iter_entry_points = stub


class TestBuiltinsOnly:
    """H1 ships zero builtins; lookup against the empty registry."""

    def test_h1_release_ships_no_builtin_hooks(self):
        """H1 deliberately ships zero builtins (guard against silent additions)."""
        # Arrange
        from scitex_msword.hooks._builtins import ALL_HOOKS
        # Act
        contents = dict(ALL_HOOKS)
        # Assert
        assert contents == {}

    def test_lookup_returns_none_for_unknown_hook_id(self):
        """Looking up an unregistered id returns ``None`` rather than raising."""
        # Arrange
        from scitex_msword.hooks import lookup
        # Act
        result = lookup("DOES-NOT-EXIST")
        # Assert
        assert result is None

    def test_lookup_resolves_a_temporarily_installed_builtin(self):
        """A hook inserted into ``_builtins.ALL_HOOKS`` is resolvable by id."""
        # Arrange
        from scitex_msword.hooks import lookup, reset_cache

        hook = _make_hook("SXM-BUILTIN")
        _install_builtin(hook)
        reset_cache()
        # Act
        resolved = lookup("SXM-BUILTIN")
        # Assert
        assert resolved is hook


class TestProjectLocalDiscovery:
    """``.scitex/msword/hooks/*.py`` is discovered by walking parents."""

    def test_walk_up_from_project_root_finds_registered_hook(
        self, project_tree_with_hook, chdir_to
    ):
        """``register(Hook(...))`` in ``.scitex/msword/hooks/`` is resolvable."""
        # Arrange
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
        # Act
        found = lookup("GRANT-NB001")
        # Assert
        assert found is not None and found.id == "GRANT-NB001"

    def test_walk_up_from_nested_subdirectory_finds_registered_hook(
        self, project_tree_with_hook, chdir_to
    ):
        """Walking up several parent levels still resolves the project hook."""
        # Arrange
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
        # Act
        found = lookup("GRANT-SUB001")
        # Assert
        assert found is not None

    def test_underscore_prefixed_hook_files_are_skipped_on_discovery(
        self, project_tree_with_hook, chdir_to
    ):
        """Hook modules whose filename starts with ``_`` are not imported."""
        # Arrange
        from scitex_msword.hooks import lookup, reset_cache

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
        # Act
        resolved = lookup("GRANT-PRIVATE")
        # Assert
        assert resolved is None


class TestOverridePrecedence:
    """Project-local > entry-point > builtin (highest wins on collisions)."""

    def test_project_local_hook_overrides_a_builtin_with_same_id(
        self, project_tree_with_hook, chdir_to
    ):
        """A same-id project hook wins over a builtin (project wins)."""
        # Arrange
        from scitex_msword.hooks import lookup, reset_cache

        _install_builtin(_make_hook("SXM-COLLIDE", category="builtin"))

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
        # Act
        resolved = lookup("SXM-COLLIDE")
        # Assert
        assert resolved is not None and resolved.category == "project"

    def test_entry_point_hook_overrides_a_builtin_with_same_id(self):
        """A same-id entry-point hook wins over a builtin (plugin wins)."""
        # Arrange
        from scitex_msword.hooks import lookup, reset_cache

        _install_builtin(_make_hook("SXM-EP", category="builtin"))
        plugin = _make_hook("SXM-EP", category="plugin")

        class _EP:
            name = "fake"

            def load(self_inner):
                return plugin

        _install_iter_entry_points(lambda group: [_EP()])
        reset_cache()
        # Act
        resolved = lookup("SXM-EP")
        # Assert
        assert resolved is not None and resolved.category == "plugin"

    def test_project_local_hook_overrides_an_entry_point_with_same_id(
        self, project_tree_with_hook, chdir_to
    ):
        """A same-id project hook wins over an entry-point hook (project wins)."""
        # Arrange
        from scitex_msword.hooks import lookup, reset_cache

        plugin = _make_hook("SXM-WIN", category="plugin")

        class _EP:
            name = "fake"

            def load(self_inner):
                return plugin

        _install_iter_entry_points(lambda group: [_EP()])

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
        # Act
        resolved = lookup("SXM-WIN")
        # Assert
        assert resolved is not None and resolved.category == "project"


class TestEntryPointPayloadCoercion:
    """Entry-point ``load()`` may return a Hook, a dict, or garbage."""

    def test_dict_payload_from_entry_point_is_unpacked_by_id(self):
        """A ``dict`` payload's first id is resolvable after coercion."""
        # Arrange
        from scitex_msword.hooks import lookup, reset_cache

        bundle = {
            "SXM-A": _make_hook("SXM-A", category="bundle"),
            "SXM-B": _make_hook("SXM-B", category="bundle"),
        }

        class _EP:
            name = "bundle"

            def load(self_inner):
                return bundle

        _install_iter_entry_points(lambda group: [_EP()])
        reset_cache()
        # Act
        resolved = lookup("SXM-A")
        # Assert
        assert resolved is not None

    def test_dict_payload_second_entry_is_also_resolvable(self):
        """Both keys of a ``dict`` payload are independently resolvable."""
        # Arrange
        from scitex_msword.hooks import lookup, reset_cache

        bundle = {
            "SXM-A": _make_hook("SXM-A", category="bundle"),
            "SXM-B": _make_hook("SXM-B", category="bundle"),
        }

        class _EP:
            name = "bundle"

            def load(self_inner):
                return bundle

        _install_iter_entry_points(lambda group: [_EP()])
        reset_cache()
        # Act
        resolved = lookup("SXM-B")
        # Assert
        assert resolved is not None

    def test_garbage_payload_does_not_break_subsequent_lookups(self):
        """A non-Hook/non-dict/non-iterable payload is logged and skipped."""
        # Arrange
        from scitex_msword.hooks import lookup, reset_cache

        class _EP:
            name = "garbage"

            def load(self_inner):
                return 42  # not a Hook / dict / iterable

        _install_iter_entry_points(lambda group: [_EP()])
        reset_cache()
        # Act
        result = lookup("DOES-NOT-EXIST")
        # Assert
        assert result is None


class TestResetCache:
    """``reset_cache()`` drops the memoised resolution."""

    def test_reset_cache_makes_newly_installed_builtin_visible(self):
        """A builtin added AFTER an initial probe becomes visible after reset."""
        # Arrange
        from scitex_msword.hooks import lookup, reset_cache

        # Prime the cache with a miss (no assertion here — STX-TQ007).
        lookup("anything")

        hook = _make_hook("SXM-NEW")
        _install_builtin(hook)
        # Act
        reset_cache()
        resolved = lookup("SXM-NEW")
        # Assert
        assert resolved is hook


# EOF
