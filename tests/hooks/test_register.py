#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 00:00:00
# File: tests/hooks/test_register.py

"""Tests for the ``register`` decorator and ``run_phase`` dispatcher."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestRegisterDecorator:
    def test_decorator_stitches_fn_when_none(self):
        from scitex_msword.hooks import Hook, Phase, register
        from scitex_msword.hooks._dispatch import _REGISTRY

        @register(
            Hook(
                id="SXM-EX001",
                phase=Phase.PRE_SAVE,
                severity="info",
                category="example",
                message="m",
                suggestion="s",
            )
        )
        def my_hook(doc, ctx):
            return None

        assert "SXM-EX001" in _REGISTRY
        assert _REGISTRY["SXM-EX001"].fn is my_hook

    def test_register_callable_form(self):
        from scitex_msword.hooks import Hook, Phase, register
        from scitex_msword.hooks._dispatch import _REGISTRY

        def fn(doc, ctx):
            return None

        register(
            Hook(
                id="SXM-EX002",
                phase=Phase.PRE_SAVE,
                severity="info",
                category="example",
                message="m",
                suggestion="s",
                fn=fn,
            )
        )
        assert _REGISTRY["SXM-EX002"].fn is fn

    def test_reregister_overwrites_prior(self):
        from scitex_msword.hooks import Hook, Phase, register
        from scitex_msword.hooks._dispatch import _REGISTRY

        def fn1(doc, ctx):
            return None

        def fn2(doc, ctx):
            return None

        for fn in (fn1, fn2):
            register(
                Hook(
                    id="SXM-EX003",
                    phase=Phase.PRE_SAVE,
                    severity="info",
                    category="example",
                    message="m",
                    suggestion="s",
                    fn=fn,
                )
            )
        assert _REGISTRY["SXM-EX003"].fn is fn2


class TestRunPhasePreSave:
    def test_runs_hooks_in_declaration_order(self):
        from scitex_msword.hooks import Hook, HookContext, Phase, register, run_phase

        calls: list[str] = []

        def make(name):
            def _fn(doc, ctx):
                calls.append(name)

            return _fn

        for name in ("A", "B", "C"):
            register(
                Hook(
                    id=f"SXM-{name}",
                    phase=Phase.PRE_SAVE,
                    severity="info",
                    category="ex",
                    message="m",
                    suggestion="s",
                    fn=make(name),
                )
            )
        ctx = HookContext(
            doc=object(),
            config={"hooks": {"enable": ["SXM-A", "SXM-B", "SXM-C"]}},
        )
        run_phase(Phase.PRE_SAVE, ctx.doc, ctx)
        assert calls == ["A", "B", "C"]

    def test_no_enable_list_runs_all_registered(self):
        from scitex_msword.hooks import Hook, HookContext, Phase, register, run_phase

        calls: list[str] = []
        for name in ("A", "B"):
            register(
                Hook(
                    id=f"SXM-{name}",
                    phase=Phase.PRE_SAVE,
                    severity="info",
                    category="ex",
                    message="m",
                    suggestion="s",
                    fn=lambda doc, ctx, n=name: calls.append(n),
                )
            )
        ctx = HookContext(doc=object(), config={})
        run_phase(Phase.PRE_SAVE, ctx.doc, ctx)
        assert set(calls) == {"A", "B"}

    def test_fails_loud_on_first_raise(self):
        from scitex_msword.hooks import Hook, HookContext, Phase, register, run_phase

        calls: list[str] = []

        def good(doc, ctx):
            calls.append("good")

        def boom(doc, ctx):
            calls.append("boom")
            raise RuntimeError("nope")

        def never(doc, ctx):
            calls.append("never")

        for hid, fn in (("SXM-A", good), ("SXM-B", boom), ("SXM-C", never)):
            register(
                Hook(
                    id=hid,
                    phase=Phase.PRE_SAVE,
                    severity="info",
                    category="ex",
                    message="m",
                    suggestion="s",
                    fn=fn,
                )
            )
        ctx = HookContext(
            doc=object(),
            config={"hooks": {"enable": ["SXM-A", "SXM-B", "SXM-C"]}},
        )
        with pytest.raises(RuntimeError, match="nope"):
            run_phase(Phase.PRE_SAVE, ctx.doc, ctx)
        assert calls == ["good", "boom"]  # "never" was skipped.

    def test_unknown_id_in_enable_is_ignored(self):
        from scitex_msword.hooks import Hook, HookContext, Phase, register, run_phase

        calls: list[str] = []
        register(
            Hook(
                id="SXM-A",
                phase=Phase.PRE_SAVE,
                severity="info",
                category="ex",
                message="m",
                suggestion="s",
                fn=lambda doc, ctx: calls.append("A"),
            )
        )
        ctx = HookContext(
            doc=object(),
            config={"hooks": {"enable": ["SXM-MISSING", "SXM-A"]}},
        )
        run_phase(Phase.PRE_SAVE, ctx.doc, ctx)
        assert calls == ["A"]

    def test_phase_mismatch_filtered_out(self):
        from scitex_msword.hooks import Hook, HookContext, Phase, register, run_phase

        calls: list[str] = []
        register(
            Hook(
                id="SXM-PRE",
                phase=Phase.PRE_SAVE,
                severity="info",
                category="ex",
                message="m",
                suggestion="s",
                fn=lambda doc, ctx: calls.append("pre"),
            )
        )
        register(
            Hook(
                id="SXM-POST",
                phase=Phase.POST_SAVE,
                severity="info",
                category="ex",
                message="m",
                suggestion="s",
                fn=lambda doc, ctx, *, out_path: calls.append("post"),
            )
        )
        ctx = HookContext(
            doc=object(),
            config={"hooks": {"enable": ["SXM-PRE", "SXM-POST"]}},
        )
        run_phase(Phase.PRE_SAVE, ctx.doc, ctx)
        assert calls == ["pre"]


class TestRunPhasePostSave:
    def test_post_save_requires_out_path(self):
        from scitex_msword.hooks import HookContext, Phase, run_phase

        ctx = HookContext(doc=object(), config={})
        with pytest.raises(AssertionError):
            run_phase(Phase.POST_SAVE, ctx.doc, ctx)

    def test_post_save_receives_out_path_kwarg(self, tmp_path):
        from scitex_msword.hooks import Hook, HookContext, Phase, register, run_phase

        seen: list[Path] = []

        def post(doc, ctx, *, out_path):
            seen.append(out_path)

        register(
            Hook(
                id="SXM-POST",
                phase=Phase.POST_SAVE,
                severity="info",
                category="ex",
                message="m",
                suggestion="s",
                fn=post,
            )
        )
        ctx = HookContext(
            doc=object(), config={"hooks": {"enable": ["SXM-POST"]}}
        )
        target = tmp_path / "saved.docx"
        run_phase(Phase.POST_SAVE, ctx.doc, ctx, out_path=target)
        assert seen == [target]

    def test_post_save_issue_aborts_remainder(self, tmp_path):
        from scitex_msword.hooks import (
            Hook,
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
            register(
                Hook(
                    id=hid,
                    phase=Phase.POST_SAVE,
                    severity="error",
                    category="ex",
                    message="m",
                    suggestion="s",
                    fn=fn,
                )
            )
        ctx = HookContext(
            doc=object(),
            config={"hooks": {"enable": ["SXM-FIRST", "SXM-SECOND"]}},
        )
        with pytest.raises(Issue) as exc_info:
            run_phase(Phase.POST_SAVE, ctx.doc, ctx, out_path=tmp_path / "f.docx")
        assert exc_info.value.hook_id == "SXM-FIRST"
        assert ran == ["first"]


class TestAllHooksByPhase:
    def test_view_buckets_live_registry(self):
        from scitex_msword.hooks import (
            ALL_HOOKS_BY_PHASE,
            Hook,
            Phase,
            register,
        )

        register(
            Hook(
                id="SXM-A",
                phase=Phase.PRE_SAVE,
                severity="info",
                category="ex",
                message="m",
                suggestion="s",
                fn=lambda doc, ctx: None,
            )
        )
        register(
            Hook(
                id="SXM-B",
                phase=Phase.POST_SAVE,
                severity="info",
                category="ex",
                message="m",
                suggestion="s",
                fn=lambda doc, ctx, *, out_path: None,
            )
        )
        assert [h.id for h in ALL_HOOKS_BY_PHASE[Phase.PRE_SAVE]] == ["SXM-A"]
        assert [h.id for h in ALL_HOOKS_BY_PHASE[Phase.POST_SAVE]] == ["SXM-B"]


# EOF
