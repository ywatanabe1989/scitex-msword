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
# suppress_warnings was set to ["docutils"] in v0.2.0 to scope-suppress
# two "Unexpected indentation" ERRORs in scitex_msword.convert_docx_to_tex's
# Examples block (multi-line `>>> / ...` doctest continuation). Polished
# in v0.2.1 by rewriting that block as `.. code-block:: python`, after
# which the suppress was no longer needed and was lifted to keep `-W`
# enforced globally with no scoped exceptions.
# Per the scitex-dev convention (msg 546b8181): explicit exception with
# a clear forward-pointer until the underlying issue is fixed at source.

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
