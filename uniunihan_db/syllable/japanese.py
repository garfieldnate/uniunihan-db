import re
from dataclasses import dataclass
from enum import Enum
from typing import List


class Romanization(Enum):
    # *not* revised hepburn, so no macrons
    HEPBURN = 1


@dataclass
class Syllable:
    onset: str
    vowel: str
    coda: str

    def __post_init__(self):
        self.rhyme = self.vowel + self.coda
        self.is_glide = len(self.onset) > 1 and "y" in self.onset
        # TODO: provide morae count (1,2 or 3)


VOWELS = "aiueo"

CONSONANTS = "kgszjtdnhfbpmyrw"

DIGRAPHS = "ch|ts"

NON_DIPHTHONS = r"("

SPLITTER = f"(?i)(?<=[{VOWELS}])(?=[{CONSONANTS}])(?!n$|n[{CONSONANTS}])|(?<=n)(?=[{CONSONANTS}])|(?={DIGRAPHS})"


def split_syllables(word, romanization=Romanization.HEPBURN) -> List[str]:
    return list(filter(lambda x: len(x), re.split(SPLITTER, word)))


def parse_syllable(word, romanization=Romanization.HEPBURN) -> List[Syllable]:
    pass
