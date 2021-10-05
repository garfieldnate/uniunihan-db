# Step 2: gather pronunciations for each character
# Final structure: {char -> {char data, 'prons': {pron1: {pron data}, pron2: {pron data}...}}}

from typing import List

from loguru import logger

from uniunihan_db.data.datasets import get_cedict, get_unihan, index_vocab
from uniunihan_db.data.types import ZhWord
from uniunihan_db.lingua.aligner import ZhAligner
from uniunihan_db.lingua.mandarin import pinyin_tone_marks_to_numbers
from uniunihan_db.util import format_json


def load_prons_jp(char_data):
    # Use pronunciations from Joyo specification.
    # This only requires restructuring; no new data loading.
    for _, c_data in char_data.items():
        c_data["prons"] = prons = {}
        for pron in c_data["readings"]:
            prons[pron] = pron_data = {}
            pron_data["joyo"] = pron not in c_data["non_joyo"]
            if old_pron := c_data.get("historical_pron", {}).get(pron):
                pron_data["historical"] = old_pron
                del c_data["historical_pron"][pron]
            else:
                pron_data["historical"] = None
        # delete copied keys
        del c_data["readings"]
        del c_data["non_joyo"]
        try:
            del c_data["historical_pron"]
        except KeyError:
            pass

    return char_data


def load_prons_zh(char_data):
    # Get pronunciations that are used in modern words present in CEDICT. This allows
    # us to guarantee that we have examples for most pronunciations, and avoids super
    # obscure pronunciations that increase the grouping complexity significantly.
    # If a character is not found in CEDICT, fall back to using Unihan pronunciation data.
    # Supplement all pronunciations with with kHanyuPinlu pronunciation frequency data.

    word_list: List[ZhWord] = get_cedict()
    char_to_pron_to_vocab = index_vocab(word_list, ZhAligner())
    for c, pron_to_vocab in char_to_pron_to_vocab.items():
        if c_data := char_data.get(c):
            prons = c_data.setdefault("prons", {})
            for p, _ in pron_to_vocab.items():
                prons[p] = {}

    unihan = get_unihan()
    fallback_chars = set()
    no_pron_chars = set()
    for c, c_data in char_data.items():
        unihan_prons = __get_mandarin_pronunciations(unihan[c])
        if "prons" not in c_data:
            if unihan_prons:
                fallback_chars.add(c)
                c_data["prons"] = unihan_prons
            else:
                no_pron_chars.add(c)
        else:
            for p, up_data in unihan_prons.items():
                if p in c_data["prons"] and "frequency" in up_data:
                    c_data["prons"][p]["frequency"] = up_data["frequency"]

    if fallback_chars:
        logger.warning(
            f"Fell back to using Mandarin readings from Unihan for {len(fallback_chars)} characters"
        )
        logger.debug(format_json(fallback_chars))
    if no_pron_chars:
        logger.warning(f"No pronunciations found for {len(no_pron_chars)} characters")
        logger.debug(no_pron_chars)

    return char_data


def __get_mandarin_pronunciations(unihan_entry):
    # check all of the available fields in order of usefulness/accuracy
    if pron := unihan_entry.get("kHanyuPinlu"):
        return {
            pinyin_tone_marks_to_numbers(p["phonetic"]): {"frequency": p["frequency"]}
            for p in pron
        }
    elif pron := unihan_entry.get("kXHC1983"):
        return {pinyin_tone_marks_to_numbers(p["reading"]): {} for p in pron}
    elif pron := unihan_entry.get("kHanyuPinyin"):
        return {
            pinyin_tone_marks_to_numbers(r): {} for p in pron for r in p["readings"]
        }
    elif pron := unihan_entry.get("kMandarin"):
        return {pinyin_tone_marks_to_numbers(pron["zh-Hans"]): {}}
    return {}


def load_prons_ko(char_data):
    # no new data loading; only requires restructuring
    for _, c_data in char_data.items():
        c_data["prons"] = prons = {}
        if pron := c_data.get("eum"):
            prons[pron] = {}
            del c_data["eum"]

    return char_data


def load_prons_vi(char_data):
    # no new data loading; only requires restructuring
    for _, c_data in char_data.items():
        c_data["prons"] = {p: {} for p in c_data["prons"]}

    return char_data


ADD_PRONUNCIATIONS = {
    "jp": load_prons_jp,
    "zh": load_prons_zh,
    "ko": load_prons_ko,
    "vi": load_prons_vi,
}
