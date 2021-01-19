from uniunihan_db.util import read_joyo


def test_read_joyo():
    old_char_to_prons, new_char_to_prons, char_supplement = read_joyo()

    # There should be 2136 joyo characters
    assert len(new_char_to_prons) == 2136
    # When using kyuujitai, the number is higher because 弁=辨瓣辯辦辮
    assert len(old_char_to_prons) == 2140

    assert char_supplement["辯"] == {
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
    assert char_supplement["辮"]["old"] == "辮"
    assert char_supplement["和"]["non-joyo"] == ["オ"]

    assert new_char_to_prons["労"] == ["ロウ"]

    assert old_char_to_prons["勞"] == ["ロウ"]
    # new glyph is used if old one not available
    assert old_char_to_prons["老"] == ["ロウ"]

    # 1-to-many new-to-old mappings should be listed in a separate row for each variant
    assert all([len(char_supplement[c]["old"] or "") <= 1 for c in char_supplement])
    assert all([len(char_supplement[c]["new"]) == 1 for c in char_supplement])
