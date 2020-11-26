# Qiskit Metal [![](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](https://github.com/Qiskit/qiskit-metal) [![](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/Qiskit/qiskit-metal)
>  Quantum hardware design and analysis

### Early access for quantum device design project now open
https://qiskit.org/metal/

Unpolished, early-access alpha version for a first-of-its-kind, open-source project for engineers and scientists to design superconducting quantum devices with ease.

#### Early Access
Through this early-access program, we are thrilled to ask you to join this journey to revolutionize quantum devices.

The early-access program will start in November and proceed through March, 2021, during which time we will work closely to develop Metal and design quantum devices with it.
<br><br>

#### Get help: Slack
Use the [Slack channel (Join here!)](https://join.slack.com/share/zt-jjgzilxu-1u2FGivroQi64fHajpTWiw) to communicate with the developers and other early-access participats. (Troubleshooting: If the Slack invitation has expired, request one by opening a GitHub issue.)


## Installation

To setup a development environment, first `git clone` this repository.

* On your computer, clone the repository from qiskit-metal/main:
`git clone https://github.com/Qiskit/qiskit-metal`

* Note: If you don't have git installed, you can download and use [GitHub Desktop GUI](https://desktop.github.com/) and see these [notes](https://help.github.com/en/desktop/contributing-to-projects/cloning-a-repository-from-github-to-github-desktop).

Then Qiskit Metal can either be installed using a [conda environment](https://docs.conda.io/en/latest/miniconda.html) or a Python virtual environment, as described below. We recommend conda.

Notes:

* For your own sanity, it is recommended to read this document in its entirety before proceeding.
* On Windows, the conda environment is strongly recommended because Shapely is difficult to install directly via pip.

### Conda environment setup (preferred setup)

To use a conda environment, assuming [you have conda installed](https://docs.conda.io/projects/conda/en/latest/user-guide/install/), we will install the qiskit_metal package locally.

##### Option 1: A new environment

The most reliable way to set up a qiskit_metal environment is to build one from scratch using the provided conda environment specification file `environment.yml`.
To do so, execute these commands in the top-level of the repository:

```
conda env create -n <env_name> environment.yml
conda activate <env_name>
python -m pip install -ve .
```

This will first create a new environment with name `<env_name>`, which you can choose to name `metal` for example.
Then we activate the new environment.
Finally, we install the local package inside that environment.

The `-e` flag install qiskit\_metal in [editable mode](https://pip.pypa.io/en/stable/reference/pip_install/#cmdoption-e).
The `-v` flag is for verbose.

##### Option 2: Install into an existing environment

For convenience, you can try to install directly in an existing environment such as the `base` environment, if it is relatively up to date.
To install qiskit_metal and its depenencies into an existing environment named `<env_name>`, execute these commands in the top-level of the repository:

```
conda env update -n <env_name> environment.yml
conda activate <env_name>
python -m pip install -ve .
```

##### Notes on using conda

It is possible that you may run into version issues in the above if previously installed packages conflict with the requirements of qiskit_metal.

**Important**: Every time you intend to develop code using this environment, you MUST first run the command: `conda activate <env_name>`.  See what a [conda environment is](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)

To use the new environment inside jupyter lab you will need to follow these additional steps right after the above:

```
conda install ipykernel
ipython kernel install --user --name=<any_name_for_kernel>
```

This will create a kernel based on the environment that is "active" at the moment and you will be able to select that kernel inside jupyter lab.

### Without conda: Virtual environment setup (alternative setup)

**On Windows, do this first:** It is recommended that you first install `Visual C++ 14.0`, it is required for a successful install of `gdspy`.
If you do not have `Visual C++ 14.0` installed you will be notified to install it when `gdspy` attempts to install.
You can do this by downloading and installing [C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
Be sure to select the latest versions of `MSVCv142 - VS 2019 C++ x64/x86 build tools` and `Windows 10 SDK` in the installer as suggested in [this wiki](https://wiki.python.org/moin/WindowsCompilers) referenced by the gdspy documentation.

To use a Python virtual environment, execute these commands in the top-level of the repository:

```
python -m venv <virtual_env_path>
source <virtual_env_path>/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt -r requirements-dev.txt -e .
```

where `<virtual_env_path>` is where you want the Python virtual environment to be installed.
On Windows, replace `source <virtual_env_path>/bin/activate` with `.\<virtual_env_path>\Scripts\activate`.


### Installation hints

Here are some things to consider when setting up a development environment:

* If using a virtual environment, make sure `pip` is up to date. In initial environment testing, PySide2 is installable with only the latest version of `pip`.

* Add the path of your qiskit-metal folder to your PATH


### Additional steps for developers
If you are planning to develop the qiskmit metal codebase, you'll want to use these instructions to [setup user environment](/docs/NEW_DEVELOPER_SETUP.md)


### Common Issues

#### pyqode/pyside
Please be aware that the environment.xml and requirements.txt each use a different pyside version. This is done to prevent kernel crashes formerly caused by pyqode. For non-Windows users, this setup causes an older version of pyqode.qt to be overwritten with a later forked version. On Windows, the background installation process is more complicated. Because of this, Windows users may experience GUI or other issues. If such issues occur, try rerunning `python setup.py install` or create a new, pristine conda environment as per above instructions.

#### Jupyter Lab
If you can not start Jupyter Lab in the new enviroment.

Based on: https://anaconda.org/conda-forge/jupyterlab
Install Jupyter lab by
```
conda install -c conda-forge jupyterlab
```
Then change directory to top level of repository.
```
python -m pip install -e .
```

#### qutip
`qutip` may have issues finding your path if using VSCode, resulting in a `KeyError: 'physicalcpu'`. If the error occurs, please add your PATH to VSCode's settings as follows.


 ##### Windows:
 Open you Windows Command Prompt and type in
 ```
 $Env:Path
 ```
Copy the resulting output. Example: `"PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"`
Then open the applicable settings.json in your VS Code. (See how to open command palette [here](https://code.visualstudio.com/docs/getstarted/tips-and-tricks). Search "settings" and click Open Workspace Settings (JSON)). Paste:
```
 "terminal.integrated.env.windows": {
        "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        }
```

##### MacOs:
 Open you Windows Command Prompt and type in
 ```
echo $PATH
 ```
Copy the resulting output. Example: `"PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"`
Then open the applicable settings.json in your VS Code. (See how to open command palette [here](https://code.visualstudio.com/docs/getstarted/tips-and-tricks). Search "settings" and click Open Workspace Settings (JSON)). Paste:
```
    "terminal.integrated.env.osx": {
        "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        }
```

## Docs and how to use

[Conda User Guide](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)

[Python Setup and Usage](https://docs.python.org/3/using/)

[Python Language Reference](https://docs.python.org/3/reference/index.html)

[Python How-To's](https://docs.python.org/3/howto/index.html)

[Python Tutorials](https://docs.python.org/3/tutorial/index.html)

[Python Style Guide](https://www.python.org/dev/peps/pep-0008/)

[Metal Docs](/docs)

[Docstring cheat sheet](/docs/docstring_cheat_sheet.md)


## Authors and Citation

Qiskit Metal is the work of [many people](https://github.com/Qiskit/qiskit-metal/pulse/monthly) who contribute to the project at different levels. Metal was conceived and developed by Zlatko Minev at IBM, then co-led with Thomas McConkey. If you use Qiskit, please cite as per the included [BibTeX file](https://github.com/Qiskit/qiskit/blob/master/Qiskit.bib).For icon attributions, see [here](/qiskit_metal/_gui/_imgs/icon_attributions.txt).


## License

[Apache License 2.0](LICENSE.txt)
