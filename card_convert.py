from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from xml.etree import ElementTree as ET

from anki import collection, models
from aqt import mw

from .card_templates import *
from .string_parsing import contains_pua
from .tones import convert_numeric_sentence

if TYPE_CHECKING:
    from anki.cards import Card, CardId
    from anki.decks import Deck, DeckId
    from anki.notes import Note, NoteId

NOTE_TYPE_NAME = "PlecoImports"

@dataclass
class NoteContent:
    headword_sc:    str
    pron:           str
    defn:           str
    notes:          Optional[str] = ""
    audio:          Optional[str] = ""
    reverse:        Optional[str] = ""

@dataclass
class Flashcard:
    content:        NoteContent
    dict_type:      Optional[bool] = False
    needs_check:    Optional[bool] = False

@dataclass
class CardTemplate:
    front_html:     str # The content of the HTML for the front of a card.
    back_html:      str # The content of the HTML for the back of a card.
    front_js:       Optional[str] = "" # Optional JS script to attach to the end of front_html.
    back_js:        Optional[str] = "" # Optional JS script to attach to the end of back_html.

    @property
    def front(self):
        if self.front_js:
            return self.front_html + f"<script type=\"text/javascript\">{self.front_js}</script>"
        return self.front_html
    
    @property
    def back(self):
        if self.back_js:
            return self.back_html + f"<script type=\"text/javascript\">{self.back_js}</script>"
        return self.back_html

class CardTemplates:
    """Consolidated multiple card templates (front and back HTML) along with the CSS for a NoteType.
    JavaScript can also optionally be added to the end of each HTML file."""

    def __init__(self, template_files: list[tuple[str, ...]], css_filename: str):
        """Loads the contents of given filenames into CardTemplate objects.
        
        :param template_files: List of tuples where each tuple contains the filenames (with path) used to create a card template.
                               These filenames are ordered as such:
                               1. The HTML file for the front of the card.
                               2. The HTML file for the back of the card.
                               3. (Optional) The JavaScript file to run with the front-side HTML.
                               4. (Optional) The JavaScript file to run with the back-side HTML.
        :param css_filename: The path to the CSS file for the Note Type that this object represents."""
        with open(css_filename, "r") as file:
            self.css = file.read()

        def grab_contents(filename: str) -> str:
            if filename == "":
                return ""
            with open(filename, "r") as f:
                return f.read()
        
        self.templates: list[CardTemplate] = []
        for card_type in  template_files:
            contents = (grab_contents(side) for side in card_type)
            self.templates.append(CardTemplate(*contents))
        

class AnkiNotes:
    """This class provides an abstraction for the creation and management of an Anki NoteType (aka Models), 
    as well as the creation of notes that use said NoteType.
    """

    def __init__(self, model_name: str, ordered_fields: list[str], templates: CardTemplates):
        """Defines the content of the NoteType. If the NoteType already exists, 
        its fields and templates are overwritten with those provided."""
        collection = mw.col
        self.fields = ordered_fields

        model_manager = collection.models
        # Create the Note Type (model) if it doesn't already exist.
        self.model = model_manager.by_name(model_name)
        new = False
        if self.model is None:
            self.model = model_manager.new(model_name)
            new = True
        
        # Add the listed fields to the Note Type.
        for f in ordered_fields:
            if f not in model_manager.field_names(self.model):
                field = model_manager.new_field(f)
                model_manager.add_field(self.model, field)

        if templates.css:
            self.model["css"] = templates.css

        # Overwrite / set the card templates for this note type.
        for i, template in enumerate(templates.templates):
            templ_name = model_name + " card " + str(i)
            templ = model_manager.new_template(templ_name)
            templ["qfmt"] = template.front
            templ["afmt"] = template.back
            if i < len(self.model["tmpls"]):
                self.model["tmpls"][i]["qfmt"] = templ["qfmt"]
                self.model["tmpls"][i]["afmt"] = templ["afmt"]
            else:
                model_manager.add_template(self.model, templ)

        if new:
            model_manager.add_dict(self.model)
        else:
            model_manager.update_dict(self.model)

    @property
    def id(self) -> models.NotetypeId:
        """Returns the ID of the NoteType that this model represents."""
        return self.model["id"]
    
    @property
    def name(self) -> str:
        """Returns the name of the NoteType that this model represents."""
        return self.model["name"]
    
    def create_note(self, deck_id: DeckId, card: dict[str, str], overwrite: bool=False) -> list[tuple[NoteId, bool]]:
        """Creates notes with the provided data and returns the ID of each note creates and whether it already existed in the deck.
        
        :param deck_id: The ID of the deck to which to add the note.
        :param card: A dictionary that maps field names to field values for the note.
        :param overwrite: If true, for instances in which the headword of a note already exists in the deck, 
                          overwrite its content. Ignore otherwise.

        :return A list of tuples. Each tuple represents one note created / modified and contains the note's ID 
                and whether its headword already existed in the deck.
        """
        collection = mw.col
        field_values = [card[f] for f in self.fields]

        dupe_ids = collection.find_notes(
            collection.build_search_string(f"{self.fields[0]}:{field_values[0]} AND note:{self.name} AND did:{deck_id}")
        )

        # If there's duplicates and they aren't being modified, no action needs to be taken.
        if dupe_ids and not overwrite:
            return []

        modified_ids: list[tuple[NoteId, bool]] = []
        # Update all duplicates with the newly given field values.
        if dupe_ids:
            notes: list[Note] = []
            for note_id in dupe_ids:
                note = collection.get_note(note_id)
                note.fields = field_values
                notes.append(note)
                modified_ids.append((note_id, True))
            collection.update_notes(notes)
        # Create a new note with the given field values.
        else:
            note = collection.new_note(self.model)
            note.fields = field_values
            collection.add_note(note, deck_id)

            modified_ids.append((note.id, True))

        return modified_ids
    

class AnkiDeck:
    """This class provides an abstraction for manipulating an Anki deck with the provided name."""

    def __init__(self, name):
        """Initialises the deck that this class interfaces with.
        if no deck matches the provided name, one will be created.
        """
        collection = mw.col

        deck_id = collection.decks.id_for_name(name)
        if not deck_id:
            deck = collection.decks.new_deck()
            deck.name = name
            collection.decks.add_deck(deck)
            deck_id = collection.decks.id_for_name(name)
        
        self._id = deck_id
    
    @property
    def id(self):
        """Returns the ID of the deck which this class represents."""
        return self._id
    
    def cards_for_note(self, note_id: NoteId) -> list[CardId]:
        """Returns a list of all cards that were generated for the note with the given ID."""
        collection = mw.col

        return collection.find_cards(
            collection.build_search_string(f"nid:{note_id} AND did:{self.id}")
        )

    def reset_cards(self, card_ids: list[CardId]):
        """Sets the scheduling information to "new" for each card whose ID is in the given list."""
        if len(card_ids) == 0:
            return
        
        collection = mw.col
        collection.sched.schedule_cards_as_new(card_ids)
    

def parse_pleco_xml(filename: str) -> list[Flashcard]:
    """Returns a list of Flashcard objects that contain the parsed and formatted data from a Pleco flashcard XML export."""
    flashcards: list[Flashcard] = []
    
    tree = ET.parse(filename)
    root = tree.getroot()

    for card in root.find("cards"):
        back_info: ET.Element = card.find("entry") # The Pleco spec for XML isn't set in stone, so it's best not to use child indices to find tags.
        headword = [(h.attrib.get("charset"), h.text) for h in back_info.findall("headword")]
        pron = back_info.find("pron").text
        defn = back_info.find("defn").text
        
        selected_headword = headword[0][1] #TODO select this based on either Simplified or Traditional.
        # Check if this is a dictionary card.
        dict_card = True if card.find("dictref") is not None else False
        if dict_card:
            flashcards.append(parse_dict_card(selected_headword, pron, defn))
        # Otherwise the card is a custom card.
        else:
            flashcards.append(parse_user_card(selected_headword, pron, defn))

    return flashcards
        

def parse_dict_card(headword: str, pron: str, defn: str) -> Flashcard:
    """Creates and returns a Flashcard object that contains the data of a dictionary-type Pleco flashcard."""
    definitions = defn.split("\n")
    return Flashcard(NoteContent(headword, convert_numeric_sentence(pron), definitions), True, contains_pua(defn))

def parse_user_card(headword: str, pron: str, defn: str) -> Flashcard:
    """Creates and returns a Flashcard object that contains the data of a custom Pleco flashcard."""
    return Flashcard(NoteContent(headword, convert_numeric_sentence(pron), defn))


def test_import():
    cards = parse_pleco_xml("./flash-fixed.xml")

if __name__ == "__main__":
    test_import()