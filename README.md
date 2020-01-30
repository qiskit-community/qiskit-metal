# Qiskit Metal [![](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](https://github.com/zlatko-minev/pyEPR) [![](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/zlatko-minev/pyEPR)
>  Quantum VLSI and Sims 

## Docs and how to use

(Under construction)

## Installation

To setup a development environment, first `git clone` this repository.

### Virtual environment setup

To use a Python virtual environment, execute these commands in the top-level of the repository:

```
python -m venv <virtual_env_path>
source <virtual_env_path>/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt -r requirements-dev.txt -e .
```

where `<virtual_env_path>` is where you want the Python virtual environment to be installed.
On Windows, replace `source <virtual_env_path>/bin/activate` with `.\<virtual_env_path>\Scripts\activate`.

### Conda environment setup

To use a conda environment, execute these commands in the top-level of the repository:

```
conda env create -n <env_name> environment.yml
conda activate <env_name>
python -m pip install -e .
```

### Installation hints

Here are some things to consider when setting up a development environment:

1. If using a virtual environment, make sure `pip` is up to date. In initial environment testing, PyQt5 was not installable with recent (but not the latest) versions of `pip`.
2. Shapely is difficult to install on Windows outside of conda. Currently, a different source than PyPI is used to specify for the location to obtain Shapely from on Windows because the wheels on PyPI did not work out of the box when tested.

## Authors and Citation

Qiskit Metal is the work of [many people](https://github.com/Qiskit/qiskit-terra/graphs/contributors) who contribute to the project at different levels. Metal was concieved of and developed by Zlatko Minev at IBM, then co-led with Thomas McConkey. If you use Qiskit, please cite as per the included [BibTeX file](TODO).For icon attributions, see [here](\qiskit_metal\_gui\_imgs\icon_attributions.txt).


## License

[Apache License 2.0](LICENSE.txt)
