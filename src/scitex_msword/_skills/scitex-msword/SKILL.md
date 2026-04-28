---
name: scitex-msword
description: MS Word (.docx) ↔ SciTeX writer document model. `import_docx(path)` parses Word paragraphs into the writer schema; `export_docx(doc, path)` writes back. Strategy: Word users write text only; figures/tables/refs/LaTeX stay in SciTeX. Drop-in replacement for `python-docx` boilerplate when round-tripping with the manuscript pipeline.
primary_interface: python
interfaces:
  python: 2
  cli: 0
  mcp: 0
  skills: 2
  hook: 0
  http: 0
canonical-location: scitex-msword/src/scitex_msword/_skills/scitex-msword/SKILL.md
tags: [scitex-msword, scitex-package]
---

> **Interfaces:** Python ⭐⭐ · CLI — · MCP — · Skills ⭐⭐ · Hook — · HTTP —

# scitex-msword

MS Word (.docx) ↔ SciTeX writer document model. `import_docx(path)` parses Word paragraphs into the writer schema; `export_docx(doc, path)` writes back. Strategy: Word users write text only; figures/tables/refs/LaTeX stay in SciTeX. Drop-in replacement for `python-docx` boilerplate when round-tripping with the manuscript pipeline.

See README.md and the package's public `__init__.py` for the full
function list. This skill leaf exists so agents discover the package
exists and roughly what shape it has — refer to the source for
signatures.

<!-- EOF -->
