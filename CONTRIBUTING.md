# Contributing to Quantum Metal

Quantum Metal (formerly Qiskit Metal) is community-maintained — see [ROADMAP.md](./ROADMAP.md) for the direction. Contributions follow the guidelines below, with the original Qiskit-project guidelines as background reading: [Qiskit Documentation](https://github.com/Qiskit/qiskit/blob/main/CONTRIBUTING.md).

Please read those general guidelines first, then the specific details for contributing to Metal below.

## CLA - Contributor License Agreement
Contributors sign a CLA before their first contribution is merged. It's a one-time action and applies to all future contributions.

Sign here: https://cla-assistant.io/qiskit-community/qiskit-metal

Once you open a pull request, the CLA bot will leave a comment with a link to sign if you haven't already. The PR's required `license/cla` check turns green once signed.

## Adding a New Issue
### Reporting a Bug
When you encounter a problem while using Metal, please open an issue in the
[Issue Tracker](https://github.com/qiskit-community/qiskit-metal/issues).

When reporting an issue, please follow this template::

```
<!--- Provide a general summary of the issue in the Title -->
### Informations
- **Qiskit Metal version**:
- **Python version**:
- **Operating system**:
### What is the current behavior?
### Steps to reproduce the problem
### What is the expected behavior?
### Suggested solutions
```

### Improvement Proposal
If you have an idea for a new feature, please open an Enhancement issue in the issue tracker.
Describe your idea, its benefits, and your implementation proposal, if you have one.
Opening an issue initiates a discussion with the team about your idea, how it fits in with the project, how it can be implemented, etc.

## Contributing Code
### Code Formatting
We use [Ruff](https://docs.astral.sh/ruff/) for both linting and auto formatting. Configuration lives under `[tool.ruff.lint]` in the root `pyproject.toml`; there are no separate `.pylintrc` or `.style.yapf` files. Our CI pipeline runs `tox -e lint` on every pull request — please run it locally before pushing.

Common commands:
- `tox -e lint` — lint the `qiskit_metal/` source tree
- `tox -e format` — auto-format the `qiskit_metal/` source tree
- `uvx ruff check src` — lint without tox (faster, same result)
- `uvx ruff format src` — format without tox

#### VSCode Setup

Steps:
1. Install the [Ruff extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) (publisher `charliermarsh`).
2. Add the following workspace setting in the workspace `settings.json` so format-on-save and lint-on-save both go through Ruff:

```json
{
    "editor.formatOnSave": true,
    "files.trimTrailingWhitespace": true,
    "files.trimFinalNewlines": true,
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.codeActionsOnSave": {
            "source.organizeImports.ruff": "explicit"
        }
    }
}
```

(If you previously had `python.linting.pylintEnabled` or `python.formatting.provider = yapf` in your settings, remove them — they are no longer used by this project.)

### Code Review
Code review is done in the open and open to anyone. While only maintainers have access to merge commits, providing feedback on pull requests is very valuable and helpful. It is also a good mechanism to learn about the code base. You can view a list of all open pull requests to review any open pull requests and provide feedback on it.

### Good First Contributions
If you would like to contribute to Qiskit Metal, but aren't sure of where to get started, the `good first issue` label highlights items for people new to the project to work on. These are all issues that have been reviewed by contributors and tagged as something a new contributor should be able to develop a fix for.

### Testing

Once you've made a code change, it is important to verify that your change does not break any existing tests and that any new tests that you've added also run successfully. Before you open a new pull request for your change, you'll want to run the test suite locally.

The easiest way to do this is `tox` (which builds an isolated environment and runs the full suite the same way CI does):

- `tox` — run the test suite on every supported Python (3.10, 3.11, 3.12)
- `tox -e py3.12` — run on a specific Python only
- `pytest tests/` — run tests in your current environment (faster iteration; use this once you've confirmed the env is set up)
- `pytest tests/test_<file>.py` — run a single test file

CI also runs the suite on every push to any branch in the repository.

### Pull Requests

To submit your contribution, make a pull request from your forked repository to the `main` branch of Metal. Please ensure

-  The code follows the code style of the project (discussed above) and
   successfully passes all tests.
-  The documentation has been updated accordingly. In particular, if a
   function or class has been modified during the PR, please update the
   *docstring* accordingly. If you have added or modified a feature, please update a corresponding tutorial in the `tutorials` folder as well to show its usage. See below for documentation structure and instructions.
- If your code does not pass the automated CI tests, please fix the problems. Your pull request cannot be merged until the tests are passed and you have obtained approval from reviewers.

## Documentation Structure

The Metal documentation is located at `docs/build/html`. The way documentation is structured in Qiskit Metal is to push as much of the actual
documentation into the docstrings as possible. This makes it easier for
additions and corrections to be made during development, because the majority
of the documentation lives near the code being changed. There are three levels in the normal documentation structure in Metal:

#### The `.rst` Files in the `docs/apidocs`

These files are used to tell Sphinx which modules to include in the rendered
documentation. This contains two pieces of information:
an `internal reference <http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#reference-names>`__
or `cross reference <https://www.sphinx-doc.org/en/latest/usage/restructuredtext/roles.html#ref-role>`__
to the module, which can be used for internal links
inside the documentation, and an `automodule directive <http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`__
used to parse the
module docstrings from a specified import path. For example, the analyses.rst
file contains:

```
.. automodule:: qiskit_metal.analyses
    :no-members:
    :no-inherited-members:
    :no-special-members:
```

   If you're adding a new ``.rst`` file for a new module's documentation, make
   sure to add it to the [toctree](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#table-of-contents).
   in that file.

#### The Module-Level Docstring
   This docstring is at the module
   level for the module specified in the ``automodule`` directive in the rst file.
   If the module specified is a directory/namespace, the docstring should be
   specified in the ``__init__.py`` file for that directory. This module-level
   docstring contains more details about the module being documented.
   The normal structure to this docstring is to outline all the classes and
   functions of the public API that are contained in that module. This is typically
   done using the `autosummary directive <https://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html>`__
   (or `autodoc directives <http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`__
   directly if the module is simple, such as in the case of ``qiskit.execute``). The
   autosummary directive is used to autodoc a list of different Python elements
   (classes, functions, etc.) directly without having to manually call out the
   autodoc directives for each one. The module-level docstring is where to
   provide a high-level overview of what functionality the module provides.
   This is normally done by grouping the different
   components of the public API together into multiple subsections.

   For example, as in the previous dagcircuit module example, the
   contents of the module docstring for ``qiskit/analyses/__init__.py`` would
   be:

```
"""
=================================================
Analyses (:mod:`qiskit_metal.analyses`)
=================================================
.. currentmodule:: qiskit_metal.analyses
Module containing all Qiskit Metal analyses.

Submodules
----------
.. autosummary::
    :toctree:
    em
    quantization
    hamiltonian
"""
```

The actual docstring for the elements listed in the module docstring
   You should strive to document thoroughly all the public interfaces
   exposed using examples when necessary. For docstrings, [Google Python Style
   Docstrings](https://google.github.io/styleguide/pyguide.html?showone=Comments#38-comments-and-docstrings>)
   are used. This is parsed using the [napoleon
   sphinx extension](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html).
   The [napoleon documentation](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
   contains a good example of how docstrings should be formatted.


    >  You can use any Sphinx directive or rst formatting in a docstring as it
    >  makes sense.

### Rebuilding Documentation

If you make changes to the codebase and want to rebuild the documentation: `tox -e docs`.

Sometimes Sphinx can have bad cache state. Run `tox -e docs-clean` to reset Tox.

## Check-list for specific types of Pull Requests
Please refer to [these instructions](https://github.com/qiskit-community/qiskit-metal/blob/main/contributor_guidelines/pull_request_rules.md)
