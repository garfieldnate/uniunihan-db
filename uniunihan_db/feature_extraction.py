import dataclasses
import json
from pathlib import Path

from .lingua import japanese, mandarin

PROJECT_DIR = Path(__file__).parents[1]

DATA_DIR = PROJECT_DIR / "data"


def _read_hsk(max_level):
    if max_level < 1 or max_level > 6:
        raise ValueError("max HSK level must be between 1 and 6")
    char_set = set()
    word_list = []
    for level in range(1, max_level + 1):
        with open(DATA_DIR / "hsk" / f"hsk-{level}.txt") as f:
            for line in f:
                word = line.strip()
                word_list.append(word)
                char_set.update(word)

    return word_list, char_set


def _read_unihan():
    with open(DATA_DIR / "unihan.json") as f:
        unihan = json.load(f)
    return unihan


def _get_pronunciation_feats(syl, prefix):
    syl = dataclasses.asdict(syl)
    return {f"{prefix}_{k}": v for k, v in syl.items()}


def get_feats(unihan_entry):
    feats = {"char": unihan_entry["char"]}
    # get traditional variant
    # pronunciation: JP

    if on_list := unihan_entry.get("kJapaneseOn"):
        # TODO: allow using other pronunciations?
        ime = japanese.alpha_to_alpha(on_list[0])
        if han_syl := japanese.parse_han_syllable(ime):
            feats |= _get_pronunciation_feats(han_syl, "jp")

    # pronunciation: ZH
    if s := unihan_entry.get("kMandarin", {}).get("zh-Hans"):
        # TODO: allow using Taiwan pronunciations
        if syl := mandarin.parse_syllable(s):
            feats |= _get_pronunciation_feats(syl, "zh")

    # list of top-level radicals
    # list of recursively added radicals
    return feats


def main():
    # TODO: allow choosing character set
    _, char_set = _read_hsk(6)
    unihan = _read_unihan()
    feature_sets = [get_feats(entry) for entry in unihan]
    for s in feature_sets:
        # collect all features
        print(s)
        exit()
        # print(",".join(vector))
    # print(word_list)
    print(char_set)
    # for char in char_list:
    #     pass


if __name__ == "__main__":
    main()
