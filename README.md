[![Build Status](https://travis.ibm.com/IBM-Q-Restricted-Research/qiskit-metal.svg?token=p3Ak3Pz4fK3rsU99vhd2&branch=master)](https://travis.ibm.com/IBM-Q-Restricted-Research/qiskit-metal)

# Qiskit Metal [![](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](https://github.com/zlatko-minev/pyEPR) [![](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/zlatko-minev/pyEPR)
>  Quantum VLSI and Sims 

## Docs and how to use

(Under construction)

## Installation

To setup a development environment, first `git clone` this repository.
1. On your computer, clone the repository from [qiskit-metal/dev-0.2](https://github.ibm.com/IBM-Q-Restricted-Research/qiskit-metal/edit/v0.2-dev/). (If you don't have git installed, you can download and use [GitHub Desktop GUI](https://desktop.github.com/) and see these [notes](https://help.github.com/en/desktop/contributing-to-projects/cloning-a-repository-from-github-to-github-desktop).

Then Qiskit Metal can either be installed using a [conda environment](https://docs.conda.io/en/latest/miniconda.html) or a Python virtual environment, as described below. We recomend conda. 

*NOTE:* on Windows, the conda environment is strongly recommended because Shapely is difficult to install directly via pip.

### Conda environment setup (preffered)

To use a conda environment, assuming [you have conda installed](https://docs.conda.io/projects/conda/en/latest/user-guide/install/), we will install the qiskit_metal package locally. 

2. `Option 1: The simple way.` For convinience, you can try to install directly in your `base` environement, if it is relativly up to date. In the top-level of the repository:
```
python -m pip install -e .
```
The -e flag install qiskit_metal in [editable mode](https://pip.pypa.io/en/stable/reference/pip_install/#cmdoption-e).

2. `Option 2: THe fool-proof way.` It is possible that you can run into version issues in the above. Instead, to avoid this, you 
can rather create a new conda environemtn to avoid this issue. Execute these commands in the top-level of the repository:
```
conda env create -n <env_name> environment.yml
conda activate <env_name>
python -m pip install -e .
```
This will create a new environemnt with name `<env_name>`, which you can choose as `metal`. We will then activate it. Fianlly, in it, we will install the local package. If you follow this approach, each time you want to use the package, or launch a jupyter notebook, you MUST first run `conda activate <env_name>`. See what a [conda environment is](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)

### No conda: Virtual environment setup

2. To use a Python virtual environment, execute these commands in the top-level of the repository:

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

1. If using a virtual environment, make sure `pip` is up to date. In initial environment testing, PyQt5 was not installable with recent (but not the latest) versions of `pip`.

## Authors and Citation

Qiskit Metal is the work of [many people](https://github.com/Qiskit/qiskit-terra/graphs/contributors) who contribute to the project at different levels. Metal was concieved of and developed by Zlatko Minev at IBM, then co-led with Thomas McConkey. If you use Qiskit, please cite as per the included [BibTeX file](TODO).For icon attributions, see [here](\qiskit_metal\_gui\_imgs\icon_attributions.txt).


## License

[Apache License 2.0](LICENSE.txt)
