# Change log

## 2026-05-31, Version 1.1.3

* Replaced setup.py with modern pyproject.toml file.
* Uses UV.
* Removed PySide2 and QtPy dependencies. Only works with PyQt5.
* Fix crash when clicking on empty editor.
* Fix error on exit.


## 2018-10-07, Version 1.1.2

* Works with PySide2.


## 2016-11-05, Version 1.1.1

* Source code is shown in a dock-widget.
* Fixed setup.py to work when PyQt is not installed.


## 2016-10-29, Version 1.1.0

* Works with Python 3.
* Works with PyQt5.
* Persistent state (e.g. window size/pos) across sessions.
* Assumes Python files are UTF-8 encoded instead of ASCII.
* Clicking the text will select the corresponding node in the tree.
* Highlighting works recursively.  
    Still not perfect, see [Issue 1](https://github.com/titusjan/astviewer/issues/1)


## 2013-08-10, Version 1.0.0

* Added setup.py installer.
* Made separate (pyasterviewer) command line application
    and (asterviewer.py) module.
* The AstViewer class constructor accepts a source_code.
    parameter so source can be compared from a string.
* The AstViewer class constructor accepts a mode parameter.
* Bug fix: highlighting of the last element now works.

	