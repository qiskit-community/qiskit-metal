# Qiskit Metal
### Quantum VLSI and Sims

[![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](https://github.com/zlatko-minev/pyEPR)
[![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/zlatko-minev/pyEPR)

# Docs and how to use 

Todo. 

# Installation notes

For development, the best way is to fork the repository. Then install the following required packages. Certain packages are only required if you require a particulat plugin. For example, if one does not require to export to gds, one does not need to install pygds.  

#### Core packages 
```
conda install shapely
```

Install pyEPR(https://github.com/zlatko-minev/pyEPR)

#### Plugin: Export yo GDS for mask design 
To use the GDS export plugin, please install `gdspy`. This will require you to first install Microsoft Visual C++ Build Tools, as a C++ compiler for speed is needed. This can be done with 
```
pip install gdspy
```
If you do not already have the compiler, and get `error: Microsoft Visual C++ 14.0 is required. Get it with "Microsoft Visual C++ Build Tools": https://visualstudio.microsoft.com/downloads/`, please download the build tools from the site. You can find it under `Tools for Visual Studio` entitled `Build Tools for Visual Studio 20xx`. Note, you do not need to intsll the Windows SDK. 


Additional packages 
**Energy Participation Ratio**
  * Fully automated, eigen-analysis to calculate both the Hamiltonian and dissipative parameters of a distributed circuit, based on the fraction of energy stored in the non-linear/dissipative element in a given mode of the circuit



# Coding notes 


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