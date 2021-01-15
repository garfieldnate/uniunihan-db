import argparse
import csv
import dataclasses
import json
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, List, Set

from .component_group import ComponentGroup, PurityType
from .util import GENERATED_DATA_DIR, INCLUDED_DATA_DIR, Aligner, configure_logging

log = configure_logging(__name__)

OUTPUT_DIR = GENERATED_DATA_DIR / "regularities"


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        elif dataclasses.is_dataclass(obj):
            return vars(obj)

        return json.JSONEncoder.default(self, obj)


def _read_joyo():
    log.info("Loading joyo data...")
    new_char_to_prons = {}
    old_char_to_prons = {}
    with open(INCLUDED_DATA_DIR / "joyo.csv") as f:
        # filter comments
        rows = csv.DictReader(filter(lambda row: row[0] != "#", f))
        for r in rows:
            readings = r["on-yomi"].split("|")
            # remove empty readings;
            # forget about parenthesized readings; focus on the main reading for pattern finding
            readings = [yomi for yomi in readings if yomi and "（" not in yomi]
            for c in r["new"]:
                new_char_to_prons[c] = readings
            # old glyph same as new glyph when missing
            for c in r["old"] or r["new"]:
                old_char_to_prons[c] = readings

    return old_char_to_prons, new_char_to_prons


def _read_edict_freq(aligner):
    log.info("Loading EDICT frequency list...")
    char_to_pron_to_words = defaultdict(lambda: defaultdict(list))
    with open(GENERATED_DATA_DIR / "edict-freq.tsv") as f:
        num_words = 0
        for line in f.readlines():
            line = line.strip()
            surface, surface_normalized, pronunciation, frequency = line.split("\t")
            alignment = aligner.align(surface_normalized, pronunciation)
            if alignment:
                for c, pron in alignment.items():
                    char_to_pron_to_words[c][pron].append(surface)
                num_words += 1
    return char_to_pron_to_words


def _read_unihan():
    log.info("Loading unihan data...")
    # TODO: read path from constants file
    with open(GENERATED_DATA_DIR / "unihan.json") as f:
        unihan = json.load(f)

    return unihan


def _get_hk_ed_chars(unihan):
    def get_pron(info):
        # check all of the available fields in order of usefulness/accuracy
        if pron := info.get("kHanyuPinlu"):
            #             print('returning pinlu')
            return [p["phonetic"] for p in pron]
        elif pron := info.get("kXHC1983"):
            #             print('returning 1983')
            return [p["reading"] for p in pron]
        elif pron := info.get("kHanyuPinyin"):
            #             print('returning pinyin!')
            return [r for p in pron for r in p["readings"]]
        elif pron := info.get("kMandarin"):
            print("returning mandarin!")
            return pron["zh-Hans"]
        return []

    chars = {}
    for char, info in unihan.items():
        if "kGradeLevel" in info:
            prons = get_pron(info)
            chars[char] = prons
    return chars


def _read_phonetic_components():
    log.info("Loading phonetic components...")
    char_to_component = {}
    with open(GENERATED_DATA_DIR / "chars_to_components.tsv") as f:
        rows = csv.DictReader(f, delimiter="\t")
        for r in rows:
            char = r["character"]
            component = r["component"]
            char_to_component[char] = component

    return char_to_component


def _read_jp_netflix(aligner, max_words=1_000_000):
    log.info("Loading Netflix frequency list...")
    char_to_pron_to_words = defaultdict(lambda: defaultdict(list))
    with open(INCLUDED_DATA_DIR / "jp_Netflix10K.txt") as f:
        num_words = 0
        for line in f.readlines():
            if not line.startswith("#"):
                line = line.strip()
                surface, pronunciation = line.split("\t")
                alignment = aligner.align(surface, pronunciation)
                if alignment:
                    for c, pron in alignment.items():
                        char_to_pron_to_words[c][pron].append(surface)
                    num_words += 1
                    if num_words == max_words:
                        break
    return char_to_pron_to_words


def _get_component_groups(index):
    groups = []
    for component, pron_to_chars in index.comp_pron_char.items():
        group = ComponentGroup(
            component,
            # sort pronunciations by number of characters
            OrderedDict(sorted(pron_to_chars.items(), key=lambda item: -len(item[1]))),
        )
        groups.append(group)

    # Organize and sort the groups for easier inspection
    return sorted(groups, key=lambda g: (g.purity_type, -len(g.chars)))


@dataclass
class Index:
    # char -> pronuncitions
    char_to_prons: Dict[str, List[str]]
    # component -> pronunciation -> chars with component and pronunciation
    comp_pron_char: DefaultDict[str, DefaultDict[str, List[str]]]
    # component -> chars containing it
    comp_to_char: DefaultDict[str, Set[str]]
    # char -> components it contains
    char_to_comp: Dict[str, str]
    # pronuncation -> all chars with that pronunciation
    pron_to_chars: Dict[str, Set[str]]
    # unique pronunciations and their corresponding character
    unique_pron_to_char: Dict[str, str]
    # characters without any pronunciations
    no_pron_chars: List[str]
    # characters with no pronunciation components
    no_comp_chars: Set[str]


def _index(char_to_prons, char_to_comp):
    # component -> pronunciation -> character
    comp_pron_char = defaultdict(lambda: defaultdict(list))
    pron_to_chars = defaultdict(set)
    comp_to_char = defaultdict(set)
    no_comp_chars = set()
    no_pron_chars = set()
    for char, char_prons in char_to_prons.items():
        if char not in char_to_comp:
            no_comp_chars.add(char)
            continue
        component = char_to_comp[char]
        comp_to_char[component].add(char)
        if not char_prons:
            no_pron_chars.add(char)
            continue
        for char_pron in char_prons:
            pron_to_chars[char_pron].add(char)
            comp_pron_char[component][char_pron].append(char)

    # get the characters which have a unique reading
    unique_readings = {}
    for pron, chars in pron_to_chars.items():
        if len(chars) == 1:
            unique_readings[pron] = next(iter(chars))

    # ensure that pronunciations are ordered deterministically in char_to_prons dictionary
    char_to_prons = {k: sorted(v) for k, v in char_to_prons.items()}

    return Index(
        char_to_prons,
        comp_pron_char,
        comp_to_char,
        char_to_comp,
        pron_to_chars,
        unique_readings,
        no_pron_chars,
        no_comp_chars,
    )


def _get_vocab_per_char_pron(char_to_prons, char_to_pron_to_words):
    """char_to_prons: dict character -> iterable of pronunciations
    char_to_pron_to_words: dict character -> pronunciation -> list
    of vocab sorted by frequency of use"""

    found_words = []
    missing_words = []
    prons_to_move = defaultdict(list)
    for char, prons in char_to_prons.items():
        for p in prons:
            if word := char_to_pron_to_words.get(char, {}).get(p):
                found_words.append(f"{char}/{p}: {word}")
                prons_to_move[char].append(p)
            else:
                missing_words.append(f"{char}/{p}")

    return found_words, missing_words


def _format_json(data):
    return json.dumps(
        data,
        cls=CustomJsonEncoder,
        ensure_ascii=False,
        indent=2,
    )


def main():
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

    char_to_comp = _read_phonetic_components()

    if args.language == "jp":
        # old glyphs give a better matching with non-Japanese datasets
        # new glyphs are matchable against modern word lists
        char_to_prons, new_char_to_prons = _read_joyo()
        aligner = Aligner(new_char_to_prons)
        # char_to_pron_to_vocab = _read_jp_netflix(aligner, 10000)
        char_to_pron_to_vocab = _read_edict_freq(aligner)
        found_words, missing_words = _get_vocab_per_char_pron(
            new_char_to_prons, char_to_pron_to_vocab
        )
    elif args.language == "zh-HK":
        unihan = _read_unihan()
        char_to_prons = _get_hk_ed_chars(unihan)
        # print(char_to_prons)
        # get chars to prons from unihan where
    # elif args.language == 'zh-Zh':
    else:
        log.error(f"Cannot handle language {args.language} yet")
        exit()

    index = _index(char_to_prons, char_to_comp)
    groups = _get_component_groups(index)

    purity_to_chars = defaultdict(set)
    purity_to_groups = defaultdict(int)
    exceptional_chars = set()
    for g in groups:
        purity_to_chars[g.purity_type].update(g.chars)
        purity_to_groups[g.purity_type] += 1
        exceptional_chars.update(g.exceptions.values())

    log.info(
        f"{len(index.no_comp_chars)} characters with no phonetic component data: {index.no_comp_chars}"
    )
    log.info(f"{len(index.no_pron_chars)} characters with no pronunciations")
    log.info(f"{len(index.unique_pron_to_char)} characters with unique readings")

    log.info(f"{len(groups)} total groups:")
    for purity_type in PurityType:
        log.info(
            f"    {purity_to_groups[purity_type]} {purity_type.name} groups ({len(purity_to_chars[purity_type])} characters)"
        )

    log.info(
        f"Found words for {len(found_words)}/{len(found_words) + len(missing_words)} words"
    )

    out_dir = OUTPUT_DIR / args.language
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "groups.json", "w") as f:
        f.write(_format_json(groups))
    with open(out_dir / "unique_readings.json", "w") as f:
        f.write(_format_json(index.unique_pron_to_char))
    with open(out_dir / "no_readings.json", "w") as f:
        f.write(_format_json(index.no_pron_chars))
    with open(out_dir / "found_words.json", "w") as f:
        f.write(_format_json(found_words))


if __name__ == "__main__":
    main()
