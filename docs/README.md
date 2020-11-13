# Docs for Qiskit Metal

This folder contains the doc file src. We use sphinx to build the docs.

### Setup your environment to build the docs

1. Install sphinx and numpydoc
``` 
	 conda install sphinx numpydoc
	 (or pip install -U Sphinx)
```

2. Install read [the docs theme](https://github.com/rtfd/sphinx_rtd_theme) and set in the config `html_theme = "sphinx_rtd_theme"`
``` 
	pip install sphinx_rtd_theme
```

3. Install required packages
``` 
	pip install sphinx_automodapi
	pip install jupyter_sphinx
```

### How to build the docs

1. Make the docs.  In the `docs` directory 
```
	make html
```

Congratulations!  The docs can now be found in your `docs\build\html` directory.
