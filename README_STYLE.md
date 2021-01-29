# Qiskit Metal Style Guide
The Metal code style sticks to the PEP-8 convention for Python code.

## PEP-8 Cheat Sheet
**Naming Conventions**

* Never use I, O, or l single letter names as these can be mistaken for 1 and 0 depending on typeface.
* Use snake case for function names.  e.g. `function`, `my_function`
* Use snake case for method names.  e.g. `class_method`, `method`
* Use snake case for variable names.  e.g. `x`, `var`, `my_variable`
* Use snake case for module names.  e.g. `module.py`, `my_modeul.py`
* Use camel case for class names.  e.g. `Model`, `MyClass`
* Use all capital letters for constants.  e.g. `CONSTANT`, `MY_CONSTANT`

**Maximum Line Length**

* Line length should be limited to 79 characters.
* Python will assume line continuation if the code is contained within parentheses, brackets, or braces:

```
def function(arg_one, arg_two,
             arg_three, arg_four):
    return arg_one
```

* Use a backslash to break lines that a too long:

```
from mypackage import example1, example2 \
    example3
```

**Indentation**

* Use 4 spaces to indicate indentation.
* Spaces are preferred over tabs

**Comments**

* Use complete sentences, starting with a capital letter.
* Remember to update the comments when the code changes.
* Indent block comments to the same level as the code they describe.
* Start each line with a # followed by a single space.
* Separate paragraphs by a line containing a single #.
* Use inline comments sparingly.
* Don't use inline comments to explain the obvious.

**When to Avoid Adding Whitespace**

* At the end of a line.
* Immediately inside parentheses, brackets, or braces.
* Before a comma, semicolon, or colon.
* Before the open parenthesis that starts the argument list of a function.
* Before the open bracket that starts an index.
* Between a trailing comma and a closing parenthesis.

**Where to Put Closing Braces**

* Line up the closing brace with the first character of the line that starts the construct:

```
list_of_numbers = [
    1, 2, 3,
    4, 5, 6
]
```

**Whitespace Around Binary Operators**

* Surround assignment and comparison binary operators with a single space on either side.
* When = is used to assign a default value to a function argument do not surround it with spaces.

**Other Recommendations**

* To be sure a function can't be called again, use the `del` method.

```
my_function()
del my_function
```

* Use a function when you want to *do* something.
* Use a class to define a specific thing that *does* something.
* Define simple interfaces over simple implementation.
* Utilize encapsulation and abstraction to manage complexity.
* Define errors out of existence

## PEP-8 Style Guide
For a more complete understanding of PEP-8, familiarize yourself with the complete [Python Style Guide](https://www.python.org/dev/peps/pep-0008/).
