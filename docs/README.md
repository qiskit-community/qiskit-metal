# Docs for Qiskit Metal

This folder contains the src and resulting doc files. We use sphinx. 

### The easy way

Notes for users.

1. In your local copy of the repository, navigate to /docs/build/html and open index.html in your browser

That's it.

### The hard way - build the docs yourself

Notes for developers only.

**Generally, there is no need to build these docs.  Use the prebuilt docs**

Many files are changed when the docs are built, therefore a semi-regular update the docs is done by the docs owner @jdrysda.  If you feel the docs need to be updated immediately, please reach out to @jdrysda for assistance.

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

4. Make the docs.  In the `docs` directory 
```
	make html
```

You can also use this to update the doc tree.

