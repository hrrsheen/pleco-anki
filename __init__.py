from aqt import mw # import the main window object (mw) from aqt
from aqt.utils import showInfo, qconnect # import the "show info" tool from utils.py
from aqt.qt import * # import all of the Qt GUI library

def setup_menu() -> None:
    action = QAction("Import Pleco cards...", mw)

    # The function to be called when the menu item is activated    
    def on_import_action() -> None:
    #     w = Wizard()
    #     w.exec()
    #     mw.reset()
        print("Test")
        pass
    
    # action.triggered.connect(on_import_action)
    qconnect(action.triggered, on_import_action)
    mw.form.menuTools.addAction(action)

setup_menu()