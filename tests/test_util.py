from uniunihan_db.util import read_ckip_20k, read_joyo


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
    print(ckip_20k.keys())
    assert len(ckip_20k) == 3499
