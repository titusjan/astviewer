astviewer
=========

Python Abstract Syntax Tree viewer/browser in Qt.

![astviewer screen shot](screen_shot.png)

#### Installation:

1.	Install PySide:
	http://qt-project.org/wiki/Category:LanguageBindings::PySide
	
2.	Run the installer:

		%> sudo python setup.py install
	
#### Usage:
	
*	Command line example:
	
		%> pyastviewer myprog.py
	
*	Examples to use from within Python:

		>>> from astviewer import view
		>>> view(file_name='myprog.py', width=800, height=600)
		>>> view(source_code = 'a + 3', mode='eval')


#### Further links:

The [Green Tree Snakes documentation on ASTs](http://greentreesnakes.readthedocs.org/) is available
for those who find the [Python ast module documentation](http://docs.python.org/3/library/ast) too brief.
