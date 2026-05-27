---
description: |
  [TOPIC] Quick Start
  [DETAILS] Smallest useful example demonstrating the primary use case in
  under 30 seconds.
tags: [scitex-msword-quick-start]
---

# Quick Start

```python
import scitex_msword as sxm

# Load a DOCX file (generic profile)
doc = sxm.load_docx("manuscript.docx", profile="generic")

# Inspect blocks
for block in doc["blocks"]:
    print(block["type"], ":", block.get("text", "")[:80])

# Save with a journal-specific profile
sxm.save_docx(doc, "output.docx", profile="ieee")

# Or convert directly to LaTeX (requires scitex-tex)
sxm.convert_docx_to_tex(
    "manuscript.docx", "manuscript.tex",
    profile="resna-2025", image_dir="figures",
)
```
