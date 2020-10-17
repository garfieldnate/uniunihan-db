import csv
from pathlib import Path

from uniunihan_db.lingua import japanese

CODE_DIR = Path(__file__).parents[0]


def idfn(val):
    if type(val) == str:
        return "empty string" if not len(val) else val
    else:
        return str(val)


def pytest_generate_tests(metafunc):
    if "hepburn" in metafunc.fixturenames:
        data = read_hepburn_test_data()
        metafunc.parametrize("hepburn,expected", data, ids=idfn)


def read_hepburn_test_data():
    data_csv = Path(CODE_DIR, "hepburn_to_kana.csv")
    data = []

    reader = read_csv(data_csv)
    for row in reader:
        data.append((row["hepburn"], row["hiragana"]))
    return data


def read_csv(path: Path) -> csv.DictReader:
    csvfile = open(path, newline="")
    # skip comments
    return csv.DictReader(filter(lambda row: row[0] != "#", csvfile))


###### Tests ######


def test_split_hepburn(hepburn, expected):
    actual = japanese.to_kana(hepburn)
    assert actual == expected
