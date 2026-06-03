# Changelog

All notable changes to `scitex-msword` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

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
