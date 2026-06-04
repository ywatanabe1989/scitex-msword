---
description: |
  [TOPIC] insert_table_after_paragraph — insert a Word table at a paragraph anchor.
  [DETAILS] Pure-lxml <w:tbl> insertion via Paragraph._p.addnext(). Supports
  per-column dxa widths, header-row styling (default MS ゴシック bold) vs.
  body-row styling (default MS 明朝), configurable font size, and
  automatic row-level <w:trPr><w:ins/></w:trPr> wrapping when the document
  already has Track Changes enabled. Lifted from proj-grant build_v43.py
  (BOOST 2026 dogfood) as the canonical sxm public API.
tags: [scitex-msword-tables, scitex-msword-track-changes]
---

# Insert a Word table after a paragraph

```python
from docx import Document
from scitex_msword import insert_table_after_paragraph

doc = Document("draft.docx")
insert_table_after_paragraph(
    doc,
    paragraph_index=17,
    rows=[
        ("役割", "モジュール名"),
        ("論文執筆・ジャーナル投稿自動化", "scitex-writer, scitex-msword"),
        ("AI チャット型研究エージェント", "scitex-orochi"),
    ],
    col_widths_dxa=(3000, 6000),
    header_row=True,
    body_font="MS 明朝",
    header_font="MS ゴシック",
    font_size_pt=10.5,
)
doc.save("draft_with_table.docx")
```

## Signature

```python
insert_table_after_paragraph(
    doc,
    paragraph_index,
    rows,
    col_widths_dxa=(3000, 6000),
    header_row=True,
    body_font="MS 明朝",
    header_font="MS ゴシック",
    font_size_pt=10.5,
    *,
    track_changes=None,
    track_changes_author="agent",
    track_changes_date=None,
) -> lxml.etree._Element
```

- `rows` is any sequence-of-sequences-of-strings; all rows must have
  the same column count, equal to `len(col_widths_dxa)`.
- `font_size_pt=10.5` is encoded as `<w:sz w:val="21">` (half-points).
- The returned `<w:tbl>` element is also already in the document tree
  — return value is for callers that want to chain a follow-up
  `addnext()` (e.g. an explanatory paragraph after the table).

## Track Changes integration

When `track_changes=None` (the default), the writer inspects
`word/settings.xml` for `<w:trackRevisions/>`:

- If present: each inserted `<w:tr>` is marked
  `<w:trPr><w:ins w:id w:author w:date/></w:trPr>` so Word renders the
  rows as accept/reject-able revisions. `w:id` values are assigned
  contiguously starting one past the max id already present.
- If absent: the table is inserted as plain content.

Force the behaviour with `track_changes=True` or `track_changes=False`.

To make Track Changes show up in Word, pair this with
`enable_track_changes` / `save_with_track_changes_on`:

```python
from scitex_msword import (
    insert_table_after_paragraph,
    enable_track_changes,
    save_with_track_changes_on,
)

enable_track_changes(doc, enabled=True)
insert_table_after_paragraph(doc, 17, rows)  # autoTC -> rows marked as ins
save_with_track_changes_on(doc, "draft_with_table.docx")
```

## CLI

```sh
scitex-msword insert-table \
    --path draft.docx \
    --out draft_with_table.docx \
    --paragraph-index 17 \
    --rows '[["役割","モジュール名"],["論文執筆","scitex-writer"]]' \
    --col-widths-dxa 3000,6000 \
    --track-changes-author claude-agent
```

Long row lists are easier to keep in a file:

```sh
scitex-msword insert-table \
    --path draft.docx --out draft_with_table.docx \
    --paragraph-index 17 \
    --rows-file table_rows.json
```

`--track-changes` / `--no-track-changes` force the wrapping mode; omit
both to let the document's existing Track Changes state decide.

## MCP

The MCP server exposes the same surface as
`insert_table_after_paragraph_tool` — same kwargs, same default
column widths, same return-out-path convention as the other sxm
`*_tool` wrappers. Run it via:

```sh
python -m scitex_msword.mcp_server
```

## OOXML details

The generated `<w:tbl>` carries:

- `<w:tblPr><w:tblW w:w="5000" w:type="pct"/>` (table fills 100% of the
  page text width — caller-controlled cell widths drive layout).
- `<w:tblBorders>` with single-line borders on all six sides
  (top/left/bottom/right/insideH/insideV).
- `<w:tblGrid>` with one `<w:gridCol>` per entry in
  `col_widths_dxa`.

Each cell carries `<w:tcPr><w:tcW w:type="dxa"/><w:vAlign
w:val="center"/></w:tcPr>` and a single paragraph whose run has
`<w:rPr><w:rFonts ascii/eastAsia/hAnsi/cs/><w:sz/><w:szCs/></w:rPr>`
(`<w:b/><w:bCs/>` added when `header_row` and row 0).

This element shape is byte-identical to what proj-grant's
`build_v43.py` ships in BOOST today — the canonical pattern.
