from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree as ET

from anki import collection, decks, models, notes
from aqt import mw

from .string_parsing import contains_pua
from .tones import convert_numeric_sentence

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
        self.collection = mw.col
        self.fields = ordered_fields

        model_manager = self.collection.models
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

    @classmethod
    def init_from_filenames(cls, model_name: str, ordered_fields: list[str], templates: list[tuple[str, str]], css_filename: str=""):
        template_contents = [CardTemplate(front, back) for  front, back in templates]
        css = ""
        if css_filename:
            with open(css_filename, "r") as css_file:
                css = css_file.read()

        return cls(model_name, ordered_fields, template_contents, css)
    
    def create_note(self, deck_id: decks.DeckId, card: dict[str, str]) -> notes.Note:
        fields = [card[f] for f in self.fields]

        note = self.collection.new_note(self.model)
        note.fields = fields

        self.collection.add_note(note, deck_id)

        return note
    

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