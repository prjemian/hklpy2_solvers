# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import pathlib
import sys
import tomllib
from datetime import datetime
from importlib.metadata import version as _version

root_path = pathlib.Path(__file__).parent.parent.parent

with open(root_path / "pyproject.toml", "rb") as _f:
    _toml = tomllib.load(_f)

sys.path.insert(0, str(root_path / "src"))

# -- Project information -----------------------------------------------------

project = _toml["project"]["name"]
author = _toml["project"]["authors"][0]["name"]
copyright = f"2025-{datetime.now().year}, Argonne National Laboratory"
github_url = _toml["project"]["urls"]["source"]

release = _version("hklpy2-solvers")
version = ".".join(release.split(".")[:2])

# version_match: used by the version switcher to highlight the current version.
# Set DOC_VERSION in CI to "latest" (main branch) or the tag (e.g. "0.1.0").
switcher_version_match = os.environ.get("DOC_VERSION", release)

# -- General configuration ---------------------------------------------------

extensions = [
    "autoapi.extension",
    "myst_nb",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_tabs.tabs",
]

myst_enable_extensions = ["colon_fence"]
nb_execution_mode = "off"

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "myst-nb",
    ".ipynb": "myst-nb",
}

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]
templates_path = ["_templates"]

# -- AutoAPI -----------------------------------------------------------------

autoapi_root = "api"
autoapi_dirs = [str(root_path / "src")]
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
]
autoapi_member_order = "alphabetical"
autoapi_python_class_content = "both"
autoapi_add_toctree_entry = False
suppress_warnings = ["autoapi.python_import_resolution"]


def autoapi_skip_member(app, what, name, obj, skip, options):
    """Skip logger instances from autoapi output."""
    if what == "data" and name.endswith(".logger"):
        return True
    return skip


def setup(app):
    app.connect("autoapi-skip-member", autoapi_skip_member)


# -- Intersphinx -------------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
}

# -- extlinks ----------------------------------------------------------------

extlinks = {
    "issue": (f"{github_url}/issues/%s", "issue #%s"),
    "pr": (f"{github_url}/pull/%s", "PR #%s"),
}

# -- copybutton --------------------------------------------------------------

copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True

# -- HTML output -------------------------------------------------------------

html_theme = "pydata_sphinx_theme"
html_title = f"{project} {version}"
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]

html_theme_options = {
    "github_url": github_url,
    "navbar_end": ["version-switcher", "theme-switcher", "navbar-icon-links"],
    "switcher": {
        "json_url": f"https://prjemian.github.io/hklpy2_solvers/latest/_static/switcher.json",
        "version_match": switcher_version_match,
    },
    "check_switcher": False,
    "show_version_warning_banner": True,
}
