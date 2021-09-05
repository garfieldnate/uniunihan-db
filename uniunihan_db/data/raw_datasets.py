import csv
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from functools import cache
from typing import Any, Mapping, Sequence, Set

import commentjson as json
import jaconv
import requests

from uniunihan_db.util import GENERATED_DATA_DIR, INCLUDED_DATA_DIR, configure_logging

YTENX_URL = "https://github.com/BYVoid/ytenx/archive/master.zip"
YTENX_ZIP_FILE = GENERATED_DATA_DIR / "ytenx-master.zip"
YTENX_DIR = YTENX_ZIP_FILE.with_suffix("")

BAXTER_SAGART_FILE = INCLUDED_DATA_DIR / "BaxterSagartOC2015-10-13.csv"

log = configure_logging(__name__)


def __ytenx_download():
    """Download and unzip the ytenx rhyming data."""
    # download
    if YTENX_ZIP_FILE.exists() and YTENX_ZIP_FILE.stat().st_size > 0:
        log.debug(f"{YTENX_ZIP_FILE.name} already exists; skipping download")
    else:
        log.info(f"Downloading ytenx rhyming data to {YTENX_ZIP_FILE}...")
        r = requests.get(YTENX_URL, stream=True)
        with open(YTENX_ZIP_FILE, "wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

    # unzip
    if YTENX_DIR.exists() and YTENX_DIR.is_dir():
        log.debug(f"  {YTENX_DIR.name} already exists; skipping unzip")
    else:
        with zipfile.ZipFile(YTENX_ZIP_FILE, "r") as zip_ref:
            zip_ref.extractall(GENERATED_DATA_DIR)


@cache
def get_ytenx_rhymes():
    __ytenx_download()

    log.info("  Reading rhymes from ytenx...")
    char_to_component = defaultdict(list)
    with open(YTENX_DIR / "ytenx" / "sync" / "dciangx" / "DrienghTriang.txt") as f:
        rows = csv.DictReader(f, delimiter=" ")
        for r in rows:
            char = r["#字"]
            del r["#字"]
            # store two alternative OC pronunciations in a list
            r["擬音"] = [r["擬音"]]
            if pron_2 := r["擬音2"]:
                r["擬音"].append(pron_2)
            del r["擬音2"]
            # keep all keys with non-empty values
            char_info = {k: v for k, v in r.items() if v}
            char_to_component[char].append(char_info)

    return char_to_component


@dataclass
class BaxterSagart:
    char: str
    pinyin: str
    middle_chinese: str
    old_chinese: str
    gloss: str


@cache
def get_baxter_sagart():
    log.info("Loading Baxter/Sagart reconstruction data...")
    char_to_info = defaultdict(list)
    with BAXTER_SAGART_FILE.open() as f:
        # filter comments
        rows = csv.DictReader(filter(lambda row: row[0] != "#", f))
        for r in rows:
            char = r["zi"]
            char_to_info[char].append(
                BaxterSagart(
                    char=char.strip(),
                    pinyin=r["py"].strip(),
                    middle_chinese=r["MC"].strip(),
                    old_chinese=r["OC"].strip(),
                    gloss=r["gloss"].strip(),
                )
            )
    return char_to_info


@cache
def get_ytenx_variants():
    __ytenx_download()

    log.info("  Reading variants from ytenx...")
    char_to_variants = defaultdict(set)
    with open(YTENX_DIR / "ytenx" / "sync" / "jihthex" / "JihThex.csv") as f:
        rows = csv.DictReader(f)
        for r in rows:
            char = r["#字"]
            for field in ["全等", "語義交疊", "簡體", "繁體"]:
                if variants := r[field]:
                    for v in variants:
                        char_to_variants[char].add(v)
    with open(YTENX_DIR / "ytenx" / "sync" / "jihthex" / "ThaJihThex.csv") as f:
        rows = csv.DictReader(f)
        for r in rows:
            char = r["#字"]
            if variants := r["其他異體"]:
                for v in variants:
                    char_to_variants[char].add(v)

    return char_to_variants


@cache
def get_ckip_20k(index_chars: bool = False) -> Mapping[str, Any]:
    ckip_path = INCLUDED_DATA_DIR / "CKIP_20000" / "mandarin_20K.tsv"
    log.info(f"Loading {ckip_path}")

    if index_chars:
        # char -> pronunciation -> word list
        entries: Mapping[str, Any] = defaultdict(lambda: defaultdict(list))
    else:
        # surface form -> word list
        entries = defaultdict(list)
    with open(ckip_path) as f:
        num_words = 0
        rows = csv.DictReader(filter(lambda row: row[0] != "#", f), delimiter="\t")
        for r in rows:
            # rows contains: word, function, roman, meaning, freq
            pronunciation = r["roman"]
            word = r["word"]
            word_dict = {
                "surface": word,
                "pron": pronunciation,
                "freq": int(r["freq"]),
                "en": r["meaning"],
            }
            num_words += 1
            if index_chars:
                syllables = pronunciation.split(" ")
                if len(syllables) != len(word):
                    raise ValueError(
                        f"Number of pinyin syllables does not match number of characters: {word}/{pronunciation}"
                    )
                for c, pron in zip(word, syllables):
                    entries[c][pron].append(word_dict)
            else:
                entries[word].append(word_dict)

    log.info(f"  Read {num_words} words from CKIP frequency list")
    return entries


@cache
def get_cedict(index_chars: bool = False, filter: bool = True) -> Mapping[str, Any]:
    log.info("Loading CEDICT data...")
    cedict_file = GENERATED_DATA_DIR / "cedict_1_0_ts_utf-8_mdbg" / "cedict_ts.u8"
    num_words = 0
    if index_chars:
        # char -> pronunciation -> word list
        entries: Mapping[str, Any] = defaultdict(lambda: defaultdict(list))
    else:
        # surface form -> word list
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
            if filter:
                if (
                    "variant of" in en
                    or en.startswith("surname")
                    or en.startswith("(old)")
                ):
                    continue

            remaining, pron = remaining.split("[")

            trad, simp = remaining.rstrip().split(" ")
            if len(trad) != len(simp):
                raise ValueError(
                    f"Number of characters for traditional and simplified forms do not match: {trad}/{simp}"
                )

            pron = pron.lstrip("[").rstrip("] ").lower()
            word_dict = {"en": en, "trad": trad, "simp": simp, "pron": pron}

            # store word
            if index_chars:
                syllables = pron.split(" ")
                # We can't automatically (simply) align many words, e.g. those with
                # numbers or letters or multi-syllabic characters like ㍻. So we just
                # remove these from the index altogether
                if len(syllables) != len(trad):
                    continue
                    # raise ValueError(
                    #     f"Number of pinyin syllables does not match number of characters: {len(trad)} ({trad}) != {len(pron)} ({pron})"
                    # )
                num_words += 1
                for c, pron in zip(trad, syllables):
                    entries[c][pron].append(word_dict)

            else:
                num_words += 1
                entries[trad].append(word_dict)
    log.info(f"  Read {num_words} entries from CEDICT")
    return entries


@dataclass
class Joyo:
    old_char_to_prons: Mapping[str, Sequence[str]]
    new_char_to_prons: Mapping[str, Sequence[str]]
    char_to_supplementary_info: Mapping[str, Mapping[str, Any]]

    def __post_init__(self) -> None:
        self._new_to_old: Mapping[str, Set[str]] = defaultdict(set)
        for c_sup in self.char_to_supplementary_info.values():
            new_c = c_sup["new"]
            old_c = c_sup["old"] or c_sup["new"]
            self._new_to_old[new_c].add(old_c)

    def new_to_old(self, new_char: str) -> Set[str]:
        return self._new_to_old[new_char]


@cache
def get_joyo():
    log.info("Loading joyo data...")
    new_char_to_prons = {}
    old_char_to_prons = {}
    char_info = {}
    with open(INCLUDED_DATA_DIR / "augmented_joyo.csv") as f:
        # filter comments
        rows = csv.DictReader(filter(lambda row: row[0] != "#", f))
        for r in rows:
            kun_yomi = [yomi for yomi in (r["kun-yomi"] or "").split("|") if yomi]
            supplementary_info = {
                "keyword": r["English_meaning"],
                "kun_yomi": kun_yomi,
                "grade": r["grade"],
                "strokes": r["strokes"],
                "new": r["new"],
                "old": None,
            }
            # remove empty readings
            readings = [yomi for yomi in r["on-yomi"].split("|") if yomi]
            # note the non-Joyo readings and strip the indicator asterisk
            supplementary_info["non_joyo"] = [
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


@cache
def get_phonetic_components():
    log.info("Loading phonetic components...")
    comp_to_char = {}
    with open(GENERATED_DATA_DIR / "components_to_chars.tsv") as f:
        rows = csv.DictReader(f, delimiter="\t")
        for r in rows:
            component = r["component"]
            chars = r["characters"]
            comp_to_char[component] = set(chars)

    return comp_to_char


@cache
def get_edict_freq(aligner):
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


@cache
def get_historical_on_yomi():
    log.info("Loading historical on-yomi data...")
    char_to_new_to_old_pron = defaultdict(dict)
    with open(INCLUDED_DATA_DIR / "historical_kanji_on-yomi.csv") as f:
        # filter comments
        rows = csv.DictReader(filter(lambda row: row[0] != "#", f))
        for r in rows:
            modern = r["現代仮名遣い"]
            historical = jaconv.hira2kata(r["字音仮名遣い"])
            if historical != modern:
                chars = r["字"]
                for c in chars:
                    char_to_new_to_old_pron[c][modern] = historical

    return char_to_new_to_old_pron


@cache
def get_unihan() -> Mapping[str, Any]:
    log.info("Loading unihan data...")
    # TODO: read path from constants file
    with open(GENERATED_DATA_DIR / "unihan.json") as f:
        unihan = json.load(f)
    log.info(f"  Read {len(unihan)} characters from Unihan DB")

    return unihan
