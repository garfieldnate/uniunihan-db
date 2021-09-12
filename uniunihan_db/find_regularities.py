import argparse
from collections import defaultdict
from typing import List

# allows commenting lines with # or //
import commentjson as json

from uniunihan_db.compile import compile_final_output
from uniunihan_db.component.group import ComponentGroup
from uniunihan_db.component.index import ComponentGroupIndex, find_component_groups
from uniunihan_db.data.types import Char2Pron2Words, ZhWord
from uniunihan_db.data_paths import (
    GENERATED_DATA_DIR,
    HK_ED_CHARS_FILE,
    JP_VOCAB_OVERRIDE,
    KO_ED_CHARS_FILE,
)

from .data.datasets import (
    Joyo,
    StringToStrings,
    Word,
    get_cedict,
    get_ckip_20k,
    get_edict_freq,
    get_historical_on_yomi,
    get_joyo,
    get_phonetic_components,
    get_unihan,
    get_vocab_override,
    index_vocab,
)
from .lingua.aligner import JpAligner, SpaceAligner
from .util import configure_logging, filter_keys, format_json

log = configure_logging(__name__)

OUTPUT_DIR = GENERATED_DATA_DIR / "regularities"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--language",
        # sanity check against Heisig Volume II
        default="jp",
        choices=["jp", "zh-ZH", "zh-HK"],
        help="",
    )

    args = parser.parse_args()
    out_dir = OUTPUT_DIR / args.language

    comp_to_char = get_phonetic_components()

    if args.language == "jp":
        main_jp(args, out_dir, comp_to_char)
    elif args.language == "zh-HK":
        main_zh_hk(args, out_dir, comp_to_char)
    elif args.language == "ko":
        main_ko(args, out_dir, comp_to_char)
    else:
        log.error(f"Cannot handle language {args.language} (yet)")
        exit()


def main_jp(args, out_dir, comp_to_char: StringToStrings):
    joyo = _load_jp_character_data()

    char_to_pron_to_vocab = _load_jp_char_pron_vocab(joyo)

    index = find_component_groups(joyo.old_char_to_prons, comp_to_char)
    # 国字 do not have phonetic characters, but can be usefully learned together
    index.groups.append(ComponentGroup("国字", {c: [] for c in index.no_comp_chars}))
    index.log_diagnostics(log, out_dir)

    _report_missing_words(index, joyo.old_char_to_prons, char_to_pron_to_vocab, out_dir)

    final = _compile_final_output_jp(
        index,
        char_to_pron_to_vocab,
        joyo.char_to_supplementary_info,
    )

    with open(out_dir / "final_output.json", "w") as f:
        f.write(format_json(final))


def _load_jp_character_data() -> Joyo:
    # read initial character data
    joyo = get_joyo()

    # update character information with historical kana spellings
    char_to_new_to_old_pron = get_historical_on_yomi()
    for c, new_to_old_pron in char_to_new_to_old_pron.items():
        if c_sup := joyo.char_to_supplementary_info.get(c):
            c_sup["historical_pron"] = new_to_old_pron

    return joyo


def _load_jp_char_pron_vocab(joyo: Joyo):
    """Compile a dictionary of characters to high frequency words which use them.
    Old glyphs will be presented to the user in the end, but new glyphs are
    required for finding vocab."""

    # Read initial vocab list
    word_list: List[Word] = get_edict_freq()
    aligner = JpAligner(joyo.new_char_to_prons)
    char_to_pron_to_vocab: Char2Pron2Words = index_vocab(word_list, aligner)

    # some pronunciations listed in the Joyo data might not have an example word, so just add an empty list
    for c, info in joyo.char_to_supplementary_info.items():
        pron_to_vocab = char_to_pron_to_vocab[c]
        for pron in info["readings"]:
            if pron not in pron_to_vocab:
                pron_to_vocab[pron] = []

    # Add mappings for old character glyphs
    old_char_to_words = {}
    for new_char, words in char_to_pron_to_vocab.items():
        for old_c in joyo.new_to_old(new_char):
            old_char_to_words[old_c] = words
    char_to_pron_to_vocab.update(old_char_to_words)

    # Some words have to be specified manually instead of extracted from our downloaded dictionary
    jp_vocab_override = get_vocab_override(JP_VOCAB_OVERRIDE)
    char_to_pron_to_vocab.update(jp_vocab_override)

    return char_to_pron_to_vocab


def _find_jp_component_groups(
    char_to_prons,
    comp_to_char,
    out_dir,
) -> ComponentGroupIndex:
    index = find_component_groups(char_to_prons, comp_to_char)
    # 国字 do not have phonetic characters, but can be usefully learned together
    index.groups.append(ComponentGroup("国字", {c: [] for c in index.no_comp_chars}))
    index.log_diagnostics(log, out_dir)

    return index


def _compile_final_output_jp(
    index: ComponentGroupIndex,
    char_to_pron_to_vocab: Char2Pron2Words,
    char_supplement,
):
    # put the Joyo pronunciations before the non-joyo ones # TODO: no frequency?
    def pron_entry_sort_key(pron_entry):
        return (pron_entry["non_joyo"], pron_entry["pron"])

    def augment(c, c_entry):
        c_sup = char_supplement[c]
        for pron_entry in c_entry["prons"]:
            pron = pron_entry["pron"]
            pron_entry["non_joyo"] = pron in c_sup["non_joyo"]

            if old_pron := c_sup.get("historical_pron", {}).get(pron):
                pron_entry["historical"] = old_pron

        c_entry.update(c_sup)
        # already added this in pronunciation entries
        c_entry.pop("historical_pron", None)

    return compile_final_output(
        index,
        char_to_pron_to_vocab,
        pron_entry_sort_key,
        augment,
    )


def main_zh_hk(args, out_dir, comp_to_char: StringToStrings):
    with open(HK_ED_CHARS_FILE) as f:
        char_list = set(json.load(f))
    char_to_supplementary_info = _zh_supplementary_info(char_list)

    char_to_pron_to_vocab = _load_zh_char_pron_vocab(char_list)

    index = find_component_groups(char_to_pron_to_vocab, comp_to_char)
    index.log_diagnostics(log, out_dir)

    _report_missing_words(index, char_to_pron_to_vocab, char_to_pron_to_vocab, out_dir)

    final = _compile_final_output_zh(
        index,
        char_to_pron_to_vocab,
        char_to_supplementary_info,
    )

    with open(out_dir / "final_output.json", "w") as f:
        f.write(format_json(final))


def _load_zh_char_pron_vocab(char_list):
    word_list: List[ZhWord] = get_cedict()
    _incorporate_ckip_freq_data(word_list)
    char_to_pron_to_vocab = index_vocab(word_list, SpaceAligner())
    char_to_pron_to_vocab = filter_keys(char_to_pron_to_vocab, char_list)

    return char_to_pron_to_vocab


def _incorporate_ckip_freq_data(words: List[ZhWord]) -> None:
    ckip20k_entries = get_ckip_20k()
    for w in words:
        if w_with_freq := ckip20k_entries.get(w.surface):
            # use first entry (highest frequency)
            w.frequency = w_with_freq[0]["freq"]
    # sort words descending by frequency and then orthographically
    words.sort(key=lambda w: (-w.frequency, w.surface))


def _zh_supplementary_info(char_list):
    unihan = get_unihan()
    sup_info = defaultdict(dict)
    for char in char_list:
        sup_info[char]["trad"] = char
        if simplified := unihan[char].get("kSimplifiedVariant", []):
            sup_info[char]["simp"] = simplified

    return sup_info


def _compile_final_output_zh(
    index, char_to_pron_to_vocab: Char2Pron2Words, char_supplement
):
    def pron_entry_sort_key(pron_entry):
        return (-pron_entry["vocab"].frequency, pron_entry["pron"])

    def augment(c, c_entry):
        c_sup = char_supplement[c]
        c_entry.update(c_sup)

    return compile_final_output(
        index,
        char_to_pron_to_vocab,
        pron_entry_sort_key,
        augment,
    )


def main_ko(args, out_dir, comp_to_char):
    with open(KO_ED_CHARS_FILE) as f:
        char_list = set(json.load(f))
        print(char_list)


# Utility methods used in all languages


def _report_missing_words(
    index: ComponentGroupIndex, char_to_prons, char_to_pron_to_vocab, out_dir
):
    missing_words = set()
    for g in index.groups:
        for c in g.chars:
            missing = set(char_to_prons[c]) - set(char_to_pron_to_vocab[c].keys())
            for p in missing:
                missing_words.add(f"{c}/{p}")

    if missing_words:
        log.warn(f"Missing vocab for {len(missing_words)} char/pron pairs")

    with open(out_dir / "missing_words.json", "w") as f:
        # Character/pronunciation pairs for which no vocab examples could be found
        f.write(format_json(sorted(list(missing_words))))


if __name__ == "__main__":
    main()
