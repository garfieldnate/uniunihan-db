import argparse
import json
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from typing import Any, DefaultDict, Dict, List, Mapping, Sequence, Set

from .component_group import ComponentGroup, PurityType
from .lingua.jp.aligner import Aligner
from .lingua.mandarin import pinyin_numbers_to_tone_marks
from .util import (
    GENERATED_DATA_DIR,
    HK_ED_CHARS_FILE,
    INCLUDED_DATA_DIR,
    KO_ED_CHARS_FILE,
    configure_logging,
    filter_keys,
    read_cedict,
    read_ckip_20k,
    read_edict_freq,
    read_historical_on_yomi,
    read_joyo,
    read_phonetic_components,
)

log = configure_logging(__name__)

OUTPUT_DIR = GENERATED_DATA_DIR / "regularities"


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> object:
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, ComponentGroup):
            return vars(obj)

        return json.JSONEncoder.default(self, obj)


def _incorporate_ckip_freq_data(char_to_pron_to_words) -> None:
    ckip20k_entries = read_ckip_20k()
    for pron_to_words in char_to_pron_to_words.values():
        for words in pron_to_words.values():
            for w in words:
                if w_with_freq := ckip20k_entries.get(w["trad"]):
                    # use first entry (highest frequency)
                    w["freq"] = w_with_freq[0]["freq"]
                else:
                    # -1 to indicate it's unattested in the CKIP list
                    w["freq"] = -1
            # sort words descending by frequency and then orthographically
            words.sort(key=lambda w: (-w["freq"], w["trad"]))


@dataclass
class Index:
    groups: List[ComponentGroup]
    # char -> pronuncitions
    char_to_prons: Mapping[str, Sequence[str]]
    # unique pronunciations and their corresponding character
    unique_pron_to_char: Mapping[str, str]
    # characters without any pronunciations
    no_pron_chars: Set[str]
    # characters with no pronunciation components
    no_comp_chars: Set[str]


def _index(char_to_prons, comp_to_char) -> Index:
    # Group and classify characters by component
    chars_assigned_to_a_group = set()
    groups = []
    for component, chars in comp_to_char.items():
        # comp_to_char likely contains way more characters than we need
        chars = {c for c in chars if c in char_to_prons}
        if not chars:
            continue
        c2p = {c: prons for c, prons in char_to_prons.items() if c in chars}
        group = ComponentGroup(
            component,
            c2p,
        )
        groups.append(group)
        chars_assigned_to_a_group.update(chars)

    # find characters with no assigned group
    all_chars = set(char_to_prons.keys())
    chars_with_no_group = all_chars - chars_assigned_to_a_group

    # Find characters with no listed pronunciations
    no_pron_chars = set()
    for char, prons in char_to_prons.items():
        if not prons:
            no_pron_chars.add(char)
    no_pron_chars -= chars_with_no_group

    # get unique character readings
    pron_to_chars = defaultdict(set)
    for char, char_prons in char_to_prons.items():
        for char_pron in char_prons:
            pron_to_chars[char_pron].add(char)
    unique_readings = {
        pron: next(iter(chars))
        for pron, chars in pron_to_chars.items()
        if len(chars) == 1
    }

    return Index(
        groups,
        char_to_prons,
        unique_readings,
        no_pron_chars,
        chars_with_no_group,
    )


def _format_json(data: object) -> str:
    return json.dumps(
        data,
        cls=CustomJsonEncoder,
        ensure_ascii=False,
        indent=2,
    )


def _print_reports(index: Index, char_to_prons, char_to_pron_to_vocab, out_dir) -> None:
    purity_to_chars = defaultdict(set)
    purity_to_groups: Dict[PurityType, int] = defaultdict(int)
    missing_words = set()
    for g in index.groups:
        purity_to_chars[g.purity_type].update(g.chars)
        purity_to_groups[g.purity_type] += 1
        for c in g.chars:
            missing = set(char_to_prons[c]) - set(char_to_pron_to_vocab[c].keys())
            for p in missing:
                missing_words.add(f"{c}/{p}")

    if index.no_comp_chars:
        log.warn(
            f"{len(index.no_comp_chars)} characters with no phonetic component: {index.no_comp_chars}"
        )
    if index.no_pron_chars:
        log.warn(
            f"{len(index.no_pron_chars)} characters with no pronunciations: {index.no_pron_chars}"
        )
    if missing_words:
        log.warn(f"Missing vocab for {len(missing_words)} char/pron pairs")
    log.info(f"{len(index.unique_pron_to_char)} characters with unique readings")

    log.info(f"{len(index.groups)} total groups:")
    for purity_type in PurityType:
        log.info(
            f"    {purity_to_groups[purity_type]} {purity_type.name} groups ({len(purity_to_chars[purity_type])} characters)"
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "unique_readings.json", "w") as f:
        # Characters with unique on'yomi (for the joyo data)
        f.write(_format_json(index.unique_pron_to_char))
    with open(out_dir / "missing_words.json", "w") as f:
        # Character/pronunciation pairs for which no vocab examples could be found
        f.write(_format_json(sorted(list(missing_words))))


def _print_final_output_jp(index, char_to_words, char_supplement, out_dir) -> None:
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
                    vocab_list = char_to_words[c].get(pron, [])
                    if vocab_list:
                        # find a multi-char word if possible
                        try:
                            vocab = next(
                                filter(lambda v: len(v["surface"]) > 1, vocab_list)
                            )
                        except StopIteration:
                            vocab = vocab_list[0]
                        highest_freq = max(highest_freq, vocab["freq"])
                    else:
                        vocab = None
                    pron_entry = {
                        "pron": pron,
                        "vocab": vocab,
                        "non-joyo": pron in c_sup["non-joyo"],
                    }
                    if old_pron := c_sup.get("historical_pron", {}).get(pron):
                        pron_entry["historical"] = old_pron
                    pron_entries.append(pron_entry)
                # put the Joyo pronunciations before the non-joyo ones
                pron_entries.sort(key=lambda item: (item["non-joyo"], item["pron"]))
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
        purity_2_groups[group_entry["purity"]].append(group_entry)

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

    final = OrderedDict(sorted(purity_2_groups.items(), key=lambda kv: kv[0]))

    with open(out_dir / "final_output.json", "w") as f:
        f.write(_format_json(final))


def _print_final_output_zh(
    index, char_to_pron_to_vocab, char_supplement, out_dir
) -> None:
    log.info("Constructing final output...")
    final = []
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
                        vocab = next(filter(lambda v: len(v["trad"]) > 1, vocab_list))
                    except StopIteration:
                        vocab = vocab_list[0]
                    vocab["pron"] = pinyin_numbers_to_tone_marks(vocab["pron"])
                    highest_freq = max(highest_freq, vocab["freq"])
                    pron_entry = {
                        "pron": pinyin_numbers_to_tone_marks(pron),
                        "vocab": vocab,
                    }
                    # TODO: add MC and OC reconstructions
                    # if old_pron := c_sup.get("historical_pron", {}).get(pron):
                    #     pron_entry["historical"] = old_pron
                    pron_entries.append(pron_entry)
                # sort pronunciations by vocab frequency and then alphabetically
                pron_entries.sort(
                    key=lambda item: (-item["vocab"]["freq"], item["pron"])
                )
                c_entry = {"prons": pron_entries}
                c_entry.update(c_sup)
                # already added this in pronunciation entries
                # c_entry.pop("historical_pron", None)
                cluster_entry[c] = c_entry
            # sort characters by frequency of most frequent vocab, then by character
            cluster_entry = OrderedDict(
                sorted(
                    cluster_entry.items(),
                    key=lambda item: (-item[1]["prons"][0]["vocab"]["freq"], item[0]),
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
        final.append(group_entry)

    # Sort the entries by purity type, then number of characters descending, then frequency
    # of most frequent word descending, and final orthographically by component
    final.sort(
        key=lambda g: (
            g["purity"],
            -len(g["chars"]),
            -g["highest_vocab_freq"],
            g["component"],
        )
    )

    with open(out_dir / "final_output.json", "w") as f:
        f.write(_format_json(final))


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

    comp_to_char = read_phonetic_components()

    if args.language == "jp":
        # read initial character data
        joyo = read_joyo()

        # update character information with historical kana spellings
        char_to_new_to_old_pron = read_historical_on_yomi()
        for c, new_to_old_pron in char_to_new_to_old_pron.items():
            if c_sup := joyo.char_to_supplementary_info.get(c):
                c_sup["historical_pron"] = new_to_old_pron

        # Compile a dictionary of characters to high frequency words which use them
        # Old glyphs will be presented to the user in the end, but new glyphs are
        # required for finding vocab.
        # Create aligner to determine which character pronunciations are used in a word
        aligner = Aligner(joyo.new_char_to_prons)
        # Read initial vocab list
        char_to_pron_to_vocab = read_edict_freq(aligner)
        # Add mappings for old character glyphs
        old_char_to_words = {}
        for new_char, words in char_to_pron_to_vocab.items():
            for old_c in joyo.new_to_old(new_char):
                old_char_to_words[old_c] = words
        char_to_pron_to_vocab.update(old_char_to_words)
        # Some words had to be specified manually instead of extracted from our downloaded dictionary
        jp_vocab_override = json.load(
            open(INCLUDED_DATA_DIR / "jp_vocab_override.json")
        )
        del jp_vocab_override["//"]
        char_to_pron_to_vocab.update(jp_vocab_override)

        # Extract character groups and grade their pronunciation regularities
        index = _index(joyo.old_char_to_prons, comp_to_char)
        # 国字 do not have phonetic characters, but can be usefully learned together
        index.groups.append(ComponentGroup("国字", {c: [] for c in index.no_comp_chars}))

        _print_reports(index, joyo.old_char_to_prons, char_to_pron_to_vocab, out_dir)
        _print_final_output_jp(
            index,
            char_to_pron_to_vocab,
            joyo.char_to_supplementary_info,
            out_dir,
        )
    elif args.language == "zh-HK":
        with open(HK_ED_CHARS_FILE) as f:
            char_list = set(json.load(f))
        char_to_pron_to_vocab = read_cedict(index_chars=True)
        char_to_pron_to_vocab = filter_keys(char_to_pron_to_vocab, char_list)
        _incorporate_ckip_freq_data(char_to_pron_to_vocab)
        # # get chars to prons from unihan where
        index = _index(char_to_pron_to_vocab, comp_to_char)
        # char_to_pron_to_vocab = {}  # TODO
        # char_to_supplementary_info = {}  # TODO
        _print_reports(index, char_to_pron_to_vocab, char_to_pron_to_vocab, out_dir)
        # Next: make this work

        _print_final_output_zh(
            index,
            char_to_pron_to_vocab,
            defaultdict(dict),  # char_to_supplementary_info,
            out_dir,
        )
    elif args.language == "ko":
        with open(KO_ED_CHARS_FILE) as f:
            char_list = set(json.load(f))
    else:
        log.error(f"Cannot handle language {args.language} yet")
        exit()


if __name__ == "__main__":
    main()
