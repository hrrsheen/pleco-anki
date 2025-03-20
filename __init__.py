from dataclasses import asdict, dataclass, fields
from functools import partial
from os.path import dirname, realpath
from pathlib import Path
from typing import Optional, Union

from aqt import mw  # import the main window object (mw) from aqt
from aqt.operations import QueryOp
from aqt.qt import *  # import all of the Qt GUI library
from aqt.utils import qconnect  # import the "show info" tool from utils.py

from .anki_manip import AnkiDeck, AnkiNotes, CardTemplates
from .pleco_import import parse_pleco_file
from .ui.import_ui import Ui_Dialog

TEMPLATE_DIR: str       = dirname(realpath(__file__)) + "/templates/" # The directory path to the template files.
NOTE_TEMPLATE_FILES     = (TEMPLATE_DIR + "front.html", TEMPLATE_DIR + "back.html")
REVERSE_TEMPLATE_FILES  = (TEMPLATE_DIR + "front_reverse.html", TEMPLATE_DIR + "back_reverse.html")

ID_YES = 1
ID_NO = 0

tr = partial(QCoreApplication.translate, "Dialog")

@dataclass
class ImportConfig:
    overwrite: bool
    set_new: bool
    reverse: Union[str, bool] = False

    def __post_init__(self):
        self.reverse = "y" if self.reverse else ""

class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = Ui_Dialog()
        self.dialog.setupUi(self)
        self.connect_signals()

        # Holds the last directory that the user opened when browsing for the Pleco XML file.
        self.last_dir = str(Path.home())

        self.dialog.group_reverse_buttons.setId(self.dialog.reverse_yes, ID_YES)
        self.dialog.group_reverse_buttons.setId(self.dialog.reverse_no, ID_NO)
        self.dialog.group_audio_buttons.setId(self.dialog.audio_yes, ID_YES)
        self.dialog.group_audio_buttons.setId(self.dialog.audio_no, ID_NO)

        # Populate the decks menu with options of decks to import to.
        decks = [deck.name for deck in mw.col.decks.all_names_and_ids()]
        self.dialog.select_deck.addItems(decks)
    
    def connect_signals(self):
        self.dialog.button_file.clicked.connect(self.select_file)       # Connect the file button to the file browser.
        self.dialog.button_import.clicked.connect(self.perform_import)  # Connect the import button to the import oprtation.
        self.dialog.button_cancel.clicked.connect(lambda: self.close()) # Close the plugin UI when "Cancel" is clicked.

    def select_file(self):
        tr = partial(QCoreApplication.translate, "Dialog")
        
        selected_file, _ = QFileDialog.getOpenFileName(self, 
                                                      tr("Open the exported Pleco deck"), 
                                                      self.last_dir, 
                                                      tr("Pleco export files (*.txt *.xml)"))
        self.last_dir = dirname(selected_file) # Update the last directory that the user looked in.
        if selected_file:
            self.dialog.line_file.setText(selected_file)
    
    def perform_import(self):
        pleco_file = self.dialog.line_file.text()
        deck_name = self.dialog.select_deck.currentText()
        config = ImportConfig(
            self.dialog.checkbox_overwrite.isChecked(),
            self.dialog.checkbox_new.isChecked(),
            self.dialog.group_reverse_buttons.checkedId() == ID_YES
        )

        # Set the import operation to run in the background.
        op = QueryOp(
            parent=mw,
            op=lambda _: import_pleco(pleco_file, deck_name, config),
            success=self.import_success,   
        )

        # Style the import button.
        self.dialog.button_import.setText(tr("Importing..."))
        self.dialog.button_import.setEnabled(False)
        # Run the import operation.
        op.with_progress().run_in_background()

    def import_success(self, status: int):
        self.dialog.button_import.setText(tr("Import"))
        self.dialog.button_import.setEnabled(True)

def import_pleco(xml_file: str, deck_name: str, config: ImportConfig):
    print("Importing deck from: " + xml_file + " -> to deck: " + deck_name )
    notes_custom: Optional[AnkiNotes] = None   # Note handler for custom user flashcards.
    notes_dict: Optional[AnkiNotes] = None     # Note handler for Pleco dictionary flashcards.

    # Read the Pleco XML file and store the data in Flashcard objects.
    flashcards = parse_pleco_file(xml_file)
    
    # Open / create the selected deck.
    deck = AnkiDeck(deck_name)
    # Process all flashcards.
    for card in flashcards:
        # Generate a reverse card if the config specifies.
        if config.reverse:
            card.content.reverse = "y"

        if card.dict_type:
            pass # TODO We'll come back to this.
        else:
            # Load the custom NoteType interface only if some actually exist in the import. 
            if notes_custom is None:
                note_fields = [f.name for f in fields(card.content)] # Generate the ordered field names.
                notes_custom = AnkiNotes("CustomPleco", note_fields, CardTemplates([NOTE_TEMPLATE_FILES, REVERSE_TEMPLATE_FILES], TEMPLATE_DIR + "card.css"))

            # Create a note for the current flashcard and add it to the deck.
            modified_notes = notes_custom.create_note(deck.id, asdict(card.content), config.overwrite)
            if config.set_new:
                # Reset the scheduling of any duplicate cards.
                deck.reset_cards([card_id 
                                    for note_id, dupe in modified_notes if dupe 
                                    for card_id in deck.cards_for_note(note_id)])
    
    return 0 #TODO Is this needed?


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