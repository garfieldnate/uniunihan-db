from collections import defaultdict
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from typing import Collection, Mapping, MutableMapping, MutableSequence

from uniunihan_db.component.group import ComponentGroup, PurityType
from uniunihan_db.data.datasets import StringToStrings
from uniunihan_db.util import format_json


@dataclass(frozen=True)
class ComponentGroupIndex:
    groups: MutableSequence[ComponentGroup]
    # char -> pronunciaions
    char_to_prons: StringToStrings
    # unique pronunciations and their corresponding character
    unique_pron_to_char: Mapping[str, str]
    # characters assigned to a component group but missing a pronunciation
    missing_pron_chars: Collection[str]
    # characters with no pronunciation components
    no_comp_chars: Collection[str]

    def log_diagnostics(self, log: Logger, out_dir: Path):
        """Write a diagnostic summary to log and more details where necessary to
        files in out_dir."""
        purity_to_chars = defaultdict(set)
        purity_to_groups: MutableMapping[PurityType, int] = defaultdict(int)
        for g in self.groups:
            purity_to_chars[g.purity_type].update(g.chars)
            purity_to_groups[g.purity_type] += 1

        if self.no_comp_chars:
            log.warn(
                f"{len(self.no_comp_chars)} characters with no phonetic component: {self.no_comp_chars}"
            )
        if self.missing_pron_chars:
            log.warn(
                f"{len(self.missing_pron_chars)} characters with no pronunciations: {self.missing_pron_chars}"
            )
        log.info(f"{len(self.unique_pron_to_char)} characters with unique readings")

        log.info(f"{len(self.groups)} total groups:")
        for purity_type in PurityType:
            log.info(
                f"    {purity_to_groups[purity_type]} {purity_type.name} groups ({len(purity_to_chars[purity_type])} characters)"
            )

        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / "unique_readings.json", "w") as f:
            f.write(format_json(self.unique_pron_to_char))


def find_component_groups(
    char_to_prons: StringToStrings, comp_to_char: StringToStrings
) -> ComponentGroupIndex:
    """Group characters by component and classify the groups by their pronunciation
    regularity.
    char_to_prons: mapping from a character to a collection of pronunciations for the character
    comp_to_char: mapping from phonetic phonetic components to the characters which use the compooent phonetically
    """
    # loop through the provided dictionaries and create ComponentGroup objects
    groups = []
    chars_assigned_to_a_group = set()
    for component, chars in comp_to_char.items():
        # comp_to_char likely contains way more characters than we need
        chars = set(chars).intersection(char_to_prons.keys())
        if not chars:
            continue
        c2p = {c: char_to_prons[c] for c in chars}
        group = ComponentGroup(
            component,
            c2p,
        )
        groups.append(group)
        chars_assigned_to_a_group.update(chars)

    # index characters that do not fit into groups

    # find characters with no assigned group
    all_chars = set(char_to_prons.keys())
    chars_with_no_group = all_chars - chars_assigned_to_a_group

    # Find characters assigned to a group but without listed pronunciations
    missing_pron_chars = set()
    for char, prons in char_to_prons.items():
        if not prons:
            missing_pron_chars.add(char)
    missing_pron_chars -= chars_with_no_group

    # get unique character readings
    pron_to_chars = defaultdict(set)
    for char, prons in char_to_prons.items():
        for pron in prons:
            pron_to_chars[pron].add(char)
    unique_readings = {
        pron: next(iter(chars))
        for pron, chars in pron_to_chars.items()
        if len(chars) == 1
    }

    return ComponentGroupIndex(
        groups,
        char_to_prons,
        unique_readings,
        missing_pron_chars,
        chars_with_no_group,
    )
