from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree as ET

from .string_parsing import contains_pua
from .tones import convert_numeric_sentence


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
    cards = parse_pleco_xml("./flashUserDict.xml")

if __name__ == "__main__":
    test_import()