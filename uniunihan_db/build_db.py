import dataclasses
import tarfile
import zipfile
from collections import defaultdict

# allows commenting lines with # or //
import commentjson as json
import jaconv
import requests
from unihan_etl.process import Packager as unihan_packager
from unihan_etl.process import export_json

from uniunihan_db.constants import GENERATED_DATA_DIR, INCLUDED_DATA_DIR

from .data.datasets import (
    HK_ED_CHARS_FILE,
    KO_ED_CHARS_FILE,
    get_unihan,
    get_variants,
    get_ytenx_rhymes,
)
from .lingua import japanese, mandarin
from .util import configure_logging

UNIHAN_FILE = GENERATED_DATA_DIR / "unihan.json"
UNIHAN_AUGMENTATION_FILE = GENERATED_DATA_DIR / "unihan_augmentation.json"

LIB_HANGUL_URL = "https://github.com/libhangul/libhangul/archive/master.zip"
LIB_HANGUL_ZIP_FILE = GENERATED_DATA_DIR / "libhangul-master.zip"
LIB_HANGUL_DIR = LIB_HANGUL_ZIP_FILE.with_suffix("")

EDICT_FREQ_URL = "http://ftp.monash.edu.au/pub/nihongo/edict-freq-20081002.tar.gz"
EDICT_FREQ_TARBALL = GENERATED_DATA_DIR / "edict-freq-20081002.tar.gz"
EDICT_FREQ_DIR = EDICT_FREQ_TARBALL.with_suffix("").with_suffix("")
SIMPLIFIED_EDICT_FREQ = GENERATED_DATA_DIR / "edict-freq.tsv"

PHONETIC_COMPONENTS_FILE = GENERATED_DATA_DIR / "components_to_chars.tsv"

JUN_DA_CHAR_FREQ_URL = (
    "https://lingua.mtsu.edu/chinese-computing/statistics/char/list.php"
)
JUN_DA_CHAR_FREQ_FILE = GENERATED_DATA_DIR / "jun_da_char.tsv"

CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip"
CEDICT_ZIP = GENERATED_DATA_DIR / "cedict_1_0_ts_utf-8_mdbg.zip"
CEDICT_DIR = CEDICT_ZIP.with_suffix("")

log = configure_logging(__name__)


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


def edict_freq_download():
    """Download and unzip Utsumi Hiroshi's frequency-annotated EDICT"""

    # download
    if EDICT_FREQ_TARBALL.exists() and EDICT_FREQ_TARBALL.stat().st_size > 0:
        log.info(f"{EDICT_FREQ_TARBALL.name} already exists; skipping download")
    else:
        log.info(
            f"Downloading frequency-annotated EDICT to {EDICT_FREQ_TARBALL.name}..."
        )
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


def cedict_download():
    """Download and unzip CC-CEDICT"""

    # download
    if CEDICT_ZIP.exists() and CEDICT_ZIP.stat().st_size > 0:
        log.info(f"{CEDICT_ZIP.name} already exists; skipping download")
    else:
        log.info(f"Downloading CC-CEDICT to {CEDICT_ZIP.name}...")
        r = requests.get(CEDICT_URL, stream=True)
        with open(CEDICT_ZIP, "wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

    CEDICT_DIR = CEDICT_ZIP.with_suffix("")
    # unzip
    if CEDICT_DIR.exists() and CEDICT_DIR.stat().st_size > 0:
        log.info(f"  {CEDICT_DIR.name} already exists; skipping decompress")
    else:
        log.info(f"  Writing decompressed contents to {CEDICT_DIR.name}")
        with zipfile.ZipFile(CEDICT_ZIP, "r") as zip_ref:
            zip_ref.extractall(CEDICT_DIR)


def edict_freq_format():
    """Write a simplified version of the edict frequency document"""

    log.info(f"Simplifying data in {EDICT_FREQ_DIR.name}...")
    words = []
    with open(EDICT_FREQ_DIR / "edict-freq-20081002") as f:
        for line in f.readlines()[1:]:
            word = line.split(" ")[0]
            word_normalized = jaconv.hira2kata(word)
            freq = int(line.split("#")[-1][:-2])
            english = "/".join(line.split("/")[1:-2])
            if "[" not in line:
                # line contains no kanji
                continue
            pron = line.split("[")[1].split("]")[0]
            # use Katakana to match other phonetic sources
            pron_katakana = jaconv.hira2kata(pron)
            # negative frequency to sort descending
            words.append((-freq, word, word_normalized, pron_katakana, english))

    log.info(f"  Writing {SIMPLIFIED_EDICT_FREQ.name}...")
    with open(SIMPLIFIED_EDICT_FREQ, "w") as f:
        for entry in sorted(words):
            f.write("\t".join(entry[1:]))
            f.write("\t")
            f.write(str(-entry[0]))
            f.write("\n")


def write_phonetic_components():
    """Extract and augment the phonetic component data in ytenx"""

    if (
        PHONETIC_COMPONENTS_FILE.exists()
        and PHONETIC_COMPONENTS_FILE.stat().st_size > 0
    ):
        log.info(f"{PHONETIC_COMPONENTS_FILE.name} already exists; skipping creation")
        return

    log.info("Determining phonetic components...")

    ytenx_rhyme_data = get_ytenx_rhymes()
    char_to_component = {char: info[0]["聲符"] for char, info in ytenx_rhyme_data.items()}

    with open(INCLUDED_DATA_DIR / "manual_components.json") as f:
        extra_char_to_components = json.load(f)
        char_to_component.update(extra_char_to_components)

    variants = get_variants()
    log.info("  Addding phonetic components for variants...")
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

    log.info(f"  Writing phonetic components to {PHONETIC_COMPONENTS_FILE}")
    with open(PHONETIC_COMPONENTS_FILE, "w") as f:
        f.write("component\tcharacters\n")
        for component, chars in component_to_chars.items():
            chars = "".join(chars)
            f.write(f"{component}\t{chars}\n")
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


def write_hk_ed_chars():
    if HK_ED_CHARS_FILE.exists() and HK_ED_CHARS_FILE.stat().st_size > 0:
        log.info(f"{HK_ED_CHARS_FILE.name} already exists; skipping unihan scan")
        return
    log.info("Scanning Unihan for Hong Kong educational character list...")

    unihan = get_unihan()
    chars = []
    for char, info in unihan.items():
        if "kGradeLevel" in info:
            chars.append(char)

    export_json(chars, HK_ED_CHARS_FILE)
    log.info(f"  Wrote {len(chars)} characters to {HK_ED_CHARS_FILE.name}")


def write_ko_ed_chars():
    if KO_ED_CHARS_FILE.exists() and KO_ED_CHARS_FILE.stat().st_size > 0:
        log.info(f"{KO_ED_CHARS_FILE.name} already exists; skipping unihan scan")
        return
    log.info("Scanning Unihan for Korea educational character list...")

    unihan = get_unihan()
    chars = []
    for char, info in unihan.items():
        if "kKoreanEducationHanja" in info:
            chars.append(char)

    export_json(chars, KO_ED_CHARS_FILE)
    log.info(f"  Wrote {len(chars)} characters to {KO_ED_CHARS_FILE.name}")


def hanja_wordlist_download():
    """Download and unzip the libhangul hanja data."""
    # download
    if LIB_HANGUL_ZIP_FILE.exists() and LIB_HANGUL_ZIP_FILE.stat().st_size > 0:
        log.info(f"{LIB_HANGUL_ZIP_FILE.name} already exists; skipping download")
    else:
        log.info(f"Downloading libhangul to {LIB_HANGUL_ZIP_FILE}...")
        r = requests.get(LIB_HANGUL_URL, stream=True)
        with open(LIB_HANGUL_ZIP_FILE, "wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

    # unzip
    if LIB_HANGUL_DIR.exists() and LIB_HANGUL_DIR.is_dir():
        log.info(f"  {LIB_HANGUL_DIR.name} already exists; skipping unzip")
    else:
        with zipfile.ZipFile(LIB_HANGUL_ZIP_FILE, "r") as zip_ref:
            zip_ref.extractall(GENERATED_DATA_DIR)


def main():
    unihan_download()

    write_phonetic_components()

    edict_freq_download()
    edict_freq_format()

    jun_da_char_freq_download()

    cedict_download()

    hanja_wordlist_download()

    # expand_unihan()
    write_hk_ed_chars()
    write_ko_ed_chars()


if __name__ == "__main__":
    main()
