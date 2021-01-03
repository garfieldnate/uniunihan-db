# import argparse
import csv
import dataclasses
import json
import logging
import os
import re
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Set

# TODO: putting logging config in shared file
logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "INFO"),
    format="[%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).parents[1]

DATA_DIR = PROJECT_DIR / "data"
GENERATED_DATA_DIR = DATA_DIR / "generated"
INCLUDED_DATA_DIR = DATA_DIR / "included"

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
        "口",  # could technically be useful, but appears way to often so block for now
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


def _get_pure_groups(regularities, char_to_prons):
    # TODO next: extract pure groups (start with components with one pronunciation, take largest group of chars with one pronunciation)
    pure_groups = []
    pure_comps_to_pron = {}

    for component, pron_to_chars in regularities.items():
        if len(pron_to_chars) == 1:
            pron = next(iter(pron_to_chars.keys()))
            chars = pron_to_chars[pron]

            all_have_one_pron = True
            for char in chars:
                if len(char_to_prons[char]) != 1:
                    all_have_one_pron = False
                    break
            if all_have_one_pron:
                # print(
                #     f"Found pure group with {1} pronunciation! {component}/{pron}:{chars}"
                # )
                pure_comps_to_pron[component] = pron
                pure_groups.append(PureGroup(pron, chars, component))
    # for comp in sorted(pure_comps_to_pron.keys()
    #     pass
    return sorted(pure_groups, key=lambda pg: (-len(pg.chars), pg.pron))


def get_phonetic_regularities(char_to_prons, ids):
    # component -> pronunciation -> character
    regularities = defaultdict(lambda: defaultdict(set))
    pronunciation_to_chars = defaultdict(set)
    # TODO: character -> candidate regularity components
    no_pron_chars = set()
    for char, char_prons in char_to_prons.items():
        if not char_prons:
            no_pron_chars.add(char)
            continue
        for char_pron in char_prons:
            pronunciation_to_chars[char_pron].add(char)
            regularities[char][char_pron].add(char)
            #  TODO: be smarter about creating components if needed
            for component in ids[char]:
                if component in BLACKLIST:
                    continue
                regularities[component][char_pron].add(char)

    # delete the characters with only themselves in the value
    comps_to_delete = []
    for component, pron_to_chars in regularities.items():
        prons_to_delete = [k for k, v in pron_to_chars.items() if len(v) == 1]
        for k in prons_to_delete:
            # log.info(k)
            del pron_to_chars[k]
        if not len(pron_to_chars):
            comps_to_delete.append(component)
    for k in comps_to_delete:
        del regularities[k]

    # get the list of characters for which no regularities could be found
    chars_with_regularities = set()
    for pron_to_char in regularities.values():
        for chars in pron_to_char.values():
            chars_with_regularities |= chars
    no_regularities = char_to_prons.keys() - no_pron_chars - chars_with_regularities

    # get the characters which have a unique reading
    unique_readings = {}
    for pron, chars in pronunciation_to_chars.items():
        if len(chars) == 1:
            unique_readings[pron] = next(iter(chars))

    pure_groups = _get_pure_groups(regularities, char_to_prons)
    return regularities, no_regularities, no_pron_chars, unique_readings, pure_groups


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
    # char_set = _find_joyo(unihan)
    ids = _read_ids()
    for char, rad in joyo_radicals.items():
        ids[char] = ids[char] + rad

    (
        regularities,
        no_regularities,
        no_pron_chars,
        unique_readings,
        pure_groups,
    ) = get_phonetic_regularities(char_to_prons, ids)
    log.info(f"Found {len(regularities)} candidate pattern components")
    log.info(
        f"Found {sum([len(prons) for prons in regularities.values()])} candidate pronunciation patterns"
    )
    log.info(f"{len(no_pron_chars)} characters with no pronunciations: {no_pron_chars}")
    log.info(
        f"{len(no_regularities)} characters with no regularities: {no_regularities}"
    )
    log.info(
        f"{len(unique_readings)} characters with unique readings: {unique_readings}"
    )
    log.info(f"{len(pure_groups)} potential pure groups")
    print(_format_json(pure_groups))
    print(_format_json(OrderedDict(sorted(regularities.items()))))

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
# write to data directory with dedicated files (unique readings, no readings, etc.)
# create human-curated acceptance file


if __name__ == "__main__":
    main()
