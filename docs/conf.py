# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import sys

from pathlib import Path

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, Path("../socon").absolute().as_posix())
sys.path.append(Path(Path(__file__).parent, "_ext").absolute().as_posix())

# -- Project information -----------------------------------------------------

project = "Socon"
copyright = "2023, Stephane Capponi and others"
author = "Stephane Capponi"

# The full version, including alpha/beta/rc tags
version = "0.1.0"

# The full version, including alpha/beta/rc tags.
try:
    from socon import get_version
except ImportError:
    release = version
else:
    release = get_version()

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "socondoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autodoc",
    "sphinx_rtd_theme",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".txt"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "requirements.txt"]

# Spelling check needs an additional module that is not installed by default.
# Add it only if spelling check is requested so docs can be generated without it.
if "spelling" in sys.argv:
    extensions.append("sphinxcontrib.spelling")

# Spelling language.
spelling_lang = "en_US"

# Location of word list.
spelling_word_list_filename = "spelling_wordlist"

# Activate the warning
spelling_warning = True

# External links
extlinks = {
    "source": ("https://github.com/socon-dev/socon/blob/master/%s", "%s"),
}

# The master toctree document.
master_doc = "contents"

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = False

# A list of prefixes that are ignored for sorting the Python module
# index (e.g., if this is set to ['foo.'], then foo.bar is
# shown under B, not F). This can be handy if you document a project
# that consists of a single package. Works only for the HTML builder
# currently. Default is [].
modindex_common_prefix = ["socon."]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

# If set, autosectionlabel chooses the sections for labeling by its depth.
# For example, when set 1 to autosectionlabel_maxdepth, labels
# are generated only for top level sections, and deeper sections are
# not labeled. It defaults to None (disabled).
autosectionlabel_maxdepth = 1
