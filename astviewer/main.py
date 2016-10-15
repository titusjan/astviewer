
""" 
   Program that shows the program on the right and its abstract syntax tree (ast) on the left.
"""
from __future__ import print_function
                
import sys, logging, ast, traceback

from astviewer.misc import get_qapplication_instance, class_name, get_qsettings
from astviewer.misc import ABOUT_MESSAGE, PROGRAM_NAME, DEBUGGING
from astviewer.qtpy import QtCore, QtGui, QtWidgets
from astviewer.toggle_column_mixin import ToggleColumnTreeWidget


logger = logging.getLogger(__name__)


def view(*args, **kwargs):
    """ Opens an AstViewer window
    """
    app = get_qapplication_instance()
    
    window = AstViewer(*args, **kwargs)
    window.show()

    if 'darwin' in sys.platform:
        window.raise_()
        
    logger.info("Starting the AST event loop.")
    exit_code = app.exec_()
    logger.info("AST viewer done...")
    return exit_code


# The main window inherits from a Qt class, therefore it has many 
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201, R0913 

class AstViewer(QtWidgets.QMainWindow):
    """ The main application.
    """
    HEADER_LABELS = ["Node", "Field", "Class", "Value", "Line : Col", "Highlight"]
    (COL_NODE, COL_FIELD, COL_CLASS, COL_VALUE, COL_POS, COL_HIGHLIGHT) = range(len(HEADER_LABELS))

    def __init__(self, file_name = '', source_code = '', mode='exec', reset=False):
        """ Constructor
            
            AST browser windows that displays the Abstract Syntax Tree
            of source code. 
            
            The source can be given as text in the source parameter, or
            can be read from a file. The file_name parameter overrides
            the source parameter.
            
            The mode argument specifies what kind of code must be compiled; 
            it can be 'exec' if source consists of a sequence of statements, 
            'eval' if it consists of a single expression, or 'single' if it 
            consists of a single interactive statement (in the latter case, 
            expression statements that evaluate to something other than None 
            will be printed).
            (see http://docs.python.org/2/library/functions.html#compile)
            
            If reset is True, the persistenc settings (e.g. window size) are
            reset to their default values.
        """
        super(AstViewer, self).__init__()
        
        valid_modes = ['exec', 'eval', 'single']
        if mode not in valid_modes:
            raise ValueError("Mode must be one of: {}".format(valid_modes))
        
        # Models
        self._file_name = '<source>'
        self._source_code = source_code
        self._mode = mode
        
        # Views
        #self._setup_actions()
        self._setup_menu()
        self._setup_views(reset=reset)
        self.setWindowTitle('{}'.format(PROGRAM_NAME))
        
        # Update views
        if file_name and source_code:
            logger.warning("Both the file_name and source_code are defined: source_code ignored.")
            
        if not file_name and not source_code:
            file_name = self._get_file_name_from_dialog()
        
        self._update_widgets(file_name)


    def _setup_menu(self):
        """ Sets up the main menu.
        """
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("&New", self.new_file, "Ctrl+N")
        file_menu.addAction("&Open...", self.open_file, "Ctrl+O")
        file_menu.addAction("E&xit", self.quit_application, "Ctrl+Q")
        
        if DEBUGGING is True:
            file_menu.addSeparator()
            file_menu.addAction("&Test", self.my_test, "Ctrl+T")
        
        #view_menu = self.menuBar().addMenu("&View")

        self.menuBar().addSeparator()
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction('&About', self.about)


    def _setup_views(self, reset=False):
        """ Creates the UI widgets. 
        """
        self.central_splitter = QtWidgets.QSplitter(self, orientation = QtCore.Qt.Horizontal)
        self.setCentralWidget(self.central_splitter)

        # Tree widget
        self.ast_tree = ToggleColumnTreeWidget()
        self.central_splitter.addWidget(self.ast_tree)

        self.ast_tree.setAlternatingRowColors(True)
        self.ast_tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.ast_tree.setUniformRowHeights(True)
        self.ast_tree.setAnimated(False)

        self.ast_tree.setHeaderLabels(AstViewer.HEADER_LABELS)
        tree_header = self.ast_tree.header()
        self.ast_tree.add_header_context_menu(checkable={'Node': False}, enabled={'Node': False})
        
        # Don't stretch last column, it doesn't play nice when columns are
        # hidden and then shown again.
        tree_header.setStretchLastSection(False)

        # Editor widget
        font = QtGui.QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(13)

        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setFont(font)
        self.editor.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.editor.setStyleSheet("selection-color: black; selection-background-color: yellow;")
        self.central_splitter.addWidget(self.editor)
        
        # Splitter parameters
        self.central_splitter.setCollapsible(0, False)
        self.central_splitter.setCollapsible(1, False)
        self.central_splitter.setSizes([500, 500])
        self.central_splitter.setStretchFactor(0, 0.5)
        self.central_splitter.setStretchFactor(1, 0.5)

        # Read persistent settings
        self._readViewSettings(reset = reset)

        # Connect signals
        self.ast_tree.currentItemChanged.connect(self.highlight_node)
        
    
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
            file_name = self._get_file_name_from_dialog()
        
        self._update_widgets(file_name)

    
    def _get_file_name_from_dialog(self):
        """ Opens a file dialog and returns the file name selected by the user
        """
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open File",
                        '', "Python Files (*.py);;All Files (*)")
        return file_name

    
    def _update_widgets(self, file_name):
        """ Reads source from a file and updates the tree and editor widgets.. 
        """            
        if file_name:
            self._load_file(file_name)
            
        self.setWindowTitle('{} - {}'.format(PROGRAM_NAME, self._file_name))
        self.editor.setPlainText(self._source_code)

        #pylint: disable=broad-except
        try:
            self._fill_ast_tree_widget()
        except Exception as ex:
            if DEBUGGING:
                raise
            else:
                stack_trace = traceback.format_exc()
                msg = "Unable to parse file: {}\n\n{}\n\n{}" \
                    .format(self._file_name, ex, stack_trace)
                logger.exception(ex)
                QtWidgets.QMessageBox.warning(self, 'error', msg)
        
                
    def _load_file(self, file_name):
        """ Opens a file and sets self._file_name and self._source code if succesful
        """
        logger.debug("Opening {!r}".format(file_name))
        
        in_file = QtCore.QFile(file_name)
        if in_file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
            text = in_file.readAll()
            try:
                source_code = str(text, encoding='ascii')  # Python 3
            except TypeError:
                source_code = str(text)                    # Python 2
                
            self._file_name = file_name
            self._source_code = source_code
            
        else:
            msg = "Unable to open file: {}".format(file_name)
            logger.warning(msg)
            QtWidgets.QMessageBox.warning(self, 'error', msg)
            

    def _fill_ast_tree_widget(self):
        """ Populates the tree widget.
        """
        self.ast_tree.clear()    
        
        # State we keep during the recursion.
        # Is needed to populate the selection column.
        to_be_updated = list([])
        state = {'from': '? : ?', 'to': '1 : 0'}
                
        def add_node(ast_node, parent_item, field_label):
            """ Helper function that recursively adds nodes.

                :param parent_item: The parent QTreeWidgetItem to which this node will be added
                :param field_label: Labels how this node is known to the parent
            """
            node_item = QtWidgets.QTreeWidgetItem(parent_item)

            if hasattr(ast_node, 'lineno'):
                position_str = "{:d} : {:d}".format(ast_node.lineno, ast_node.col_offset)

                # If we find a new position string we set the items found since the last time
                # to 'old_line : old_col : new_line : new_col' and reset the list 
                # of to-be-updated nodes                 
                if position_str != state['to']:
                    state['from'] = state['to']
                    state['to'] = position_str
                    for elem in to_be_updated:
                        elem.setText(AstViewer.COL_HIGHLIGHT,
                                     "{} : {}".format(state['from'], state['to']))
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
            elif isinstance(ast_node, (list, tuple)):
                value_str = ''
                node_str = "{} = {}".format(field_label, class_name(ast_node))
                for idx, elem in enumerate(ast_node):
                    add_node(elem, node_item, "{}[{:d}]".format(field_label, idx))
            else:
                value_str = repr(ast_node)
                node_str = "{} = {}".format(field_label, value_str)
                
            node_item.setText(AstViewer.COL_NODE, node_str)
            node_item.setText(AstViewer.COL_FIELD, field_label)
            node_item.setText(AstViewer.COL_CLASS, class_name(ast_node))
            node_item.setText(AstViewer.COL_VALUE, value_str)
            node_item.setText(AstViewer.COL_POS, position_str)
            
        # End of helper function
        
        syntax_tree = ast.parse(self._source_code, filename=self._file_name, mode=self._mode)
        #logger.debug(ast.dump(syntax_tree))
        add_node(syntax_tree, self.ast_tree, '"{}"'.format(self._file_name))
        self.ast_tree.expandToDepth(1)
        
        # Fill highlight column for remainder of nodes
        for elem in to_be_updated:
            elem.setText(AstViewer.COL_HIGHLIGHT, "{} : {}".format(state['to'], "... : ..."))
            
        
 
    @QtCore.Slot(QtWidgets.QTreeWidgetItem, QtWidgets.QTreeWidgetItem)
    def highlight_node(self, current_item, _previous_item):
        """ Highlights the node if it has line:col information.
        """
        highlight_str = current_item.text(AstViewer.COL_HIGHLIGHT)
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


    def _readViewSettings(self, reset=False):
        """ Reads the persistent program settings

            :param reset: If True, the program resets to its default settings
        """
        pos = QtCore.QPoint(20, 20)
        window_size = QtCore.QSize(1024, 700)

        header = self.ast_tree.header()
        header_restored = False

        if reset:
            logger.debug("Resetting persistent view settings")
        else:
            logger.debug("Reading view settings")
            settings = get_qsettings()
            settings.beginGroup('view')
            pos = settings.value("main_window/pos", pos)
            window_size = settings.value("main_window/size", window_size)
            splitter_state = settings.value("central_splitter/state")
            if splitter_state:
                self.central_splitter.restoreState(splitter_state)
            header_restored = self.ast_tree.read_view_settings('tree/header_state', settings, reset)
            settings.endGroup()

        if not header_restored:

            header.resizeSection(AstViewer.COL_NODE, 250)
            header.resizeSection(AstViewer.COL_FIELD, 80)
            header.resizeSection(AstViewer.COL_CLASS, 80)
            header.resizeSection(AstViewer.COL_VALUE, 80)
            header.resizeSection(AstViewer.COL_POS, 80)
            header.resizeSection(AstViewer.COL_HIGHLIGHT, 100)

            for idx in range(len(AstViewer.HEADER_LABELS)):
                visible = False if idx == AstViewer.COL_HIGHLIGHT else True
                self.ast_tree.toggle_column_actions_group.actions()[idx].setChecked(visible)

        self.resize(window_size)
        self.move(pos)


    def _writeViewSettings(self):
        """ Writes the view settings to the persistent store
        """
        logger.debug("Writing view settings for window")

        settings = get_qsettings()
        settings.beginGroup('view')
        self.ast_tree.write_view_settings("tree/header_state", settings)
        settings.setValue("central_splitter/state", self.central_splitter.saveState())
        settings.setValue("main_window/pos", self.pos())
        settings.setValue("main_window/size", self.size())
        settings.endGroup()


    def my_test(self):
        """ Function for testing """
        pass


    def about(self):
        """ Shows the about message window. """
        QtWidgets.QMessageBox.about(self, "About %s" % PROGRAM_NAME, ABOUT_MESSAGE)


    def closeEvent(self, event):
        """ Called when the window is closed
        """
        logger.debug("closeEvent")
        self._writeViewSettings()
        self.close()
        event.accept()
        logger.debug("Closed {}".format(PROGRAM_NAME))


    def quit_application(self):
        """ Closes all windows """
        app = QtWidgets.QApplication.instance()
        app.closeAllWindows()
