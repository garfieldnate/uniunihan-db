# Parse Japanese sino-xenic vocabulary, which were imported from syllables in foreign languages
# into mono- or polymoraic morphemes.

import re
from enum import Enum

# from dataclasses import dataclass
# from typing import List


class Romanization(Enum):
    # *not* revised hepburn, so no macrons
    HEPBURN = 1
    # It's like nihonsiki, but without diacritics
    IME = 2


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
    "shi": "し",
    "chi": "ち",
    "tsu": "つ",
    "sha": "しゃ",
    "shu": "しゅ",
    "sho": "しょ",
    "cha": "ちゃ",
    "chu": "ちゅ",
    "cho": "ちょ",
}

HEPBURN_50 = {
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

HEPBURN_GLIDE = {
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

VOWELS = {
    "a": "あ",
    "i": "い",
    "u": "う",
    "e": "え",
    "o": "お",
}

# Lots of nihonsiki/IME are the same as hepburn
NIHONSIKI_TRIGRAPH = {**HEPBURN_GLIDE}
# override the parts that are different for nihonsiki
NIHONSIKI_TRIGRAPH.pop("ja")
NIHONSIKI_TRIGRAPH.pop("ju")
NIHONSIKI_TRIGRAPH.pop("jo")
NIHONSIKI_TRIGRAPH.update(
    {
        "zya": "じゃ",
        "zyu": "じゅ",
        "zyo": "じょ",
        "sya": "しゃ",
        "syu": "しゅ",
        "syo": "しょ",
        "tya": "ちゃ",
        "tyu": "ちゅ",
        "tyo": "ちょ",
    }
)

NIHONSIKI_COMPOUND = {**HEPBURN_50, **HEPBURN_GLIDE, **HEPBURN_SEMIVOWELS}
# override the parts that are different for nihonsiki
NIHONSIKI_COMPOUND.pop("fu")
NIHONSIKI_COMPOUND.pop("ji")
NIHONSIKI_COMPOUND.update(
    {
        "hu": "ふ",
        "zi": "じ",
        "si": "し",
        "ti": "ち",
        "tu": "つ",
    }
)


def to_kana(word: str, romanization: Romanization = Romanization.HEPBURN) -> str:
    """Convert romanized Japanese pronunciation into kana
    Currently only supports hiragana and Hepburn romanization used in Unihan database"""
    word = word.lower().strip()
    for k, v in HEPBURN_DIGRAPHS.items():
        word = word.replace(k, v)
    for k, v in HEPBURN_50.items():
        word = word.replace(k, v)
    for k, v in HEPBURN_GLIDE.items():
        word = word.replace(k, v)
    for k, v in HEPBURN_SEMIVOWELS.items():
        word = word.replace(k, v)
    for k, v in VOWELS.items():
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
    word = word.replace("p", "っ")
    word = word.replace("h", "っ")
    return word


def to_alpha(word: str, romanization=Romanization.IME) -> str:
    """Romanize kana input; currently only supports IME"""
    for k, v in NIHONSIKI_TRIGRAPH.items():
        word = word.replace(v, k)
    for k, v in NIHONSIKI_COMPOUND.items():
        word = word.replace(v, k)
    for k, v in VOWELS.items():
        word = word.replace(v, k)
    # Personally, I type "nn" in IME's, but "n'" is easier to read, so we'll go with that
    word = re.sub("ん(?=[aiueoy])", "n'", word)
    word = word.replace("ん", "n")
    # geminates
    word = word.replace("っk", "kk")
    word = word.replace("っs", "ss")
    word = word.replace("っt", "tt")
    word = word.replace("っp", "pp")
    word = word.replace("っh", "hh")
    return word


# def split_syllables(word, romanization=Romanization.HEPBURN) -> List[str]:
#     pass
#     # return list(filter(lambda x: len(x), re.split(SPLITTER, word)))


# def parse_syllable(word, romanization=Romanization.HEPBURN) -> List[Syllable]:
#     pass

# def hepburn_to_kana(word: str) -> str:
#     pass
