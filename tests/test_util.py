import string

from uniunihan_db.util import filter_keys, read_cedict, read_ckip_20k, read_joyo


def test_filter_keys():
    d = {c: ord(c) for c in string.ascii_lowercase}
    letters = "abc"
    assert filter_keys(d, letters) == {"a": ord("a"), "b": ord("b"), "c": ord("c")}


def test_read_joyo():
    joyo = read_joyo()

    # There should be 2136 joyo characters
    assert len(joyo.new_char_to_prons) == 2136
    # When using kyuujitai, the number is higher because 弁=辨瓣辯辦辮
    assert len(joyo.old_char_to_prons) == 2140

    assert joyo.char_to_supplementary_info["辯"] == {
        "keyword": "articulate",
        "kun-yomi": "",
        "grade": "5",
        "strokes": "5",
        "new": "弁",
        "non-joyo": [],
        "readings": ["ベン"],
        "old": "辯",
    }
    # make sure these are properly recognized as separate characters
    assert joyo.char_to_supplementary_info["辮"]["old"] == "辮"
    assert joyo.char_to_supplementary_info["和"]["non-joyo"] == ["オ"]

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


def test_read_ckip_20k():
    ckip_20k = read_ckip_20k()
    assert len(ckip_20k) == 18462
    assert ckip_20k["黴菌"] == [
        {
            "en": "family_Aspergillaceae",
            "freq": 11,
            "pron": "méi jùn",
            "surface": "黴菌",
        },
    ]

    ckip_20k = read_ckip_20k(index_chars=True)
    assert len(ckip_20k) == 3499
    assert ckip_20k["黴"] == {
        "méi": [
            {
                "en": "family_Aspergillaceae",
                "freq": 11,
                "pron": "méi jùn",
                "surface": "黴菌",
            },
        ]
    }


def test_read_cedict():
    entries = read_cedict()
    # Assuming the size of the dictionary will only grow over time
    assert len(entries) >= 116751
    assert entries["分錢"] == [
        {
            "en": "cent/penny",
            "trad": "分錢",
            "simp": "分钱",
            "pron": "fen1 qian2",
        }
    ]
    char_to_pron_to_word = read_cedict(index_chars=True)
    # Assuming the number of characters in the dictionary will only grow over time
    assert len(char_to_pron_to_word) >= 11733
    assert "qian2" in char_to_pron_to_word["錢"]
    assert {
        "en": "cent/penny",
        "trad": "分錢",
        "simp": "分钱",
        "pron": "fen1 qian2",
    } in char_to_pron_to_word["錢"]["qian2"]

    assert "ai2" in char_to_pron_to_word["癌"]
