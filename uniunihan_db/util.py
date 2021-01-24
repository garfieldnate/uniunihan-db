import csv
import json
import logging
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import jaconv

from uniunihan_db.lingua import mandarin

PROJECT_DIR = Path(__file__).parents[1]

DATA_DIR = PROJECT_DIR / "data"

GENERATED_DATA_DIR = DATA_DIR / "generated"
GENERATED_DATA_DIR.mkdir(exist_ok=True)

INCLUDED_DATA_DIR = DATA_DIR / "included"

LOG_FILE = GENERATED_DATA_DIR / "log.txt"

HK_ED_CHARS_FILE = GENERATED_DATA_DIR / "hk_ed_chars.json"


def configure_logging(name):
    logging.basicConfig(
        level=os.environ.get("LOGLEVEL", "INFO"),
        format="[%(levelname)s] %(name)s: %(message)s",
    )
    log = logging.getLogger(name)

    fh = logging.FileHandler(LOG_FILE, mode="w")
    fh.setLevel(logging.WARN)
    log.addHandler(fh)

    return log


log = configure_logging(__name__)


@dataclass
class Joyo:
    old_char_to_prons: Dict[str, List[str]]
    new_char_to_prons: Dict[str, List[str]]
    char_to_supplementary_info: Dict[str, Dict[str, Any]]

    def __post_init__(self):
        self._new_to_old = defaultdict(set)
        for c_sup in self.char_to_supplementary_info.values():
            new_c = c_sup["new"]
            old_c = c_sup["old"] or c_sup["new"]
            self._new_to_old[new_c].add(old_c)

    def new_to_old(self, new_char):
        return self._new_to_old[new_char]


def read_joyo():
    log.info("Loading joyo data...")
    new_char_to_prons = {}
    old_char_to_prons = {}
    char_info = {}
    with open(INCLUDED_DATA_DIR / "augmented_joyo.csv") as f:
        # filter comments
        rows = csv.DictReader(filter(lambda row: row[0] != "#", f))
        for r in rows:
            supplementary_info = {
                "keyword": r["English_meaning"],
                "kun-yomi": r["kun-yomi"],
                "grade": r["grade"],
                "strokes": r["strokes"],
                "new": r["new"],
                "old": None,
            }
            # remove empty readings
            readings = [yomi for yomi in r["on-yomi"].split("|") if yomi]
            # note the non-Joyo readings and strip the indicator asterisk
            supplementary_info["non-joyo"] = [
                yomi[:-1] for yomi in readings if yomi[-1] == "*"
            ]
            readings = [yomi.rstrip("*") for yomi in readings if yomi]
            supplementary_info["readings"] = sorted(readings)

            new_c = r["new"]
            new_char_to_prons[new_c] = readings
            char_info[new_c] = supplementary_info

            # old glyph same as new glyph when missing
            old_c = r["old"] or new_c
            old_char_to_prons[old_c] = readings
            char_info[old_c] = supplementary_info
            if old_c != new_c:
                supplementary_info["old"] = old_c

    return Joyo(old_char_to_prons, new_char_to_prons, char_info)


def read_phonetic_components():
    log.info("Loading phonetic components...")
    comp_to_char = {}
    with open(GENERATED_DATA_DIR / "components_to_chars.tsv") as f:
        rows = csv.DictReader(f, delimiter="\t")
        for r in rows:
            component = r["component"]
            chars = r["characters"]
            comp_to_char[component] = set(chars)

    return comp_to_char


def read_edict_freq(aligner):
    log.info("Loading EDICT frequency list...")
    char_to_pron_to_words = defaultdict(lambda: defaultdict(list))
    with open(GENERATED_DATA_DIR / "edict-freq.tsv") as f:
        num_words = 0
        for line in f.readlines():
            line = line.strip()
            surface, surface_normalized, pronunciation, english, frequency = line.split(
                "\t"
            )
            alignment = aligner.align(surface_normalized, pronunciation)
            if alignment:
                word = {
                    "surface": surface,
                    "pron": pronunciation,
                    "freq": int(frequency),
                    "en": english,
                }
                for c, pron in alignment.items():
                    char_to_pron_to_words[c][pron].append(word)
                num_words += 1
    log.info(f"  Read {num_words} words from EDICT frequency list")
    return char_to_pron_to_words


def read_historical_on_yomi(normalizer=jaconv.hira2kata):
    log.info("Loading historical on-yomi data...")
    char_to_new_to_old_pron = defaultdict(dict)
    with open(INCLUDED_DATA_DIR / "historical_kanji_on-yomi.csv") as f:
        # filter comments
        rows = csv.DictReader(filter(lambda row: row[0] != "#", f))
        for r in rows:
            modern = r["現代仮名遣い"]
            historical = r["字音仮名遣い"]
            historical_kata = normalizer(historical)
            if historical_kata != modern:
                chars = r["字"]
                for c in chars:
                    char_to_new_to_old_pron[c][modern] = historical

    return char_to_new_to_old_pron


def read_unihan():
    log.info("Loading unihan data...")
    # TODO: read path from constants file
    with open(GENERATED_DATA_DIR / "unihan.json") as f:
        unihan = json.load(f)
    log.info(f"  Read {len(unihan)} characters from Unihan DB")

    return unihan


def get_mandarin_pronunciation(unihan_entry):
    # check all of the available fields in order of usefulness/accuracy
    if pron := unihan_entry.get("kHanyuPinlu"):
        #             print('returning pinlu')
        return [p["phonetic"] for p in pron]
    elif pron := unihan_entry.get("kXHC1983"):
        #             print('returning 1983')
        return [p["reading"] for p in pron]
    elif pron := unihan_entry.get("kHanyuPinyin"):
        #             print('returning pinyin!')
        return [r for p in pron for r in p["readings"]]
    elif pron := unihan_entry.get("kMandarin"):
        # print("returning mandarin!")
        return pron["zh-Hans"]
    return []


def read_ckip_20k():
    ckip_path = INCLUDED_DATA_DIR / "CKIP_20000" / "mandarin_20K.tsv"
    log.info(f"Loading {ckip_path}")

    char_to_pron_to_words = defaultdict(lambda: defaultdict(list))
    with open(ckip_path) as f:
        num_words = 0
        rows = csv.DictReader(filter(lambda row: row[0] != "#", f), delimiter="\t")
        for r in rows:
            # word	function	roman	meaning	freq
            pronunciation = mandarin.pinyin_numbers_to_tone_marks(r["roman"])
            syllables = pronunciation.split(" ")
            word = r["word"]
            if len(syllables) != len(word):
                raise ValueError(
                    f"Number of pinyin syllables does not match number of characters: {word}/{pronunciation}"
                )
            else:
                word_dict = {
                    "surface": word,
                    "pron": pronunciation,
                    "freq": int(r["freq"]),
                    "en": r["meaning"],
                }
                for c, pron in zip(word, syllables):
                    char_to_pron_to_words[c][pron].append(word_dict)
                num_words += 1
    log.info(f"  Read {num_words} words from CKIP frequency list")
    return char_to_pron_to_words


def read_cedict():
    log.info("Loading CEDICT data...")
    cedict_file = GENERATED_DATA_DIR / "cedict_1_0_ts_utf-8_mdbg" / "cedict_ts.u8"
    num_words = 0
    entries = defaultdict(list)
    with open(cedict_file) as f:
        for line in f.readlines():
            # skip comments or empty lines
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # parse format: trad simp [pin yin] /en1/en2/en3/
            remaining, en = line.split("/", 1)
            en = en.rstrip("/")
            remaining, pron = remaining.split("[")
            pron = pron.rstrip("] ")
            trad, simp = remaining.rstrip().split(" ")
            pron = pron.lstrip("[").rstrip("]")

            # store word
            word = {"en": en, "trad": trad, "simp": simp, "pron": pron}
            num_words += 1
            entries[trad].append(word)
    log.info(f"  Read {num_words} entries from CEDICT")
    return entries
