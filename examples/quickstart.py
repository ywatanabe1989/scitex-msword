"""Quickstart for scitex_msword.

Builds a small SciTeX-writer-shaped document and writes it to a .docx file,
then loads it back via `load_docx` and inspects the structure.
"""

import tempfile
from pathlib import Path

import scitex_msword as smw


def main() -> int:
    doc = {
        "blocks": [
            {"type": "heading", "level": 1, "text": "Quickstart Report"},
            {
                "type": "paragraph",
                "text": "This document was produced by scitex_msword.",
            },
            {"type": "heading", "level": 2, "text": "Findings"},
            {
                "type": "paragraph",
                "text": "All twelve quickstart examples in batch A run cleanly.",
            },
            {"type": "heading", "level": 2, "text": "Next Steps"},
            {"type": "paragraph", "text": "Wire up CI smoke tests for each package."},
        ],
        "images": [],
        "metadata": {"title": "scitex_msword quickstart", "author": "demo"},
    }

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "report.docx"
        written = smw.save_docx(doc, out, profile="generic")
        assert written.exists() and written.stat().st_size > 0
        print(f"Wrote {written} ({written.stat().st_size} bytes)")

        loaded = smw.load_docx(written)
        print(f"Loaded back: {len(loaded.get('blocks', []))} blocks")
        for blk in loaded.get("blocks", [])[:4]:
            print(f"  - {blk.get('type'):<10} {blk.get('text', '')[:60]}")

        # Validate the SciTeX-writer-shaped doc
        report = smw.validate_document(doc)
        print(f"validate_document -> ok={report.get('ok', report)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
