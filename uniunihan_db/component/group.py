import copy
from collections import defaultdict
from enum import IntEnum
from typing import Collection, Sequence, Tuple

from uniunihan_db.data.datasets import StringToStrings


# Inspired by Heisig volume 2 (except for MIXED_D and SINGLETON)
class PurityType(IntEnum):
    # Custom constructor to allow specifying documentation string;
    # See https://stackoverflow.com/a/50473952/474819 for discussion
    def __new__(cls, value, display=None, doc=None):
        self = int.__new__(cls, value)  # calling super().__new__(value) here would fail
        self._value_ = value
        if display is not None:
            self.display = display
        if doc is not None:
            self.__doc__ = doc
        return self

    # Only one pronunciation for the whole group
    PURE = (
        1,
        "pure",
        "These groups have only a single pronunciation shared by all characters in the group, making them the easiest to learn and remember.",
    )
    # 2 Pronunciations, one of them contains only one character
    SEMI_PURE = (
        2,
        "single-exception",
        "These groups contain only 1 exceptional character pronunciation.",
    )
    # At least 4 chars, only 2 pronunciations
    MIXED_A = (
        3,
        "mixed-A",
        "These groups have at least 4 characters and only 2 pronunciations.",
    )
    # At least 4 chars, only 3 pronunciations
    MIXED_B = (
        4,
        "mixed-B",
        "These groups have at least 4 characters and only 3 pronunciations.",
    )
    # At least 4 chars, at least 1 shared pronunciation
    MIXED_C = (
        5,
        "mixed-C",
        "These groups have at least 4 characters and share at least 1 pronunciation.",
    )
    # At least one shared pronunciation
    MIXED_D = (
        6,
        "mixed-D",
        "These groups have less than 4 characters and share at least 1 pronunciation.",
    )
    # Multiple characters, no pattern found
    NO_PATTERN = (
        7,
        "potpourri",
        "There are no shared pronunciations in these groups. However, the pronunciations are still related, since they have a common ancestor in ancient Chinese.",
    )
    # Only one character in the group
    SINGLETON = (
        8,
        "loner",
        "These groups each contain only one character. It is still good to know the phonetic component, since it may be of use in learning new characters not treated here, in the same or other languages.",
    )
    # No pronunciations are available to judge the group's purity
    NO_PRONUNCIATIONS = (
        9,
        "neologism",
        "The characters in these groups have no pronunciations based on ancient Chinese.",
    )


class ComponentGroup:
    def __init__(self, component: str, char_to_prons: StringToStrings):
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
                # If a group contains only 国字, then it won't have any Chinese readings;
                # otherwise, all characters should have them.
                raise ValueError(
                    f"Characters both with and without pronunciations were provided to group {self.component}; {self.pron_to_chars}"
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

    def get_ordered_clusters(self) -> Sequence[Sequence[str]]:
        """Returns a list of lists of characters (clusters) which share a pronunciation.
        The lists are sorted by their size and then by the pronunciation which they share.
        This ordering is meant to allow the learner to memorize pronunciations as rules
        with exceptions."""
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
