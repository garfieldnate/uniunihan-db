from uniunihan_db.util import read_joyo


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
