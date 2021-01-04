# import argparse
import csv
import dataclasses
import json
import re
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
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
        "糹",
        "阝",
        "飠",
        "口",  # could technically be useful, but appears way too often so block for now
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


def _read_joyo():
    log.info("Loading joyo data...")
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
            chars[r["new"]] = readings
            radicals[r["new"]] = r["radical"]

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
            ids[r[1]] = breakdown
    return ids


@dataclass
class PureGroup:
    pron: str
    chars: Set[str]
    component: str
    # warnings: [str]


def _get_pure_groups(index):
    pure_groups = []
    pure_comps_to_pron = {}

    for component, pron_to_chars in index.regularities.items():
        if len(pron_to_chars) == 1:
            pron = next(iter(pron_to_chars.keys()))
            chars = pron_to_chars[pron]

            all_have_one_pron = True
            for char in chars:
                if len(index.char_to_prons[char]) != 1:
                    all_have_one_pron = False
                    break
            if all_have_one_pron:
                pure_comps_to_pron[component] = pron
                pure_groups.append(PureGroup(pron, chars, component))
    return sorted(pure_groups, key=lambda pg: (-len(pg.chars), pg.pron))


@dataclass
class Index:
    # char -> pronuncitions
    char_to_prons: Dict[str, List[str]]
    # component -> pronunciation -> chars with component and pronunciation
    comp_pron_char: DefaultDict[str, DefaultDict[str, List[str]]]
    # pronuncation -> all chars with that pronunciation
    pron_to_chars: Dict[str, List[str]]
    # same as comp_pron_char, but removes unique component/pronunciation mappings
    regularities: DefaultDict[str, DefaultDict[str, List[str]]]
    # unique pronunciations and their corresponding character
    unique_pron_to_char: Dict[str, str]
    # characters without any pronunciations
    no_pron_chars: List[str]
    # characters for which no regularities could be found (but do not have unique readings)
    no_regularity_chars: List[str]


def get_phonetic_regularities(char_to_prons, ids):
    # component -> pronunciation -> character
    comp_pron_char = defaultdict(lambda: defaultdict(set))
    pron_to_chars = defaultdict(set)
    # TODO: character -> candidate regularity components
    no_pron_chars = set()
    for char, char_prons in char_to_prons.items():
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

    # get the list of characters for which no regularities could be found;
    # exclude those with unique or no readings
    no_regularities = (
        char_to_prons.keys()
        - chars_with_regularities
        - no_pron_chars
        - set(unique_readings.values())
    )

    return Index(
        char_to_prons,
        comp_pron_char,
        pron_to_chars,
        regularities,
        unique_readings,
        no_pron_chars,
        no_regularities,
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
    for char, rad in joyo_radicals.items():
        ids[char] = ids[char] + rad

    index = get_phonetic_regularities(char_to_prons, ids)
    pure_group_candidates = _get_pure_groups(index)

    log.info(f"Found {len(index.regularities)} candidate pattern components")
    log.info(
        f"Found {sum([len(prons) for prons in index.regularities.values()])} candidate pronunciation patterns"
    )
    log.info(f"{len(index.no_pron_chars)} characters with no pronunciations")
    log.info(f"{len(index.no_regularity_chars)} characters with no regularities")
    log.info(f"{len(index.unique_pron_to_char)} characters with unique readings")
    log.info(f"{len(pure_group_candidates)} potential pure groups")

    with open(OUTPUT_DIR / "pure_group_candidates.json", "w") as f:
        f.write(_format_json(pure_group_candidates))
    with open(OUTPUT_DIR / "all_regularities.json", "w") as f:
        f.write(_format_json(OrderedDict(sorted(index.regularities.items()))))
    with open(OUTPUT_DIR / "no_regularities.json", "w") as f:
        f.write(_format_json(index.no_regularity_chars))
    with open(OUTPUT_DIR / "unique_readings.json", "w") as f:
        f.write(_format_json(index.unique_pron_to_char))
    with open(OUTPUT_DIR / "no_readings.json", "w") as f:
        f.write(_format_json(index.no_pron_chars))

    # Next: warn if char is itself a component and triggers different usages (will have to save one-offs!):

    #   {
    #     "pron": "シ",
    #     "chars": [
    #       "市",
    #       "師"
    #     ],
    #     "component": "巾"
    #   },
    # * following should be joined:
    #       {
    #     "pron": "ショウ",
    #     "chars": [
    #       "掌",
    #       "賞"
    #     ],
    #     "component": "𫩠"
    #   },
    #     {
    #     "pron": "ショウ",
    #     "chars": [
    #       "賞",
    #       "償"
    #     ],
    #     "component": "賞"
    #   },

    # issues:
    # *
    # * try extracting component combos for better coverage?
    # * sprinkle in exceptions to get the numbers down
    # * hou and bou, kaku and gaku, etc. are similar and can be combined in "similar pronunciation" groups
    #   "半": {
    #     "ハン": [
    #       "伴",
    #       "畔",
    #       "半",
    #       "判"
    #     ],
    #     "バン": [
    #       "伴",
    #       "判"
    #     ]
    #   },
    # * uses wrong IDS:


#   {
#     "pron": "セイ",
#     "chars": [
#       "政",
#       "整"
#     ],
#     "component": "攴"
#   },
# * wrong, probably because we're only taking single pronunciations for now
#       "牛": {
#     "セイ": [
#       "牲",
#       "制"
#     ]
#   },

# * Extract pure groups with multiple pronunciations
# * Extract semi-pure and mixed groups

# Other needs:
# create human-curated acceptance file


if __name__ == "__main__":
    main()
