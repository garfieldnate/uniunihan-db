import csv
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


log = configure_logging(__name__)


def read_joyo():
    log.info("Loading joyo data...")
    new_char_to_prons = {}
    old_char_to_prons = {}
    char_to_supplementary_info = {}
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
            }
            # remove empty readings
            readings = [yomi for yomi in r["on-yomi"].split("|") if yomi]
            # note the non-Joyo readings and strip the indicator asterisk
            supplementary_info["non-joyo"] = [
                yomi[:-1] for yomi in readings if yomi[-1] == "*"
            ]
            readings = [yomi.rstrip("*") for yomi in readings if yomi]
            supplementary_info["readings"] = sorted(readings)

            for c in r["new"]:
                new_char_to_prons[c] = readings
                char_to_supplementary_info[c] = supplementary_info
            # old glyph same as new glyph when missing
            for c in r["old"] or r["new"]:
                old_char_to_prons[c] = readings
                char_to_supplementary_info[c] = dict(supplementary_info)
            # handle multiple old characters case (弁/辨瓣辯辦辮)
            if old := r["old"]:
                for old_c in old:
                    char_to_supplementary_info[old_c]["old"] = old_c
                    for new_c in r["new"]:
                        # put all of the kyuujitai in 弁's 'old' field
                        if new_c == "弁":
                            char_to_supplementary_info[new_c]["old"] = old
                        else:
                            char_to_supplementary_info[new_c]["old"] = old_c

    return old_char_to_prons, new_char_to_prons, char_to_supplementary_info
