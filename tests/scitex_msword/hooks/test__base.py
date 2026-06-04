#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: tests/scitex_msword/hooks/test__base.py

"""Smoke tests for the ``sxm.hooks`` core dataclasses (``Phase``, ``Hook``,
``Issue``, ``HookContext``).

Style: AAA-marker comments on every test (STX-TQ002), one assertion per
test (STX-TQ007), ≥3-word descriptive names (STX-TQ003), no ``monkeypatch``
(PA-306 §3).
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestPhase:
    """``Phase`` is a 2-member string enum."""

    def test_phase_has_exactly_two_distinct_members(self):
        """``Phase`` exposes precisely ``pre_save`` and ``post_save``."""
        # Arrange
        from scitex_msword.hooks import Phase
        # Act
        values = {p.value for p in Phase}
        # Assert
        assert values == {"pre_save", "post_save"}

    def test_phase_pre_save_member_equals_string(self):
        """``Phase.PRE_SAVE`` compares equal to its string form."""
        # Arrange
        from scitex_msword.hooks import Phase
        # Act
        value = Phase.PRE_SAVE
        # Assert
        assert value == "pre_save"

    def test_phase_post_save_member_equals_string(self):
        """``Phase.POST_SAVE`` compares equal to its string form."""
        # Arrange
        from scitex_msword.hooks import Phase
        # Act
        value = Phase.POST_SAVE
        # Assert
        assert value == "post_save"


class TestHookDataclass:
    """``Hook`` is a frozen dataclass with optional ``fn``."""

    def _make_hook(self):
        from scitex_msword.hooks import Hook, Phase

        return Hook(
            id="SXM-EX001",
            phase=Phase.PRE_SAVE,
            severity="info",
            category="example",
            message="m",
            suggestion="s",
        )

    def test_hook_instance_is_frozen_against_mutation(self):
        """Assigning to a field on a built ``Hook`` raises."""
        # Arrange
        hook = self._make_hook()
        # Act
        # Assert
        with pytest.raises(Exception):
            hook.id = "other"  # type: ignore[misc]

    def test_hook_fn_field_defaults_to_none_when_omitted(self):
        """``Hook(...)`` without ``fn=`` leaves the attribute as ``None``."""
        # Arrange
        hook = self._make_hook()
        # Act
        fn = hook.fn
        # Assert
        assert fn is None


class TestIssueException:
    """``Issue`` is an ``Exception`` subclass with structured fields."""

    def test_issue_is_a_subclass_of_exception(self):
        """``Issue`` inherits from the built-in ``Exception``."""
        # Arrange
        from scitex_msword.hooks import Issue
        # Act
        is_subclass = issubclass(Issue, Exception)
        # Assert
        assert is_subclass is True

    def _raise_and_capture_issue(self):
        """Helper: raise an ``Issue`` with fixed fields and return the caught instance."""
        from scitex_msword.hooks import Issue

        try:
            raise Issue(
                hook_id="X-001",
                severity="error",
                location="loc",
                message="m",
                suggestion="s",
            )
        except Issue as caught:
            return caught

    def test_issue_raise_then_catch_preserves_hook_id(self):
        """Raising an ``Issue`` and catching it preserves ``hook_id``."""
        # Arrange
        # (Issue is constructed inside the helper below.)
        # Act
        caught = self._raise_and_capture_issue()
        # Assert
        assert caught.hook_id == "X-001"

    def test_issue_raise_then_catch_preserves_severity(self):
        """Raising an ``Issue`` and catching it preserves ``severity``."""
        # Arrange
        # (Issue is constructed inside the helper below.)
        # Act
        caught = self._raise_and_capture_issue()
        # Assert
        assert caught.severity == "error"

    def test_issue_raise_then_catch_preserves_location(self):
        """Raising an ``Issue`` and catching it preserves ``location``."""
        # Arrange
        # (Issue is constructed inside the helper below.)
        # Act
        caught = self._raise_and_capture_issue()
        # Assert
        assert caught.location == "loc"

    def test_issue_raise_then_catch_preserves_message(self):
        """Raising an ``Issue`` and catching it preserves ``message``."""
        # Arrange
        # (Issue is constructed inside the helper below.)
        # Act
        caught = self._raise_and_capture_issue()
        # Assert
        assert caught.message == "m"

    def test_issue_raise_then_catch_preserves_suggestion(self):
        """Raising an ``Issue`` and catching it preserves ``suggestion``."""
        # Arrange
        # (Issue is constructed inside the helper below.)
        # Act
        caught = self._raise_and_capture_issue()
        # Assert
        assert caught.suggestion == "s"

    def test_issue_str_form_includes_hook_id_and_location_and_message(self):
        """``str(Issue(...))`` embeds the ``hook_id``, ``location``, and ``message``."""
        # Arrange
        from scitex_msword.hooks import Issue

        issue = Issue(
            hook_id="X-001",
            severity="warning",
            location="L",
            message="M",
        )
        # Act
        rendered = str(issue)
        # Assert
        assert "X-001" in rendered and "L" in rendered and "M" in rendered


class TestHookContextDefaults:
    """``HookContext`` constructor defaults are stable."""

    def test_hookcontext_default_profile_is_none(self):
        """When constructed only with ``doc``, ``profile`` defaults to ``None``."""
        # Arrange
        from scitex_msword.hooks import HookContext
        # Act
        ctx = HookContext(doc=object())
        # Assert
        assert ctx.profile is None

    def test_hookcontext_default_path_is_a_path_instance(self):
        """When constructed only with ``doc``, ``path`` is a ``Path`` instance."""
        # Arrange
        from scitex_msword.hooks import HookContext
        # Act
        ctx = HookContext(doc=object())
        # Assert
        assert isinstance(ctx.path, Path)

    def test_hookcontext_default_config_is_empty_dict(self):
        """When constructed only with ``doc``, ``config`` defaults to ``{}``."""
        # Arrange
        from scitex_msword.hooks import HookContext
        # Act
        ctx = HookContext(doc=object())
        # Assert
        assert ctx.config == {}


class TestHookContextElementFor:
    """``HookContext.element_for`` walks ``doc.part.package.parts`` by name."""

    def test_element_for_raises_attribute_error_on_plain_object(self):
        """A bare ``object()`` doc lacks the walk path and raises ``AttributeError``."""
        # Arrange
        from scitex_msword.hooks import HookContext

        ctx = HookContext(doc=object())
        # Act
        # Assert
        with pytest.raises(AttributeError):
            ctx.element_for("/word/settings.xml")

    def test_element_for_resolves_walks_doc_part_package_parts_by_name(self):
        """When the walk path exists, ``element_for`` returns ``part.element``."""
        # Arrange
        from scitex_msword.hooks import HookContext

        class _Element:
            pass

        sentinel = _Element()

        class _Part:
            element = sentinel

        class _Package:
            parts = {"/word/settings.xml": _Part()}

        class _DocPart:
            package = _Package()

        class _Doc:
            part = _DocPart()

        ctx = HookContext(doc=_Doc())
        # Act
        result = ctx.element_for("/word/settings.xml")
        # Assert
        assert result is sentinel


# EOF
