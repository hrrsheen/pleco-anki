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

VOWELS = "aeiouü"

WORD_PATTERN = r"([a-zA-Z]{2,})([1-5]{1})?"


def apply_tone(pinyin: str, tone: int) -> str:
    tone_index = tone - 1
    new_pinyin: list[chr] = []          # Stores the chatacters to be used in the tonal pinyin.
    capitalisation: list[int] = []      # Stores the position of each capital character.
    vowels_present: dict[chr, int] = {} # Stores the position of each vowel in the word.

    last_vowel: int = 0
    for i, c in enumerate(pinyin):
        # Record the position of any capitalised letters.
        if c.isupper():
            capitalisation.append(i)
        # Record the position of each vowel
        if c in VOWELS:
            last_vowel = i
            vowels_present[c] = i
        new_pinyin.append(c.lower())

    # 'a' and 'e' take priority. There will never be both an 'a' and 'e' in a word.
    if 'a' in vowels_present:
        new_pinyin[vowels_present['a']] = TONE_MAP['a'][tone_index]
    elif 'e' in vowels_present:
        new_pinyin[vowels_present['e']] = TONE_MAP['e'][tone_index]
    # In 'ou' or 'uo' combinations, the 'o' always take the tone.
    elif 'o' in vowels_present and 'u' in vowels_present:
        o_pos = vowels_present['o']
        u_pos = vowels_present['u']
        space = o_pos - u_pos

        if space * space == 1:
            new_pinyin[o_pos] = TONE_MAP['o'][tone_index]
    # Otherwise the last vowel gets the tone.
    else:
        test_vowel = pinyin[last_vowel]
        new_pinyin[last_vowel] = TONE_MAP[test_vowel][tone_index]
        
    for i in capitalisation:
        new_pinyin[i] = new_pinyin[i].upper()
    return ''.join(new_pinyin)


def convert_numeric_word(pinyin: str) -> str:
    matches = re.findall(WORD_PATTERN, pinyin)

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