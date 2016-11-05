"""
   Program that shows source code on the right and its abstract syntax tree (ast) on the left.
"""
from __future__ import print_function
                
import sys, logging, ast, traceback

from astviewer.misc import get_qapplication_instance, get_qsettings, ABOUT_MESSAGE
from astviewer.editor import SourceEditor
from astviewer.qtpy import QtCore, QtWidgets
from astviewer.version import PROGRAM_NAME, DEBUGGING

from astviewer.tree import SyntaxTreeWidget


logger = logging.getLogger(__name__)


def view(*args, **kwargs):
    """ Opens an AstViewer window
    """
    app = get_qapplication_instance()
    
    window = AstViewer(*args, **kwargs)
    window.show()

    if 'darwin' in sys.platform:
        window.raise_()
        
    logger.info("Starting {} the event loop.".format(PROGRAM_NAME))
    exit_code = app.exec_()
    logger.info("{} viewer done...".format(PROGRAM_NAME))
    return exit_code



# The main window inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201, R0913


class AstViewer(QtWidgets.QMainWindow):
    """ The main application.
    """

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
            
            If reset is True, the persistent settings (e.g. window size) are
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
        self._setup_views()
        self._setup_menu()
        self.setWindowTitle('{}'.format(PROGRAM_NAME))
        
        # Update views
        if file_name and source_code:
            logger.warning("Both the file_name and source_code are defined: source_code ignored.")

        if file_name:
            self._load_file(file_name)

        self._update_widgets()

        # Read persistent settings
        self._readViewSettings(reset)
        self._settingsSaved = False


    def _setup_menu(self):
        """ Sets up the main menu.
        """
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("&Open File...", self.open_file, "Ctrl+O")
        file_menu.addAction("&Close File", self.close_file)
        file_menu.addAction("E&xit", self.quit_application, "Ctrl+Q")
        
        if DEBUGGING is True:
            file_menu.addSeparator()
            file_menu.addAction("&Test", self.my_test, "Ctrl+T")
        
        self.view_menu = self.menuBar().addMenu("&View")
        self.view_menu.addAction(self.editorDock.toggleViewAction())

        self.header_menu = self.view_menu.addMenu("&Tree Columns")

        # Add toggling of tree columns to the View menu
        for action in self.ast_tree.get_header_context_menu_actions():
            self.header_menu.addAction(action)

        self.expand_menu = self.view_menu.addMenu("&Expand")
        self.expand_menu.addAction('Reset', self.ast_tree.expand_reset, "Ctrl+=")
        self.expand_menu.addAction('Collapse all', self.ast_tree.collapseAll, "Ctrl+-")
        self.expand_menu.addAction('Expand all', self.ast_tree.expandAll, "Ctrl++")

        self.menuBar().addSeparator()
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction('&About...', self.about)


    def _setup_views(self):
        """ Creates the UI widgets. 
        """
        self.file_dialog = QtWidgets.QFileDialog(parent=self, caption="Open File")
        self.file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        self.file_dialog.setNameFilter("Python Files (*.py);;All Files (*)")

        self.ast_tree = SyntaxTreeWidget()
        self.setCentralWidget(self.ast_tree)

        self.editor = SourceEditor()
        self.editorDock = QtWidgets.QDockWidget("Source code", self)
        self.editorDock.setObjectName("editor_dock") # needed for saveState
        self.editorDock.setWidget(self.editor)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.editorDock)

        # Connect signals
        self.ast_tree.currentItemChanged.connect(self.highlight_node)
        self.editor.sigTextClicked.connect(self.ast_tree.select_node)


    def finalize(self):
        """ Cleanup resources.
        """
        logger.debug("Cleaning up resources.")

        self.ast_tree.currentItemChanged.disconnect(self.highlight_node)


    def close_file(self):
        """ Clears the widgets
        """
        self._file_name = ""
        self._source_code = ""
        self.editor.clear()
        self.ast_tree.clear()
        self.setWindowTitle('{}'.format(PROGRAM_NAME))

    
    def open_file(self, file_name=None):
        """ Opens a Python file. Show the open file dialog if file_name is None.
        """
        if not file_name:
            file_name = self._get_file_name_from_dialog()

            if not file_name:
                logger.debug("Open file canceled.")
                return # user pressed cancel

        self.close_file() # Close any old file.
        self._load_file(file_name)

        self._update_widgets()


    def _get_file_name_from_dialog(self):
        """ Opens a file dialog and returns the file name selected by the user
        """
        logger.debug("_get_file_name_from_dialog, directory: {}"
                     .format(self.file_dialog.directory().path()))

        self.file_dialog.exec_()
        files = self.file_dialog.selectedFiles()

        if len(files) == 0:
            return None
        elif len(files) == 1:
            return files[0]
        else:
            assert False, "Bug: more than one file selected."

    
    def _update_widgets(self):
        """ Updates the tree and editor widgets.
        """            
        self.setWindowTitle('{} - {}'.format(self._file_name, PROGRAM_NAME))
        self.editor.setPlainText(self._source_code)

        if not self._source_code:
            logger.debug("Empty source code, use empty tree.")
            self.ast_tree.clear()
            return

        try:
            syntax_tree = ast.parse(self._source_code, filename=self._file_name, mode=self._mode)
            ast.fix_missing_locations(syntax_tree) # Doesn't seem to do anything.
        except Exception as ex:
            if DEBUGGING:
                raise
            else:
                stack_trace = traceback.format_exc()
                msg = "Unable to parse file: {}\n\n{}\n\n{}" \
                    .format(self._file_name, ex, stack_trace)
                logger.exception(ex)
                QtWidgets.QMessageBox.warning(self, 'error', msg)
        else:
            last_pos = self.editor.get_last_pos()
            root_item = self.ast_tree.populate(syntax_tree, last_pos, root_label=self._file_name)
            self.ast_tree.setCurrentItem(root_item)
            self.ast_tree.expand_reset()

                
    def _load_file(self, file_name):
        """ Opens a file and sets self._file_name and self._source code if successful
        """
        logger.debug("Opening {!r}".format(file_name))
        
        in_file = QtCore.QFile(file_name)
        if in_file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
            text = in_file.readAll()
            try:
                source_code = str(text, encoding='utf-8')  # Python 3
            except TypeError:
                source_code = str(text)                    # Python 2
                
            self._file_name = file_name
            self._source_code = source_code
        else:
            msg = "Unable to open file: {}".format(file_name)
            logger.warning(msg)
            QtWidgets.QMessageBox.warning(self, 'error', msg)


    @QtCore.Slot(QtWidgets.QTreeWidgetItem, QtWidgets.QTreeWidgetItem)
    def highlight_node(self, current_item, _previous_item):
        """ Highlights the node if it has line:col information.
        """
        from_pos = to_pos = (0, 0) # unselect

        if current_item:
            try:
                from_pos, to_pos = self.ast_tree.get_item_span(current_item)
            except:
                logger.warning("No span founc for item. Unselecting text.")

        if from_pos is None or to_pos is None:
            pass # unselecting text
        else:
            self.editor.select_text(from_pos, to_pos)


    def _readViewSettings(self, reset):
        """ Reads the persistent program settings.

            :param reset: If True, the program resets to its default settings
        """
        header = self.ast_tree.header()
        header_restored = False

        if reset:
            logger.debug("Resetting persistent view settings")
        else:
            logger.debug("Reading view settings")
            settings = get_qsettings()
            settings.beginGroup('view')

            dialog_state = settings.value("file_dialog/state")
            if dialog_state:
                dialog_restored = self.file_dialog.restoreState(dialog_state)
                if not dialog_restored:
                    logger.warning("Unable to restore open-file dialog settings.")

            # restoreState doesn't seem to restore the directory so do it ourselves.
            self.file_dialog.setDirectory(settings.value("file_dialog/dir"))

            win_geom = settings.value("geometry")
            if win_geom:
                self.restoreGeometry(win_geom)
            else:
                # Can happen in new version
                logger.warning("Unable to restore main window geometry.")

            win_state = settings.value("state")
            if win_state:
                self.restoreState(win_state)
            else:
                # Can happen in new version
                logger.warning("Unable to restore main window state.")

            header_restored = self.ast_tree.read_view_settings('tree/header_state', settings, reset)
            settings.endGroup()

        if not header_restored:
            header.resizeSection(SyntaxTreeWidget.COL_NODE, 250)
            header.resizeSection(SyntaxTreeWidget.COL_FIELD, 80)
            header.resizeSection(SyntaxTreeWidget.COL_CLASS, 80)
            header.resizeSection(SyntaxTreeWidget.COL_VALUE, 80)
            header.resizeSection(SyntaxTreeWidget.COL_POS, 80)
            header.resizeSection(SyntaxTreeWidget.COL_HIGHLIGHT, 100)

            for idx in range(len(SyntaxTreeWidget.HEADER_LABELS)):
                visible = False if idx == SyntaxTreeWidget.COL_HIGHLIGHT else True
                self.ast_tree.toggle_column_actions_group.actions()[idx].setChecked(visible)


    def _writeViewSettings(self):
        """ Writes the view settings to the persistent store
        """
        if self._settingsSaved:
            logger.debug("Settings have been saved before. Returning to caller.")
            return

        try:
            logger.debug("Writing view settings for window")

            settings = get_qsettings()
            settings.beginGroup('view')
            self.ast_tree.write_view_settings("tree/header_state", settings)
            settings.setValue("file_dialog/state", self.file_dialog.saveState())
            settings.setValue("file_dialog/dir", self.file_dialog.directory().path())

            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("state", self.saveState())
            settings.endGroup()
        finally:
            self._settingsSaved = True


    def my_test(self):
        """ Function for testing.
        """
        logger.debug("Test function called.")
        #logger.info("Last character: {}".format(self.editor.get_last_pos()))



    def about(self):
        """ Shows the about message window.
        """
        QtWidgets.QMessageBox.about(self, "About %s" % PROGRAM_NAME, ABOUT_MESSAGE)


    def closeEvent(self, event):
        """ Called when the window is closed.
        """
        logger.debug("closeEvent")
        self._writeViewSettings()
        self.finalize()
        self.close()
        event.accept()
        logger.debug("Closed {}".format(PROGRAM_NAME))


    def quit_application(self):
        """ Closes all windows.
        """
        logger.debug("quit_application")
        # Save the settings before closing any windows. Otherwise it may close the dock window
        # and then save the state. In _writeViewSettings it is checked if the settings have
        # already been saved.
        self._writeViewSettings()
        app = QtWidgets.QApplication.instance()
        app.closeAllWindows()
        logger.debug("quit_application done")

