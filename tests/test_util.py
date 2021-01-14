from uniunihan_db.util import Aligner

CHAR_TO_PRONS = {
    "漢": ["カン"],
    "字": ["ジ"],
    "学": ["ガク"],
    "校": ["コウ"],
    "賭": ["ト"],
    "博": ["ハク"],
    "伴": ["ハン", "バン"],
    "走": ["ソウ"],
}
ALIGNER = Aligner(CHAR_TO_PRONS)


def test_basic_alignment():
    alignment = ALIGNER.align("漢字", "カンジ")
    assert alignment == {"漢": "カン", "字": "ジ"}


def test_sokuon_alignment():
    alignment = ALIGNER.align("学校", "ガッコウ")
    assert alignment == {"学": "ガク", "校": "コウ"}


def test_rendaku_alignment():
    alignment = ALIGNER.align("賭博", "トバク")
    assert alignment == {"賭": "ト", "博": "ハク"}


def test_no_rendaku_dakuten_alignment():
    alignment = ALIGNER.align("伴走", "バンソウ")
    assert alignment == {"伴": "バン", "走": "ソウ"}
