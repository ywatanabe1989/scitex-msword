# scitex-msword

<!-- scitex-badges:start -->
[![PyPI](https://img.shields.io/pypi/v/scitex-msword.svg)](https://pypi.org/project/scitex-msword/)
[![Python](https://img.shields.io/pypi/pyversions/scitex-msword.svg)](https://pypi.org/project/scitex-msword/)
[![Tests](https://github.com/ywatanabe1989/scitex-msword/actions/workflows/test.yml/badge.svg)](https://github.com/ywatanabe1989/scitex-msword/actions/workflows/test.yml)
[![Install Test](https://github.com/ywatanabe1989/scitex-msword/actions/workflows/install-test.yml/badge.svg)](https://github.com/ywatanabe1989/scitex-msword/actions/workflows/install-test.yml)
[![Coverage](https://codecov.io/gh/ywatanabe1989/scitex-msword/graph/badge.svg)](https://codecov.io/gh/ywatanabe1989/scitex-msword)
[![Docs](https://readthedocs.org/projects/scitex-msword/badge/?version=latest)](https://scitex-msword.readthedocs.io/en/latest/)
[![License: AGPL v3](https://img.shields.io/badge/license-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
<!-- scitex-badges:end -->

<p align="center">
  <a href="https://scitex.ai">
    <img src="docs/scitex-logo-blue-cropped.png" alt="SciTeX" width="400">
  </a>
</p>

<p align="center"><b>MS Word (.docx) reader/writer with journal-style profiles.</b></p>

<p align="center">
  <a href="https://scitex-msword.readthedocs.io/">Full Documentation</a> · <code>pip install scitex-msword</code>
</p>

---

## Installation

```bash
pip install scitex-msword
```

## Quick Start

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

## 1 Interfaces

<details>
<summary><strong>Python API</strong></summary>

<br>

```python
import scitex_msword as sxm

# Round-trip
doc = sxm.load_docx("paper.docx", profile="generic")
sxm.save_docx(doc, "paper-styled.docx", profile="ieee")

# Helpers
sxm.link_captions_to_images(doc)
sxm.link_captions_to_images_by_proximity(doc)
sxm.normalize_section_headings(doc)
sxm.validate_document(doc)
sxm.create_post_import_hook(doc)

# Register custom profile
sxm.register_profile("my-style", {...})
```

### Built-in profiles

`generic`, `mdpi-ijerph`, `resna-2025`, `iop-double-anonymous`, `ieee`,
`springer`, `elsevier`.

</details>

## Status

Standalone fork of `scitex.msword`. Only runtime dep is `python-docx`. The
umbrella `scitex.msword` import path is preserved via a `sys.modules`-alias
bridge. `convert_docx_to_tex` lazily imports `scitex.tex`, so it works only
when the umbrella package is also installed.

## Part of SciTeX

`scitex-msword` is part of [**SciTeX**](https://scitex.ai).

>Four Freedoms for Research
>
>0. The freedom to **run** your research anywhere — your machine, your terms.
>1. The freedom to **study** how every step works — from raw data to final manuscript.
>2. The freedom to **redistribute** your workflows, not just your papers.
>3. The freedom to **modify** any module and share improvements with the community.
>
>AGPL-3.0 — because we believe research infrastructure deserves the same freedoms as the software it runs on.

## License

AGPL-3.0-only (see [LICENSE](./LICENSE)).

---

<p align="center">
  <a href="https://scitex.ai" target="_blank"><img src="docs/scitex-icon-navy-inverted.png" alt="SciTeX" width="40"/></a>
</p>
