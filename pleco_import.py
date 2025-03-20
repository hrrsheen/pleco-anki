import re
from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree as ET

if __name__ == "__main__":
    from string_parsing import contains_pua, is_pua
    from tones import convert_numeric_sentence
else:
    from .string_parsing import contains_pua, is_pua
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


def parse_pleco_txt(filename: str) -> list[Flashcard]:
    """Returns a list of Flashcard objects that contain the parsed and formatted data from a Pleco flashcard .txt file export."""
    flashcards: list[Flashcard] = []

    # https://regex101.com/r/oRAWLT/1
    card_re = r"((?:[\u4E00-\u9FFF。，])+)\t((?:[a-zA-Zü'。，.,]+[1-5]?[ (?:\/\/)。]*)+)\t(.+)"
    with open(filename, "r") as f:
        flashcard_all = f.read()
    cards = re.findall(card_re, flashcard_all)

    card: tuple[str, str, str]
    for card in cards:
        headword, pron, defn = card
        if len(re.split("[ 。，..]", pron)) == 1:
            # Dict-type cards only contain a single word in their pronunciation.
            # Parse the definition.
            pass
        else:
            flashcards.append(Flashcard(NoteContent(headword, convert_numeric_sentence(pron), defn)))

    return flashcards
        
        

def parse_dict_card(headword: str, pron: str, defn: str) -> Flashcard:
    """Creates and returns a Flashcard object that contains the data of a dictionary-type Pleco flashcard."""
    definitions: list[chr] = []
    pua_present = False
    for c in defn:
        definitions.append(c)
        if not is_pua(c):
            pass
        else:
            pua_present = True
    return Flashcard(NoteContent(headword, convert_numeric_sentence(pron), "".join(definitions)), True, pua_present)

def parse_user_card(headword: str, pron: str, defn: str) -> Flashcard:
    """Creates and returns a Flashcard object that contains the data of a custom Pleco flashcard."""
    return Flashcard(NoteContent(headword, convert_numeric_sentence(pron), defn))

def test_import():
    cards = parse_pleco_txt("./flash 4.txt")
    for c in cards:
        print(c)

if __name__ == "__main__":
    test_import()