# Parse Japanese sino-xenic vocabulary, which were imported from syllables in foreign languages
# into polymoraic morphemes.

# import re

# from dataclasses import dataclass
from enum import Enum

# from typing import List


class Romanization(Enum):
    # *not* revised hepburn, so no macrons
    HEPBURN = 1


# @dataclass
# class Syllable:
#     onset: str
#     vowel: str
#     coda: str

#     def __post_init__(self):
#         self.rhyme = self.vowel + self.coda
#         self.is_glide = len(self.onset) > 1 and "y" in self.onset
#         # TODO: provide morae count (1,2 or 3)


# VOWELS = "aiueo"

# CONSONANTS = "kgszjtdnhfbpmyrw"

# DIGRAPHS = "ch|ts"

# NON_DIPHTHONS = r"("

# SPLITTER = f"(?i)(?<=[{VOWELS}])(?=[{CONSONANTS}])(?!n$|n[{CONSONANTS}])|(?<=n)(?=[{CONSONANTS}])|(?={DIGRAPHS})"
# a
# i
# u
# e
# o
# ya
# yu
# yo
# '
# du and di?

HEPBURN_DIGRAPHS = {
    "chi": "ち",
    "tsu": "つ",
    "sha": "しゃ",
    "shu": "しゅ",
    "sho": "しょ",
    "cha": "ちゃ",
    "chu": "ちゅ",
    "cho": "ちょ",
}

HEPBURN_TO_KANA_50 = {
    "ka": "か",
    "ki": "き",
    "ku": "く",
    "ke": "け",
    "ko": "こ",
    "ga": "が",
    "gi": "ぎ",
    "gu": "ぐ",
    "ge": "げ",
    "go": "ご",
    "sa": "さ",
    "shi": "し",
    "su": "す",
    "se": "せ",
    "so": "そ",
    "za": "ざ",
    "ji": "じ",
    "zu": "ず",
    "ze": "ぜ",
    "zo": "ぞ",
    "ta": "た",
    "te": "て",
    "to": "と",
    "da": "だ",
    "de": "で",
    "do": "ど",
    "na": "な",
    "ni": "に",
    "nu": "ぬ",
    "ne": "ね",
    "no": "の",
    "ha": "は",
    "hi": "ひ",
    "fu": "ふ",
    "he": "へ",
    "ho": "ほ",
    "ba": "ば",
    "bi": "び",
    "bu": "ぶ",
    "be": "べ",
    "bo": "ぼ",
    "pa": "ぱ",
    "pi": "ぴ",
    "pu": "ぷ",
    "pe": "ぺ",
    "po": "ぽ",
    "ma": "ま",
    "mi": "み",
    "mu": "む",
    "me": "め",
    "mo": "も",
    "ra": "ら",
    "ri": "り",
    "ru": "る",
    "re": "れ",
    "ro": "ろ",
    "wa": "わ",
    "wo": "を",
}

HEPBURN_TO_KANA_GLIDE = {
    "kya": "きゃ",
    "kyu": "きゅ",
    "kyo": "きょ",
    "gya": "ぎゃ",
    "gyu": "ぎゅ",
    "ja": "じゃ",
    "ju": "じゅ",
    "jo": "じょ",
    "gyo": "ぎょ",
    "nya": "にゃ",
    "nyu": "にゅ",
    "nyo": "にょ",
    "hya": "ひゃ",
    "hyu": "ひゅ",
    "hyo": "ひょ",
    "bya": "びゃ",
    "byu": "びゅ",
    "byo": "びょ",
    "pya": "ぴゃ",
    "pyu": "ぴゅ",
    "pyo": "ぴょ",
    "mya": "みゃ",
    "myu": "みゅ",
    "myo": "みょ",
    "rya": "りゃ",
    "ryu": "りゅ",
    "ryo": "りょ",
}

HEPBURN_SEMIVOWELS = {
    "ya": "や",
    "yu": "ゆ",
    "yo": "よ",
}

HEPBURN_VOWELS = {
    "a": "あ",
    "i": "い",
    "u": "う",
    "e": "え",
    "o": "お",
}


def to_kana(word: str, romanization: Romanization = Romanization.HEPBURN) -> str:
    """Convert romanized Japanese pronunciation into kana
    Currently only supports hiragana and Hepburn romanization used in Unihan database"""
    word = word.lower().strip()
    for k, v in HEPBURN_DIGRAPHS.items():
        word = word.replace(k, v)
    for k, v in HEPBURN_TO_KANA_50.items():
        word = word.replace(k, v)
    for k, v in HEPBURN_TO_KANA_GLIDE.items():
        word = word.replace(k, v)
    for k, v in HEPBURN_SEMIVOWELS.items():
        word = word.replace(k, v)
    for k, v in HEPBURN_VOWELS.items():
        word = word.replace(k, v)
    # other final nasal orthography
    word = word.replace("n", "ん")
    word = word.replace("m", "ん")
    word = word.replace("'", "")
    word = word.replace("-", "")
    # geminates
    word = word.replace("k", "っ")
    word = word.replace("s", "っ")
    word = word.replace("t", "っ")
    word = word.replace("h", "っ")
    return word


# def split_syllables(word, romanization=Romanization.HEPBURN) -> List[str]:
#     pass
#     # return list(filter(lambda x: len(x), re.split(SPLITTER, word)))


# def parse_syllable(word, romanization=Romanization.HEPBURN) -> List[Syllable]:
#     pass

# def hepburn_to_kana(word: str) -> str:
#     pass
