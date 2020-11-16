# Contributing to Qiskit Metal
Qiskit Metal follows the overall Qiskit project contributing guidelines. These are all included in the [Qiskit Documentation](https://qiskit.org/documentation/contributing_to_qiskit.html).

Please read those general guidelines first, then the specific details for contributing to Metal below.

## Adding a New Issue

### Reporting a Bug

When you encounter a problem while using Metal, please open an issue in the
[Issue Tracker](https://github.com/Qiskit/qiskit-metal/issues).

When reporting an issue, please follow this template::

```
<!--- Provide a general summary of the issue in the Title above -->

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
If you have an idea for a new feature, please open an Enhancement issue in the issue tracker. Describe your idea, what the benefits are, and your implementation proposal, if you have one. Opening an issue starts a discussion with the team about your idea, how it fits in with the project, how it can be implemented, etc.

## Building Metal from Source

We highly recommend using a local Python environment rather than
installing Qiskit Metal natively. Metal can either be installed using a
[conda environment](<https://docs.conda.io/en/latest/miniconda.html>)
or a Python virtual environment, as described below. We recommend conda.

1.  Clone the Qiskit Metal repository.

``` sh
git clone https://github.com/Qiskit/qiskit-metal.git
```

2.  Cloning the repository creates a local folder called `qiskit-metal`.

``` sh
cd qiskit-metal
```

3.  Set up your local environment and instal.

The most reliable way to set up a Metal environment is to build
one from scratch using the provided conda environment specification file
`environment.yml`. To do so, execute these
commands in the top-level of the repository:

``` sh
conda env create -n <env_name> environment.yml
conda activate <env_name>
python -m pip install -e .
```

For convenience, you can also try to install directly in an existing
environment such as the `base` environment,
if it is relatively up to date. To install Metal and its dependencies into an
existing environment named `env_name` execute these commands in
the top-level of the repository:

``` sh
conda env update -n <env_name> environment.yml
conda activate <env_name>
python -m pip install -e .
```

### Notes on Using Conda

It is possible that you may run into version issues in the above if
previously installed packages conflict with the requirements of Metal.

**Important**: Every time you intend to develop code using this
environment, you MUST first run the command: `conda activate env_name`. More info on the [conda environment](<https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>).

To use the new environment inside jupyter lab you will need to follow
these additional steps right after the above:

``` sh
conda install ipykernel
ipython kernel install --user --name=<any_name_for_kernel>
```

To use a Python virtual environment instead, execute these commands in
the top-level of the repository:

``` sh
python -m venv <virtual_env_path>
source <virtual_env_path>/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt -r requirements-dev.txt -e .
```

## Contributing Code

### Code Formatting
To enforce a consistent code style in the project, we use customized [Pylint](https://www.pylint.org) for linting and 
[YAPF](https://github.com/google/yapf) with the [Google style](
https://google.github.io/styleguide/pyguide.html) for auto formatting. The custom 
`.pylintrc` and `.style.yapf` files are located in the root of the repository. Our CI pipeline will enforce these styles when you make the pull request.

#### VSCode Setup

If you are using VSCode for your code editor, you can add these settings 
to your `settings.json` to enforce your code to our style. Make sure to add PySide2 to the linter:
```
{
    "python.linting.pylintEnabled": true,
    "python.linting.enabled": true,    
    "python.linting.pylintArgs": [
        "--extension-pkg-whitelist=PySide2"
    ],
    "python.formatting.provider": "yapf",
    "editor.formatOnSave": true,
    "files.trimTrailingWhitespace": true,
    "files.trimFinalNewlines": true
}
```

### Code Review
Code review is done in the open and open to anyone. While only maintainers have access to merge commits, providing feedback on pull requests is very valuable and helpful. It is also a good mechanism to learn about the code base. You can view a list of all open pull requests to review any open pull requests and provide feedback on it.

### Good First Contributions
If you would like to contribute to Qiskit Metal, but aren't sure of where to get started, the `good first issue` label highlights items for people new to the project to work on. These are all issues that have been reviewed by contributors and tagged as something a new contributor should be able to develop a fix for.

### Testing

Once you've made a code change, it is important to verify that your change does not break any existing tests and that any new tests that you've added also run successfully. Before you open a new pull request for your change, you'll want to run the test suite locally.

The easiest way to do this is to execute the `run_all_tests.py` script in the `tests` directory.  It executes all test files in that directory.  You'll recieve a message informing you if the tests were successful or not.  Alternatively you may run an individual suite of tests by executing invidual `test_XYZ.py` files individually.  All test files utilize the `unittest` module - no further setup is needed.

Additionally, CI will run the test suite on all pushes made to any branch in the repository.

### Pull Requests

To submit your contribution, make a pull request from your forked repository to the `master` branch of Metal. Please ensure 

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
@date: 2019
@author: Zlatko Minev (IBM)
Submodules
----------
.. autosummary::
    :toctree:
    cpw_calculations
    lumped_capacitive
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
    >  makes sense. For example, one common extension used is the ``jupyter-execute``
    >  directive, which is used to execute a code block in Jupyter and display both
    >  the code and output. This is particularly useful for visualizations.

### Rebuilding Documentation

If you make changes to the codebase and want to rebuild the documentation, 

1. Install `sphinx` and `numpydoc`.
``` 
conda install sphinx numpydoc
(or pip install -U sphinx)
```

2. Install [read the docs theme](https://github.com/rtfd/sphinx_rtd_theme) and set in the config `html_theme = "sphinx_rtd_theme"`.
``` 
pip install sphinx_rtd_theme
```

3. Install required packages.
``` 
pip install sphinx_automodapi
pip install jupyter_sphinx
```

4. Make the docs.  In the `docs` directory,
```
make html
```

You can also use this to update the doc tree.

