from uniunihan_db.lingua.aligner import JpAligner, SpaceAligner


class TestJpAligner:
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
    ALIGNER = JpAligner(CHAR_TO_PRONS)

    @staticmethod
    def test_basic_alignment() -> None:
        alignment = TestJpAligner.ALIGNER.align("漢字", "カンジ")
        assert alignment == {("漢", "カン"), ("字", "ジ")}

    @staticmethod
    def test_sokuon_alignment() -> None:
        alignment = TestJpAligner.ALIGNER.align("学校", "ガッコウ")
        assert alignment == {("学", "ガク"), ("校", "コウ")}

    @staticmethod
    def test_n_cannot_be_sokuon() -> None:
        alignment = TestJpAligner.ALIGNER.align("納得", "ナットク")
        assert alignment == {("納", "ナッ"), ("得", "トク")}

    @staticmethod
    def test_rendaku_alignment() -> None:
        alignment = TestJpAligner.ALIGNER.align("賭博", "トバク")
        assert alignment == {("賭", "ト"), ("博", "ハク")}

        alignment = TestJpAligner.ALIGNER.align("今昔", "コンシャク")
        assert alignment == {("今", "コン"), ("昔", "シャク")}

    @staticmethod
    def test_no_rendaku_dakuten_alignment() -> None:
        alignment = TestJpAligner.ALIGNER.align("伴走", "バンソウ")
        assert alignment == {("伴", "バン"), ("走", "ソウ")}

    @staticmethod
    def test_renpandaku_alignment() -> None:
        alignment = TestJpAligner.ALIGNER.align("分泌", "ブンピツ")
        assert alignment == {("分", "ブン"), ("泌", "ヒツ")}

    @staticmethod
    def test_kana_alignment() -> None:
        alignment = TestJpAligner.ALIGNER.align("シソ科", "シソカ")
        assert alignment == {("科", "カ")}


class TestSpaceAligner:
    ALIGNER = SpaceAligner()

    @staticmethod
    def test_basic_alignment():
        alignment = TestSpaceAligner.ALIGNER.align("日本", "ri4 ben3")
        assert alignment == {("日", "ri4"), ("本", "ben3")}

    @staticmethod
    def test_multi_syllable_chars_skipped():
        alignment = TestSpaceAligner.ALIGNER.align("㍻", "ping2 cheng2")
        assert alignment == set()
