# New Qiskit Metal Developer Onboarding
Follow the instructions in the sections below to setup your local development environment.

## Setup Visual Studio 2019 Code
1. On your development machine download [Visual Studio Code](https://code.visualstudio.com/docs/).
2. Install extensions: `File -> Preferences -> Extensions`

      a. Python Docstring Generator
  
      b. Install .VSIX
  
      c. Markdown Preview Enhanced
  
      d. PYQT Integration
  
      e. Python
  
      f. Qt for Python
  
      g. SFTP
  
      h. YAML
  
      i. GitLens

3. Open a file with simple python code: `helloworld.py` example below:
```
msg = "hello world"
print(msg)
```

Notes:

* When you open `Visual Studio Code`, select this folder or file within the folder.  You will be prompted to install python extensions, agree. 
* Agree to install linting.  
* You'll be asked if you agree to telemetry data being sent to Microsoft.  We recommend not doing this.
* Look at the bottom of Visual Studio Code screen, the version of python will be listed.  Select `env` to be `‘base’:conda`.  Substitute `base` for the name of your conda environment.

## Setup Visual Studio 2019 Code git access
From your development machine

1. Install two extensions.  From the top ribbon, choose `Extensions -> Manage Extensions` and install:

      a. GitHub Extension for Visual Studio

      b. Microsoft Visual Studio Installer Projects

## Install git command line tool (optional)
If you want to use git though the windows command line, install git-scm (or your favorite command line tool) to your local account.  You can download it here: `https://git-scm.com/download/win`

## Setup pylint and yapf
1. Install pylint and yapf: `pip install pylint yapf`
2. To run automatically in vscode every time you save, put these settings in `settings.json` file:
```
"python.linting.pylintEnabled": true,
"python.linting.enabled": true,
"editor.formatOnSave": true,
"python.formatting.provider": "yapf",
```
For help finding your `settings.json` file click [here](https://www.google.com/search?q=vscode+where+is+settings.json).

Since the style file is already in the metal directory, yapf should automatically format to those rules when you save.

To run manually on a file, execute `yapf -i <file>`.  To run recursively in a directory, execute `yapf -ir <directory>`.  Note that you shouldn't have to do this if your IDE is set up correctly.

## VS Code Tweaks & Issues
Take a look at this [summary of a great setup](https://donjayamanne.github.io/pythonVSCodeDocs/docs/python-path/). 

## Auto Formatting
Formatting the source code as and when you save the contents of the file is supported.
You can add these settings
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

Make sure that you have installed

``` 
pip install pep8   
pip install --upgrade autopep8
```
 
## Enable/Disable Linting
By default linting is enabled and uses pylint. `"python.linting.enabled": true`

If [Intellisense/Autocompletion is not working for custom modules](https://donjayamanne.github.io/pythonVSCodeDocs/docs/troubleshooting_intellisense/), then [configure the settings.json to include this custom location for autocompletion to work](https://donjayamanne.github.io/pythonVSCodeDocs/docs/autocomplete/)

You can hide unwanted files from file tree by going to the `user` section and adding these filers:

* `**/.git`
* `**/.svn`
* `**/.hg`
* `**/CVS`
* `**/.DS_Store`
* `__pycache__`

## Git Extension
Another few extensions you may find useful to install from the vs marketplace are

* gitFlow - for those of you that like the git graph functionality
* gittLab
  * When you click a line in the source code, tells you who wrote it.
  * Has powerful git diff viewer for different branches


## Developer: Docs and how to use

[Conda User Guide](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)

[Python Setup and Usage](https://docs.python.org/3/using/)

[Python Language Reference](https://docs.python.org/3/reference/index.html)

[Python How-To's](https://docs.python.org/3/howto/index.html)

[Python Tutorials](https://docs.python.org/3/tutorial/index.html)

[Python Style Guide](https://www.python.org/dev/peps/pep-0008/)

[Metal Docs](/)

[Docstring cheat sheet](/docs/docstring_cheat_sheet.md)
