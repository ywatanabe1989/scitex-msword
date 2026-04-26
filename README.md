# scitex-msword

MS Word (.docx) reader/writer with journal-style profiles, extracted from the [SciTeX](https://github.com/ywatanabe1989/scitex-python) ecosystem as a standalone package.

## Install

```bash
pip install scitex-msword
```

## Usage

```python
import scitex_msword as sxm

# Word -> intermediate JSON-like document
doc = sxm.load_docx("input.docx", profile="generic")

# JSON-like document -> Word (apply a journal style)
sxm.save_docx(doc, "output.docx", profile="mdpi-ijerph")

# DOCX -> LaTeX (requires the umbrella `scitex` package for the .tex export step)
sxm.convert_docx_to_tex(
    "manuscript.docx", "manuscript.tex",
    profile="resna-2025", image_dir="figures",
)
```

### Built-in profiles

`generic`, `mdpi-ijerph`, `resna-2025`, `iop-double-anonymous`, `ieee`,
`springer`, `elsevier`. Register your own with `sxm.register_profile`.

### Helpers

`link_captions_to_images`, `link_captions_to_images_by_proximity`,
`normalize_section_headings`, `validate_document`, `create_post_import_hook`.

## Status

Standalone fork of `scitex.msword`. Only runtime dep is `python-docx`. The
umbrella `scitex.msword` import path is preserved via a `sys.modules`-alias
bridge. `convert_docx_to_tex` lazily imports `scitex.tex`, so it works only
when the umbrella package is also installed.

## License

AGPL-3.0-only (see [LICENSE](./LICENSE)).
