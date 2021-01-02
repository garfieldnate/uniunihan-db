# import argparse
import csv
import json
import logging
import os
import re
from collections import OrderedDict, defaultdict
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

IDC_REGEX = r"[\u2FF0-\u2FFB]"
UNENCODED_DC_REGEX = r"[①-⑳]"


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


def _read_unihan():
    log.info("Loading unihan data...")
    # TODO: read path from constants file
    with open(DATA_DIR / "unihan.json") as f:
        unihan = json.load(f)
    return unihan


def _find_joyo(unihan):
    log.info("Extracting Joyo Kanji from Unihan database...")
    chars = set()
    for char, entry in unihan.items():
        if "kJoyoKanji" in entry:
            joyo = entry["kJoyoKanji"][0]
            # Don't include variants
            if not joyo.startswith("U"):
                chars.add(char)

    return chars


def _read_ids():
    log.info("Loading IDS data...")
    ids = {}
    with open(DATA_DIR / "cjkvi-ids-master" / "ids.txt") as f:
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


def get_phonetic_regularities(char_set: Set[str], ids, unihan):
    pron_field = "kJapaneseOn"
    regularities = defaultdict(set)
    no_pron_chars = set()
    unknown_comps = set()
    no_pron_comps = set()
    for char in char_set:
        char_prons = unihan[char].get(pron_field)
        if not char_prons:
            no_pron_chars.add(char)
            continue
        for char_pron in char_prons:
            regularities[f"{char}:{char_pron}"].add(char)
            #  TODO: be smarter about creating components if needed
            for component in ids[char]:
                regularities[f"{component}:{char_pron}"].add(char)
                if component not in unihan:
                    unknown_comps.add(component)
                    continue
                component_prons = unihan[component].get(pron_field)
                if not component_prons:
                    no_pron_comps.add(component)
                    continue

    # delete the characters with only themselves in the value
    to_delete = [k for k, v in regularities.items() if len(v) == 1]
    for k in to_delete:
        del regularities[k]

    # get the list of characters for which no regularities could be found
    chars_with_regularities = set()
    for _, v in regularities.items():
        chars_with_regularities |= v
    no_regularities = char_set - no_pron_chars - chars_with_regularities

    return regularities, no_regularities, no_pron_chars, no_pron_comps, unknown_comps


def _format_json(data):
    return json.dumps(OrderedDict(data), cls=SetEncoder, ensure_ascii=False, indent=2)


def main():
    # args = parser.parse_args()

    unihan = _read_unihan()
    # TODO: allow choosing character set
    # _, char_set = _read_hsk(6)
    char_set = _find_joyo(unihan)
    ids = _read_ids()

    (
        regularities,
        no_regularities,
        no_pron_chars,
        no_pron_comps,
        unknown_comps,
    ) = get_phonetic_regularities(char_set, ids, unihan)
    log.info(f"Found {len(regularities)} pronunciation groups")
    log.info(f"{len(no_pron_comps)} components with no pronunciations: {no_pron_comps}")
    log.info(f"{len(unknown_comps)} components not found in unihan: {unknown_comps}")
    log.info(f"{len(no_pron_chars)} characters with no pronunciations: {no_pron_chars}")
    log.info(
        f"{len(no_regularities)} characters with no regularities: {no_regularities}"
    )
    print(_format_json(regularities))

    # Next issues:

    # * hou and bou should at least be linked as similar
    # * sprinkle in exceptions to get the numbers down


if __name__ == "__main__":
    main()
