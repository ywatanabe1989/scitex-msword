#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: tests/hooks/test_base.py

"""Smoke tests for the ``sxm.hooks`` core dataclasses."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestPhase:
    def test_phase_has_exactly_two_members(self):
        from scitex_msword.hooks import Phase

        assert {p.value for p in Phase} == {"pre_save", "post_save"}

    def test_phase_is_string_enum(self):
        from scitex_msword.hooks import Phase

        assert Phase.PRE_SAVE == "pre_save"
        assert Phase.POST_SAVE == "post_save"


class TestHook:
    def test_hook_is_frozen(self):
        from scitex_msword.hooks import Hook, Phase

        h = Hook(
            id="SXM-EX001",
            phase=Phase.PRE_SAVE,
            severity="info",
            category="example",
            message="m",
            suggestion="s",
        )
        with pytest.raises(Exception):
            h.id = "other"  # type: ignore[misc]

    def test_hook_fn_optional_at_construction(self):
        from scitex_msword.hooks import Hook, Phase

        h = Hook(
            id="SXM-EX001",
            phase=Phase.PRE_SAVE,
            severity="info",
            category="example",
            message="m",
            suggestion="s",
        )
        assert h.fn is None


class TestIssue:
    def test_issue_is_an_exception(self):
        from scitex_msword.hooks import Issue

        assert issubclass(Issue, Exception)

    def test_issue_can_be_raised_and_caught(self):
        from scitex_msword.hooks import Issue

        with pytest.raises(Issue) as exc_info:
            raise Issue(
                hook_id="X-001",
                severity="error",
                location="loc",
                message="m",
                suggestion="s",
            )
        assert exc_info.value.hook_id == "X-001"
        assert exc_info.value.severity == "error"
        assert exc_info.value.location == "loc"
        assert exc_info.value.message == "m"
        assert exc_info.value.suggestion == "s"

    def test_issue_str_includes_hook_id_and_location(self):
        from scitex_msword.hooks import Issue

        issue = Issue(
            hook_id="X-001", severity="warning", location="L", message="M",
        )
        s = str(issue)
        assert "X-001" in s and "L" in s and "M" in s


class TestHookContext:
    def test_hookcontext_defaults(self):
        from scitex_msword.hooks import HookContext

        ctx = HookContext(doc=object())
        assert ctx.profile is None
        assert isinstance(ctx.path, Path)
        assert ctx.config == {}

    def test_element_for_attribute_error_on_plain_object(self):
        from scitex_msword.hooks import HookContext

        ctx = HookContext(doc=object())
        with pytest.raises(AttributeError):
            ctx.element_for("/word/settings.xml")

    def test_element_for_walks_doc_part_package_parts(self):
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
        assert ctx.element_for("/word/settings.xml") is sentinel


# EOF
