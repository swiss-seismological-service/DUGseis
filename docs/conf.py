# Configuration file for the Sphinx documentation builder.
import pathlib
import shutil

import sphinx.ext.apidoc


SCRIPT_DIR = pathlib.Path(__file__).parent
MODULE_DIR = pathlib.Path(__file__).parent.parent / "dug_seis"

# -- Project information -----------------------------------------------------

project = "DUGSeis"
copyright = "2021, SED/ETHZ"
author = "SED/ETHZ"

master_doc = "index"
language = "en"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_book_theme"
html_logo = "_static/dug_seis_logo.svg"
html_theme_options = {
    "github_url": "https://github.com/swiss-seismological-service/DUGseis",
    "repository_url": "https://github.com/swiss-seismological-service/DUGseis",
    "use_edit_page_button": True,
    "repository_branch": "main",
    "path_to_docs": "docs",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.9", None),
}


# Automatically build sphinx ext apidoc.
# Adapted from https://github.com/readthedocs/readthedocs.org/issues/1139
def run_apidoc(*args, **kwargs):
    output_path = SCRIPT_DIR / ".generated"
    # Make sure to have a clean build.
    if output_path.exists():
        shutil.rmtree(output_path)
    print(f"Autogenerating API doc in '{output_path}'")
    sphinx.ext.apidoc.main(
        [
            "-e",
            "--force",
            "-o",
            str(output_path),
            str(MODULE_DIR),
            # All remaining items are folders to be ignored.
            str(MODULE_DIR / "graphical_interface"),
        ]
    )


def setup(app):
    app.connect("builder-inited", run_apidoc)
