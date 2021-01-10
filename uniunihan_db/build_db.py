import dataclasses
import json
import zipfile
from collections import defaultdict

import requests
from unihan_etl.process import Packager as unihan_packager
from unihan_etl.process import export_json

from .lingua import japanese, mandarin
from .util import GENERATED_DATA_DIR, configure_logging

UNIHAN_FILE = GENERATED_DATA_DIR / "unihan.json"
UNIHAN_AUGMENTATION_FILE = GENERATED_DATA_DIR / "unihan_augmentation.json"
REVERSE_COMPAT_VARIANTS_FILE = (
    GENERATED_DATA_DIR / "reverse_compatibility_variants.json"
)

CJKVI_IDS_URL = "https://github.com/cjkvi/cjkvi-ids/archive/master.zip"
CJKVI_IDS_ZIP_FILE = GENERATED_DATA_DIR / "cjkvi-ids-master.zip"
CJKVI_IDS_DIR = GENERATED_DATA_DIR / "cjkvi-ids-master"

YTENX_URL = "https://github.com/BYVoid/ytenx/archive/master.zip"
YTENX_ZIP_FILE = GENERATED_DATA_DIR / "ytenx-master.zip"
YTENX_DIR = GENERATED_DATA_DIR / "ytenx-master"

JUN_DA_CHAR_FREQ_URL = (
    "https://lingua.mtsu.edu/chinese-computing/statistics/char/list.php"
)
JUN_DA_CHAR_FREQ_FILE = GENERATED_DATA_DIR / "jun_da_char.tsv"

log = configure_logging(__name__)


def unihan_download():
    """Download the famous Unihan database from the Unicode Consortium,
    and store it has a normalized JSON file"""

    if UNIHAN_FILE.exists() and UNIHAN_FILE.stat().st_size > 0:
        log.info(f"{UNIHAN_FILE.name} already exists; skipping download")
        return

    log.info("Downloading unihan data...")
    p = unihan_packager.from_cli(["-F", "json", "--destination", str(UNIHAN_FILE)])
    p.download()
    # instruct packager to return data instead of writing to file
    # https://github.com/cihai/unihan-etl/issues/233
    p.options["format"] = "python"
    unihan = p.export()

    log.info("Converting unihan data to dictionary format...")
    unihan_dict = {entry["char"]: entry for entry in unihan}

    log.info("Simplifying variant fields...")
    for d in unihan_dict.values():
        # TODO: address duplication below
        # TODO: write reverse compatibility variants, since they are not symmetric
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

    log.info(f"Writing unihan to {UNIHAN_FILE}...")
    export_json(unihan_dict, UNIHAN_FILE)


def cjkvi_ids_download():
    """Download and unzip the CJKV IDS data."""
    # download
    if CJKVI_IDS_ZIP_FILE.exists() and CJKVI_IDS_ZIP_FILE.stat().st_size > 0:
        log.info(f"{CJKVI_IDS_ZIP_FILE.name} already exists; skipping download")
    else:
        log.info(f"Downloading CJKV-IDS to {CJKVI_IDS_ZIP_FILE}...")
        r = requests.get(CJKVI_IDS_URL, stream=True)
        with open(CJKVI_IDS_ZIP_FILE, "wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

    # unzip
    if CJKVI_IDS_DIR.exists() and CJKVI_IDS_DIR.is_dir():
        log.info(f"{CJKVI_IDS_DIR.name} already exists; skipping unzip")
    else:
        with zipfile.ZipFile(CJKVI_IDS_ZIP_FILE, "r") as zip_ref:
            zip_ref.extractall(GENERATED_DATA_DIR)


def ytenx_download():
    """Download and unzip the ytenx rhyming data."""
    # TODO: duplicated code with cjkvi_ids_download
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
        log.info(f"{YTENX_DIR.name} already exists; skipping unzip")
    else:
        with zipfile.ZipFile(YTENX_ZIP_FILE, "r") as zip_ref:
            zip_ref.extractall(GENERATED_DATA_DIR)


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
                f"Writing Jun Da's character frequency list to {JUN_DA_CHAR_FREQ_FILE}"
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

    log.info("Reading in Unihan DB...")
    with open(UNIHAN_FILE) as f:
        unihan = json.load(f)
    log.info(f"Read {len(unihan)} characters from Unihan DB")

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
                        f"{entry['char']}/{on}/romanization={ime}: Failed to parse Han syllable!"
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
        if comp_variant := entry.get("kCompatibilityVariant"):
            reverse_compatibilities[comp_variant].append(key)

    for key, variants in reverse_compatibilities.items():
        new_data[key]["kReverseCompatibilityVariants"] = variants

    log.info(
        f"Writing reverse compatibility variants to {REVERSE_COMPAT_VARIANTS_FILE.name}..."
    )
    with open(REVERSE_COMPAT_VARIANTS_FILE, "w") as f:
        json.dump(reverse_compatibilities, f, indent=2, ensure_ascii=False)

    log.info(f"Writing Unihan augmentations to {UNIHAN_AUGMENTATION_FILE.name}...")
    with open(UNIHAN_AUGMENTATION_FILE, "w") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)


def main():
    unihan_download()
    cjkvi_ids_download()
    ytenx_download()
    jun_da_char_freq_download()

    expand_unihan()


if __name__ == "__main__":
    main()
