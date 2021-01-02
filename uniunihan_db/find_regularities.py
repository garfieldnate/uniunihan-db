# import argparse
import csv
import json
import logging
import os
import re
from collections import defaultdict
from pathlib import Path

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


def _read_unihan():
    log.info("Loading unihan data...")
    # TODO: read path from constants file
    with open(DATA_DIR / "unihan.json") as f:
        unihan = json.load(f)
    return unihan


def _find_joyo(unihan):
    log.info("Extracting Joyo Kanji from Unihan database...")
    chars = []
    for char, entry in unihan.items():
        if "kJoyoKanji" in entry:
            joyo = entry["kJoyoKanji"][0]
            # Don't include variants
            if not joyo.startswith("U"):
                chars.append(char)

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


def get_phonetic_regularities(char_set, ids, unihan):
    pron_field = "kJapaneseOn"
    regularities = defaultdict(list)
    no_regularities = set()
    no_pronunciations = set()
    unique_chars = set()
    for char in char_set:
        char_prons = unihan[char].get(pron_field)
        if not char_prons:
            no_pronunciations.add(char)
            continue
        has_regularity = False
        for char_pron in char_prons:
            #  TODO: be smarter about creating components if needed
            for component in ids[char]:
                if component not in unihan:
                    log.info(f"Component {component} not found in unihan")
                    continue
                component_prons = unihan[component].get(pron_field)
                if not component_prons:
                    log.info(f"Component {component} has no values for {pron_field}")
                    continue
                for component_pron in component_prons:
                    if component_pron == char_pron:
                        regularities[f"{component}:{component_pron}"].append(char)
                        unique_chars.add(component)
                        unique_chars.add(char)
                        has_regularity = True
        if not has_regularity:
            no_regularities.add(char)
            # TODO: report characters with no regularities

    regularities = {k: v for k, v in regularities.items() if len(v) > 1}
    return regularities, no_regularities, no_pronunciations, unique_chars


def _format_json(data):
    return json.dumps(data, ensure_ascii=False, indent=2)


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
        no_pronunciations,
        unique_chars,
    ) = get_phonetic_regularities(char_set, ids, unihan)
    # TODO: report characters not in unihan
    log.info(f"{len(unique_chars)} unique characters")
    log.info(
        f"{len(no_pronunciations)} characters with no pronunciations: {no_pronunciations}"
    )
    log.info(
        f"{len(no_regularities)} characters with no regularities: {no_regularities}"
    )
    print(_format_json(regularities))

    # Next issues:
    # * 韻:  should be categorized under 音:IN. Also 動 -> add ALL characters under their own name as a regularity
    # * 妨: 方 should give bou regularity, but it doesn't have that reading on its own. Also 穂,
    # * 化: we need to explicitly set characters to their own components; similar to kokoro
    # * hou and bou should at least be linked as similar
    # * okay to sprinkle in exceptions


if __name__ == "__main__":
    main()
