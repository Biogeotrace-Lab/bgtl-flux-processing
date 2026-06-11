# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import sys
import os


# 1. Path setup: Points Sphinx to your local source code
sys.path.insert(0, os.path.abspath("../src"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'bgtl-fluxy'
copyright = '2026, Biogeotrace Lab'
author = 'Biogeotrace Lab'
release = 'v0.0.0b4'


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # Core library for pulling in docstrings
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",  # Allows Sphinx to understand Google/NumPy docstrings
    "sphinx.ext.viewcode",  # Adds "Source" links next to your code definitions
    "myst_parser",  # Enabler for writing documentation in .md instead of .rst
    "sphinx_copybutton",  # Quick click-to-copy utility on code snippets
    "sphinx_inline_tabs",  # Tab groups utility
    "sphinx_click"
]
autosummary_generate = True

autodoc_typehints = "signature"

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}

templates_path = ['_templates']
exclude_patterns = []



# 4. Modern Source Suffixes
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ['_static']
html_theme_options = {
    'logo': {'text': 'fluxy',
             'image_light': 'bgtl.png',
             'image_dark': 'bgtl.png' },
    # 1. Remove top header tabs by setting the count to 0
    # This forces ALL your toctree items down into the left sidebar!
    "header_links_before_dropdown": 2,
    
    # 2. Ensure the left sidebar expands down to show your sub-items
    "show_nav_level": 2,
    "navigation_depth": 4,

    "icon_links": [
        {
            "name": "Organization",
            "url": "https://your-organization.org",
            "icon": "fa-solid fa-building",  # Uses FontAwesome icons
            "type": "fontawesome",
        },],

    "footer_start": ["uab-logo"],
    "footer_center": ["copyright"],
    "footer_end": ["nothing.html"]
}
html_css_files = [
    'config.css',
]