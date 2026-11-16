.. _contributor_guide:

********************************
Contributing to Quantum Metal
********************************

Quantum Metal is an open-source project, and bug reports, fixes, new components,
tutorials and documentation are all welcome. This page covers how to set up,
check your work, and get a change merged. For how the code is organized, see
:doc:`architecture`.

The source is at https://github.com/qiskit-community/qiskit-metal. The PyPI
package is ``quantum-metal``; the import name is ``qiskit_metal``.

Set up
======

Quantum Metal uses `uv <https://docs.astral.sh/uv/>`_ for environments and
dependencies. Install uv, then fork and clone the repository:

.. code-block:: sh

   git clone https://github.com/<your-username>/qiskit-metal.git
   cd qiskit-metal
   uv sync --group test --group lint --extra full

The project supports Python 3.11 to 3.14 (``requires-python = ">=3.11,<3.15"``).
Dependencies are in ``pyproject.toml`` and locked in ``uv.lock``.

*Dependency groups* (``--group``) are development tools: ``test``, ``lint``,
``docs`` and ``jupyter``. No group is installed by default.
*Extras* (``--extra``) are optional features of the package: ``gui``, ``ansys``,
``mesh``, ``fem``, ``skfem`` and ``full`` (all of ``gui``, ``ansys`` and
``mesh``). The base install is "lite" (no Qt, no Ansys, no gmsh) and ``import
qiskit_metal`` and ``qm.view(design)`` must keep working there.

If you change dependencies in ``pyproject.toml``, run ``uv lock`` and commit
``uv.lock``; CI fails when they disagree. ``environment.yml`` must also agree with
``pyproject.toml`` (checked by ``scripts/check_env_consistency.py``).

Git hooks
---------

.. code-block:: sh

   ./hook_setup.sh

installs two hooks from ``hooks/``. The pre-commit hook runs ``ruff check`` and
``ruff format --check`` on staged Python files. The pre-push hook runs both on the
whole repository, the environment-file check, the qlibrary image check
(``scripts/check_qlibrary_images.py``), and, when a push touches ``_gui/`` or
``renderers/renderer_mpl/``, the on-screen GUI tests (needs a display). Skip them
for a work-in-progress push with ``git push --no-verify``.

Run the tests
=============

.. code-block:: sh

   QISKIT_METAL_HEADLESS=1 uv run --group test --extra full pytest tests/

Run one file with ``pytest tests/test_<name>.py``. ``QISKIT_METAL_HEADLESS=1``
keeps Qt out of the run. Tests that open the real Qt GUI and have crashed
natively (issue #1048) are skipped unless you pass ``--run-crashy-gui``; run them
when you touch ``_gui/``.

To test a single Python version the way CI does, use tox:

.. code-block:: sh

   uvx --with tox-uv tox -e py3.12

Add a test with every behavior change. Put it in an existing ``tests/test_*.py``
file when one fits, and use ``unittest``-style classes or plain pytest functions,
as the neighboring tests do.

Lint and format
===============

Linting and formatting use `ruff <https://docs.astral.sh/ruff/>`_. The rule set is
pinned explicitly in ``pyproject.toml`` under ``[tool.ruff.lint]``. CI checks the
whole repository:

.. code-block:: sh

   uvx ruff check .
   uvx ruff format .

Before you push, ``uvx ruff format --check .`` must be clean. The git hooks pin
ruff 0.15.14; CI uses the latest ruff.

Build the docs
==============

.. code-block:: sh

   uv run --python 3.12 --group docs sphinx-build -b html docs docs/_build/html

Open ``docs/_build/html/index.html``. Notebooks are not executed during the build;
the docs show their stored outputs. Set ``QISKIT_DOCS_BUILD_TUTORIALS`` to execute
them. The CI docs job runs ``tox -e docs`` (Python 3.12, lite install); for live
rebuilding while you edit, use ``tox -e docs-autobuild``.

The component gallery, its images and the component catalog are generated at build
time (``_dev/generate_qcomponent_gallery.py``); do not commit
``docs/qcomponents-gallery.rst``, ``docs/images/qlibrary/`` or ``docs/apidocs/*.png``.

Add or change a QComponent
==========================

Components live in ``src/qiskit_metal/qlibrary/``. Read
``qlibrary/core/base.py`` first, and compare your class with a similar one.

#. Subclass ``QComponent`` (or a more specific base) and implement ``make()``.
   Set ``default_options`` with a default and a unit for every key, and set
   ``component_metadata``.
#. Write the class docstring: a summary line, a description of every option with
   its default, the pin names, and the image directive written on two lines (the
   GUI scanner does not read the one-line form)::

      .. image::
          MyComponent.png

#. Generate the thumbnail and insert the directive where it is missing:

   .. code-block:: sh

      QISKIT_METAL_HEADLESS=1 uv run python _dev/generate_qlibrary_thumbnails.py \
          --write --inject-docstrings

   This writes ``src/qiskit_metal/_gui/_imgs/components/<ClassName>.png`` for the
   classes that lack one (``--force`` redraws all). Look at the PNG and the
   docstring before you commit both. If the component needs pins, anchors or
   non-default options to render (a route, for example), add a recipe to
   ``SPECIAL_RECIPES`` at the top of ``_dev/generate_qlibrary_thumbnails.py``. Check
   the references with
   ``uv run python _dev/generate_qlibrary_thumbnails.py --verify``.
#. Make the class appear in the API reference: add it to the matching
   ``autosummary`` list in the module docstring of
   ``src/qiskit_metal/qlibrary/__init__.py``, and add an import under
   ``if config.is_building_docs():`` in the same file.
#. Add tests: the instantiation, options and functionality files
   ``tests/test_qlibrary_1_instantiate.py``, ``tests/test_qlibrary_2_options.py``
   and ``tests/test_qlibrary_3_functionality.py``. Idempotency and pin geometry
   are checked for all components by ``tests/test_qlibrary_idempotency.py`` and
   ``tests/test_qlibrary_pin_sanity.py``. If you find a real pin bug in a component
   you are not changing, record it in that file's ``KNOWN_INWARD_PINS`` list
   rather than fixing it in the same change.
#. Add a short example or a section in a notebook (see below).

A custom display name in the GUI can be set with a ``.. meta::`` directive in the
class docstring (see ``qlibrary/couplers/cap_n_interdigital_tee.py``).

Changes to ``QComponent``, ``QDesign`` and ``QRenderer`` public signatures need a
deprecation path (see :ref:`deprecation_policy`).

Write or change a tutorial notebook
===================================

Notebooks live once, under ``docs/tut/`` (numbered tutorials, Appendix B and the
reference designs) or ``docs/circuit-examples/`` (circuit examples and full
design-flow examples). Input files and helper modules are in
``docs/tut/resources/``. There is no second copy; ``tutorials/`` holds only a
README that maps the old paths.

- The docs site renders the **stored outputs**. Keep them when you edit a notebook,
  and re-execute the notebook (on a scratch copy) when the code changes what it
  prints or draws. Check every figure.
- Stored outputs must not contain local paths, user names or log noise.
- List each notebook in exactly one ``nbgallery`` toctree with an explicit entry
  (no globs): a lesson on one of the four part pages under ``docs/tut/``, an example
  on ``docs/circuit-examples/index.rst``, a reproduction of a published device on
  ``docs/research.rst``. A notebook in no toctree triggers a Sphinx warning.
- Pure-Python notebooks (no Ansys, gmsh, Elmer, under about three minutes) go on
  ``_dev/notebooks-auto-refresh.txt``, which the ``tests-lite`` CI job executes.
- Hyphenated file names; Colab and Binder badges point at the notebook's own path
  under ``docs/``.

More detail is in ``.claude/skills/tutorial-notebook/SKILL.md``.

Docstrings
==========

Docstrings follow `Google style
<https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings>`__
and are parsed by Sphinx ``napoleon``. See
`docs/docstring_cheat_sheet.md
<https://github.com/qiskit-community/qiskit-metal/blob/main/docs/docstring_cheat_sheet.md>`__
for the layout of ``Args``, ``Returns`` and ``Raises``. When you change a public
function or class, update its docstring in the same change. Pages under
``docs/apidocs/*.rst`` list the modules; a new module needs an entry in the
``toctree`` of the page that holds its siblings.

.. _deprecation_policy:

Deprecations
============

Mark a deprecated feature with ``warnings.warn(..., DeprecationWarning,
stacklevel=2)``, name the replacement in the message, and keep the old behavior
working for at least one release after the one that carries the warning.

Hard-touch areas
================

These need maintainer approval before you change them, because they cannot be
validated without Ansys or an interactive Qt session:

- ``src/qiskit_metal/renderers/renderer_ansys/`` and ``renderer_ansys_pyaedt/``
  (HFSS and Q3D)
- ``src/qiskit_metal/_gui/``, including startup, teardown, stylesheet handling and
  stored window state; read ``docs/architecture/gui_crash_defenses.md`` first
- the pyEPR bridge (``renderer_ansys/parse.py``, ``solution_types.py``)
- public method signatures of ``QComponent``, ``QDesign`` and ``QRenderer``

If you find a bug there, open an issue (or note it in a test's ``KNOWN_*`` list)
instead of fixing it without validation.

Changelog
=========

Add one line to ``changelog.md`` under ``## Unreleased``, in ``### Added``,
``### Changed`` or ``### Fixed``. Say what changed and, for a fix, the symptom and
the issue number. The pull request template asks for this.

Branches and pull requests
==========================

#. Create a branch from ``main`` in your fork. If you plan a large change, open an
   issue first so the approach can be discussed.
#. Commit in small steps. Write commit messages and PR text that state **what
   changed and why, technically**, in a first line that says which part of the code
   is affected. Reference issues with ``Fixes #1234``. Leave out strategy and
   comments about people.
#. Run the tests, ``ruff check``, ``ruff format --check`` and, if you edited
   documentation, the docs build.
#. Open a pull request against ``main`` and fill in the template (issue links,
   tests, docs, summary). Open it as a draft if it is not ready for review.
#. Sign the contributor license agreement when the bot asks (below).

``main`` is protected: the pull request needs a code-owner review, the required
checks must pass, and the branch must be up to date with ``main`` before it merges.
The required checks are ``lint``, ``Build and Publish Documentation``,
``tests-python3.11-ubuntu-24.04``, ``tests-python3.12-ubuntu-24.04`` and
``tests-python3.14-windows-2025``. CI also runs ``format``, the lockfile and
environment-file checks, the qlibrary thumbnail check, the lite install, each
extra, minimum and pandas-3 dependency bounds, GUI tests on a virtual display, and
coverage; a failure in any of them needs a fix or an explanation. Only maintainers
merge, and merge by squashing the branch into one commit.

Code review is public and open to anyone; comments on open pull requests at
https://github.com/qiskit-community/qiskit-metal/pulls are welcome.

Contributor license agreement
-----------------------------

Contributors sign a CLA once, before their first contribution is merged. After you
open a pull request, the CLA bot comments with a link, and the required
``license/cla`` status turns green once you sign. The signing page is
https://cla-assistant.io/qiskit-community/qiskit-metal. The project is licensed
under Apache-2.0 (``LICENSE.txt``). No ``Signed-off-by`` line is required.

Report a bug or request a feature
=================================

Open an issue at https://github.com/qiskit-community/qiskit-metal/issues and choose
the bug, feature or documentation template. A useful bug report has:

.. code-block:: text

   Environment:  Quantum Metal version, Python version, OS, install command
                 (for example pip install "quantum-metal[gui]"), and which
                 backend is involved (core, GUI, HFSS, gmsh/Elmer, GDS)
   Current:      what happens
   Expected:     what should happen
   Reproduce:    a minimal, self-contained script (lite install if possible)
   Traceback:    the full error output

``python -c "import qiskit_metal; print(qiskit_metal.__version__)"`` prints the
version. For a feature, describe the use case and, if you have one, an idea for the
implementation. Issues labeled ``good first issue`` are a place to start.

Ask questions
=============

Open a GitHub issue or a discussion in the repository. The Discord server linked from the
:doc:`home page <index>` is for live community chat. Read the
:doc:`faq` first.

Code of conduct
===============

This project follows the
`code of conduct <https://github.com/qiskit-community/qiskit-metal/blob/main/CODE_OF_CONDUCT.md>`__.
