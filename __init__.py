from aqt import mw # import the main window object (mw) from aqt
from aqt.operations import QueryOp
from aqt.utils import showInfo, qconnect # import the "show info" tool from utils.py
from aqt.qt import * # import all of the Qt GUI library
from functools import partial
from os.path import dirname
from pathlib import Path
from .card_convert import test_import, parse_pleco_xml, FlashcardBack
from .ui.main_widget import Ui_Dialog

class ImportDialog(QDialog):
    tr = partial(QCoreApplication.translate, "Dialog")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = Ui_Dialog()
        self.dialog.setupUi(self)
        self.connect_signals()

        self.last_dir = str(Path.home())
    
    def connect_signals(self):
        self.dialog.button_file.clicked.connect(self.select_file)
        self.dialog.button_import.clicked.connect(self.perform_import)

    def select_file(self):
        tr = partial(QCoreApplication.translate, "Dialog")
        
        selected_xml, _ = QFileDialog.getOpenFileName(self, self.tr("Open the exported Pleco deck"), self.last_dir, "XML files (*.xml)")
        self.last_dir = dirname(selected_xml)
        if selected_xml:
            self.dialog.line_file.setText(selected_xml)
    
    def perform_import(self):
        pleco_file = self.dialog.line_file.text()
        op = QueryOp(
            parent=mw,
            op=lambda _: parse_pleco_xml(pleco_file),
            success=self.import_success,   
        )
        op.failure(self.import_failure)
        self.dialog.button_import.setText(self.tr("Importing..."))
        self.dialog.button_import.setEnabled(False)
        op.with_progress().run_in_background()

    def import_success(self, flashcards: dict[FlashcardBack]):
        self.dialog.button_import.setText(self.tr("Import"))
        self.dialog.button_import.setEnabled(True)

    def import_failure(self, error: Exception):
        print(type(error))
        print(error)
        self.dialog.button_import.setText(self.tr("Import"))
        self.dialog.button_import.setEnabled(True)


def setup_menu() -> None:
    action = QAction("Import Pleco cards...", mw)

    # The function to be called when the menu item is activated    
    def on_import_action() -> None:
        import_dialog = ImportDialog()
        import_dialog.exec()
        mw.reset()
        # test_import()
    
    # action.triggered.connect(on_import_action)
    qconnect(action.triggered, on_import_action)
    mw.form.menuTools.addAction(action)

setup_menu()