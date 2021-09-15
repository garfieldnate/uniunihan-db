from pathlib import Path
from typing import Any, Collection, Tuple, Union

import pytest

from uniunihan_db.lingua import japanese
from uniunihan_db.util import read_csv

CODE_DIR = Path(__file__).parents[0]


def idfn(val: Union[object, str]) -> str:
    if isinstance(val, str):
        return "empty string" if not len(val) else val
    else:
        return str(val)


def pytest_generate_tests(metafunc: Any) -> None:
    if "hepburn" in metafunc.fixturenames:
        data = read_hepburn_test_data()
        metafunc.parametrize("hepburn,expected", data, ids=idfn)
    elif "expected_ime" in metafunc.fixturenames:
        data = read_ime_test_data()
        metafunc.parametrize("kana,expected_ime", data, ids=idfn)


def read_hepburn_test_data() -> Collection[Tuple[str, str]]:
    data_csv = CODE_DIR / "romaji_kanaization.csv"
    data = []

    reader = read_csv(data_csv)
    for row in reader:
        data.append((row["hepburn"], row["hiragana"]))
    return data


def read_ime_test_data() -> Collection[Tuple[str, str]]:
    data_csv = CODE_DIR / "kana_romanization.csv"
    data = []

    reader = read_csv(data_csv)
    for row in reader:
        data.append((row["hiragana"], row["IME"]))
    return data


###### Tests ######


def test_hepburn_to_kana(hepburn: str, expected: str) -> None:
    actual = japanese.alpha_to_kana(hepburn)
    assert actual == expected


def test_kana_to_ime(kana: str, expected_ime: str) -> None:
    actual = japanese.kana_to_alpha(kana)
    assert actual == expected_ime


@pytest.mark.parametrize(
    "input,expected",
    [("katsu", "katu"), ("jachunfu", "zyatyunhu"), ("saan'i", "saan'i")],
)
def test_hepburn_to_ime(input: str, expected: str) -> None:
    actual = japanese.alpha_to_alpha(input)
    assert actual == expected


@pytest.mark.parametrize(
    "input,onset,semivowel,vowel,coda,epenthetic_vowel,rhyme",
    [
        ("kyatu", "k", "y", "a", "t", "u", "yat"),
        ("piti", "p", "", "i", "t", "i", "it"),
        ("ban", "b", "", "a", "n", "", "an"),
        ("doku", "d", "", "o", "k", "u", "ok"),
        ("osu", "", "", "o", "s", "u", "os"),
        ("kou", "k", "", "ou", "", "", "ou"),
        ("ryuu", "r", "y", "uu", "", "", "yuu"),
        ("watu", "", "w", "a", "t", "u", "wat"),
        ("kamu", "k", "", "a", "m", "u", "am"),
        ("ani", "", "", "a", "n", "i", "an"),
        ("kuwa", "k", "w", "a", "", "", "wa"),
        ("hiyaku", "h", "y", "a", "k", "u", "yak"),
        ("habi", "h", "", "a", "b", "i", "ab"),
        # uppercase with whitespace
        (" HATi  ", "h", "", "a", "t", "i", "at"),
    ],
)
def test_parse_legal_han_syllable(
    input: str,
    onset: str,
    semivowel: str,
    vowel: str,
    coda: str,
    epenthetic_vowel: str,
    rhyme: str,
) -> None:
    actual = japanese.parse_han_syllable(input)
    assert actual is not None
    assert actual.surface == input.strip().lower()
    assert actual.onset == onset
    assert actual.semivowel == semivowel
    assert actual.vowel == vowel
    assert actual.coda == coda
    assert actual.epenthetic_vowel == epenthetic_vowel
    assert actual.rhyme == rhyme


def test_parse_nonce_han_syllable() -> None:
    syl = japanese.parse_han_syllable("xyadfs")
    assert syl is None
