import unicodedata

from uniunihan_db.data.vietnamese import (
    _char_from_codepoint,
    _gloss_agreement,
    _norm,
    _reconstruct_han_viet_reading,
)


def test_gloss_agreement_exact_and_prefix():
    # exact match
    assert _gloss_agreement({"mayor"}, {"mayor", "chief"}) == 1
    # shared prefix (>= 4 chars) forgives inflection / wording differences
    assert _gloss_agreement({"development"}, {"develop"}) == 1
    assert _gloss_agreement({"nation"}, {"national"}) == 1
    # no agreement
    assert _gloss_agreement({"seek"}, {"ball", "player"}) == 0
    # short words must match exactly (no spurious prefix match)
    assert _gloss_agreement({"art"}, {"artery"}) == 0


def test_norm_lowercases_and_strips():
    assert _norm("  Quốc  ") == "quốc"


def test_norm_is_nfc():
    # a decomposed (NFD) input should be composed to NFC
    decomposed = unicodedata.normalize("NFD", "quốc")
    assert _norm(decomposed) == unicodedata.normalize("NFC", "quốc")


def test_char_from_codepoint_bmp():
    assert _char_from_codepoint("U+570B") == "國"


def test_char_from_codepoint_ext_b():
    assert _char_from_codepoint("U+20000") == "𠀀"


def test_char_from_codepoint_literal_char():
    assert _char_from_codepoint("越") == "越"


def test_reconstruct_reading_finds_attested_word():
    char_to_readings = {"國": {"quốc"}, "家": {"gia"}}
    vnedict = {"quốc gia": {"country", "nation"}}
    assert _reconstruct_han_viet_reading(["國", "家"], char_to_readings, vnedict) == (
        "quốc",
        "gia",
    )


def test_reconstruct_reading_prefers_gloss_match_among_alternates():
    # 市長 "mayor": the reading "thị trường" spells the (unrelated) common word
    # "market"; only "thị trưởng" matches the source meaning, so it must win.
    char_to_readings = {"市": {"thị"}, "長": {"trường", "trưởng"}}
    vnedict = {
        "thị trường": {"market", "marketplace"},
        "thị trưởng": {"mayor"},
    }
    meaning = {"mayor"}
    assert _reconstruct_han_viet_reading(
        ["市", "長"], char_to_readings, vnedict, meaning
    ) == ("thị", "trưởng")


def test_reconstruct_reading_returns_empty_when_not_a_word():
    char_to_readings = {"國": {"quốc"}, "家": {"gia"}}
    vnedict = {"some other word": {"foo"}}
    assert _reconstruct_han_viet_reading(["國", "家"], char_to_readings, vnedict) == ()
