# Step 4: Add useful vocabulary that illustrates the
# pronunciations of each character

from typing import List

from loguru import logger

from uniunihan_db.data.datasets import (
    get_cedict,
    get_chunom_org_vocab,
    get_ckip_20k,
    get_edict_freq,
    get_kengdic,
    get_vocab_override,
    index_vocab,
)
from uniunihan_db.data.paths import JP_VOCAB_OVERRIDE
from uniunihan_db.data.types import Char2Pron2Words, Word, ZhWord
from uniunihan_db.lingua.aligner import JpAligner, KoAligner, ZhAligner
from uniunihan_db.util import format_json

MAX_EXAMPLE_VOCAB = 2


def select_vocab_jp(data):
    char_data = data["char_data"]
    # construct data necessary for char/pronunciation alignment
    new_char_to_prons = {}
    for c_data in char_data.values():
        new_c = c_data["new"]
        new_char_to_prons[new_c] = c_data["prons"]

    word_list: List[Word] = get_edict_freq()
    aligner = JpAligner(new_char_to_prons)
    char_to_pron_to_vocab: Char2Pron2Words = index_vocab(word_list, aligner)
    # Some words have to be specified manually instead of extracted from our downloaded dictionary
    vocab_override: Char2Pron2Words = get_vocab_override(JP_VOCAB_OVERRIDE)

    duplicate_used = set()
    used_vocab = set()
    for old_c, c_data in char_data.items():
        # Vocab override uses old forms, edict vocab data uses new forms
        if pron_to_words := vocab_override.get(old_c):
            for pron, words in pron_to_words.items():
                c_data["prons"].get(pron, {})["vocab"] = words
                used_vocab.update({v.surface for v in c_data["prons"][pron]["vocab"]})
            for pron_data in c_data["prons"].values():
                if "vocab" not in pron_data:
                    pron_data["vocab"] = []
        else:
            new_c = c_data["new"]
            for pron, pron_data in c_data["prons"].items():
                words = char_to_pron_to_vocab.get(new_c, {}).get(pron, [])
                pron_data["vocab"] = __order_vocab(words, used_vocab)
                for w in pron_data["vocab"]:
                    if w.surface in used_vocab:
                        duplicate_used.add(w.surface)
                used_vocab.update({v.surface for v in pron_data["vocab"]})

    def char_data_iter():
        for c_data in char_data.values():
            yield c_data["new"], c_data

    _report_missing_words(char_data_iter())
    _report_duplicate_use(duplicate_used)

    return data


def __order_vocab(words, used):
    """Take the top MAX_EXAMPLE_VOCAB vocab, preferring those which consist of multiple
    characters and which have not been used yet (words should also be
    pre-sorted by frequency, etc.)"""

    words = sorted(words, key=lambda w: (w.surface in used, len(w.surface) == 1))
    return words[:MAX_EXAMPLE_VOCAB]


def select_vocab_zh(data):
    char_data = data["char_data"]
    word_list: List[ZhWord] = get_cedict()
    _incorporate_ckip_freq_data(word_list)
    char_to_pron_to_vocab = index_vocab(word_list, ZhAligner())

    duplicate_used = set()
    used_vocab = set()
    for c, c_data in char_data.items():
        for pron, pron_data in c_data["prons"].items():
            words = char_to_pron_to_vocab.get(c, {}).get(pron, [])
            pron_data["vocab"] = __order_vocab(words, used_vocab)
            for w in pron_data["vocab"]:
                if w.surface in used_vocab:
                    duplicate_used.add(w.surface)
            used_vocab.update({v.surface for v in pron_data["vocab"]})

    def char_data_iter():
        for c, c_data in char_data.items():
            yield c, c_data

    _report_missing_words(char_data_iter())
    _report_duplicate_use(duplicate_used)

    return data


def _incorporate_ckip_freq_data(words: List[ZhWord]) -> None:
    ckip20k_entries = get_ckip_20k()
    for w in words:
        if w_with_freq := ckip20k_entries.get(w.surface):
            # use first entry (highest frequency)
            w.frequency = w_with_freq[0]["freq"]
    # sort words descending by frequency and then orthographically
    words.sort(key=lambda w: (-w.frequency, w.surface))


def select_vocab_ko(data):
    char_data = data["char_data"]

    # TODO: Kengdic needs a ton of cleaning for this to work okay
    word_list: List[Word] = get_kengdic()
    char_to_pron_to_vocab = index_vocab(word_list, KoAligner())

    duplicate_used = set()
    used_vocab = set()
    for c, c_data in char_data.items():
        for pron, pron_data in c_data["prons"].items():
            words = char_to_pron_to_vocab.get(c, {}).get(pron, [])
            pron_data["vocab"] = __order_vocab(words, used_vocab)
            for w in pron_data["vocab"]:
                if w.surface in used_vocab:
                    duplicate_used.add(w.surface)
            used_vocab.update({v.surface for v in pron_data["vocab"]})

    def char_data_iter():
        for c, c_data in char_data.items():
            yield c, c_data

    _report_missing_words(char_data_iter())
    _report_duplicate_use(duplicate_used)

    return data


def select_vocab_vi(data):
    char_data = data["char_data"]
    word_list: List[Word] = get_chunom_org_vocab()
    char_to_pron_to_vocab = index_vocab(word_list, ZhAligner())

    duplicate_used = set()
    used_vocab = set()
    for c, c_data in char_data.items():
        for pron, pron_data in c_data["prons"].items():
            words = char_to_pron_to_vocab.get(c, {}).get(pron, [])
            pron_data["vocab"] = words
            for w in pron_data["vocab"]:
                if w.surface in used_vocab:
                    duplicate_used.add(w.surface)
            used_vocab.update({v.surface for v in pron_data["vocab"]})

    def char_data_iter():
        for c, c_data in char_data.items():
            yield c, c_data

    _report_missing_words(char_data_iter())
    _report_duplicate_use(duplicate_used)

    return data


def _report_missing_words(char_data_iter):
    missing_words = set()
    for c, char_data in char_data_iter:
        print(c)
        print(char_data)
        for pron, pron_data in char_data["prons"].items():
            if not pron_data["vocab"]:
                missing_words.add(f"{c}/{pron}")

    if missing_words:
        logger.warning(f"Missing vocab for {len(missing_words)} char/pron pairs")
        logger.debug(format_json(sorted(list(missing_words))))


def _report_duplicate_use(words):
    if words:
        logger.warning(f"{len(words)} duplicate vocab used")
        logger.debug(words)


SELECT_VOCAB = {
    "jp": select_vocab_jp,
    "zh": select_vocab_zh,
    "ko": select_vocab_ko,
    "vi": select_vocab_vi,
}
