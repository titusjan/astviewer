
""" 
   Program that shows the program on the right and its abstract syntax tree (ast) on the left.
"""
from __future__ import print_function

import sys, logging, types, ast

from PySide import QtCore, QtGui

logger = logging.getLogger(__name__)

DEBUGGING = False

PROGRAM_NAME = 'astview'
PROGRAM_VERSION = '1.0.0'
ABOUT_MESSAGE = u"""%(prog)s version %(version)s
""" % {"prog": PROGRAM_NAME, "version": PROGRAM_VERSION}

# Tree column indices
COL_NODE = 0
COL_FIELD = 1
COL_CLASS = 2
COL_VALUE = 3
COL_POS = 4
COL_HIGHLIGHT = 5



def check_class(obj, target_class, allow_none = False):
    """ Checks that the  obj is a (sub)type of target_class. 
        Raises a TypeError if this is not the case.
    """
    if not isinstance(obj, target_class):
        if not (allow_none and obj is None):
            raise TypeError("obj must be a of type {}, got: {}"
                            .format(target_class, type(obj)))


def get_qapplication_instance():
    """ Returns the QApplication instance. Creates one if it doesn't exist.
    """
    app = QtGui.QApplication.instance()
    if app is None:
        app = QtGui.QApplication(sys.argv)
    check_class(app, QtGui.QApplication)
    return app


def view(width=None, height=None, *args, **kwargs):
    """ Opens an AstViewer window
    """
    app = get_qapplication_instance()
    
    window = AstViewer(*args, **kwargs)
    if width and height:
        window.resize(width, height)
    window.show()
        
    logger.info("Starting the AST viewer...")
    exit_code = app.exec_()
    logger.info("AST viewer viewer done...")
    return exit_code

        
def class_name(obj):
    """ Returns the class name of an object"""
    return obj.__class__.__name__


# The main window inherits from a Qt class, therefore it has many 
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201 

class AstViewer(QtGui.QMainWindow):
    """ The main application.
    """
    def __init__(self, file_name = None):
        """ Constructor
        """
        super(AstViewer, self).__init__()
        
        # Models
        self._file_name = ""
        self._source_code = ""
        
        # Views
        self._setup_actions()
        self._setup_menu()
        self._setup_views()
        self.setWindowTitle('{}'.format(PROGRAM_NAME))
        
        # Update views
        self.col_field_action.setChecked(False)
        self.col_class_action.setChecked(False)
        self.col_value_action.setChecked(False)
        self.open_file(file_name = file_name)


    def _setup_actions(self):
        """ Creates the MainWindow actions.
        """  
        self.col_field_action = QtGui.QAction(
            "Show Field Column", self, checkable=True, checked=True,
            statusTip = "Shows or hides the Field column")
        self.col_field_action.setShortcut("Ctrl+1")
        assert self.col_field_action.toggled.connect(self.show_field_column)
        
        self.col_class_action = QtGui.QAction(
            "Show Class Column", self, checkable=True, checked=True,
            statusTip = "Shows or hides the Class column")
        self.col_class_action.setShortcut("Ctrl+2")
        assert self.col_class_action.toggled.connect(self.show_class_column)
        
        self.col_value_action = QtGui.QAction(
            "Show Value Column", self, checkable=True, checked=True,
            statusTip = "Shows or hides the Value column")
        self.col_value_action.setShortcut("Ctrl+3")
        assert self.col_value_action.toggled.connect(self.show_value_column)
        
        self.col_pos_action = QtGui.QAction(
            "Show Line:Col Column", self, checkable=True, checked=True,
            statusTip = "Shows or hides the 'Line : Col' column")
        self.col_pos_action.setShortcut("Ctrl+4")
        assert self.col_pos_action.toggled.connect(self.show_pos_column)
                              
    def _setup_menu(self):
        """ Sets up the main menu.
        """
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("&New", self.new_file, "Ctrl+N")
        file_menu.addAction("&Open...", self.open_file, "Ctrl+O")
        #file_menu.addAction("C&lose", self.close_window, "Ctrl+W")
        file_menu.addAction("E&xit", self.quit_application, "Ctrl+Q")
        
        if DEBUGGING is True:
            file_menu.addSeparator()
            file_menu.addAction("&Test", self.my_test, "Ctrl+T")
        
        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.col_field_action)        
        view_menu.addAction(self.col_class_action)        
        view_menu.addAction(self.col_value_action)        
        view_menu.addAction(self.col_pos_action)        
        
        self.menuBar().addSeparator()
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction('&About', self.about)


    def _setup_views(self):
        """ Creates the UI widgets. 
        """
        central_splitter = QtGui.QSplitter(self, orientation = QtCore.Qt.Horizontal)
        self.setCentralWidget(central_splitter)
        central_layout = QtGui.QHBoxLayout()
        central_splitter.setLayout(central_layout)
        
        # Tree widget
        self.ast_tree = QtGui.QTreeWidget()
        self.ast_tree.setColumnCount(2)
        
        self.ast_tree.setHeaderLabels(["Node", "Field", "Class", "Value", 
                                       "Line : Col", "Highlight"])
        self.ast_tree.header().resizeSection(COL_NODE, 250)
        self.ast_tree.header().resizeSection(COL_FIELD, 80)
        self.ast_tree.header().resizeSection(COL_CLASS, 80)
        self.ast_tree.header().resizeSection(COL_VALUE, 80)
        self.ast_tree.header().resizeSection(COL_POS, 80)
        self.ast_tree.header().resizeSection(COL_HIGHLIGHT, 100)
        self.ast_tree.setColumnHidden(COL_HIGHLIGHT, not DEBUGGING)          
        
        # Don't stretch last column, it doesn't play nice when columns are 
        # hidden and then shown again. 
        self.ast_tree.header().setStretchLastSection(True) 
        central_layout.addWidget(self.ast_tree)

        # Editor widget
        font = QtGui.QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(13)

        self.editor = QtGui.QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setFont(font)
        self.editor.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.editor.setStyleSheet("selection-color: black; selection-background-color: yellow;")
        central_layout.addWidget(self.editor)
        
        # Splitter parameters
        central_splitter.setCollapsible(0, False)
        central_splitter.setCollapsible(1, False)
        central_splitter.setSizes([330, 760])
        central_splitter.setStretchFactor(0, 1)
        central_splitter.setStretchFactor(1, 0)
        
        # Connect signals
        assert self.ast_tree.currentItemChanged.connect(self.highlight_node)
        
    
    def new_file(self):
        """ Clears the widgets """
        self._file_name = ""
        self._source_code = ""
        self.editor.clear()
        self._fill_ast_tree_widget()
        

    def open_file(self, file_name=None):
        """ Opens a new file. Show the open file dialog if file_name is None.
        """
        if not file_name:
            file_name, _ = QtGui.QFileDialog.getOpenFileName(self, "Open File", 
                                                             '', "Python Files (*.py)")
        if file_name:
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
                msg = "Unable to open: {}".format(file_name)
                logger.warn(msg)
                QtGui.QMessageBox.warning(self, 'warning', msg)
                file_name = ''
                
        self.setWindowTitle('{} - {}'.format(PROGRAM_NAME, file_name))
        self._fill_ast_tree_widget()
   
    
    def _fill_ast_tree_widget(self):
        """ Populates the tree widget.
        """
        # State we keep during the recursion.
        # Is needed to populate the selection column.
        to_be_updated = list([])
        state = {'from': '? : ?', 'to': '1 : 0'}
                
        def add_node(ast_node, parent_item, field_label):
            """ Helper function that recursively adds nodes.

                :param parent_item: The parent QTreeWidgetItem to which this node will be added
                :param field_label: Labels how this node is known to the parent
            """
            node_item = QtGui.QTreeWidgetItem(parent_item)

            if hasattr(ast_node, 'lineno'):
                position_str = "{:d} : {:d}".format(ast_node.lineno, ast_node.col_offset)

                # If we find a new position string we set the items found since the last time
                # to 'old_line : old_col : new_line : new_col' and reset the list 
                # of to-be-updated nodes                 
                if position_str != state['to']:
                    state['from'] = state['to']
                    state['to'] = position_str
                    for elem in to_be_updated:
                        elem.setText(COL_HIGHLIGHT, "{} : {}".format(state['from'], state['to']))
                    to_be_updated[:] = [node_item]
                else:
                    to_be_updated.append(node_item)
            else:
                to_be_updated.append(node_item)
                position_str = ""

            # Recursively descent the AST 
            if isinstance(ast_node, ast.AST):
                value_str = ''
                node_str = "{} = {}".format(field_label, class_name(ast_node))
                for key, val in ast.iter_fields(ast_node):
                    add_node(val, node_item, key)
            elif type(ast_node) == types.ListType or type(ast_node) == types.TupleType:
                value_str = ''
                node_str = "{} = {}".format(field_label, class_name(ast_node))
                for idx, elem in enumerate(ast_node):
                    add_node(elem, node_item, "{}[{:d}]".format(field_label, idx))
            else:
                value_str = repr(ast_node)
                node_str = "{} = {}".format(field_label, value_str)
                
            node_item.setText(COL_NODE, node_str)
            node_item.setText(COL_FIELD, field_label)
            node_item.setText(COL_CLASS, class_name(ast_node))
            node_item.setText(COL_VALUE, value_str)
            node_item.setText(COL_POS, position_str)
            
        # End of helper function
        
        syntax_tree = ast.parse(self._source_code, filename=self._file_name, mode='exec')
        #logger.debug(ast.dump(syntax_tree))
        
        self.ast_tree.clear()    
        add_node(syntax_tree, self.ast_tree, '"{}"'.format(self._file_name))
        self.ast_tree.expandToDepth(1)
        
        # Fill highlight column for remainder of nodes
        for elem in to_be_updated:
            elem.setText(COL_HIGHLIGHT, "{} : {}".format(state['to'], "... : ..."))
            
        
 
    @QtCore.Slot(QtGui.QTreeWidgetItem, QtGui.QTreeWidgetItem)
    def highlight_node(self, current_item, _previous_item):
        """ Highlights the node if it has line:col information.
        """
        highlight_str = current_item.text(COL_HIGHLIGHT)
        from_line_str, from_col_str, to_line_str, to_col_str = highlight_str.split(":")
            
        try:
            from_line_col = (int(from_line_str), int(from_col_str)) 
        except ValueError:    
            from_line_col = None

        try:
            to_line_col = (int(to_line_str), int(to_col_str)) 
        except ValueError:    
            to_line_col = None
        
        logger.debug("Highlighting ({!r}) : ({!r})".format(from_line_col, to_line_col))
        self.select_text(from_line_col, to_line_col)
        

    def select_text(self, from_line_col, to_line_col):
        """ Selects a text in the range from_line:col ... to_line:col
            
            from_line_col and to_line_col should be a (line, column) tuple
            If from_line_col is None, the selection starts at the beginning of the document
            If to_line_col is None, the selection goes to the end of the document
        """
        text_cursor = self.editor.textCursor()
        
        if from_line_col is None:
            text_cursor.movePosition(QtGui.QTextCursor.Start, QtGui.QTextCursor.MoveAnchor)
        else:
            from_line, from_col = from_line_col
            # findBlockByLineNumber seems to be 0-based.
            from_text_block = self.editor.document().findBlockByLineNumber(from_line - 1)
            from_pos = from_text_block.position() + from_col
            text_cursor.setPosition(from_pos, QtGui.QTextCursor.MoveAnchor)

        if to_line_col is None:
            text_cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)
        else:
            to_line, to_col = to_line_col
            to_text_block = self.editor.document().findBlockByLineNumber(to_line - 1)
            to_pos = to_text_block.position() + to_col
            text_cursor.setPosition(to_pos, QtGui.QTextCursor.KeepAnchor)
        
        self.editor.setTextCursor(text_cursor)
        

    @QtCore.Slot(int)
    def show_field_column(self, checked):
        """ Shows or hides the field column"""
        self.ast_tree.setColumnHidden(COL_FIELD, not checked)                

    @QtCore.Slot(int)
    def show_class_column(self, checked):
        """ Shows or hides the class column"""
        self.ast_tree.setColumnHidden(COL_CLASS, not checked)                

    @QtCore.Slot(int)
    def show_value_column(self, checked):
        """ Shows or hides the value column"""
        self.ast_tree.setColumnHidden(COL_VALUE, not checked)                

    @QtCore.Slot(int)
    def show_pos_column(self, checked):
        """ Shows or hides the line:col column"""
        self.ast_tree.setColumnHidden(COL_POS, not checked)                

    def my_test(self):
        """ Function for testing """
        self.select_text(1, 5, 2, 5)

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

# pylint: enable=R0901, R0902, R0904, W0201

