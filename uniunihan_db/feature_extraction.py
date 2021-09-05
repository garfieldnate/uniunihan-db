import csv
import dataclasses
import json
import re
from collections import defaultdict

from opencc import OpenCC

from uniunihan_db.data.datasets import get_unihan
from uniunihan_db.data_paths import GENERATED_DATA_DIR, INCLUDED_DATA_DIR

from .lingua import japanese, mandarin
from .util import configure_logging

log = configure_logging(__name__)

IDC_REGEX = r"[\u2FF0-\u2FFB]"
UNENCODED_DC_REGEX = r"[①-⑳]"


# TODO: put data loading in utils file or something
def _read_hsk(max_level):
    if max_level < 1 or max_level > 6:
        raise ValueError("max HSK level must be between 1 and 6")

    cc = OpenCC("s2t")
    char_set = set()
    word_list = []
    for level in range(1, max_level + 1):
        with open(INCLUDED_DATA_DIR / "hsk" / f"hsk-{level}.txt") as f:
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


def _get_pronunciation_feats(syl, prefix):
    syl = dataclasses.asdict(syl)
    return {f"{prefix}_{k}": str(v) for k, v in syl.items()}


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
    feats |= {f"ids_{c}": "T" for c in ids_entry}
    # the character itself may be useful for grouping it with other characters of the same pronunciation
    # if it's unique, we trim it out in _trim_ids
    feats[f"ids_{unihan_entry['char']}"] = "T"
    # TODO: list of recursively added radicals?

    return feats


def _trim_ids(data, class_):
    """Delete IDS features that are only found once, since they are useless for
    predicting pronunciation for our character list"""
    # ids -> class_ -> frequency
    ids_class_freq = defaultdict(lambda: defaultdict(int))
    for feats in data:
        class_value = feats.get(class_, None)
        if not class_value:
            continue
        for feat in feats:
            if feat.startswith("ids"):
                ids_class_freq[feat][class_value] += 1

    # get the maximum number of characters where the IDS could help in classification
    # log.info(ids_class_freq)
    # ids_max = {k: max(ids_class_freq[k].values()) for k in ids_class_freq}
    ids_filtered = {k for k in ids_class_freq if max(ids_class_freq[k].values()) > 1}
    # log.info(ids_filtered)
    # log.info(ids_max)
    for feats in data:
        class_value = feats.get(class_, None)
        if not class_value:
            continue
        to_delete = [
            feat
            for feat in feats
            # feat in ids_filtered  #
            if feat.startswith("ids") and feat not in ids_filtered
        ]
        for feat in to_delete:
            del feats[feat]


def _format_json(data):
    return json.dumps(data, ensure_ascii=False, indent=2)


def _format_arff(data):
    unique_features = set()
    for feats in data:
        unique_features |= feats.keys()

    log.info(f"{len(unique_features)} unique features")

    text_builder = []
    text_builder.append("@RELATION chinese_characters\n")
    counter = 0
    for feat in sorted(unique_features):
        if feat.startswith("ids_"):
            text_builder.append(f"@ATTRIBUTE {feat} {{T, F}}\n")
        else:
            text_builder.append(f"@ATTRIBUTE {feat} string\n")
        counter += 1

    log.info(f"wrote {counter} attributes")

    text_builder.append("@data\n")
    for feats in data:
        data_spec = []
        for feat in sorted(unique_features):
            if feat.startswith("ids_"):
                data_spec.append(str(feat in feats)[0])
            else:
                data_spec.append(feats.get(feat, "?") or "?")
        text_builder.append(",".join(data_spec))
        text_builder.append("\n")

    return "".join(text_builder)


def main():
    # TODO: allow choosing character set
    # _, char_set = _read_hsk(6)
    unihan = get_unihan()
    char_set = _find_joyo(unihan)
    ids = _read_ids()

    log.info("Extracting features...")
    feature_dicts = []
    for c in char_set:
        unihan_entry = unihan[c]
        ids_entry = ids[c]
        feature_dicts.append(get_feats(unihan_entry, ids_entry))

    # TODO: read the class from a parameter
    _trim_ids(feature_dicts, "jp_surface")

    # with open(GENERATED_DATA_DIR / 'features.json') as f:
    print(_format_json(feature_dicts))
    # print(_format_arff(feature_dicts))


if __name__ == "__main__":
    main()
