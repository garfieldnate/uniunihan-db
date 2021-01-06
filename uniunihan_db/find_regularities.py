# import argparse
import csv
import dataclasses
import json
import re
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from enum import IntEnum
from typing import DefaultDict, Dict, List, Set

from .util import GENERATED_DATA_DIR, INCLUDED_DATA_DIR, configure_logging

log = configure_logging(__name__)

OUTPUT_DIR = GENERATED_DATA_DIR / "regularities"
OUTPUT_DIR.mkdir(exist_ok=True)


IDC_REGEX = r"[\u2FF0-\u2FFB]"
UNENCODED_DC_REGEX = r"[①-⑳]"

# none of these are phonetic characters
BLACKLIST = set(
    [
        "一",
        "八",
        "辶",
        "艹",
        "扌",
        "宀",
        "亻",
        "人",
        "𠂉",
        "氵",
        "𭕄",
        "䒑",
        "丨",
        "丬",
        "丶",
        "丷",
        "丿",
        "亍",
        "亠",
        "冂",
        "冖",
        "彳",
        "忄",
        "日",
        "月",
        "木",  # except maybe 朴?
        "疒",
        "广",
        "糹",
        "阝",
        "阜",
        "飠",
        "食",
        "口",  # could technically be useful, but appears way too often so block for now
        "厶",
        "水",
        "手",
        "心",
        "言",
        "糸",
        "土",
        "辵",
        "艸",
        "肉",
        "貝",
        "女",
        "刀",
        "金",
        "十",
        "田",  # except maybe 電
        "力",
        "火",
        "刂",
        "犬",
        "大",
        "竹",
        "王",
        "攵",
        "衣",
        "寸",
        "頁",
        "示",
        "礻",
        "弓",
        "山",
        "尸",
        "囗",
        "禾",
        "石",
    ]
)

# parser = argparse.ArgumentParser()
# parser.add_argument(
#     "-l",
#     "--language",
#     # sanity check against Heisig Volume II
#     default="jp",
#     choices=['jp','zh-ZH','zh-HK'],
#     help="",
# )


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        elif dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)

        return json.JSONEncoder.default(self, obj)


def _read_joyo(use_old_glyphs=True):
    # Using the old forms of the characters can find more regularities
    log.info(f"Loading joyo ({'old' if use_old_glyphs else 'new'} glyph) data...")
    chars = {}
    radicals = {}
    with open(INCLUDED_DATA_DIR / "joyo.csv") as f:
        # filter comments
        rows = csv.DictReader(filter(lambda row: row[0] != "#", f))
        for r in rows:
            readings = r["on-yomi"].split("|")
            # remove empty readings;
            # forget about parenthesized readings; focus on the main reading for pattern finding
            readings = [yomi for yomi in readings if yomi and "（" not in yomi]
            char = r["old"] or r["new"]
            for c in char:
                chars[c] = readings
                radicals[c] = r["radical"]

    return chars, radicals


def _read_unihan():
    log.info("Loading unihan data...")
    # TODO: read path from constants file
    with open(GENERATED_DATA_DIR / "unihan.json") as f:
        unihan = json.load(f)
    return unihan


def _read_ids():
    log.info("Loading IDS data...")
    ids = {}
    with open(GENERATED_DATA_DIR / "cjkvi-ids-master" / "ids.txt") as f:
        rows = csv.reader(f, delimiter="\t")
        for r in rows:
            # comments
            if r[0].startswith("#"):
                continue
            # remove country specification and just use first one
            # TODO: allow specifying country?
            breakdown = r[2].split("[")[0]
            # remove IDC's
            # TODO: this could be useful information for prediction
            breakdown = re.sub(IDC_REGEX, "", breakdown)
            # remove unencoded DC's
            breakdown = re.sub(UNENCODED_DC_REGEX, "", breakdown)
            ids[r[1]] = set(breakdown)
    return ids


def _read_jp_netflix(max_words):
    log.info("Loading Netflix frequency list...")
    char_to_words = defaultdict(list)
    with open(INCLUDED_DATA_DIR / "jp_Netflix10K.txt") as f:
        num_words = 0
        for line in f.readlines():
            if not line.startswith("#"):
                line = line.strip()
                # TODO: organize by reading
                for c in line:
                    char_to_words[c].append(line)
                num_words += 1
                if num_words == max_words:
                    break
    return char_to_words


# Taken from Heisig volume 2
class PurityType(IntEnum):
    PURE = 1
    SEMI_PURE = 2
    MIXED_A = 3
    MIXED_B = 4
    MIXED_C = 5
    NO_PATTERN = 6


@dataclass
class ComponentGroup:
    component: str
    prons_to_chars: Dict[str, Set[str]]
    chars: List[str]
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.num_prons = len(self.prons_to_chars)

        self.exceptions = set()
        for chars in self.prons_to_chars.values():
            if len(chars) == 1:
                self.exceptions.add(next(iter(chars)))

        self.purity_type = PurityType.NO_PATTERN
        if len(self.chars) == len(self.exceptions):
            # T_T must have destroyed the group somehow
            pass
        elif self.num_prons == 1:
            self.purity_type = PurityType.PURE
        elif self.num_prons == 2 and len(self.exceptions) == 1:
            self.purity_type = PurityType.SEMI_PURE
        elif len(self.chars) >= 4:
            if self.num_prons == 2:
                self.purity_type = PurityType.MIXED_A
            elif self.num_prons == 3:
                self.purity_type = PurityType.MIXED_B
            else:
                self.purity_type = PurityType.MIXED_C

    def remove(self, char):
        self.chars.remove(char)
        to_delete = []
        for pron, chars in self.prons_to_chars.items():
            chars.discard(char)
            if not chars:
                to_delete.append(pron)
        for pron in to_delete:
            del self.prons_to_chars[pron]

        self.__post_init__()

        self.warn(f"Removed {char}")

    def warn(self, message):
        self.warnings.append(message)


def _get_component_group_candidates(index):
    candidate_groups = []
    for component, pron_to_chars in index.comp_pron_char.items():
        # skip combinations with no regularities
        if not any(len(chars) > 1 for chars in pron_to_chars.values()):
            continue

        all_chars = set()
        for chars in pron_to_chars.values():
            all_chars.update(chars)

        candidate_group = ComponentGroup(
            component,
            # sort pronunciations by number of characters
            OrderedDict(sorted(pron_to_chars.items(), key=lambda item: -len(item[1]))),
            all_chars,
        )
        candidate_groups.append(candidate_group)

    return candidate_groups


def _post_process_group_candidates(group_candidates):
    # char -> groups containing it
    char_to_groups = defaultdict(list)
    for group in group_candidates:
        for c in group.chars:
            char_to_groups[c].append(group)

    # When a char exists in several groups, we need to decide which group it should belong to.
    # Groups of groups:
    # If char is regular in some groups but not others, it should be removed from the irregular groups
    # "Regular" meaning another character shares one of its pronunciations
    # If component contains another group's component, they should be considered for combination
    # - rule would be complex, so just write a warning
    for char, groups in char_to_groups.items():
        # if char occurs in more than one candidate group
        if len(groups) > 1:

            # If char is itself a component of a candidate group, then it should only belong to that group
            if any(char == g.component for g in groups):
                removed = False
                for g in groups:
                    if char != g.component:
                        if len(g.chars) == 2:
                            g.warn(
                                f"Consider merging with {char} group (moving just {char} would destroy this group)"
                            )
                        else:
                            log.debug(
                                f"Removing {char} from {g.component}:{g.chars} because it's already a component"
                            )
                            g.remove(char)
                            removed = True
                # The char was removed from all but one group, so we can stop looking at groups for this char
                if removed:
                    continue

            # if char is regular in some groups
            if any(char not in g.exceptions for g in groups):
                # remove it from any groups where it is exceptional
                for g in groups:
                    if char in g.exceptions:
                        g.remove(char)
            else:
                group_string = ",".join([g.component for g in groups])
                for g in groups:
                    g.warn(
                        f"Character {char} is in multiple groups ({group_string}) but never irregular"
                    )

    # Organize and sort the groups for easier inspection
    purity_to_group = defaultdict(list)
    for gc in group_candidates:
        # purity_type is updated automatically by CandidateGroup, so we may have some groups that are no longer viable
        if gc.purity_type != PurityType.NO_PATTERN:
            purity_to_group[gc.purity_type].append(gc)
    for groups in purity_to_group.values():
        groups.sort(key=lambda g: (-len(g.chars)))

    return OrderedDict(sorted(purity_to_group.items(), key=lambda item: item[0]))


def _move_exceptions_to_vocab(candidate_groups, char_to_words):
    for groups in candidate_groups.values():
        for group in groups:
            for c in group.exceptions:
                if c in char_to_words:
                    group.warn(
                        f"Consider moving {c} to common vocab {char_to_words[c]}"
                    )
    # TODO: add vocab based on pronunciations
    return []


@dataclass
class Index:
    # char -> pronuncitions
    char_to_prons: Dict[str, List[str]]
    # component -> pronunciation -> chars with component and pronunciation
    comp_pron_char: DefaultDict[str, DefaultDict[str, List[str]]]
    # component -> chars containing it
    comp_to_char: DefaultDict[str, Set[str]]
    # char -> components it contains
    char_to_comp: Dict[str, str]
    # pronuncation -> all chars with that pronunciation
    pron_to_chars: Dict[str, Set[str]]
    # unique pronunciations and their corresponding character
    unique_pron_to_char: Dict[str, str]
    # characters without any pronunciations
    no_pron_chars: List[str]


def _index(char_to_prons, ids):
    # component -> pronunciation -> character
    comp_pron_char = defaultdict(lambda: defaultdict(set))
    pron_to_chars = defaultdict(set)
    comp_to_char = defaultdict(set)
    # TODO: character -> candidate regularity components
    no_pron_chars = set()
    for char, char_prons in char_to_prons.items():
        for component in ids[char]:
            comp_to_char[component].add(char)
        if not char_prons:
            no_pron_chars.add(char)
            continue
        for char_pron in char_prons:
            pron_to_chars[char_pron].add(char)
            comp_pron_char[char][char_pron].add(char)
            #  TODO: be smarter about creating components if needed
            for component in ids[char]:
                if component in BLACKLIST:
                    continue
                comp_pron_char[component][char_pron].add(char)

    # the list of characters for which regularities were found
    chars_with_regularities = set()
    # filter out unique comp -> pron mappings
    regularities = defaultdict(lambda: defaultdict(set))
    for comp, p2c in comp_pron_char.items():
        for pron, chars in p2c.items():
            if len(chars) > 1:
                regularities[comp][pron] = chars
                chars_with_regularities.update(chars)

    # get the characters which have a unique reading
    unique_readings = {}
    for pron, chars in pron_to_chars.items():
        if len(chars) == 1:
            unique_readings[pron] = next(iter(chars))

    # ensure that pronunciations are ordered deterministically in char_to_prons dictionary
    char_to_prons = {k: sorted(v) for k, v in char_to_prons.items()}

    return Index(
        char_to_prons,
        comp_pron_char,
        comp_to_char,
        ids,
        pron_to_chars,
        unique_readings,
        no_pron_chars,
    )


def _format_json(data):
    return json.dumps(
        data,
        cls=CustomJsonEncoder,
        ensure_ascii=False,
        indent=2,
    )


def main():
    # args = parser.parse_args()

    # unihan = _read_unihan()
    # TODO: allow choosing character set
    # _, char_set = _read_hsk(6)
    char_to_prons, joyo_radicals = _read_joyo()
    ids = _read_ids()
    high_freq = _read_jp_netflix(1000)
    # all_freq = _read_jp_netflix(10_000)
    # for char, rad in joyo_radicals.items():
    #     ids[char].add(rad)

    index = _index(char_to_prons, ids)
    group_candidates = _get_component_group_candidates(index)
    group_candidates = _post_process_group_candidates(group_candidates)
    _move_exceptions_to_vocab(group_candidates, high_freq)

    all_regular_chars = set()
    for groups in group_candidates.values():
        for g in groups:
            all_regular_chars.update(g.chars)
    no_regularity_chars = (
        char_to_prons.keys()
        - all_regular_chars
        - index.no_pron_chars
        - set(index.unique_pron_to_char.values())
    )

    exceptional_chars = set()
    for groups in group_candidates.values():
        for g in groups:
            exceptional_chars.update(g.exceptions)

    log.info(
        f"{sum([len(g) for g in group_candidates.values()])} total potential groups:"
    )
    for purity_type, groups in group_candidates.items():
        log.info(f"    {len(groups)} potential groups of type {purity_type}")
    log.info(f"{len(index.no_pron_chars)} characters with no pronunciations")
    log.info(f"{len(no_regularity_chars)} characters with no regularities")
    log.info(f"{len(exceptional_chars)} characters listed as exceptions")
    log.info(f"{len(index.unique_pron_to_char)} characters with unique readings")

    with open(OUTPUT_DIR / "group_candidates.json", "w") as f:
        f.write(_format_json(group_candidates))
    with open(OUTPUT_DIR / "no_regularities.json", "w") as f:
        f.write(_format_json(no_regularity_chars))
    with open(OUTPUT_DIR / "exceptions.json", "w") as f:
        f.write(_format_json(exceptional_chars))
    with open(OUTPUT_DIR / "unique_readings.json", "w") as f:
        f.write(_format_json(index.unique_pron_to_char))
    with open(OUTPUT_DIR / "no_readings.json", "w") as f:
        f.write(_format_json(index.no_pron_chars))

    # issues:
    # * try extracting component combos or component positions for better coverage?


# Other needs:
# create human-curated acceptance file


if __name__ == "__main__":
    main()
