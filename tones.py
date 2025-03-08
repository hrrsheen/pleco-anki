import re
from typing import Union

TONE_MAP = {
    'a': ['ā', 'á', 'ǎ', 'à', 'a'], 
    'e': ['ē', 'é', 'ě', 'è', 'e'], 
    'i': ['ī', 'í', 'ǐ', 'ì', 'i'], 
    'o': ['ō', 'ó', 'ǒ', 'ò', 'o'], 
    'u': ['ū', 'ú', 'ǔ', 'ù', 'u'], 
    'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ', 'ü']
}

VOWELS = list(TONE_MAP.keys())

WORD_PATTERN = re.compile(r"([a-z]{2,})([1-5]{1})?")

def vowel_positions(pinyin: Union[str, list[chr]]) -> dict[chr, int]:
    present_vowels: dict[chr, int] = {}

    last_vowel: int = 0
    for i, c in enumerate(pinyin):
        if c in VOWELS:
            last_vowel = i
            present_vowels[c] = i
    present_vowels['l'] = last_vowel

    return present_vowels


def apply_tone(pinyin: str, tone: int) -> str:
    tone_index = tone - 1
    new_pinyin = list(pinyin.lower())
    vowels = vowel_positions(pinyin)

    # 'a' and 'e' take priprity. There will never be both an 'a' and 'e' in a word.
    if 'a' in vowels:
        new_pinyin[vowels['a']] = TONE_MAP['a'][tone_index]
        return ''.join(new_pinyin)
    elif 'e' in vowels:
        new_pinyin[vowels['e']] = TONE_MAP['e'][tone_index]
        return ''.join(new_pinyin)
        
    # In 'ou' or 'uo' combinations, the 'o' always take the tone.
    if 'o' in vowels and 'u' in vowels:
        o_pos = vowels['o']
        u_pos = vowels['u']
        space = o_pos - u_pos

        if space * space == 1:
            new_pinyin[o_pos] = TONE_MAP['o'][tone_index]
            return ''.join(new_pinyin)
    
    # Otherwise the last vowel gets the tone.
    test_vowel = new_pinyin[vowels['l']]
    new_pinyin[vowels['l']] = TONE_MAP[test_vowel][tone_index]
    return ''.join(new_pinyin)


def convert_numeric_word(pinyin: str) -> str:
    matches = WORD_PATTERN.findall(pinyin)

    corrected_pinyin: str = ""
    for numeric_pinyin in matches:
        tone = 5
        if numeric_pinyin[1] != "":
            tone = int(numeric_pinyin[1])
        corrected_pinyin += apply_tone(numeric_pinyin[0], tone)

    return corrected_pinyin

def convert_numeric_sentence(sentence: str) -> str:
    words: list[str] = sentence.split(" ")
    for i, word in enumerate(words):
        pinyin = convert_numeric_word(word)
        words[i] = pinyin

    return " ".join(words)