from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Set


# Inspired by Heisig volume 2 (except for MIXED_D and SINGLETON)
class PurityType(IntEnum):
    # Only one pronunciation for the whole group
    PURE = 1
    # 2 Pronunciations, one of them contains only one character
    SEMI_PURE = 2
    # At least 4 chars, only 2 pronunciations
    MIXED_A = 3
    # At least 4 chars, only 3 pronunciations
    MIXED_B = 4
    # At least 4 chars, at least 1 shared pronunciation
    MIXED_C = 5
    # At least one shared pronunciation
    MIXED_D = 6
    # Multiple characters, no pattern found
    NO_PATTERN = 7
    # Only one character in the group
    SINGLETON = 8


@dataclass
class ComponentGroup:
    component: str
    pron_to_chars: Dict[str, Set[str]]

    def __post_init__(self):
        self.chars = set()
        for chars in self.pron_to_chars.values():
            self.chars.update(chars)

        num_prons = len(self.pron_to_chars)

        self.exceptions = {}
        for pron, chars in self.pron_to_chars.items():
            if len(chars) == 1:
                self.exceptions[pron] = next(iter(chars))

        self.purity_type = PurityType.NO_PATTERN

        if len(self.chars) == 1:
            self.purity_type = PurityType.SINGLETON
        elif num_prons == 1:
            self.purity_type = PurityType.PURE
        elif num_prons == 2 and len(self.exceptions) == 1:
            self.purity_type = PurityType.SEMI_PURE
        elif len(self.chars) >= 4:
            if num_prons == 2:
                self.purity_type = PurityType.MIXED_A
            elif num_prons == 3:
                self.purity_type = PurityType.MIXED_B
            elif len(self.exceptions) != num_prons:
                self.purity_type = PurityType.MIXED_C
        elif len(self.exceptions) != num_prons:
            self.purity_type = PurityType.MIXED_D
