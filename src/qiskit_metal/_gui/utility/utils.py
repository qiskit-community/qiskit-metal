import re
from pathlib import Path

"""
Given a filename and a search target, we
open that file and search
"""


def findProperty(filename, searchTarget):
    pathname = Path(filename)
    if pathname.is_file():
        filetext = pathname.read_text()
        matches = re.findall(searchTarget, filetext)
        return matches
    else:
        return None


def module_path_from_abs_file_path(abs_file_path: str) -> str:
    """Return the importable dotted module path for a source file.

    Walks up from the file to the highest directory still containing an
    ``__init__.py``, which is the package root, and joins the traversed
    names. This works for any importable package, not just
    ``qiskit_metal`` -- so a QComponent shipped by a separate
    distribution resolves correctly (issue #1178).

    Replaces a substring slice of the form
    ``abs_file_path[abs_file_path.index("qiskit_metal"):]``, which had
    been copy-pasted into two call sites. That matched on a *path
    substring*, which broke in two ways:

    * a file outside ``qiskit_metal`` raised
      ``ValueError: substring not found``;
    * any path merely containing the name -- a checkout under
      ``~/qiskit_metal_dev/``, a folder called
      ``qiskit_metal_experiments`` -- was sliced at the wrong place and
      resolved to a module that does not exist.

    Lives here, in a Qt-free utility module, so both the Library-pane
    delegate and the parameter-entry window can share one implementation
    without an import cycle.

    Known limitation: PEP 420 namespace packages (directories with no
    ``__init__.py``) are importable by Python but are rejected here,
    because the walk has nothing to anchor on. Regular packages -- the
    overwhelming majority, and what every component in this repository
    uses -- are unaffected. Resolving those would mean deriving the
    module path from the longest matching ``sys.path`` entry instead;
    see issue #1178, where the external-component discovery mechanism is
    still being decided.

    Args:
        abs_file_path (str): absolute path to a ``.py`` file.

    Returns:
        str: dotted module path, e.g.
        ``qiskit_metal.qlibrary.qubits.transmon_pocket``.

    Raises:
        ValueError: if the file is not inside an importable package.
    """
    path = Path(abs_file_path)
    if not path.is_absolute():
        # A relative path would be resolved against the current working
        # directory, which is arbitrary and almost never where the package
        # lives. Callers pass absolute paths; say so rather than silently
        # resolving to the wrong file (or to nothing).
        raise ValueError(
            f"{abs_file_path} is not an absolute path; module resolution "
            "would depend on the current working directory."
        )
    if not path.is_file():
        raise ValueError(f"{abs_file_path} does not exist, so it has no module path.")

    path = path.resolve()
    parts = [path.stem]

    directory = path.parent
    while (directory / "__init__.py").is_file():
        parts.append(directory.name)
        parent = directory.parent
        if parent == directory:  # filesystem root
            break
        directory = parent

    if len(parts) == 1:
        raise ValueError(
            f"{abs_file_path} is not inside an importable package "
            "(no __init__.py alongside it), so it has no module path."
        )

    return ".".join(reversed(parts))


def class_from_abs_file_path(abs_file_path: str):
    """Import ``abs_file_path`` and return the class it defines.

    Returns the first class whose ``__module__`` ends with the file's own
    module name, i.e. the class defined *in* that file rather than one
    imported into it.

    Args:
        abs_file_path (str): absolute path to a ``.py`` file.

    Returns:
        type | None: the class, or ``None`` if the module defines none.
    """
    import importlib
    import inspect

    module_path = module_path_from_abs_file_path(abs_file_path)
    module = importlib.import_module(module_path)
    class_owner = module_path.split(".")[-1]

    for _, member in inspect.getmembers(module, inspect.isclass):
        if str(member.__module__).endswith(class_owner):
            return member
    return None
