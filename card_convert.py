from .string_parsing import contains_pua
from .tones import convert_numeric_sentence
from aqt import mw
from anki import collection
from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree as ET

NOTE_TYPE_NAME = "PlecoImports"

@dataclass
class Definition:
    defn: str
    syntax: Optional[str] = ""

@dataclass
class FlashcardBack:
    pron: str
    defn: list[Definition]
    needs_check: Optional[bool] = False

@dataclass
class CardTemplate:
    front_html: str
    back_html: str

    def __post_init__(self):
        with open(self.front_html, "r") as file:
            self.front_html = file.read()

        with open(self.back_html, "r") as file:
            self.back_html = file.read()


def parse_pleco_xml(filename: str) -> dict[str, FlashcardBack]:
    flashcards: dict[str, FlashcardBack] = {}
    
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
            flashcards[selected_headword] = parse_dict_card(pron, defn)
        # Otherwise the card is a custom card.
        else:
            flashcards[selected_headword] = parse_user_card(pron, defn)
            # print(flashcards[selected_headword])
            # print("----------------------------------------------------------------------------------")

    return flashcards
        

def parse_dict_card(pron: str, defn: str) -> FlashcardBack:
    definitions = defn.split("\n")
    return FlashcardBack(convert_numeric_sentence(pron), definitions, contains_pua(defn))

def parse_user_card(pron: str, defn: str) -> FlashcardBack:
    return FlashcardBack(convert_numeric_sentence(pron), defn)

class AnkiNotes:
    """
    Manages the creation of Anki notes.
    """

    def __init__(self, model_name: str, ordered_fields: list[str], templates: list[CardTemplate], css: str=""):
        self.collection = mw.col

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


def test_import():
    custom_templ = CardTemplate("./front.html", "./back.html")
    with open("./card.css", "r") as css_file:
        css = css_file.read()
    custom_notes = AnkiNotes("CustomPleco", ["headword_sc", "pron", "defn"], [custom_templ], css)
    cards = parse_pleco_xml("./flash-fixed.xml")

if __name__ == "__main__":
    test_import()