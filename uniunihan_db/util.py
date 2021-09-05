import logging
import os
from typing import Collection, Mapping, TypeVar

from uniunihan_db.constants import GENERATED_DATA_DIR

LOG_FILE = GENERATED_DATA_DIR / "log.txt"


def configure_logging(name: str) -> logging.Logger:
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

T = TypeVar("T")
U = TypeVar("U")


def filter_keys(d: Mapping[T, U], s: Collection[T]) -> Mapping[T, U]:
    """Filter keys in d to just elements present in s"""
    return {k: v for k, v in d.items() if k in s}


def get_mandarin_pronunciation(unihan_entry):
    # check all of the available fields in order of usefulness/accuracy
    if pron := unihan_entry.get("kHanyuPinlu"):
        #             print('returning pinlu')
        return [p["phonetic"] for p in pron]
    elif pron := unihan_entry.get("kXHC1983"):
        #             print('returning 1983')
        return [p["reading"] for p in pron]
    elif pron := unihan_entry.get("kHanyuPinyin"):
        #             print('returning pinyin!')
        return [r for p in pron for r in p["readings"]]
    elif pron := unihan_entry.get("kMandarin"):
        # print("returning mandarin!")
        return pron["zh-Hans"]
    return []
