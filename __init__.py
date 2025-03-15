from dataclasses import asdict, fields, Field
from functools import partial
from os.path import dirname
from pathlib import Path
from typing import Optional

from aqt import mw  # import the main window object (mw) from aqt
from aqt.operations import QueryOp
from aqt.qt import *  # import all of the Qt GUI library
from aqt.utils import qconnect  # import the "show info" tool from utils.py

from .card_convert import AnkiNotes, CardTemplate, Flashcard, NoteContent, parse_pleco_xml
from .ui.main_widget import Ui_Dialog

tr = partial(QCoreApplication.translate, "Dialog")

class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = Ui_Dialog()
        self.dialog.setupUi(self)
        self.connect_signals()

        # Holds the last directory that the user opened when browsing for the Pleco XML file.
        self.last_dir = str(Path.home())

        self.notes_custom: Optional[AnkiNotes] = None   # Note handler for custom user flashcards.
        self.notes_dict: Optional[AnkiNotes] = None     # Note handler for Pleco dictionary flashcards.

        # Populate the decks menu with options of decks to import to.
        decks = [deck.name for deck in mw.col.decks.all_names_and_ids()]
        self.dialog.select_deck.addItems(decks)
    
    def connect_signals(self):
        self.dialog.button_file.clicked.connect(self.select_file)       # Connect the file button to the file browser.
        self.dialog.button_import.clicked.connect(self.perform_import)  # Connect the import button to the import oprtation.
        self.dialog.button_cancel.clicked.connect(lambda: self.close()) # Close the plugin UI when "Cancel" is clicked.

    def select_file(self):
        tr = partial(QCoreApplication.translate, "Dialog")
        
        selected_xml, _ = QFileDialog.getOpenFileName(self, tr("Open the exported Pleco deck"), self.last_dir, "XML files (*.xml)")
        self.last_dir = dirname(selected_xml)
        if selected_xml:
            self.dialog.line_file.setText(selected_xml)
    
    def perform_import(self):
        pleco_file = self.dialog.line_file.text()
        deck_name = self.dialog.select_deck.currentText()

        # Set the import operation to run in the background.
        op = QueryOp(
            parent=mw,
            op=lambda _: self.import_pleco(pleco_file, deck_name),
            success=self.import_success,   
        )

        # Style the import button.
        self.dialog.button_import.setText(tr("Importing..."))
        self.dialog.button_import.setEnabled(False)
        # Run the import operation.
        op.with_progress().run_in_background()

    def import_pleco(self, xml_file: str, deck_name: str):
        print("Importing deck from: " + xml_file + " -> to deck: " + deck_name )
        flashcards = parse_pleco_xml(xml_file)
        
        # Open / create the selected deck.
        collection = mw.col
        deck_id = collection.decks.id_for_name(deck_name)
        if not deck_id:
            deck = collection.decks.new_deck()
            deck.name = deck_name
            collection.decks.add_deck(deck)
            deck_id = collection.decks.id_for_name(deck_name)

        # collection.decks.get(deck_id)["mid"]
        for card in flashcards:
            if card.dict_type:
                pass # TODO We'll come back to this.
            else:
                # Load the custom NoteType interface only if some actually exist in the import. 
                if self.notes_custom is None:
                    note_fields = [f.name for f in fields(card.content)]
                    self.notes_custom = AnkiNotes.init_from_filenames("CustomPleco", note_fields, [("./front.html", "./back.html")], "./card.css")

                new_note = self.notes_custom.create_note(deck_id, asdict(card.content))
        
        return 0

    def import_success(self, status: int):
        self.dialog.button_import.setText(tr("Import"))
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