#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: tests/scitex_msword/hooks/test__dispatch.py

"""Tests for the ``register`` decorator and ``run_phase`` dispatcher.

Style: AAA-marker comments on every test (STX-TQ002), one assertion per
test (STX-TQ007), ≥3-word descriptive names (STX-TQ003), no
``monkeypatch`` (PA-306 §3).
"""

from __future__ import annotations

from pathlib import Path

import pytest


def _make_pre_save_hook(hook_id, *, fn=None):
    from scitex_msword.hooks import Hook, Phase

    return Hook(
        id=hook_id,
        phase=Phase.PRE_SAVE,
        severity="info",
        category="ex",
        message="m",
        suggestion="s",
        fn=fn,
    )


def _make_post_save_hook(hook_id, *, fn=None, severity="info"):
    from scitex_msword.hooks import Hook, Phase

    return Hook(
        id=hook_id,
        phase=Phase.POST_SAVE,
        severity=severity,
        category="ex",
        message="m",
        suggestion="s",
        fn=fn,
    )


class TestRegisterDecorator:
    """``register`` works as both decorator and direct callable."""

    def test_decorator_form_stitches_fn_when_hook_fn_is_none(self):
        """``@register(Hook(...))`` over a function attaches the function as ``fn``."""
        # Arrange
        from scitex_msword.hooks import register
        from scitex_msword.hooks._dispatch import _REGISTRY

        # Act
        @register(_make_pre_save_hook("SXM-EX001"))
        def my_hook(doc, ctx):
            return None

        # Assert
        assert _REGISTRY["SXM-EX001"].fn is my_hook

    def test_callable_form_with_explicit_fn_registers_the_callable(self):
        """``register(Hook(..., fn=f))`` registers the supplied callable."""
        # Arrange
        from scitex_msword.hooks import register
        from scitex_msword.hooks._dispatch import _REGISTRY

        def fn(doc, ctx):
            return None

        # Act
        register(_make_pre_save_hook("SXM-EX002", fn=fn))
        # Assert
        assert _REGISTRY["SXM-EX002"].fn is fn

    def test_reregistering_same_id_overwrites_prior_registration(self):
        """Calling ``register`` twice with the same id keeps the latest ``fn``."""
        # Arrange
        from scitex_msword.hooks import register
        from scitex_msword.hooks._dispatch import _REGISTRY

        def fn1(doc, ctx):
            return None

        def fn2(doc, ctx):
            return None

        for fn in (fn1, fn2):
            register(_make_pre_save_hook("SXM-EX003", fn=fn))
        # Act
        active_fn = _REGISTRY["SXM-EX003"].fn
        # Assert
        assert active_fn is fn2


class TestRunPhasePreSave:
    """``run_phase(PRE_SAVE, ...)`` invokes enabled hooks in order."""

    def test_run_phase_pre_save_runs_hooks_in_declaration_order(self):
        """Enabled hooks fire in the order they were ``register``-ed."""
        # Arrange
        from scitex_msword.hooks import HookContext, Phase, register, run_phase

        calls: list[str] = []

        def make(name):
            def _fn(doc, ctx):
                calls.append(name)

            return _fn

        for name in ("A", "B", "C"):
            register(_make_pre_save_hook(f"SXM-{name}", fn=make(name)))
        ctx = HookContext(
            doc=object(),
            config={"hooks": {"enable": ["SXM-A", "SXM-B", "SXM-C"]}},
        )
        # Act
        run_phase(Phase.PRE_SAVE, ctx.doc, ctx)
        # Assert
        assert calls == ["A", "B", "C"]

    def test_run_phase_with_no_enable_list_runs_all_registered_hooks(self):
        """Omitting ``hooks.enable`` runs every registered hook for the phase."""
        # Arrange
        from scitex_msword.hooks import HookContext, Phase, register, run_phase

        calls: list[str] = []
        for name in ("A", "B"):
            register(
                _make_pre_save_hook(
                    f"SXM-{name}",
                    fn=lambda doc, ctx, n=name: calls.append(n),
                )
            )
        ctx = HookContext(doc=object(), config={})
        # Act
        run_phase(Phase.PRE_SAVE, ctx.doc, ctx)
        # Assert
        assert set(calls) == {"A", "B"}

    def test_run_phase_pre_save_fails_loud_on_first_raising_hook(self):
        """A hook that raises stops the chain — subsequent hooks do not fire."""
        # Arrange
        from scitex_msword.hooks import HookContext, Phase, register, run_phase

        calls: list[str] = []

        def good(doc, ctx):
            calls.append("good")

        def boom(doc, ctx):
            calls.append("boom")
            raise RuntimeError("nope")

        def never(doc, ctx):
            calls.append("never")

        for hid, fn in (("SXM-A", good), ("SXM-B", boom), ("SXM-C", never)):
            register(_make_pre_save_hook(hid, fn=fn))
        ctx = HookContext(
            doc=object(),
            config={"hooks": {"enable": ["SXM-A", "SXM-B", "SXM-C"]}},
        )
        # Act / Assert
        with pytest.raises(RuntimeError, match="nope"):
            run_phase(Phase.PRE_SAVE, ctx.doc, ctx)

    def test_run_phase_pre_save_skips_remainder_after_raising_hook(self):
        """The post-condition of fail-loud: ``never`` is never called."""
        # Arrange
        from scitex_msword.hooks import HookContext, Phase, register, run_phase

        calls: list[str] = []

        def good(doc, ctx):
            calls.append("good")

        def boom(doc, ctx):
            calls.append("boom")
            raise RuntimeError("nope")

        def never(doc, ctx):
            calls.append("never")

        for hid, fn in (("SXM-A", good), ("SXM-B", boom), ("SXM-C", never)):
            register(_make_pre_save_hook(hid, fn=fn))
        ctx = HookContext(
            doc=object(),
            config={"hooks": {"enable": ["SXM-A", "SXM-B", "SXM-C"]}},
        )
        # Act
        try:
            run_phase(Phase.PRE_SAVE, ctx.doc, ctx)
        except RuntimeError:
            pass
        # Assert
        assert calls == ["good", "boom"]

    def test_run_phase_silently_ignores_unknown_id_in_enable_list(self):
        """Unknown ids in ``hooks.enable`` do not raise — they are skipped."""
        # Arrange
        from scitex_msword.hooks import HookContext, Phase, register, run_phase

        calls: list[str] = []
        register(
            _make_pre_save_hook(
                "SXM-A", fn=lambda doc, ctx: calls.append("A")
            )
        )
        ctx = HookContext(
            doc=object(),
            config={"hooks": {"enable": ["SXM-MISSING", "SXM-A"]}},
        )
        # Act
        run_phase(Phase.PRE_SAVE, ctx.doc, ctx)
        # Assert
        assert calls == ["A"]

    def test_run_phase_pre_save_filters_out_post_save_phase_hooks(self):
        """A ``POST_SAVE`` hook is excluded from a ``PRE_SAVE`` invocation."""
        # Arrange
        from scitex_msword.hooks import HookContext, Phase, register, run_phase

        calls: list[str] = []
        register(
            _make_pre_save_hook(
                "SXM-PRE", fn=lambda doc, ctx: calls.append("pre")
            )
        )
        register(
            _make_post_save_hook(
                "SXM-POST",
                fn=lambda doc, ctx, *, out_path: calls.append("post"),
            )
        )
        ctx = HookContext(
            doc=object(),
            config={"hooks": {"enable": ["SXM-PRE", "SXM-POST"]}},
        )
        # Act
        run_phase(Phase.PRE_SAVE, ctx.doc, ctx)
        # Assert
        assert calls == ["pre"]


class TestRunPhasePostSave:
    """``run_phase(POST_SAVE, ...)`` requires ``out_path`` and runs hooks."""

    def test_run_phase_post_save_without_out_path_raises_assertion(self):
        """Calling ``run_phase(POST_SAVE, ...)`` without ``out_path=`` raises."""
        # Arrange
        from scitex_msword.hooks import HookContext, Phase, run_phase

        ctx = HookContext(doc=object(), config={})
        # Act / Assert
        with pytest.raises(AssertionError):
            run_phase(Phase.POST_SAVE, ctx.doc, ctx)

    def test_run_phase_post_save_forwards_out_path_to_hook_callable(
        self, tmp_path
    ):
        """Post-save hooks receive ``out_path=`` as a keyword argument."""
        # Arrange
        from scitex_msword.hooks import HookContext, Phase, register, run_phase

        seen: list[Path] = []

        def post(doc, ctx, *, out_path):
            seen.append(out_path)

        register(_make_post_save_hook("SXM-POST", fn=post))
        ctx = HookContext(
            doc=object(), config={"hooks": {"enable": ["SXM-POST"]}}
        )
        target = tmp_path / "saved.docx"
        # Act
        run_phase(Phase.POST_SAVE, ctx.doc, ctx, out_path=target)
        # Assert
        assert seen == [target]

    def test_run_phase_post_save_aborts_remainder_when_hook_raises_issue(
        self, tmp_path
    ):
        """An ``Issue`` raised by a post-save hook stops subsequent hooks."""
        # Arrange
        from scitex_msword.hooks import (
            HookContext,
            Issue,
            Phase,
            register,
            run_phase,
        )

        ran: list[str] = []

        def first(doc, ctx, *, out_path):
            ran.append("first")
            raise Issue(
                hook_id="SXM-FIRST",
                severity="error",
                location="x.xml",
                message="boom",
                suggestion="fix",
            )

        def second(doc, ctx, *, out_path):
            ran.append("second")

        for hid, fn in (("SXM-FIRST", first), ("SXM-SECOND", second)):
            register(_make_post_save_hook(hid, fn=fn, severity="error"))
        ctx = HookContext(
            doc=object(),
            config={"hooks": {"enable": ["SXM-FIRST", "SXM-SECOND"]}},
        )
        # Act
        try:
            run_phase(
                Phase.POST_SAVE, ctx.doc, ctx, out_path=tmp_path / "f.docx"
            )
        except Issue:
            pass
        # Assert
        assert ran == ["first"]


class TestAllHooksByPhase:
    """``ALL_HOOKS_BY_PHASE`` buckets the live registry by phase."""

    def test_all_hooks_by_phase_lists_pre_save_registered_ids(self):
        """``ALL_HOOKS_BY_PHASE[Phase.PRE_SAVE]`` includes the pre-save hook id."""
        # Arrange
        from scitex_msword.hooks import (
            ALL_HOOKS_BY_PHASE,
            Phase,
            register,
        )

        register(
            _make_pre_save_hook("SXM-A", fn=lambda doc, ctx: None)
        )
        register(
            _make_post_save_hook(
                "SXM-B", fn=lambda doc, ctx, *, out_path: None
            )
        )
        # Act
        pre_ids = [h.id for h in ALL_HOOKS_BY_PHASE[Phase.PRE_SAVE]]
        # Assert
        assert pre_ids == ["SXM-A"]

    def test_all_hooks_by_phase_lists_post_save_registered_ids(self):
        """``ALL_HOOKS_BY_PHASE[Phase.POST_SAVE]`` includes the post-save hook id."""
        # Arrange
        from scitex_msword.hooks import (
            ALL_HOOKS_BY_PHASE,
            Phase,
            register,
        )

        register(
            _make_pre_save_hook("SXM-A", fn=lambda doc, ctx: None)
        )
        register(
            _make_post_save_hook(
                "SXM-B", fn=lambda doc, ctx, *, out_path: None
            )
        )
        # Act
        post_ids = [h.id for h in ALL_HOOKS_BY_PHASE[Phase.POST_SAVE]]
        # Assert
        assert post_ids == ["SXM-B"]


# EOF
