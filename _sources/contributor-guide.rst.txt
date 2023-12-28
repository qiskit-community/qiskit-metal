.. _contributor_guide:

********************************
Contributing to Qiskit Metal
********************************

Qiskit Metal is an open-source project committed to bringing quantum hardware design to
people of all backgrounds. This page describes how you can join the Qiskit Metal
community in this goal.


.. _where_things_are:

****************
Where Things Are
****************

The code for Qiskit Metal is located in the `Qiskit GitHub organization <https://github.com/Qiskit>`__, 
as part of the larger umbrella of Qiskit projects.

******************************************
Reporting Bugs and Requesting Enhancements
******************************************

When you encounter a problem, please open an issue in the
issue tracker: https://github.com/Qiskit/qiskit-metal/issues

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


*****************
Contributing Code
*****************



Style Guide
===========

To enforce a consistent code style in the project, we use customized `Pylint
<https://www.pylint.org>`__ for linting and `YAPF`<https://github.com/google/yapf>__ with the `Google style
<https://google.github.io/styleguide/pyguide.html>`__ for auto formatting. The custom 
`.pylintrc` and `.style.yapf` files is located in the root of the repository.
Our CI pipeline will enforce these styles when you make the pull request.

Contributor License Agreement
=============================

Before you can submit any code, all contributors must sign a
contributor license agreement (CLA). By signing a CLA, you're attesting
that you are the author of the contribution, and that you're freely
contributing it under the terms of the Apache-2.0 license.

When you contribute to the Qiskit project with a new pull request,
a bot will evaluate whether you have signed the CLA. If required, the
bot will comment on the pull request, including a link to accept the
agreement. The `individual CLA <https://qiskit.org/license/qiskit-cla.pdf>`__
document is available for review as a PDF.

.. note::
   If your contribution is part of your employment or your contribution
   is the property of your employer, then you will more than likely need to sign a
   `corporate CLA <https://qiskit.org/license/qiskit-corporate-cla.pdf>`__ too and
   email it to us at <qiskit@us.ibm.com>.



Pull Requests
=============

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
===========

Code review is done in the open and is open to anyone. While only maintainers have
access to merge commits, community feedback on pull requests is extremely valuable.
It is also a good mechanism to learn about the code base. You can
view a list of all open pull requests at https://github.com/Qiskit/qiskit-metal/pulls


Commit Messages
===============

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
=====================

If you make a change to an element, make sure you update the associated
*docstrings* and parts of the documentation under ``docs/apidocs`` in the
corresponding repo. To locally build the element-specific
documentation, run ``tox -edocs`` to compile and build the
documentation locally and save the output to ``docs/_build/html``.
Additionally, the Docs CI job on azure pipelines will run this and host a zip
file of the output that you can download and view locally.

If you have an issue with the `combined documentation <https://qiskit.org/documentation/>`__
that is maintained in the `Qiskit/qiskit repo <https://github.com/Qiskit/qiskit>`__,
you can open a `documentation issue <https://github.com/Qiskit/qiskit/issues/new/choose>`__
if you see doc bugs, have a new feature that needs to be documented, or think
that material could be added to the existing docs.



Good First Contributions
========================

If you would like to contribute to Qiskit Metal, but aren't sure
where to get started, the ``good first issue`` label on issues for a project
highlights items appropriate for people new to the project.
These are all issues that have been reviewed and tagged by contributors
as something a new contributor should be able to work on. In other
words, intimate familiarity with Qiskit Metal is not a requirement to develop a fix
for the issue.



Deprecation Policy
==================

Qiskit users need to know if a feature or an API they rely
upon will continue to be supported by the software tomorrow. Knowing under which conditions
the project can remove (or change in a backwards-incompatible manner) a feature or
API is important to the user. To manage expectations, the following policy is how API
and feature deprecation/removal is handled by Qiskit:

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
     warnings.warn('The qiskit.foo() function is deprecated as of 0.9.0, and '
                   'will be removed no earlier than 3 months after that '
                   'release date. You should use the qiskit.bar() function '
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
====================

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
reference to the change on master. When you create the branch for the
stable PR, use::

    $ git cherry-pick -x $master_commit_id

However, this only works for small self-contained patches from master.
If you need to backport a subset of a larger commit (from a squashed PR,
for example) from master, do this manually. In these cases, add::

    Backported from: #master pr number

so that we can track the source of the change subset, even if
a strict cherry-pick doesn\'t make sense.

If the patch you're proposing will not cherry-pick cleanly, you can help
by resolving the conflicts yourself and proposing the resulting patch.
Please keep Conflicts lines in the commit message to help review of the
stable patch.



Backport labels
---------------

Bugs or PRs tagged with ``stable backport potential`` are bugs
that apply to the stable release too and may be suitable for
backporting once a fix lands in master. Once the backport has been
proposed, the tag should be removed.

Include ``[Stable]`` in the title of the PR against the stable branch,
as a sign that setting the target branch as stable was not
a mistake. Also, reference to the PR number in master that you are
porting.



Custom Names and Images for QComponents
====================

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
the qiskit metal application that the image for the qcomponent is named
``myqcomponent.png`` and is located in::

   qiskit-metal/qiskit_metal/_gui/_imgs/components/myqcomponent.png

and that they want the display name of this file to be ``MyQComponent``.



*****************************
Contributing to Documentation
*****************************

Qiskit documentation is shaped by the `docs as code
<https://www.writethedocs.org/guide/docs-as-code/>`__ philosophy, primarily
drawn from Qiskit code comments in the `style of API documentation
<https://alistapart.com/article/the-ten-essentials-for-good-api-documentation/>`__.

The documentation is built from the master branch of `Qiskit/qiskit/docs
<https://github.com/Qiskit/qiskit/tree/master/docs>`__ using `Sphinx
<http://www.sphinx-doc.org/en/master/>`__. The majority of documentation, under
`API Reference <https://qiskit.org/documentation/apidoc/qiskit.html>`__, is
drawn from code comments in the repositories listed in :ref:`where_things_are`.



Documentation Structure
=======================

The way documentation is structured in Qiskit Metal is to push as much of the actual
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

   .. image:: images/contributer-example-1.jpg

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
   directly if the module is simple, such as in the case of ``qiskit.execute``). The
   autosummary directive is used to autodoc a list of different Python elements
   (classes, functions, etc.) directly without having to manually call out the
   autodoc directives for each one. The module-level docstring is where to
   provide a high-level overview of what functionality the module provides.
   This is normally done by grouping the different
   components of the public API together into multiple subsections.

   For example, as in the previous dagcircuit module example, the
   contents of the module docstring for ``qiskit/analyses/__init__.py`` would
   be

   .. image:: images/contributer-example-2.jpg

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
HTML files by navigating to `/docs/` and running the following in a terminal
window:

.. code-block:: sh

   make html

This will build a styled, HTML version of your local documentation repository
in the subdirectory `/docs/_build/html/`.



Tutorials
---------

Jupyter notebook tutorials showing off features of Qiskit Metal are located in the `_tutorials_`
folder. If you add a new feature, please add a demonstration of its use to a notebook or start a new notebook.


Documentation Integration
-------------------------

The hosted documentation at https://qiskit.org/documentation/ covers the entire
Qiskit project; Metal is just one component of that. As such, the documentation
builds for the hosted version are built by the Qiskit meta-package repository
https://github.com/Qiskit/qiskit. When commits are merged to that repo, the
output of Sphinx builds are uploaded to the qiskit.org website. Those Sphinx
builds are configured to pull in the documentation from the version of the
Qiskit elements installed by the meta-package at that point. For example, if
the meta-package version is currently 0.13.0, then that will copy the
documentation from Metal's 0.10.0 release. When the meta-package's requirements
are bumped, then it will start pulling documentation from the new version. This
means that fixes for incorrect API documentation will need to be
included in a new release. Documentation fixes are valid backports for a stable
patch release per the stable branch policy (see that section below).

During the build process, the contents of each element's ``docs/apidocs/``
are recursively copied into a shared copy of ``doc/apidocs/`` in the meta-package
repository along with all the other elements. This means that what is in the root of
docs/apidocs on each element at a release will end up on the root of
https://qiskit.org/documentation/apidoc/.



Translating Documentation
=========================

Qiskit documentation is translated (localized) using Crowdin, a software and web
localization platform that allows organizations to coordinate translation
projects and collaborate with communities to translate materials. Crowdin allows
our community of translators to amplify their impact by automatically reusing
the work invested translating one sentence to translate other, similar
sentences. Crowdin also makes translations resilient to many types of changes to
the original material, such as moving sentences around, even across files.

Qiskit localization requests are handled in `Qiskit Translations <https://github.com/Qiskit/qiskit-translations>`__
repository. To contribute to Qiskit localization, please follow these steps:

#. Add your name (or ID) to the `LOCALIZATION_CONTRIBUTORS
   <https://github.com/qiskit-community/qiskit-translations/blob/master/LOCALIZATION_CONTRIBUTORS>`__
   file.
#. Create a pull request (PR) to merge your change. Make sure to follow the template
   to open a Pull Request.

   .. note::

      - Each contributor has to create their own PR and sign the CLA.
      - Please mention the language that you'd like to contribute to in the PR
        summary.
      - If you have an open issue for a language request, **add the issue link
        to the PR**.
#. You will be asked to sign the Qiskit Contributors License Agreement (CLA);
   please do so.
#. A minimum of **three contributors** per language are necessary for any new
   languages to be added, to receive official support from the administrators of
   the localization project.
#. Among the group of contributors, a translation lead must be identified to serve
   as a liaison with the administrators of the localization project.
   The lead must contact: Yuri Kobayashi (yurik@jp.ibm.com) by email.
#. In the `Qiskit-Docs <https://crowdin.com/project/qiskit-docs>`__
   Crowdin project, choose the language that you want to contribute to.

   .. note::

      As mentioned in the blog post, `Qiskit in my language is Qiskit <https://medium.com/qiskit/qiskit-in-my-language-is-qiskit-73d4626a99d3>`__,
      we want to make sure that translated languages have enough community support
      to build a translation team with translators, proofreaders, and translation leads.
      If you want to be a translation lead or would be willing to join a new
      translation project team, you can open a `GitHub issue <https://github.com/qiskit-community/qiskit-translations/issues/new/choose>`__
      to start a discussion with the Qiskit team and recruit translation project members.
#. Click the **Join** button and **paste the URL of your PR** in the dialog box where you
   are asked why you want to join the Crowdin project.

The administrators of the Crowdin project will review your request and give you
access as quickly as they can.

