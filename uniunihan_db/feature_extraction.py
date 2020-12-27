import csv
import dataclasses
import json
import logging
import os
import re
from pathlib import Path

from opencc import OpenCC

from .lingua import japanese, mandarin

# TODO: put constants in shared file
PROJECT_DIR = Path(__file__).parents[1]

DATA_DIR = PROJECT_DIR / "data"
LOG_FILE = DATA_DIR / "log.txt"

# TODO: putting logging config in shared file
logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "INFO"),
    format="[%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

fh = logging.FileHandler(LOG_FILE, mode="w")
fh.setLevel(logging.WARN)
log.addHandler(fh)

IDC_REGEX = r"[\u2FF0-\u2FFB]"


# TODO: put data loading in utils file or something
def _read_hsk(max_level):
    if max_level < 1 or max_level > 6:
        raise ValueError("max HSK level must be between 1 and 6")

    cc = OpenCC("s2t")
    char_set = set()
    word_list = []
    for level in range(1, max_level + 1):
        with open(DATA_DIR / "hsk" / f"hsk-{level}.txt") as f:
            for line in f:
                word = line.strip()
                # Use traditional characters for better IDS->pronunciation predictability
                # TODO: did the designers really get the system that wrong? Test once with simplified.
                traditional_word = cc.convert(word)
                word_list.append(traditional_word)

                # remove parentheticals specifying POS
                chars = traditional_word.split("（")[0]
                chars = chars.replace("…", "")
                char_set.update(chars)

    return word_list, char_set


def _read_unihan():
    log.info("Loading unihan data...")
    # TODO: read path from constants file
    with open(DATA_DIR / "unihan.json") as f:
        unihan = json.load(f)
    return unihan


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
            breakdown = re.sub(IDC_REGEX, "", breakdown)
            ids[r[1]] = breakdown
    return ids


def _get_pronunciation_feats(syl, prefix):
    syl = dataclasses.asdict(syl)
    return {f"{prefix}_{k}": v for k, v in syl.items()}


def get_feats(unihan_entry, ids_entry):
    feats = {"char": unihan_entry["char"]}
    # get traditional variant
    # pronunciation: JP

    if on_list := unihan_entry.get("kJapaneseOn"):
        # TODO: allow using other pronunciations?
        ime = japanese.alpha_to_alpha(on_list[0])
        if han_syl := japanese.parse_han_syllable(ime):
            feats |= _get_pronunciation_feats(han_syl, "jp")
            feats["jp_surface"] = han_syl.surface

    # pronunciation: ZH
    if s := unihan_entry.get("kMandarin", {}).get("zh-Hans"):
        # TODO: allow using Taiwan pronunciations
        if syl := mandarin.parse_syllable(s):
            feats |= _get_pronunciation_feats(syl, "zh")
            feats["zh_surface"] = syl.surface

    # list of top-level radicals
    feats |= {f"ids_{c}": True for c in ids_entry}
    feats[f"ids_{unihan_entry['char']}"] = True
    # TODO: list of recursively added radicals?

    return feats


def main():
    # TODO: allow choosing character set
    _, char_set = _read_hsk(6)
    unihan = _read_unihan()
    ids = _read_ids()

    log.info("Extracting features...")
    feature_dicts = []
    for c in char_set:
        unihan_entry = unihan[c]
        ids_entry = ids[c]
        feature_dicts.append(get_feats(unihan_entry, ids_entry))

    # with open(DATA_DIR / 'features.json') as f:
    print(json.dumps(feature_dicts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
