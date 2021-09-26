import csv
import json
import sys
from json.encoder import JSONEncoder
from pathlib import Path
from typing import Any, Collection, Mapping, MutableMapping, TypeVar

from loguru import logger

from uniunihan_db.data.paths import GENERATED_DATA_DIR


def configure_logging(name):
    """Configure the core logger; write to stderr in color and to a log file in the generated data dir (using `name`
    in the file name)."""

    logger.configure(
        handlers=[
            dict(
                sink=sys.stderr, format="[<lvl>{level}</lvl>] {message}", level="INFO"
            ),
            dict(
                sink=GENERATED_DATA_DIR / f"debug-log-{name}.txt",
                format="[<lvl>{level}</lvl>] {name} line {line}: {message}",
                level="DEBUG",
                mode="w",
            ),
        ]
    )


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


def is_han(c):
    """Return true if the input is a han character, false otherwise"""
    return 0x4E00 <= ord(c) <= 0x9FFF
