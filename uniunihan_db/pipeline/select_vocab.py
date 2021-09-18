# Step 4: Add useful vocabulary that illustrates the
# pronunciations of each character

from typing import List

from uniunihan_db.data.datasets import (
    get_cedict,
    get_ckip_20k,
    get_edict_freq,
    get_vocab_override,
    index_vocab,
)
from uniunihan_db.data.types import Char2Pron2Words, Word, ZhWord
from uniunihan_db.data_paths import JP_VOCAB_OVERRIDE
from uniunihan_db.lingua.aligner import JpAligner, SpaceAligner
from uniunihan_db.util import configure_logging, format_json

log = configure_logging(__name__)

MAX_EXAMPLE_VOCAB = 2


def select_vocab_jp(data, out_dir):
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

    for old_c, c_data in char_data.items():
        # Vocab override uses old forms, edict vocab data uses new forms
        if pron_to_words := vocab_override.get(old_c):
            for pron, words in pron_to_words.items():
                c_data["prons"].get(pron, {})["vocab"] = words
        else:
            new_c = c_data["new"]
            for pron, pron_data in c_data["prons"].items():
                words = char_to_pron_to_vocab.get(new_c, {}).get(pron, [])
                pron_data["vocab"] = __filter_vocab(words)

    def char_data_iter():
        for c_data in char_data.values():
            yield c_data["new"], c_data

    _report_missing_words(char_data_iter(), out_dir)

    return data


def __filter_vocab(words):
    """Take the top MAX_EXAMPLE_VOCAB which contain 2 or more characters (words should be pre-sorted by frequency)"""
    return list(filter(lambda w: len(w.surface) > 1, words))[:MAX_EXAMPLE_VOCAB]


def select_vocab_zh_hk(data, out_dir):
    char_data = data["char_data"]
    word_list: List[ZhWord] = get_cedict()
    _incorporate_ckip_freq_data(word_list)
    char_to_pron_to_vocab = index_vocab(word_list, SpaceAligner())

    for c, c_data in char_data.items():
        for pron, pron_data in c_data["prons"].items():
            words = char_to_pron_to_vocab.get(c, {}).get(pron, [])
            pron_data["vocab"] = __filter_vocab(words)

    def char_data_iter():
        for c, c_data in char_data.items():
            yield c, c_data

    _report_missing_words(char_data_iter(), out_dir)

    return data


def _incorporate_ckip_freq_data(words: List[ZhWord]) -> None:
    ckip20k_entries = get_ckip_20k()
    for w in words:
        if w_with_freq := ckip20k_entries.get(w.surface):
            # use first entry (highest frequency)
            w.frequency = w_with_freq[0]["freq"]
    # sort words descending by frequency and then orthographically
    words.sort(key=lambda w: (-w.frequency, w.surface))


def select_vocab_ko(data, out_dir):
    char_data = data["char_data"]
    for c, c_data in char_data.items():
        for pron, pron_data in c_data["prons"].items():
            # TODO: need Korean vocab data
            pron_data["vocab"] = []
    return data


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
