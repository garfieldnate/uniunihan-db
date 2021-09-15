import csv
import json
import logging
import os
from json.encoder import JSONEncoder
from pathlib import Path
from typing import Any, Collection, Mapping, MutableMapping, TypeVar

from uniunihan_db.data_paths import GENERATED_DATA_DIR

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


def filter_keys(d: Mapping[T, U], s: Collection[T]) -> MutableMapping[T, U]:
    """Filter keys in d to just elements present in s"""
    return {k: v for k, v in d.items() if k in s}


class ExtendedJsonEncoder(JSONEncoder):
    """Serializes sets as sorted lists, and any other objects not handled by
    the default JSON decoder as dictionaries with their fields as the keys."""

    def default(self, obj: Any) -> object:
        try:
            return JSONEncoder.default(self, obj)
        except TypeError:
            if isinstance(obj, set):
                return sorted(list(obj))
            else:
                return vars(obj)


def format_json(data: object) -> str:
    return json.dumps(
        data,
        cls=ExtendedJsonEncoder,
        ensure_ascii=False,
        indent=2,
    )


def read_csv(path: Path) -> csv.DictReader:
    """Return a csv.DictReader, removing commented lines
    (which start with a #)."""
    csvfile = open(path, newline="")
    # skip comments
    return csv.DictReader(filter(lambda row: row[0] != "#", csvfile))


# TODO: move to datasets file?
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
