import copy
from collections import defaultdict
from enum import IntEnum
from typing import Collection, Iterable, Mapping, Sequence, Tuple


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
    # No pronunciations are available to judge the group's purity
    NO_PRONUNCIATIONS = 9


class ComponentGroup:
    def __init__(self, component: str, char_to_prons: Mapping[str, Iterable[str]]):
        """component: phonetic component common to all characters in the group
        char_to_prons: dict[char -> [pronunciations]] for all characters in the group"""
        self.component = component

        self.chars = set()
        # reverse the char/pron mapping to determine pronunciation regularities
        self.pron_to_chars = defaultdict(list)
        for char, prons in char_to_prons.items():
            if not prons:
                prons = [""]
            self.chars.add(char)
            for p in prons:
                self.pron_to_chars[p].append(char)
        if not self.chars:
            raise ValueError(f"No characters were provided to group {self.component}")

        # sort chars so that iteration is deterministic
        for chars in self.pron_to_chars.values():
            chars.sort()

        num_prons = len(self.pron_to_chars)

        self.exceptions = {}
        for pron, chars in self.pron_to_chars.items():
            if len(chars) == 1:
                self.exceptions[pron] = chars[0]

        if "" in self.pron_to_chars:
            if len(self.pron_to_chars) != 1:
                # 国字 characters are the only ones without pronunciations, and they should never be assigned to a phonetic
                # component group with characters that actually have Chinese readings
                raise ValueError(
                    "Characters both with and without pronunciations were provided to group {self.component}"
                )
            self.purity_type = PurityType.NO_PRONUNCIATIONS
            return

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

    def get_char_presentation(self) -> Sequence[Sequence[str]]:
        """Returns a list of lists of characters which share a pronunciation.
        The lists are sorted by their size and then by the pronunciation which they share."""
        # sort by number of characters descending and then orthographically by pronunciation
        def sorter(item: Tuple[str, Collection[str]]) -> Tuple[int, str]:
            return (-len(item[1]), item[0])

        pron_to_chars = copy.deepcopy(self.pron_to_chars)
        presentation = []
        while pron_to_chars:
            # get next group of chars
            pron, added_chars = min(pron_to_chars.items(), key=sorter)
            presentation.append(added_chars)

            # delete them from the multimap
            del pron_to_chars[pron]
            to_delete = []
            for pron, chars in pron_to_chars.items():
                for c in added_chars:
                    try:
                        chars.remove(c)
                    except ValueError:
                        pass
                if not chars:
                    to_delete.append(pron)
            for pron in to_delete:
                del pron_to_chars[pron]

        return presentation
