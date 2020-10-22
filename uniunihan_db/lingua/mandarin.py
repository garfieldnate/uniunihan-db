import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Syllable:
    """
    The structure of this class follows the traditional classification of Mandarin syllables,
    which are traditionally divided into
    C, G, V and X. These are an initial consonant, a glide or prenuclear vowel, the nucleus
    or nuclear vowel, and a final vowel or nasal consonant.
    See http://orient.avcr.cz/miranda2/export/sitesavcr/data.avcr.cz/humansci/orient/kontakty/pracovnici/publikace/Triskova/ArOr_Mandarin_Syllable.pdf
    for a more detailed explanation.
    Fields:
    `onset` = X: /b/, /p/, /m/, /f/, /d/,/t/, /n/, /l/…
    `glide` = G: /i/, /u/, /ü/
    `nucleus` = V: /a/, /o/, /e/, /i/, /u/, /ü/
    `final` = X: /i/, /u/, /n/, /ng/
    `tone`: an integer between 0 and 4
    `tone_stripped`: same as the original spelling but with the tone diacritic removed
    `rhyme`: phonetic transcription of the glide, nucleus and final
    """

    onset: str
    glide: str
    nucleus: str
    final: str
    tone: int
    tone_stripped: str

    def __post_init__(self):
        self.rhyme = self.glide + self.nucleus + self.final


def __setup_pinyin_parsing():

    pinyin_vowels = [
        "aāáǎà",
        "eēéěè",
        "iīíǐì",
        "oōóǒò",
        "uūúǔù",
        "üǖǘǚǜ",
    ]
    vowel_list = "".join(pinyin_vowels)
    # integer tone to [chars with diacritic]
    tone_matchers = {}
    for tone in range(1, 5):
        tone_matchers[tone] = "[" + "".join([s[tone] for s in pinyin_vowels]) + "]"
    # vowel without diacritic to [same vowel with diacritic]
    tone_removers = {}
    for vowel_set in pinyin_vowels:
        tone_removers[vowel_set[0]] = "[" + vowel_set[1:] + "]"

    return vowel_list, tone_matchers, tone_removers


VOWEL_LIST, TONE_MATCHERS, TONE_REMOVERS = __setup_pinyin_parsing()


ONSETS = "tdkgpbwqryljhszxcnmf"

SYLLABLE_RE = f"(?i)^(?P<onset>[{ONSETS}]h?)?(?P<glide>i|u|ü)?(?P<nucleus>[{VOWEL_LIST}])(?P<final>ng?|r|i|u|o)?$"


def parse_syllable(s: str) -> Optional[Syllable]:
    """Parse a pinyin-romanized syllable into its constituent parts. This does not attempt
    to prevent any nonsense syllables from being parsed, but if the input cannot be parsed
    then None will be returned."""
    s = s.strip().lower()

    # determine the tone and strip the diacritic first to simplify later processing
    tone = 0
    for t, matcher in TONE_MATCHERS.items():
        if re.search(matcher, s):
            tone = t
    for no_tone, with_tone in TONE_REMOVERS.items():
        s = re.sub(with_tone, no_tone, s)

    tone_stripped = s

    # "ying" is allophonic with "ing"
    s = s.replace("yi", "i")
    # "yu" is allophonic with "ü"
    s = s.replace("yu", "ü")
    # elsewhere 'y' is an 'i' in the glide
    s = s.replace("y", "i")
    # 'wen' is pronounced 'un'
    if s == "wen":
        s = "un"
    # 'wu' is allophonic with 'wu'
    s = s.replace("wu", "u")
    # elsewhere 'w' is a 'u' in the glide
    s = s.replace("w", "u")

    match = re.match(SYLLABLE_RE, s)
    if match is None:
        return None
    pieces = match.groupdict()

    if "iu" in s:
        pieces["glide"] = "i"
        pieces["nucleus"] = "o"
        pieces["final"] = "u"
    if "ui" in s:
        pieces["glide"] = "u"
        pieces["nucleus"] = "e"
        pieces["final"] = "i"

    final = pieces["final"]
    # ao, iao, etc. are spelled with 'o' but the final is an 'u'
    if final == "o":
        final = "u"

    return Syllable(
        pieces["onset"] or "",
        pieces["glide"] or "",
        # vowel_no_tone,
        pieces["nucleus"],
        final or "",
        tone,
        tone_stripped,
    )