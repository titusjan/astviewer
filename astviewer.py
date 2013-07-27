
""" 
   Program that shows the program on the right and its abstract syntax tree (ast) on the left.
"""

from __future__ import print_function

import sys, argparse, os, logging, types, ast

from PySide import QtCore, QtGui
from PySide.QtCore import Qt

logger = logging.getLogger(__name__)


PROGRAM_NAME = 'astviewer'
PROGRAM_VERSION = '0.0.1'
PROGRAM_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
IMAGE_DIRECTORY = PROGRAM_DIRECTORY + '/images/'
ABOUT_MESSAGE = u"""%(prog)s version %(version)s
""" % {"prog": PROGRAM_NAME, "version": PROGRAM_VERSION}


# The main window inherits from a Qt class, therefore it has many ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904 

class AstViewer(QtGui.QMainWindow):
    """ The main application.
    """
    def __init__(self, file_name = None):
        """ Constructor
        
            :param ast_tree: list of Figure objects
            :param figure_names: optional list with a name/label for each figure
        """
        super(AstViewer, self).__init__()
        
        # Models
        self._file_name = ""
        self._source_code = ""
        
        # Views
        self._setup_menu()
        self._setup_views()
        self.setWindowTitle(PROGRAM_NAME)
        
        # Update views
        self.open_file(file_name = file_name)

              
    def _setup_menu(self):
        """ Sets up the main menu.
        """
        file_menu = QtGui.QMenu("&File", self)
        file_menu.addAction("&New...", self.new_file, "Ctrl+N")
        file_menu.addAction("&Open...", self.open_file, "Ctrl+O")
        
        close_action = file_menu.addAction("C&lose", self.close_window)
        close_action.setShortcut("Ctrl+W")

        quit_action = file_menu.addAction("E&xit", self.quit_application)
        quit_action.setShortcut("Ctrl+Q")
        
        help_menu = QtGui.QMenu('&Help', self)
        help_menu.addAction('&About', self.about)

        self.menuBar().addMenu(file_menu)

        self.menuBar().addSeparator()
        self.menuBar().addMenu(help_menu)
        

    def _setup_views(self):
        """ Creates the UI widgets. 
        """
        #central_splitter = QtGui.QWidget()
        central_splitter = QtGui.QSplitter(self, orientation = QtCore.Qt.Horizontal)
        self.setCentralWidget(central_splitter)
        central_layout = QtGui.QHBoxLayout()
        central_splitter.setLayout(central_layout)
        
        # Tree widget
        self.ast_tree = QtGui.QTreeWidget()
        self.ast_tree.setColumnCount(2)
        #self.ast_tree.setHeaderLabels(["Class", "Field"])
        self.ast_tree.setHeaderLabels(["Field", "Class", "Value"])
        
        central_layout.addWidget(self.ast_tree)

        # Editor widget
        
        font = QtGui.QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(12)

        self.editor = QtGui.QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setFont(font)
        central_layout.addWidget(self.editor)

        central_splitter.setCollapsible(0, False)
        central_splitter.setCollapsible(1, False)
        central_splitter.setStretchFactor(0, 30)
        central_splitter.setStretchFactor(1, 30)
        
        # Connect signals
        self.ast_tree.currentItemChanged.connect(self.update_syntax_highlighting)
        

    # End of setup_methods
    # pylint: enable=W0201
    
    def new_file(self):
        self._file_name = ""
        self._source_code = ""
        self.editor.clear()
        
        self._fill_ast_tree_widget()
        

    def open_file(self, file_name=None):
        if not file_name:
            file_name, _ = QtGui.QFileDialog.getOpenFileName(self, "Open File", '', "Python Files (*.py)")

        if file_name != '':
            self._file_name = file_name 
            logger.debug("Opening {!r}".format(file_name))
            
            in_file = QtCore.QFile(file_name)
            if in_file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
                text = in_file.readAll()
                try:
                    text = str(text, encoding='ascii')  # Python 3
                except TypeError:
                    text = str(text)                    # Python 2
                self._source_code = text
                self.editor.setPlainText(self._source_code)
            else: 
                logger.warn("Unable to open: {}".format(file_name))
                
        self._fill_ast_tree_widget()
   
    
    def _fill_ast_tree_widget(self):
        """ Fills the figure list widget with the titles/number of the figures
        """
        logger.debug("_fill_ast_tree_widget")
        syntax_tree = ast.parse(self._source_code, filename=self._file_name, mode='exec')
        logger.debug(ast.dump(syntax_tree))
        
        def class_name(obj):
            return obj.__class__.__name__
                
        def add_node(ast_node, parent_item, field_label):
            """ Recursively adds nodes.

                :param parent_item: The parent QTreeWidgetItem to which this node will be added
                :param field_label: Labels how this node is known to the parent
            """
            #node_item = QtGui.QTreeWidgetItem(parent_item, [class_name(ast_node), field_label])
            node_item = QtGui.QTreeWidgetItem(parent_item, [field_label, class_name(ast_node), ""])
            
            if isinstance(ast_node, ast.AST):
                for key, val in ast.iter_fields(ast_node):
                    add_node(val, node_item, key)
                    
            elif type(ast_node) == types.ListType or type(ast_node) == types.TupleType:
                for idx, elem in enumerate(ast_node):
                    add_node(elem, node_item, "{}[{:d}]".format(field_label, idx))
                    
            else:
                node_item.setText(2, repr(ast_node))
            
        # Call helper function    
        add_node(syntax_tree, self.ast_tree, '<root>')
        self.ast_tree.expandAll()

            

    def update_syntax_highlighting(self):
        """ Updates and draws the plot with the new data
        """
        logger.debug("update_syntax_highlighting")


    def about(self):
        """ Shows the about message window. """
        QtGui.QMessageBox.about(self, "About %s" % PROGRAM_NAME, ABOUT_MESSAGE)

    def close_window(self):
        """ Closes the window """
        self.close()
        
    def quit_application(self):
        """ Closes all windows """
        app = QtGui.QApplication.instance()
        app.closeAllWindows()

# pylint: enable=R0901, R0902, R0904        


        
def main():
    """ Main program to test stand alone 
    """
    app = QtGui.QApplication(sys.argv)
    
    parser = argparse.ArgumentParser(description='Python abstract syntax tree viewer')
    parser.add_argument(dest='_file_name', help='Python input file', nargs='?')
    parser.add_argument('-l', '--log-level', dest='log_level', default = 'debug', 
        help = "Log level. Only log messages with a level higher or equal than this will be printed. Default: 'debug'",
        choices = ('debug', 'info', 'warn', 'error', 'critical'))
    
    args = parser.parse_args()

    logging.basicConfig(level = args.log_level.upper(), 
        format='%(filename)20s:%(lineno)-4d : %(levelname)-7s: %(message)s')

    logger.info('Started {}'.format(PROGRAM_NAME))
    
    ast_viewer = AstViewer(file_name = args._file_name)
    ast_viewer.resize(1200, 800)
    ast_viewer.show()
    
    exit_code = app.exec_()
    logging.info('Done {}'.format(PROGRAM_NAME))
    sys.exit(exit_code)


if __name__ == '__main__':

    main()
    
    
        
