---
name: scitex-msword
description: MS Word (.docx) ↔ SciTeX writer document model. `import_docx(path)` parses Word paragraphs into the writer schema; `export_docx(doc, path)` writes back. Strategy: Word users write text only; figures/tables/refs/LaTeX stay in SciTeX. Drop-in replacement for `python-docx` boilerplate when round-tripping with the manuscript pipeline.
primary_interface: python
interfaces:
  python: 3
  cli: 1
  mcp: 1
  skills: 3
  hook: 0
  http: 0
canonical-location: scitex-msword/src/scitex_msword/_skills/scitex-msword/SKILL.md
tags: [scitex-msword, scitex-package]
---

> **Interfaces:** Python ⭐⭐⭐ · CLI ⭐ · MCP ⭐ · Skills ⭐⭐⭐ · Hook — · HTTP —

# scitex-msword

MS Word (.docx) ↔ SciTeX writer document model. `import_docx(path)` parses Word paragraphs into the writer schema; `export_docx(doc, path)` writes back. Strategy: Word users write text only; figures/tables/refs/LaTeX stay in SciTeX. Drop-in replacement for `python-docx` boilerplate when round-tripping with the manuscript pipeline.

See README.md and the package's public `__init__.py` for the full
function list. This skill leaf exists so agents discover the package
exists and roughly what shape it has — refer to the source for
signatures.

## Sub-skills

### Core (01–09)
- [01_installation.md](01_installation.md) — install + import sanity check
- [02_quick-start.md](02_quick-start.md) — 30-second tour
- [03_python-api.md](03_python-api.md) — Python API surface
- [04_insert-table.md](04_insert-table.md) — `insert_table_after_paragraph` (Python/CLI/MCP) — pure-lxml Word table insertion at a paragraph anchor, with optional Track-Changes row markers
