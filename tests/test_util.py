import string

from uniunihan_db.util import (
    filter_keys,
    read_baxter_sagart,
    read_cedict,
    read_ckip_20k,
    read_historical_on_yomi,
    read_joyo,
)


def test_filter_keys() -> None:
    d = {c: ord(c) for c in string.ascii_lowercase}
    letters = "abc"
    assert filter_keys(d, letters) == {"a": ord("a"), "b": ord("b"), "c": ord("c")}


def test_read_joyo() -> None:
    joyo = read_joyo()

    # There should be 2136 joyo characters
    assert len(joyo.new_char_to_prons) == 2136
    # When using kyuujitai, the number is higher because 弁=辨瓣辯辦辮
    assert len(joyo.old_char_to_prons) == 2140

    assert joyo.char_to_supplementary_info["辯"] == {
        "keyword": "articulate",
        "kun_yomi": [],
        "grade": "5",
        "strokes": "5",
        "new": "弁",
        "non_joyo": [],
        "readings": ["ベン"],
        "old": "辯",
    }
    # make sure these are properly recognized as separate characters
    assert joyo.char_to_supplementary_info["辮"]["old"] == "辮"
    assert joyo.char_to_supplementary_info["和"]["non_joyo"] == ["オ"]

    assert joyo.new_char_to_prons["労"] == ["ロウ"]

    assert joyo.old_char_to_prons["勞"] == ["ロウ"]
    # new glyph is used if old one not available
    assert joyo.old_char_to_prons["老"] == ["ロウ"]

    # 1-to-many new-to-old mappings should be listed in a separate row for each variant
    assert all(
        [
            len(joyo.char_to_supplementary_info[c]["old"] or "") <= 1
            for c in joyo.char_to_supplementary_info
        ]
    )
    assert all(
        [
            len(joyo.char_to_supplementary_info[c]["new"]) == 1
            for c in joyo.char_to_supplementary_info
        ]
    )

    assert set("辨瓣辯辦辮") == joyo.new_to_old("弁")

    assert joyo.char_to_supplementary_info["抱"]["kun_yomi"] == ["だ-く", "いだ-く", "かか-える"]


def test_read_ckip_20k() -> None:
    ckip_20k = read_ckip_20k()
    assert len(ckip_20k) == 18462
    assert ckip_20k["黴菌"] == [
        {
            "en": "family_Aspergillaceae",
            "freq": 11,
            "pron": "mei2 jun4",
            "surface": "黴菌",
        },
    ]

    ckip_20k = read_ckip_20k(index_chars=True)
    assert len(ckip_20k) == 3499
    assert ckip_20k["黴"] == {
        "mei2": [
            {
                "en": "family_Aspergillaceae",
                "freq": 11,
                "pron": "mei2 jun4",
                "surface": "黴菌",
            },
        ]
    }


def test_read_cedict() -> None:
    entries = read_cedict()
    # Assuming the size of the dictionary will only grow over time
    assert len(entries) >= 113420
    assert entries["分錢"] == [
        {
            "en": "cent/penny",
            "trad": "分錢",
            "simp": "分钱",
            "pron": "fen1 qian2",
        }
    ]
    # Ensure pronunciations are lower-cased
    assert entries["辯機"][0]["pron"] == "bian4 ji1"

    char_to_pron_to_word = read_cedict(index_chars=True)
    # Assuming the number of characters in the dictionary will only grow over time
    assert len(char_to_pron_to_word) >= 9997
    assert "qian2" in char_to_pron_to_word["錢"]
    assert {
        "en": "cent/penny",
        "trad": "分錢",
        "simp": "分钱",
        "pron": "fen1 qian2",
    } in char_to_pron_to_word["錢"]["qian2"]

    assert "ai2" in char_to_pron_to_word["癌"]


def test_read_historical_on_yomi():
    char_to_new_to_old_pron = read_historical_on_yomi()
    assert "位" in char_to_new_to_old_pron
    char = char_to_new_to_old_pron["位"]
    assert "イ" in char
    old_kana = char["イ"]
    assert old_kana == "ヰ"


def test_read_baxter_sagart():
    char_to_info = read_baxter_sagart()
    assert "坐" in char_to_info
    assert len(char_to_info["坐"]) == 3
    assert char_to_info["坐"][0] == {
        "keyword": "sit",
        "middle_chinese": "dzwaX",
        "old_chinese": "*[dz]ˤo[j]ʔ ",
        "pinyin": "zuò",
    }
