import abc
from typing import Iterable, Mapping, Set, Tuple


class Aligner(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def align(self, surface: str, phonetic_spelling: str) -> Set[Tuple[str, str]]:
        """surface: the surface string of a word containing han characters
        phonetic_spelling: the phonetic spelling of the same word
        return: a set of tuples (char, pron) giving the mappings from han characters
        to pronunciations found in the word. The alignment strategy is
        language-dependent."""
        raise NotImplementedError


class SpaceAligner(Aligner):
    """This aligner only works on words which have the same number of characters as
    pronounced syllables. The phonetic spelling must be syllables separated by a space
    (such as pinyin)."""

    def align(self, surface: str, phonetic_spelling: str) -> Set[Tuple[str, str]]:
        syllables = phonetic_spelling.split(" ")
        # We can't automatically (simply) align many words, e.g. those with
        # numbers or letters or multi-syllabic characters like ㍻. So we just
        # remove these from the index altogether
        if len(syllables) != len(surface):
            return set()
        return set(zip(surface, syllables))


class JpAligner(Aligner):
    """A word/furigana character aligner for Japanese (katakana only)"""

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

    def __init__(self, char_to_prons: Mapping[str, Iterable[str]]):
        self.char_to_prons = char_to_prons
        self.sokuon = "ッ"

    def align(self, surface: str, phonetic_spelling: str) -> Set[Tuple[str, str]]:
        """Recursively construct a set of (char, pronunciation) mappings for the
        characters in surface and the pronunciation in phonetic_spelling.
        This implementation is very specific to the project's current needs, and is limited."""
        if surface:
            char = surface[0]
            # if surface char is katakana, align with identical katakana in pronunciation;
            # matching_kana will signal not to store the useless alignment
            codepoint = ord(char)
            if JpAligner.KATAKANA_LOW <= codepoint <= JpAligner.KATAKANA_HIGH:
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
                if phonetic_spelling.startswith(pron):
                    matched_pron = pron
                # test for sokuon, e.g. little っ
                elif (
                    phonetic_spelling.startswith(pron[:-1] + self.sokuon)
                    and pron[-1] not in JpAligner.NO_SOKUON_ALLOWED
                ):
                    matched_pron = pron[:-1] + self.sokuon
                # test for rendaku, e.g. added tenten
                elif pron[
                    0
                ] in JpAligner.RENDAKU.keys() and phonetic_spelling.startswith(
                    JpAligner.RENDAKU[pron[0]] + pron[1:]
                ):
                    matched_pron = JpAligner.RENDAKU[pron[0]] + pron[1:]
                # test for renpandaku, e.g. added maru (I made that word up)
                elif pron[
                    0
                ] in JpAligner.RENPANDAKU.keys() and phonetic_spelling.startswith(
                    JpAligner.RENPANDAKU[pron[0]] + pron[1:]
                ):
                    matched_pron = JpAligner.RENPANDAKU[pron[0]] + pron[1:]
                if matched_pron:
                    # base case: this character must map to this pronunciation
                    if len(phonetic_spelling) == len(matched_pron):
                        if matching_kana:
                            return set()
                        return {(char, pron)}
                    # recurse to see if this pronunciation gives a viable alignment
                    if alignment := self.align(
                        surface[1:], phonetic_spelling.removeprefix(matched_pron)
                    ):
                        # if successful and match is a kanji, add this char->pron mapping to the alignment and return it
                        if not matching_kana:
                            alignment.add((char, pron))
                        return alignment
        # No alignment could be found
        return set()
