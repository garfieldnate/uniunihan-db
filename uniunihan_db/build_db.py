import json
import logging
import os
import zipfile
from pathlib import Path

import requests
from unihan_etl.process import Packager as unihan_packager

from .lingua import japanese

logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "INFO"),
    format="[%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).parents[1]
DATA_DIR = Path(PROJECT_DIR, "data")
DATA_DIR.mkdir(exist_ok=True)
UNIHAN_FILE = Path(DATA_DIR, "unihan.json")
UNIHAN_AUGMENTATION_FILE = Path(DATA_DIR, "unihan_augmentation.json")
CJKVI_IDS_URL = "https://github.com/cjkvi/cjkvi-ids/archive/master.zip"
CJKV_IDS_ZIP_FILE = Path(DATA_DIR, "cjkvi-ids-master.zip")
CJKV_IDS_DIR = Path(DATA_DIR, "cjkvi-ids-master")


def unihan_download():
    """Download the famous Unihan database, from the Unicode Consortium,
    and store it has a normalized JSON file"""

    if UNIHAN_FILE.exists() and UNIHAN_FILE.stat().st_size > 0:
        log.info(f"{UNIHAN_FILE.name} already exists; skipping download")
        return

    log.info(f"Downloading unihan to {UNIHAN_FILE}...")
    p = unihan_packager.from_cli(["-F", "json", "--destination", str(UNIHAN_FILE)])
    p.download()
    p.export()


def cjkvi_ids_download():
    """Download and unzip the CJKV IDS database. As it is better formatted
    and actively maintained, cjkdecomp recommended using this instead
    of itself."""
    # download
    if CJKV_IDS_ZIP_FILE.exists() and CJKV_IDS_ZIP_FILE.stat().st_size > 0:
        log.info(f"{CJKV_IDS_ZIP_FILE.name} already exists; skipping download")
    else:
        log.info(f"Downloading CJKV-IDS to {CJKV_IDS_ZIP_FILE}...")
        r = requests.get(CJKVI_IDS_URL, stream=True)
        with open(CJKV_IDS_ZIP_FILE, "wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

    # unzip
    if CJKV_IDS_DIR.exists() and CJKV_IDS_DIR.is_dir():
        log.info(f"{CJKV_IDS_DIR.name} already exists; skipping unzip")
    else:
        with zipfile.ZipFile(CJKV_IDS_ZIP_FILE, "r") as zip_ref:
            zip_ref.extractall(DATA_DIR)


def expand_unihan():
    """Write Kana and IME spellings for Japanese on'yomi in Unihan DB"""

    log.info("Reading in Unihan DB...")
    with open(UNIHAN_FILE) as f:
        unihan = json.load(f)

    log.info("Expanding kJapaneseOn spellings...")
    new_data = {}
    for entry in unihan:
        if on_list := entry.get("kJapaneseOn"):
            kana_list = []
            ime_list = []
            for on in on_list:
                kana = japanese.alpha_to_kana(on)
                ime = japanese.kana_to_alpha(kana)
                kana_list.append(kana)
                ime_list.append(ime)
            key = entry["ucn"]
            new_data[key] = {"kJapaneseOn_kana": kana_list, "kJapaneseOn_ime": ime_list}

    log.info(f"Writing Unihan augmentations to {UNIHAN_AUGMENTATION_FILE.name}...")
    with open(UNIHAN_AUGMENTATION_FILE, "w") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)


def main():
    unihan_download()
    cjkvi_ids_download()
    expand_unihan()


if __name__ == "__main__":
    main()
