# Pull Request content guidelines

## New components or updating existing components

You have worked hard and updated a component code or created your custom component (a class that directly or indirectly inherits the `QComponent` class and implements the `make()` method). Now you would like to showcase your work in Qiskit Metal, for everyone to see and use. So what do you need to do?

The first step is to put your code in a github branch or fork, and then create a Pull Request, to propose the new code to be added to the main repository. But is your code complete to pass the pull-request approval process? And is the code all you need to properly showcase your work?

### Checklist for a complete pull request (explained more in details in the sections below):
* Your component class conforms to the structure of the others (compare to others).
* Your code is documented for developers and for user-guide.
* You have attached a tutorial notebook to explain how to use it.
* Create unit-test. NOTE: The qiskit-metal team can help taking care of this action for you, after the pull-request is created.
* (not required in most cases) add the hooks and notebooks to include the component in the list of examples accessible from the online documentation.

#### Minimum requirements to create an draft pull request:
1. Use `default_options` to parameterize your component. Add valid default strings, numerals and/or units to each of the keys. The best components are the most configurable.
2. Add `component_metadata`. This is necessary for qiskit-metal to be aware of which type of shapes are being created by your component.
3. Add doc_strings. Every method and every class need a description that will be shown in the online documentation.
    - The method description must also include details of the method signature and returns
    - The class description should include a details of the `default_options` keys you defined. it should also include an image
4. Make the doc_strings visible to the online documentation by adding the component to the TOC (table of content)
    1. Open the file `qiskit_metal/qlibrary/__init__.py`
    1. Add the QComponent class name to the most appropriate toc-tree section
    1. Then locate the code line `if config.is_building_docs():` and inside(under) it add an import statement to your new QComponent class.
5. Add a sample tutorial notebook
    - Even if you do not want this to appear in the official documentation, the tutorial notebook will be helpful for the general users. Please add this in the tutorials appendix C folder
    - Make sure the notebook looks the same as the other notebooks in that folder, especially the cmponent rendering lines. Only deviate from a similar component template if your component has some especially unique behavior that is worth highlighting
    - Important: Make sure the cell outputs are "cleared" before committing the notebook to your pull request.

#### Unit-test for the new QComponent
Unit-test plays the most important part in making sure your work is functional and that subsequent commits to github do not accidental modify the component behavior. The qiskit-metal team can help you add the unit-test during the pull-request review (cannot be approved without it), but you can also add the unit-test following these seimple instructions
1. Add the instantiation test for the new component inside file `test_qlibrary_1_instantiate.py`:
    1. Add an import towards the top of the file for the new component class
    1. Create a method to test the instance. You can use as a template the method `test_qlibrary_qubits_transmon_pocket()`
1. Add the options test for the new component inside file `test_qlibrary_2_options.py`:
    1. Add an import towards the top of the file for the new component class
    1. Create a method to test the options. You can use as a template the method `test_qlibrary_transmon_concentric_options()`
1. Add the functionality test for the new component inside file `test_qlibrary_3_functionality.py`:
    1. Add an import towards the top of the file for the new component class
    1. If needed, create a method to test the metadata. You can use as a template the method `test_qlibrary_transmon_pocket_component_metadata()`
    1. Add any other functional test that you deem appropriate

#### Circuit example notebook to the QComponent documentation
Documentation plays the most important part in your showcase. If you completed the steps above you already have already completed the basic API documentation. Some special components might need to be added to the list of explicit notebook examples. To do that you need to follow these instructions below
1. Add the notebook icon to correctly visualize in the qiskit-metal gui
    1. Edit and execute the `docs/_utility/generate_images.ipynb` to include the new component and generate its icon image for the doc notebook
1. Create the notebook in the doc examples folder
    1. Copy to doc/circuit-examples the tutorial component notebook that you previously created in the tutorial appendix C.
    1. Enable the tags: View -> Cell toolbar -> tags
    1. Find the cell that contains the image generation: `gui.figure.savefig('shot.png') ...` . If you do not have it in the notebook, please check other notebooks in this folder and mimic them.
        - Add to this cell the tag nbsphinx-thumbnail
    1. Execute and save the notebook with all the cell results
1. Run the doc build locally to update the apidocs folder files
1. Commit back to the PR
