# Step 4: Add useful vocabulary that illustrates the
# pronunciations of each character

from typing import List

from uniunihan_db.data.datasets import get_edict_freq, get_vocab_override, index_vocab
from uniunihan_db.data.types import Char2Pron2Words, Word
from uniunihan_db.data_paths import JP_VOCAB_OVERRIDE
from uniunihan_db.lingua.aligner import JpAligner
from uniunihan_db.util import configure_logging, format_json

log = configure_logging(__name__)

JP_MAX_WORDS = 2


def select_vocab_jp(purity_groups, out_dir):
    # construct data necessary for char/pronunciation alignment
    new_char_to_prons = {}
    for pg in purity_groups.values():
        for comp_data in pg.values():
            for old_c, char_data in comp_data["char_data"].items():
                new_c = char_data["new"]
                new_char_to_prons[new_c] = char_data["prons"]

    word_list: List[Word] = get_edict_freq()
    aligner = JpAligner(new_char_to_prons)
    char_to_pron_to_vocab: Char2Pron2Words = index_vocab(word_list, aligner)
    # Some words have to be specified manually instead of extracted from our downloaded dictionary
    vocab_override: Char2Pron2Words = get_vocab_override(JP_VOCAB_OVERRIDE)

    for pg in purity_groups.values():
        for comp_data in pg.values():
            for old_c, char_data in comp_data["char_data"].items():
                # Vocab override uses old forms, edict vocab data uses new forms
                if pron_to_words := vocab_override.get(old_c):
                    for pron, words in pron_to_words.items():
                        char_data["prons"].get(pron, {})["vocab"] = words
                else:
                    new_c = char_data["new"]
                    for pron, pron_data in char_data["prons"].items():
                        words = char_to_pron_to_vocab.get(new_c, {}).get(pron, [])
                        pron_data["vocab"] = __filter_jp_vocab(words)

    def char_data_iter():
        for pg in purity_groups.values():
            for comp_data in pg.values():
                for char_data in comp_data["char_data"].values():
                    yield char_data["new"], char_data

    _report_missing_words(char_data_iter(), out_dir)

    return purity_groups


def __filter_jp_vocab(words):
    """Take the top JP_MAX_WORDS which contain 2 or more characters (words is pre-sorted by frequency)"""
    return list(filter(lambda w: len(w.surface) > 1, words))[:JP_MAX_WORDS]


def select_vocab_zh_hk(purity_groups, out_dir):
    return purity_groups


def select_vocab_ko(purity_groups, out_dir):
    return purity_groups


def _report_missing_words(char_data_iter, out_dir):
    missing_words = set()
    for c, char_data in char_data_iter:
        for pron, pron_data in char_data["prons"].items():
            if not pron_data["vocab"]:
                missing_words.add(f"{c}/{pron}")

    if missing_words:
        log.warn(f"Missing vocab for {len(missing_words)} char/pron pairs")

    with open(out_dir / "missing_words.json", "w") as f:
        # Character/pronunciation pairs for which no vocab examples could be found
        f.write(format_json(sorted(list(missing_words))))


SELECT_VOCAB = {
    "jp": select_vocab_jp,
    "zh-HK": select_vocab_zh_hk,
    "ko": select_vocab_ko,
}
