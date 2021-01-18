import csv
import logging
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).parents[1]

DATA_DIR = PROJECT_DIR / "data"

GENERATED_DATA_DIR = DATA_DIR / "generated"
GENERATED_DATA_DIR.mkdir(exist_ok=True)

INCLUDED_DATA_DIR = DATA_DIR / "included"

LOG_FILE = GENERATED_DATA_DIR / "log.txt"


def configure_logging(name):
    logging.basicConfig(
        level=os.environ.get("LOGLEVEL", "INFO"),
        format="[%(levelname)s] %(name)s: %(message)s",
    )
    log = logging.getLogger(name)

    fh = logging.FileHandler(LOG_FILE, mode="w")
    fh.setLevel(logging.WARN)
    log.addHandler(fh)

    return log


log = configure_logging(__name__)


class Aligner:
    """A word/furigana character aligner"""

    RENDAKU = {
        "カ": "ガ",
        "キ": "ギ",
        "ク": "グ",
        "ケ": "ゲ",
        "コ": "ゴ",
        "サ": "ザ",
        "シ": "ジ",
        "ス": "ズ",
        "セ": "ゼ",
        "ソ": "ゾ",
        "タ": "ダ",
        "チ": "ジ",
        "ツ": "ズ",
        "テ": "デ",
        "ト": "ド",
        "ハ": "バ",
        "ヒ": "ビ",
        "フ": "ブ",
        "へ": "ベ",
        "ホ": "ボ",
    }

    RENPANDAKU = {
        "ハ": "パ",
        "ヒ": "ピ",
        "フ": "プ",
        "へ": "ペ",
        "ホ": "ポ",
    }
    # katakana codepoints are in this range
    KATAKANA_LOW = int("30a0", 16)
    KATAKANA_HIGH = int("30ff", 16)
    NO_SOKUON_ALLOWED = set("ンアイウエオ")

    def __init__(self, char_to_prons):
        self.char_to_prons = char_to_prons
        self.sokuon = "ッ"

    def align(self, s, p):
        """Recursively construct a char->pronunciation mapping for the characters in s and the pronunciation in p.
        This implementation is very specific to the project's current needs, and is limited; particularly, it assumes
        that each character in s has one pronunciation in p."""
        if s:
            char = s[0]
            # if surface char is katakana, align with identical katakana in pronunciation;
            # matching_kana will signal not to store the useless alignment
            codepoint = ord(char)
            if Aligner.KATAKANA_LOW <= codepoint <= Aligner.KATAKANA_HIGH:
                prons = [char]
                matching_kana = True
            else:
                # Otherwise, we have kanji. Go through the pronunciations we have for the character,
                # in reverse order to get dakuon spellings first, providing more exact pronunciations
                # for characters with matching pronunciations with and without dakuon (e.g. a character
                # with listed pronunciations ハン and バン)
                prons = sorted(self.char_to_prons.get(char, []), reverse=True)
                matching_kana = False
            for pron in prons:
                matched_pron = None
                if p.startswith(pron):
                    matched_pron = pron
                # test for sokuon, e.g. little っ
                elif (
                    p.startswith(pron[:-1] + self.sokuon)
                    and pron[-1] not in Aligner.NO_SOKUON_ALLOWED
                ):
                    matched_pron = pron[:-1] + self.sokuon
                # test for rendaku, e.g. added tenten
                elif pron[0] in Aligner.RENDAKU.keys() and p.startswith(
                    Aligner.RENDAKU[pron[0]] + pron[1:]
                ):
                    matched_pron = Aligner.RENDAKU[pron[0]] + pron[1:]
                # test for renpandaku, e.g. added maru (I made that word up)
                elif pron[0] in Aligner.RENPANDAKU.keys() and p.startswith(
                    Aligner.RENPANDAKU[pron[0]] + pron[1:]
                ):
                    matched_pron = Aligner.RENPANDAKU[pron[0]] + pron[1:]
                if matched_pron:
                    # base case: this character must map to this pronunciation
                    if len(p) == len(matched_pron):
                        if matching_kana:
                            return {}
                        return {char: pron}
                    # recurse to see if this pronunciation gives a viable alignment
                    if alignment := self.align(s[1:], p.removeprefix(matched_pron)):
                        # if successful and match is a kanji, add this char->pron mapping to the alignment and return it
                        if not matching_kana:
                            alignment[char] = pron
                        return alignment
        # No alignment could be found
        return None


def read_joyo():
    log.info("Loading joyo data...")
    new_char_to_prons = {}
    old_char_to_prons = {}
    char_to_supplementary_info = {}
    with open(INCLUDED_DATA_DIR / "augmented_joyo.csv") as f:
        # filter comments
        rows = csv.DictReader(filter(lambda row: row[0] != "#", f))
        for r in rows:
            supplementary_info = {
                "keyword": r["English_meaning"],
                "kun-yomi": r["kun-yomi"],
                "grade": r["grade"],
                "strokes": r["strokes"],
                "new": r["new"],
            }
            # remove empty readings
            readings = [yomi for yomi in r["on-yomi"].split("|") if yomi]
            # note the non-Joyo readings and strip the indicator asterisk
            supplementary_info["non-joyo"] = [
                yomi[:-1] for yomi in readings if yomi[-1] == "*"
            ]
            readings = [yomi.rstrip("*") for yomi in readings if yomi]
            supplementary_info["readings"] = sorted(readings)

            for c in r["new"]:
                new_char_to_prons[c] = readings
                char_to_supplementary_info[c] = supplementary_info
            # old glyph same as new glyph when missing
            for c in r["old"] or r["new"]:
                old_char_to_prons[c] = readings
                char_to_supplementary_info[c] = dict(supplementary_info)
            # handle multiple old characters case (弁/辨瓣辯辦辮)
            if old := r["old"]:
                for old_c in old:
                    char_to_supplementary_info[old_c]["old"] = old_c
                    for new_c in r["new"]:
                        # put all of the kyuujitai in 弁's 'old' field
                        if new_c == "弁":
                            char_to_supplementary_info[new_c]["old"] = old
                        else:
                            char_to_supplementary_info[new_c]["old"] = old_c

    return old_char_to_prons, new_char_to_prons, char_to_supplementary_info
