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

    def __init__(self, char_to_prons):
        self.char_to_prons = char_to_prons

    def align(self, s, p):
        """Recursively construct a char->pronunciation mapping for the characters in s and the pronunciation in p.
        This implementation is very specific to the project's current needs, and is limited; particularly, it assumes
        that each character in s has one pronunciation in p."""
        if s:
            char = s[0]
            for pron in self.char_to_prons.get(char, []):
                if p.startswith(pron):
                    # base case: this character must map to this pronunciation
                    if len(p) == len(pron):
                        return {char: pron}
                    # recurse to see if this pronunciation gives a viable alignment
                    if alignment := self.align(s[1:], p.removeprefix(pron)):
                        # if successful, add this char->pron mapping to the alignment and return it
                        alignment[char] = pron
                        return alignment
        # No alignment could be found
        return None
