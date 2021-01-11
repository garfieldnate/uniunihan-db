import argparse
import csv
import dataclasses
import json
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from enum import IntEnum
from typing import DefaultDict, Dict, List, Set

from .util import GENERATED_DATA_DIR, INCLUDED_DATA_DIR, Aligner, configure_logging

log = configure_logging(__name__)

OUTPUT_DIR = GENERATED_DATA_DIR / "regularities"


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        elif dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)

        return json.JSONEncoder.default(self, obj)


def _read_joyo(use_old_glyphs=True):
    # Using the old forms of the characters can find more regularities
    log.info(f"Loading joyo ({'old' if use_old_glyphs else 'new'} glyph) data...")
    chars = {}
    radicals = {}
    if use_old_glyphs:
        glyph_type = "old"
        glyph_type_backup = "new"
    else:
        glyph_type = "new"
        glyph_type_backup = "old"
    with open(INCLUDED_DATA_DIR / "joyo.csv") as f:
        # filter comments
        rows = csv.DictReader(filter(lambda row: row[0] != "#", f))
        for r in rows:
            readings = r["on-yomi"].split("|")
            # remove empty readings;
            # forget about parenthesized readings; focus on the main reading for pattern finding
            readings = [yomi for yomi in readings if yomi and "（" not in yomi]
            char = r[glyph_type] or r[glyph_type_backup]
            for c in char:
                chars[c] = readings
                radicals[c] = r["radical"]

    return chars, radicals


def _read_unihan():
    log.info("Loading unihan data...")
    # TODO: read path from constants file
    with open(GENERATED_DATA_DIR / "unihan.json") as f:
        unihan = json.load(f)

    log.info("Loading reverse compatibility variants...")
    with open(GENERATED_DATA_DIR / "reverse_compatibility_variants.json") as f:
        reverse_compat_variants = json.load(f)
    for char, variants in reverse_compat_variants.items():
        unihan[char]["kReverseCompatibilityVariants"] = variants

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


def _read_ytenx(unihan):
    log.info("Loading phonetic components...")
    char_to_component = {}
    with open(
        GENERATED_DATA_DIR
        / "ytenx-master"
        / "ytenx"
        / "sync"
        / "dciangx"
        / "DrienghTriang.txt"
    ) as f:
        rows = csv.DictReader(f, delimiter=" ")
        for r in rows:
            char = r["#字"]
            component = r["聲符"]
            char_to_component[char] = component
    with open(INCLUDED_DATA_DIR / "ytenx_ammendment.json") as f:
        extra_char_to_components = json.load(f)
        char_to_component.update(extra_char_to_components)

    log.info("Addding phonetic components for variants...")
    variant_to_component = {}
    for char in char_to_component:
        # TODO: address duplication
        for field_name in [
            "kSemanticVariant",
            "kZVariant",
            "kSimplifiedVariant",
            "kTraditionalVariant",
            "kReverseCompatibilityVariants",
            "kJinmeiyoKanji",
            "kJoyoKanji",
        ]:
            if variants := unihan.get(char, {}).get(field_name):
                # print(f"Found {variants} for {char}")
                for c in variants:
                    if c not in char_to_component:
                        variant_to_component[c] = char_to_component[char]
        if comp_variant := unihan.get(char, {}).get("kCompatibilityVariant"):
            # print(f"Found {comp_variant} for {char}")
            if comp_variant not in char_to_component:
                variant_to_component[comp_variant] = char_to_component[char]

    char_to_component.update(variant_to_component)

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


# Inspired by Heisig volume 2 (except for MIXED_D and SINGLETON)
class PurityType(IntEnum):
    PURE = 1
    SEMI_PURE = 2
    # At least 4 chars, only 2 pronunciations
    MIXED_A = 3
    # At least 4 chars, only 3 pronunciations
    MIXED_B = 4
    # At least 4 chars, at least 1 shared pronunciation
    MIXED_C = 5
    # At least one shared pronunciation
    MIXED_D = 6
    # Multiple characters, no pattern found
    NO_PATTERN = 7
    # Only one character in the group
    SINGLETON = 8


@dataclass
class ComponentGroup:
    component: str
    prons_to_chars: Dict[str, Set[str]]
    chars: List[str]
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.num_prons = len(self.prons_to_chars)

        self.exceptions = {}
        for pron, chars in self.prons_to_chars.items():
            if len(chars) == 1:
                self.exceptions[pron] = next(iter(chars))

        self.purity_type = PurityType.NO_PATTERN

        if len(self.chars) == 1:
            self.purity_type = PurityType.SINGLETON
        elif self.num_prons == 1:
            self.purity_type = PurityType.PURE
        elif self.num_prons == 2 and len(self.exceptions) == 1:
            self.purity_type = PurityType.SEMI_PURE
        elif len(self.chars) >= 4:
            if self.num_prons == 2:
                self.purity_type = PurityType.MIXED_A
            elif self.num_prons == 3:
                self.purity_type = PurityType.MIXED_B
            elif len(self.exceptions) != self.num_prons:
                self.purity_type = PurityType.MIXED_C
        elif len(self.exceptions) != self.num_prons:
            self.purity_type = PurityType.MIXED_D

    def remove(self, char):
        self.chars.remove(char)
        to_delete = []
        for pron, chars in self.prons_to_chars.items():
            chars.discard(char)
            if not chars:
                to_delete.append(pron)
        for pron in to_delete:
            del self.prons_to_chars[pron]

        self.__post_init__()

        self.warn(f"Removed {char}")

    def warn(self, message):
        self.warnings.append(message)


def _get_component_groups(index):
    groups = []
    for component, pron_to_chars in index.comp_pron_char.items():
        all_chars = set()
        for chars in pron_to_chars.values():
            all_chars.update(chars)

        group = ComponentGroup(
            component,
            # sort pronunciations by number of characters
            OrderedDict(sorted(pron_to_chars.items(), key=lambda item: -len(item[1]))),
            all_chars,
        )
        groups.append(group)

    return groups


def _post_process_groups(groups):
    # char -> groups containing it
    char_to_group = {}
    for group in groups:
        for c in group.chars:
            char_to_group[c] = group

    warnings_per_char = defaultdict(set)

    # Organize and sort the groups for easier inspection
    purity_to_group = defaultdict(list)
    for gc in groups:
        purity_to_group[gc.purity_type].append(gc)
    for groups in purity_to_group.values():
        groups.sort(key=lambda g: (-len(g.chars)))

    return (
        OrderedDict(sorted(purity_to_group.items(), key=lambda item: item[0])),
        warnings_per_char,
    )


def _move_exceptions_to_vocab(purity_type_to_group, char_to_pron_to_words):
    prons_to_move = defaultdict(list)
    for groups in purity_type_to_group.values():
        for group in groups:
            for pron, c in group.exceptions.items():
                if c in char_to_pron_to_words and pron in char_to_pron_to_words[c]:
                    group.warn(
                        f"Consider moving exceptional {c}/{pron} to common vocab {char_to_pron_to_words[c][pron]}"
                    )
                    prons_to_move[c].append(pron)
    return prons_to_move


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
    comp_pron_char = defaultdict(lambda: defaultdict(set))
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
            comp_pron_char[component][char_pron].add(char)

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

    unihan = _read_unihan()
    char_to_comp = _read_ytenx(unihan)

    # unihan = _read_unihan()
    if args.language == "jp":
        # old glyphs give a better matching with non-Japanese datasets
        char_to_prons, joyo_radicals = _read_joyo(use_old_glyphs=True)
        aligner = Aligner(char_to_prons)
        high_freq = _read_jp_netflix(aligner, 1000)
    elif args.language == "zh-HK":
        char_to_prons = _get_hk_ed_chars(unihan)
        # print(char_to_prons)
        # get chars to prons from unihan where
    # elif args.language == 'zh-Zh':
    else:
        log.error(f"Cannot handle language {args.language} yet")
        exit()

    index = _index(char_to_prons, char_to_comp)
    groups = _get_component_groups(index)
    purity_type_to_groups, warnings_per_char = _post_process_groups(groups)
    prons_to_move = _move_exceptions_to_vocab(purity_type_to_groups, high_freq)

    exceptional_chars = set()
    for groups in purity_type_to_groups.values():
        for g in groups:
            exceptional_chars.update(g.exceptions.values())

    # Log statistics about the results
    if warnings_per_char:
        log.info("Warnings:")
        for warning, chars in warnings_per_char.items():
            log.info(f"    {warning}: {len(chars)} chars")

    log.info(
        f"{sum(len(chars) for chars in prons_to_move.values())} pronunciation/character combos suggested to move to common words"
    )
    log.info(
        f"{len(index.no_comp_chars)} characters with no phonetic component data: {index.no_comp_chars}"
    )

    log.info(f"{len(index.no_pron_chars)} characters with no pronunciations")
    log.info(f"{len(index.unique_pron_to_char)} characters with unique readings")

    log.info(f"{sum([len(g) for g in purity_type_to_groups.values()])} total groups:")
    for purity_type, groups in purity_type_to_groups.items():
        num_chars = sum(len(g.chars) for g in groups)
        log.info(
            f"    {len(groups)} {purity_type.name} groups ({num_chars} characters)"
        )

    out_dir = OUTPUT_DIR / args.language
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "groups.json", "w") as f:
        f.write(_format_json(purity_type_to_groups))
    with open(out_dir / "unique_readings.json", "w") as f:
        f.write(_format_json(index.unique_pron_to_char))
    with open(out_dir / "no_readings.json", "w") as f:
        f.write(_format_json(index.no_pron_chars))
    with open(out_dir / "warnings_per_character.json", "w") as f:
        f.write(_format_json(warnings_per_char))

    # issues:
    # * try extracting component combos or component positions for better coverage?


# Other needs:
# create human-curated acceptance file


if __name__ == "__main__":
    main()
