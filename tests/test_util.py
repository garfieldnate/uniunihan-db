from uniunihan_db.util import Aligner, read_joyo

CHAR_TO_PRONS = {
    "漢": ["カン"],
    "字": ["ジ"],
    "学": ["ガク"],
    "校": ["コウ"],
    "賭": ["ト"],
    "博": ["ハク"],
    "伴": ["ハン", "バン"],
    "走": ["ソウ"],
    "分": ["ブン"],
    "泌": ["ヒツ"],
    "科": ["カ"],
    "納": ["ナン", "ナッ"],
    "得": ["トク"],
    "今": ["コン"],
    "昔": ["シャク"],
}
ALIGNER = Aligner(CHAR_TO_PRONS)


def test_basic_alignment():
    alignment = ALIGNER.align("漢字", "カンジ")
    assert alignment == {"漢": "カン", "字": "ジ"}


def test_sokuon_alignment():
    alignment = ALIGNER.align("学校", "ガッコウ")
    assert alignment == {"学": "ガク", "校": "コウ"}


def test_n_cannot_be_sokuon():
    alignment = ALIGNER.align("納得", "ナットク")
    assert alignment == {"納": "ナッ", "得": "トク"}


def test_rendaku_alignment():
    alignment = ALIGNER.align("賭博", "トバク")
    assert alignment == {"賭": "ト", "博": "ハク"}

    alignment = ALIGNER.align("今昔", "コンシャク")
    assert alignment == {"今": "コン", "昔": "シャク"}


def test_no_rendaku_dakuten_alignment():
    alignment = ALIGNER.align("伴走", "バンソウ")
    assert alignment == {"伴": "バン", "走": "ソウ"}


def test_renpandaku_alignment():
    alignment = ALIGNER.align("分泌", "ブンピツ")
    assert alignment == {"分": "ブン", "泌": "ヒツ"}


def test_kana_alignment():
    alignment = ALIGNER.align("シソ科", "シソカ")
    assert alignment == {"科": "カ"}


def test_read_joyo():
    old_char_to_prons, new_char_to_prons, char_supplement = read_joyo()

    # There should be 2136 joyo characters
    assert len(new_char_to_prons) == 2136
    # When using kyuujitai, the number is higher because 弁=辨瓣辯辦辮
    assert len(old_char_to_prons) == 2140

    assert char_supplement["辯"] == {
        "keyword": "valve",
        "kun-yomi": "",
        "grade": "5",
        "strokes": "5",
        "new": "弁",
        "non-joyo": [],
        "readings": ["ベン"],
        "old": "辯",
    }
    # make sure these are properly recognized as separate characters
    assert char_supplement["辮"]["old"] == "辮"
    assert char_supplement["弁"]["old"] == "辨瓣辯辦辮"
    assert char_supplement["和"]["non-joyo"] == ["オ"]

    assert new_char_to_prons["労"] == ["ロウ"]

    assert old_char_to_prons["勞"] == ["ロウ"]
    # new glyph is used if old one not available
    assert old_char_to_prons["老"] == ["ロウ"]
