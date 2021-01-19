import pytest

from uniunihan_db.lingua import mandarin


# NEXT: reorganize as CGVX;
@pytest.mark.parametrize(
    "input,onset,glide,nucleus,final,tone,tone_stripped,rhyme",
    [
        ("e", "", "", "e", "", 0, "e", "e"),
        ("de", "d", "", "e", "", 0, "de", "e"),
        ("meng", "m", "", "e", "ng", 0, "meng", "eng"),
        ("bai", "b", "", "a", "i", 0, "bai", "ai"),
        ("gou", "g", "", "o", "u", 0, "gou", "ou"),
        ("lüe", "l", "ü", "e", "", 0, "lüe", "üe"),
        ("zhuang", "zh", "u", "a", "ng", 0, "zhuang", "uang"),
        ("niao", "n", "i", "a", "u", 0, "niao", "iau"),
        ("kuai", "k", "u", "a", "i", 0, "kuai", "uai"),
        ("er", "", "", "e", "r", 0, "er", "er"),
        ("huar", "h", "u", "a", "r", 0, "huar", "uar"),
        # uppercase
        ("LÜE", "l", "ü", "e", "", 0, "lüe", "üe"),
        # spellings that don't exactly match the syllable structure
        ("jiu", "j", "i", "o", "u", 0, "jiu", "iou"),
        ("shui", "sh", "u", "e", "i", 0, "shui", "uei"),
        ("ying", "", "", "i", "ng", 0, "ying", "ing"),
        ("yu", "", "", "ü", "", 0, "yu", "ü"),
        ("yue", "", "ü", "e", "", 0, "yue", "üe"),
        ("yang", "", "i", "a", "ng", 0, "yang", "iang"),
        ("wu", "", "", "u", "", 0, "wu", "u"),
        ("wai", "", "u", "a", "i", 0, "wai", "uai"),
        ("wen", "", "", "u", "n", 0, "wen", "un"),
        # tones
        ("fàn", "f", "", "a", "n", 4, "fan", "an"),
        ("guān", "g", "u", "a", "n", 1, "guan", "uan"),
        ("xiě", "x", "i", "e", "", 3, "xie", "ie"),
        ("liú", "l", "i", "o", "u", 2, "liu", "iou"),
        ("hǎo", "h", "", "a", "u", 3, "hao", "au"),
    ],
)
def test_parse_legal_syllable(
    input, onset, glide, nucleus, final, tone, tone_stripped, rhyme
):
    actual = mandarin.parse_syllable(input)
    assert actual is not None
    assert actual.surface == input.strip().lower()
    assert actual.onset == onset
    assert actual.glide == glide
    assert actual.nucleus == nucleus
    assert actual.final == final
    assert actual.tone == tone
    assert actual.tone_stripped == tone_stripped
    assert actual.rhyme == rhyme


def test_parse_nonce_syllable():
    syl = mandarin.parse_syllable("xyadfs")
    assert syl is None


def test_pinyin_tone_marks_to_numbers():
    s = "shén me"
    assert mandarin.pinyin_tone_marks_to_numbers(s) == "shen2 me"
