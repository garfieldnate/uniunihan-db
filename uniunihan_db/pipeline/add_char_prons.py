# Step 2: gather pronunciations for each character
# Final structure: {char -> {char data, 'prons': {pron1: {pron data}, pron2: {pron data}...}}}

from typing import List

from uniunihan_db.data.datasets import get_cedict, index_vocab
from uniunihan_db.data.types import ZhWord
from uniunihan_db.data_paths import PIPELINE_OUTPUT_DIR
from uniunihan_db.lingua.aligner import SpaceAligner
from uniunihan_db.util import configure_logging

log = configure_logging(__name__)

OUTPUT_DIR = PIPELINE_OUTPUT_DIR / "chars"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_prons_jp(char_data):
    # no new data loading; only requires restructuring
    for _, c_data in char_data.items():
        c_data["prons"] = prons = {}
        for pron in c_data["readings"]:
            prons[pron] = pron_data = {}
            if old_pron := c_data.get("historical_pron", {}).get(pron):
                pron_data["historical"] = old_pron
                del c_data["historical_pron"][pron]
        del c_data["readings"]
        try:
            del c_data["historical_pron"]
        except KeyError:
            pass

    return char_data


def load_prons_zh_hk(char_data):
    word_list: List[ZhWord] = get_cedict()
    char_to_pron_to_vocab = index_vocab(word_list, SpaceAligner())

    for c, pron_to_vocab in char_to_pron_to_vocab.items():
        if c_data := char_data.get(c):
            prons = c_data.setdefault("prons", {})
            for p, _ in pron_to_vocab.items():
                prons[p] = {}

    return char_data


def load_prons_ko(char_data):
    # no new data loading; only requires restructuring
    for _, c_data in char_data.items():
        c_data["prons"] = prons = {}
        if pron := c_data.get("eum"):
            prons[pron] = {}
            del c_data["eum"]

    return char_data


ADD_PRONUNCIATIONS = {
    "jp": load_prons_jp,
    "zh-HK": load_prons_zh_hk,
    "ko": load_prons_ko,
}
