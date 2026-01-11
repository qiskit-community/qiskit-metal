.. _contributor_guide:

********************************
Contributing to Quantum Metal
********************************


.. attention::
   Quantum Metal is undergoing a major transition to become Quantum Metal. Some of the instructions below might be outdated and will be updated soon.

Quantum Metal is an open-source project committed to bringing quantum hardware design to
people of all backgrounds. This page describes how you can join the Quantum Metal
community in this goal.


.. _where_things_are:

=================
Where Things Are
=================

The source code for Quantum Metal is currently located in the `Quantum Community GitHub organization <https://github.com/Quantum-community>`__,
as part of the larger umbrella of community-driven Quantum projects. This repository will change ownership in the future. 


==========================================
Reporting Bugs and Requesting Enhancements
==========================================

When you encounter a problem, please open an issue in the
issue tracker: https://github.com/Quantum/Quantum-metal/issues

When reporting an issue, please follow this template::

   <!--- Provide a general summary of the issue in the Title above -->

   ## Expected Behavior
   <!--- Tell us what should happen -->

   ## Current Behavior
   <!--- Tell us what happens instead of the expected behavior -->

   ## System Settings
   <!--- Post the results of `metal.about()` here. --->

   ## Steps to Reproduce
   <!--- Provide a link to a live example, or an unambiguous set of steps to -->
   <!--- reproduce this bug. Include code to reproduce, if relevant -->
   1.
   2.
   3.

   ## Detailed Description
   <!--- Provide a detailed description of the change or addition you are proposing -->

   ## Possible Implementation
   <!--- Not obligatory, but suggest an idea for implementing addition or change -->

If you have an idea for a new feature, please open an **Enhancement** issue in
the repository issue tracker. Opening an issue starts a discussion with the team about your idea, how it
fits in with the project, how it can be implemented, etc.


=========================================
Contributing Code
=========================================


Development Setup for Quantum Metal v0.5+
-----------------------------------------

Quantum Metal uses `uv <https://docs.astral.sh/uv/>`_ for project and dependency management. This guide describes how to set up your local development environment. First, install uv on your system as described by the `instructions here <https://docs.astral.sh/uv/getting-started/installation/>`_.


Development (virtual) environments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The next few paragraphs describe the setup. We recommend reading through it at least once before you start making contributions. Skip to the next section for instructions on how to activate venvs, run tasks, etc.

All development activities should be carried out inside Python virtual environments (venvs). Thankfully, uv can manage all our venvs for us. In addition to this, we can use tox to orchestrate venvs to fit the needs of different development tasks: testing, linting, building docs, etc.

All information about project dependencies can be found in the ``pyproject.toml`` file located in the root directory of this repository. The direct project dependencies are listed in the ``requirements`` section of the ``[project]`` table. These are required to run user code.

Development dependencies are specified in the ``[dependency-groups]`` table. There are four groups available: ``test``, ``lint``, ``docs``, and ``jupyter``. These are used by tox to create a virtual environment with the required dependencies for each task. At the time of writing, the ``jupyter`` group is available for convenience, but unused in tasks.
See `PEP 735-Dependency Groups in pyproject.toml <https://peps.python.org/pep-0735/>`_ and the `PyPA specification page for dependency groups <https://packaging.python.org/en/latest/specifications/dependency-groups/#dependency-groups>`_ for more information.

The file ``uv.lock`` lists "locked" versions for all dependencies listed in ``pyproject.toml`` across different platforms. This allows uv to create reproducible environments. At present, tox does not create virtual environments using the lockfile, but the `tox-uv <https://github.com/tox-dev/tox-uv>`_ plugin allows for this functionality to be enabled by setting the ``runner`` configuration variable in each tox task, as described `here <https://github.com/tox-dev/tox-uv?tab=readme-ov-file#uvlock-support>`_.


Running tests
^^^^^^^^^^^^^

Tox is configured to run tests (using pytest) for Python 3.10–3.12. Use the following command to run tests for all three versions::

   tox -m test

We use the `pytest-rich <https://github.com/nicoddemus/pytest-rich>`_ plugin to provide rich output of testing progress. Tests can be run for specific versions using the following command::

   tox -e py3.12  # replace 3.12 with the version you want to run

Linting and Formatting
^^^^^^^^^^^^^^^^^^^^^^^

We use `ruff <https://docs.astral.sh/ruff/>`_ for linting and formatting. Our linting configuration is described in ``pyproject.toml`` under the ``[tool.ruff.lint]`` table. Note that this configuration is a work in progress and likely to change until further notice. The linter can be run using the following command::

   tox -e lint

This will show all the linting errors and the location for each. For a summary showing the number of violations of each linting rule, use the following command::

   tox -e lint -- --statistics

Formatting for the whole repository can be performed using the following command::

   tox -e format

Note that we have not yet settled on a formatting configuration other than default options provided by ruff, but this may change.




Style Guide
-----------

.. attention::
   The style guide presented below is being deprecated. Quantum Metal v0.5+ uses ruff for linting and formatting. An updated style guide will be added soon.

To enforce a consistent code style in the project, we use customized `Pylint
<https://www.pylint.org>`__ for linting and `YAPF`<https://github.com/google/yapf>__ with the `Google style
<https://google.github.io/styleguide/pyguide.html>`__ for auto formatting. The custom
`.pylintrc` and `.style.yapf` files is located in the root of the repository.
Our CI pipeline will enforce these styles when you make the pull request.

Contributor License Agreement
-----------------------------

Before you can submit any code, all contributors must sign a
contributor license agreement (CLA). By signing a CLA, you're attesting
that you are the author of the contribution, and that you're freely
contributing it under the terms of the Apache-2.0 license.

When you contribute to Quantum Metal with a new pull request,
a bot will evaluate whether you have signed the CLA. If required, the
bot will comment on the pull request, including a link to accept the
agreement. The `individual CLA <https://Qiskit.org/license/Qiskit-cla.pdf>`__
document is available for review as a PDF.

.. note::
   If your contribution is part of your employment or your contribution
   is the property of your employer, then you will more than likely need to sign a
   `corporate CLA <https://Qiskit.org/license/Qiskit-corporate-cla.pdf>`__ too and
   email it to us at <Qiskit@us.ibm.com>.



Pull Requests
-------------

We use `GitHub pull requests
<https://help.github.com/articles/about-pull-requests>`__ to accept
contributions.

While not required, opening a new issue about the bug you're fixing or the
feature you're working on before you open a pull request is an important step
in starting a discussion with the community about your work. The issue gives us
a place to talk about the idea and how we can work together to implement it in
the code. It also lets the community know what you're working on, and if you
need help, you can reference the issue when discussing it with other community
and team members.

If you've written some code but need help finishing it, want to get initial
feedback on it prior to finishing it, or want to share it and discuss prior
to finishing the implementation, you can open a *Work in Progress* pull request.
This will indicate to reviewers that the code in
the PR isn't in its final state and will change. It also means that we will
not merge the commit until it is finished. You or a reviewer can remove the
WIP status when the code is ready to be fully reviewed for merging.



Code Review
-----------

Code review is done in the open and is open to anyone. While only maintainers have
access to merge commits, community feedback on pull requests is extremely valuable.
It is also a good mechanism to learn about the code base. You can
view a list of all open pull requests at https://github.com/qiskit-community/qiskit-metal/pulls


Commit Messages
---------------

The content of the commit message describing a change is just as important as the
change itself. The commit message provides the context for
not only code review but also the change history in the git log. A detailed
commit message will make it easier for your code to be reviewed, and will also provide
context to the change when someone looks at it in the future. When writing a commit
message, remember these important details:

Do not assume the reviewer understands what the original problem was.
   When reading an issue, after a number of back & forth comments, it is often
   clear what the root cause problem is. The commit message should have a clear
   statement as to what the original problem is. The bug is merely interesting
   historical background on *how* the problem was identified. It should be
   possible to review a proposed patch for correctness from the commit message,
   without needing to read the bug ticket.

Do not assume the code is self-evident/self-documenting.
   What is self-evident to one person, might not be clear to another person. Always
   document what the original problem was and how it is being fixed, for any change
   except the most obvious typos, or whitespace-only commits.

Describe why a change is being made.
   A common mistake is only to document how the code has been written, without
   describing *why* the developer chose to do it that way. Certainly, you should describe
   the overall code structure, particularly for large changes, but more importantly,
   be sure to describe the intent/motivation behind the changes.

Read the commit message to see if it hints at improved code structure.
   Often when describing a large commit message, it becomes obvious that a commit
   should have been split into two or more parts. Don't be afraid to go back
   and rebase the change to split it up into separate pull requests.

Ensure sufficient information to decide whether to review.
   When GitHub sends out email alerts for new pull request submissions, there is
   minimal information included - usually just the commit message and the list of
   files changes. Because of the high volume of patches, a commit message must
   contain sufficient information for potential reviewers to find the patch that
   they need to review.

The first commit line is the most important.
   In Git commits, the first line of the commit message has special significance.
   It is used as the default pull request title, email notification subject line,
   git annotate messages, gitk viewer annotations, merge commit messages, and many
   more places where space is at a premium. As well as summarizing the change
   itself, it should take care to detail what part of the code is affected.

   In addition, the first line of the commit message becomes an entry in the
   generated changelog if the PR is tagged as being included in the changelog.
   It is critically important that you write clear and succinct summary lines.

Describe any limitations of the current code.
   If the code being changed still has future scope for improvements, or any known
   limitations, mention these in the commit message. This demonstrates to the
   reviewer that the broader picture has been considered, and what tradeoffs have
   been done in terms of short-term goals versus long-term wishes.

Include references to issues.
   If the commit fixes are related to an issue, make sure you annotate that in
   the commit message. Use the syntax::

       Fixes #1234

   if it fixes the issue (GitHub will close the issue when the PR merges).

The main rule to follow is:

The commit message must contain all the information required to fully
understand and review the patch for correctness. Less is not more.



Documenting Your Code
---------------------

If you make a change to an element, make sure you update the associated
*docstrings* and parts of the documentation under ``docs/apidocs`` in the
corresponding repo. To locally build the element-specific
documentation, run ``tox -e docs`` to compile and build the
documentation locally and save the output to ``docs/_build/html``.
Additionally, the Docs CI job on GitHub Actions will run this and deploy to Github Pages.

You can open a `documentation issue <https://github.com/qiskit-community/qiskit-metal/issues/new/choose>`__
if you see doc bugs, have a new feature that needs to be documented, or think
that material could be added to the existing docs.



Good First Contributions
------------------------

If you would like to contribute to Quantum Metal, but aren't sure
where to get started, the ``good first issue`` label on issues for a project
highlights items appropriate for people new to the project.
These are all issues that have been reviewed and tagged by contributors
as something a new contributor should be able to work on. In other
words, intimate familiarity with Quantum Metal is not a requirement to develop a fix
for the issue.



Deprecation Policy
------------------

Quantum Metal users need to know if a feature or an API they rely
upon will continue to be supported by the software tomorrow. Knowing under which conditions
the project can remove (or change in a backwards-incompatible manner) a feature or
API is important to the user. To manage expectations, the following policy is how API
and feature deprecation/removal is handled by Quantum Metal:

1. Features, APIs, or configuration options are marked deprecated in the code.
Appropriate ``DeprecationWarning`` class warnings will be sent to the user. The
deprecated code will be frozen and receive only minimal maintenance (just so
that it continues to work as-is).

2. A migration path will be documented for current users of the feature. This
will be outlined in the both the release notes adding the deprecation, and the
release notes removing the feature at the completion of the deprecation cycle.
If feasible, the warning message will also include the migration
path. A migration path might be "stop using that feature", but in such cases
it is necessary to first judge how widely used and/or important the feature
is to users, in order to determine a reasonable obsolescence date.

3. An obsolescence date for the feature will be set. The feature must remain
intact and working (although with the proper warning being emitted) in all
releases pushed until after that obsolescence date. At the very minimum, the
feature (or API, or configuration option) should be marked as deprecated (and
continue to be supported) for at least three months of linear time from the release
date of the first release to include the deprecation warning.

Note that this delay is a minimum. For significant features, it is recommended
that the deprecated feature appears for at least double that time. Also, per
the stable branch policy, deprecation removals can only occur during minor
version releases; they are not appropriate for backporting.



Deprecation Warnings
--------------------

The proper way to raise a deprecation warning is to use the ``warn`` function
from the `warnings module <https://docs.python.org/3/library/warnings.html>`__
in the Python standard library. The warning category class
should be a ``DeprecationWarning``. An example would be::

 import warnings

 def foo(input):
     warnings.warn('The Quantum.foo() function is deprecated as of 0.9.0, and '
                   'will be removed no earlier than 3 months after that '
                   'release date. You should use the Quantum.bar() function '
                   'instead.', DeprecationWarning, stacklevel=2)

One thing to note here is the ``stack_level`` kwarg on the warn() call. This
argument is used to specify which level in the call stack will be used as
the line initiating the warning. Typically, ``stack_level`` should be set to 2,
as this will show the line calling the context where the warning was raised.
In the above example, it would be the caller of ``foo()``. If you did not set this,
the warning would show that it was caused by the line in the foo()
function, which is not helpful for users trying to determine the origin
of a deprecated call. However, this value may be adjusted, depending on the call
stack and where ``warn()`` gets called from. For example, if the warning is always
raised by a private method that only has one caller, ``stack_level=3`` might be
appropriate.



Stable Branch Policy
--------------------

The stable branch is intended to be a safe source of fixes for high-impact
bugs and security issues that have been fixed on master since a
release. When reviewing a stable branch PR, we must balance the risk
of any given patch with the value that it will provide to users of the
stable branch. Only a limited class of changes are appropriate for
inclusion on the stable branch. A large, risky patch for a major issue
might make sense, as might a trivial fix for a fairly obscure error-handling
case. A number of factors must be weighed when considering a
change:

-   The risk of regression: even the tiniest changes carry some risk of
    breaking something, and we really want to avoid regressions on the
    stable branch.
-   The user visibility benefit: are we fixing something that users might
    actually notice, and if so, how important is it?
-   How self-contained the fix is: if it fixes a significant issue but
    also refactors a lot of code, it's probably worth thinking about
    what a less risky fix might look like.
-   Whether the fix is already on master: a change must be a backport of
    a change already merged onto master, unless the change simply does
    not make sense on master.



Backporting procedure:
----------------------

When backporting a patch from master to stable, we want to keep a
reference to the change on main. When you create the branch for the
stable PR, use::

    $ git cherry-pick -x $main_commit_id

However, this only works for small self-contained patches from main.
If you need to backport a subset of a larger commit (from a squashed PR,
for example) from main, do this manually. In these cases, add::

    Backported from: #main pr number

so that we can track the source of the change subset, even if
a strict cherry-pick doesn\'t make sense.

If the patch you're proposing will not cherry-pick cleanly, you can help
by resolving the conflicts yourself and proposing the resulting patch.
Please keep Conflicts lines in the commit message to help review of the
stable patch.



Backport labels
^^^^^^^^^^^^^^^

Bugs or PRs tagged with ``stable backport potential`` are bugs
that apply to the stable release too and may be suitable for
backporting once a fix lands in main. Once the backport has been
proposed, the tag should be removed.

Include ``[Stable]`` in the title of the PR against the stable branch,
as a sign that setting the target branch as stable was not
a mistake. Also, reference to the PR number in main that you are
porting.



Custom Names and Images for QComponents
----------------------------------------

When adding new qcomponents, new images for these components go
in the following directory::

    qiskit-metal/qiskit_metal/_gui/_imgs/components

In the qcomponent file itself, the following attribute somewhere in
the comments will tell the application which image corresponds to
this file::

    .. image::
        myqcomponent.png

The meta attribute can used to add a custom display name to the file::

    .. meta::
        MyQComponent

If you had a file with the previous two attributes, the user is telling
the Quantum metal application that the image for the qcomponent is named
``myqcomponent.png`` and is located in::

   qiskit-metal/qiskit_metal/_gui/_imgs/components/myqcomponent.png

and that they want the display name of this file to be ``MyQComponent``.



==============================
Contributing to Documentation
==============================

Quantum Metal documentation is shaped by the `docs as code
<https://www.writethedocs.org/guide/docs-as-code/>`__ philosophy, primarily
drawn from Quantum Metal code comments in the `style of API documentation
<https://alistapart.com/article/the-ten-essentials-for-good-api-documentation/>`__.

The documentation is built using `Sphinx
<http://www.sphinx-doc.org/en/master/>`__. The majority of documentation, under
`API Reference <https://Quantum-community.github.io/Quantum-metal/overview.html>`__, is
drawn from code comments in the repositories listed in :ref:`where_things_are`.

Documentation Structure
--------------------------------

The way documentation is structured in Quantum Metal is to push as much of the actual
documentation into the docstrings as possible. This makes it easier for
additions and corrections to be made during development, because the majority
of the documentation lives near the code being changed. There are three levels in
the normal documentation structure in Metal:

The ``.rst`` files in the ``docs/apidocs``
   These files are used to tell Sphinx which modules to include in the rendered
   documentation. This contains two pieces of information:
   an `internal reference <http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#reference-names>`__
   or `cross reference <https://www.sphinx-doc.org/en/latest/usage/restructuredtext/roles.html#ref-role>`__
   to the module, which can be used for internal links
   inside the documentation, and an `automodule directive <http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`__
   used to parse the
   module docstrings from a specified import path. For example, the analyses.rst
   file contains
   
   .. code-block:: rst

      .. automodule:: qiskit_metal.analyses
         :no-members:
         :no-inherited-members:
         :no-special-members:

   If you're adding a new ``.rst`` file for a new module's documentation, make
   sure to add it to the `toctree <https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#table-of-contents>`__
   in that file.

The module-level docstring
   This docstring is at the module
   level for the module specified in the ``automodule`` directive in the rst file.
   If the module specified is a directory/namespace, the docstring should be
   specified in the ``__init__.py`` file for that directory. This module-level
   docstring contains more details about the module being documented.
   The normal structure to this docstring is to outline all the classes and
   functions of the public API that are contained in that module. This is typically
   done using the `autosummary directive <https://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html>`__
   (or `autodoc directives <http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`__
   directly if the module is simple, such as in the case of ``Quantum.execute``). The
   autosummary directive is used to autodoc a list of different Python elements
   (classes, functions, etc.) directly without having to manually call out the
   autodoc directives for each one. The module-level docstring is where to
   provide a high-level overview of what functionality the module provides.
   This is normally done by grouping the different
   components of the public API together into multiple subsections.

   For example, as in the previous dagcircuit module example, the
   contents of the module docstring for ``Quantum/analyses/__init__.py`` would
   be

   .. code-block:: python3
      
      """
      Analyses (:mod:`qiskit_metal.analyses`)
      =======================================

      .. currentmodule:: qiskit_metal.analyses

      Module containing all Qiskit Metal analyses.

      Submodules
      ----------

      .. autosummary::
         :toctree:

         em.cpw_calculations
         quantization.lumped_capacitive
      """



   .. note::

      This is just an example and the actual module docstring for the dagcircuit
      module might diverge from this.

The actual docstring for the elements listed in the module docstring
   You should strive to document thoroughly all the public interfaces
   exposed using examples when necessary. For docstrings, `Google Python Style
   Docstrings <https://google.github.io/styleguide/pyguide.html?showone=Comments#38-comments-and-docstrings>`__
   are used. This is parsed using the `napoleon
   sphinx extension <https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html>`__.
   The `napoleon documentation <https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`__
   contains a good example of how docstrings should be formatted.

Rebuilding Documentation
------------------------

As you make changes to your local RST files, you can update your
HTML files by navigating to `/docs/` and running:

.. code-block:: sh

   uv run --group docs make html

For a fast, more advanced build that uses parallelization and makes sure we skip
executing notebooks (which is the default behavior), run (if using uv):

.. code-block:: sh

   uv run --group docs sphinx-build -M html . _build -j auto
   uv run --group docs sphinx-build -M html . _build -j auto -v -T

Notes:

- `-j auto` enables parallel Sphinx workers to speed up the build on multi-core machines.
- The HTML output is written to `/docs/_build/html/`. Use `open _build/html/index.html` (macOS) or `python -m http.server 8000 -d _build/html` to preview locally.
- We also added -v for verbose output and -T traceback during the build.
- Env variable `Quantum_DOCS_BUILD_TUTORIALS=never` skips executing notebooks during the build (fast; uses stored outputs if present).

For convenience, the first command can be run using tox (from the root directory of the repository) as follows:

.. code-block:: sh

   tox -e docs



Live Preview with autobuild
---------------------------

To get fast, automatic rebuilding of the documentation while you edit it, use the `docs-autobuild` tox environment.

.. code-block:: sh

   tox -e docs-autobuild

This launches a local server (default: http://127.0.0.1:8000) and rebuilds the HTML pages incrementally whenever source files change.


.. warning::

   Avoid running the docs build **and** importing `Quantum_metal` at the same time from the same checkout. A legacy guard (`config.is_building_docs()` looks for a `.buildingdocs` file) can skip certain imports when that marker file is present. If you see unexpected import errors while developing and building docs, check for and remove `docs/.buildingdocs` before importing. Longer-term we’ll remove this guard, but for now be mindful of the interaction.


=================================
Local release vs. GitHub release
=================================

There are two supported release paths:

- **GitHub Actions (automated):** pushing a tag triggers the release workflow to build artifacts and upload to PyPI using the repository’s PyPI token.
- **Local publish (manual):** useful for testing or hotfixes when you need to ship from your workstation.

Local publish steps:

#. Bump the version in ``pyproject.toml`` (e.g., 0.5.1 → 0.5.2) using uv.

   .. code-block:: sh

      # Set the version directly
      uv version 0.5.2
      # Alternatively, bump the version with the --bump flag
      # The --bump flag can be used to bump the version to the next major, minor, or patch version
      uv version --bump patch


#. Commit (and optionally tag) using the version manually:

   .. code-block:: sh

      git commit -am "Bump version to 0.5.2"
      git tag v0.5.2
      git push origin main --tags

#. Build and publish with ``uv`` (requires a PyPI token, e.g., ``UV_PYPI_TOKEN``):

   .. code-block:: sh

      uv build
      uv publish --token $UV_PYPI_TOKEN

If you prefer the automated path, just push the tag and let GitHub Actions publish using the configured PyPI secret.


=================================
Tutorials
=================================

Jupyter notebook tutorials showing off features of Quantum Metal are located in the `_tutorials_`
folder. If you add a new feature, please add a demonstration of its use to a notebook or start a new notebook.
