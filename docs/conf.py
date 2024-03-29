#!/usr/bin/env python3
#
# projectq documentation build configuration file, created by
# sphinx-quickstart on Tue Nov 29 11:51:46 2016.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

"""Configuration file for generating the documentation for ProjectQ."""

# pylint: disable=invalid-name

import functools
import importlib
import inspect
import os
import sys
from importlib.metadata import version

sys.path.insert(0, os.path.abspath('..'))  # for projectq
sys.path.append(os.path.abspath('.'))  # for package_description

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.mathjax',
    'sphinx.ext.autosummary',
    'sphinx.ext.linkcode',
]

autosummary_generate = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The encoding of source files.
#
# source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'ProjectQ'
copyright = '2017-2021, ProjectQ'  # pylint: disable=redefined-builtin
author = 'ProjectQ'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.

release = version('projectq')  # Full version string
version = '.'.join(release.split('.')[:3])  # X.Y.Z

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#
# today = ''
#
# Else, today_fmt is used as the format for a strftime call.
#
# today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'README.rst']

# The reST default role (used for this markup: `text`) to use for all
# documents.
#
# default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#
# add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#
# add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
# modindex_common_prefix = []

# If true, keep warnings as "system message" paragraphs in the built documents.
# keep_warnings = False

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom themes here, relative to this directory.
# html_theme_path = []

# The name for this set of Sphinx documents.
# "<project> v<release> documentation" by default.
#
# html_title = 'projectq v1'

# A shorter title for the navigation bar.  Default is the same as html_title.
#
# html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#
# html_logo = None

# The name of an image file (relative to this directory) to use as a favicon of
# the docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x
# 32 pixels large.
#
# html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

# Add any extra paths that contain custom files (such as robots.txt or
# .htaccess) here, relative to this directory. These files are copied
# directly to the root of the documentation.
#
# html_extra_path = []

# If not None, a 'Last updated on:' timestamp is inserted at every page
# bottom, using the given strftime format.
# The empty string is equivalent to '%b %d, %Y'.
#
# html_last_updated_fmt = None

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#
# html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#
# html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#
# html_additional_pages = {}

# If false, no module index is generated.
#
# html_domain_indices = True

# If false, no index is generated.
#
# html_use_index = True

# If true, the index is split into individual pages for each letter.
#
# html_split_index = False

# If true, links to the reST sources are added to the pages.
#
# html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
#
# html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
#
# html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#
# html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = None

# Language to be used for generating the HTML full-text search index.
# Sphinx supports the following languages:
#   'da', 'de', 'en', 'es', 'fi', 'fr', 'h', 'it', 'ja'
#   'nl', 'no', 'pt', 'ro', 'r', 'sv', 'tr', 'zh'
#
# html_search_language = 'en'

# A dictionary with options for the search language support, empty by default.
# 'ja' uses this config value.
# 'zh' user can custom change `jieba` dictionary path.
#
# html_search_options = {'type': 'default'}

# The name of a javascript file (relative to the configuration directory) that
# implements a search results scorer. If empty, the default will be used.
#
# html_search_scorer = 'scorer.js'

# Output file base name for HTML help builder.
htmlhelp_basename = 'projectqdoc'

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'projectq.tex', 'projectq Documentation', 'a', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#
# latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#
# latex_use_parts = False

# If true, show page references after internal links.
#
# latex_show_pagerefs = False

# If true, show URL addresses after external links.
#
# latex_show_urls = False

# Documents to append as an appendix to all manuals.
#
# latex_appendices = []

# It false, will not define \strong, \code,     itleref, \crossref ... but only
# \sphinxstrong, ..., \sphinxtitleref, ... To help avoid clash with user added
# packages.
#
# latex_keep_old_macro_names = True

# If false, no module index is generated.
#
# latex_domain_indices = True

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [(master_doc, 'projectq', 'projectq Documentation', [author], 1)]

# If true, show URL addresses after external links.
#
# man_show_urls = False

# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        'projectq',
        'projectq Documentation',
        author,
        'projectq',
        'One line description of project.',
        'Miscellaneous',
    ),
]

# Documents to append as an appendix to all manuals.
#
# texinfo_appendices = []

# If false, no module index is generated.
#
# texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
#
# texinfo_show_urls = 'footnote'

# If true, do not generate a @detailmenu in the "Top" node's menu.
#
# texinfo_no_detailmenu = False

# -- Options for sphinx.ext.linkcode --------------------------------------


def recursive_getattr(obj, attr, *args):
    """Recursively get the attributes of a Python object."""

    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split('.'))


def linkcode_resolve(domain, info):
    """Change URLs in documentation on the fly."""
    # Copyright 2018 ProjectQ (www.projectq.ch), all rights reserved.
    on_rtd = os.environ.get('READTHEDOCS') == 'True'
    github_url = "https://github.com/ProjectQ-Framework/ProjectQ/tree/"
    github_tag = 'v' + version
    if on_rtd:
        rtd_tag = os.environ.get('READTHEDOCS_VERSION')
        if rtd_tag == 'latest':
            github_tag = 'develop'
        elif rtd_tag == 'stable':
            github_tag = 'master'
        else:
            # RTD changes "/" in branch name to "-"
            # As we use branches like fix/cool-feature, this is a
            # problem -> as a fix we require that all branch names
            # which contain a '-' must first contain one '/':
            if list(rtd_tag).count('-'):
                github_tag = list(rtd_tag)
                github_tag[github_tag.index('-')] = '/'
                github_tag = ''.join(github_tag)
            else:
                github_tag = rtd_tag

    if domain != 'py':
        return None
    try:
        module = importlib.import_module(info['module'])
        obj = recursive_getattr(module, info['fullname'])
    except (AttributeError, ValueError):
        # AttributeError:
        # Object might be a non-static attribute of a class, e.g., self.num_qubits, which would only exist after init
        # was called.
        # For the moment we don't need a link for that as there is a link for the class already
        #
        # ValueError:
        # info['module'] is empty
        return None
    try:
        filepath = inspect.getsourcefile(obj)
        line_number = inspect.getsourcelines(obj)[1]
    except TypeError:
        # obj might be a property or a static class variable, e.g.,
        # loop_tag_id in which case obj is an int and inspect will fail
        try:
            # load obj one hierarchy higher (either class or module)
            new_higher_name = info['fullname'].split('.')
            module = importlib.import_module(info['module'])
            if len(new_higher_name) > 1:
                obj = module
            else:
                obj = recursive_getattr(module, '.' + '.'.join(new_higher_name[:-1]))

            filepath = inspect.getsourcefile(obj)
            line_number = inspect.getsourcelines(obj)[1]
        except AttributeError:
            return None

    # Calculate the relative path of the object with respect to the root directory (ie. projectq/some/path/to/a/file.py)
    projectq_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..')) + os.path.sep
    idx = len(projectq_path)
    relative_path = filepath[idx:]

    url = github_url + github_tag + "/" + relative_path + "#L" + str(line_number)
    return url


# ------------------------------------------------------------------------------

desc = importlib.import_module('package_description')
PackageDescription = desc.PackageDescription

# ------------------------------------------------------------------------------
# Define the description of ProjectQ packages and their submodules below.
#
# In order for the automatic package recognition to work properly, it is
# important that PackageDescription of sub-packages appear earlier in the list
# than their parent package (see for example libs.math and libs.revkit
# compared to libs).
#
# It is also possible to customize the presentation of submodules (see for
# example the setups and setups.decompositions) or even to have private
# sub-modules listed in the documentation page of a parent packages (see for
# example the cengines package)

descriptions = [
    PackageDescription('backends'),
    PackageDescription(
        'cengines',
        desc='''
The ProjectQ compiler engines package.
''',
    ),
    PackageDescription(
        'libs.math',
        desc='''
A tiny math library which will be extended throughout the next weeks. Right now, it only contains the math functions
necessary to run Beauregard's implementation of Shor's algorithm.
''',
    ),
    PackageDescription(
        'libs.revkit',
        desc='''
This library integrates `RevKit <https://msoeken.github.io/revkit.html>`_ into
ProjectQ to allow some automatic synthesis routines for reversible logic.  The
library adds the following operations that can be used to construct quantum
circuits:

- :class:`~projectq.libs.revkit.ControlFunctionOracle`: Synthesizes a reversible circuit from Boolean control function
- :class:`~projectq.libs.revkit.PermutationOracle`: Synthesizes a reversible circuit for a permutation
- :class:`~projectq.libs.revkit.PhaseOracle`: Synthesizes phase circuit from an arbitrary Boolean function

RevKit can be installed from PyPi with `pip install revkit`.

.. note::

    The RevKit Python module must be installed in order to use this ProjectQ library.

    There exist precompiled binaries in PyPi, as well as a source distribution.
    Note that a C++ compiler with C++17 support is required to build the RevKit
    python module from source.  Examples for compatible compilers are Clang
    6.0, GCC 7.3, and GCC 8.1.

The integration of RevKit into ProjectQ and other quantum programming languages is described in the paper

    * Mathias Soeken, Thomas Haener, and Martin Roetteler "Programming Quantum Computers Using Design Automation,"
      in: Design Automation and Test in Europe (2018) [`arXiv:1803.01022 <https://arxiv.org/abs/1803.01022>`_]
''',
        module_special_members='__init__,__or__',
    ),
    PackageDescription(
        'libs',
        desc='''
The library collection of ProjectQ which, for now, consists of a tiny math library and an interface library to RevKit.
Soon, more libraries will be added.
''',
    ),
    PackageDescription(
        'meta',
        desc='''
Contains meta statements which allow more optimal code while making it easier for users to write their code.
Examples are `with Compute`, followed by an automatic uncompute or `with Control`, which allows the user to condition
an entire code block upon the state of a qubit.
''',
    ),
    PackageDescription(
        'ops',
        desc='''
The operations collection consists of various default gates and is a work-in-progress, as users start to work with
ProjectQ.
''',
        module_special_members='__init__,__or__',
    ),
    PackageDescription(
        'setups.decompositions',
        desc='''
The decomposition package is a collection of gate decomposition / replacement rules which can be used by,
e.g., the AutoReplacer engine.
''',
    ),
    PackageDescription(
        'setups',
        desc='''
The setups package contains a collection of setups which can be loaded by the `MainEngine`.
Each setup contains a `get_engine_list` function which returns a list of compiler engines:

Example:
    .. code-block:: python

        import projectq.setups.ibm as ibm_setup
        from projectq import MainEngine

        eng = MainEngine(engine_list=ibm_setup.get_engine_list())
        # eng uses the default Simulator backend

The subpackage decompositions contains all the individual decomposition rules
which can be given to, e.g., an `AutoReplacer`.
''',
        submodules_desc='''
Each of the submodules contains a setup which can be used to specify the
`engine_list` used by the `MainEngine` :''',
        submodule_special_members='__init__',
    ),
    PackageDescription(
        'types',
        (
            'The types package contains quantum types such as Qubit, Qureg, and WeakQubitRef. With further development '
            'of the math library, also quantum integers, quantum fixed point numbers etc. will be added.'
        ),
    ),
]
# ------------------------------------------------------------------------------
# Automatically generate ReST files for each package of ProjectQ

docgen_path = os.path.join(os.path.dirname(os.path.abspath('__file__')), '_doc_gen')
if not os.path.isdir(docgen_path):
    os.mkdir(docgen_path)

for desc in descriptions:
    fname = os.path.join(docgen_path, f'projectq.{desc.name}.rst')
    lines = None
    if os.path.exists(fname):
        with open(fname) as fd:
            lines = [line[:-1] for line in fd.readlines()]

    new_lines = desc.get_ReST()

    if new_lines != lines:
        with open(fname, 'w') as fd:
            fd.write('\n'.join(desc.get_ReST()))
