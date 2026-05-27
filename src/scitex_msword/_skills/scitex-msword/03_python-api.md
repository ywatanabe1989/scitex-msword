---
description: |
  [TOPIC] Python API
  [DETAILS] Public Python API of scitex-msword — exported functions, signatures,
  return types, and minimal usage examples per function.
tags: [scitex-msword-python-api]
---

# Python API

```python
from scitex_msword import (
    load_docx,
    save_docx,
    convert_docx_to_tex,
    list_profiles,
    get_profile,
    register_profile,
    BaseWordProfile,
    WordReader,
    WordWriter,
)
```

## load_docx(path, profile=None, extract_images=True) -> dict

Load a DOCX file and convert it into a SciTeX writer document.

```python
doc = load_docx("manuscript.docx", profile="resna-2025")
# doc["blocks"]   -> list of document blocks
# doc["metadata"] -> profile, source, timestamps
# doc["images"]   -> extracted embedded images
# doc["references"] -> parsed reference entries
# doc["warnings"] -> conversion warnings
```

## save_docx(writer_doc, path, profile=None, overwrite=True, template_path=None) -> Path

Save a SciTeX writer document as a DOCX file with journal-specific formatting.

```python
save_docx(doc, "submission.docx", profile="ieee")
```

## convert_docx_to_tex(input_path, output_path, profile=None, ...) -> Path

Convert a DOCX file directly to LaTeX (requires `scitex-tex`).

```python
convert_docx_to_tex(
    "manuscript.docx", "manuscript.tex",
    profile="resna-2025", image_dir="figures",
)
```

## list_profiles() -> list[str]

List available MS Word profile names.

```python
assert "generic" in list_profiles()
```

## get_profile(name=None) -> BaseWordProfile

Get a profile by name; returns "generic" when name is None.

## register_profile(profile) -> None

Register a custom `BaseWordProfile`.

```python
custom = BaseWordProfile(
    name="my-journal",
    description="My custom journal template",
    heading_styles={1: "Title", 2: "Subtitle"},
)
register_profile(custom)
```

## Utility functions

```python
from scitex_msword.utils import (
    link_captions_to_images,
    link_captions_to_images_by_proximity,
    normalize_section_headings,
    validate_document,
    create_post_import_hook,
)
```
