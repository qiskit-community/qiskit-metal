# Changelog Note Scratchpad for Developers

This log is used by developers to jot notes.

For the offical user-facing changelog for a particular release can be found in the correspondent Github release page. For example, you can find the changelog for the `0.0.4` release [here](https://github.com/Qiskit/qiskit-metal/releases/tag/0.0.4)

The changelog for all releases can be found in the release page: [![Releases](https://img.shields.io/github/release/Qiskit/qiskit-metal.svg?style=popout-square)](https://github.com/Qiskit/qiskit-metal/releases)

## QISKIT METAL v0.5 (2025)

Adressing massive package changes and ports:
- pyqt5 to pyside6 - massive port of the GUI.
- GDSPY to GDSTK
- PYAEDT to ansys and v1.0 new syntax. Major update. Needs lots of testing.

### Gui
1. Added traceback reporting in the logging.
2.  Fixed - "metal: WARNING: endResetModel called on LibraryFileProxyModel(0x17fda8200) without calling beginResetModel first (No context available from Qt)"
3. Fixed MPL Rendere axes issue "Ignoring fixed y limits to fulfill fixed data aspect with adjustable data limits. Ignoring fixed x limits to fulfill fixed data aspect with adjustable data limits."
4. Added red border style to new component UI create button to underscore

### PYAEDT
FutureWarning: Module 'pyaedt' has become an alias to the new package structure. Please update you imports to use the new architecture based on 'ansys.aedt.core'. In addition, some files have been renamed to follow the PEP 8 naming convention. The old structure and file names will be deprecated in future versions, see https://aedt.docs.pyansys.com/version/stable/release_1_0.html
