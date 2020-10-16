import logging
import os
from pathlib import Path

from unihan_etl.process import Packager as unihan_packager

logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "INFO"),
    format="[%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).parents[1]
DATA_DIR = Path(PROJECT_DIR, "data")
DATA_DIR.mkdir(exist_ok=True)
UNIHAN_FILE = Path(DATA_DIR, "unihan.json")


def unihan_download():
    if UNIHAN_FILE.exists() and UNIHAN_FILE.stat().st_size > 0:
        log.info(f"{UNIHAN_FILE} already exists; skipping download")
        return

    log.info(f"Downloading unihan to {UNIHAN_FILE}...")
    p = unihan_packager.from_cli(["-F", "json", "--destination", str(UNIHAN_FILE)])
    p.download()
    p.export()


def main():
    unihan_download()


if __name__ == "__main__":
    main()
