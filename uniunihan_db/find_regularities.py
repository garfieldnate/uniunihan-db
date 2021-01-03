# import argparse
import csv
import json
import logging
import os
import re
from collections import OrderedDict, defaultdict
from pathlib import Path

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


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
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


def get_phonetic_regularities(char_to_readings, ids):
    # component -> pronunciation -> character
    regularities = defaultdict(lambda: defaultdict(set))
    # TODO: character -> candidate regularity components
    no_pron_chars = set()
    unknown_comps = set()
    for char, char_prons in char_to_readings.items():
        if not char_prons:
            no_pron_chars.add(char)
            continue
        for char_pron in char_prons:
            regularities[char][char_pron].add(char)
            #  TODO: be smarter about creating components if needed
            for component in ids[char]:
                if component in BLACKLIST:
                    continue
                regularities[component][char_pron].add(char)
                # if component not in unihan:
                #     unknown_comps.add(component)
                #     continue

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
    no_regularities = char_to_readings.keys() - no_pron_chars - chars_with_regularities

    return regularities, no_regularities, no_pron_chars, unknown_comps


def _format_json(data):
    return json.dumps(
        OrderedDict(sorted(data.items())), cls=SetEncoder, ensure_ascii=False, indent=2
    )


def main():
    # args = parser.parse_args()

    # unihan = _read_unihan()
    # TODO: allow choosing character set
    # _, char_set = _read_hsk(6)
    char_to_readings, joyo_radicals = _read_joyo()
    # char_set = _find_joyo(unihan)
    ids = _read_ids()
    for char, rad in joyo_radicals.items():
        ids[char] = ids[char] + rad

    (
        regularities,
        no_regularities,
        no_pron_chars,
        unknown_comps,
    ) = get_phonetic_regularities(char_to_readings, ids)
    log.info(f"Found {len(regularities)} candidate pattern components")
    log.info(
        f"Found {sum([len(prons) for prons in regularities.values()])} candidate pronunciation patterns"
    )
    log.info(f"{len(unknown_comps)} components not found in unihan: {unknown_comps}")
    log.info(f"{len(no_pron_chars)} characters with no pronunciations: {no_pron_chars}")
    log.info(
        f"{len(no_regularities)} characters with no regularities: {no_regularities}"
    )
    print(_format_json(regularities))

    # Next issues:
    # * look at Heisig for un-classified chars to determine next step
    # * try extracting component combos for better coverage?
    # * sprinkle in exceptions to get the numbers down
    # * hou and bou, kaku and gaku, etc. are similar and can be combined in "similar pronunciation" groups


if __name__ == "__main__":
    main()
