from uniunihan_db.lingua.jp.aligner import Aligner

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
    "同": ["ドウ"],
}
ALIGNER = Aligner(CHAR_TO_PRONS)


def test_basic_alignment() -> None:
    alignment = ALIGNER.align("漢字", "カンジ")
    assert alignment == {"漢": "カン", "字": "ジ"}


def test_sokuon_alignment() -> None:
    alignment = ALIGNER.align("学校", "ガッコウ")
    assert alignment == {"学": "ガク", "校": "コウ"}


def test_n_cannot_be_sokuon() -> None:
    alignment = ALIGNER.align("納得", "ナットク")
    assert alignment == {"納": "ナッ", "得": "トク"}


def test_rendaku_alignment() -> None:
    alignment = ALIGNER.align("賭博", "トバク")
    assert alignment == {"賭": "ト", "博": "ハク"}

    alignment = ALIGNER.align("今昔", "コンシャク")
    assert alignment == {"今": "コン", "昔": "シャク"}


def test_no_rendaku_dakuten_alignment() -> None:
    alignment = ALIGNER.align("伴走", "バンソウ")
    assert alignment == {"伴": "バン", "走": "ソウ"}


def test_renpandaku_alignment() -> None:
    alignment = ALIGNER.align("分泌", "ブンピツ")
    assert alignment == {"分": "ブン", "泌": "ヒツ"}


def test_kana_alignment() -> None:
    alignment = ALIGNER.align("シソ科", "シソカ")
    assert alignment == {"科": "カ"}
