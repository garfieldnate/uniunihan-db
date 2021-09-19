from uniunihan_db.data.datasets import (
    BaxterSagart,
    YtenxRhyme,
    get_baxter_sagart,
    get_cedict,
    get_ckip_20k,
    get_edict_freq,
    get_historical_on_yomi,
    get_joyo,
    get_unihan_variants,
    get_ytenx_rhymes,
    get_ytenx_variants,
    index_vocab,
)
from uniunihan_db.data.types import Word, ZhWord
from uniunihan_db.data_paths import TEST_CORPUS_DIR
from uniunihan_db.lingua.aligner import SpaceAligner


def test_get_ytenx_rhymes():
    data = get_ytenx_rhymes()
    assert data["搋"] == [
        YtenxRhyme("搋", "虒", ["hr'eː"], None, None),
        YtenxRhyme("搋", "虒", ["hr'eː", "shreːl"], None, None),
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


def test_get_joyo() -> None:
    char_info = get_joyo()

    # There should be 2140 joyo characters
    assert len(char_info) == 2140

    assert char_info["辯"] == {
        "keyword": ["articulate"],
        "kun_yomi": set(),
        "grade": "5",
        "strokes": "5",
        "new": "弁",
        "non_joyo": set(),
        "readings": {"ベン"},
        "old": "辯",
    }
    # make sure these are properly recognized as separate characters
    assert char_info["辮"]["old"] == "辮"
    assert char_info["和"]["non_joyo"] == {"オ"}

    # 1-to-many new-to-old mappings should be listed in a separate row for each variant
    assert all([len(char_info[c]["old"] or "") <= 1 for c in char_info])
    assert all([len(char_info[c]["new"]) == 1 for c in char_info])

    assert char_info["抱"]["kun_yomi"] == {"だ-く", "いだ-く", "かか-える"}


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


def test_get_edict_freq():
    words = get_edict_freq(TEST_CORPUS_DIR / "edict_freq_sample.txt")
    assert words[0] == Word(
        surface="植え替え",
        id="edict-1",
        pron="うえかえ",
        english="(n) transplanting/transplantation",
        frequency=18686,
    )
    assert [w.surface for w in words] == [
        "植え替え",
        "心配事",
        "卒園",
        "敵対",
        "保湿",
    ]


def test_index_vocab():
    words = [
        Word("伴走", "", "ban sou", "", 0),
        Word("同伴", "", "dou han", "", 0),
        Word("漢字", "", "kan ji", "", 0),
    ]
    char_to_pron_to_words = index_vocab(words, SpaceAligner())
    print(char_to_pron_to_words)
    assert len(char_to_pron_to_words) == 5
    assert len(char_to_pron_to_words["伴"]) == 2
    assert char_to_pron_to_words["伴"]["han"][0].surface == "同伴"


def test_get_cedict():
    words = get_cedict(TEST_CORPUS_DIR / "cedict_sample.u8", filter=True)
    assert words[0] == ZhWord(
        surface="三文魚",
        id="cedict-1",
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
