import logging
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).parents[1]

DATA_DIR = PROJECT_DIR / "data"

GENERATED_DATA_DIR = DATA_DIR / "generated"
GENERATED_DATA_DIR.mkdir(exist_ok=True)

INCLUDED_DATA_DIR = DATA_DIR / "included"

LOG_FILE = GENERATED_DATA_DIR / "log.txt"


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
