import csv
import json
import tarfile
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import (
    AbstractSet,
    Any,
    Dict,
    List,
    Mapping,
    MutableMapping,
    MutableSet,
    Optional,
    TypeVar,
)

import commentjson
import jaconv
import requests
from datapackage import Package
from loguru import logger
from unihan_etl.core import Packager as unihan_packager
from unihan_etl.types import UntypedUnihanData

from uniunihan_db.data.paths import (
    CEDICT_FILE,
    CEDICT_URL,
    CEDICT_ZIP,
    CHUNOM_VOCAB_FILE,
    COMPONENT_OVERRIDE_FILE,
    EDICT_FREQ_DIR,
    EDICT_FREQ_FILE,
    EDICT_FREQ_TARBALL,
    EDICT_FREQ_URL,
    GENERATED_DATA_DIR,
    INCLUDED_DATA_DIR,
    JUN_DA_CHAR_FREQ_FILE,
    JUN_DA_CHAR_FREQ_URL,
    KENGDIC_DATA_PACKAGE_URL,
    LIB_HANGUL_DIR,
    LIB_HANGUL_URL,
    LIB_HANGUL_ZIP_FILE,
    UNIHAN_FILE,
)
from uniunihan_db.data.types import Char2Pron2Words, StringToStrings, Word, ZhWord
from uniunihan_db.lingua.aligner import Aligner
from uniunihan_db.util import read_csv

YTENX_URL = "https://github.com/BYVoid/ytenx/archive/master.zip"
YTENX_ZIP_FILE = GENERATED_DATA_DIR / "ytenx-master.zip"
YTENX_DIR = YTENX_ZIP_FILE.with_suffix("")

BAXTER_SAGART_FILE = INCLUDED_DATA_DIR / "BaxterSagartOC2015-10-13.csv"

#################
# Downloaders ###
#################


def __download_unihan():
    """Download the famous Unihan database from the Unicode Consortium,
    and store it has a normalized JSON file"""

    if UNIHAN_FILE.exists() and UNIHAN_FILE.stat().st_size > 0:
        logger.info(f"{UNIHAN_FILE.name} already exists; skipping download")
        return

    logger.info("  Downloading unihan data...")
    p = unihan_packager.from_cli(["-F", "json", "--destination", str(UNIHAN_FILE)])
    p.download()
    # instruct packager to return data instead of writing to file
    # https://github.com/cihai/unihan-etl/issues/233
    p.options.format = "python"
    unihan = p.export()
    if unihan is None:
        raise ValueError("Could not load unihan data")

    logger.info("  Converting unihan data to dictionary format...")
    unihan_dict: Dict[
        str, UntypedUnihanData
    ] = {}  # {entry["char"]: entry for entry in unihan}

    logger.info("  Simplifying variant fields...")
    # for entry in (dict(e) for e in unihan_dict.values()):
    for entry in (dict(e) for e in unihan):
        unihan_dict[entry["char"]] = entry
        # TODO: address duplication below
        if compat_variant := entry.get("kCompatibilityVariant"):
            codepoint = compat_variant[2:]
            char = chr(int(codepoint, 16))
            entry["kCompatibilityVariant"] = char
        for field_name in [
            "kSemanticVariant",
            "kZVariant",
            "kSimplifiedVariant",
            "kTraditionalVariant",
        ]:
            if variants := entry.get(field_name, []):
                new_variants = []
                for v in variants:
                    # https://github.com/cihai/unihan-etl/issues/80#issuecomment-757470998
                    codepoint = v.split("<")[0][2:]
                    char = chr(int(codepoint, 16))
                    new_variants.append(char)
                entry[field_name] = new_variants
        # slightly different structure
        if jinmeiyo := entry.get("kJinmeiyoKanji", []):
            new_variants = []
            for variant in jinmeiyo:
                if "U+" in variant:
                    codepoint = variant[7:]
                    char = chr(int(codepoint, 16))
                    new_variants.append(char)
            entry["kJinmeiyoKanji"] = new_variants
        if joyo := entry.get("kJoyoKanji"):
            new_variants = []
            for variant in joyo:
                if "U+" in variant:
                    codepoint = variant[2:]
                    char = chr(int(codepoint, 16))
                    new_variants.append(char)
            entry["kJoyoKanji"] = new_variants

    logger.info(f"  Writing unihan to {UNIHAN_FILE}...")
    with Path(UNIHAN_FILE).open("w", encoding="utf-8") as f:
        json.dump(unihan_dict, f, indent=2, ensure_ascii=False)
    logger.info(f"  Saved unihan DB to: {UNIHAN_FILE}")

    global UNIHAN_DICT
    UNIHAN_DICT = unihan_dict


def export_json(data, destination):
    """Export UNIHAN in JSON format."""
    with Path(destination).open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def __download_edict_freq():
    """Download and unzip Utsumi Hiroshi's frequency-annotated EDICT"""

    # download
    if EDICT_FREQ_TARBALL.exists() and EDICT_FREQ_TARBALL.stat().st_size > 0:
        logger.info(f"{EDICT_FREQ_TARBALL.name} already exists; skipping download")
    else:
        logger.info(
            f"Downloading frequency-annotated EDICT to {EDICT_FREQ_TARBALL.name}..."
        )
        r = requests.get(EDICT_FREQ_URL, stream=True)
        with open(EDICT_FREQ_TARBALL, "wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

    # unzip
    if EDICT_FREQ_DIR.exists() and EDICT_FREQ_DIR.is_dir():
        logger.info(f"  {EDICT_FREQ_DIR.name} already exists; skipping decompress")
    else:
        tar = tarfile.open(EDICT_FREQ_TARBALL, "r:gz")
        tar.extractall(GENERATED_DATA_DIR)
        tar.close()


def get_edict_freq(file=EDICT_FREQ_FILE):
    """Retrieve Utsumi Hiroshi's frequency-annotated EDICT data"""

    __download_edict_freq()

    logger.info(f"Reading EDICT frequency data from {file}...")
    words = []
    with open(file) as f:
        # skip header
        for i, line in enumerate(f.readlines()[1:]):
            word = line.split(" ")[0]
            freq = int(line.split("#")[-1][:-2])
            english = "/".join(line.split("/")[1:-2])
            if "[" not in line:
                # line contains no kanji
                continue
            pron = line.split("[")[1].split("]")[0]
            # negative frequency to sort descending
            words.append((-freq, word, pron, english, i))

    output = []
    for freq, word, pron, english, i in sorted(words):
        output.append(Word(word, f"edict-{i+1}", pron, english, -freq))

    return output


def __download_cedict():
    """Download and unzip CC-CEDICT"""

    # download
    if CEDICT_ZIP.exists() and CEDICT_ZIP.stat().st_size > 0:
        logger.info(f"{CEDICT_ZIP.name} already exists; skipping download")
    else:
        logger.info(f"Downloading CC-CEDICT to {CEDICT_ZIP.name}...")
        r = requests.get(CEDICT_URL, stream=True)
        with open(CEDICT_ZIP, "wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

    CEDICT_DIR = CEDICT_ZIP.with_suffix("")
    # unzip
    if CEDICT_DIR.exists() and CEDICT_DIR.stat().st_size > 0:
        logger.info(f"  {CEDICT_DIR.name} already exists; skipping decompress")
    else:
        logger.info(f"  Writing decompressed contents to {CEDICT_DIR.name}")
        with zipfile.ZipFile(CEDICT_ZIP, "r") as zip_ref:
            zip_ref.extractall(CEDICT_DIR)


def __download_jun_da_char_freq():
    """Download Jun Da's character frequency list"""
    # TODO: this thing is super fragile. Would be better to create and distribute
    # a data package version of the list somewhere.

    if JUN_DA_CHAR_FREQ_FILE.exists() and JUN_DA_CHAR_FREQ_FILE.stat().st_size > 0:
        logger.info(f"{JUN_DA_CHAR_FREQ_FILE.name} already exists; skipping download")
        return

    logger.info(
        f"Downloading Jun Da's character frequency list from {JUN_DA_CHAR_FREQ_URL}..."
    )
    r = requests.get(JUN_DA_CHAR_FREQ_URL)
    r.encoding = "GBK"
    for line in r.text.splitlines():
        if line.startswith("<pre>"):
            # remove leading <pre>
            line = line[5:]
            # remove trailing </pre> and extra content
            line = line.split("</pre>")[0]

            logger.info(
                "  Writing Jun Da's character frequency list to "
                f"{JUN_DA_CHAR_FREQ_FILE}"
            )
            with open(JUN_DA_CHAR_FREQ_FILE, "w") as f:
                f.write(
                    "Rank\tCharacter\tRaw Frequency\t"
                    "Frequency Percentile\tPinyin\tEnglish\n"
                )
                for entry in line.split("<br>"):
                    if entry:
                        f.write(entry)
                        f.write("\n")


def __download_libhangul():
    """Download and unzip the libhangul hanja word list data."""
    # download
    if LIB_HANGUL_ZIP_FILE.exists() and LIB_HANGUL_ZIP_FILE.stat().st_size > 0:
        logger.info(f"{LIB_HANGUL_ZIP_FILE.name} already exists; skipping download")
    else:
        logger.info(f"Downloading libhangul to {LIB_HANGUL_ZIP_FILE}...")
        r = requests.get(LIB_HANGUL_URL, stream=True)
        with open(LIB_HANGUL_ZIP_FILE, "wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

    # unzip
    if LIB_HANGUL_DIR.exists() and LIB_HANGUL_DIR.is_dir():
        logger.info(f"  {LIB_HANGUL_DIR.name} already exists; skipping unzip")
    else:
        with zipfile.ZipFile(LIB_HANGUL_ZIP_FILE, "r") as zip_ref:
            zip_ref.extractall(GENERATED_DATA_DIR)


def __download_ytenx():
    """Download and unzip the ytenx rhyming data."""
    # download
    if YTENX_ZIP_FILE.exists() and YTENX_ZIP_FILE.stat().st_size > 0:
        logger.debug(f"{YTENX_ZIP_FILE.name} already exists; skipping download")
    else:
        logger.info(f"Downloading ytenx rhyming data to {YTENX_ZIP_FILE}...")
        r = requests.get(YTENX_URL, stream=True)
        with open(YTENX_ZIP_FILE, "wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

    # unzip
    if YTENX_DIR.exists() and YTENX_DIR.is_dir():
        logger.debug(f"  {YTENX_DIR.name} already exists; skipping unzip")
    else:
        with zipfile.ZipFile(YTENX_ZIP_FILE, "r") as zip_ref:
            zip_ref.extractall(GENERATED_DATA_DIR)


###############
# Accessors ###
###############


@dataclass
class YtenxRhyme:
    char: str
    phonetic_component: str
    old_chinese: List[str]
    middle_chinese: Optional[str]
    late_middle_chinese: Optional[str]


@cache
def get_ytenx_rhymes():
    __download_ytenx()

    logger.info("  Reading rhymes from ytenx...")
    char_to_component = defaultdict(list)
    with open(YTENX_DIR / "ytenx" / "sync" / "dciangx" / "DrienghTriang.txt") as f:
        rows = csv.DictReader(f, delimiter=" ")
        for r in rows:
            char = r["#字"]
            del r["#字"]
            # store two alternative OC pronunciations in a list
            r["擬音"] = [r["擬音"]]  # type: ignore
            if pron_2 := r["擬音2"]:
                r["擬音"].append(pron_2)
            del r["擬音2"]
            char_to_component[char].append(
                YtenxRhyme(
                    char,
                    r["聲符"],
                    r["擬音"],
                    r["擬音（後世）"] or None,
                    r["擬音（更後世）"] or None,
                )
            )

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
    logger.info("Loading Baxter/Sagart reconstruction data...")
    char_to_info = defaultdict(list)
    rows = read_csv(BAXTER_SAGART_FILE)
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
    __download_ytenx()

    logger.info("Constructing variants index from Ytenx...")
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
def get_ckip_20k() -> Mapping[str, Any]:
    ckip_path = INCLUDED_DATA_DIR / "CKIP_20000" / "mandarin_20K.tsv"
    logger.info(f"Loading {ckip_path}")

    # surface form -> word list
    entries = defaultdict(list)
    num_words = 0
    rows = read_csv(ckip_path, delimiter="\t")
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
        entries[word].append(word_dict)

    logger.info(f"  Read {num_words} words from CKIP frequency list")
    return entries


@cache
def get_cedict(file=CEDICT_FILE, filter: bool = True) -> List[ZhWord]:
    __download_cedict()
    logger.info("Loading CEDICT data...")

    words: List[ZhWord] = []
    with open(file) as f:
        # current CEDICT has one bad line in it, and may have more in the future,
        # so we'll skip over them
        failed = 0
        for i, line in enumerate(f.readlines()):
            try:
                # skip comments or empty lines
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # parse format: trad simp [pin yin] /en1/en2/en3/
                remaining, en = line.split("/", 1)
                en = en.rstrip("/")
                if filter:
                    if (
                        en.startswith("variant of")
                        or en.startswith("see ")
                        or en.startswith("surname")
                        or en.startswith("(old)")
                    ):
                        continue

                remaining, pron = remaining.split("[")

                trad, simp = remaining.rstrip().split(" ")
                if len(trad) != len(simp):
                    raise ValueError(
                        "Number of characters for traditional and simplified "
                        f"forms do not match: {trad}/{simp}"
                    )

                pron = pron.lstrip("[").rstrip("] ").lower()
                # frequency is TODO
                word = ZhWord(
                    surface=trad,
                    id=f"cedict-{i+1}",
                    pron=pron,
                    english=en,
                    frequency=-1,
                    simplified=simp,
                )
                words.append(word)
            except Exception as e:
                failed += 1
                logger.error(f"Failed to parse line {i+1}: {line} ({e})")

    logger.info(f"  Read {len(words)} entries from CEDICT. {failed} failed to parse.")
    return words


@dataclass
class Joyo:
    old_char_to_prons: StringToStrings
    new_char_to_prons: StringToStrings
    char_to_supplementary_info: MutableMapping[str, MutableMapping[str, Any]]

    def __post_init__(self) -> None:
        self._new_to_old: Mapping[str, MutableSet[str]] = defaultdict(set)
        for c_sup in self.char_to_supplementary_info.values():
            new_c = c_sup["new"]
            old_c = c_sup["old"] or c_sup["new"]
            self._new_to_old[new_c].add(old_c)

    def new_to_old(self, new_char: str) -> AbstractSet[str]:
        return self._new_to_old[new_char]


@cache
def get_joyo():
    logger.info("Loading joyo data...")
    char_info: MutableMapping[str, MutableMapping[str, Any]] = {}
    rows = read_csv(INCLUDED_DATA_DIR / "augmented_joyo.csv")
    for r in rows:
        kun_yomi = {yomi for yomi in (r["kun-yomi"] or "").split("|") if yomi}
        supplementary_info = {
            "keyword": r["English_meaning"].split("|"),
            "kun_yomi": kun_yomi,
            "grade": r["grade"],
            "strokes": r["strokes"],
            "new": r["new"],
            "old": None,
        }
        # remove empty readings
        readings = {yomi for yomi in r["on-yomi"].split("|") if yomi}
        # note the non-Joyo readings and strip the indicator asterisk
        supplementary_info["non_joyo"] = {
            yomi[:-1] for yomi in readings if yomi[-1] == "*"
        }
        readings = {yomi.rstrip("*") for yomi in readings if yomi}
        supplementary_info["readings"] = readings

        new_c = r["new"]
        # old glyph same as new glyph when missing
        old_c = r["old"] or new_c
        char_info[old_c] = supplementary_info

        if old_c != new_c:
            supplementary_info["old"] = old_c

    return char_info


# TODO: unit test
@cache
def get_phonetic_components():
    """Extract and augment the phonetic component data in ytenx"""

    logger.info("Determining phonetic components...")

    ytenx_rhyme_data = get_ytenx_rhymes()
    char_to_component = {
        char: info[0].phonetic_component for char, info in ytenx_rhyme_data.items()
    }

    with COMPONENT_OVERRIDE_FILE.open() as f:
        extra_char_to_components = commentjson.load(f)
        char_to_component.update(extra_char_to_components)

    variants = get_variants()
    logger.info("  Addding phonetic components for variants...")
    variant_to_component = {}
    for char in char_to_component:
        for c in variants.get(char, []):
            if c not in char_to_component:
                variant_to_component[c] = char_to_component[char]
    char_to_component.update(variant_to_component)

    # group by component to make it easier to use
    component_to_chars = defaultdict(list)
    for char, component in sorted(char_to_component.items()):
        component_to_chars[component].append(char)

    return component_to_chars


W = TypeVar("W", bound=Word)


def index_vocab(words: List[W], aligner: Aligner) -> Char2Pron2Words:
    char_to_pron_to_words: Char2Pron2Words = defaultdict(lambda: defaultdict(list))
    for word in words:
        alignment = aligner.align(word.surface, word.pron)
        for c, pron in alignment:
            char_to_pron_to_words[c][pron].append(word)
    return char_to_pron_to_words


@cache
def get_historical_on_yomi():
    logger.info("Loading historical on-yomi data...")
    char_to_new_to_old_pron = defaultdict(dict)
    rows = read_csv(INCLUDED_DATA_DIR / "historical_kanji_on-yomi.csv")
    for r in rows:
        modern = r["現代仮名遣い"]
        historical = jaconv.hira2kata(r["字音仮名遣い"])
        if historical != modern:
            chars = r["字"]
            for c in chars:
                char_to_new_to_old_pron[c][modern] = historical

    return char_to_new_to_old_pron


@cache
def get_vocab_override(file) -> Char2Pron2Words:
    data = commentjson.load(file.open())
    counter = 1
    for char, pron2vocab in data.items():
        for pron, vocab in pron2vocab.items():
            words = []
            for v in vocab:
                word = Word(
                    surface=v["surface"],
                    id=f"override-{counter}",
                    pron=v["pron"],
                    english=v["en"],
                    frequency=v["freq"],
                )
                words.append(word)
                counter += 1
            pron2vocab[pron] = words
    return data


@cache
def get_unihan(file=UNIHAN_FILE) -> Mapping[str, Any]:
    __download_unihan()
    logger.info("Loading unihan data...")
    with open(file) as f:
        unihan = json.load(f)
    logger.info(f"  Read {len(unihan)} characters from Unihan DB")

    return unihan


@cache
def get_unihan_variants(file=GENERATED_DATA_DIR / "unihan.json"):
    unihan = get_unihan(file)
    logger.info("Constructing variants index from Unihan...")

    char_to_variants = defaultdict(set)
    for char, entry in unihan.items():
        for field_name in [
            "kSemanticVariant",
            "kZVariant",
            "kSimplifiedVariant",
            "kTraditionalVariant",
            "kReverseCompatibilityVariants",
            "kJinmeiyoKanji",
            "kJoyoKanji",
            "kCompatibilityVariant",
        ]:
            if variants := entry.get(field_name):
                if not isinstance(variants, list):
                    variants = [variants]
                for v in variants:
                    char_to_variants[char].add(v)

        # These are asymmetrically noted in Unihan, so
        # we need to reverse the mapping direction
        for field_name in ["kCompatibilityVariant", "kJinmeiyoKanji", "kJoyoKanji"]:
            if comp_variant := entry.get(field_name):
                if not isinstance(comp_variant, list):
                    comp_variant = [comp_variant]
                for v in comp_variant:
                    char_to_variants[v].add(char)

    return char_to_variants


@cache
def get_variants():
    char_to_variants = defaultdict(set)
    for char, variants in get_unihan_variants().items():
        char_to_variants[char].update(variants)
    for char, variants in get_ytenx_variants().items():
        char_to_variants[char].update(variants)

    return dict(char_to_variants)


@cache
def get_kengdic():
    # TODO: add separate download step
    logger.info("Loading kengdic data...")
    package = Package(KENGDIC_DATA_PACKAGE_URL)
    resource = package.get_resource("kengdic")
    if resource is None:
        raise ValueError("Could not load kengdic resource")
    data = resource.read(keyed=True)

    # No frequency data available, so we'll translate the level data to fake
    # frequencies to help
    level_to_frequency = {"A": 500, "B": 400, "C": 300, "D": 200}
    words = []
    for d in data:
        if d["hanja"] and d["gloss"]:
            if level := d["level"]:
                frequency = level_to_frequency[level]
            else:
                frequency = -1

            w = Word(
                d["hanja"],
                "kengdic-{id}".format(**d),
                d["surface"],
                d["gloss"],
                frequency,
            )
            words.append(w)

    logger.info(f"Loaded {len(words)} usable words from Kengdic")
    return sorted(words, key=lambda w: -w.frequency)


@cache
def get_chunom_org_vocab() -> List[Word]:
    with open(CHUNOM_VOCAB_FILE, "r") as f:
        rows = csv.DictReader(f, delimiter="\t")
        seen = set()
        words = []
        for r in rows:
            # skip character rows and only read vocab rows
            if r["Unicode"]:
                continue
            key = "{Text}/{QN}/{English}".format(**r)
            if key in seen:
                continue
            seen.add(key)
            w = Word(
                r["Text"],
                # remove trailing dot before converting to int
                "chunom.org-" + r["#"][:-1],
                r["QN"],
                r["English"],
                # negative so that we can use it as a sorting key
                -int(r["Freq."]),
            )
            words.append(w)
    return words
