from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from xml.etree import ElementTree as ET

from anki import collection, models
from aqt import mw

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
    defn:           list[str]

@dataclass
class Flashcard:
    content:        NoteContent
    dict_type:      Optional[bool] = False
    needs_check:    Optional[bool] = False

@dataclass
class CardTemplate:
    front_html:     str
    back_html:      str

    def __post_init__(self):
        with open(self.front_html, "r") as file:
            self.front_html = file.read()

        with open(self.back_html, "r") as file:
            self.back_html = file.read()

class AnkiNotes:
    """
    Manages the creation of Anki notes.
    """
    def __init__(self, model_name: str, ordered_fields: list[str], templates: list[CardTemplate], css: str=""):
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

        if css:
            self.model["css"] = css

        # Overwrite / set the card templates for this note type.
        for i, template in enumerate(templates):
            templ_name = model_name + " card " + str(i)
            templ = model_manager.new_template(templ_name)
            templ["qfmt"] = template.front_html
            templ["afmt"] = template.back_html
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
        return self.model["id"]
    
    @property
    def name(self) -> str:
        return self.model["name"]

    @classmethod
    def init_from_filenames(cls, model_name: str, ordered_fields: list[str], templates: list[tuple[str, str]], css_filename: str=""):
        template_contents = [CardTemplate(front, back) for  front, back in templates]
        css = ""
        if css_filename:
            with open(css_filename, "r") as css_file:
                css = css_file.read()

        return cls(model_name, ordered_fields, template_contents, css)
    
    def create_note(self, deck_id: DeckId, card: dict[str, str], overwrite=False) -> list[tuple[NoteId, bool]]:
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
    def __init__(self, name):
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
        return self._id
    
    def cards_for_note(self, note_id: NoteId) -> list[CardId]:
        collection = mw.col

        return collection.find_cards(
            collection.build_search_string(f"nid:{note_id} AND did:{self.id}")
        )

    def reset_cards(self, card_ids: list[CardId]):
        if len(card_ids) == 0:
            return
        
        collection = mw.col
        collection.sched.schedule_cards_as_new(card_ids)
    

def parse_pleco_xml(filename: str) -> list[Flashcard]:
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
    definitions = defn.split("\n")
    return Flashcard(NoteContent(headword, convert_numeric_sentence(pron), definitions), True, contains_pua(defn))

def parse_user_card(headword: str, pron: str, defn: str) -> Flashcard:
    return Flashcard(NoteContent(headword, convert_numeric_sentence(pron), defn))


def test_import():
    cards = parse_pleco_xml("./flash-fixed.xml")

if __name__ == "__main__":
    test_import()