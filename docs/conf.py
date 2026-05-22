# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os

# Let Metal know we are building the docs.
# Environment variables are per-process, not global
os.environ["QISKIT_METAL_DOCS_BUILD"] = "1"

# In docs-build mode, ``renderers/__init__.py`` imports the Qt-coupled
# ``mpl_canvas`` module, which transitively  pulls
# ``matplotlib.backends.backend_qt5agg``. Without a hint, matplotlib's
# qt_compat probes for PyQt5 / PySide2 and fails on environments
# (RTD, Colab) that only have PySide6 — the project's actual Qt
# binding. Telling matplotlib to use PySide6 makes the legacy
# qt5agg alias resolve to the modern Qt-agnostic backend_qtagg.
os.environ.setdefault("QT_API", "pyside6")


# Pre-mock heavy / native-extension dependencies BEFORE importing
# qiskit_metal. As of v0.7.0 the docs tox env installs only the
# lite package — PySide6, pyaedt, pyEPR, gmsh, qdarkstyle, IPython
# are not on disk. ``autodoc_mock_imports`` (set further down) only
# kicks in for autodoc's cross-reference walk; it does not protect
# THIS file's own ``import qiskit_metal`` below, which transitively
# touches ``mpl_canvas`` → ``matplotlib.backends.backend_qt5agg`` →
# ``from PySide6 import ...`` and various ``_gui/`` widgets that
# subclass ``QTableView`` etc.
#
# Use sphinx's own ``_MockObject`` (rather than ``unittest.mock.
# MagicMock``) because the former handles being used as a class
# base — Python's ``MagicMock`` triggers ``TypeError: metaclass
# conflict`` when two mocked classes are listed as bases.
import sys
from sphinx.ext.autodoc.mock import _MockModule

_MOCKED_MODULES = [
    "PySide6",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "qdarkstyle",
    "gmsh",
    "pyEPR",
    "pyaedt",
    "ansys",
    "ansys.aedt",
    "ansys.aedt.core",
    "IPython",
    "IPython.core",
    "IPython.core.magic",
    "IPython.display",
    "matplotlib.backends.backend_qt5agg",
    "matplotlib.backends.backend_qtagg",
    "matplotlib.backends.qt_compat",
]
for _mod in _MOCKED_MODULES:
    sys.modules.setdefault(_mod, _MockModule(_mod))


import qiskit_metal
import qiskit_sphinx_theme

"""
Sphinx documentation builder
"""

# The short X.Y version
version = qiskit_metal.__version__
# The full version, including alpha/beta/rc tags
release = qiskit_metal.__version__

rst_prolog = f"""
.. |version| replace:: {release}

.. role:: rc
.. role:: mpltype

"""

nbsphinx_prolog = """
{% set docname = env.doc2path(env.docname, base=None) %}

.. only:: html

    .. role:: raw-html(raw)
        :format: html

    .. note::
        This page was generated from `{{ docname }}`__.

    __ https://github.com/Qiskit/qiskit-metal/blob/main/docs/{{ docname }}
"""

# This is added to the end of each rendered notebook html
nbsphinx_epilog = """
{% set docname = env.doc2path(env.docname, base=None) %}
.. only:: html

    .. role:: raw-html(raw)
        :format: html

    .. raw:: html

        <br><br>
        <h3>For more information, review the <b>Introduction to Quantum Computing and Quantum Hardware</b> lectures below</h3>
        <div style="border:solid 1 px #990000;">
        <table>
        <tr><td><ul><li>Superconducting Qubits I: Quantizing a Harmonic Oscillator, Josephson Junctions Part 1</ul></td>
        <td width="15%"><a href="https://www.youtube.com/watch?v=eZJjQGu85Ps&list=PLOFEBzvs-VvrXTMy5Y2IqmSaUjfnhvBHR">Lecture Video</a></td>
        <td width="15%"><a href="https://github.com/qiskit-community/intro-to-quantum-computing-and-quantum-hardware/blob/master/lectures/introqcqh-lecture-notes-6.pdf?raw=true">Lecture Notes</a></td>
        <td width="5%"><a href="https://github.com/qiskit-community/intro-to-quantum-computing-and-quantum-hardware/blob/master/labs/introqcqh-lab-6.zip?raw=true">Lab</a></td></tr>
        <tr><td><ul><li>Superconducting Qubits I: Quantizing a Harmonic Oscillator, Josephson Junctions Part 2</ul></td>
        <td><a href="https://www.youtube.com/watch?v=SDiiFOham6Y&list=PLOFEBzvs-VvrXTMy5Y2IqmSaUjfnhvBHR">Lecture Video</a></td>
        <td><a href="https://github.com/qiskit-community/intro-to-quantum-computing-and-quantum-hardware/blob/master/lectures/introqcqh-lecture-notes-6.pdf?raw=true">Lecture Notes</a></td>
        <td><a href="https://github.com/qiskit-community/intro-to-quantum-computing-and-quantum-hardware/blob/master/labs/introqcqh-lab-6.zip?raw=true">Lab</a></td></tr>
        <tr><td><ul><li>Superconducting Qubits I: Quantizing a Harmonic Oscillator, Josephson Junctions Part 3</ul></td>
        <td><a href="https://www.youtube.com/watch?v=hGBAz63NIH8&list=PLOFEBzvs-VvrXTMy5Y2IqmSaUjfnhvBHR">Lecture Video</a></td>
        <td><a href="https://github.com/qiskit-community/intro-to-quantum-computing-and-quantum-hardware/blob/master/lectures/introqcqh-lecture-notes-6.pdf?raw=true">Lecture Notes</a></td>
        <td><a href="https://github.com/qiskit-community/intro-to-quantum-computing-and-quantum-hardware/blob/master/labs/introqcqh-lab-6.zip?raw=true">Lab</a></td></tr>
        <tr><td><ul><li>Superconducting Qubits II: Circuit Quantum Electrodynamics, Readout and Calibration Methods Part 1</ul></td>
        <td><a href="https://www.youtube.com/watch?v=dmYnfGo-8eM&list=PLOFEBzvs-VvrXTMy5Y2IqmSaUjfnhvBHR">Lecture Video</a></td>
        <td><a href="https://github.com/qiskit-community/intro-to-quantum-computing-and-quantum-hardware/blob/master/lectures/introqcqh-lecture-notes-7.pdf?raw=true">Lecture Notes</a></td>
        <td><a href="https://github.com/qiskit-community/intro-to-quantum-computing-and-quantum-hardware/blob/master/labs/introqcqh-lab-7.zip?raw=true">Lab</a></td></tr>
        <tr><td><ul><li>Superconducting Qubits II: Circuit Quantum Electrodynamics, Readout and Calibration Methods Part 2</ul></td>
        <td><a href="https://www.youtube.com/watch?v=jUPAeOoZpEU&list=PLOFEBzvs-VvrXTMy5Y2IqmSaUjfnhvBHR">Lecture Video</a></td>
        <td><a href="https://github.com/qiskit-community/intro-to-quantum-computing-and-quantum-hardware/blob/master/lectures/introqcqh-lecture-notes-7.pdf?raw=true">Lecture Notes</a></td>
        <td><a href="https://github.com/qiskit-community/intro-to-quantum-computing-and-quantum-hardware/blob/master/labs/introqcqh-lab-7.zip?raw=true">Lab</a></td></tr>
        <tr><td><ul><li>Superconducting Qubits II: Circuit Quantum Electrodynamics, Readout and Calibration Methods Part 3</ul></td>
        <td><a href="https://www.youtube.com/watch?v=_IpCwMvc0dA&list=PLOFEBzvs-VvrXTMy5Y2IqmSaUjfnhvBHR">Lecture Video</a></td>
        <td><a href="https://github.com/qiskit-community/intro-to-quantum-computing-and-quantum-hardware/blob/master/lectures/introqcqh-lecture-notes-7.pdf?raw=true">Lecture Notes</a></td>
        <td><a href="https://github.com/qiskit-community/intro-to-quantum-computing-and-quantum-hardware/blob/master/labs/introqcqh-lab-7.zip?raw=true">Lab</a></td></tr></table>
        </div>

"""

# -- Project information -----------------------------------------------------
project = "Quantum Metal"  # {version}
copyright = "Quantum Metal Community; 2019-2025 Qiskit Development Team"
author = qiskit_metal.__author__
# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.extlinks",
    "nbsphinx",
    "qiskit_sphinx_theme",
    "sphinx_design",
    # JupyterLite — builds an in-browser Jupyter runtime into the docs
    # site so visitors can run any tutorial without installing anything.
    # See the ``jupyterlite_*`` config block further down for content
    # selection and kernel choice.
    "jupyterlite_sphinx",
]

# --- JupyterLite ----------------------------------------------------------
# Ship a JupyterLite instance under ``/lite/`` on the docs site with the
# tutorial notebooks pre-loaded. nbsphinx pages automatically gain a
# "Try it live" / "Launch in JupyterLite" button.
#
# Trade-off: build time +1-2 min, output size +~20 MB. Worth it — every
# tutorial becomes a zero-install try-it experience for newcomers, which
# is the single biggest adoption lever for a library that already has a
# lite-by-default install path.
#
# The Pyodide kernel runs Python in WebAssembly. Quantum Metal's lite
# install (no Qt / Ansys / gmsh) works in Pyodide; the GUI / Ansys / FEM
# extras don't, so we only surface the lite-compatible tutorials by
# default (Section 1 + most of Section 2).
jupyterlite_contents = ["tutorials/"]
jupyterlite_dir = "."
jupyterlite_silence = True  # quiet build-time chatter
# Each tutorial notebook gets a "Launch in JupyterLite" link in its header
# (default behavior — no extra config needed since contents include
# the ``tutorials/`` tree).

# Intersphinx — resolve cross-references to external project docs so that
# type annotations like ``logging.Logger`` and ``matplotlib.figure.Figure``
# in docstrings become hyperlinks instead of "unresolved reference"
# warnings. Without this, bare names like ``logger`` and ``figure`` in
# Napoleon-style docstrings get resolved against every ``logger`` /
# ``figure`` attribute in our own codebase, causing the "more than one
# target found" ambiguity warnings that previously flooded the build.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}

# When autodoc encounters a bare type name in a docstring that matches an
# attribute on many of our classes (``logger``, ``figure``, ...), Sphinx
# emits "more than one target found for cross-reference" warnings. The
# real fix is in the docstrings themselves (use qualified types like
# ``logging.Logger`` or ``matplotlib.figure.Figure``), but this list
# keeps stragglers from breaking builds and matches the patterns that
# have shown up historically.
nitpick_ignore = [
    ("py:attr", "logger"),
    ("py:attr", "figure"),
    ("py:class", "logger"),
    ("py:class", "figure"),
]

# Suppress specific warning categories that are unavoidable trade-offs:
#
# - ``toc.not_included``: the ``docs/apidocs/qiskit_metal.analyses.*.rst``
#   stubs are not toctreed (see comment block in ``docs/apidocs/analyses.rst``
#   for the rationale — adding a toctree there would re-document each class
#   via two paths and trigger 600+ ``duplicate object description`` warnings).
#   Re-classify these stubs as orphans by suppressing the warning instead.
# - ``misc.highlighting_failure``: occasional Pygments hiccups on
#   notebook code that has unicode quirks; harmless.

html_static_path = ["_static"]
templates_path = ["_templates"]

exclude_patterns = [
    "_build",
    "build",
    "**.ipynb_checkpoints",
    "_utility",  # '*.ipynb',
    "_archive",  # archived configs / configs kept for revival
    "stubs/**",  # autosummary stub files are generated but not included in any toctree
]

nbsphinx_execute_arguments = [
    "--InlineBackend.figure_formats={'svg', 'pdf'}",
    "--InlineBackend.rc={'figure.dpi': 96}",
]

nbsphinx_execute = os.getenv("QISKIT_DOCS_BUILD_TUTORIALS", "never")

# The "ipython3" Pygments lexer that nbsphinx emits for code cells is
# registered by the ``ipython`` package — see the ``ipython`` entry in
# pyproject.toml's ``[dependency-groups] docs`` for the reason.

# Let Sphinx/nbsphinx choose the appropriate parser for each suffix.
# source_suffix = ['.rst', '.ipynb']
source_suffix = {".rst": "restructuredtext"}

suppress_warnings = ["ref.ref"]

nbsphinx_thumbnails = {
    "tut/quick-topics/Opening-documentation": "_static/qt-open-docs.png",
    "tut/4-Analysis/4.31-Plot-quantum-oscillator-wavefunction": "_static/4-31-plotting-wavefunction.png",
    "tut/4-Analysis/4.32-Transmon-analytics-HCPB": "_static/4-32-transmon-hcpb.png",
    "tut/4-Analysis/4.33-Transmon-analytics": "_static/4-33-transmon-analytics.png",
    "tut/4-Analysis/4.34-Transmon-qubit-CPB-hamiltonian-charge-basis": "_static/4-34-transmon-cpb.png",
    "tut/4-Analysis/4.15-CPW-kappa-calculation": "_static/4-15-kappa-calc.png",
}

# -----------------------------------------------------------------------------
# Autosummary
# -----------------------------------------------------------------------------
autosummary_generate = True

# -----------------------------------------------------------------------------
# Autodoc
# -----------------------------------------------------------------------------

autodoc_default_options = {
    "inherited-members": None,
}

autoclass_content = "both"

# If true, figures, tables and code-blocks are automatically numbered if they
# have a caption.
numfig = True

# Mock heavy/external modules so autodoc does not pull in their docstrings
# (e.g., matplotlib roles that are not defined in our docs build).
#
# As of v0.7.0 the docs tox env installs only the base/lite package
# (no [full] extras). The heavies below are not on disk during a docs
# build; mocking them keeps autodoc's cross-reference walk from blowing
# up when it follows type hints into Qt / pyEPR / pyaedt / gmsh /
# IPython symbols. With these mocks in place, the renderer modules can
# import cleanly under autodoc even though their native libs are absent.
autodoc_mock_imports = [
    "matplotlib",
    "PySide6",
    "qdarkstyle",
    "pyEPR",
    "pyaedt",
    "ansys",  # ansys.aedt.core etc.
    "gmsh",
    "IPython",  # Jupyter-environment only; lazified in display.py
]

# A dictionary mapping 'figure', 'table', 'code-block' and 'section' to
# strings that are used for format of figure numbers. As a special character,
# %s will be replaced to figure number.
numfig_format = {"table": "Table %s"}
# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# A boolean that decides whether module names are prepended to all object names
# (for object types where a “module” of some kind is defined), e.g. for
# py:function directives.
add_module_names = False

# A list of prefixes that are ignored for sorting the Python module index
# (e.g., if this is set to ['foo.'], then foo.bar is shown under B, not F).
# This can be handy if you document a project that consists of a single
# package. Works only for the HTML builder currently.
modindex_common_prefix = ["qiskit_metal."]

# -- Configuration for extlinks extension ------------------------------------
# Refer to https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html

# -- Options for HTML output -------------------------------------------------

html_theme = "qiskit-ecosystem"
html_title = f"{project} {release}"

html_last_updated_fmt = "%Y/%m/%d"
