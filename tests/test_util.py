from uniunihan_db.lingua.mandarin import strip_tone
from uniunihan_db.util import (
    get_mandarin_pronunciation,
    read_ckip_20k,
    read_joyo,
    read_unihan,
)


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
    unihan = read_unihan()
    total_unihan_prons = 0
    total_ckip_prons = 0
    total_chars = len(ckip_20k)
    chars_with_missing_prons = 0
    for char in ckip_20k:
        ckip_prons = set(ckip_20k[char].keys())
        unihan_prons = set(get_mandarin_pronunciation(unihan[char]))
        unihan_prons_to_remove = set()
        for up in unihan_prons:
            up_no_tone, tone = strip_tone(up)
            if tone == 0:
                continue
            if up_no_tone in unihan_prons:
                unihan_prons_to_remove.add(up)
        for up in unihan_prons_to_remove:
            unihan_prons.remove(up)
        # print(char)
        # print(unihan_prons)
        # print(ckip_prons)
        # tone sandhi, dialectal pronunciations, should probably ignore 0 tones
        # if char not in set("一不個了人"):
        total_unihan_prons += len(unihan_prons)
        total_ckip_prons += len(ckip_prons)
        if unihan_prons <= ckip_prons:
            chars_with_missing_prons += 1

    print(f"{chars_with_missing_prons}/{total_chars} chars with missing prons")
    print(f"{total_unihan_prons} total unihan prons")
    print(f"{total_ckip_prons} total ckip prons")
    # assert False
