import csv
import zipfile
from collections import defaultdict

import requests

from uniunihan_db.util import GENERATED_DATA_DIR, configure_logging

YTENX_URL = "https://github.com/BYVoid/ytenx/archive/master.zip"
YTENX_ZIP_FILE = GENERATED_DATA_DIR / "ytenx-master.zip"
YTENX_DIR = YTENX_ZIP_FILE.with_suffix("")
PHONETIC_COMPONENTS_FILE = GENERATED_DATA_DIR / "components_to_chars.tsv"

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


YTENX_RHYMES = None


def get_ytenx_rhymes():
    global YTENX_RHYMES
    if YTENX_RHYMES:
        return YTENX_RHYMES

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

    YTENX_RHYMES = char_to_component
    return YTENX_RHYMES


YTENX_VARIANTS = None


def get_ytenx_variants():
    global YTENX_VARIANTS
    if YTENX_VARIANTS:
        return YTENX_VARIANTS

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

    YTENX_VARIANTS = char_to_variants
    return char_to_variants
