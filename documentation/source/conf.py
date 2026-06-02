"""Sphinx configuration for the cyopt documentation.

Purpose
-------
Configure paths, project metadata, Sphinx extensions, and HTML output
options for the documentation build.

Main public API
---------------
Module-level Sphinx configuration variables such as ``project``,
``extensions``, ``html_theme``, and ``mathjax3_config``.

Design notes
------------
This file is executed by Sphinx, so imports should stay minimal and
documentation-specific.
"""

import os
import re
import sys

from sphinx.ext import autosummary as _sphinx_autosummary

sys.path.insert(0, os.path.abspath('../../'))

# -- Project information -----------------------------------------------------

project = "cyopt"
copyright = "2026, The cyopt developers"

try:
    from importlib.metadata import version as _version
    release = _version("cyopt")
    version = ".".join(release.split(".")[:2])
except Exception:
    release = "1.1.0"
    version = "1.1"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx_autodoc_typehints",
    "sphinx_togglebutton",
    "sphinx_design",
    "myst_nb",
]

templates_path = ["_templates"]

source_suffix = {
    ".rst": "restructuredtext",
    ".ipynb": "myst-nb",
    ".md": "myst-nb",
}

exclude_patterns = ["_autosummary/*"]

suppress_warnings = [
    "sphinx_autodoc_typehints.forward_reference",
]

pygments_style = None

autodoc_default_options = {}
autosummary_generate = True
napoleon_use_rtype = False
napoleon_custom_sections = [('Returns', 'params_style')]

autodoc_mock_imports = ["cytools"]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_book_theme"

html_theme_options = {
    "repository_url": "https://github.com/sheride/cyopt",
    "repository_branch": "main",
    "path_to_docs": "documentation/source",
    "use_repository_button": True,
    "use_edit_page_button": True,
}

html_static_path = ["_static"]

html_css_files = ["css/cyopt-figures.css"]

# Enable MathJax 3 to process inline $...$ inside raw HTML blocks.
# Sphinx's default setup only renders :math: nodes; raw HTML carrying
# $...$ (in the embedded SVG figures) needs this hook.
mathjax3_config = {
    "tex": {"inlineMath": [["$", "$"], ["\\(", "\\)"]]},
    "svg": {"fontCache": "global"},
}

add_module_names = False
toc_object_entries_show_parents = "hide"

# -- Options for myst / notebooks --------------------------------------------

nb_execution_mode = "off"
myst_enable_extensions = ["dollarmath"]
myst_heading_anchors = 4
myst_dmath_double_inline = True
nb_execution_allow_errors = False
nb_merge_streams = True


# -- Custom docstring processing ---------------------------------------------

def _strip_leading_description_marker(lines):
    """Remove the project's leading Markdown-style description marker."""
    lines = list(lines)
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        marker = "**Description:**"
        if stripped == marker:
            del lines[idx]
        elif stripped.startswith(marker):
            indent = line[: len(line) - len(line.lstrip())]
            lines[idx] = indent + stripped[len(marker):].lstrip()
        break
    return lines


def _extract_project_summary(doc, settings):
    """Extract autosummary text without parsing project docstring markers."""
    first_stanza = []
    content_started = False
    for line in _strip_leading_description_marker(doc):
        stripped = line.strip()
        if not content_started:
            if not stripped:
                continue
            content_started = True
        if (
            not stripped
            or stripped.startswith("```")
            or stripped in {
                "Args:", "Arguments:", "Returns:", "Raises:",
                "Example:", "Examples:",
            }
            or stripped.startswith(".. ")
        ):
            break
        first_stanza.append(stripped)
    if not first_stanza:
        return ""
    summary = " ".join(first_stanza).strip()
    return re.sub(r"::$", ".", summary)


_sphinx_autosummary.extract_summary = _extract_project_summary


def _normalise_project_docstring(app, what, name, obj, options, lines):
    """Adapt Markdown-flavoured docstrings for Sphinx/ReST."""
    lines[:] = _strip_leading_description_marker(lines)
    normalised = []
    in_fence = False
    fence_indent = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_fence:
                in_fence = False
                normalised.append("")
            else:
                language = stripped[3:].strip() or "text"
                fence_indent = line[: len(line) - len(line.lstrip())]
                normalised.append(f"{fence_indent}.. code-block:: {language}")
                normalised.append("")
                in_fence = True
            continue
        if in_fence:
            normalised.append(f"{fence_indent}    {line}")
        else:
            normalised.append(line)
    lines[:] = normalised


def setup(app):
    app.connect("autodoc-process-docstring", _normalise_project_docstring)
