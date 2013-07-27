
""" 
   Program that shows the program on the right and its abstract syntax tree (ast) on the left.
"""

from __future__ import print_function

import sys, argparse, os, logging


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
    def __init__(self):
        """ Constructor
        
            :param ast_tree: list of Figure objects
            :param figure_names: optional list with a name/label for each figure
        """
        super(AstViewer, self).__init__()
        
        # Models

        self._setup_menu()
        self._setup_views()
        self.setWindowTitle(PROGRAM_NAME)

              
    def _setup_menu(self):
        """ Sets up the main menu.
        """
        file_menu = QtGui.QMenu("&File", self)

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
        central_widget = QtGui.QWidget()
        self.setCentralWidget(central_widget)
        
        central_layout = QtGui.QHBoxLayout()
        central_widget.setLayout(central_layout)
        
        self.ast_tree = QtGui.QListWidget()
        central_layout.addWidget(self.ast_tree)
        self._fill_ast_tree()
        
        # Connect signals
        self.ast_tree.currentItemChanged.connect(self.update_syntax_highlighting)
        self.ast_tree.setCurrentRow(0)
        

    # End of setup_methods
    # pylint: enable=W0201
    
    def _fill_ast_tree(self):
        """ Fills the figure list widget with the titles/number of the figures
        """
        logger.debug("update_syntax_highlighting")
        return 
        for fig_idx, fig_name in enumerate(self._figure_names):
            item = QtGui.QListWidgetItem(fig_name)
            item.setData(Qt.UserRole, fig_idx)
            self.ast_tree.addItem(item)
        

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
    parser.add_argument('-l', '--log-level', dest='log_level', default = 'debug', 
        help = "Log level. Only log messages with a level higher or equal than this will be printed. Default: 'warn'",
        choices = ('debug', 'info', 'warn', 'error', 'critical'))
    
    args = parser.parse_args()

    logging.basicConfig(level = args.log_level.upper(), stream = sys.stdout, 
        format='%(filename)20s:%(lineno)-4d : %(levelname)-7s: %(message)s')

    logger.info('Started {}'.format(PROGRAM_NAME))

    
    ast_viewer = AstViewer()
    ast_viewer.show()

    exit_code = app.exec_()
    logging.info('Done {}'.format(PROGRAM_NAME))
    sys.exit(exit_code)
    
    
    logger.info('Done {}'.format(PROGRAM_NAME))

    sys.exit(exit_code)


if __name__ == '__main__':

    main()
    
    
        
