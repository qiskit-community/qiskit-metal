# Contributing to Qiskit Metal
Qiskit Metal follow the overall Qiskit project contributing guidelines. These are all included in the qiskit documentation:

https://qiskit.org/documentation/contributing_to_qiskit.html

In addition to the general guidelines there are specific details for contributing to metal, these are documented below.

## Issue reporting
When you encounter a problem please open an issue for it to the issue tracker.

## Improvement proposal
If you have an idea for a new feature please open an Enhancement issue in the issue tracker. Opening an issue starts a discussion with the team about your idea, how it fits in with the project, how it can be implemented, etc.

## Code Review
Code review is done in the open and open to anyone. While only maintainers have access to merge commits, providing feedback on pull requests is very valuable and helpful. It is also a good mechanism to learn about the code base. You can view a list of all open pull requests to review any open pull requests and provide feedback on it.

## Good first contributions
If you would like to contribute to the qiskit-metal project, but aren't sure of where to get started, the good first issue label highlights items for people new to the project to work on. These are all issues that have been reviewed by contributors and tagged as something a new contributor should be able to develop a fix for. In other words it shouldn't require intimate familiarity with qiskit-metal to develop a fix for the issue.

## Pull requests
We use GitHub pull requests to accept contributions.

While not required, opening a new issue about the bug you're fixing or the feature you're working on before you open a pull request is an important step in starting a discussion with the community about your work. The issue gives us a place to talk about the idea and how we can work together to implement it in the code. It also lets the community know what you're working on and if you need help, you can use the issue to go through it with other community and team members.

If you've written some code but need help finishing it, want to get initial feedback on it prior to finishing it, or want to share it and discuss prior to finishing the implementation you can open a Work in Progress pull request. When you create the pull request prefix the title with the [WIP] tag (for Work In Progress) and open it in `Draft` status. This will indicate to reviewers that the code in the PR isn't in it's final state and will change. It also means that we will not merge the commit until it is finished. You or a reviewer can remove the [WIP] tag and convert it to `Ready for review` when the code is ready to be fully reviewed for merging.

## Contributor License Agreement
Before you can submit any code we need all contributors to sign a contributor license agreement. By signing a contributor license agreement (CLA) you're basically just attesting to the fact that you are the author of the contribution and that you're freely contributing it under the terms of the Apache-2.0 license. You can find the forms and informations half-way down this page:

https://qiskit.org/documentation/contributing_to_qiskit.html

# Setting up your coding environemnt 

Notes on what environemnt we prefer to use. If using VS Code, see the VS code section. 

## VsCode setup 

VSCode settings, make sure to add PyQt5 to linter:
```
{
    "python.pythonPath": "D:\\ProgramData\\Anaconda3",
    "editor.fontSize": 15,
    "python.linting.pylintArgs": [
        "--extension-pkg-whitelist=PyQt5"
    ],
    "files.trimTrailingWhitespace": true,
    "files.trimFinalNewlines": true
}
```
See https://donjayamanne.github.io/pythonVSCodeDocs/docs/formatting/

## Immutable vs mutable 
<!--
https://medium.com/@meghamohan/mutable-and-immutable-side-of-python-c2145cf72747
-->



```
{
    "python.pythonPath": "D:\\ProgramData\\Anaconda3",
    "editor.fontSize": 16,
    "python.linting.pylintEnabled": true,
    "python.linting.pylintArgs": [
        "--extension-pkg-whitelist=PyQt5",
        "--disable=C0326",
        "--disable=W0125",
        "--disable=protected-access",
        "--disable=logging-fstring-interpolation",
        "--class-naming-style=snake_case",
        "--good-names=i,j,k,w,ex,Run,_,logger"
    ],
    "files.trimTrailingWhitespace": true,
    "files.trimFinalNewlines": true,
    "python.formatting.provider" : "autopep8",
    "python.formatting.autopep8Args": [
        "--max-line-length=99"
    ],
    "workbench.colorCustomizations": {
        "editorCursor.foreground": "#ff0000"
    }/*
    "python.linting.pep8Enabled": true,
    "python.formatting.autopep8Args": ["--max-line-length", "120"] */
}
```
