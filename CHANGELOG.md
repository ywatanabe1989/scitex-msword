# Changelog

All notable changes to `scitex-msword` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.3.1] - 2026-06-04

Track Changes correctness + Japanese-typography slot semantics for the
JST BOOST 2026 dogfood. Three fixes (one P0, one P1, one P2 cleanup)
plus a switchable contract on `save_with_track_changes_on` and a
committed Word-emitted ground-truth fixture so the conformance gate
can no longer pass on self-consistent wrong-name state.

### Fixed — Track Changes element name (P0, affects every release ≥v0.2.0)

`enable_track_changes` / `save_with_track_changes_on` /
`is_track_changes_enabled` have been operating on the wrong OOXML
element since v0.2.0. ECMA-376 §17.15.1.92 names the actual Track
Changes toggle `<w:trackRevisions/>` (CT_Settings child); sxm has
been emitting `<w:trackChanges/>`, which is a different element
entirely (CT_HdrFtr §17.10.1.84, for header/footer revisions).
Desktop Word silently ignores `<w:trackChanges/>` in this position,
so every `.docx` ever produced via the helper has had Track Changes
**silently OFF** in Word, and `is_track_changes_enabled` returned
False on documents Word itself produced.

- `enable_track_changes` and `save_with_track_changes_on` now emit
  `<w:trackRevisions/>` at the same ECMA-376-ordered slot. Public
  API names (`enable_track_changes`, `save_with_track_changes_on`,
  `is_track_changes_enabled`) are unchanged.
- `enable_track_changes` also writes the matching
  `<w:documentProtection w:edit="trackedChanges" w:enforcement="0"/>`
  that desktop Word emits when Track Changes is toggled on (state-
  only, not enforced — the user can still disable interactively).
- `is_track_changes_enabled` now reads `<w:trackRevisions/>`.
- New internal helper
  `scitex_msword._settings_order.ensure_document_protection_for_tracked_changes`
  owns the documentProtection placement; the ordered-placement
  routine generalised to a per-tag anchor-table dispatch so future
  CT_Settings elements with schema-prescribed positions can reuse it.
- Files produced by ≤v0.3.0 need to be re-saved with this version
  to actually have Track Changes on.

### Fixed — boost-2026 profile slot semantics + width forms

v0.3.0 routed `boost-2026`'s `body_font` (Mincho) only to ascii +
hAnsi, leaving the docDefaults `<w:eastAsia/>` slot set to `bold_font`
(Gothic). Every Japanese body paragraph therefore rendered in Gothic
sans-serif instead of Mincho serif, and bold runs lost their weight
contrast.

- `save_document` now routes `profile.body_font` to
  **eastAsia + ascii + hAnsi** in
  `<w:docDefaults>/<w:rPrDefault>/<w:rPr>/<w:rFonts>` (BOOST uses
  Mincho for embedded Latin runs too — operator id 685).
- `save_document` no longer writes `profile.bold_font` into
  docDefaults. The new `_apply_bold_font_to_bold_runs(doc, bold_font)`
  internal helper walks every `<w:r>` under the body and applies
  `rFonts/@w:eastAsia=bold_font` only on runs whose `rPr/b` is
  present-and-not-explicitly-false. Non-bold runs stay at the
  docDefaults body_font.
- `boost-2026` profile now ships full-width forms (`ＭＳ 明朝` /
  `ＭＳ ゴシック`) so Word's Japanese font picker resolves them — the
  half-width `MS 明朝` / `MS ゴシック` forms in v0.3.0 did not.

### Fixed — Track Changes writer cleans up legacy stale state (P2)

`enable_track_changes` (and therefore `save_with_track_changes_on`) now
strips every stray `<w:trackChanges/>` from `CT_Settings` before
writing — so re-saving a document originally produced by sxm
≤v0.3.0 (which wrote the wrong element name; see above) yields a
byte-clean settings.xml that matches Word's own emission. CT_HdrFtr
trackChanges (a different element entirely) is not touched. The writer
is now idempotent: calling `save_with_track_changes_on` twice on the
same document yields exactly one `<w:trackRevisions/>` and one
`<w:documentProtection edit=trackedChanges enforcement=0>`.

### Added — switchable kwargs (per operator spec)

`enable_track_changes` and `save_with_track_changes_on` gain two
keyword-only flags, both defaulting `True` so today's callers keep the
default-correct Word-matching recipe:

```python
enable_track_changes(doc, enabled=True, *, emit_doc_protection_echo=True)
save_with_track_changes_on(
    doc, path, *, track_revisions=True, emit_doc_protection_echo=True,
)
```

- `emit_doc_protection_echo=False` writes `<w:trackRevisions/>`
  without the matching `<w:documentProtection/>` echo (for callers
  that read the protection element independently).
- `track_revisions=False` is the clean-export path on
  `save_with_track_changes_on`: strips both elements before saving.

### Added — committed Word-emitted ground-truth fixture

`tests/scitex_msword/fixtures/track_changes/word_groundtruth_settings.xml`
is the `word/settings.xml` Word itself wrote when the operator
manually toggled Track Changes ON during the BOOST v40 dogfood. The
new `TestTrackRevisionsAgainstVendoredWordGroundTruth` class pins
the writer against this committed reference, closing the
self-consistent-wrong-name blind-spot that let the trackChanges /
trackRevisions bug ship from v0.2.0 through v0.3.0. Full provenance
+ sha256 in the fixtures `README.md`.

### Internal

- Extract the OOXML primitive helpers (`_make_w_element`,
  `_scan_max_revision_id`, `_resolve_runs`, `_wrap_runs_in_element`,
  `_next_revision_id`, `_settings_element`, `_now_iso`) from
  `track_changes.py` into a sibling module
  `_track_changes_helpers.py`. Public API surface unchanged.
- Generalise `_settings_order.insert_in_settings_order` via a
  per-tag `_ANCHOR_TABLES` dispatch so additional CT_Settings
  children with schema-prescribed positions can reuse the routine.
- New `_settings_order.ensure_document_protection_for_tracked_changes`
  owns the documentProtection placement.

## [0.3.0] - 2026-06-04

Cut to unblock the JST BOOST 2026 grant dogfood (T-7d). Three new
public surfaces — `sxm.hooks`, `save_with_track_changes_on`,
`save_document` — plus a corrected `boost-2026` profile.

### Added

- `sxm.hooks` package skeleton (H1). `Hook` / `Phase` / `Issue` /
  `HookContext` dataclasses, `register()` decorator, `run_phase()`
  dispatcher, three-tier discovery (engine builtins +
  `scitex_msword.hooks` entry-points + walk-up project-local
  `<root>/.scitex/msword/hooks/*.py`). Override precedence:
  project-local > entry-points > builtins. Fail-loud dispatch: the
  first exception raised by any hook aborts the rest of the phase and
  is propagated to the caller. `PRE_SAVE` hooks must be idempotent;
  `POST_SAVE` hooks are read-only and signal violations by raising
  `Issue` (also an `Exception`). No builtin hooks ship in H1 —
  `SXM-TC001` (track-changes audit) and `SXM-JP001` (Japanese
  typography) land in H4 / H5. Per proj-grant
  `design_sxm_hooks_v01.md` + the proj-scitex-dev design-lock thread.
- `scitex_msword.save_document(doc, path, profile=None)` — direct save
  path for python-docx `Document` instances. Unlike `save_docx` (which
  round-trips through a SciTeX writer-dict), `save_document` preserves
  python-docx-level edits intact (table cell XML manipulation,
  embedded image positioning, run-level bold preservation). When a
  profile is supplied, its advisory layout hints land in
  `<w:docDefaults>` so caller per-run / per-paragraph overrides keep
  winning. The `sxm.hooks` dispatcher fires for both phases: `PRE_SAVE`
  before the file is written; `POST_SAVE` after, with `out_path=path`.
- `scitex_msword.save_with_track_changes_on(doc, path)` — canonical
  helper for the BOOST workflow: enable Track Changes (in ECMA-376
  ordered position) and save in one call.
- `BaseWordProfile.bold_font: Optional[str]` — paired bold typeface
  field. Lets a profile declare a bold/heading typeface alongside
  `body_font`. Japanese templates use this to land Mincho in `ascii`/
  `hAnsi` and Gothic in `eastAsia`, so weight contrast comes from the
  typeface rather than a synthetic-bold transform.

### Changed

- `boost-2026` profile aligned with the proj-grant BOOST v37
  dogfooding spec: regular body = MS 明朝 (Mincho), bold = MS ゴシック
  (Gothic), both at 10.5pt; heading background D9D9D9, line spacing
  1.0, `参考文献` reference title — unchanged. The previous
  `body_font="MS Gothic"` was at odds with the spec; the field now
  carries Mincho and `bold_font` carries Gothic.
- `enable_track_changes` now inserts `<w:trackChanges/>` at the
  ECMA-376 §17.15.1 `CT_Settings` ordered slot (after the last present
  predecessor, before the first present successor) rather than naively
  appending. Word silently ignored out-of-order elements in some
  files; this is required for the BOOST v37 workflow (proj-grant lost
  ~1h to this on v36).

### Internal

- New module `scitex_msword._settings_order`: owns the ECMA-376
  `CT_Settings` placement decision. Generic so future ordered
  insertions (other elements with schema-prescribed positions) can
  reuse it.
- New module `scitex_msword._save_document`: hosts `save_document` and
  its profile→docDefaults bridge. Keeps `__init__.py` and `writer.py`
  small.

## [0.2.0] - 2026-06-04

### Added

- `scitex_msword.enable_track_changes(doc, enabled=True)` — toggle Word's
  Track Changes switch by inserting/removing `<w:trackChanges/>` in
  `word/settings.xml`. Idempotent and reversible.
- `scitex_msword.is_track_changes_enabled(doc)` — report whether the
  switch is currently on.
- `scitex_msword.wrap_as_tracked_insertion(paragraph, runs, author, date,
  w_id)` and `wrap_as_tracked_deletion(...)` — wrap selected runs as
  `<w:ins>` / `<w:del>` revision blocks so Word renders them as
  accept/reject-able tracked changes. Deletions also convert `<w:t>`
  children to `<w:delText>` for strike-through rendering.
- `scitex_msword.extract_tracked_changes(doc)` — structured extraction
  of every `<w:ins>` / `<w:del>` in the body
  (`type`, `paragraph_idx`, `author`, `date`, `id`, `text`).
- `scitex_msword.accept_all_tracked_changes(doc)` and
  `reject_all_tracked_changes(doc)` — bulk equivalents of Word's
  "Accept All" / "Reject All" Review actions.
- `scitex_msword.diff_docx(a, b)` and `summarize_diff(ops)` — paragraph-
  level diff between two DOCX files with run-level formatting deltas
  (bold/italic/underline/font/highlight).
- `scitex_msword.mark_additions(doc, runs, color="turquoise")` and
  `mark_modifications(doc, runs, color="magenta")` — visualize edits
  with Word highlight colors.
- `scitex_msword.extract_highlights(doc, by_color=True)` — read back
  highlighted runs, bucketed by color name.
- `scitex_msword.clear_highlights(doc, colors=None)` — strip highlights.
- `scitex_msword.preserve_bold_tokens(doc, tokens, font_name="MS Gothic")`
  — re-split runs and bold-emphasize keyword tokens, with Latin +
  East-Asian + complex-script font slots all populated so Japanese
  tokens render in MS Gothic.
- `scitex_msword.extract_comments(doc)` — pull Word comments and their
  anchor ranges from `word/comments.xml`.
- `scitex_msword.apply_comments_as_edits(doc, grammar="replace")` —
  apply comments whose body matches `REPLACE: ...` as literal anchor
  substitutions. Other grammars (e.g. natural language) are out of scope.
- New profile `boost-2026` (alias `boost`): JST BOOST 2026 grant
  application template — 10.5pt MS Gothic body, D9D9D9 heading
  background, 1.0 line spacing.
- New `BaseWordProfile` advisory fields: `body_font`,
  `body_font_size_pt`, `heading_background_hex`, `line_spacing`.
- `scitex_msword.mcp_server` — Model Context Protocol server scaffold
  exposing diff / mark / preserve-bold / extract-highlights / extract-
  comments / list-profiles as MCP tools.
- Optional `mcp` extras (`pip install scitex-msword[mcp]`) for the MCP
  scaffold; the module imports cleanly without it.

### Fixed

- Highlight color buckets no longer leak the `WD_COLOR_INDEX` enum's
  integer suffix (e.g. `"turquoise (3)"`); they now use `.name` and
  bucket cleanly as `"turquoise"`.

## [0.1.1]

- Initial CHANGELOG entry — see git log for prior history.
