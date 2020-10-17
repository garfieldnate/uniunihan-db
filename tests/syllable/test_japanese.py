import pytest

from uniunihan_db.syllable import japanese

hepburn_syllable_split_testdata = [
    # empty
    ("", []),
    # 1 syllable
    ("ka", ["ka"]),
    # digraphs
    ("tsutsu", ["tsu", "tsu"]),
    ("chichi", ["chi", "chi"]),
    ("shishi", ["shi", "shi"]),
    # 2 syllables
    ("jojo", ["jo", "jo"]),
    ("kara", ["ka", "ra"]),
    # syllable-final nasal
    ("karan", ["ka", "ran"]),
    # same, followed by consonant
    ("karanda", ["ka", "ran", "da"]),
    # n used as initial
    ("kanada", ["ka", "na", "da"]),
    # uppercase
    ("KANADA", ["KA", "NA", "DA"]),
    # all consonants
    (
        "akasatanahamayarawan",
        ["a", "ka", "sa", "ta", "na", "ha", "ma", "ya", "ra", "wan"],
    ),
    ("ikishichinihimirin", ["i", "ki", "shi", "chi", "ni", "hi", "mi", "rin"]),
    ("ukusutsunufumuyurun", ["u", "ku", "su", "tsu", "nu", "fu", "mu", "yu", "run"]),
    # long vowels
    ("apaato", ["a", "paa", "to"]),
    ("ruumumeeto", ["ruu", "mu", "mee", "to"]),
    ("ookami", ["oo", "ka", "mi"]),
    # diphthongs
    ("keisanki", ["kei", "san", "ki"]),
    ("ousama", ["ou", "sa", "ma"]),
    ("oishii", ["oi", "shii"]),
    ("deau", ["de", "au"]),
    # adjacent vowels; actually not sure about these 🤔
    ("iie", ["ii", "e"]),
    ("iu", ["i", "u"]),
    ("ue", ["u", "e"]),
    # double long vowel (these are two syllables, right?)
    ("keieigaku", ["kei", "ei", "ga", "ku"]),
    ("keioudaigaku", ["kei", "ou", "dai", "ga", "ku"]),
]


def idfn(val):
    if type(val) == str:
        return "empty string" if not len(val) else val
    else:
        return str(val)


@pytest.mark.parametrize("word,expected", hepburn_syllable_split_testdata, ids=idfn)
def test_split_hepburn(word, expected):
    actual = japanese.split_syllables(word)
    assert actual == expected
