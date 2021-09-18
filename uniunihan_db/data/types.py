from dataclasses import dataclass
from typing import Collection, Mapping, MutableMapping, MutableSequence, Optional


@dataclass
class Word:
    # the dictionary form of the word using Chinese characters and perhaps other orthographies
    surface: str
    # Unique identifier
    id: str
    # the commonly used phonetic spelling (whatever would go in ruby text, or in place of
    # Chinese characters when one forgets or wishes to write without them)
    pron: str
    # definition in English
    english: str
    # TODO: generalize to sort key of parameterized type
    # unnormalized frequency within some corpus; -1 to indicate missing data
    frequency: int


@dataclass
class ZhWord(Word):
    # the surface field contains the traditional form; if the simplified form is different, it will be
    # stored here
    simplified: Optional[str]


# character -> {pronunciation-> [words that use that character with that pronunciation]}
Char2Pron2Words = MutableMapping[str, MutableMapping[str, MutableSequence[Word]]]

StringToStrings = Mapping[str, Collection[str]]
