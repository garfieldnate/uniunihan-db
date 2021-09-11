from tests.lingua.test_aligner import TestJpAligner
from uniunihan_db.data.datasets import (
    BaxterSagart,
    get_baxter_sagart,
    get_cedict,
    get_ckip_20k,
    get_edict,
    get_historical_on_yomi,
    get_joyo,
    get_unihan_variants,
    get_ytenx_rhymes,
    get_ytenx_variants,
    index_vocab_jp,
    index_vocab_zh,
)
from uniunihan_db.data.types import JpWord, ZhWord
from uniunihan_db.data_paths import TEST_CORPUS_DIR


def test_get_ytenx_rhymes():
    data = get_ytenx_rhymes()
    assert data["搋"] == [
        {
            "廣韻聲": "徹",
            "廣韻韻": "皆",
            "聲調": "平",
            "等": "2",
            "開合": "開",
            "上字": "丑",
            "下字": "皆",
            "聲符": "虒",
            "韻部": "支",
            "擬音": ["hr'eː"],
            "註釋": "見通俗文",
        },
        {
            "廣韻聲": "徹",
            "廣韻韻": "佳",
            "聲調": "平",
            "等": "2",
            "開合": "開",
            "上字": "丑",
            "下字": "佳",
            "聲符": "虒",
            "韻部": "支",
            "擬音": ["hr'eː", "shreːl"],
            "註釋": "扠字注或體",
        },
    ]


def test_get_ytenx_variants():
    data = get_ytenx_variants()
    assert data["鮮"] == {"鱻", "尠", "尟", "鲜"}


def test_get_baxter_sagart():
    char_to_info = get_baxter_sagart()
    assert "坐" in char_to_info
    assert len(char_to_info["坐"]) == 3
    assert char_to_info["坐"][0] == BaxterSagart(
        char="坐",
        pinyin="zuò",
        middle_chinese="dzwaX",
        old_chinese="*[dz]ˤo[j]ʔ",
        gloss="sit",
    )


def test_get_ckip_20k() -> None:
    ckip_20k = get_ckip_20k()
    assert len(ckip_20k) == 18462
    assert ckip_20k["黴菌"] == [
        {
            "en": "family_Aspergillaceae",
            "freq": 11,
            "pron": "mei2 jun4",
            "surface": "黴菌",
        },
    ]

    ckip_20k = get_ckip_20k(index_chars=True)
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


def test_get_joyo() -> None:
    joyo = get_joyo()

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


def test_get_historical_on_yomi():
    char_to_new_to_old_pron = get_historical_on_yomi()
    assert "位" in char_to_new_to_old_pron
    char = char_to_new_to_old_pron["位"]
    assert "イ" in char
    old_kana = char["イ"]
    assert old_kana == "ヰ"


def test_get_unihan_variants():
    # test with smaller file because it takes too long to load the full one
    char_to_variants = get_unihan_variants(TEST_CORPUS_DIR / "unihan_sample.json")
    assert char_to_variants == {
        "㑯": {"㑔"},
        "㖈": {"䎛"},
        "㗖": {"啖", "啗", "噉"},
        "㘎": {"㘚"},
    }


def test_get_edict():
    words = get_edict(TEST_CORPUS_DIR / "edict_freq_sample.tsv")
    assert words[0] == JpWord(
        surface="植え替え",
        pron="うえかえ",
        english="(n) transplanting/transplantation",
        frequency=18686,
        alignable_surface="植エ替エ",
        alignable_pron="ウエカエ",
    )
    assert [w.surface for w in words] == [
        "植え替え",
        "心配事",
        "卒園",
        "敵対",
        "保湿",
    ]


def test_index_vocab_jp():
    words = [
        JpWord("", "", "", 0, alignable_surface="伴走", alignable_pron="バンソウ"),
        JpWord("", "", "", 0, alignable_surface="同伴", alignable_pron="ドウハン"),
        JpWord("", "", "", 0, alignable_surface="漢字", alignable_pron="カンジ"),
    ]
    char_to_pron_to_words = index_vocab_jp(words, TestJpAligner.ALIGNER)
    assert len(char_to_pron_to_words) == 5
    assert len(char_to_pron_to_words["伴"]) == 2
    assert char_to_pron_to_words["伴"]["ハン"][0].alignable_surface == "同伴"


def test_get_cedict():
    words = get_cedict(TEST_CORPUS_DIR / "cedict_sample.u8", filter=True)
    assert words[0] == ZhWord(
        surface="三文魚",
        # also tests lowercasing
        pron="san1 wen2 yu2",
        english="salmon (loanword)",
        frequency=-1,
        simplified="三文鱼",
    )
    assert [w.surface for w in words] == [
        "三文魚",
        "伏虎",
        "伏臥",
    ]


# TODO: mark as a larger test and only run sometimes
def test_get_cedict_full() -> None:
    words = get_cedict()
    # Assuming the size of the dictionary will only grow over time
    assert len(words) >= 113420


def test_index_vocab_zh():
    words = [
        ZhWord("伏虎", "fu2 hu3", "", 0, ""),
        ZhWord("伏輸", "fu2 shu1", "", 0, ""),
        ZhWord("自己", "zi4 ji3", "", 0, ""),
        ZhWord("梯己", "ti1 ji2", "", 0, ""),
    ]
    char_to_pron_to_words = index_vocab_zh(words)
    assert len(char_to_pron_to_words) == 6
    assert len(char_to_pron_to_words["己"]) == 2
    assert char_to_pron_to_words["己"]["ji3"][0].surface == "自己"
