This directory contains qtpy, which is used to make AstViewer compatiable with
PyQt5, PyQt4 and PySide.

It is included in AstViewer instead of making it an external dependency because AstViewer is not
expected to change and no issues are expected to be found in qtpy.

The included version is forked from commit e863f422c7ef78f66223adaa40d52cba4a3b2fce because the
next commit throws exceptions in case the old header methods of QHeaderView are used, which may
break things if packages that do and do not use qtpy are used in one program (which is admittedly
unlikely with AstViewer). See: https://github.com/spyder-ide/qtpy/pull/65#issuecomment-252472704

This directory only contains the parts of qtpy that are needed to keep it small (it is already
twice the size of the AstViewer itself. For the complete source of qtpy look on GitHub here:
https://github.com/spyder-ide/qtpy

2016-10-15, Pepijn Kenter.
