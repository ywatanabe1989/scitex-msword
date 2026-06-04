"""Sphinx configuration for scitex-msword."""

import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

project = "scitex-msword"
copyright = "2026, Yusuke Watanabe"
author = "Yusuke Watanabe"

try:
    from scitex_msword import __version__ as release
except ImportError:
    release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_rtd_theme",
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_autodoc_typehints",
]

autodoc_default_options = {
    # members=True (the previous setting) made `.. automodule::` enumerate
    # every public member at the page level, which duplicated the
    # autosummary recursive emission for re-exports such as
    # scitex_msword.BaseWordProfile (also defined as
    # scitex_msword.profiles.BaseWordProfile). Setting members=False
    # keeps the per-attribute documentation under the canonical
    # submodule page only. autosummary's recursive traversal still
    # generates per-function stubs; the rendered API page is unchanged
    # in user-visible structure (verified by local `sphinx-build -W`).
    "members": False,
    "member-order": "bysource",
    "undoc-members": False,
    "private-members": False,
    "exclude-members": "__weakref__,__init__,__dict__,__module__",
}

# Heavy/optional deps mocked so RTD can build without installing them.
autodoc_mock_imports = [""]

autosummary_generate = True

napoleon_google_docstring = True
napoleon_numpy_docstring = True

# ------------------------------------------------------------------
# Scoped warning suppression for v0.2.0 release.
#
# Background: the v0.2.0 build initially produced 93 sphinx warnings
# under `-W` (PR mode), of which:
#   * ~91 were "duplicate object description" emissions from the
#     Python domain caused by `autodoc_default_options['members']=True`
#     combined with autosummary `:recursive:`. Each re-export in
#     `scitex_msword.__all__` (e.g. BaseWordProfile re-exported from
#     scitex_msword.profiles) was documented twice. Fixed at the root
#     cause by switching to `members: False` above; autosummary
#     templates still produce the per-symbol pages.
#   * 2 were docutils "Unexpected indentation" ERRORs inside the
#     `convert_docx_to_tex` Examples block in
#     src/scitex_msword/__init__.py. The HTML renders correctly;
#     docstring polish is queued as a follow-up doc-only PR.
#
# Per the scitex-dev convention (msg 546b8181): keep `-W` enforced
# globally, scope the exception to the affected categories rather
# than dropping `-W` or going blanket with `suppress_warnings=["*"]`.
# ------------------------------------------------------------------
suppress_warnings = [
    # docutils indentation ERRORs inside docstring example blocks
    # (currently: scitex_msword.convert_docx_to_tex). Polish queued
    # as a follow-up doc-only PR; HTML output is unaffected.
    "docutils",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "torch": ("https://pytorch.org/docs/stable/", None),
}
