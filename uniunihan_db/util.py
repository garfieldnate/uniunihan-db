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


class Aligner:
    """A word/furigana character aligner"""

    rendaku = {
        "ハ": "バ",
        "ヒ": "ビ",
        "フ": "ブ",
        "へ": "ベ",
        "ホ": "ボ",
    }

    def __init__(self, char_to_prons):
        self.char_to_prons = char_to_prons
        self.sokuon = "ッ"

    def align(self, s, p):
        """Recursively construct a char->pronunciation mapping for the characters in s and the pronunciation in p.
        This implementation is very specific to the project's current needs, and is limited; particularly, it assumes
        that each character in s has one pronunciation in p."""
        if s:
            char = s[0]
            # reverse sort to get dakuon spellings first gives more exact pronunciations for characters with matching pronunciations with and without dakuon
            for pron in sorted(self.char_to_prons.get(char, []), reverse=True):
                matched_pron = None
                if p.startswith(pron):
                    matched_pron = pron
                elif p.startswith(pron[:-1] + self.sokuon):
                    matched_pron = pron[:-1] + self.sokuon
                elif pron[0] in Aligner.rendaku.keys() and p.startswith(
                    Aligner.rendaku[pron[0]] + pron[1:]
                ):
                    matched_pron = Aligner.rendaku[pron[0]] + pron[1:]
                if matched_pron:
                    # base case: this character must map to this pronunciation
                    if len(p) == len(matched_pron):
                        return {char: pron}
                    # recurse to see if this pronunciation gives a viable alignment
                    if alignment := self.align(s[1:], p.removeprefix(matched_pron)):
                        # if successful, add this char->pron mapping to the alignment and return it
                        alignment[char] = pron
                        return alignment
        # No alignment could be found
        return None
