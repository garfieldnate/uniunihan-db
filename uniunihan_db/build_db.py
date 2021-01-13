import csv
import dataclasses
import json
import tarfile
import zipfile
from collections import defaultdict

import jaconv
import requests
from unihan_etl.process import Packager as unihan_packager
from unihan_etl.process import export_json

from .lingua import japanese, mandarin
from .util import GENERATED_DATA_DIR, INCLUDED_DATA_DIR, configure_logging

UNIHAN_FILE = GENERATED_DATA_DIR / "unihan.json"
UNIHAN_AUGMENTATION_FILE = GENERATED_DATA_DIR / "unihan_augmentation.json"

YTENX_URL = "https://github.com/BYVoid/ytenx/archive/master.zip"
YTENX_ZIP_FILE = GENERATED_DATA_DIR / "ytenx-master.zip"
YTENX_DIR = YTENX_ZIP_FILE.with_suffix("")

EDICT_FREQ_URL = "http://ftp.monash.edu.au/pub/nihongo/edict-freq-20081002.tar.gz"
EDICT_FREQ_TARBALL = GENERATED_DATA_DIR / "edict-freq-20081002.tar.gz"
EDICT_FREQ_DIR = EDICT_FREQ_TARBALL.with_suffix("").with_suffix("")

PHONETIC_COMPONENTS_FILE = GENERATED_DATA_DIR / "chars_to_components.tsv"

JUN_DA_CHAR_FREQ_URL = (
    "https://lingua.mtsu.edu/chinese-computing/statistics/char/list.php"
)
JUN_DA_CHAR_FREQ_FILE = GENERATED_DATA_DIR / "jun_da_char.tsv"

log = configure_logging(__name__)

# lazy load this, since it's a lot of data
UNIHAN_DICT = None


def get_unihan():
    global UNIHAN_DICT
    if not UNIHAN_DICT:
        log.info("Reading in Unihan DB...")
        with open(UNIHAN_FILE) as f:
            UNIHAN_DICT = json.load(f)
        log.info(f"  Read {len(UNIHAN_DICT)} characters from Unihan DB")
    return UNIHAN_DICT


def unihan_download():
    """Download the famous Unihan database from the Unicode Consortium,
    and store it has a normalized JSON file"""

    if UNIHAN_FILE.exists() and UNIHAN_FILE.stat().st_size > 0:
        log.info(f"{UNIHAN_FILE.name} already exists; skipping download")
        return

    log.info("  Downloading unihan data...")
    p = unihan_packager.from_cli(["-F", "json", "--destination", str(UNIHAN_FILE)])
    p.download()
    # instruct packager to return data instead of writing to file
    # https://github.com/cihai/unihan-etl/issues/233
    p.options["format"] = "python"
    unihan = p.export()

    log.info("  Converting unihan data to dictionary format...")
    unihan_dict = {entry["char"]: entry for entry in unihan}

    log.info("  Simplifying variant fields...")
    for d in unihan_dict.values():
        # TODO: address duplication below
        if compat_variant := d.get("kCompatibilityVariant"):
            codepoint = compat_variant[2:]
            char = chr(int(codepoint, 16))
            d["kCompatibilityVariant"] = char
        for field_name in [
            "kSemanticVariant",
            "kZVariant",
            "kSimplifiedVariant",
            "kTraditionalVariant",
        ]:
            if variants := d.get(field_name, []):
                new_variants = []
                for v in variants:
                    # https://github.com/cihai/unihan-etl/issues/80#issuecomment-757470998
                    codepoint = v.split("<")[0][2:]
                    char = chr(int(codepoint, 16))
                    new_variants.append(char)
                d[field_name] = new_variants
        # slightly different structure
        if jinmeiyo := d.get("kJinmeiyoKanji", []):
            new_variants = []
            for variant in jinmeiyo:
                if "U+" in variant:
                    codepoint = variant[7:]
                    char = chr(int(codepoint, 16))
                    new_variants.append(char)
            d["kJinmeiyoKanji"] = new_variants
        if joyo := d.get("kJoyoKanji"):
            new_variants = []
            for variant in joyo:
                if "U+" in variant:
                    codepoint = variant[2:]
                    char = chr(int(codepoint, 16))
                    new_variants.append(char)
            d["kJoyoKanji"] = new_variants

    log.info(f"  Writing unihan to {UNIHAN_FILE}...")
    export_json(unihan_dict, UNIHAN_FILE)
    global UNIHAN_DICT
    UNIHAN_DICT = unihan_dict


def ytenx_download():
    """Download and unzip the ytenx rhyming data."""
    # download
    if YTENX_ZIP_FILE.exists() and YTENX_ZIP_FILE.stat().st_size > 0:
        log.info(f"{YTENX_ZIP_FILE.name} already exists; skipping download")
    else:
        log.info(f"Downloading ytenx rhyming data to {YTENX_ZIP_FILE}...")
        r = requests.get(YTENX_URL, stream=True)
        with open(YTENX_ZIP_FILE, "wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

    # unzip
    if YTENX_DIR.exists() and YTENX_DIR.is_dir():
        log.info(f"  {YTENX_DIR.name} already exists; skipping unzip")
    else:
        with zipfile.ZipFile(YTENX_ZIP_FILE, "r") as zip_ref:
            zip_ref.extractall(GENERATED_DATA_DIR)


def edict_freq_download():
    """Download, unzip and reformat Utsumi Hiroshi's frequency-annotated EDICT"""

    # download
    if EDICT_FREQ_TARBALL.exists() and EDICT_FREQ_TARBALL.stat().st_size > 0:
        log.info(f"{EDICT_FREQ_TARBALL.name} already exists; skipping download")
    else:
        log.info(f"Downloading frequency-annotated EDICT to {EDICT_FREQ_TARBALL}...")
        r = requests.get(EDICT_FREQ_URL, stream=True)
        with open(EDICT_FREQ_TARBALL, "wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

    # unzip
    if EDICT_FREQ_DIR.exists() and EDICT_FREQ_DIR.is_dir():
        log.info(f"  {EDICT_FREQ_DIR.name} already exists; skipping decompress")
    else:
        tar = tarfile.open(EDICT_FREQ_TARBALL, "r:gz")
        tar.extractall(GENERATED_DATA_DIR)
        tar.close()

    words = []
    with open(EDICT_FREQ_DIR / "edict-freq-20081002") as f:
        for line in f.readlines()[1:]:
            word = line.split(" ")[0]
            freq = int(line.split("#")[-1][:-2])
            if "[" not in line:
                # line contains no kanji
                continue
            pron = line.split("[")[1].split("]")[0]
            # use Katakana to match other phonetic sources
            pron_katakana = jaconv.hira2kata(pron)
            # negative frequency to sort descending
            words.append((-freq, word, pron_katakana))

    with open(GENERATED_DATA_DIR / "edict-freq.tsv", "w") as f:
        for entry in sorted(words):
            f.write(f"{entry[1]}\t{entry[2]}")
            f.write("\n")


def write_phonetic_components():
    """Extract and augment the phonetic component data in ytenx"""

    if (
        PHONETIC_COMPONENTS_FILE.exists()
        and PHONETIC_COMPONENTS_FILE.stat().st_size > 0
    ):
        log.info(f"{PHONETIC_COMPONENTS_FILE.name} already exists; skipping creation")
        return

    variants = get_variants()

    log.info("Loading phonetic components from ytenx...")
    char_to_component = {}
    with open(YTENX_DIR / "ytenx" / "sync" / "dciangx" / "DrienghTriang.txt") as f:
        rows = csv.DictReader(f, delimiter=" ")
        for r in rows:
            char = r["#字"]
            component = r["聲符"]
            char_to_component[char] = component
    with open(INCLUDED_DATA_DIR / "manual_components.json") as f:
        extra_char_to_components = json.load(f)
        char_to_component.update(extra_char_to_components)

    log.info("  Addding phonetic components for variants...")
    variant_to_component = {}
    for char in char_to_component:
        for c in variants.get(char, []):
            if c not in char_to_component:
                variant_to_component[c] = char_to_component[char]
    char_to_component.update(variant_to_component)

    log.info(f"  Writing phonetic components to {PHONETIC_COMPONENTS_FILE}")
    with open(PHONETIC_COMPONENTS_FILE, "w") as f:
        f.write("character\tcomponent\n")
        for character, component in char_to_component.items():
            f.write(f"{character}\t{component}\n")
    log.info(f"  Wrote {len(char_to_component)} character/component pairs")

    return char_to_component


def jun_da_char_freq_download():
    """Download and save Jun Da's character frequency list"""
    # TODO: this thing is super fragile. Would be better to create and distribute
    # a data package version of the list somewhere.

    if JUN_DA_CHAR_FREQ_FILE.exists() and JUN_DA_CHAR_FREQ_FILE.stat().st_size > 0:
        log.info(f"{JUN_DA_CHAR_FREQ_FILE.name} already exists; skipping download")
        return

    log.info(
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

            log.info(
                f"  Writing Jun Da's character frequency list to {JUN_DA_CHAR_FREQ_FILE}"
            )
            with open(JUN_DA_CHAR_FREQ_FILE, "w") as f:
                f.write(
                    "Rank\tCharacter\tRaw Frequency\tFrequency Percentile\tPinyin\tEnglish\n"
                )
                for entry in line.split("<br>"):
                    if entry:
                        f.write(entry)
                        f.write("\n")


def get_variants():
    unihan = get_unihan()
    log.info("Constructing variants index...")

    log.info("  Reading variants from unihan...")
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
                if type(variants) != list:
                    variants = [variants]
                for v in variants:
                    char_to_variants[char].add(v)

        # These are asymmetrically noted in Unihan, so we need to reverse the mapping direction
        for field_name in ["kCompatibilityVariant", "kJinmeiyoKanji", "kJoyoKanji"]:
            if comp_variant := entry.get(field_name):
                if type(comp_variant) != list:
                    comp_variant = [comp_variant]
                for v in comp_variant:
                    char_to_variants[v].add(char)

    log.info("  Reading variants from ytenx...")
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


def expand_unihan():
    """Expand Unihan DB with the following data:
    * Kana and IME spellings for Japanese on'yomi
    * On'yomi and Mandarin syllable analyses (for testing purposes)
    * Reverse compatibility variant references"""

    unihan = get_unihan()

    log.info("Expanding Unihan data...")
    new_data = {}
    reverse_compatibilities = defaultdict(list)
    for key, entry in unihan.items():
        new_data[key] = {}
        if on_list := entry.get("kJapaneseOn"):
            kana_list = []
            ime_list = []
            parsed_list = []
            for on in on_list:
                kana = japanese.alpha_to_kana(on)
                ime = japanese.kana_to_alpha(kana)
                try:
                    han_syl = japanese.parse_han_syllable(ime)
                    han_syl = dataclasses.asdict(han_syl)
                    parsed_list.append(han_syl)
                except TypeError:
                    log.warn(
                        f"  {entry['char']}/{on}/romanization={ime}: Failed to parse Han syllable!"
                    )
                    parsed_list.append(None)
                kana_list.append(kana)
                ime_list.append(ime)
            new_data[key] |= {
                "kJapaneseOn_kana": kana_list,
                "kJapaneseOn_ime": ime_list,
                "kJapaneseOn_parsed": parsed_list,
            }
        if pinyin_dict := entry.get("kMandarin"):
            parsed_dict = {}
            for k, v in pinyin_dict.items():
                try:
                    syl = mandarin.parse_syllable(v)
                    syl = dataclasses.asdict(syl)
                    parsed_dict[k] = syl
                except TypeError:
                    log.warn(
                        f"{entry['char']}/{k}={v}: Failed to parse pinyin syllable!"
                    )
                    parsed_dict[k] = None
            new_data[key] |= {"kMandarin_parsed": parsed_dict}
        for field_name in ["kCompatibilityVariant", "kJinmeiyoKanji", "kJoyoKanji"]:
            if comp_variant := entry.get(field_name):
                if type(comp_variant) != list:
                    comp_variant = [comp_variant]
                for v in comp_variant:
                    reverse_compatibilities[v].extend(key)

    for key, variants in reverse_compatibilities.items():
        new_data[key]["kReverseCompatibilityVariants"] = variants

    log.info(f"  Writing Unihan augmentations to {UNIHAN_AUGMENTATION_FILE.name}...")
    export_json(new_data, UNIHAN_AUGMENTATION_FILE)


def main():
    unihan_download()
    ytenx_download()
    edict_freq_download()
    write_phonetic_components()
    jun_da_char_freq_download()

    # expand_unihan()


if __name__ == "__main__":
    main()
