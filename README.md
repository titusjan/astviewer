astviewer
=========

Python Abstract Syntax Tree viewer/browser in Qt.

![astviewer screen shot](screen_shot.png)

#### Installation:


1.	Install
	    [PySide](http://wiki.qt.io/Category:LanguageBindings::PySide::Downloads)
    or
	    [PyQt4](https://www.riverbankcomputing.com/software/pyqt/download).

2.	Run the installer:

		%> python setup.py install
	
#### Usage:
	
*	Command line example:
	
		%> pyastviewer myprog.py
	
*	Examples to use from within Python:

	```python
	>>> from astviewer.main import view
	>>> view(file_name='myprog.py')
	>>> view(source_code = 'a + 3', mode='eval')
	```

#### Further links:

The [Green Tree Snakes documentation on ASTs](http://greentreesnakes.readthedocs.org/) is available
for those who find the [Python ast module documentation](http://docs.python.org/3/library/ast) too brief.
