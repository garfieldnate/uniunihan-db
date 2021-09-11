import argparse
from collections import OrderedDict, defaultdict
from typing import DefaultDict, List

# allows commenting lines with # or //
import commentjson as json

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
from .lingua.mandarin import pinyin_numbers_to_tone_marks
from .util import configure_logging, filter_keys, format_json

log = configure_logging(__name__)

OUTPUT_DIR = GENERATED_DATA_DIR / "regularities"


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


def _print_final_output_jp(
    index, char_to_pron_to_vocab: Char2Pron2Words, char_supplement, out_dir
) -> None:
    log.info("Constructing final output...")
    purity_2_groups = DefaultDict(list)
    for g in index.groups:
        # keep track of highest frequency vocab used in the group
        highest_freq = -1
        cluster_entries = []
        for cluster in g.get_char_presentation():
            cluster_entry = {}
            for c in cluster:
                c_sup = char_supplement[c]
                pron_entries = []
                for pron in c_sup["readings"]:
                    vocab_list = char_to_pron_to_vocab[c].get(pron, [])
                    vocab: Word
                    if vocab_list:
                        # find a multi-char word if possible
                        try:
                            vocab = next(
                                filter(lambda v: len(v.surface) > 1, vocab_list)
                            )
                        except StopIteration:
                            vocab = vocab_list[0]
                        highest_freq = max(highest_freq, vocab.frequency)
                    pron_entry = {
                        "pron": pron,
                        "vocab": vocab,
                        "non_joyo": pron in c_sup["non_joyo"],
                    }
                    if old_pron := c_sup.get("historical_pron", {}).get(pron):
                        pron_entry["historical"] = old_pron
                    pron_entries.append(pron_entry)
                # put the Joyo pronunciations before the non-joyo ones
                pron_entries.sort(key=lambda item: (item["non_joyo"], item["pron"]))
                c_entry = {"prons": pron_entries}
                c_entry.update(c_sup)
                # already added this in pronunciation entries
                c_entry.pop("historical_pron", None)
                cluster_entry[c] = c_entry
            cluster_entries.append(cluster_entry)
        group_entry = {
            "component": g.component,
            "clusters": cluster_entries,
            "purity": g.purity_type,
            "chars": g.chars,
            "highest_vocab_freq": highest_freq,
        }
        purity_2_groups[g.purity_type].append(group_entry)

    for groups in purity_2_groups.values():
        # Sort the entries by purity type, then number of characters descending, then frequency
        # of most frequent word descending, and final orthographically by component
        groups.sort(
            key=lambda g: (
                g["purity"],
                -len(g["chars"]),
                -g["highest_vocab_freq"],
                g["component"],
            )
        )

    # sort keys by purity integer value
    final = OrderedDict(sorted(purity_2_groups.items(), key=lambda kv: kv[0]))

    with open(out_dir / "final_output.json", "w") as f:
        f.write(format_json(final))


def _print_final_output_zh(
    index, char_to_pron_to_vocab: Char2Pron2Words, char_supplement, out_dir
) -> None:

    log.info("Constructing final output...")

    def pron_entry_sort_key(pron_entry):
        return (-pron_entry["vocab"].frequency, pron_entry["pron"])

    def cluster_sort_key(cluster):
        return (-cluster[1]["prons"][0]["vocab"].frequency, cluster[0])

    purity_2_groups = DefaultDict(list)
    for g in index.groups:
        # keep track of highest frequency vocab used in the group
        highest_freq = -1
        cluster_entries = []
        for cluster in g.get_char_presentation():
            cluster_entry = OrderedDict()
            for c in cluster:
                c_sup = char_supplement[c]
                pron_entries = []
                for pron, vocab_list in char_to_pron_to_vocab[c].items():
                    # find a multi-char word if possible
                    try:
                        word = next(filter(lambda w: len(w.surface) > 1, vocab_list))
                    except StopIteration:
                        word = vocab_list[0]
                    # TODO: convert pronunciation string later
                    pron = pinyin_numbers_to_tone_marks(pron)
                    word.pron = pinyin_numbers_to_tone_marks(word.pron)
                    highest_freq = max(highest_freq, word.frequency)
                    pron_entry = {
                        "pron": pron,
                        "vocab": word,
                    }
                    # TODO: add MC and OC reconstructions
                    # if old_pron := c_sup.get("historical_pron", {}).get(pron):
                    #     pron_entry["historical"] = old_pron
                    pron_entries.append(pron_entry)
                # sort pronunciations by vocab frequency and then alphabetically
                pron_entries.sort(key=pron_entry_sort_key)
                c_entry = {"prons": pron_entries}
                c_entry.update(c_sup)
                # already added this in pronunciation entries
                # c_entry.pop("historical_pron", None)
                cluster_entry[c] = c_entry
            # sort characters by frequency of most frequent vocab, then by character
            cluster_entry = OrderedDict(
                sorted(
                    cluster_entry.items(),
                    key=cluster_sort_key
                    # key=lambda item: (-item[1]["prons"][0]["vocab"].frequency, item[0]),
                )
            )
            cluster_entries.append(cluster_entry)
        group_entry = {
            "component": g.component,
            "clusters": cluster_entries,
            "purity": g.purity_type,
            "chars": g.chars,
            "highest_vocab_freq": highest_freq,
        }
        purity_2_groups[g.purity_type].append(group_entry)

    for groups in purity_2_groups.values():
        # Sort the entries by purity type, then number of characters descending, then frequency
        # of most frequent word descending, and final orthographically by component
        groups.sort(
            key=lambda g: (
                g["purity"],
                -len(g["chars"]),
                -g["highest_vocab_freq"],
                g["component"],
            )
        )

    # sort keys by purity integer value
    final = OrderedDict(sorted(purity_2_groups.items(), key=lambda kv: kv[0]))

    with open(out_dir / "final_output.json", "w") as f:
        f.write(format_json(final))


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
        log.error(f"Cannot handle language {args.language} yet")
        exit()


def main_jp(args, out_dir, comp_to_char: StringToStrings):
    # read initial character data
    joyo = get_joyo()

    # update character information with historical kana spellings
    char_to_new_to_old_pron = get_historical_on_yomi()
    for c, new_to_old_pron in char_to_new_to_old_pron.items():
        if c_sup := joyo.char_to_supplementary_info.get(c):
            c_sup["historical_pron"] = new_to_old_pron

    # Compile a dictionary of characters to high frequency words which use them
    # Old glyphs will be presented to the user in the end, but new glyphs are
    # required for finding vocab.

    # Create aligner to determine which character pronunciations are used in a word
    aligner = JpAligner(joyo.new_char_to_prons)

    # Read initial vocab list
    word_list: List[Word] = get_edict_freq()
    char_to_pron_to_vocab: Char2Pron2Words = index_vocab(word_list, aligner)

    # Add mappings for old character glyphs
    old_char_to_words = {}
    for new_char, words in char_to_pron_to_vocab.items():
        for old_c in joyo.new_to_old(new_char):
            old_char_to_words[old_c] = words
    char_to_pron_to_vocab.update(old_char_to_words)

    # Some words have to be specified manually instead of extracted from our downloaded dictionary
    jp_vocab_override = get_vocab_override(JP_VOCAB_OVERRIDE)
    char_to_pron_to_vocab.update(jp_vocab_override)

    # Extract character groups and grade their pronunciation regularities
    index = find_component_groups(joyo.old_char_to_prons, comp_to_char)
    # 国字 do not have phonetic characters, but can be usefully learned together
    index.groups.append(ComponentGroup("国字", {c: [] for c in index.no_comp_chars}))
    index.log_diagnostics(log, out_dir)
    _report_missing_words(index, joyo.old_char_to_prons, char_to_pron_to_vocab, out_dir)

    _print_final_output_jp(
        index,
        char_to_pron_to_vocab,
        joyo.char_to_supplementary_info,
        out_dir,
    )


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


def main_zh_hk(args, out_dir, comp_to_char: StringToStrings):
    with open(HK_ED_CHARS_FILE) as f:
        char_list = set(json.load(f))
    word_list: List[ZhWord] = get_cedict()
    _incorporate_ckip_freq_data(word_list)
    char_to_pron_to_vocab = index_vocab(word_list, SpaceAligner())
    char_to_pron_to_vocab = filter_keys(char_to_pron_to_vocab, char_list)
    # get chars to prons from unihan where TODO
    index = find_component_groups(char_to_pron_to_vocab, comp_to_char)
    index.log_diagnostics(log, out_dir)
    _report_missing_words(index, char_to_pron_to_vocab, char_to_pron_to_vocab, out_dir)

    char_to_supplementary_info = _zh_supplementary_info(char_list)

    _print_final_output_zh(
        index,
        char_to_pron_to_vocab,
        char_to_supplementary_info,
        out_dir,
    )


def main_ko(args, out_dir, comp_to_char):
    with open(KO_ED_CHARS_FILE) as f:
        char_list = set(json.load(f))
        print(char_list)


if __name__ == "__main__":
    main()
