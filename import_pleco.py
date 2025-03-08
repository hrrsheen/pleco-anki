from tones import convert_numeric_sentence
from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree as ET

@dataclass
class FlashcardBack:
    pron: str
    defn: list[str]
    syntax: Optional[str] = None

def parse_file(filename: str) -> dict[str, FlashcardBack]:
    flashcards: dict[str, FlashcardBack] = {}
    
    tree = ET.parse(filename)
    root = tree.getroot()

    for card in root.find("cards"):
        back_info: ET.Element = card[0]
        headword = [(h.attrib.get("charset"), h.text) for h in back_info.findall("headword")]
        pron = back_info[len(headword)].text
        defn = back_info[len(headword) + 1].text
        
        # Check if this is a dictionary card
        dict_card = True if card[1].tag == "dictref" else False
        if dict_card:
            flashcards[headword[0][1]] = parse_dict_card(pron, defn) #TODO create a less hard-coded way of addressing headword elements
        else:
            flashcards[headword[0][1]] = parse_user_card(pron, defn)
        
        print(flashcards[headword[0][1]])


def parse_dict_card(pron: str, defn: str) -> FlashcardBack:
    return FlashcardBack(convert_numeric_sentence(pron), defn)

def parse_user_card(pron: str, defn: str) -> FlashcardBack:
    return FlashcardBack(convert_numeric_sentence(pron), defn)

if __name__ == "__main__":
    parse_file("./flash-fixed.xml")