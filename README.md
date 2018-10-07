astviewer
=========

Graphical User Interface for viewing Python Abstract Syntax Trees.

![astviewer screen shot](screen_shot.png)

### Installation:

First install [PyQt](https://www.riverbankcomputing.com/software/pyqt/download5) or 
[PySide](http://wiki.qt.io/Category:LanguageBindings::PySide::Downloads). Either one is fine, 
AstViewer automatically detects which Qt bindings are installed. If both bindings are installed
it prefers PyQt over PySide (You can force AstViewer to use a certain binding by setting the
`QT_API` environment variable to `pyqt5`, `pyqt4`, `pyside` or `pyside2`.)

If you are using the Anaconda Python distribution it is recommended to install PyQt as follows:

    %> conda install pyqt
    
or, for PySide use

    %> conda install pyside2

If you are *not* using the Anaconda Python distro, you can install the dependencies with Pip as follows:

    %> pip3 install pyqt5
    
or

    %> pip install pyside2

There is no conda recipe for the AstViewer, but you can use Pip to install it even if you use 
Anaconda. To install it type:

    %> pip install astviewer


### Usage:
	
Command line example:
	
    %> pyastviewer myprog.py
	
Examples to use from within Python:

```python
	>>> from astviewer.main import view
	>>> view(file_name='myprog.py')
	>>> view(source_code = 'a + 3', mode='eval')
```

### Further links:

The [Green Tree Snakes documentation on ASTs](http://greentreesnakes.readthedocs.org/) is available
for those who find the [Python ast module documentation](http://docs.python.org/3/library/ast) too brief.
