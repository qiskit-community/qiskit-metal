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

# pylint: disable=invalid-name
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
import sys

sys.path.insert(0, os.path.abspath('..'))

import qiskit_metal
import qiskit_sphinx_theme
"""
Sphinx documentation builder
"""

# The short X.Y version
version = qiskit_metal.__version__
# The full version, including alpha/beta/rc tags
release = qiskit_metal.__version__

rst_prolog = """
.. raw:: html

    <br><br><br>

.. |version| replace:: {0}
""".format(release)

nbsphinx_prolog = """
{% set docname = env.doc2path(env.docname, base=None)|replace("circuit-examples", "circuit-examples/") %}
{% set docname = docname|replace("A.Qubits", "A.Qubits/") %}
{% set docname = docname|replace("B.Resonators", "B.Resonators/") %}
{% set docname = docname|replace("C.Composite-bi-partite", "C.Composite-bi-partite/") %}
{% set docname = docname|replace("D.Qubit-couplers", "D.Qubit-couplers/") %}
{% set docname = docname|replace("E.Input-output-coupling", "E.Input-output-coupling/") %}
{% set docname = docname|replace("F.Small-quantum-chips", "F.Small-quantum-chips/") %}
{% set docname = docname|replace("full-design-flow-examples", "full-design-flow-examples/") %}
{% set docname = docname|replace("tut", "tut/") %}
{% set docname = docname|replace("1-Overview", "1-Overview/") %}
{% set docname = docname|replace("2-From-components-to-chip", "2-From-components-to-chip/") %}
{% set docname = docname|replace("3-Renderers", "3-Renderers/") %}
{% set docname = docname|replace("4-Analysis", "4-Analysis/") %}
{% set docname = docname|replace("quick-topics", "quick-topics/") %}

.. only:: html

    .. role:: raw-html(raw)
        :format: html

    .. raw:: html

        <br><br><br>

    .. note::
        This page was generated from `{{ docname }}`__.

    __ https://github.com/Qiskit/qiskit-metal/blob/main/docs/{{ docname }}
"""

nbsphinx_epilog = """
{% set docname = env.doc2path(env.docname, base=None) %}
.. only:: html

    .. role:: raw-html(raw)
        :format: html

    .. raw:: html

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
project = 'Qiskit Metal {}'.format(version)
copyright = '2019, Qiskit Development Team'  # pylint: disable=redefined-builtin
author = 'Qiskit Metal Development Team'
# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.extlinks',
    "nbsphinx",
    "qiskit_sphinx_theme",
]

html_static_path = ['_static']
templates_path = ['_templates']

exclude_patterns = [
    '_build', 'build', '*.ipynb', '**.ipynb_checkpoints', '_utility'
]

nbsphinx_execute_arguments = [
    "--InlineBackend.figure_formats={'svg', 'pdf'}",
    "--InlineBackend.rc={'figure.dpi': 96}",
]

nbsphinx_execute = os.getenv('QISKIT_DOCS_BUILD_TUTORIALS', 'never')

source_suffix = ['.rst', '.ipynb']

suppress_warnings = ['ref.ref']

nbsphinx_thumbnails = {
    'tut/quick-topics/Opening-documentation':
        '_static/qt-open-docs.png',
    'tut/4-Analysis/4.31-Plot-quantum-oscillator-wavefunction':
        '_static/4-31-plotting-wavefunction.png',
    'tut/4-Analysis/4.32-Transmon-analytics-HCPB':
        '_static/4-32-transmon-hcpb.png',
    'tut/4-Analysis/4.33-Transmon-analytics':
        '_static/4-33-transmon-analytics.png',
    'tut/4-Analysis/4.34-Transmon-qubit-CPB-hamiltonian-charge-basis':
        '_static/4-34-transmon-cpb.png',
    'tut/4-Analysis/4.15-CPW-kappa-calculation':
        '_static/4-15-kappa-calc.png',
    'tut/1-Overview/1.3-Saving-Your-Chip-Design':
        '_static/1-3-save.png',
}

# -----------------------------------------------------------------------------
# Autosummary
# -----------------------------------------------------------------------------
autosummary_generate = True

# -----------------------------------------------------------------------------
# Autodoc
# -----------------------------------------------------------------------------

autodoc_default_options = {
    'inherited-members': None,
}

autoclass_content = 'both'

# If true, figures, tables and code-blocks are automatically numbered if they
# have a caption.
numfig = True

# A dictionary mapping 'figure', 'table', 'code-block' and 'section' to
# strings that are used for format of figure numbers. As a special character,
# %s will be replaced to figure number.
numfig_format = {'table': 'Table %s'}
# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = 'en'

# A boolean that decides whether module names are prepended to all object names
# (for object types where a “module” of some kind is defined), e.g. for
# py:function directives.
add_module_names = False

# A list of prefixes that are ignored for sorting the Python module index
# (e.g., if this is set to ['foo.'], then foo.bar is shown under B, not F).
# This can be handy if you document a project that consists of a single
# package. Works only for the HTML builder currently.
modindex_common_prefix = ['qiskit_metal.']

# -- Configuration for extlinks extension ------------------------------------
# Refer to https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html

# -- Options for HTML output -------------------------------------------------

html_theme = "qiskit-ecosystem"
html_title = f"{project} {release}"

html_last_updated_fmt = '%Y/%m/%d'
