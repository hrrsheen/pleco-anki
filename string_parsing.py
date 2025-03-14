from unicodedata import category

def is_pua(c: chr) -> bool:
    return category(c) == "Co"

def contains_pua(s: str) -> bool:
    for c in s:
        if is_pua(c):
            return True
    
    return False